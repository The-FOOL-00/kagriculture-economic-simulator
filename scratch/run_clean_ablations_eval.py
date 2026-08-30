import os
import sys
import time
import math
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
ablation_dir = os.path.join(project_root, "scratch", "clean_ablations")
apex_base_file = os.path.join(ablation_dir, "apex_base.py")

ablation_tests = [
    ("A1: Apex Base Self-Play (Verification)", "apex_base.py"),
    ("A2: Apex without 2-Day Feed Buffer (4-Day Revert)", "apex_no_2day_feed.py"),
    ("A3: Apex without Cycle-2 Melons (0 Secondary Melons)", "apex_no_cycle2_melon.py"),
    ("A4: Apex without Batch 24 (Revert to Batch 14)", "apex_no_batch24.py"),
    ("A5: Apex without Emergency Liquidity", "apex_no_emergency.py"),
    ("A6: Apex without Day-0 Land Opening", "apex_no_day0_land.py"),
]

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

def main():
    print("=" * 125, flush=True)
    print("PART 8 & 9: CAUSAL ATTRIBUTION 1-FACTOR ABLATIONS (N=100 matches vs Apex Base)", flush=True)
    print("=" * 125, flush=True)

    seeds = [50000 + i for i in range(50)]
    results = []

    with ProcessPoolExecutor(max_workers=6) as executor:
        for label, fname in ablation_tests:
            fpath = os.path.join(ablation_dir, fname)
            tasks = []
            for s in seeds:
                # Cand is the ablation variant, Opp is Apex Base
                tasks.append((fpath, apex_base_file, s, True))
                tasks.append((apex_base_file, fpath, s, False))

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

            # Calculate Apex Base gain over this ablation
            apex_gain_margin = -mean_margin
            apex_gain_wr = (100.0 - pooled_wr) - 50.0

            print(f"{label:55s} | Ablation WR: {pooled_wr:5.1f}% | CI: [{w_low:4.1f}%, {w_high:4.1f}%] | Margin vs Apex: {mean_margin:+7.0f} | Apex Gain: {apex_gain_margin:+7.0f} cash ({elapsed:.1f}s)", flush=True)

            results.append({
                "label": label, "file": fname,
                "ablation_wr": pooled_wr, "ci_95": [w_low, w_high],
                "p0_wr": p0_wr, "p1_wr": p1_wr,
                "margin_vs_apex": mean_margin, "median_margin": median_margin,
                "apex_gain_margin": apex_gain_margin,
                "mean_ablation_cash": mean_cand, "mean_apex_cash": mean_opp,
                "worst_drawdown": worst, "elapsed_sec": elapsed
            })

    out_json = os.path.join(project_root, "scratch", "causal_attribution_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nCausal attribution ablation results saved to: {out_json}", flush=True)

if __name__ == "__main__":
    main()
