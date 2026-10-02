#!/usr/bin/env python3
"""Shop-route counterfactual search for Kagriculture V48.

Tests whether overriding weak non-yarn shop routes (103, 110, 112, 117, 118, 121)
with the high-compounding 8-cow Route 105 or Route 0 yields positive alpha vs Native 2945.

Runs across clean dev seeds in parallel across 8 processes.
Calculates:
- Paired Delta vs Native 2945
- Win flip rate
- 95% Confidence Interval
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
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import research.v47.elite_corpus.agents.thomastschinkel_2945.main as m2945

# 64 Clean dev seeds
SEEDS = [249800 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


WEAK_SHOP_PAIRS = {
    ("PET_CAFE", "FARMERS_MARKET"): 105,  # Native: 117
    ("BAKERY", "BRUNCH_SPOT"): 105,        # Native: 103
    ("BRUNCH_SPOT", "FARMERS_MARKET"): 105,# Native: 110
    ("FARMERS_MARKET", "BRUNCH_SPOT"): 105,# Native: 112
    ("PET_CAFE", "PET_CAFE"): 105,         # Native: 118
    ("PIZZA_SHOP", "FARMERS_MARKET"): 105, # Native: 121
    ("PET_CAFE", "BAKERY"): 105,           # Native: 103
}


def build_patched_router(override_map: Dict[Tuple[str, str], int]):
    def custom_router(observation, step, state):
        if step == 2:
            try:
                _rv = observation["farms"][1 - int(observation["player"])]
                state["rkey"] = (round(float(_rv["money"]), 3), int(observation["market"]["inventory"]["WHEAT"]))
            except Exception:
                state["rkey"] = None
        if step >= 144 and not state.get("day6"):
            town = m2945._get(observation, "town", {}) or {}
            shops = tuple((m2945._get(town, "unlocked_shops", []) or [])[:2])
            use_new = shops.count("YARN_STORE") <= 0
            state["expert"] = "EXP240" if use_new else "V39"

            if shops in override_map:
                state["route"] = override_map[shops]
            else:
                state["route"] = m2945._R108_SHOP_ROUTES.get(shops, 100) if use_new else m2945._R110_OLD_SHOPS.get(shops, 0)
                state["route"] = m2945._V92_TABLE.get(shops, state["route"])
                if "YARN_STORE" in shops and state.get("rkey") in m2945._V93_ROUTE_BY_RIVAL:
                    state["route"] = m2945._V93_ROUTE_BY_RIVAL[state["rkey"]]
            state["day6"] = True
        if step >= 648 and not state.get("day27"):
            state["route"] = 2
            state["day27"] = True
        return state.get("route", 0)

    return custom_router


def run_paired_counterfactual(args: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, opp_name = args
    opp_seat = 1 - seat

    # 1. Native 2945 agent
    agent_native = m2945.make_agent(m2945._ROUTES, router=m2945._router, **m2945._SETTINGS)
    opp_1 = load_elite_agent(opp_name)

    sim1 = FastKagricultureSim(seed=seed)
    obs1 = sim1.reset(seed=seed)
    for step in range(719):
        a_nat = agent_native(obs1[seat])
        a_opp = opp_1.act(obs1[opp_seat]) if hasattr(opp_1, "act") else opp_1(obs1[opp_seat])
        actions = [a_nat, a_opp] if seat == 0 else [a_opp, a_nat]
        obs1, rew, done, info = sim1.step(actions)
    cash_nat = float(obs1[seat]["farms"][seat]["money"])
    cash_opp_1 = float(obs1[opp_seat]["farms"][opp_seat]["money"])

    # 2. Patched 2945 challenger
    patched_router = build_patched_router(WEAK_SHOP_PAIRS)
    agent_challenger = m2945.make_agent(m2945._ROUTES, router=patched_router, **m2945._SETTINGS)
    opp_2 = load_elite_agent(opp_name)

    sim2 = FastKagricultureSim(seed=seed)
    obs2 = sim2.reset(seed=seed)
    for step in range(719):
        a_chal = agent_challenger(obs2[seat])
        a_opp = opp_2.act(obs2[opp_seat]) if hasattr(opp_2, "act") else opp_2(obs2[opp_seat])
        actions = [a_chal, a_opp] if seat == 0 else [a_opp, a_chal]
        obs2, rew, done, info = sim2.step(actions)
    cash_chal = float(obs2[seat]["farms"][seat]["money"])
    cash_opp_2 = float(obs2[opp_seat]["farms"][opp_seat]["money"])

    town = obs1[0].get("town", {}) or {}
    shops = list(town.get("unlocked_shops", []) or [])
    first_two = tuple(shops[:2])
    was_overridden = first_two in WEAK_SHOP_PAIRS

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "shops": shops,
        "was_overridden": was_overridden,
        "overridden_shops": list(first_two) if was_overridden else None,
        "target_route": WEAK_SHOP_PAIRS.get(first_two) if was_overridden else None,
        "cash_nat": cash_nat,
        "cash_chal": cash_chal,
        "delta": cash_chal - cash_nat,
        "margin_nat": cash_nat - cash_opp_1,
        "margin_chal": cash_chal - cash_opp_2,
        "win_nat": cash_nat > cash_opp_1,
        "win_chal": cash_chal > cash_opp_2,
    }


def main():
    print("Evaluating Step-144 Shop-Route Counterfactuals across 64 clean seeds x 2 seats x 2 key opponents (V44, dmitrii_lb2800)...")
    tasks = [(s, seat, opp) for opp in ("V44", "dmitrii_lb2800") for s in SEEDS for seat in (0, 1)]

    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(run_paired_counterfactual, t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            results.append(res)
            if res["delta"] != 0:
                print(f"  [OVERRIDE ACTIVE] Opp={res['opp']:14s} Seed={res['seed']} Seat={res['seat']} Delta={res['delta']:+7.1f} | Shops={res['shops'][:3]} | Margins: {res['margin_nat']:+.1f} -> {res['margin_chal']:+.1f}")

    deltas = [r["delta"] for r in results]
    mean_delta = float(np.mean(deltas))
    median_delta = float(np.median(deltas))
    ci95_low = mean_delta - 1.96 * float(np.std(deltas, ddof=1) / np.sqrt(len(deltas)))
    ci95_high = mean_delta + 1.96 * float(np.std(deltas, ddof=1) / np.sqrt(len(deltas)))

    modified_legs = [r for r in results if r["was_overridden"]]
    print(f"\nTotal Legs: {len(results)} | Overridden Legs: {len(modified_legs)}")
    print(f"Overall Mean Delta vs 2945: {mean_delta:+.2f} (95% CI [{ci95_low:+.2f}, {ci95_high:+.2f}]), Median: {median_delta:+.2f}")

    if modified_legs:
        mod_deltas = [r["delta"] for r in modified_legs]
        rescues = [r for r in modified_legs if not r["win_nat"] and r["win_chal"]]
        casualties = [r for r in modified_legs if r["win_nat"] and not r["win_chal"]]
        print(f"\n--- Overridden Cohort Analysis ({len(modified_legs)} legs) ---")
        print(f"Mean Delta in Overridden Cohort: {np.mean(mod_deltas):+.2f}")
        print(f"Median Delta in Overridden Cohort: {np.median(mod_deltas):+.2f}")
        print(f"Rescued Losses (Loss -> Win): {len(rescues)}")
        print(f"Casualties (Win -> Loss): {len(casualties)}")

    out_file = os.path.join(REPO_ROOT, "research", "v48", "shop_routes", "shop_counterfactuals.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nCounterfactual results saved to {out_file}!")


if __name__ == "__main__":
    main()
