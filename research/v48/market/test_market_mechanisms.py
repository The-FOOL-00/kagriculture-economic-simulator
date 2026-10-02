#!/usr/bin/env python3
"""Market Mechanism & Rival-Harvest Tracking Counterfactuals for Kagriculture V48.

Evaluates causal variants of ORDERPRI2 / Rival-Harvest Tracking:
- Variant A: No tracking (ablation: disable advance, slot swap, and exposure reorder)
- Variant B: Exact tracking (Native 2945)
- Variant E: Commodity-Specific Tracking (restrict advance to MILK & WOOL only)
- Variant F: Town-Demand-Aware Tracking (protect town contract items from premature dump)
- Variant G: Market-Depth-Aware Tracking (suppress advance when market is already flooded)

Evaluates complete games to Step 719 across 64 clean seeds x 2 seats = 128 legs.
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

SEEDS = [249800 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def build_market_agent(variant: str):
    """Builds a modified 2945 agent for the given market tracking variant."""
    # We can clone m2945's implementation or customize the wrapper
    # Let's inspect how agent is structured in m2945
    return variant


def run_market_leg(args: Tuple[int, int, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, variant = args
    opp_seat = 1 - seat

    # Setup agent based on variant
    # We can modify module flags or instantiate customized agent
    agent_base = m2945.make_agent(m2945._ROUTES, router=m2945._router, **m2945._SETTINGS)
    opp = load_elite_agent(opp_name)

    # If variant == "B", run raw 2945 agent
    if variant == "B":
        agent_fn = m2945.agent
    elif variant == "A":
        # No tracking: run base agent without ORDERPRI2 wrapper
        agent_fn = agent_base
    else:
        # Custom wrappers for E, F, G
        def custom_agent(obs, cfg=None):
            # If variant E: only advance MILK and WOOL
            orig_sn = m2945._OR2_SN_ITEMS
            if variant == "E":
                m2945._OR2_SN_ITEMS = ("MILK", "WOOL")
            elif variant == "F":
                # Check town shops: if town consumes item, don't dump
                town = obs.get("town", {}) or {}
                # Filter out active shop items from sn_items
                active_demands = set()
                for shop in town.get("unlocked_shops", []):
                    if shop in ("PET_CAFE", "BAKERY", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"):
                        active_demands.add("MILK")
                    if shop in ("YARN_STORE",):
                        active_demands.add("WOOL")
                m2945._OR2_SN_ITEMS = tuple(i for i in ("MILK", "WOOL", "CARROT") if i not in active_demands)
            elif variant == "G":
                # Depth aware: only advance if inventory < 15
                mkt_inv = obs.get("market", {}).get("inventory", {})
                m2945._OR2_SN_ITEMS = tuple(i for i in ("MILK", "WOOL", "CARROT", "STRAWBERRY") if mkt_inv.get(i, 0) < 15)

            act = m2945.agent(obs, cfg)
            m2945._OR2_SN_ITEMS = orig_sn
            return act

        agent_fn = custom_agent

    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    for step in range(719):
        a_2945 = agent_fn(obs[seat])
        a_opp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        actions = [a_2945, a_opp] if seat == 0 else [a_opp, a_2945]
        obs, rew, done, info = sim.step(actions)

    cash_2945 = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "variant": variant,
        "cash": cash_2945,
        "opp_cash": cash_opp,
        "margin": cash_2945 - cash_opp,
    }


def main():
    print("Evaluating Rival-Harvest Market Variants across 64 seeds x 2 seats = 128 legs vs V44...")
    tasks_base = [(s, seat, "V44") for s in SEEDS for seat in (0, 1)]

    # 1. Variant B (Raw 2945 with exact tracking)
    print("Running Variant B (Exact tracking baseline)...")
    b_tasks = [(s, seat, opp, "B") for s, seat, opp in tasks_base]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        b_results = list(executor.map(run_market_leg, b_tasks))
    b_cash = { (r["seed"], r["seat"]): r["cash"] for r in b_results }

    variants = ["A", "E", "F", "G"]
    variant_summaries = {}

    for var in variants:
        print(f"Running Variant {var}...")
        var_tasks = [(s, seat, opp, var) for s, seat, opp in tasks_base]
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            var_results = list(executor.map(run_market_leg, var_tasks))

        deltas = [r["cash"] - b_cash[(r["seed"], r["seat"])] for r in var_results]
        mean_d = float(np.mean(deltas))
        median_d = float(np.median(deltas))
        std_err = float(np.std(deltas, ddof=1) / np.sqrt(len(deltas)))
        ci_low = mean_d - 1.96 * std_err
        ci_high = mean_d + 1.96 * std_err
        pos = sum(d > 0 for d in deltas)
        neg = sum(d < 0 for d in deltas)
        zero = sum(d == 0 for d in deltas)

        variant_summaries[var] = {
            "mean_delta": mean_d,
            "median_delta": median_d,
            "ci_95": [ci_low, ci_high],
            "positive_legs": pos,
            "negative_legs": neg,
            "zero_legs": zero,
        }
        print(f"  Variant {var}: Mean Delta={mean_d:+7.2f} (95% CI [{ci_low:+7.2f}, {ci_high:+7.2f}]), Median={median_d:+7.2f} | Pos={pos} Neg={neg} Zero={zero}")

    out_file = os.path.join(REPO_ROOT, "research", "v48", "market", "market_counterfactuals.json")
    with open(out_file, "w") as f:
        json.dump(variant_summaries, f, indent=2)

    print(f"\nMarket evaluation complete! Saved to {out_file}")


if __name__ == "__main__":
    main()
