# SPDX-License-Identifier: MIT
"""ARCH-002 H1 shadow simulator (prereg §7/S1, §8.2/H1–H4, §11).

Two responsibilities:

1. BASELINE PREDICTION — replay the frozen V54++ terminal pipeline
   exactly (replay → weed-assumed-empty → planner reorder → controller
   ``_repay`` / ``_release_pending`` / fronting / 718 liquidation →
   outer recall/units/market overlays) on cloned ledgers, using the
   EXACT live functions captured by :mod:`h1_baseline`.  Structurally
   disabled mechanisms (seed-trim, shed-guard, ``_defer``, ``_preempt``,
   market-maker) are skipped by asserted proof; the skip is policed by
   the G5 handshake + stepwise re-verification, never trusted blindly.

2. SCHEDULE SIMULATION — Dmitrii-style rollouts
   (``terminal_planner.simulate`` structure) with H1's preregistered
   adaptations: NO step-718 recompute (D3 verbatim passthrough),
   unilateral shared-inventory projection with the exact SELL $1-rule
   and exact town-tick timing, exact BUY modeling with the G4 coverage
   gate, and DROP-overflow / deposit / acquisition event tracking.

Unit and decay transitions call the pinned engine extract
(:mod:`h1_units`) — no reimplementation.  Money is tracked
unilaterally (own executions + town ticks at frozen entry quotes for
the FIRST unit of each order... precisely: per-unit quotes from the
projected inventory); the opponent residual is confined to trigger
modeling and policed by re-verification (audit R5).
"""

from __future__ import annotations

import copy

import h1_units as _U
from h1_dominance import coverage_required
from h1_const import (
    ENTRY_STEP,
    FINAL_STEP,
    PIN_BOARD_SIZE,
    PIN_EPISODE_STEPS,
    PIN_MAX_ORDERS,
    PIN_SHED_CAPACITY,
    PIN_TURNS_PER_DAY,
    PRODUCTS_9,
)
from h1_telemetry import H1Abstain

# Validated engine tick intervals (port Config defaults 4/24, corroborated
# by cppsim + Dmitrii + 719-action routes; audit §4).  Used ONLY for the
# unilateral shared-inventory projection (town_consume timing).  Any engine
# divergence here affects trigger modeling only and is policed by
# re-verification (safe direction: abandon to baseline).
ENGINE_TICK_CONFIG = {
    "townShopSellInterval": 4,
    "townCenterSellInterval": 24,
}


# ---------------------------------------------------------------- physical
def physical_state(obs):
    """Comparable own physical state; money intentionally excluded.

    Mirror of Dmitrii ``physical_state`` (terminal_planner.py:40–44).
    Returns deep copies (stored snapshots must not alias live objects).
    """
    seat = int((obs or {}).get("player", 0) or 0)
    farms = (obs or {}).get("farms", []) or []
    farm = farms[seat] if seat < len(farms) else {}
    snap = {key: copy.deepcopy(value) for key, value in farm.items()
            if key != "money"}
    return snap, copy.deepcopy((obs or {}).get("private", {}) or {})


def physical_equal(left, right):
    """Deep equality on (farm-minus-money, private) snapshots."""
    return left == right


def _commands(action, n):
    """Mirror of Dmitrii ``_commands`` (terminal_planner.py:47–49)."""
    hands = action.get("hands", []) or []
    return [action.get("farmer", ["PASS"]), *hands][:n] + [
        ["PASS"] for _ in range(max(0, n - 1 - len(hands)))]


# ------------------------------------------------------------------- cursor
class ShadowCursor:
    """Mutable single-seat rollout state (shadow-owned throughout)."""

    def __init__(self, baseline, seat, entry_obs, configuration,
                 visible_cfg, ledgers, route_name, route_table,
                 coverage_U=None):
        self.fb = baseline
        self.seat = int(seat)
        self.configuration = configuration
        self.visible_cfg = visible_cfg
        self.route_name = route_name
        self.route_table = route_table
        # Precomputed window BUY units for the G4 gate / BUY defense.
        self.coverage_U = coverage_U
        self.step0 = int(entry_obs.get("step", ENTRY_STEP))
        farm = ((entry_obs.get("farms", []) or [])[int(seat)] or {})
        self.farm = copy.deepcopy(farm)
        if "money" not in self.farm:
            self.farm["money"] = 0.0
        self.private = copy.deepcopy(entry_obs.get("private", {}) or {})
        market = (entry_obs.get("market", {}) or {})
        inv = (market.get("inventory", {}) or {})
        prc = (market.get("prices", {}) or {})
        self.proj_inventory = {p: int(inv.get(p, 10000)) for p in PRODUCTS_9}
        self.proj_prices = {p: int(prc.get(p, 1)) for p in PRODUCTS_9}
        opp = ((entry_obs.get("farms", []) or [])[1 - int(seat)] or {})
        self.frozen_opp_farm = copy.deepcopy(opp)
        town = (entry_obs.get("town", {}) or {})
        self.frozen_shops = list(town.get("unlocked_shops", []) or [])
        n = 1 + len(self.farm.get("hands", []) or [])
        while len(self.private.get("inventories", [])) < n:
            self.private.setdefault("inventories", []).append({})
        self.n = n
        self.ledgers = ledgers  # shadow-owned clone (may be {})
        self.ctrl = None  # shadow controller namespace (lazy)
        self.deposited = [dict() for _ in range(n)]
        self.sold = {}
        self.overflow = 0
        self.events = []
        self.rows = []
        self.executed = []

    def controller_self(self):
        if self.ctrl is None:
            from h1_baseline import shadow_controller_self
            self.ctrl = shadow_controller_self(self.fb.config)
        return self.ctrl

    def money(self):
        return float(self.farm.get("money", 0.0) or 0.0)

    # -- projected observation --------------------------------------
    def project_obs(self, t):
        """Projected obs for baseline-pipeline replay at step ``t``.

        Own farm/private are cursor-projected; opponent farm, shops, and
        hand count are frozen at entry (no dawn/unlocks/HIRE in-window —
        engine premises policed by re-verification).
        """
        t = int(t)
        farms = [None, None]
        farms[self.seat] = copy.deepcopy(self.farm)
        farms[1 - self.seat] = copy.deepcopy(self.frozen_opp_farm)
        return {
            "step": t,
            "day": t // PIN_TURNS_PER_DAY,
            "hour": t % PIN_TURNS_PER_DAY,
            "player": self.seat,
            "farms": farms,
            "market": {
                "inventory": dict(self.proj_inventory),
                "prices": dict(self.proj_prices),
            },
            "town": {"unlocked_shops": list(self.frozen_shops)},
            "private": copy.deepcopy(self.private),
        }

    def snapshot_state(self):
        """Pre-step (farm-minus-money, private) snapshot for re-verify."""
        snap = {k: copy.deepcopy(v) for k, v in self.farm.items()
                if k != "money"}
        return snap, copy.deepcopy(self.private)


# ------------------------------------------------- baseline prediction
def predict_baseline_action(cursor, t):
    """Replay the frozen baseline pipeline for step ``t`` (pure shadow).

    Mirrors ``ResidualValueController.apply`` (v49:743–816) +
    ``build_sparse_planner.agent`` (v23.planner:42–60) +
    ``wrap_weed_repair`` empty path (v22_weed_repair:46–117) + the outer
    agent overlays (compiled:4468–4485), on the cursor's projected obs
    and cloned ledgers.  Every behavioral function is the EXACT live
    object from :mod:`h1_baseline`; the only replicated code is the
    ~30-line ``apply()`` sequencing (cited line-for-line below).
    """
    fb = cursor.fb
    cfg = fb.config
    ctrl = cursor.controller_self()
    obs = cursor.project_obs(t)
    state = cursor.ledgers
    # v49.apply:747-748 reset check (exact; _reset itself is exact).
    if not state or t == 0 or t < int(state.get("last_step", -1)):
        state = fb.m_reset(ctrl, cursor.seat, t)
        cursor.ledgers = state
    # v49.apply:750 flow inference (exact unbound method).
    fb.m_update_flow(ctrl, obs, cursor.visible_cfg, state, t)
    # v49.apply:752-763 near streak + latch (sequencing mirror).
    distance = fb.clone_distance(obs)
    if distance <= float(cfg.near_distance):
        state["near_streak"] = int(state.get("near_streak", 0)) + 1
        ctrl.telemetry["near_turns"] += 1
    else:
        state["near_streak"] = 0
    if (
        not bool(state.get("near_latched", False))
        and int(state.get("near_streak", 0))
        >= max(1, int(cfg.near_streak_required))
    ):
        state["near_latched"] = True
        ctrl.telemetry["near_latches"] += 1
    # Sparse planner: replay (v21:4-8, exact table read) → weed repair
    # EMPTY path (no active transactions; handshake-verified) → reorder
    # (v23.planner:42-60 sequencing mirror with exact functions).
    step_index = min(max(0, int(t)), len(cursor.route_table) - 1)
    base = fb.align_hands(
        copy.deepcopy(cursor.route_table[step_index]), obs
    )
    base = fb.align_hands(base, obs)  # wrap_weed_repair exit normalization
    regime = fb.regime_from_configuration(cursor.visible_cfg)
    alpha = fb.rebalance_demand_alpha if regime == "rebalance" else 0.0
    action = fb.reorder_sell_slots(obs, base, cursor.visible_cfg,
                                   demand_alpha=alpha)
    # v49.apply:766-769 route bookkeeping (route_selector None).
    state["route"] = str(state.get("route"))
    ctrl.telemetry["routes"][state["route"]] += 1
    # v49.apply:770-771 repay + pending release (exact unbound methods).
    action = fb.m_repay(ctrl, action, state, t)
    action = fb.m_release_pending(ctrl, obs, action, state, t)
    # v49.apply:772 _defer — SKIPPED: defer_enabled False asserted at
    # baseline load (fail closed); skip policed by G5/re-verification.
    # v49.apply:773 _preempt — SKIPPED: active window [72,700) asserted
    # disjoint from 712–718 at load (fail closed); policed likewise.
    # v49.apply:775-797 fronting branch (sequencing mirror).
    front_items = {str(item) for item in cfg.front_items}
    supply_peak = max(
        (
            float(value)
            for item, value in state.get("opponent_supply", {}).items()
            if item in front_items
        ),
        default=0.0,
    )
    # _money_gap mirror (v49:246-253, incl. the len!=2 guard).
    _farms = list(obs.get("farms", []) or [])
    if len(_farms) != 2:
        gap = 0.0
    else:
        _own = _farms[cursor.seat] if isinstance(
            _farms[cursor.seat], dict) else {}
        _opp = _farms[1 - cursor.seat] if isinstance(
            _farms[1 - cursor.seat], dict) else {}
        gap = float(_own.get("money", 0) or 0) - float(
            _opp.get("money", 0) or 0)
    should_front = bool(cfg.front_existing_sells) and (
        (bool(cfg.front_on_near) and bool(state.get("near_latched", False)))
        or -gap >= float(cfg.front_money_deficit)
        or supply_peak >= float(cfg.front_supply_threshold)
    )
    before = copy.deepcopy(action.get("market", []))
    if should_front:
        action = fb.sort_sells_front(
            obs, action, cursor.visible_cfg, cfg.front_items
        )
    else:
        # NOTE: literal demand_alpha=0.25 mirrors v49.apply:795 exactly.
        action = fb.reorder_sell_slots(
            obs, action, cursor.visible_cfg, demand_alpha=0.25
        )
    if action.get("market", []) != before:
        ctrl.telemetry["front_turns"] += 1
    # v49.apply:799-800 market maker — SKIPPED: market_maker_enabled
    # False asserted at load (fail closed); policed likewise.
    # v49.apply:801-804 terminal liquidation branch (exact mirror).
    if t == FINAL_STEP and str(cfg.terminal_rule) != "none":
        action = fb.terminal_market(
            obs, action, rule=str(cfg.terminal_rule), replace=True
        )
    # v49.apply:806-815 safe + truncate + ledger updates (exact mirror).
    action = fb.safe_controller_action(action, obs)
    action["market"] = action["market"][: max(1, int(cfg.maximum_orders))]
    state["last_market_net"] = fb.executable_market_net(
        obs, action, cursor.visible_cfg
    )
    state["last_shops"] = list(
        ((obs.get("town", {}) or {}).get("unlocked_shops", []) or [])
    )
    state["last_step"] = t
    ctrl.telemetry["calls"] += 1
    # Outer overlays (compiled:4468-4485).  Seed-trim + shed-guard are
    # SKIPPED by proof (audit §1.3; prereg §8.2/H3); policed by G5.
    if 713 <= t <= 716:
        action = fb.route_loaded_units(obs, action, t)
    if t in (717, 718):
        action = fb.terminal_units(obs, action, t)
    if t == FINAL_STEP:
        action = fb.terminal_market(obs, action, rule="collision",
                                    replace=True)
    return action


# ------------------------------------------------- schedule simulation
def execute_units(cursor, action, t, offset):
    """Execute one step's unit commands with Dmitrii event tracking.

    Structure mirrors ``terminal_planner.simulate`` unit loop
    (:158–181): pre-action inventory/shed snapshots, exact unit
    application, deposit-delta + DROP-overflow + acquisition events.
    No PLANT seed-contention pre-pass (D1/G3 exclude PLANT; the pinned
    unit model handles single PLANTs exactly if ever present).
    """
    farm, private = cursor.farm, cursor.private
    n = cursor.n
    day = int(t) // PIN_TURNS_PER_DAY
    for actor, command in enumerate(_commands(action, n)):
        if not isinstance(command, list) or not command:
            command = ["PASS"]
        pos = farm["farmer"] if actor == 0 else farm["hands"][actor - 1]
        xy = tuple(pos)
        inv = private["inventories"][actor]
        watch_inv = command[0] in {"DROP", "HARVEST", "COLLECT_FERTILIZER"}
        watch_shed = command[0] in {"DROP", "PLACE"}
        before_inv = dict(inv) if watch_inv else None
        before_shed = dict(private["shed"]) if watch_shed else None
        _U._apply_unit_action(farm, private, actor, command,
                              PIN_BOARD_SIZE, day, PIN_TURNS_PER_DAY,
                              PIN_SHED_CAPACITY)
        if before_shed is not None:
            delta = {item: amount - before_shed.get(item, 0)
                     for item, amount in private["shed"].items()
                     if amount > before_shed.get(item, 0)}
            for item, amount in delta.items():
                dep = cursor.deposited[actor]
                dep[item] = dep.get(item, 0) + amount
            if delta:
                cursor.events.append({"offset": offset, "actor": actor,
                                      "op": command[0], "xy": xy,
                                      "deposited": delta})
            if command[0] == "DROP":
                cursor.overflow += sum(
                    max(0, amount - inv.get(item, 0) - delta.get(item, 0))
                    for item, amount in before_inv.items())
        if command[0] in {"HARVEST", "COLLECT_FERTILIZER"}:
            delta = {item: amount - before_inv.get(item, 0)
                     for item, amount in inv.items()
                     if amount > before_inv.get(item, 0)}
            if delta:
                cursor.events.append({"offset": offset, "actor": actor,
                                      "op": command[0], "xy": xy,
                                      "acquired": delta})


def execute_market(cursor, market, t):
    """Unilateral market execution with exact engine quantity semantics.

    Per-order slot order; per-unit quotes from the projected inventory
    (SELL: ``price(inv)`` + $1-rule inventory increment; BUY: ``price
    (inv-1)``, money + shed-room gates, remainder-dead on first failure)
    — mirroring port ``process_market``/``commit_unit`` (sim.py:542–652)
    for a passive opponent.  Town-consume ticks apply AFTER the market
    (engine order) at validated engine intervals.  Unknown-item orders
    are engine-exact no-ops (dead orders).

    A shadow BUY money failure raises ``H1Abstain(ABSTAIN_BUY_COVERAGE)``:
    under the G4 gate this is unreachable; reaching it proves coverage
    modeling breakdown and must fail closed, never silently diverge.
    """
    fb = cursor.fb
    shed = cursor.private["shed"]
    for raw in list(market or [])[:PIN_MAX_ORDERS]:
        if not isinstance(raw, list) or len(raw) < 3:
            continue  # engine conv_order: malformed → M_NONE no-op
        op, item = raw[0], raw[1]
        try:
            qty = int(raw[2])
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue  # engine: o[2] > 0 required, else skipped
        if op == "SELL" and item in PRODUCTS_9:
            for _ in range(qty):
                if int(shed.get(item, 0) or 0) <= 0:
                    break  # remainder dead (commit_unit False)
                quote = int(fb.market_price(
                    item, int(cursor.proj_inventory[item])))
                shed[item] = int(shed.get(item, 0)) - 1
                cursor.farm["money"] = cursor.money() + quote
                cursor.sold[item] = cursor.sold.get(item, 0) + 1
                if quote > 1:
                    cursor.proj_inventory[item] += 1
        elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
            for _ in range(qty):
                quote = int(fb.market_price(
                    item, int(cursor.proj_inventory[item]) - 1))
                if cursor.money() < quote:
                    units = cursor.coverage_U
                    raise H1Abstain(
                        "ABSTAIN_BUY_COVERAGE",
                        {"U": units, "money_at_E": cursor.money(),
                         "required": coverage_required(units or 0)})
                total = sum(int(v or 0) for v in shed.values()
                            if isinstance(v, (int, float)))
                if total >= PIN_SHED_CAPACITY:
                    break  # remainder dead on shed room (engine-exact)
                cursor.farm["money"] = cursor.money() - quote
                shed[item] = int(shed.get(item, 0) or 0) + 1
                cursor.proj_inventory[item] -= 1
        # else: engine-dead order (unknown op/item) → exact no-op.
    # Town-consume ticks (engine order: after market; validated intervals).
    for item in PRODUCTS_9:
        cursor.proj_inventory[item] -= int(fb.demand_at(
            cursor.frozen_shops, int(t), ENGINE_TICK_CONFIG, item))
    # Price refresh (mirror refresh_prices).
    for item in PRODUCTS_9:
        cursor.proj_prices[item] = int(fb.market_price(
            item, int(cursor.proj_inventory[item])))


def simulate_step(cursor, action, t, offset):
    """One full shadow step: units → market → decay + row record."""
    action = copy.deepcopy(action)
    execute_units(cursor, action, t, offset)
    pre_market = dict(cursor.private["shed"])
    execute_market(cursor, action.get("market", []), t)
    _U._decay_plants(cursor.farm, int(t))
    cursor.rows.append({
        "pre_market_shed": pre_market,
        "post_market_shed": dict(cursor.private["shed"]),
        "deposited_by_actor": [dict(v) for v in cursor.deposited],
        "sold": dict(cursor.sold),
    })
    cursor.executed.append(action)
    return action


def run_baseline_window(cursor):
    """Detailed shadow baseline run over 712–718 (prereg §7/S1).

    Interleaves baseline prediction + execution per step.  Returns the
    run record (mirror of Dmitrii ``simulate(..., detailed=True)``).
    """
    states = []
    for offset, t in enumerate(range(ENTRY_STEP, FINAL_STEP + 1)):
        if (int(t) + 1) % PIN_TURNS_PER_DAY == 0:
            raise H1Abstain("ABSTAIN_CONFIG",
                            {"pin": "dawn-free-window", "expected": True,
                             "observed": int(t)})
        states.append(cursor.snapshot_state())
        action = predict_baseline_action(cursor, t)
        simulate_step(cursor, action, t, offset)
    states.append(cursor.snapshot_state())
    return {
        "rows": cursor.rows,
        "states": states,
        "events": cursor.events,
        "actions": cursor.executed,
        "overflow_units": cursor.overflow,
        "farm": cursor.farm,
        "private": cursor.private,
        "sold": cursor.sold,
    }


def simulate_schedule(baseline, seat, entry_obs, schedule):
    """Roll out a FIXED schedule (trial/candidate) from entry state.

    No baseline prediction, no ledger use: markets execute verbatim
    from the schedule.  Returns the run record.  Raises ``H1Abstain``
    on BUY-coverage breakdown (defense in depth; G4-gated).
    """
    if len(schedule) != FINAL_STEP - ENTRY_STEP + 1:
        raise H1Abstain("ABSTAIN_CONFIG",
                        {"pin": "schedule-len-7", "expected": 7,
                         "observed": len(schedule)})
    cursor = ShadowCursor(baseline, seat, entry_obs, None, None, {},
                          "", [])
    states = []
    for offset, t in enumerate(range(ENTRY_STEP, FINAL_STEP + 1)):
        states.append(cursor.snapshot_state())
        simulate_step(cursor, schedule[offset], t, offset)
    states.append(cursor.snapshot_state())
    return {
        "rows": cursor.rows,
        "states": states,
        "events": cursor.events,
        "actions": cursor.executed,
        "overflow_units": cursor.overflow,
        "farm": cursor.farm,
        "private": cursor.private,
        "sold": cursor.sold,
    }
