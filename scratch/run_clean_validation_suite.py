import os
import sys
import time
import math
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
apex_file = os.path.join(project_root, "agents", "apex_v2_frozen.py")
ctrl_file = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
titan_file = os.path.join(project_root, "opponents", "o1_titan.py")
golden_file = os.path.join(project_root, "agents", "golden_v1.py")
pure_live_file = os.path.join(project_root, "scratch", "strategy_candidates", "s3_pure_livestock.py")

def wilson_ci(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def _run_single_match(item):
    a0_path, a1_path, seed, cand_is_p0 = item
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    try:
        env.run([a0_path, a1_path])
        elapsed = time.time() - t0
        last = env.steps[-1]
        r0 = float(last[0].reward or 0.0)
        r1 = float(last[1].reward or 0.0)
        
        if cand_is_p0:
            r_cand = r0
            r_opp = r1
        else:
            r_cand = r1
            r_opp = r0
            
        margin = r_cand - r_opp
        win = 1.0 if r_cand > r_opp else (0.0 if r_opp > r_cand else 0.5)
        return {
            "seed": seed, "cand_is_p0": cand_is_p0,
            "r_cand": r_cand, "r_opp": r_opp,
            "margin": margin, "win": win,
            "elapsed": elapsed, "error": None
        }
    except Exception as e:
        return {
            "seed": seed, "cand_is_p0": cand_is_p0,
            "r_cand": 0.0, "r_opp": 0.0,
            "margin": 0.0, "win": 0.0,
            "elapsed": 0.0, "error": str(e)
        }

def evaluate_matchup(executor, cand_path, opp_path, seeds, label):
    tasks = []
    for s in seeds:
        tasks.append((cand_path, opp_path, s, True))  # Cand as P0
        tasks.append((opp_path, cand_path, s, False)) # Cand as P1

    t_start = time.time()
    futures = [executor.submit(_run_single_match, t) for t in tasks]
    matches = [f.result() for f in futures]
    elapsed = time.time() - t_start

    p0_res = [r for r in matches if r["cand_is_p0"]]
    p1_res = [r for r in matches if not r["cand_is_p0"]]

    p0_wins = sum(1 for r in p0_res if r["win"] == 1.0)
    p1_wins = sum(1 for r in p1_res if r["win"] == 1.0)
    total_wins = p0_wins + p1_wins
    total_games = len(matches)

    p0_wr = (p0_wins / len(p0_res)) * 100.0 if p0_res else 0.0
    p1_wr = (p1_wins / len(p1_res)) * 100.0 if p1_res else 0.0
    pooled_wr = (total_wins / total_games) * 100.0 if total_games else 0.0
    w_low, w_high = wilson_ci(total_wins, total_games)

    margins = [r["margin"] for r in matches]
    cand_cash = [r["r_cand"] for r in matches]
    opp_cash = [r["r_opp"] for r in matches]

    mean_margin = float(np.mean(margins))
    median_margin = float(np.median(margins))
    mean_cand = float(np.mean(cand_cash))
    mean_opp = float(np.mean(opp_cash))
    worst = float(np.min(margins))
    catastrophic = sum(1 for m in margins if m < -10000)

    print(f"{label:35s} | WR: {pooled_wr:5.1f}% | CI: [{w_low:4.1f}%, {w_high:4.1f}%] | P0: {p0_wr:4.1f}% | P1: {p1_wr:4.1f}% | Margin: {mean_margin:+7.0f} (Med: {median_margin:+7.0f}) | Cand: ${mean_cand:6,.0f} vs Opp: ${mean_opp:6,.0f} | Worst: ${worst:7,.0f} ({elapsed:.1f}s)", flush=True)

    return {
        "label": label, "games": total_games,
        "pooled_wr": pooled_wr, "ci_95": [w_low, w_high],
        "p0_wr": p0_wr, "p1_wr": p1_wr,
        "mean_margin": mean_margin, "median_margin": median_margin,
        "mean_cand_cash": mean_cand, "mean_opp_cash": mean_opp,
        "worst_drawdown": worst, "catastrophic_rate": (catastrophic / total_games) * 100.0,
        "elapsed_sec": elapsed
    }

def main():
    print("=" * 125, flush=True)
    print("FRESH RIGOROUS EXPERIMENTAL VERIFICATION SUITE: APEX V2 VS CONTROL & MULTI-ARCHETYPE ECOSYSTEM", flush=True)
    print("=" * 125, flush=True)

    seeds_primary = [50000 + i for i in range(50)] # 100 games per matchup
    
    results = {}
    with ProcessPoolExecutor(max_workers=6) as executor:
        # Part 4 & 5: Paired comparison of Apex vs Opponent and Control vs Opponent
        results["Apex_vs_Ctrl"] = evaluate_matchup(executor, apex_file, ctrl_file, seeds_primary, "Apex v2 vs Frozen Control")
        results["Ctrl_vs_Titan"] = evaluate_matchup(executor, ctrl_file, titan_file, seeds_primary, "Control vs Titan Baseline")
        results["Apex_vs_Titan"] = evaluate_matchup(executor, apex_file, titan_file, seeds_primary, "Apex v2 vs Titan Baseline")
        results["Ctrl_vs_Golden"] = evaluate_matchup(executor, ctrl_file, golden_file, seeds_primary, "Control vs Golden Control v1")
        results["Apex_vs_Golden"] = evaluate_matchup(executor, apex_file, golden_file, seeds_primary, "Apex v2 vs Golden Control v1")
        results["Ctrl_vs_PureLive"] = evaluate_matchup(executor, ctrl_file, pure_live_file, seeds_primary, "Control vs Pure Livestock Fleet")
        results["Apex_vs_PureLive"] = evaluate_matchup(executor, apex_file, pure_live_file, seeds_primary, "Apex v2 vs Pure Livestock Fleet")

        # Part 6: Holdout Verification on Seeds 30000-30049 and New Untouched Block 40000-40049
        print("-" * 125, flush=True)
        print("PART 6: HOLDOUT SEED VERIFICATION", flush=True)
        print("-" * 125, flush=True)
        seeds_holdout1 = [30000 + i for i in range(50)]
        seeds_holdout2 = [40000 + i for i in range(50)] # Completely untouched block

        results["Holdout1_Apex_vs_Ctrl"] = evaluate_matchup(executor, apex_file, ctrl_file, seeds_holdout1, "Holdout 30k: Apex vs Control")
        results["Holdout1_Apex_vs_Titan"] = evaluate_matchup(executor, apex_file, titan_file, seeds_holdout1, "Holdout 30k: Apex vs Titan")
        results["Holdout2_Apex_vs_Ctrl"] = evaluate_matchup(executor, apex_file, ctrl_file, seeds_holdout2, "Holdout 40k: Apex vs Control (NEW)")
        results["Holdout2_Apex_vs_Titan"] = evaluate_matchup(executor, apex_file, titan_file, seeds_holdout2, "Holdout 40k: Apex vs Titan (NEW)")

    out_json = os.path.join(project_root, "scratch", "fresh_verification_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFresh verification results saved to: {out_json}", flush=True)

if __name__ == "__main__":
    main()
