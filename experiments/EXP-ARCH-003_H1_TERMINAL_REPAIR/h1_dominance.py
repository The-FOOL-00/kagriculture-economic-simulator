# SPDX-License-Identifier: MIT
"""ARCH-003 H1 dominance and acceptance predicates (prereg §8/D5, §9/D6).

Architectural separation between:
1. D5 SAFETY / DOMINANCE INVARIANT (evaluated on all trial proposals during
   search and re-verified on final_run):
   - Zero overflow across all window steps.
   - Intermediate market solvency on 712–717: candidate pre-market shed
     satisfies all baseline scheduled SELL orders; BUY obligations feasible.
   - Terminal weak dominance at step 718: candidate pre-market shed >= baseline;
     candidate cumulative total deposits across all actors >= baseline;
     candidate cumulative sold >= baseline.
   - No-steal invariant: other actors' acquisitions preserved.

2. ECONOMIC ACCEPTANCE CRITERION (evaluated on final_run vs baseline_run):
   - worker_changed == True
   - terminal money delta > 0 (exact simulator/engine coin accounting)
   - sold delta >= 0 for all PRODUCTS_9
   - some sold delta > 0
   - zero overflow

3. AUTHORITATIVE STEP-718 MARKET LIQUIDATION (Change 1):
   - Single authoritative generator used in shadow simulation, live emission,
     and validation.
   - Frozen baseline `terminal_market(obs, action, rule="collision", replace=True)`
     applied to candidate post-drop shed state.
   - Restrictions: SELL only, PRODUCTS_9 only, 0 < qty <= shed, max orders <= 10,
     no BUY, no speculative orders.
"""

from __future__ import annotations

import copy

from h1_const import (
    BUY_COVERAGE_PER_UNIT,
    ENTRY_STEP,
    FINAL_STEP,
    PIN_MAX_ORDERS,
    PRODUCTS_9,
)


def entry_prices(obs):
    """Frozen integer entry prices (§7/S6): public prices at E, missing→1.

    Returns {product: int ≥ 1}.  Raises ValueError on non-numeric live
    prices (caller maps to ABSTAIN_CONFIG — fail closed).
    """
    market = ((obs or {}).get("market", {}) or {})
    prices = (market.get("prices", {}) or {})
    out = {}
    for item in PRODUCTS_9:
        raw = prices.get(item, 1)
        if isinstance(raw, bool):
            raise ValueError("non-numeric price for %s" % item)
        try:
            number = int(raw)
        except (TypeError, ValueError):
            raise ValueError("non-numeric price for %s" % item)
        out[item] = max(1, number)
    return out


def _ge(left, right):
    """Integer per-product inclusion."""
    for item, value in right.items():
        if int(left.get(item, 0) or 0) < int(value or 0):
            return False
    return True


def total_deposits(row_or_run):
    """Cumulative deposits summed across ALL actors for all products."""
    if "deposited_by_actor" in row_or_run:
        actor_deposits = row_or_run["deposited_by_actor"]
    elif "rows" in row_or_run and row_or_run["rows"]:
        actor_deposits = row_or_run["rows"][-1]["deposited_by_actor"]
    else:
        return {}
    totals = {}
    for actor_dep in actor_deposits:
        for item, qty in actor_dep.items():
            totals[item] = totals.get(item, 0) + int(qty or 0)
    return totals


def scheduled_sell_units(schedule_or_run, offset):
    """Quantities of PRODUCTS_9 scheduled for sale at step offset."""
    if isinstance(schedule_or_run, dict) and "actions" in schedule_or_run:
        actions = schedule_or_run["actions"]
    elif isinstance(schedule_or_run, list):
        actions = schedule_or_run
    else:
        return {}
    if offset >= len(actions):
        return {}
    action = actions[offset]
    sells = {}
    for order in action.get("market", []) or []:
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            item = order[1]
            if item in PRODUCTS_9:
                try:
                    qty = int(order[2])
                    if qty > 0:
                        sells[item] = sells.get(item, 0) + qty
                except (TypeError, ValueError):
                    continue
    return sells


def intermediate_market_solvency(candidate, baseline):
    """Intermediate market solvency invariant on steps 712–717.

    For every offset in 0..5 (steps 712..717) and product p in PRODUCTS_9:
    candidate pre-market shed must satisfy all baseline scheduled SELL
    orders that are executable in baseline execution.
    """
    cand_rows = candidate.get("rows", [])
    base_rows = baseline.get("rows", [])
    if len(cand_rows) < 6 or len(base_rows) < 6:
        return False

    # Check intermediate steps 712–717 (offsets 0 to 5)
    for offset in range(FINAL_STEP - ENTRY_STEP):
        base_sells = scheduled_sell_units(baseline, offset)
        cand_pre_shed = cand_rows[offset].get("pre_market_shed", {})
        base_pre_shed = base_rows[offset].get("pre_market_shed", {})
        for item, req_qty in base_sells.items():
            executable_qty = min(req_qty, int(base_pre_shed.get(item, 0) or 0))
            if int(cand_pre_shed.get(item, 0) or 0) < executable_qty:
                return False
    return True


def terminal_weak_dominance(candidate, baseline):
    """Terminal weak dominance at step 718.

    1. candidate pre-market shed >= baseline pre-market shed for all PRODUCTS_9.
    2. candidate cumulative total deposits (all actors) >= baseline total deposits.
    3. candidate cumulative sold >= baseline cumulative sold for all PRODUCTS_9.
    """
    cand_rows = candidate.get("rows", [])
    base_rows = baseline.get("rows", [])
    if not cand_rows or not base_rows:
        return False

    cand_term_row = cand_rows[-1]
    base_term_row = base_rows[-1]

    # 1. Pre-market shed weak dominance
    if not _ge(cand_term_row.get("pre_market_shed", {}),
               base_term_row.get("pre_market_shed", {})):
        return False

    # 2. Cumulative total deposits across all actors
    cand_deposits = total_deposits(cand_term_row)
    base_deposits = total_deposits(base_term_row)
    if not _ge(cand_deposits, base_deposits):
        return False

    # 3. Cumulative sold units weak dominance
    cand_sold = candidate.get("sold", cand_term_row.get("sold", {}))
    base_sold = baseline.get("sold", base_term_row.get("sold", {}))
    if not _ge(cand_sold, base_sold):
        return False

    return True


def dominates(candidate, baseline):
    """D5 Safety / Dominance invariant (prereg §8/D5).

    Enforces:
    1. Zero overflow across all simulated steps.
    2. Intermediate market solvency on 712–717.
    3. Terminal weak dominance at step 718 on shed, deposits, and sales.
    """
    if int(candidate.get("overflow_units", 0) or 0) != 0:
        return False
    if not intermediate_market_solvency(candidate, baseline):
        return False
    if not terminal_weak_dominance(candidate, baseline):
        return False
    return True


def stock_value(run, prices):
    """Strict-gain value term at frozen entry prices (§8.1(3)).

    Σ(sold + final_shed) × priceE over the 9 products. Integer-exact.
    Used for proposal ranking and intermediate search guidance.
    """
    shed = (run.get("private", {}) or {}).get("shed", {}) or {}
    sold = run.get("sold", {}) or {}
    total = 0
    for item in PRODUCTS_9:
        units = int(sold.get(item, 0) or 0) + int(shed.get(item, 0) or 0)
        total += units * int(prices.get(item, 1))
    return total


def no_steal_pass(trial_run, best_run, actor):
    """No-steal adoption gate (prereg §8.1(4)).

    Every HARVEST/COLLECT acquisition by OTHER actors in the current
    best run must still occur (same cell, op, actor, ≥ quantity) in the
    trial.
    """
    required = {}
    for event in best_run.get("events", []) or []:
        if "acquired" in event and event.get("actor") != actor:
            key = (tuple(event["xy"]), event["op"], event["actor"])
            required[key] = event["acquired"]
    acquired = {}
    for event in trial_run.get("events", []) or []:
        if "acquired" in event:
            key = (tuple(event["xy"]), event["op"], event["actor"])
            dst = acquired.setdefault(key, {})
            for item, amount in event["acquired"].items():
                dst[item] = dst.get(item, 0) + amount
    for key, want in required.items():
        if not _ge(acquired.get(key, {}), want):
            return False
    return True


def worker_commands(action, n):
    """First-n worker commands (farmer + hands prefix)."""
    hands = action.get("hands", []) or []
    return [action.get("farmer", ["PASS"]), *hands][:n]


def acceptance(final_run, baseline_run, baseline_schedule):
    """Acceptance conjunction: economic adoption criterion (prereg §8.1(5)).

    Requires:
    1. worker_changed == True
    2. final_run_money - baseline_run_money > 0 (exact simulator/engine money)
    3. sold_delta[p] >= 0 for all p in PRODUCTS_9
    4. some sold_delta[p] > 0
    5. final_run overflow == 0
    """
    n = len(final_run["rows"][-1]["deposited_by_actor"])
    changed = any(
        worker_commands(new, n) != worker_commands(old, n)
        for new, old in zip(final_run["actions"], baseline_schedule)
    )

    final_money = float(final_run.get("final_money",
                                      (final_run.get("farm") or {}).get("money", 0.0)) or 0.0)
    baseline_money = float(baseline_run.get("final_money",
                                            (baseline_run.get("farm") or {}).get("money", 0.0)) or 0.0)
    money_delta = final_money - baseline_money
    money_gain = money_delta > 0.0

    delta = {
        item: int(final_run["sold"].get(item, 0) or 0)
        - int(baseline_run["sold"].get(item, 0) or 0)
        for item in PRODUCTS_9
    }
    values = list(delta.values())
    all_nonnegative = all(v >= 0 for v in values)
    some_positive = any(v > 0 for v in values)
    zero_overflow = int(final_run.get("overflow_units", 0) or 0) == 0

    conjuncts = {
        "worker_change": bool(changed),
        "money_delta": float(money_delta),
        "money_gain": bool(money_gain),
        "sold_delta_min": min(values) if values else 0,
        "sold_delta_max": max(values) if values else 0,
        "all_nonnegative": bool(all_nonnegative),
        "some_positive": bool(some_positive),
        "zero_overflow": bool(zero_overflow),
    }
    accepted = bool(
        changed
        and money_gain
        and all_nonnegative
        and some_positive
        and zero_overflow
    )
    return accepted, conjuncts, delta


def compute_terminal_liquidation_market(baseline, obs, action, post_drop_shed=None):
    """Authoritative step-718 liquidation market generator (Change 1).

    Applies the frozen baseline's `terminal_market(obs, action, rule='collision',
    replace=True)` to the candidate's post-worker-action / post-drop shed state.

    Enforces all preregistered restrictions:
    - SELL only
    - PRODUCTS_9 only
    - quantity positive integer
    - quantity no greater than candidate available shed
    - max market orders = PIN_MAX_ORDERS
    - no BUY
    - no speculative orders
    """
    obs_for_market = copy.deepcopy(obs)
    if post_drop_shed is not None:
        obs_for_market.setdefault("private", {})["shed"] = {
            k: max(0, int(v or 0)) for k, v in post_drop_shed.items()
        }

    # Call frozen baseline terminal_market
    recomputed = baseline.terminal_market(
        obs_for_market,
        copy.deepcopy(action),
        rule="collision",
        replace=True,
    )
    raw_market = recomputed.get("market", []) or []

    # Apply strict restriction filter
    shed_now = dict((obs_for_market.get("private", {}) or {}).get("shed", {}) or {})
    valid_orders = []
    for order in raw_market:
        if len(valid_orders) >= PIN_MAX_ORDERS:
            break
        if not isinstance(order, list) or len(order) < 3:
            continue
        op, item = order[0], order[1]
        if op != "SELL":
            continue
        if item not in PRODUCTS_9:
            continue
        try:
            qty = int(order[2])
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        avail = int(shed_now.get(item, 0) or 0)
        final_qty = min(qty, avail)
        if final_qty > 0:
            valid_orders.append(["SELL", item, final_qty])

    return valid_orders[:PIN_MAX_ORDERS]


def markets_712_717_verbatim(plan_actions, baseline_schedule):
    """Verifies that market orders on steps 712–717 are bit-identical."""
    for offset in range(FINAL_STEP - ENTRY_STEP):
        if plan_actions[offset].get("market", []) != baseline_schedule[offset].get("market", []):
            return False
    return True


def window_buy_units(schedule):
    """Total window BUY units U over 712–718 (prereg §8.2/H2)."""
    total = 0
    items = set()
    for action in schedule:
        for order in action.get("market", []) or []:
            if (
                isinstance(order, list)
                and len(order) >= 3
                and order[0] == "BUY_PRODUCT"
            ):
                try:
                    qty = int(order[2])
                except (TypeError, ValueError):
                    continue
                if qty > 0:
                    total += qty
                    items.add(order[1])
    return total, sorted(str(i) for i in items)


def coverage_required(units):
    """G4 gate: money_at_E ≥ $125 × U (prereg §8.2/H2)."""
    return BUY_COVERAGE_PER_UNIT * max(0, int(units))
