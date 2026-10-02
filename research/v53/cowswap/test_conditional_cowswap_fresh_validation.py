#!/usr/bin/env python3
"""Fresh Validation of Conditional COWSWAP Policies (V53 Section 8).

Evaluates surviving surgical COWSWAP candidates across 32 fresh seeds [250600..250631]
x 2 seats x 9 opponents (576 legs per candidate, exceeding the 256 minimum).
Ensures:
- 0 casualties vs current-engine V49
- Paired economic delta >= 0
- WR >= V49 WR
- At least one actual rescue
"""

import concurrent.futures
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
from research.v53.cowswap.test_conditional_cowswap_loss_rescues import should_suppress_cowswap

FRESH_SEEDS = [250600 + i for i in range(32)]
ELITE_OPPONENTS = [
    "V44",
    "dmitrii_lb2800",
    "tetsutani_pasture",
    "kaitofukami_v48_3009",
    "indarkarhana_top10",
    "saiteja_mega_3000",
]
ADV_OPPONENTS = [
    "DAIRY_FLOOD",
    "WOOL_FLOOD",
    "TERMINAL_DUMPER",
]
ALL_OPPONENTS = ELITE_OPPONENTS + ADV_OPPONENTS


def make_adversary(strategy: str) -> Any:
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


def load_opp(opp_name: str) -> Any:
    if opp_name in ADV_OPPONENTS:
        return make_adversary(opp_name)
    return load_elite_agent(opp_name)


def run_cowswap_leg(task: Tuple[int, int, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, policy = task
    opp_seat = 1 - seat

    # 1. Baseline V49
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    opp49 = load_opp(opp_name)
    agent49 = v49_mod.agent

    for _ in range(719):
        a49 = agent49(obs49[seat])
        aopp = opp49.act(obs49[opp_seat]) if hasattr(opp49, "act") else opp49(obs49[opp_seat])
        obs49, _, _, _ = sim49.step([a49, aopp] if seat == 0 else [aopp, a49])

    cash49 = float(obs49[seat]["farms"][seat]["money"])
    cash_opp49 = float(obs49[opp_seat]["farms"][opp_seat]["money"])
    win49 = cash49 > cash_opp49

    # 2. Policy Candidate
    sim_c = FastKagricultureSim(seed=seed)
    obs_c = sim_c.reset(seed=seed)
    opp_c = load_opp(opp_name)

    activations = 0

    def _policy_agent(obs, cfg=None):
        nonlocal activations
        orig_options = v49_mod._CS_OPTIONS
        suppress = should_suppress_cowswap(policy, obs)
        if suppress:
            activations += 1
            v49_mod._CS_OPTIONS = ()
        else:
            v49_mod._CS_OPTIONS = orig_options
        act = v49_mod.agent(obs, cfg)
        v49_mod._CS_OPTIONS = orig_options
        return act

    for _ in range(719):
        ac = _policy_agent(obs_c[seat])
        aopp = opp_c.act(obs_c[opp_seat]) if hasattr(opp_c, "act") else opp_c(obs_c[opp_seat])
        obs_c, _, _, _ = sim_c.step([ac, aopp] if seat == 0 else [aopp, ac])

    cash_c = float(obs_c[seat]["farms"][seat]["money"])
    cash_opp_c = float(obs_c[opp_seat]["farms"][opp_seat]["money"])
    win_c = cash_c > cash_opp_c

    delta = cash_c - cash49
    rescue = (not win49) and win_c
    casualty = win49 and (not win_c)

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "policy": policy,
        "cash49": cash49,
        "cash_c": cash_c,
        "delta": delta,
        "win49": win49,
        "win_c": win_c,
        "rescue": rescue,
        "casualty": casualty,
        "activated": activations > 0,
    }


def compute_policy_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    deltas = np.array([r["delta"] for r in results], dtype=float)
    active = [r for r in results if r["delta"] != 0.0]
    rescues = sum(r["rescue"] for r in results)
    casualties = sum(r["casualty"] for r in results)
    wins49 = sum(r["win49"] for r in results)
    wins_c = sum(r["win_c"] for r in results)

    rng = np.random.default_rng(42)
    boot_means = np.mean(rng.choice(deltas, size=(10000, len(deltas)), replace=True), axis=1)

    return {
        "legs": len(results),
        "mean_delta": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "ci95_low": float(np.percentile(boot_means, 2.5)),
        "ci95_high": float(np.percentile(boot_means, 97.5)),
        "win_rate_v49": float(wins49 / len(results)),
        "win_rate_cand": float(wins_c / len(results)),
        "rescues": rescues,
        "casualties": casualties,
        "active_legs": len(active),
        "activations": sum(r["activated"] for r in results),
    }


def evaluate_policy(policy: str) -> Dict[str, Any]:
    tasks = [(s, seat, opp, policy) for opp in ALL_OPPONENTS for s in FRESH_SEEDS for seat in (0, 1)]
    print(f"\n--- Evaluating Policy {policy} ({len(tasks)} legs across 9 opponents) ---")
    t0 = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_cowswap_leg, tasks))
    elapsed = time.time() - t0

    overall = compute_policy_metrics(results)
    elite = compute_policy_metrics([r for r in results if r["opp"] in ELITE_OPPONENTS])
    adv = compute_policy_metrics([r for r in results if r["opp"] in ADV_OPPONENTS])

    print(f"  Overall Delta: {overall['mean_delta']:+6.1f} | 95% CI=[{overall['ci95_low']:+6.1f}, {overall['ci95_high']:+6.1f}] | WR: {overall['win_rate_cand']*100:.2f}% (Rescues: {overall['rescues']}, Casualties: {overall['casualties']})")
    print(f"  Elite Delta:   {elite['mean_delta']:+6.1f} | Elite WR: {elite['win_rate_cand']*100:.2f}% | Casualties: {elite['casualties']}")
    
    return {
        "policy": policy,
        "elapsed": elapsed,
        "overall": overall,
        "elite": elite,
        "adversarial": adv,
    }


def main():
    print("=" * 80)
    print("V53 SECTION 8: FRESH VALIDATION OF SURGICAL COWSWAP POLICIES")
    print("=" * 80)

    # We evaluate candidate policies
    test_policies = ["C1", "C2", "C4", "C6"]
    results = {}

    for p in test_policies:
        results[p] = evaluate_policy(p)

    out_file = os.path.join(REPO_ROOT, "research", "v53", "cowswap", "cowswap_fresh_results.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved fresh validation results to {out_file}")


if __name__ == "__main__":
    main()
