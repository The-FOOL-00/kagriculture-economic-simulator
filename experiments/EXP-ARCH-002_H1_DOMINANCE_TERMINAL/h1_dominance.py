# SPDX-License-Identifier: MIT
"""ARCH-002 H1 dominance predicate (prereg §8/D5, §9/D6).

Mirror of Dmitrii ``dominates`` / ``_value`` / adoption gate /
acceptance conjunction (terminal_planner.py:205–220, 223–225, 341–391)
with the preregistered adaptations:

* integer frozen entry prices (§7/S6 — stricter than Dmitrii floats);
* markets-verbatim certificate adapted to sparse markets (§8.1(6));
* BUY_PRODUCT modeled with the entry-money coverage gate (§8.2/H2);
* no step-718 recompute anywhere (D3 verbatim passthrough).
"""

from __future__ import annotations

from h1_const import (
    BUY_COVERAGE_PER_UNIT,
    ENTRY_STEP,
    FINAL_STEP,
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
    """Integer per-product inclusion (mirror terminal_planner.py:205)."""
    for item, value in right.items():
        if int(left.get(item, 0) or 0) < int(value or 0):
            return False
    return True


def dominates(candidate, baseline):
    """Row-wise prefix dominance (prereg §8.1(1–2)).

    Candidate overflow ⇒ fail.  For EVERY row: pre-market shed ⊇,
    cumulative sold ⊇, per-actor cumulative deposits ⊇ (integer ⊇).
    Mirror of terminal_planner.py:209–220.
    """
    if int(candidate.get("overflow_units", 0) or 0):
        return False
    for new, old in zip(candidate["rows"], baseline["rows"]):
        if not _ge(new["pre_market_shed"], old["pre_market_shed"]):
            return False
        if not _ge(new["sold"], old["sold"]):
            return False
        new_dep = new["deposited_by_actor"]
        old_dep = old["deposited_by_actor"]
        if len(new_dep) != len(old_dep):
            return False
        for left, right in zip(new_dep, old_dep):
            if not _ge(left, right):
                return False
    return True


def stock_value(run, prices):
    """Strict-gain value term at frozen entry prices (§8.1(3)).

    Σ(sold + final_shed) × priceE over the 9 products.  Integer-exact
    (mirror of terminal_planner.py:223–225 with prereg integer prices).
    """
    shed = (run.get("private", {}) or {}).get("shed", {}) or {}
    sold = run.get("sold", {}) or {}
    total = 0
    for item in PRODUCTS_9:
        units = int(sold.get(item, 0) or 0) + int(shed.get(item, 0) or 0)
        total += units * int(prices[item])
    return total


def no_steal_pass(trial_run, best_run, actor):
    """No-steal adoption gate (prereg §8.1(4)).

    Every HARVEST/COLLECT acquisition by OTHER actors in the current
    best run must still occur (same cell, op, actor, ≥ quantity) in the
    trial.  Mirror of terminal_planner.py:342–353.
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
    """Acceptance conjunction (prereg §8.1(5)) + diagnostics.

    changed-workers non-empty AND some actor deposited strictly more of
    some product AND every sold delta ≥ 0 AND some sold delta > 0.
    (Final re-sim dominance + markets-verbatim cert are evaluated by
    the caller alongside.)  Mirror of terminal_planner.py:374–381.
    """
    n = len(final_run["rows"][-1]["deposited_by_actor"])
    changed = any(
        worker_commands(new, n) != worker_commands(old, n)
        for new, old in zip(final_run["actions"], baseline_schedule)
    )
    final_dep = final_run["rows"][-1]["deposited_by_actor"]
    base_dep = baseline_run["rows"][-1]["deposited_by_actor"]
    deposited_gain = any(
        int(actor_new.get(item, 0) or 0) > int(actor_old.get(item, 0) or 0)
        for actor_new, actor_old in zip(final_dep, base_dep)
        for item in PRODUCTS_9
    )
    delta = {
        item: int(final_run["sold"].get(item, 0) or 0)
        - int(baseline_run["sold"].get(item, 0) or 0)
        for item in PRODUCTS_9
    }
    values = list(delta.values())
    conjuncts = {
        "worker_change": bool(changed),
        "deposited_gain": bool(deposited_gain),
        "sold_delta_min": min(values),
        "sold_delta_max": max(values),
        "all_nonnegative": all(v >= 0 for v in values),
        "some_positive": any(v > 0 for v in values),
    }
    accepted = bool(
        changed and deposited_gain and conjuncts["all_nonnegative"]
        and conjuncts["some_positive"]
    )
    return accepted, conjuncts, delta


def markets_verbatim(plan_actions, baseline_schedule):
    """Markets-verbatim certificate 712–717 (prereg §8.1(6)).

    Element-wise market equality on steps E–717 (adapts Dmitrii's
    ``markets_712_717_unchanged`` to sparse markets; transplant H1).
    """
    for offset in range(FINAL_STEP - ENTRY_STEP):
        if plan_actions[offset].get("market", []) != baseline_schedule[
            offset
        ].get("market", []):
            return False
    return True


def window_buy_units(schedule):
    """Total window BUY units U over 712–718 (prereg §8.2/H2).

    Counts every BUY_PRODUCT unit with a positive integer quantity in
    the shadow baseline schedule.  Returns (U, items) where items is
    the sorted set of BUY-targeted products (FERTILIZER presence is a
    conservative abstain trigger — see h1_agent G3/ DISCREPANCY-1).
    """
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
