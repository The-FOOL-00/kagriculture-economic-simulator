"""
=============================================================================
PARAMETER INTERACTION & LOOKAHEAD HORIZON SWEEPS (OBJECTIVES 5, 6, 9)
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

from candidates.slot5_hybrid_8c4s import Hybrid6C3S10MAgent as StandaloneAgent
from candidates.slot4_hybrid_lookahead import HybridLookaheadAgent

def _run_single_sim(task):
    agent_inst_or_path, opp_path, seed, max_steps = task
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    t0 = time.time()
    try:
        env.run([agent_inst_or_path, opp_path])
        elapsed = time.time() - t0
        r_us = float(env.steps[-1][0].reward or 0.0)
        r_opp = float(env.steps[-1][1].reward or 0.0)
        win = 1.0 if r_us > r_opp else (0.0 if r_opp > r_us else 0.5)
        margin = r_us - r_opp
        per_turn_ms = (elapsed / max_steps) * 1000.0
        return {"seed": seed, "r_us": r_us, "r_opp": r_opp, "win": win, "margin": margin, "per_turn_ms": per_turn_ms}
    except Exception as e:
        return {"seed": seed, "r_us": 0.0, "r_opp": 0.0, "win": 0.0, "margin": 0.0, "per_turn_ms": 0.0}

def sweep_parameter_grid():
    print("=" * 95)
    print("OBJECTIVES 5, 6, 9: RIGOROUS PARAMETER & LOOKAHEAD HORIZON SWEEPS")
    print("=" * 95)

    golden_opp = os.path.join(project_root, "opponents", "o2_golden_v1.py")
    test_seeds = list(range(60000, 60020))  # 20 seeds

    # 1. Lookahead Horizon Sweep (0, 1, 2, 4, 7 days)
    print("\n--- SWEEP 1: LOOKAHEAD HORIZON (0, 1, 2, 4, 7 DAYS) ---")
    horizons = [0, 1, 2, 4, 7]
    lookahead_results = {}
    for h in horizons:
        agent_obj = HybridLookaheadAgent(base_cows=8, base_sheep=4, base_melons=15, lookahead_days=h)
        tasks = [(agent_obj, golden_opp, s, 720) for s in test_seeds]
        with ProcessPoolExecutor(max_workers=6) as executor:
            res = [f.result() for f in as_completed([executor.submit(_run_single_sim, t) for t in tasks])]
        cash = [r["r_us"] for r in res]
        wins = sum(r["win"] for r in res)
        margins = [r["margin"] for r in res]
        runtimes = [r["per_turn_ms"] for r in res]
        lookahead_results[f"{h}_day"] = {
            "horizon_days": h,
            "mean_cash": float(np.mean(cash)),
            "std_cash": float(np.std(cash)),
            "win_rate": (wins / len(res)) * 100.0,
            "margin": float(np.mean(margins)),
            "mean_turn_ms": float(np.mean(runtimes))
        }
        print(f"  Horizon {h:1d} days: Mean Cash ${np.mean(cash):8,.2f} | Win Rate {wins/len(res)*100:5.1f}% | Margin ${np.mean(margins):+8,.2f} | Runtime {np.mean(runtimes):.2f}ms")

    # 2. Herd Fleet Size Sweep
    print("\n--- SWEEP 2: HERD FLEET SIZE (COWS x SHEEP x GEESE) ---")
    herd_configs = [
        ("0C/0S/0G (Pure Crop)", 0, 0, 0, 25),
        ("4C/2S/0G (Light)", 4, 2, 0, 15),
        ("6C/3S/0G (Baseline)", 6, 3, 0, 10),
        ("8C/4S/0G (High-Capacity)", 8, 4, 0, 15),
        ("10C/5S/0G (Extreme)", 10, 5, 0, 15),
        ("8C/0S/0G (Pure Cow)", 8, 0, 0, 15),
        ("0C/8S/0G (Pure Sheep)", 0, 8, 0, 15),
        ("6C/3S/4G (Goose Hybrid)", 6, 3, 4, 10),
    ]
    herd_results = {}
    for label, c, s, g, m in herd_configs:
        agent_obj = StandaloneAgent(target_cows=c, target_sheep=s, target_geese=g, target_melons=m)
        tasks = [(agent_obj, golden_opp, seed, 720) for seed in test_seeds]
        with ProcessPoolExecutor(max_workers=6) as executor:
            res = [f.result() for f in as_completed([executor.submit(_run_single_sim, t) for t in tasks])]
        cash = [r["r_us"] for r in res]
        wins = sum(r["win"] for r in res)
        margins = [r["margin"] for r in res]
        herd_results[label] = {
            "mean_cash": float(np.mean(cash)),
            "std_cash": float(np.std(cash)),
            "win_rate": (wins / len(res)) * 100.0,
            "margin": float(np.mean(margins))
        }
        print(f"  {label:24s}: Mean Cash ${np.mean(cash):8,.2f} | Win Rate {wins/len(res)*100:5.1f}% | Margin ${np.mean(margins):+8,.2f}")

    # 3. Melon Count Sweep (0, 5, 10, 15, 20, 25, 30)
    print("\n--- SWEEP 3: DAY-0 MELON COUNT (0 to 30) ---")
    melon_counts = [0, 5, 10, 15, 20, 25, 30]
    melon_results = {}
    for mc in melon_counts:
        agent_obj = StandaloneAgent(target_cows=8, target_sheep=4, target_geese=0, target_melons=mc)
        tasks = [(agent_obj, golden_opp, seed, 720) for seed in test_seeds]
        with ProcessPoolExecutor(max_workers=6) as executor:
            res = [f.result() for f in as_completed([executor.submit(_run_single_sim, t) for t in tasks])]
        cash = [r["r_us"] for r in res]
        wins = sum(r["win"] for r in res)
        margins = [r["margin"] for r in res]
        melon_results[f"{mc}_melons"] = {
            "count": mc,
            "mean_cash": float(np.mean(cash)),
            "std_cash": float(np.std(cash)),
            "win_rate": (wins / len(res)) * 100.0,
            "margin": float(np.mean(margins))
        }
        print(f"  {mc:2d} Melons: Mean Cash ${np.mean(cash):8,.2f} | Win Rate {wins/len(res)*100:5.1f}% | Margin ${np.mean(margins):+8,.2f}")

    # 4. Market Batch Size Sweep (4, 8, 12, 14, 18, 24)
    print("\n--- SWEEP 4: MARKET SELL BATCH SIZE (4 to 24) ---")
    batch_sizes = [4, 8, 12, 14, 18, 24]
    batch_results = {}
    for bs in batch_sizes:
        agent_obj = StandaloneAgent(target_cows=8, target_sheep=4, target_geese=0, target_melons=15, sell_batch=bs)
        tasks = [(agent_obj, golden_opp, seed, 720) for seed in test_seeds]
        with ProcessPoolExecutor(max_workers=6) as executor:
            res = [f.result() for f in as_completed([executor.submit(_run_single_sim, t) for t in tasks])]
        cash = [r["r_us"] for r in res]
        wins = sum(r["win"] for r in res)
        margins = [r["margin"] for r in res]
        batch_results[f"batch_{bs}"] = {
            "batch_size": bs,
            "mean_cash": float(np.mean(cash)),
            "std_cash": float(np.std(cash)),
            "win_rate": (wins / len(res)) * 100.0,
            "margin": float(np.mean(margins))
        }
        print(f"  Batch {bs:2d}: Mean Cash ${np.mean(cash):8,.2f} | Win Rate {wins/len(res)*100:5.1f}% | Margin ${np.mean(margins):+8,.2f}")

    all_sweeps = {
        "lookahead_sweep": lookahead_results,
        "herd_sweep": herd_results,
        "melon_sweep": melon_results,
        "batch_sweep": batch_results
    }

    with open(os.path.join(project_root, "sweep_experimental_results.json"), "w") as f:
        json.dump(all_sweeps, f, indent=2)

    print("\nAll sweeps complete. Saved to sweep_experimental_results.json")

if __name__ == "__main__":
    sweep_parameter_grid()
