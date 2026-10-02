#!/usr/bin/env python3
"""Fresh Validation Benchmark for V51 (Phase 11 & 13).

Evaluates candidates on 32 strictly disjoint fresh seeds [250600..250631]
across 9 opponents (6 elite + 3 adversarial) over 576 legs per candidate.
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
import candidates.v51_blocked_repair.main as v51_mod
from research.v51.counterfactuals.run_v51_counterfactuals import compute_bootstrap_ci, make_midgame_meta_agent

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
FRESH_SEEDS = [250600 + i for i in range(32)] # 32 seeds * 2 seats * 9 opponents = 576 legs

for s in FRESH_SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"
    assert not (250400 <= s <= 250527), f"CRITICAL: Discovery seed {s} accessed in fresh evaluation!"


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


def load_any_agent(opp_name: str) -> Any:
    if opp_name in ("DAIRY_FLOOD", "WOOL_FLOOD", "TERMINAL_DUMPER"):
        return make_adversary(opp_name)
    return load_elite_agent(opp_name)


def run_fresh_leg(args: Tuple[int, int, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, candidate_key = args
    opp_seat = 1 - seat

    # 1. Baseline V49
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    opp49 = load_any_agent(opp_name)
    agent49 = v49_mod.agent

    for _ in range(719):
        a49 = agent49(obs49[seat])
        aopp = opp49.act(obs49[opp_seat]) if hasattr(opp49, "act") else opp49(obs49[opp_seat])
        obs49, _, _, _ = sim49.step([a49, aopp] if seat == 0 else [aopp, a49])

    cash49 = float(obs49[seat]["farms"][seat]["money"])
    cash_opp49 = float(obs49[opp_seat]["farms"][opp_seat]["money"])
    win49 = cash49 > cash_opp49

    # 2. Candidate
    sim_c = FastKagricultureSim(seed=seed)
    obs_c = sim_c.reset(seed=seed)
    opp_c = load_any_agent(opp_name)

    if candidate_key == "V49_Meta_Fusion":
        agent_c = v49_mod.agent
    elif candidate_key == "V51_Blocked_Repair":
        agent_c = v51_mod.agent
    elif candidate_key == "V51_Midgame_Reset_Variant":
        agent_c = make_midgame_meta_agent("M3_Midgame_Reset_Step72")
    elif candidate_key == "V51_Sell_Reorder_Variant":
        agent_c = make_midgame_meta_agent("M4_Sell_Slot_Reordering")
    else:
        agent_c = v49_mod.agent

    for _ in range(719):
        ac = agent_c(obs_c[seat])
        aopp = opp_c.act(obs_c[opp_seat]) if hasattr(opp_c, "act") else opp_c(obs_c[opp_seat])
        obs_c, _, _, _ = sim_c.step([ac, aopp] if seat == 0 else [aopp, ac])

    cash_c = float(obs_c[seat]["farms"][seat]["money"])
    cash_opp_c = float(obs_c[opp_seat]["farms"][opp_seat]["money"])
    win_c = cash_c > cash_opp_c

    delta = cash_c - cash49
    rescue = not win49 and win_c
    casualty = win49 and not win_c

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
    if not results:
        return {}
    deltas = np.array([r["delta"] for r in results], dtype=float)
    active = [r for r in results if r["delta"] != 0.0]
    rescues = sum(r["rescue"] for r in results)
    casualties = sum(r["casualty"] for r in results)
    wins49 = sum(r["win49"] for r in results)
    wins_c = sum(r["win_c"] for r in results)
    boot_ci = compute_bootstrap_ci(deltas)

    return {
        "legs": len(results),
        "mean_delta_vs_v49": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "bootstrap_95_ci": list(boot_ci),
        "win_rate_v49": float(wins49 / len(results)),
        "win_rate_cand": float(wins_c / len(results)),
        "rescues": rescues,
        "casualties": casualties,
        "active_legs": len(active),
        "active_fraction": float(len(active) / len(results)),
    }


def evaluate_candidate(candidate_key: str, elite_opponents: List[str], adversarial_opponents: List[str]) -> Dict[str, Any]:
    all_opponents = elite_opponents + adversarial_opponents
    tasks = [(s, seat, opp, candidate_key) for opp in all_opponents for s in FRESH_SEEDS for seat in (0, 1)]
    print(f"\n--- Running Fresh Evaluation: {candidate_key} ({len(tasks)} legs across 9 opponents) ---")
    t0 = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_fresh_leg, tasks))
    elapsed = time.time() - t0

    overall = compute_metrics(results)
    elite_metrics = compute_metrics([r for r in results if r["opp"] in elite_opponents])
    adv_metrics = compute_metrics([r for r in results if r["opp"] in adversarial_opponents])

    per_opp = {}
    for opp in all_opponents:
        per_opp[opp] = compute_metrics([r for r in results if r["opp"] == opp])

    summary = {
        "candidate": candidate_key,
        "time_seconds": elapsed,
        "overall": overall,
        "elite_suite": elite_metrics,
        "adversarial_suite": adv_metrics,
        "per_opponent": per_opp,
    }

    print(f"  Overall Mean Delta vs V49: {overall['mean_delta_vs_v49']:+.2f} (95% CI [{overall['bootstrap_95_ci'][0]:+.2f}, {overall['bootstrap_95_ci'][1]:+.2f}])")
    print(f"  Overall WR: V49 {overall['win_rate_v49']*100:.2f}% | Cand {overall['win_rate_cand']*100:.2f}% (Rescues: {overall['rescues']}, Casualties: {overall['casualties']})")
    print(f"  Elite Delta: {elite_metrics['mean_delta_vs_v49']:+.2f}, Cand WR: {elite_metrics['win_rate_cand']*100:.2f}%")
    print(f"  Adv Delta: {adv_metrics['mean_delta_vs_v49']:+.2f}, Cand WR: {adv_metrics['win_rate_cand']*100:.2f}%")
    return summary


def main():
    print("=" * 80)
    print("V51 FRESH VALIDATION BENCHMARK (PHASE 11 & 13)")
    print("=" * 80)

    elite_opponents = [
        "V44",
        "dmitrii_lb2800",
        "tetsutani_pasture",
        "kaitofukami_v48_3009",
        "indarkarhana_top10",
        "saiteja_mega_3000",
    ]

    adversarial_opponents = [
        "DAIRY_FLOOD",
        "WOOL_FLOOD",
        "TERMINAL_DUMPER",
    ]

    ladder = {}

    # 1. Baseline Parity Reference: V49 Meta Fusion
    ladder["V49_Meta_Fusion"] = evaluate_candidate("V49_Meta_Fusion", elite_opponents, adversarial_opponents)

    # 2. V51 Blocked Repair Candidate
    ladder["V51_Blocked_Repair"] = evaluate_candidate("V51_Blocked_Repair", elite_opponents, adversarial_opponents)

    # 3. V51 Midgame Reset Variant (Ablation / Research Artifact)
    ladder["V51_Midgame_Reset_Variant"] = evaluate_candidate("V51_Midgame_Reset_Variant", elite_opponents, adversarial_opponents)

    # 4. V51 Sell Slot Reordering Variant (Ablation / Research Artifact)
    ladder["V51_Sell_Reorder_Variant"] = evaluate_candidate("V51_Sell_Reorder_Variant", elite_opponents, adversarial_opponents)

    out_file = os.path.join(REPO_ROOT, "research", "v51", "benchmarks", "v51_fresh_ladder.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(ladder, f, indent=2)
    print(f"\nSaved fresh validation ladder to {out_file}!")


if __name__ == "__main__":
    main()
