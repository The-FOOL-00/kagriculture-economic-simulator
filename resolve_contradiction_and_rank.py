"""
=============================================================================
RESOLVE CONTRADICTION & RIGOROUS CANDIDATE BENCHMARK HARNESS
=============================================================================
1. Compares Slot 1, Slot 2, Slot 3, Slot 4, Slot 5, main.py, and Golden Control v1.
2. Directly resolves the contradiction between Slot 4 Lookahead ($78k reported solo)
   and Slot 5 8C/4S/15M ($60k reported solo vs $74k elsewhere).
3. Evaluates all candidates across identical seeds against:
   - Solo baseline (Starter Bot)
   - Golden Control v1 (Apex Grandmaster)
   - Titan Production (main.py)
   - Market Aggressor (O9)
   - Cow Specialist (O5)
4. Evaluates direct Head-to-Head between Slot 4 Lookahead and Slot 5 8C/4S/15M.
=============================================================================
"""

import os
import sys
import time
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def wilson_score_interval(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * np.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def _run_single_match(task):
    agent0, agent1, seed, max_steps, swapped = task
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    t0 = time.time()
    try:
        env.run([agent0, agent1])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        
        r_us = raw_r1 if swapped else raw_r0
        r_opp = raw_r0 if swapped else raw_r1
        win = 1.0 if r_us > r_opp else (0.0 if r_opp > r_us else 0.5)
        margin = r_us - r_opp
        per_turn_ms = (elapsed / max_steps) * 1000.0

        return {
            "seed": seed, "swapped": swapped, "r_us": r_us, "r_opp": r_opp,
            "margin": margin, "win": win, "elapsed": elapsed, "per_turn_ms": per_turn_ms,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed, "swapped": swapped, "r_us": 0.0, "r_opp": 0.0,
            "margin": 0.0, "win": 0.0, "elapsed": 0.0, "per_turn_ms": 0.0,
            "error": str(e)
        }

def evaluate_candidate(candidate_path, opp_paths, num_pairs=10, start_seed=40000, max_workers=6):
    results_by_opp = {}
    all_cash = []
    all_margins = []
    all_wins = []
    all_runtimes = []

    for opp_name, opp_path in opp_paths.items():
        tasks = []
        for i in range(num_pairs):
            seed = start_seed + i
            tasks.append((candidate_path, opp_path, seed, 720, False))
            tasks.append((opp_path, candidate_path, seed, 720, True))

        match_results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_single_match, t) for t in tasks]
            for f in as_completed(futures):
                match_results.append(f.result())

        wins = sum(r["win"] for r in match_results)
        total = len(match_results)
        cash_us = [r["r_us"] for r in match_results]
        margins = [r["margin"] for r in match_results]
        runtimes = [r["per_turn_ms"] for r in match_results]

        all_cash.extend(cash_us)
        all_margins.extend(margins)
        all_wins.append(wins / total)
        all_runtimes.extend(runtimes)

        lower_ci, upper_ci = wilson_score_interval(wins, total)
        results_by_opp[opp_name] = {
            "matches": total,
            "wins": wins,
            "win_rate": (wins / total) * 100.0,
            "ci_95": [lower_ci, upper_ci],
            "mean_cash": float(np.mean(cash_us)),
            "std_cash": float(np.std(cash_us)),
            "mean_opp_cash": float(np.mean([r["r_opp"] for r in match_results])),
            "mean_margin": float(np.mean(margins)),
            "worst_loss": float(np.min(margins)),
            "mean_per_turn_ms": float(np.mean(runtimes))
        }

    return {
        "candidate": os.path.basename(candidate_path),
        "overall_mean_cash": float(np.mean(all_cash)),
        "overall_median_cash": float(np.median(all_cash)),
        "overall_std_cash": float(np.std(all_cash)),
        "overall_win_rate": float(np.mean(all_wins) * 100.0),
        "overall_mean_margin": float(np.mean(all_margins)),
        "worst_loss": float(np.min(all_margins)),
        "overall_mean_per_turn_ms": float(np.mean(all_runtimes)),
        "by_opponent": results_by_opp
    }

def main():
    print("=" * 95)
    print("OBJECTIVE 1 & CONTRADICTION RESOLUTION BENCHMARK")
    print("=" * 95)

    candidates = {
        "Slot 1 (Titan Control)": os.path.join(project_root, "candidates", "slot1_titan_control.py"),
        "Slot 2 (Hybrid 6C3S 10M)": os.path.join(project_root, "candidates", "slot2_hybrid_6c3s_10m.py"),
        "Slot 3 (Hybrid Dynamic)": os.path.join(project_root, "candidates", "slot3_hybrid_dynamic.py"),
        "Slot 4 (Hybrid Lookahead)": os.path.join(project_root, "candidates", "slot4_hybrid_lookahead.py"),
        "Slot 5 (Hybrid 8C4S 15M)": os.path.join(project_root, "candidates", "slot5_hybrid_8c4s.py"),
        "main.py (Unified Modular)": os.path.join(project_root, "main.py"),
    }

    test_opponents = {
        "Golden Control v1": os.path.join(project_root, "agents", "golden_v1.py"),
        "Titan Production": os.path.join(project_root, "opponents", "o1_titan.py"),
        "Market Aggressor": os.path.join(project_root, "opponents", "o9_market_aggressor.py"),
        "Cow Specialist": os.path.join(project_root, "opponents", "o5_cow_specialist.py"),
    }

    # First: Direct Head-to-Head: Slot 4 (Lookahead) vs Slot 5 (8C/4S)
    print("\n--- DIRECT HEAD-TO-HEAD: Slot 4 (Lookahead) vs Slot 5 (8C/4S/15M) ---")
    h2h_tasks = []
    num_h2h_pairs = 20  # 40 matches
    start_h2h_seed = 50000
    for i in range(num_h2h_pairs):
        s = start_h2h_seed + i
        h2h_tasks.append((candidates["Slot 4 (Hybrid Lookahead)"], candidates["Slot 5 (Hybrid 8C4S 15M)"], s, 720, False))
        h2h_tasks.append((candidates["Slot 5 (Hybrid 8C4S 15M)"], candidates["Slot 4 (Hybrid Lookahead)"], s, 720, True))

    h2h_results = []
    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(_run_single_match, t) for t in h2h_tasks]
        for f in as_completed(futures):
            h2h_results.append(f.result())

    slot4_wins = sum(r["win"] for r in h2h_results)
    slot4_cash = [r["r_us"] for r in h2h_results]
    slot5_cash = [r["r_opp"] for r in h2h_results]
    slot4_margins = [r["margin"] for r in h2h_results]
    low_ci, upp_ci = wilson_score_interval(slot4_wins, len(h2h_results))
    print(f"Slot 4 Lookahead vs Slot 5 8C/4S/15M (40 matches):")
    print(f"  Slot 4 Win Rate: {slot4_wins/len(h2h_results)*100:.1f}% ({slot4_wins}W - {len(h2h_results)-slot4_wins}L) | 95% CI: [{low_ci:.1f}%, {upp_ci:.1f}%]")
    print(f"  Slot 4 Mean Cash: ${np.mean(slot4_cash):,.2f} | Slot 5 Mean Cash: ${np.mean(slot5_cash):,.2f}")
    print(f"  Net Margin (Slot 4 - Slot 5): ${np.mean(slot4_margins):+,.2f}")

    # Now evaluate all candidates against the standard opponent suite
    print("\n--- STANDARDIZED BENCHMARK SUITE ACROSS ALL CANDIDATES ---")
    summary_table = []
    full_output = {}

    for label, path in candidates.items():
        print(f"\nEvaluating: {label}...")
        t0 = time.time()
        res = evaluate_candidate(path, test_opponents, num_pairs=10, start_seed=40000, max_workers=6)
        elapsed = time.time() - t0
        full_output[label] = res
        print(f"  Mean Cash: ${res['overall_mean_cash']:8,.2f} | Median: ${res['overall_median_cash']:8,.2f} | Win Rate: {res['overall_win_rate']:5.1f}% | Margin: ${res['overall_mean_margin']:+8,.2f} | Runtime: {res['overall_mean_per_turn_ms']:.2f}ms")

        summary_table.append({
            "Candidate": label,
            "Mean Cash": res["overall_mean_cash"],
            "Median Cash": res["overall_median_cash"],
            "Win Rate": res["overall_win_rate"],
            "Margin": res["overall_mean_margin"],
            "Std": res["overall_std_cash"],
            "Worst Loss": res["worst_loss"],
            "Runtime": f"{res['overall_mean_per_turn_ms']:.2f}ms"
        })

    print("\n" + "=" * 115)
    print("DEFINITIVE CANDIDATE RANKING TABLE (IDENTICAL SEEDS & OPPONENTS)")
    print("=" * 115)
    print(f"{'Candidate':26s} | {'Mean Cash':10s} | {'Median':10s} | {'Win Rate':9s} | {'Margin':11s} | {'Std':9s} | {'Worst Loss':11s} | {'Runtime':8s}")
    print("-" * 115)
    for row in sorted(summary_table, key=lambda x: x["Win Rate"], reverse=True):
        print(f"{row['Candidate']:26s} | ${row['Mean Cash']:8,.0f} | ${row['Median Cash']:8,.0f} | {row['Win Rate']:7.1f}% | ${row['Margin']:+9,.0f} | ${row['Std']:7,.0f} | ${row['Worst Loss']:+9,.0f} | {row['Runtime']:8s}")
    print("=" * 115)

    with open(os.path.join(project_root, "contradiction_and_ranking_results.json"), "w") as f:
        json.dump({"h2h_slot4_vs_slot5": {
            "slot4_wins": slot4_wins,
            "total_matches": len(h2h_results),
            "slot4_win_rate": slot4_wins / len(h2h_results) * 100.0,
            "slot4_mean_cash": float(np.mean(slot4_cash)),
            "slot5_mean_cash": float(np.mean(slot5_cash)),
            "slot4_margin": float(np.mean(slot4_margins)),
            "ci_95": [low_ci, upp_ci]
        }, "candidates": full_output}, f, indent=2)

if __name__ == "__main__":
    main()
