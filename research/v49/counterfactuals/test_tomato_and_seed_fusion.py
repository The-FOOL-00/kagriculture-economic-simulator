#!/usr/bin/env python3
"""Evaluate M1 (Late Seed Cap) + M2 (Counter T-B Tomato Price EV Gate) against V48.

Evaluates across 64 fresh seeds x 2 seats = 128 paired legs.
Tests:
1. BASE_V48
2. M1_SEED_CAP (E402)
3. M2_TOMATO_EV (Counter T-B)
4. M1_M2_FUSION (V49 Challenger Candidate)
"""

from __future__ import annotations
import concurrent.futures
import copy
import json
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v48_challenger.main as v48_mod
import candidates.v44_economic_portfolio.main as v44_mod
import research.v47.elite_corpus.agents.thomastschinkel_2945.main as m2945

SEEDS = [250200 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


# ===========================================================================
# MECHANISM M1: E402 Late Seed Cap
# ===========================================================================
_E402_CACHE = {}

def _e402_remaining(native, step, chassis):
    route = native.get('route', 0)
    key = (route, step)
    if key in _E402_CACHE:
        return _E402_CACHE[key]
    need = 0
    for t in range(step + 1, 719):
        tape = chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        need += sum(1 for c in [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
                    if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
    _E402_CACHE[key] = need
    return need


def apply_m1_late_seed_cap(observation, action, chassis):
    step = int(observation['step'])
    if step < 624:
        return action
    market = action.get('market', [])
    if not any(len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in ('WHEAT', 'CARROT') for o in market):
        return action
    seat = int(observation['player'])
    native = chassis.players[seat]
    remaining = _e402_remaining(native, step, chassis)
    # Queued retries
    remaining += sum(1 for queue in native.get('pending', {}).values() for pos, c in queue
                     if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
    units = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
    seeds = observation.get('private', {}).get('seeds', {}) or {}
    available = {p: max(0, int(seeds.get(p, 0)) - sum(c[:2] == ['PLANT', p] for c in units)) for p in ('WHEAT', 'CARROT')}
    out = []
    changed = False
    for o in market:
        if len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in available:
            p = o[1]
            qty = max(0, int(o[2]))
            keep = min(qty, max(0, remaining - available[p]))
            available[p] += keep
            if keep < qty:
                changed = True
                o = [o[0], p, keep] if keep else []
        out.append(o)
    if changed:
        return dict(action, market=[o for o in out if o])
    return action


# ===========================================================================
# MECHANISM M2: Counter T-B Tomato EV Gate
# ===========================================================================
_CXTB_MIN_REVENUE = 9000
_CXTB_THEIR_UNITS = 0.75
_CXTB_DRAIN_SLACK = 2.4
_CXTB_OUR_UNITS = 20
_CXTB_HARVEST_DAYS = (26, 27, 28, 29)

def _cxtb_their_supply(obs, upto):
    supply = {}
    them = obs['farms'][1 - obs['player']]
    for row in them.get('tiles', []):
        for t in row:
            if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                for d in range(int(t.get('planted_day', 0)) + 8, upto + 1):
                    supply[d] = supply.get(d, 0.0) + _CXTB_THEIR_UNITS
    return supply

def _cxtb_expected_revenue(obs):
    inventory = float(obs['market']['inventory']['TOMATO'])
    day = int(obs['step']) // 24
    shops = float(sum(s in ('PIZZA_SHOP', 'FARMERS_MARKET') for s in obs['town']['unlocked_shops']))
    pending = {22: 0.25, 24: 0.25}
    last = max(_CXTB_HARVEST_DAYS)
    theirs = _cxtb_their_supply(obs, last)
    revenue = 0.0
    for d in range(day, last + 1):
        shops += pending.get(d, 0.0)
        inventory -= 1.0 + 6.0 * shops - _CXTB_DRAIN_SLACK
        inventory += theirs.get(d, 0.0)
        if d in _CXTB_HARVEST_DAYS:
            for _ in range(_CXTB_OUR_UNITS):
                revenue += v48_mod._r37_market_price('TOMATO', int(round(inventory)))
                inventory += 1
    return revenue

def cxtb_qualifies(obs, native):
    farm = obs['farms'][obs['player']]
    if len(farm.get('tiles', [])) != 10 or set(farm.get('unlocked_quadrants', [])) != {'NW', 'NE', 'SW'}:
        return False
    if farm.get('money', 0) < 12000:
        return False
    if _cxtb_expected_revenue(obs) < _CXTB_MIN_REVENUE:
        return False
    tiles = farm.get('tiles', [])
    if any(tiles[y][x] != 'LOCKED' for y in (5, 6) for x in range(5, 10)):
        return False
    private = obs.get('private', {})
    if private.get('seeds', {}).get('TOMATO', 0) or private.get('shed', {}).get('TOMATO', 0):
        return False
    if any(isinstance(t, dict) and t.get('crop') == 'TOMATO' for row in tiles for t in row):
        return False
    return True


# ===========================================================================
# Execution Runner
# ===========================================================================
def step_agent(obs, mode: str):
    # If mode includes M2, patch _v219_qualifies temporarily
    orig_qual = v48_mod._v219_qualifies
    if "TOMATO" in mode or "FUSION" in mode:
        v48_mod._v219_qualifies = cxtb_qualifies
    try:
        act = v48_mod.agent(obs)
    finally:
        v48_mod._v219_qualifies = orig_qual

    chassis = v48_mod._IMPL.chassis
    if "SEED_CAP" in mode or "FUSION" in mode:
        act = apply_m1_late_seed_cap(obs, act, chassis)
    return act


def run_paired_leg(args: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, variant = args
    opp_seat = 1 - seat

    # 1. Base V48 vs V44
    sim1 = FastKagricultureSim(seed=seed)
    obs1 = sim1.reset(seed=seed)
    for _ in range(719):
        a0 = step_agent(obs1[seat], "BASE_V48")
        a1 = v44_mod.agent(obs1[opp_seat])
        actions = [a0, a1] if seat == 0 else [a1, a0]
        obs1, _, _, _ = sim1.step(actions)
    cash_base = float(obs1[seat]["farms"][seat]["money"])
    cash_opp1 = float(obs1[opp_seat]["farms"][opp_seat]["money"])

    # 2. Candidate Variant vs V44
    sim2 = FastKagricultureSim(seed=seed)
    obs2 = sim2.reset(seed=seed)
    for _ in range(719):
        a0 = step_agent(obs2[seat], variant)
        a1 = v44_mod.agent(obs2[opp_seat])
        actions = [a0, a1] if seat == 0 else [a1, a0]
        obs2, _, _, _ = sim2.step(actions)
    cash_cand = float(obs2[seat]["farms"][seat]["money"])
    cash_opp2 = float(obs2[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "variant": variant,
        "cash_base": cash_base,
        "cash_cand": cash_cand,
        "delta": cash_cand - cash_base,
        "win_base": cash_base > cash_opp1,
        "win_cand": cash_cand > cash_opp2,
    }


def main():
    variants = ["M1_SEED_CAP", "M2_TOMATO_EV", "M1_M2_FUSION"]
    print("Testing M1 (Late Seed Cap), M2 (Tomato EV Gate), and Fusion across 64 seeds x 2 seats = 128 legs...")

    summary = {}
    for var in variants:
        tasks = [(s, seat, var) for s in SEEDS for seat in (0, 1)]
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            res = list(executor.map(run_paired_leg, tasks))

        deltas = [r["delta"] for r in res]
        wins_base = sum(r["win_base"] for r in res)
        wins_cand = sum(r["win_cand"] for r in res)
        rescues = sum(1 for r in res if not r["win_base"] and r["win_cand"])
        casualties = sum(1 for r in res if r["win_base"] and not r["win_cand"])

        summary[var] = {
            "legs": len(res),
            "win_rate_base": float(wins_base / len(res)),
            "win_rate_cand": float(wins_cand / len(res)),
            "mean_delta": float(np.mean(deltas)),
            "median_delta": float(np.median(deltas)),
            "ci_95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
            "rescues": rescues,
            "casualties": casualties,
        }
        print(f"Variant: {var:15} | Cand WR: {wins_cand/len(res)*100:5.1f}% (Base: {wins_base/len(res)*100:5.1f}%) | "
              f"Mean Delta: {np.mean(deltas):+7.2f} (95% CI [{np.percentile(deltas, 2.5):+7.2f}, {np.percentile(deltas, 97.5):+7.2f}]) | "
              f"Median: {np.median(deltas):+6.2f} | Rescues: {rescues} | Casualties: {casualties}")

    out_file = os.path.join(REPO_ROOT, "research", "v49", "counterfactuals", "tomato_seed_fusion.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved results to {out_file}")


if __name__ == "__main__":
    main()
