import os
import sys
import time
import math
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
strat_dir = os.path.join(project_root, "scratch", "strategy_candidates")

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

def run_strategy_tournament():
    ctrl_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
    titan_path = os.path.join(project_root, "opponents", "o1_titan.py")
    
    candidate_files = [
        ("S1: Control Baseline (8C/4S/15M/B14)", os.path.join(strat_dir, "s1_control_exact.py")),
        ("S2: Pure Crop (0C/0S/25M/B14)", os.path.join(strat_dir, "s2_pure_crop.py")),
        ("S3: Pure Livestock (10C/5S/0M/B14)", os.path.join(strat_dir, "s3_pure_livestock.py")),
        ("S4: Cow Heavy (10C/2S/15M/B24+Em)", os.path.join(strat_dir, "s4_cow_heavy.py")),
        ("S5: Sheep Heavy (4C/8S/15M/B24+Em)", os.path.join(strat_dir, "s5_sheep_heavy.py")),
        ("S6: Synthesis Peak (8C/4S/15M/B24+Em)", os.path.join(strat_dir, "s6_synthesis_peak.py")),
        ("S7: High Melon (8C/4S/20M/B24+Em)", os.path.join(strat_dir, "s7_high_melon.py")),
        ("S8: Fast Hybrid (6C/3S/10M/B24+Em)", os.path.join(strat_dir, "s8_fast_hybrid.py")),
        ("S9: Batch 18 Synth (8C/4S/15M/B18+Em)", os.path.join(strat_dir, "s9_batch18_synthesis.py")),
    ]

    seeds = [50000 + i for i in range(25)] # 50 games per matchup
    
    print("=" * 105, flush=True)
    print("STRATEGY SPACE EVALUATION: 9 STRATEGIC FAMILIES VS IMMUTABLE CONTROL (N=50 matches each)", flush=True)
    print("=" * 105, flush=True)

    results_vs_ctrl = []
    
    with ProcessPoolExecutor(max_workers=6) as executor:
        for label, c_path in candidate_files:
            t_start = time.time()
            tasks = []
            for s in seeds:
                tasks.append((c_path, ctrl_path, s, True))  # Cand as P0
                tasks.append((ctrl_path, c_path, s, False)) # Cand as P1

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
            catastrophic = sum(1 for m in margins if m < -10000)

            print(f"{label:40s} | Pooled WR: {pooled_wr:5.1f}% | CI: [{w_low:4.1f}%, {w_high:4.1f}%] | P0: {p0_wr:4.1f}% | P1: {p1_wr:4.1f}% | Margin: {mean_margin:+7.0f} | Cand: ${mean_cand:6,.0f} vs Ctrl: ${mean_opp:6,.0f} | Worst: ${worst:7,.0f} ({elapsed:.1f}s)", flush=True)

            results_vs_ctrl.append({
                "label": label, "file": os.path.basename(c_path),
                "pooled_wr": pooled_wr, "ci_95": [w_low, w_high],
                "p0_wr": p0_wr, "p1_wr": p1_wr,
                "mean_margin": mean_margin, "mean_cand_cash": mean_cand, "mean_opp_cash": mean_opp,
                "worst_drawdown": worst, "catastrophic": catastrophic, "elapsed_sec": elapsed
            })

    # Save to json
    out_json = os.path.join(project_root, "scratch", "strategy_space_results.json")
    with open(out_json, "w") as f:
        json.dump(results_vs_ctrl, f, indent=2)
    print(f"\nSaved strategy evaluation to: {out_json}", flush=True)

if __name__ == "__main__":
    run_strategy_tournament()
