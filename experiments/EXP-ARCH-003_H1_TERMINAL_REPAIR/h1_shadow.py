# SPDX-License-Identifier: MIT
"""ARCH-003 H1 shadow simulator (prereg §7/S1, §8.2/H1–H4, §11).

Two responsibilities:

1. BASELINE PREDICTION — replay the frozen V54++ terminal pipeline
   exactly (replay → weed-assumed-empty → planner reorder → controller
   ``_repay`` / ``_release_pending`` / fronting / 718 liquidation →
   outer recall/units/market overlays) on cloned ledgers, using the
   EXACT live functions captured by :mod:`h1_baseline`.

2. SCHEDULE SIMULATION — Dmitrii-style rollouts
   (``terminal_planner.simulate`` structure) with H1-REPAIR adaptations:
   - Steps 712–717: exact live baseline market orders verbatim.
   - Step 718: candidate deterministic liquidation market (Change 1)
     applied to post-drop candidate shed state via authoritative
     ``compute_terminal_liquidation_market``.
   - Unilateral shared-inventory projection with exact SELL $1-rule and
     exact town-tick timing.
   - Exact BUY modeling with G4 coverage gate ($125 × U).
   - Exact DROP-overflow, deposit, and acquisition event tracking.

Exact step order (CHANGE 1 / Protocol):
worker actions
-> pre-market state
-> baseline markets for 712–717 OR candidate liquidation market at 718
-> market execution
-> town consumption
-> plant decay
-> row recording
-> terminal state
"""

from __future__ import annotations

import copy

import h1_units as _U
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
from h1_dominance import coverage_required
from h1_telemetry import H1Abstain

# Validated engine tick intervals (port Config defaults 4/24, corroborated
# by cppsim + Dmitrii + 719-action routes; audit §4).  Used ONLY for the
# unilateral shared-inventory projection (town_consume timing).
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
        hand count are frozen at entry.
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
    """Replay the frozen baseline pipeline for step ``t`` (pure shadow)."""
    fb = cursor.fb
    cfg = fb.config
    ctrl = cursor.controller_self()
    obs = cursor.project_obs(t)
    state = cursor.ledgers

    if not state or t == 0 or t < int(state.get("last_step", -1)):
        state = fb.m_reset(ctrl, cursor.seat, t)
        cursor.ledgers = state

    fb.m_update_flow(ctrl, obs, cursor.visible_cfg, state, t)

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

    step_index = min(max(0, int(t)), len(cursor.route_table) - 1)
    base = fb.align_hands(
        copy.deepcopy(cursor.route_table[step_index]), obs
    )
    base = fb.align_hands(base, obs)
    regime = fb.regime_from_configuration(cursor.visible_cfg)
    alpha = fb.rebalance_demand_alpha if regime == "rebalance" else 0.0
    action = fb.reorder_sell_slots(obs, base, cursor.visible_cfg,
                                   demand_alpha=alpha)

    state["route"] = str(state.get("route"))
    ctrl.telemetry["routes"][state["route"]] += 1

    action = fb.m_repay(ctrl, action, state, t)
    action = fb.m_release_pending(ctrl, obs, action, state, t)

    front_items = {str(item) for item in cfg.front_items}
    supply_peak = max(
        (
            float(value)
            for item, value in state.get("opponent_supply", {}).items()
            if item in front_items
        ),
        default=0.0,
    )

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
        action = fb.reorder_sell_slots(
            obs, action, cursor.visible_cfg, demand_alpha=0.25
        )
    if action.get("market", []) != before:
        ctrl.telemetry["front_turns"] += 1

    if t == FINAL_STEP and str(cfg.terminal_rule) != "none":
        action = fb.terminal_market(
            obs, action, rule=str(cfg.terminal_rule), replace=True
        )

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
    """Execute one step's unit commands with event and overflow tracking."""
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
    """Unilateral market execution with exact engine quantity semantics."""
    fb = cursor.fb
    shed = cursor.private["shed"]
    for raw in list(market or [])[:PIN_MAX_ORDERS]:
        if not isinstance(raw, list) or len(raw) < 3:
            continue
        op, item = raw[0], raw[1]
        try:
            qty = int(raw[2])
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        if op == "SELL" and item in PRODUCTS_9:
            for _ in range(qty):
                if int(shed.get(item, 0) or 0) <= 0:
                    break
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
                    break
                cursor.farm["money"] = cursor.money() - quote
                shed[item] = int(shed.get(item, 0) or 0) + 1
                cursor.proj_inventory[item] -= 1

    # Town-consume ticks
    for item in PRODUCTS_9:
        cursor.proj_inventory[item] -= int(fb.demand_at(
            cursor.frozen_shops, int(t), ENGINE_TICK_CONFIG, item))
    # Price refresh
    for item in PRODUCTS_9:
        cursor.proj_prices[item] = int(fb.market_price(
            item, int(cursor.proj_inventory[item])))


def simulate_step(cursor, action, t, offset, is_candidate=False):
    """One full shadow step: units → market → decay + row record."""
    action = copy.deepcopy(action)
    execute_units(cursor, action, t, offset)
    pre_market = dict(cursor.private["shed"])

    # Step 718 Market Liquidation (Change 1):
    # Candidate market orders at 718 are recomputed from post-drop shed state.
    if t == FINAL_STEP and is_candidate:
        from h1_dominance import compute_terminal_liquidation_market
        liq_market = compute_terminal_liquidation_market(
            cursor.fb,
            cursor.project_obs(t),
            action,
            post_drop_shed=pre_market,
        )
        action["market"] = liq_market

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
    """Detailed shadow baseline run over 712–718 (prereg §7/S1)."""
    states = []
    for offset, t in enumerate(range(ENTRY_STEP, FINAL_STEP + 1)):
        if (int(t) + 1) % PIN_TURNS_PER_DAY == 0:
            raise H1Abstain("ABSTAIN_CONFIG",
                            {"pin": "dawn-free-window", "expected": True,
                             "observed": int(t)})
        states.append(cursor.snapshot_state())
        action = predict_baseline_action(cursor, t)
        simulate_step(cursor, action, t, offset, is_candidate=False)
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
        "final_money": float(cursor.farm.get("money", 0.0) or 0.0),
    }


def simulate_schedule(baseline, seat, entry_obs, schedule):
    """Roll out a candidate schedule from entry state."""
    if len(schedule) != FINAL_STEP - ENTRY_STEP + 1:
        raise H1Abstain("ABSTAIN_CONFIG",
                        {"pin": "schedule-len-7", "expected": 7,
                         "observed": len(schedule)})
    cursor = ShadowCursor(baseline, seat, entry_obs, None, None, {},
                          "", [])
    states = []
    for offset, t in enumerate(range(ENTRY_STEP, FINAL_STEP + 1)):
        states.append(cursor.snapshot_state())
        simulate_step(cursor, schedule[offset], t, offset, is_candidate=True)
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
        "final_money": float(cursor.farm.get("money", 0.0) or 0.0),
    }
