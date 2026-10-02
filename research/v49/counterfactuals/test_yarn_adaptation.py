#!/usr/bin/env python3
"""Evaluate YARN_STORE animal adaptation mechanism on fresh seeds and loss cohort.

Tests:
1. Fresh cohort: 64 seeds x 2 seats = 128 paired legs
2. Known Yarn Loss cohort: seeds where YARN_STORE unlocked and caused V48 loss
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
import research.v47.elite_corpus.agents.tetsutani_pasture.main as tet_mod

FRESH_SEEDS = [250100 + i for i in range(64)]
LOSS_SEEDS = [249877, 249920, 249865, 249884]

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in FRESH_SEEDS + LOSS_SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def apply_yarn_herd_adapt(observation, action):
    step = int(observation.get("step", 0))
    # Days 8-11: steps 192..264
    day = step // 24
    if not (8 <= day <= 11):
        return action
    shops = list((observation.get("town") or {}).get("unlocked_shops") or [])
    if "YARN_STORE" not in shops:
        return action
    market = action.get("market") or []
    if not market:
        return action
    changed = False
    out = []
    for o in market:
        if len(o) >= 3 and o[0] == "BUY_ANIMAL":
            kind = o[1]
            if kind in ("COW", "GOOSE"):
                # Swap to SHEEP if yarn is unlocked!
                changed = True
                o = ["BUY_ANIMAL", "SHEEP", o[2]]
        out.append(o)
    if changed:
        return dict(action, market=out)
    return action


def apply_m1_seed_cap(observation, action, chassis):
    step = int(observation['step'])
    if step < 624:
        return action
    market = action.get('market', [])
    if not any(len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in ('WHEAT', 'CARROT') for o in market):
        return action
    seat = int(observation['player'])
    native = chassis.players[seat]
    route = native.get('route', 0)
    need = 0
    for t in range(step + 1, 719):
        tape = chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        need += sum(1 for c in [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
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
            keep = min(qty, max(0, need - available[p]))
            available[p] += keep
            if keep < qty:
                changed = True
                o = [o[0], p, keep] if keep else []
        out.append(o)
    if changed:
        return dict(action, market=[o for o in out if o])
    return action


def step_agent(obs, mode: str):
    act = v48_mod.agent(obs)
    chassis = v48_mod._IMPL.chassis
    if mode == "BASE_V48":
        return act
    elif mode == "YARN_HERD":
        return apply_yarn_herd_adapt(obs, act)
    elif mode == "M1_SEED_CAP":
        return apply_m1_seed_cap(obs, act, chassis)
    elif mode == "V49_COMBINED":
        act = apply_yarn_herd_adapt(obs, act)
        return apply_m1_seed_cap(obs, act, chassis)
    return act


def sim_match(args):
    seed, seat, opp_name, mode = args
    opp_seat = 1 - seat
    opp_agent = v44_mod.agent if opp_name == "V44" else tet_mod.agent

    # 1. Base V48
    sim1 = FastKagricultureSim(seed=seed)
    obs1 = sim1.reset(seed=seed)
    for _ in range(719):
        a0 = step_agent(obs1[seat], "BASE_V48")
        a1 = opp_agent(obs1[opp_seat])
        actions = [a0, a1] if seat == 0 else [a1, a0]
        obs1, _, _, _ = sim1.step(actions)
    cash_base = float(obs1[seat]["farms"][seat]["money"])
    cash_opp1 = float(obs1[opp_seat]["farms"][opp_seat]["money"])

    # 2. Candidate Mode
    sim2 = FastKagricultureSim(seed=seed)
    obs2 = sim2.reset(seed=seed)
    for _ in range(719):
        a0 = step_agent(obs2[seat], mode)
        a1 = opp_agent(obs2[opp_seat])
        actions = [a0, a1] if seat == 0 else [a1, a0]
        obs2, _, _, _ = sim2.step(actions)
    cash_cand = float(obs2[seat]["farms"][seat]["money"])
    cash_opp2 = float(obs2[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "mode": mode,
        "cash_base": cash_base,
        "cash_cand": cash_cand,
        "delta": cash_cand - cash_base,
        "win_base": cash_base > cash_opp1,
        "win_cand": cash_cand > cash_opp2,
    }


def main():
    print("Evaluating YARN_STORE adaptation on known loss cohort...")
    loss_tasks = [(s, seat, "Tetsutani" if s in (249865, 249884) else "V44", "YARN_HERD")
                  for s in LOSS_SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        loss_res = list(executor.map(sim_match, loss_tasks))

    for r in loss_res:
        status = "RESCUE!" if (not r["win_base"] and r["win_cand"]) else ("WIN" if r["win_cand"] else "LOSS")
        print(f"  Loss Seed {r['seed']} (seat {r['seat']}, vs {r['opp']}): Delta = {r['delta']:+7.1f} | BaseWin={r['win_base']} -> CandWin={r['win_cand']} [{status}]")

    print("\nEvaluating V49_COMBINED (M1 Late Seed Cap + YARN Adaptation) on 64 fresh seeds x 2 seats = 128 legs vs V44...")
    fresh_tasks = [(s, seat, "V44", "V49_COMBINED") for s in FRESH_SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        fresh_res = list(executor.map(sim_match, fresh_tasks))

    deltas = [r["delta"] for r in fresh_res]
    wins_base = sum(r["win_base"] for r in fresh_res)
    wins_cand = sum(r["win_cand"] for r in fresh_res)
    rescues = sum(1 for r in fresh_res if not r["win_base"] and r["win_cand"])
    casualties = sum(1 for r in fresh_res if r["win_base"] and not r["win_cand"])

    print(f"\nFresh Cohort (128 legs):")
    print(f"  V49 Win Rate: {wins_cand/len(fresh_res)*100:5.1f}% (Base V48: {wins_base/len(fresh_res)*100:5.1f}%)")
    print(f"  Mean Delta vs V48:   {np.mean(deltas):+7.2f} (95% CI [{np.percentile(deltas, 2.5):+7.2f}, {np.percentile(deltas, 97.5):+7.2f}])")
    print(f"  Median Delta:        {np.median(deltas):+7.2f}")
    print(f"  Rescues (Loss -> Win): {rescues} | Casualties (Win -> Loss): {casualties}")

    out_file = os.path.join(REPO_ROOT, "research", "v49", "counterfactuals", "yarn_adaptation_results.json")
    with open(out_file, "w") as f:
        json.dump({"loss_res": loss_res, "mean_delta": float(np.mean(deltas)), "median_delta": float(np.median(deltas)),
                   "win_rate_v49": float(wins_cand/len(fresh_res)), "rescues": rescues, "casualties": casualties}, f, indent=2)
    print(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    main()
