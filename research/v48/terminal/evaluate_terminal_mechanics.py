#!/usr/bin/env python3
"""Terminal Liquidation Mechanism Counterfactuals for Kagriculture V48.

Tests whether V44's staggered terminal liquidation (50/50 pre-emption, 40/60 flush, or hybrid)
improves 2945's terminal cash vs Raw 2945 (T0), holding 2945 production strictly fixed.

Variants:
- T0: Raw 2945 (Step 718 single dump)
- T1: 2945 + V44 50/50 Stagger (Step 693-694 50%, Step 704-705 50%, Step 716+ flush)
- T2: 2945 + V44 40/60 Stagger (Step 693 40%, Step 704 60%, Step 716+ flush)
- T4: 2945 + Hybrid Depth-Aware Stagger (Stagger only if inventory > 15 units to prevent crash)
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

MARKETABLE_PRODUCTS = ("WHEAT", "CARROT", "POTATO", "TOMATO", "MILK", "EGG", "WOOL")


def apply_terminal_policy(action: Dict[str, Any], obs: Dict[str, Any], seat: int, step: int, policy: str):
    if policy == "T0":
        return action

    farms = obs.get("farms", [])
    if seat >= len(farms):
        return action
    shed = farms[seat].get("shed", {}) or {}
    mkt = list(action.get("market") or [])
    already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}

    if policy == "T1":
        # 50/50 Stagger
        if step in (693, 694):
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty >= 2 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, max(1, qty // 2)])
                    already_selling.add(item)
        elif step in (704, 705):
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty >= 2 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, max(1, qty // 2)])
                    already_selling.add(item)
        elif step >= 716:
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty > 0 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, qty])
                    already_selling.add(item)

    elif policy == "T2":
        # 40/60 Stagger
        if step in (693, 694):
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty >= 3 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, max(1, int(qty * 0.4))])
                    already_selling.add(item)
        elif step in (704, 705):
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty >= 2 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, max(1, int(qty * 0.6))])
                    already_selling.add(item)
        elif step >= 716:
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty > 0 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, qty])
                    already_selling.add(item)

    elif policy == "T4":
        # Hybrid depth-aware: only stagger high-volume inventory (> 12 units)
        if step in (693, 694, 704, 705):
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty >= 12 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, qty // 2])
                    already_selling.add(item)
        elif step >= 716:
            for item in MARKETABLE_PRODUCTS:
                qty = shed.get(item, 0)
                if qty > 0 and item not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", item, qty])
                    already_selling.add(item)

    action["market"] = mkt[:10]
    return action


def run_terminal_leg(args: Tuple[int, int, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, policy = args
    opp_seat = 1 - seat

    agent_2945 = m2945.make_agent(m2945._ROUTES, router=m2945._router, **m2945._SETTINGS)
    opp = load_elite_agent(opp_name)

    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    for step in range(719):
        act_2945 = agent_2945(obs[seat])
        if step >= 690:
            act_2945 = apply_terminal_policy(act_2945, obs[seat], seat, step, policy)
        act_opp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        actions = [act_2945, act_opp] if seat == 0 else [act_opp, act_2945]
        obs, rew, done, info = sim.step(actions)

    cash_2945 = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "policy": policy,
        "cash": cash_2945,
        "opp_cash": cash_opp,
        "margin": cash_2945 - cash_opp,
    }


def main():
    print("Evaluating Terminal Liquidation Policies across 64 seeds x 2 seats x 2 opponents (128 legs per policy)...")
    tasks_base = [(s, seat, opp) for opp in ("V44", "dmitrii_lb2800") for s in SEEDS for seat in (0, 1)]

    # Run T0 (Raw baseline)
    print("Running T0 (Raw 2945 baseline)...")
    t0_tasks = [(s, seat, opp, "T0") for s, seat, opp in tasks_base]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        t0_results = list(executor.map(run_terminal_leg, t0_tasks))
    t0_cash = { (r["seed"], r["seat"], r["opp"]): r["cash"] for r in t0_results }

    policies = ["T1", "T2", "T4"]
    policy_summaries = {}

    for pol in policies:
        print(f"Running {pol}...")
        pol_tasks = [(s, seat, opp, pol) for s, seat, opp in tasks_base]
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            pol_results = list(executor.map(run_terminal_leg, pol_tasks))

        deltas = [r["cash"] - t0_cash[(r["seed"], r["seat"], r["opp"])] for r in pol_results]
        mean_d = float(np.mean(deltas))
        median_d = float(np.median(deltas))
        std_err = float(np.std(deltas, ddof=1) / np.sqrt(len(deltas)))
        ci_low = mean_d - 1.96 * std_err
        ci_high = mean_d + 1.96 * std_err
        pos = sum(d > 0 for d in deltas)
        neg = sum(d < 0 for d in deltas)
        zero = sum(d == 0 for d in deltas)

        policy_summaries[pol] = {
            "mean_delta": mean_d,
            "median_delta": median_d,
            "ci_95": [ci_low, ci_high],
            "positive_legs": pos,
            "negative_legs": neg,
            "zero_legs": zero,
        }
        print(f"  {pol}: Mean Delta={mean_d:+7.2f} (95% CI [{ci_low:+7.2f}, {ci_high:+7.2f}]), Median={median_d:+7.2f} | Pos={pos} Neg={neg} Zero={zero}")

    out_file = os.path.join(REPO_ROOT, "research", "v48", "terminal", "terminal_counterfactuals.json")
    with open(out_file, "w") as f:
        json.dump(policy_summaries, f, indent=2)

    print(f"\nTerminal evaluation complete! Saved to {out_file}")


if __name__ == "__main__":
    main()
