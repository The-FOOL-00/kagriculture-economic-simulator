#!/usr/bin/env python3
"""Grand Current-Engine Benchmark Ladder for V55.

Evaluates candidates:
1. V49_Meta_Fusion (Frozen Sovereign Incumbent Reference)
2. V55_Post_Reveal_Shop (Post-Reveal Shop-Regime Continuation Candidate)
3. V55_Blocked_Action (Generic Blocked-Action Repair Candidate)

Across 32 strictly disjoint fresh seeds [250600..250631] x 2 seats x 9 opponents
(576 paired legs per candidate = 1,728 total 719-step simulation matches).
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
import research.v55.candidates.v55_post_reveal_shop.main as v55_shop_mod
import research.v55.candidates.v55_blocked_action.main as v55_blocked_mod

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
FRESH_SEEDS = [250600 + i for i in range(32)]

for s in FRESH_SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"
    assert not (250400 <= s <= 250527), f"CRITICAL: Discovery seed {s} accessed in fresh evaluation!"

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

def get_candidate_agent(candidate_key: str):
    if candidate_key == "V49_Meta_Fusion":
        return v49_mod.agent
    elif candidate_key == "V55_Post_Reveal_Shop":
        return v55_shop_mod.agent
    elif candidate_key == "V55_Blocked_Action":
        return v55_blocked_mod.agent
    raise ValueError(f"Unknown candidate {candidate_key}")

def run_ladder_leg(task: Tuple[int, int, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, candidate_key = task
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

    # 2. Candidate
    if candidate_key == "V49_Meta_Fusion":
        cash_c, cash_opp_c, win_c = cash49, cash_opp49, win49
    else:
        sim_c = FastKagricultureSim(seed=seed)
        obs_c = sim_c.reset(seed=seed)
        opp_c = load_opp(opp_name)
        agent_c = get_candidate_agent(candidate_key)

        for _ in range(719):
            ac = agent_c(obs_c[seat])
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
        "candidate": candidate_key,
        "cash49": cash49,
        "cash_c": cash_c,
        "delta": delta,
        "win49": win49,
        "win_c": win_c,
        "rescue": rescue,
        "casualty": casualty,
    }

def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        "mean_delta_vs_v49": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "ci95_low": float(np.percentile(boot_means, 2.5)),
        "ci95_high": float(np.percentile(boot_means, 97.5)),
        "win_rate_v49": float(wins49 / len(results)),
        "win_rate_cand": float(wins_c / len(results)),
        "rescues": rescues,
        "casualties": casualties,
        "active_legs": len(active),
        "active_fraction": float(len(active) / len(results)),
    }

def evaluate_ladder_candidate(candidate_key: str) -> Dict[str, Any]:
    tasks = [(s, seat, opp, candidate_key) for opp in ALL_OPPONENTS for s in FRESH_SEEDS for seat in (0, 1)]
    print(f"\n--- Evaluating Candidate: {candidate_key} ({len(tasks)} legs across 9 opponents) ---")
    t0 = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_ladder_leg, tasks))
    elapsed = time.time() - t0

    overall = compute_metrics(results)
    elite = compute_metrics([r for r in results if r["opp"] in ELITE_OPPONENTS])
    adv = compute_metrics([r for r in results if r["opp"] in ADV_OPPONENTS])

    per_opp = {}
    for opp in ALL_OPPONENTS:
        per_opp[opp] = compute_metrics([r for r in results if r["opp"] == opp])

    print(f"  Overall Delta vs V49: {overall['mean_delta_vs_v49']:+7.2f} (95% CI [{overall['ci95_low']:+7.2f}, {overall['ci95_high']:+7.2f}])")
    print(f"  Overall WR: V49 {overall['win_rate_v49']*100:.2f}% | Cand {overall['win_rate_cand']*100:.2f}% (Rescues: {overall['rescues']}, Casualties: {overall['casualties']})")
    print(f"  Elite Delta: {elite['mean_delta_vs_v49']:+7.2f} | Cand Elite WR: {elite['win_rate_cand']*100:.2f}%")
    print(f"  Adv Delta:   {adv['mean_delta_vs_v49']:+7.2f} | Cand Adv WR:   {adv['win_rate_cand']*100:.2f}%")

    return {
        "candidate": candidate_key,
        "time_seconds": elapsed,
        "overall": overall,
        "elite_suite": elite,
        "adversarial_suite": adv,
        "per_opponent": per_opp,
        "results": results
    }

def main():
    print("=" * 80)
    print("V55 FRESH PAIRED BENCHMARK LADDER (576 LEGS PER CANDIDATE)")
    print("=" * 80)

    candidates = [
        "V49_Meta_Fusion",
        "V55_Post_Reveal_Shop",
        "V55_Blocked_Action"
    ]

    ladder = {}
    per_opponent_dict = {}

    for c in candidates:
        cand_data = evaluate_ladder_candidate(c)
        per_opponent_dict[c] = cand_data["per_opponent"]
        # Save raw results separately or in ladder
        # Keep ladder summary clean
        summary_cand = {k: v for k, v in cand_data.items() if k != "results"}
        ladder[c] = summary_cand

    # Save v55_fresh_ladder.json
    out_ladder = os.path.join(REPO_ROOT, "research", "v55", "benchmarks", "v55_fresh_ladder.json")
    with open(out_ladder, "w", encoding="utf-8") as f:
        json.dump(ladder, f, indent=2)

    # Save v55_blocked_fresh_ladder.json
    out_blocked = os.path.join(REPO_ROOT, "research", "v55", "benchmarks", "v55_blocked_fresh_ladder.json")
    with open(out_blocked, "w", encoding="utf-8") as f:
        json.dump(ladder["V55_Blocked_Action"], f, indent=2)

    # Save per_opponent_results.json
    out_opp = os.path.join(REPO_ROOT, "research", "v55", "benchmarks", "per_opponent_results.json")
    with open(out_opp, "w", encoding="utf-8") as f:
        json.dump(per_opponent_dict, f, indent=2)

    print(f"\nAll benchmark ladder files saved successfully.")

if __name__ == "__main__":
    main()
