#!/usr/bin/env python3
"""Counterfactual testing of isolated tactical mechanisms against V48 backbone.

Evaluates on 64 fresh seeds x 2 seats = 128 paired legs.
Tests:
M1: E402 Late Seed Cap
M2: MG + IG Market Compaction & Hole Closure
M3: SM Liquidity Shield
M1_M2_FUSION: M1 + M2 Fusion
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

SEEDS = [250000 + i for i in range(64)]
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
# MECHANISM M2: MG (Sell Compaction) + IG (Queue Hole Closure)
# ===========================================================================
def apply_m2_market_compaction(observation, action):
    market = [list(o) for o in (action.get("market") or []) if o]
    if len(market) < 2:
        return action
    # 1. Merge same item orders
    seen = {}
    merged = []
    for o in market:
        if len(o) >= 3 and o[0] in ("SELL", "BUY_PRODUCT", "BUY_SEED"):
            it = (o[0], o[1])
            if it in seen:
                merged[seen[it]][2] = int(merged[seen[it]][2]) + int(o[2])
                continue
            seen[it] = len(merged)
        merged.append(o)
    # 2. Filter empty and pull forward
    valid = [o for o in merged if (len(o) >= 3 and int(o[2]) > 0) or (len(o) >= 2 and o[0] in ("BUY_LAND", "HIRE"))]
    return dict(action, market=valid[:10])


# ===========================================================================
# MECHANISM M3: SM (Liquidity Shield)
# ===========================================================================
_SM_ANIMAL = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
_SM_LAND = (1000, 2000, 4000)
_SM_PRODUCTS = ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT")

def apply_m3_liquidity_shield(observation, action):
    market = [list(o) for o in (action.get("market") or []) if o]
    if not market:
        return action
    seat = int(observation["player"])
    farm = observation["farms"][seat]
    shed = dict((observation.get("private") or {}).get("shed") or {})
    prices = observation["market"].get("prices") or {}
    quads = len(farm.get("unlocked_quadrants") or [])
    cash = float(farm.get("money", 0) or 0)
    sold = {}
    for o in market:
        if o[0] == "SELL" and len(o) >= 3:
            item = o[1]
            take = min(max(0, int(o[2])), int(shed.get(item, 0)) - sold.get(item, 0))
            if take > 0:
                cash += take * float(prices.get(item, 0))
                sold[item] = sold.get(item, 0) + take
        elif o[0] == "BUY_ANIMAL" and len(o) >= 3:
            cash -= _SM_ANIMAL.get(o[1], 400) * max(0, int(o[2]))
        elif o[0] == "BUY_SEED" and len(o) >= 3:
            cash -= {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(o[1], 100) * max(0, int(o[2]))
        elif o[0] == "BUY_LAND":
            extra = quads - 1
            cash -= _SM_LAND[extra] if 0 <= extra < 3 else 4000
    need = -cash
    if need <= 0:
        return action
    candidates = []
    for item in _SM_PRODUCTS:
        price = float(prices.get(item, 0))
        avail = int(shed.get(item, 0)) - sold.get(item, 0)
        if price > 1 and avail > 0:
            candidates.append((price, item, avail))
    candidates.sort(reverse=True)
    added = []
    for price, item, avail in candidates:
        if need <= 0 or len(market) + len(added) >= 10:
            break
        q = min(avail, int(need / price) + 1)
        if q <= 0:
            continue
        added.append(["SELL", item, q])
        need -= q * price
    if not added:
        return action
    idx = next((i for i, o in enumerate(market) if o and str(o[0]).startswith("BUY")), len(market))
    market = market[:idx] + added + market[idx:]
    return dict(action, market=market[:10])


# ===========================================================================
# Agent Execution Wrappers
# ===========================================================================
def step_agent(obs, variant: str):
    act = v48_mod.agent(obs)
    chassis = v48_mod._IMPL.chassis
    if variant == "BASE_V48":
        return act
    elif variant == "M1_SEED_CAP":
        return apply_m1_late_seed_cap(obs, act, chassis)
    elif variant == "M2_MARKET_COMPACT":
        return apply_m2_market_compaction(obs, act)
    elif variant == "M3_LIQUIDITY_SHIELD":
        return apply_m3_liquidity_shield(obs, act)
    elif variant == "M1_M2_FUSION":
        act = apply_m1_late_seed_cap(obs, act, chassis)
        return apply_m2_market_compaction(obs, act)
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
    variants = ["M1_SEED_CAP", "M2_MARKET_COMPACT", "M3_LIQUIDITY_SHIELD", "M1_M2_FUSION"]
    print("Testing Isolated Tactical Mechanisms across 64 seeds x 2 seats = 128 paired legs per variant...")

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
            "rescues": rescues,
            "casualties": casualties,
        }
        print(f"Variant: {var:20} | Cand WR: {wins_cand/len(res)*100:5.1f}% (Base: {wins_base/len(res)*100:5.1f}%) | "
              f"Mean Delta: {np.mean(deltas):+7.2f} | Median: {np.median(deltas):+6.2f} | "
              f"Rescues: {rescues} | Casualties: {casualties}")

    out_file = os.path.join(REPO_ROOT, "research", "v49", "counterfactuals", "isolated_mechanisms.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved results to {out_file}")


if __name__ == "__main__":
    main()
