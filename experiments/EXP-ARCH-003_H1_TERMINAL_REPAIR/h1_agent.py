# SPDX-License-Identifier: MIT
"""ARCH-003 H1 wrapper agent (prereg §5/B1–B5, §10/D7).

The frozen V54++ baseline plus the H1 terminal repair overlay.
One-factor discipline:
- Steps 0–711: live baseline action exactly (pure passthrough).
- Step 712: baseline action obtained once; planning runs in shadow sandbox.
- Steps 712–717: candidate worker commands + LIVE baseline markets verbatim.
- Step 718: candidate worker commands + candidate deterministic liquidation
  market (Change 1).
- Fail-safe: any guard failure, handshake mismatch, prediction mismatch, or
  non-consecutive callback abandons to live baseline immediately.
"""

from __future__ import annotations

import copy

from h1_const import (
    ANIMALS_3,
    ENTRY_STEP,
    FINAL_STEP,
    PIN_BOARD_SIZE,
    PIN_EPISODE_STEPS,
    PIN_MAX_ORDERS,
    PIN_SHED_CAPACITY,
    PIN_TURNS_PER_DAY,
    PRODUCTS_9,
)
from h1_dominance import (
    compute_terminal_liquidation_market,
    coverage_required,
    entry_prices,
    window_buy_units,
)
from h1_search import plan_terminal
from h1_shadow import (
    ShadowCursor,
    physical_equal,
    physical_state,
    run_baseline_window,
)
from h1_telemetry import H1Abstain, blank_record

# Rejected unit ops in window: new weed repair triggers
WEED_BLOCKED_OPS = frozenset({"PLANT", "BUILD_COOP", "BUILD_PASTURE"})

# Admitted market ops on 712–717
ADMITTED_MARKET_OPS = frozenset({"SELL", "BUY_PRODUCT"})


def _step_of(obs):
    raw = (obs or {}).get("step")
    if raw is not None:
        return int(raw)
    return 24 * int((obs or {}).get("day", 0) or 0) + int(
        (obs or {}).get("hour", 0) or 0)


def _get(configuration, key, default):
    if isinstance(configuration, dict):
        return configuration.get(key, default)
    return getattr(configuration, key, default)


class H1Overlay:
    """Stateful H1 wrapper around one frozen-baseline instance."""

    def __init__(self, baseline, shadow_only=False):
        self.fb = baseline
        self.shadow_only = bool(shadow_only)
        self.plans = {}
        self.last_steps = {}
        self.open_records = {}
        self.records = []
        self._last_shadow_schedule = {}

    # ------------------------------------------------------------ records
    def _open_record(self, seat):
        record = blank_record(seat, shadow_only=self.shadow_only)
        self.open_records[int(seat)] = record
        return record

    def _close_record(self, seat):
        record = self.open_records.pop(int(seat), None)
        if record is not None and record.get("reason") is not None:
            self.records.append(record)

    # ------------------------------------------------------------------ act
    def act(self, obs, configuration=None):
        seat = 1 if int((obs or {}).get("player", 0) or 0) == 1 else 0
        step = _step_of(obs)
        previous = self.last_steps.get(seat)
        if step == 0 or (previous is not None and step <= previous):
            self.plans.pop(seat, None)
            self._close_record(seat)
        self.last_steps[seat] = step
        plan = self.plans.get(seat)

        if plan is not None and ENTRY_STEP <= step <= FINAL_STEP:
            if previous != step - 1:
                self._abandon(
                    seat, "ABANDON_NONCONSECUTIVE",
                    {"step": step, "previous": previous})
                return self.fb.call(obs, configuration)
            live = self.fb.call(obs, configuration)
            return self._verify_and_emit(
                seat, step, obs, configuration, plan, live)

        if step != ENTRY_STEP:
            if plan is not None:
                self.plans.pop(seat, None)
            return self.fb.call(obs, configuration)

        # Step == E (712): clone ledgers BEFORE live call, then plan.
        route = self.fb.active_route(step, obs)
        if route not in self.fb.policies:
            record = self._open_record(seat)
            record["reason"] = "ABSTAIN_CONFIG"
            record["subcause"] = {"pin": "known-route",
                                  "expected": "backbone/yarn/bakery",
                                  "observed": route}
            record["step_E"] = step
            self._close_record(seat)
            return self.fb.call(obs, configuration)

        ledgers = self.fb.clone_ledgers(route, seat)
        live = self.fb.call(obs, configuration)
        record = self._open_record(seat)
        try:
            plan = self._plan_at_entry(
                seat, step, obs, configuration, route, ledgers, live,
                record)
        except H1Abstain as exc:
            record["reason"] = exc.reason
            record["subcause"] = exc.subcause
            record["step_E"] = step
            record["route"] = route
            self._close_record(seat)
            return live

        self.plans[seat] = plan
        record["reason"] = "OK_ACTIVATED"
        record["step_E"] = step
        record["route"] = route
        record["simulations"] = plan["simulations"]
        record["planning_ms"] = plan["planning_ms"]
        record["changed_workers"] = plan["changed_workers"]
        record["sold_unit_delta"] = plan["sold_unit_delta"]
        record["money_delta"] = plan["money_delta"]
        record["stock_value_gain"] = plan["stock_value_gain"]
        record["candidate_overflow"] = plan["candidate_overflow"]
        record["baseline_overflow"] = plan["baseline_overflow"]
        record["markets_verbatim"] = plan["markets_verbatim"]
        record["market_718_liquidation"] = plan["market_718_liquidation"]
        record["buy_units_U"] = plan["buy_units_U"]
        record["money_at_E"] = plan["money_at_E"]
        record["fertilizer_reaped"] = plan["fertilizer_reaped"]
        record["fertilizer_baseline"] = plan["fertilizer_baseline"]
        return self._emit(seat, step, obs, plan, live)

    # ---------------------------------------------------------- planning
    def _plan_at_entry(self, seat, step, obs, configuration, route,
                       ledgers, live, record):
        fb = self.fb
        # G0: config pins
        pins = [
            ("boardSize", PIN_BOARD_SIZE),
            ("turnsPerDay", PIN_TURNS_PER_DAY),
            ("episodeSteps", PIN_EPISODE_STEPS),
            ("shedCapacity", PIN_SHED_CAPACITY),
            ("maxMarketOrdersPerTurn", PIN_MAX_ORDERS),
        ]
        for key, want in pins:
            got = _get(configuration, key, want)
            try:
                ok = int(got) == want
            except (TypeError, ValueError):
                ok = False
            if not ok:
                raise H1Abstain("ABSTAIN_CONFIG", {
                    "pin": key, "expected": want, "observed": got})

        farms = (obs or {}).get("farms", []) or []
        if len(farms) < 2 or seat >= len(farms):
            raise H1Abstain("ABSTAIN_CONFIG", {
                "pin": "farms-shape", "expected": "2-farms",
                "observed": len(farms)})

        farm = farms[seat] or {}
        private = (obs or {}).get("private", {}) or {}

        # G1: shed validity
        shed = private.get("shed", {}) or {}
        if not isinstance(shed, dict):
            raise H1Abstain("ABSTAIN_SHED", {"detail": "shed-not-dict"})
        for item, qty in shed.items():
            if type(qty) is not int or qty < 0:
                raise H1Abstain("ABSTAIN_SHED", {
                    "detail": "bad-shed-qty:%s" % item})
        if sum(shed.values()) > PIN_SHED_CAPACITY:
            raise H1Abstain("ABSTAIN_SHED", {"detail": "overfull-shed"})

        # G2: supported items + inventory shape
        n = 1 + len(farm.get("hands", []) or [])
        inventories = private.get("inventories", []) or []
        if len(inventories) != n or n > 32:
            raise H1Abstain("ABSTAIN_ITEMS", {
                "detail": "inventory-shape:%d-vs-%d"
                % (len(inventories), n)})
        for stock in [shed, *inventories]:
            if not isinstance(stock, dict):
                raise H1Abstain("ABSTAIN_ITEMS",
                                {"detail": "stock-not-dict"})
            for item, qty in stock.items():
                if type(qty) is not int or qty < 0:
                    raise H1Abstain("ABSTAIN_ITEMS", {
                        "detail": "bad-qty:%s" % item})
                if item in PRODUCTS_9:
                    continue
                if item in ANIMALS_3 and qty == 0:
                    continue
                raise H1Abstain("ABSTAIN_ITEMS", {
                    "detail": "unsupported-item:%s" % item})

        # G4-pre: coverage gate on route prior
        route_table = fb.policies[route].route_prior
        route_u, route_items = window_buy_units(
            route_table[ENTRY_STEP:FINAL_STEP + 1])
        money = float(farm.get("money", 0) or 0)
        if money < coverage_required(route_u):
            raise H1Abstain("ABSTAIN_BUY_COVERAGE", {
                "U": route_u, "money_at_E": money,
                "required": coverage_required(route_u)})

        # Detailed shadow baseline run
        visible = fb.visible_configuration(configuration)
        try:
            prices = entry_prices(obs)
        except ValueError as exc:
            raise H1Abstain("ABSTAIN_CONFIG", {
                "pin": "entry-prices", "expected": "numeric-9",
                "observed": str(exc)})

        cursor = ShadowCursor(fb, seat, obs, configuration, visible,
                              ledgers, route, route_table,
                              coverage_U=route_u)
        baseline_run = run_baseline_window(cursor)
        schedule = baseline_run["actions"]
        self._last_shadow_schedule[int(seat)] = copy.deepcopy(schedule)

        # G3a: unit ops check
        for offset, action in enumerate(schedule):
            commands = [action.get("farmer", ["PASS"])] + list(
                action.get("hands", []) or [])
            for command in commands:
                op = command[0] if isinstance(command, list) and command else "PASS"
                if op in WEED_BLOCKED_OPS:
                    raise H1Abstain("ABSTAIN_WINDOW_OPS", {
                        "step": ENTRY_STEP + offset, "op": op})

        # G3b: market ops on 712–717
        for offset in range(FINAL_STEP - ENTRY_STEP):
            for order in schedule[offset].get("market", []) or []:
                op = order[0] if isinstance(order, list) and order else None
                if op not in ADMITTED_MARKET_OPS:
                    raise H1Abstain("ABSTAIN_MARKET_OP", {
                        "step": ENTRY_STEP + offset, "order": order})

        # G3c: pending ledger empty
        if ledgers.get("pending"):
            raise H1Abstain("ABSTAIN_MARKET_OP", {
                "step": ENTRY_STEP, "order": "pending-nonempty"})

        units_u, buy_items = window_buy_units(schedule)
        if "FERTILIZER" in buy_items:
            raise H1Abstain("ABSTAIN_MARKET_OP", {
                "step": ENTRY_STEP, "order": "BUY-FERTILIZER"})

        # G4: post-rollout coverage gate on schedule U
        required = coverage_required(units_u)
        if money < required:
            raise H1Abstain("ABSTAIN_BUY_COVERAGE", {
                "U": units_u, "money_at_E": money,
                "required": required})

        # G5: entry handshake
        norm_live = fb.align_hands(copy.deepcopy(live), obs)
        norm_shadow = fb.align_hands(copy.deepcopy(schedule[0]), obs)
        if norm_live.get("farmer") != norm_shadow.get("farmer"):
            raise H1Abstain("ABSTAIN_HANDSHAKE", {"field": "farmer"})
        if norm_live.get("hands") != norm_shadow.get("hands"):
            raise H1Abstain("ABSTAIN_HANDSHAKE", {"field": "hands"})
        if norm_live.get("market") != norm_shadow.get("market"):
            raise H1Abstain("ABSTAIN_HANDSHAKE", {"field": "market"})

        # G6/G7: search & adoption
        plan = plan_terminal(fb, seat, obs, schedule, baseline_run, prices)
        plan["buy_units_U"] = units_u
        plan["money_at_E"] = money
        plan["fertilizer_reaped"] = _fertilizer_acquired(plan["final_run"])
        plan["fertilizer_baseline"] = _fertilizer_acquired(baseline_run)
        plan["seat"] = seat
        plan["route"] = route
        plan["deviated"] = False
        plan["abandoned"] = False
        record["reason"] = "OK_ACTIVATED"
        return plan

    # ------------------------------------------------------ verification
    def _verify_and_emit(self, seat, step, obs, configuration, plan,
                         live):
        index = step - ENTRY_STEP
        physical_match = physical_equal(
            physical_state(obs), plan["expected_states"][index])
        if not physical_match:
            self._abandon(seat, "ABANDON_MISMATCH_T", {
                "step": step, "physical_match": False,
                "baseline_action_match": True})
            return live
        return self._emit(seat, step, obs, plan, live)

    def _emit(self, seat, step, obs, plan, live):
        index = step - ENTRY_STEP
        stored = plan["actions"][index]

        # CHANGE 1 / Market Boundary:
        # Steps 712–717: live baseline markets verbatim.
        # Step 718: candidate deterministic liquidation market.
        if step < FINAL_STEP:
            emitted_market = copy.deepcopy(live.get("market", []))
        else:
            # Step 718: authoritative liquidation market from plan (matching live computation)
            emitted_market = copy.deepcopy(stored.get("market", []))

        out = {
            "farmer": copy.deepcopy(stored.get("farmer", ["PASS"])),
            "hands": copy.deepcopy(stored.get("hands", [])),
            "market": emitted_market,
        }
        out = self.fb.align_hands(out, obs)
        live_units = [live.get("farmer", ["PASS"])] + list(
            live.get("hands", []) or [])
        plan_units = [out.get("farmer", ["PASS"])] + list(
            out.get("hands", []) or [])
        if plan_units != live_units:
            plan["deviated"] = True
        if step == FINAL_STEP:
            self._close_record(seat)
        if self.shadow_only:
            return live
        return out

    def _abandon(self, seat, reason, subcause):
        self.plans.pop(seat, None)
        record = self.open_records.get(int(seat))
        if record is not None:
            record["reason"] = reason
            record["subcause"] = dict(subcause)
            if reason == "ABANDON_MISMATCH_T":
                record["abandon_step"] = subcause.get("step")
        self._close_record(seat)


def _fertilizer_acquired(run):
    """Fertilizer units acquired in a run (P6/R8 audit field)."""
    total = 0
    for event in run.get("events", []) or []:
        acquired = event.get("acquired", {}) or {}
        total += int(acquired.get("FERTILIZER", 0) or 0)
    return total


def build_agent(baseline, shadow_only=False):
    """Wrap a :class:`FrozenBaseline` with the H1 overlay."""
    overlay = H1Overlay(baseline, shadow_only=shadow_only)

    def agent(obs, configuration=None):
        return overlay.act(obs, configuration)

    agent.overlay = overlay
    agent.baseline = baseline
    return agent
