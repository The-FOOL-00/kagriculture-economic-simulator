#!/usr/bin/env python3
"""Adversarial Stress Testing for Kagriculture V49 Meta Fusion.

Tests V48 and V49 against synthetic adversaries targeting:
1. Dairy Flooder (Mass cow acquisition + turn-by-turn milk price suppression)
2. Wool Flooder (Mass sheep acquisition + turn-by-turn wool price suppression)
3. Terminal Dumper (Strategic inventory withholding followed by massive Step 680 price collapse)

Evaluates paired performance across 64 clean seeds x 2 seats = 128 legs per adversary (384 legs total).
Saves to research/v49/adversaries/adversarial_results.json.
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
import candidates.v49_meta_fusion.main as v49_mod

SEEDS = [250600 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def make_adversary(strategy: str):
    def _adv(obs, cfg=None):
        step = int(obs.get("step", 0))
        seat = int(obs.get("player", 0))
        farm = obs["farms"][seat]
        shed = farm.get("shed", {}) or {}
        hands = farm.get("hands", []) or []
        mkt = []

        if strategy == "DAIRY_FLOOD":
            milk = shed.get("MILK", 0)
            if milk > 0:
                mkt.append(["SELL", "MILK", milk])
            if step < 240 and farm.get("money", 0) >= 400:
                mkt.append(["BUY_ANIMAL", "COW", 1])

        elif strategy == "WOOL_FLOOD":
            wool = shed.get("WOOL", 0)
            if wool > 0:
                mkt.append(["SELL", "WOOL", wool])
            if step < 240 and farm.get("money", 0) >= 500:
                mkt.append(["BUY_ANIMAL", "SHEEP", 1])

        elif strategy == "TERMINAL_DUMPER":
            if step >= 680:
                for item in ("MILK", "WOOL", "WHEAT", "CARROT", "EGG"):
                    qty = shed.get(item, 0)
                    if qty > 0 and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])

        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in hands],
            "market": mkt[:10],
        }

    return _adv


def run_adv_match(args: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, adv_name = args
    opp_seat = 1 - seat
    adv_fn = make_adversary(adv_name)

    # 1. V48 vs Adversary
    sim1 = FastKagricultureSim(seed=seed)
    obs1 = sim1.reset(seed=seed)
    for _ in range(719):
        a_v48 = v48_mod.agent(obs1[seat])
        a_adv = adv_fn(obs1[opp_seat])
        actions = [a_v48, a_adv] if seat == 0 else [a_adv, a_v48]
        obs1, _, _, _ = sim1.step(actions)
    cash_v48 = float(obs1[seat]["farms"][seat]["money"])
    cash_adv1 = float(obs1[opp_seat]["farms"][opp_seat]["money"])

    # 2. V49 vs Adversary
    sim2 = FastKagricultureSim(seed=seed)
    obs2 = sim2.reset(seed=seed)
    for _ in range(719):
        a_v49 = v49_mod.agent(obs2[seat])
        a_adv = adv_fn(obs2[opp_seat])
        actions = [a_v49, a_adv] if seat == 0 else [a_adv, a_v49]
        obs2, _, _, _ = sim2.step(actions)
    cash_v49 = float(obs2[seat]["farms"][seat]["money"])
    cash_adv2 = float(obs2[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "adv": adv_name,
        "cash_v48": cash_v48,
        "cash_v49": cash_v49,
        "delta": cash_v49 - cash_v48,
        "win_v48": cash_v48 > cash_adv1,
        "win_v49": cash_v49 > cash_adv2,
        "margin_v48": cash_v48 - cash_adv1,
        "margin_v49": cash_v49 - cash_adv2,
    }


def main():
    adversaries = ["DAIRY_FLOOD", "WOOL_FLOOD", "TERMINAL_DUMPER"]
    print("Executing Adversarial Stress Test across 64 seeds x 2 seats = 128 legs per adversary...")

    adv_summary = {}
    for adv in adversaries:
        print(f"Testing vs {adv}...")
        tasks = [(s, seat, adv) for s in SEEDS for seat in (0, 1)]
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            res = list(executor.map(run_adv_match, tasks))

        deltas = [r["delta"] for r in res]
        wins_v48 = sum(r["win_v48"] for r in res)
        wins_v49 = sum(r["win_v49"] for r in res)

        adv_summary[adv] = {
            "legs": len(res),
            "win_rate_v48": float(wins_v48 / len(res)),
            "win_rate_v49": float(wins_v49 / len(res)),
            "mean_delta": float(np.mean(deltas)),
            "median_delta": float(np.median(deltas)),
            "margin_v48": float(np.mean([r["margin_v48"] for r in res])),
            "margin_v49": float(np.mean([r["margin_v49"] for r in res])),
        }
        print(f"  {adv}: V49 WinRate={wins_v49/len(res)*100:.1f}%, Mean Delta={np.mean(deltas):+7.2f}, Margin={np.mean([r['margin_v49'] for r in res]):+7.1f}")

    out_file = os.path.join(REPO_ROOT, "research", "v49", "adversaries", "adversarial_results.json")
    with open(out_file, "w") as f:
        json.dump(adv_summary, f, indent=2)

    print(f"\nAdversarial results saved to {out_file}!")


if __name__ == "__main__":
    main()
