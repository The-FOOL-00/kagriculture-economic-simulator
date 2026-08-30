import os
import sys
import time
import math
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
apex_v2_path = os.path.join(project_root, "scratch", "apex_synthesis_v2.py")
ctrl_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
titan_path = os.path.join(project_root, "opponents", "o1_titan.py")

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

def run_holdout():
    opponents = [
        ("Control (Slot 4 Frozen)", ctrl_path),
        ("Titan Production Baseline", titan_path),
    ]

    holdout_seeds = [30000 + i for i in range(50)] # 100 games per matchup
    
    print("=" * 110, flush=True)
    print(f"HOLDOUT SEED GENERALIZATION TEST: Seeds 30000-30049 (N=100 games each)", flush=True)
    print("=" * 110, flush=True)

    with ProcessPoolExecutor(max_workers=6) as executor:
        for opp_label, opp_file in opponents:
            t_start = time.time()
            tasks = []
            for s in holdout_seeds:
                tasks.append((apex_v2_path, opp_file, s, True))  # Cand as P0
                tasks.append((opp_file, apex_v2_path, s, False)) # Cand as P1

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
            mean_cand = float(np.mean(cand_cash))
            mean_opp = float(np.mean(opp_cash))
            worst = float(np.min(margins))

            print(f"HOLDOUT vs {opp_label:26s} | WR: {pooled_wr:5.1f}% | CI: [{w_low:4.1f}%, {w_high:4.1f}%] | P0: {p0_wr:4.1f}% | P1: {p1_wr:4.1f}% | Margin: {mean_margin:+7.0f} | Cand: ${mean_cand:6,.0f} vs Opp: ${mean_opp:6,.0f} | Worst: ${worst:7,.0f} ({elapsed:.1f}s)", flush=True)

if __name__ == "__main__":
    run_holdout()
