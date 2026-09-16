# SPDX-License-Identifier: MIT
"""ARCH-003 H1 candidate search (prereg §7/D4, §9/D6).

Mirror of Dmitrii ``_proposals`` + ``plan_terminal`` search structure
at the frozen live settings (128 simulations, 1 pass, ≤8 proposals/worker),
with the preregistered ARCH-003 adaptations:
- Step-718 candidate liquidation market recomputation (Change 1).
- Relaxed intermediate-solvency and terminal-dominance predicate D5 (Change 2).
- Terminal money and sales gain economic acceptance criterion (Change 3).
- Strict search preservation: identical 128 budget, 1 pass, 8 proposals/worker,
  identical proposal generator and ordering, integer entry prices, deterministic
  tie-breaking.
"""

from __future__ import annotations

import copy
from time import perf_counter

import h1_units as _U
from h1_const import (
    DIRECT_RETURN_RESERVE,
    ENTRY_STEP,
    FINAL_STEP,
    MAX_SIMULATIONS,
    PASSES,
    PROPOSALS_PER_ACTOR,
    START_OFFSETS,
    TOP_PAIR_HALF,
    TOP_SINGLES,
)
from h1_dominance import (
    acceptance,
    dominates,
    markets_712_717_verbatim,
    no_steal_pass,
    stock_value,
)
from h1_shadow import simulate_schedule
from h1_telemetry import H1Abstain


def _walk(start, end):
    """X-first Manhattan walk (mirror terminal_planner.py:228–233)."""
    x, y = start
    tx, ty = end
    return ([["EAST"]] * max(0, tx - x) + [["WEST"]] * max(0, x - tx)
            + [["SOUTH"]] * max(0, ty - y) + [["NORTH"]] * max(0, y - ty))


def _return(pos):
    """Walk to nearest shed-access tile + DROP (mirror :235–238)."""
    targets = _U._shed_access_tiles(10)
    target = min(targets, key=lambda xy: (
        abs(pos[0] - xy[0]) + abs(pos[1] - xy[1]), targets.index(xy)))
    return _walk(pos, target) + [["DROP"]]


def _clone_schedule(schedule):
    """Command-level-deep schedule copy (mirror :65–76)."""
    result = []
    for action in schedule:
        value = dict(action)
        if "farmer" in action:
            value["farmer"] = list(action["farmer"])
        for key in ("hands", "market"):
            if key in action:
                value[key] = [list(command) for command in action[key]]
        result.append(value)
    return result


def proposals(best, actor, prices):
    """Ranked proposals for one worker (mirror _proposals, §7/S1–S5).

    Bundle sources: standing-yield HARVESTs (mature crops, any animal
    yield>0) + COLLECT_FERTILIZER on flagged animal tiles, excluding
    cells/ops owned by another actor in the current best run (baseline
    acquisitions ∪ adopted siblings).  Variants: carry closure + top-6
    singles + top-3×top-3 pairs; 2 direct reserves ranked first; DIR-
    capped at ≤8/worker across ALL offsets (prereg D4).
    """
    owners = {}
    for event in best.get("events", []) or []:
        if "acquired" in event:
            owners.setdefault(
                (tuple(event["xy"]), event["op"]), set()).add(
                    event["actor"])
    ranked = []
    seen = set()
    horizon = len(best["rows"])
    for offset in START_OFFSETS:
        if offset >= horizon:
            break
        farm, private = best["states"][offset]
        pos = tuple(farm["farmer"] if actor == 0
                    else farm["hands"][actor - 1])
        inventory = private["inventories"][actor]
        carried = sum(prices.get(item, 0) * count
                      for item, count in inventory.items())
        prefix = best["rows"][offset - 1]["deposited_by_actor"][actor] \
            if offset else {}
        future = best["rows"][-1]["deposited_by_actor"][actor]
        obligation = sum(prices.get(item, 0) * (
            count - prefix.get(item, 0))
            for item, count in future.items())
        bundles = []
        for y, row in enumerate(farm["tiles"]):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict):
                    continue
                xy, operations, value = (x, y), [], 0
                if tile.get("yield_units", 0) > 0:
                    if tile.get("kind") == "PLANT":
                        item = tile.get("crop")
                    elif "animal" in tile:
                        item = _U.ANIMALS.get(
                            tile.get("animal"), {}).get("product")
                    else:
                        item = None
                    mature = False
                    if item in prices:
                        if "animal" in tile:
                            mature = True
                        elif item in _U.CROPS:
                            mature = (
                                (ENTRY_STEP + offset) // 24
                                - int(tile.get("planted_day", 0))
                                >= _U.CROPS[item]["first_yield_day"])
                    if mature and not (
                            owners.get((xy, "HARVEST"), set()) - {actor}):
                        operations.append(["HARVEST"])
                        value += prices[item] * tile["yield_units"]
                if (tile.get("fertilizer_available") and "animal" in tile
                        and not (owners.get((xy, "COLLECT_FERTILIZER"),
                                            set()) - {actor})):
                    operations.append(["COLLECT_FERTILIZER"])
                    value += prices["FERTILIZER"]
                if operations:
                    distance = (len(_walk(pos, xy)) + len(operations)
                                + len(_return(xy)))
                    if distance <= horizon - offset:
                        bundles.append((xy, operations, value, distance))
        # T2: bundle rank key (-value/distance, -value, xy).
        bundles.sort(key=lambda b: (-b[2] / b[3], -b[2], b[0]))
        variants = [([], carried)] if carried else []
        for xy, ops, value, _ in bundles[:TOP_SINGLES]:
            variants.append(([(xy, ops)], carried + value))
        for first in bundles[:TOP_PAIR_HALF]:
            for second in bundles[:TOP_PAIR_HALF]:
                if first[0] != second[0]:
                    variants.append((
                        [(first[0], first[1]), (second[0], second[1])],
                        carried + first[2] + second[2]))
        for stops, value in variants:
            route, cursor = [], pos
            for xy, ops in stops:
                route += _walk(cursor, xy) + ops
                cursor = xy
            route += _return(cursor)
            if len(route) > horizon - offset:
                continue
            route += [["PASS"]] * (horizon - offset - len(route))
            key = (offset, tuple(tuple(c) for c in route))
            if key not in seen:
                seen.add(key)
                ranked.append(
                    (value - obligation, offset, route, len(stops)))
    # T3: proposal rank key (-net_value, offset, route-tuple-lex).
    ranked.sort(key=lambda p: (-p[0], p[1],
                               tuple(tuple(c) for c in p[2])))
    # T5: two direct-return reserves ranked first (mirror :301).
    direct = [p for p in ranked if p[3] == 0 and p[0] > 0][
        :DIRECT_RETURN_RESERVE]
    chosen = direct + [p for p in ranked if p not in direct]
    return chosen[:PROPOSALS_PER_ACTOR]


def plan_terminal(baseline, seat, entry_obs, baseline_schedule,
                  baseline_run, prices):
    """Worker-by-worker single-pass search (mirror plan_terminal loop).

    Returns the adopted plan record. Raises ``H1Abstain`` whenever no
    plan is adopted.
    """
    begun = perf_counter()
    if int((entry_obs or {}).get("step", -1)) != ENTRY_STEP:
        raise H1Abstain("ABSTAIN_CONFIG",
                        {"pin": "planning-step-712", "expected": ENTRY_STEP,
                         "observed": (entry_obs or {}).get("step")})
    if len(baseline_schedule) != FINAL_STEP - ENTRY_STEP + 1:
        raise H1Abstain("ABSTAIN_CONFIG",
                        {"pin": "schedule-len-7", "expected": 7,
                         "observed": len(baseline_schedule)})
    current, best = _clone_schedule(baseline_schedule), baseline_run
    baseline_value = best_value = stock_value(baseline_run, prices)
    changes, simulations = [], 0
    trials_evaluated = 0
    blocked_dominance = False
    blocked_nosteal = False
    n = len(baseline_run["private"]["inventories"])

    for _sweep in range(PASSES):
        improved = False
        for actor in range(n):
            winner = None
            for _, offset, route, bundle_count in proposals(
                    best, actor, prices):
                if simulations >= MAX_SIMULATIONS:
                    break
                trial = _clone_schedule(current)
                for i, command in enumerate(route, offset):
                    if actor == 0:
                        trial[i]["farmer"] = command
                    else:
                        trial[i].setdefault("hands", [])
                        while len(trial[i]["hands"]) < n - 1:
                            trial[i]["hands"].append(["PASS"])
                        trial[i]["hands"][actor - 1] = command
                evaluated = simulate_schedule(
                    baseline, seat, entry_obs, trial)
                simulations += 1
                trials_evaluated += 1
                score = stock_value(evaluated, prices)

                # D5 Safety/Dominance check on trial vs baseline_run
                if score > best_value and dominates(evaluated, baseline_run):
                    if no_steal_pass(evaluated, best, actor):
                        winner = (trial, offset, bundle_count)
                        best_value = score
                    else:
                        blocked_nosteal = True
                elif score > best_value:
                    blocked_dominance = True

            if winner:
                current, offset, bundle_count = winner
                best = simulate_schedule(
                    baseline, seat, entry_obs, current)
                changes.append({"actor": actor,
                                "from_step": ENTRY_STEP + offset,
                                "resource_bundles": bundle_count,
                                "estimated_stock_value": best_value})
                improved = True
            if simulations >= MAX_SIMULATIONS:
                break
        if not improved or simulations >= MAX_SIMULATIONS:
            break

    planning_ms = (perf_counter() - begun) * 1000.0

    if not changes or best_value <= baseline_value:
        if simulations >= MAX_SIMULATIONS:
            raise H1Abstain("ABSTAIN_BUDGET",
                            {"simulations": simulations})
        if blocked_nosteal:
            raise H1Abstain("ABSTAIN_NOSTEAL", {"stage": "trial"})
        if blocked_dominance:
            raise H1Abstain("ABSTAIN_DOMINANCE", {"stage": "trial"})
        raise H1Abstain("ABSTAIN_NO_GAIN",
                        {"trials_evaluated": trials_evaluated})

    # Final re-simulation of full adopted candidate schedule
    final = simulate_schedule(baseline, seat, entry_obs, current)

    # Re-verify D5 Safety / Dominance on final run vs baseline
    if not dominates(final, baseline_run):
        raise H1Abstain("ABSTAIN_DOMINANCE", {"stage": "final_resim"})

    # Evaluate Economic Acceptance Conjunction (Change 3)
    ok, conjuncts, delta = acceptance(
        final, baseline_run, baseline_schedule)
    cert = markets_712_717_verbatim(final["actions"], baseline_schedule)

    if not (ok and cert):
        raise H1Abstain("ABSTAIN_ACCEPT", {
            "worker_change": conjuncts["worker_change"],
            "money_gain": conjuncts["money_gain"],
            "money_delta": conjuncts["money_delta"],
            "sold_delta_min": conjuncts["sold_delta_min"],
            "sold_delta_max": conjuncts["sold_delta_max"],
            "markets_verbatim": bool(cert),
            "zero_overflow": conjuncts["zero_overflow"],
        })

    return {
        "accepted": True,
        "baseline": _clone_schedule(baseline_schedule),
        "actions": final["actions"],
        "expected_states": final["states"][:-1],
        "simulations": simulations,
        "planning_ms": planning_ms,
        "changes": changes,
        "changed_workers": sorted({c["actor"] for c in changes}),
        "baseline_run": baseline_run,
        "final_run": final,
        "sold_unit_delta": delta,
        "money_delta": conjuncts["money_delta"],
        "stock_value_gain": best_value - baseline_value,
        "candidate_overflow": final["overflow_units"],
        "baseline_overflow": baseline_run["overflow_units"],
        "markets_verbatim": True,
        "market_718_liquidation": final["actions"][-1].get("market", []),
    }
