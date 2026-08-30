import os
import sys
import time
import math
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def wilson_ci(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def _run_single_match(item):
    a0, a1, seed = item
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    t0 = time.time()
    try:
        env.run([a0, a1])
        elapsed = time.time() - t0
        last = env.steps[-1]
        r0 = float(last[0].reward or 0.0)
        r1 = float(last[1].reward or 0.0)
        return {
            "seed": seed, "r0": r0, "r1": r1, "diff": r0 - r1,
            "win0": 1.0 if r0 > r1 else (0.0 if r1 > r0 else 0.5),
            "elapsed": elapsed, "error": None
        }
    except Exception as e:
        return {
            "seed": seed, "r0": 0.0, "r1": 0.0, "diff": 0.0,
            "win0": 0.0, "elapsed": 0.0, "error": str(e)
        }

def run_paired_h2h(cand_path, opp_path, seed_list, max_workers=6):
    tasks = []
    for s in seed_list:
        tasks.append((cand_path, opp_path, s)) # Cand is P0
        tasks.append((opp_path, cand_path, s)) # Cand is P1

    results_p0 = [] # Cand as P0
    results_p1 = [] # Cand as P1

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_match, t): t for t in tasks}
        for f in as_completed(futures):
            t = futures[f]
            res = f.result()
            if t[0] == cand_path: # Cand was P0
                results_p0.append(res)
            else: # Cand was P1 (opp was P0)
                # Reverse perspective so win/margin is from Cand perspective
                cand_res = {
                    "seed": res["seed"],
                    "r_cand": res["r1"],
                    "r_opp": res["r0"],
                    "margin": res["r1"] - res["r0"],
                    "win": 1.0 if res["r1"] > res["r0"] else (0.0 if res["r0"] > res["r1"] else 0.5),
                    "elapsed": res["elapsed"]
                }
                results_p1.append(cand_res)

    p0_wins = sum(1 for r in results_p0 if r["win0"] == 1.0)
    p0_losses = sum(1 for r in results_p0 if r["win0"] == 0.0)
    p0_ties = sum(1 for r in results_p0 if r["win0"] == 0.5)
    p0_total = len(results_p0)
    p0_wr = (p0_wins / p0_total) * 100.0 if p0_total > 0 else 0.0
    p0_margins = [r["diff"] for r in results_p0]
    p0_cand_cash = [r["r0"] for r in results_p0]

    p1_wins = sum(1 for r in results_p1 if r["win"] == 1.0)
    p1_losses = sum(1 for r in results_p1 if r["win"] == 0.0)
    p1_ties = sum(1 for r in results_p1 if r["win"] == 0.5)
    p1_total = len(results_p1)
    p1_wr = (p1_wins / p1_total) * 100.0 if p1_total > 0 else 0.0
    p1_margins = [r["margin"] for r in results_p1]
    p1_cand_cash = [r["r_cand"] for r in results_p1]

    pooled_wins = p0_wins + p1_wins
    pooled_total = p0_total + p1_total
    pooled_wr = (pooled_wins / pooled_total) * 100.0 if pooled_total > 0 else 0.0
    w_low, w_high = wilson_ci(pooled_wins, pooled_total)

    all_margins = p0_margins + p1_margins
    all_cand_cash = p0_cand_cash + p1_cand_cash

    catastrophic = sum(1 for m in all_margins if m < -10000)

    return {
        "cand": os.path.basename(cand_path),
        "opp": os.path.basename(opp_path),
        "games": pooled_total,
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "pooled_wr": pooled_wr,
        "ci_95": (w_low, w_high),
        "mean_margin": float(np.mean(all_margins)),
        "median_margin": float(np.median(all_margins)),
        "std_margin": float(np.std(all_margins)),
        "mean_cand_cash": float(np.mean(all_cand_cash)),
        "worst_drawdown": float(np.min(all_margins)),
        "catastrophic": catastrophic
    }

if __name__ == "__main__":
    ctrl = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
    titan = os.path.join(project_root, "opponents", "o1_titan.py")
    golden = os.path.join(project_root, "agents", "golden_v1.py")
    batch24 = os.path.join(project_root, "agents", "ablation_batch_24.py")
    batch8 = os.path.join(project_root, "agents", "ablation_batch_8.py")
    emerg = os.path.join(project_root, "agents", "ablation_b_emergency_only.py")

    print("=" * 85)
    print("STEP 1: GROUND-TRUTH SELF-PLAY ASYMMETRY ACROSS 3 INDEPENDENT SEED RANGES")
    print("=" * 85)
    
    seed_ranges = [
        ("Seeds 10000-10049 (N=50 pairs, 100 games)", list(range(10000, 10050))),
        ("Seeds 20000-20049 (N=50 pairs, 100 games)", list(range(20000, 20050))),
        ("Seeds 50000-50049 (N=50 pairs, 100 games)", list(range(50000, 50050))),
    ]

    for label, s_list in seed_ranges:
        t0 = time.time()
        res = run_paired_h2h(ctrl, ctrl, s_list, max_workers=8)
        # Note: In self-play ctrl vs ctrl, P0 WR + P1 WR = 100%
        print(f"\n{label}:")
        print(f"  P0 Win Rate: {res['p0_wr']:5.1f}% | P1 Win Rate: {res['p1_wr']:5.1f}% | Pooled: {res['pooled_wr']:5.1f}%")
        print(f"  Asymmetry (P0 - P1): {res['p0_wr'] - res['p1_wr']:+5.1f}pp")
        print(f"  Mean Final Cash: ${res['mean_cand_cash']:,.2f} | Runtime: {time.time()-t0:.1f}s")

    print("\n" + "=" * 85)
    print("STEP 2: CONTROL VS STANDARD BENCHMARK OPPONENTS (Seeds 50000-50049, 100 games each)")
    print("=" * 85)
    s50 = list(range(50000, 50050))
    for opp_label, opp_file in [("Golden v1", golden), ("Titan Baseline", titan)]:
        t0 = time.time()
        res = run_paired_h2h(ctrl, opp_file, s50, max_workers=8)
        print(f"\nControl vs {opp_label:15s}:")
        print(f"  P0 WR: {res['p0_wr']:5.1f}% | P1 WR: {res['p1_wr']:5.1f}% | Pooled WR: {res['pooled_wr']:5.1f}% | CI: [{res['ci_95'][0]:.1f}%, {res['ci_95'][1]:.1f}%]")
        print(f"  Mean Margin: ${res['mean_margin']:+8,.2f} | Cand Cash: ${res['mean_cand_cash']:,.2f} | Worst: ${res['worst_drawdown']:,.2f} | Catastrophic: {res['catastrophic']}")

    print("\n" + "=" * 85)
    print("STEP 3: VERIFY CAUSAL REPORT CLAIMS (Batch 24, Batch 8, Emergency vs Control on Seeds 50000-50049)")
    print("=" * 85)
    for cand_label, cand_file in [("Batch 8 Only", batch8), ("Batch 24 Only", batch24), ("Emergency Only", emerg)]:
        t0 = time.time()
        res = run_paired_h2h(cand_file, ctrl, s50, max_workers=8)
        print(f"\n{cand_label:18s} vs Control:")
        print(f"  P0 WR: {res['p0_wr']:5.1f}% | P1 WR: {res['p1_wr']:5.1f}% | Pooled WR: {res['pooled_wr']:5.1f}% | CI: [{res['ci_95'][0]:.1f}%, {res['ci_95'][1]:.1f}%]")
        print(f"  Mean Margin: ${res['mean_margin']:+8,.2f} | Cand Cash: ${res['mean_cand_cash']:,.2f} | Worst: ${res['worst_drawdown']:,.2f} | Catastrophic: {res['catastrophic']}")
