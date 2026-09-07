"""
Phase 12: Large-Scale Tournament Evaluation
===========================================
Evaluates `candidate_closed_loop_commitment_v1` across:
- 500 Development seeds (10,000 - 10,499)
- 500 Holdout seeds (20,000 - 20,499)

Against 11 diverse benchmarks:
1. Frozen V2 (Production Slot 2 baseline)
2. Live Flooder (dynamic adversarial flood)
3. Champion Killer (dynamic aggressive competitor)
4. Market Aggressor (dynamic pricing spoiler)
5. Anti-Melon (counter-strategy proxy)
6. Top Meta (balanced elite model)
7. Replay Whyme (elite leaderboard replay)
8. Replay Crop Dusta (elite leaderboard replay)
9. Replay Kawatta (elite leaderboard replay)
10. Replay MTN (elite leaderboard replay)
11. Replay Yuan800 (elite leaderboard replay)

Measures:
- Win / Loss / Tie rate
- Mean candidate reward
- Mean opponent reward
- Net margin
- SE / 95% Confidence Intervals
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import numpy as np
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Opponent paths
OPPONENTS = [
    ("Frozen_V2", "candidates.slot2_aethel_refined_v2", "agent", "Production Slot 2 Benchmark"),
    ("Live_Flooder", "opponents.live_flooder_v1", "agent", "Dynamic Opponent"),
    ("Champion_Killer", "opponents.adversarial_champion_killer", "agent", "Dynamic Opponent"),
    ("Market_Aggressor", "opponents.o9_market_aggressor", "agent", "Dynamic Opponent"),
    ("Anti_Melon", "opponents.o10_anti_melon", "agent", "Dynamic Opponent"),
    ("Top_Meta", "opponents.o12_top_meta", "agent", "Dynamic Opponent"),
    ("Replay_Whyme", "opponents.replay_whyme_labs", "agent", "Elite Replay Evidence"),
    ("Replay_CropDusta", "opponents.replay_crop_dusta", "agent", "Elite Replay Evidence"),
    ("Replay_Kawatta", "opponents.replay_kawatta_taido", "agent", "Elite Replay Evidence"),
    ("Replay_MTN", "opponents.replay_mtn", "agent", "Elite Replay Evidence"),
    ("Replay_Yuan800", "opponents.replay_yuan800", "agent", "Elite Replay Evidence"),
]

def _run_tournament_match(opp_mod, opp_attr, opp_name, seed, seat):
    import importlib
    # Load candidate
    cand_mod = importlib.import_module("candidates.candidate_closed_loop_commitment_v1")
    cand_fn = getattr(cand_mod, "agent")
    
    # Load opponent
    opp_m = importlib.import_module(opp_mod)
    opp_fn = getattr(opp_m, opp_attr)

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    if seat == 0:
        env.run([cand_fn, opp_fn])
        r_cand = float(env.steps[-1][0]["reward"] or 0)
        r_opp = float(env.steps[-1][1]["reward"] or 0)
    else:
        env.run([opp_fn, cand_fn])
        r_cand = float(env.steps[-1][1]["reward"] or 0)
        r_opp = float(env.steps[-1][0]["reward"] or 0)

    margin = r_cand - r_opp
    return {
        "opp": opp_name,
        "seed": seed,
        "seat": seat,
        "r_cand": r_cand,
        "r_opp": r_opp,
        "margin": margin,
        "win": 1 if margin > 0 else 0,
        "loss": 1 if margin < 0 else 0,
        "tie": 1 if margin == 0 else 0
    }

def run_tournament_partition(seeds, partition_name="Development", max_workers=8):
    print(f"\n--- Running Tournament Partition: {partition_name} ({len(seeds)} matches) ---")
    tasks = []
    n_opps = len(OPPONENTS)
    for idx, seed in enumerate(seeds):
        opp_tuple = OPPONENTS[idx % n_opps]
        opp_name, opp_mod, opp_attr, _ = opp_tuple
        seat = idx % 2  # Alternate seats
        tasks.append((opp_mod, opp_attr, opp_name, seed, seat))

    results_by_opp = {opp[0]: [] for opp in OPPONENTS}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(_run_tournament_match, *t): t
            for t in tasks
        }
        for future in as_completed(future_to_task):
            res = future.result()
            results_by_opp[res["opp"]].append(res)

    summary = {}
    print(f"\n{'Opponent':<20} | {'Matches':<8} | {'Win Rate':<10} | {'Mean Cand':<10} | {'Mean Opp':<10} | {'Margin':<12}")
    print("-" * 80)
    for opp_name, res_list in results_by_opp.items():
        if not res_list: continue
        n = len(res_list)
        wins = sum(r["win"] for r in res_list)
        losses = sum(r["loss"] for r in res_list)
        ties = sum(r["tie"] for r in res_list)
        win_rate = (wins / n) * 100.0
        cands = [r["r_cand"] for r in res_list]
        opps = [r["r_opp"] for r in res_list]
        margins = [r["margin"] for r in res_list]

        summary[opp_name] = {
            "n": n,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_rate": float(win_rate),
            "cand_mean": float(np.mean(cands)),
            "cand_std": float(np.std(cands)),
            "opp_mean": float(np.mean(opps)),
            "opp_std": float(np.std(opps)),
            "margin_mean": float(np.mean(margins)),
            "margin_std": float(np.std(margins))
        }
        print(f"{opp_name:<20} | {n:<8} | {win_rate:6.1f}%    | {np.mean(cands):8.1f}   | {np.mean(opps):8.1f}   | {np.mean(margins):+10.1f}")

    return summary

def run_full_tournament(dev_seeds, holdout_seeds, max_workers=10):
    os.makedirs("reports", exist_ok=True)
    t0 = time.time()
    dev_summary = run_tournament_partition(dev_seeds, "Development (Seeds 10,000 - 10,499)", max_workers=max_workers)
    holdout_summary = run_tournament_partition(holdout_seeds, "Holdout (Seeds 20,000 - 20,499)", max_workers=max_workers)

    full_results = {
        "candidate": "candidate_closed_loop_commitment_v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dev_summary": dev_summary,
        "holdout_summary": holdout_summary,
        "total_matches": len(dev_seeds) + len(holdout_seeds),
        "total_elapsed_s": float(time.time() - t0)
    }

    with open("reports/commitment_tournament_results.json", "w") as f:
        json.dump(full_results, f, indent=2)

    print(f"\nTournament completed in {full_results['total_elapsed_s']:.1f}s. Saved to reports/commitment_tournament_results.json")

if __name__ == "__main__":
    dev_seeds = list(range(10000, 10500))      # 500 Dev seeds
    holdout_seeds = list(range(20000, 20500))  # 500 Holdout seeds
    run_full_tournament(dev_seeds, holdout_seeds, max_workers=10)
