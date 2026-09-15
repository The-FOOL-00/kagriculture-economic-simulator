# SPDX-License-Identifier: MIT
"""ARCH-002 H1 frozen-baseline access layer (prereg §3/D8, §8.2/H3).

Loads ``candidates/compiled_v54_plus_residual.py`` read-only after
verifying its SHA-256, and exposes the EXACT live pipeline functions
for the H1 shadow simulator:

* planner: ``reorder_sell_slots``, ``regime_from_configuration``;
* controller (unbound methods, called with a shadow-owned state — the
  live ledgers are never written by H1): ``_reset``, ``_update_flow``,
  ``_repay``, ``_release_pending``;
* controller helpers (module-level, pure): ``_executable_market_net``,
  ``_safe``, ``_sort_sells_front``;
* overlays (module-level, pure): ``align_hands``, ``terminal_market``,
  ``monetizable_terminal_units``, ``clone_distance``,
  ``_route_loaded_units``;
* outer assembly: ``agent``, ``_select_route``,
  ``_v56_visible_configuration``, live policies / controllers / config.

R6 compliance: H1 never calls ``build_residual_controller``, never
constructs policies, never writes live configs/ledgers/telemetry.  The
shadow invokes unbound controller methods on shadow-owned clones only.

Structurally-disabled mechanisms (``_defer``, ``_preempt``,
market-maker) are NEVER called; their disabled state is asserted from
the live config at load time (fail closed) and the skip is policed at
runtime by the G5 handshake + stepwise re-verification.  H1 source
therefore contains no sale-timing shifting, deferral, or market-maker
logic.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import importlib.util
import os
import sys
import types

from h1_const import (
    BASELINE_PATH,
    BASELINE_SHA256,
    ENTRY_STEP,
    FINAL_STEP,
)

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_LOAD_COUNTER = 0


class BaselineLoadError(RuntimeError):
    """Raised when the frozen baseline fails any integrity premise."""


def _fail(reason):
    raise BaselineLoadError("H1 FAIL-CLOSED (baseline): " + reason)


def _require_module_attr(module, name):
    try:
        value = getattr(module, name)
    except AttributeError:
        _fail("embedded module %r lacks %r" % (module.__name__, name))
    if not callable(value):
        _fail("embedded %s.%s is not callable" % (module.__name__, name))
    return value


class FrozenBaseline:
    """One isolated instance of the frozen V54++ residual baseline."""

    def __init__(self, module):
        self.module = module
        self.agent = module.agent
        self._capture_policies()
        self._capture_embedded()
        self._capture_outer()
        self._verify_live_config()

    # -- policies / controllers --------------------------------------
    def _capture_policies(self):
        mod = self.module
        self.policies = {}
        for route_name, attr in (
            ("backbone", "_POLICY_BACKBONE"),
            ("yarn", "_POLICY_YARN"),
            ("bakery", "_POLICY_BAKERY"),
        ):
            policy = getattr(mod, attr, None)
            if not callable(policy):
                _fail("missing %s" % attr)
            controller = getattr(policy, "controller", None)
            if controller is None or type(controller).__name__ != (
                "ResidualValueController"
            ):
                _fail("%s has no ResidualValueController" % attr)
            prior = getattr(policy, "route_prior", None)
            if not isinstance(prior, list) or len(prior) != 719:
                _fail("%s route_prior is not 719 actions" % attr)
            self.policies[route_name] = policy
        configs = {id(p.controller.config) for p in self.policies.values()}
        if len(configs) != 1:
            _fail("live policies do not share one ResidualConfig")
        self.config = self.policies["backbone"].controller.config
        # Route-name → module route table identity (values must match priors).
        tables = {
            "backbone": getattr(mod, "_V56_BACKBONE_ROUTE", None),
            "yarn": getattr(mod, "_V56_YARN_ROUTE", None),
            "bakery": getattr(mod, "_V58_BAKERY_YARN_ROUTE", None),
        }
        for name, table in tables.items():
            if table != self.policies[name].route_prior:
                _fail("route table mismatch for %s" % name)
        self.route_tables = tables

    # -- embedded exact functions -------------------------------------
    def _capture_embedded(self):
        def emb(name):
            module = sys.modules.get(name)
            if module is None:
                _fail("embedded module %r absent from sys.modules" % name)
            return module

        v19 = emb("scripts.v19_terminal")
        v23lib = emb("v23.policy_library")
        v23enc = emb("v23.state_encoder")
        v23sim = emb("v23.simulator")
        v23plan = emb("v23.planner")
        v49 = emb("v49.residual_controller")

        self.align_hands = _require_module_attr(v19, "align_hands")
        self.terminal_market = _require_module_attr(v19, "terminal_market")
        self.terminal_units = _require_module_attr(
            v19, "monetizable_terminal_units"
        )
        self.clone_distance = _require_module_attr(v19, "clone_distance")
        self.reorder_sell_slots = _require_module_attr(
            v23lib, "reorder_sell_slots"
        )
        self.regime_from_configuration = _require_module_attr(
            v23enc, "regime_from_configuration"
        )
        self.market_price = _require_module_attr(v23sim, "market_price")
        planner_config_cls = getattr(v23plan, "PlannerConfig", None)
        if planner_config_cls is None:
            _fail("embedded PlannerConfig missing")
        # Live sparse planners are built with PlannerConfig() defaults.
        self.rebalance_demand_alpha = float(
            planner_config_cls().rebalance_demand_alpha
        )
        self.executable_market_net = _require_module_attr(
            v49, "_executable_market_net"
        )
        self.safe_controller_action = _require_module_attr(v49, "_safe")
        self.sort_sells_front = _require_module_attr(v49, "_sort_sells_front")
        self.demand_at = _require_module_attr(v49, "_demand_at")

        controller_cls = getattr(v49, "ResidualValueController", None)
        if controller_cls is None:
            _fail("embedded ResidualValueController missing")
        # Unbound methods: invoked with a shadow-owned namespace, never on
        # a live controller.  No instantiation happens here (R6).
        self.m_reset = controller_cls._reset
        self.m_update_flow = controller_cls._update_flow
        self.m_repay = controller_cls._repay
        self.m_release_pending = controller_cls._release_pending
        for meth in (
            self.m_reset,
            self.m_update_flow,
            self.m_repay,
            self.m_release_pending,
        ):
            if not callable(meth):
                _fail("controller method %r not callable" % (meth,))

    # -- outer assembly ------------------------------------------------
    def _capture_outer(self):
        mod = self.module
        for name in (
            "_select_route",
            "_route_loaded_units",
            "_v56_visible_configuration",
        ):
            if not callable(getattr(mod, name, None)):
                _fail("outer %s missing" % name)
        self.select_route = mod._select_route
        self.route_loaded_units = mod._route_loaded_units
        self.visible_configuration = mod._v56_visible_configuration
        if mod._TERMINAL_UNITS is not self.terminal_units:
            _fail("outer _TERMINAL_UNITS identity mismatch")
        if mod._TERMINAL_MARKET is not self.terminal_market:
            _fail("outer _TERMINAL_MARKET identity mismatch")

    # -- live-config premises (assert+skip foundations) ------------------
    def _verify_live_config(self):
        cfg = self.config
        if bool(getattr(cfg, "defer_enabled", True)):
            _fail("defer_enabled is not False")
        if bool(getattr(cfg, "market_maker_enabled", True)):
            _fail("market_maker_enabled is not False")
        start = int(getattr(cfg, "active_start", -1))
        stop = int(getattr(cfg, "active_stop", -1))
        if not (stop <= ENTRY_STEP or start > FINAL_STEP):
            _fail(
                "preempt window [%d,%d) overlaps 712–718" % (start, stop)
            )
        if int(getattr(cfg, "maximum_orders", -1)) != 10:
            _fail("maximum_orders is not 10")

    # -- live interaction ------------------------------------------------
    def call(self, obs, configuration=None):
        """The single sanctioned live call: run the frozen baseline."""
        return self.agent(obs, configuration)

    def active_route(self, step, obs):
        town = (obs or {}).get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])
        return self.select_route(int(step), shops)

    def active_policy(self, route_name):
        try:
            return self.policies[route_name]
        except KeyError:
            _fail("unknown live route %r" % (route_name,))

    def clone_ledgers(self, route_name, seat):
        """Deep-copy the ACTIVE policy's controller ledgers (read-only)."""
        states = self.active_policy(route_name).controller.states
        return copy.deepcopy(states.get(int(seat), {}))


def fresh_shadow_telemetry():
    """Shadow telemetry sink with the exact live key set (v49 __init__)."""
    return {
        "games": 0,
        "calls": 0,
        "near_turns": 0,
        "near_latches": 0,
        "flow_updates": 0,
        "mirror_evidence_turns": 0,
        "mirror_confidence_sum": 0.0,
        "mirror_confidence_peak": 0.0,
        "front_turns": 0,
        "preempt_turns": 0,
        "preempt_units": 0,
        "preempt_value": 0.0,
        "repaid_units": 0,
        "defer_turns": 0,
        "defer_units": 0,
        "release_turns": 0,
        "release_units": 0,
        "routes": collections.Counter(),
    }


def shadow_controller_self(live_config):
    """Namespace satisfying the unbound controller methods' ``self`` use.

    Only ``.config`` (read), ``.telemetry`` (shadow sink),
    ``.routes`` (membership test in ``_reset``), and ``.states``
    (shadow-owned seat states for ``_reset``) are touched.
    """
    return types.SimpleNamespace(
        config=live_config,
        telemetry=fresh_shadow_telemetry(),
        routes={"default": None},
        states={},
    )


def load_baseline():
    """Import a fresh, isolated, verified frozen-baseline instance."""
    global _LOAD_COUNTER
    path = os.path.join(_REPO_ROOT, BASELINE_PATH)
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    if digest != BASELINE_SHA256:
        _fail("file hash mismatch: %s != %s" % (digest, BASELINE_SHA256))
    _LOAD_COUNTER += 1
    name = "h1_frozen_baseline_%d" % _LOAD_COUNTER
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return FrozenBaseline(module)
