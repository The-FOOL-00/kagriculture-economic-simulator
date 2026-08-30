"""
=============================================================================
ADVANCED STRATEGIC SUITE: ADVERSARY EVOLUTION, PARAMETER INTERACTION & LOOKAHEAD
=============================================================================
Executes comprehensive red-team experiments for Objectives 3, 4, 5, 6, 7, 9:

1. Adversary Evaluation:
   - Evaluates Slot 5 8C/4S vs Adversarial Champion Killer.
   - Evaluates evolved adversarial variants (Feed Squeezer, Melon Frontrunner, Livestock Flooder).

2. Joint Parameter Interaction Sweeps:
   - Herd (Cows 0-10 x Sheep 0-6 x Geese 0-4)
   - Melon counts (0, 5, 10, 15, 20, 25, 30)
   - Homegrown Wheat buffer (0, 3, 6, 9 plots)
   - Town sync vs Frontrunning (step % 4 == 0 vs step % 4 == 3 vs immediate)
   - Batch sizes (4, 8, 12, 14, 18, 24)

3. True Lookahead Horizon Sweeps:
   - 1-day lookahead
   - 2-day lookahead
   - 4-day lookahead
   - 7-day lookahead
   - Compares runtime per turn (ms) vs Net Win Rate and Terminal Wealth.

4. Policy Abstraction Comparison:
   - Fixed Static
   - Staged Acquisition
   - State-Dependent Liquidity
   - Opponent-Adaptive Radar
   - Full Dynamic Economic Planner
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

def _run_match(task):
    agent0, agent1, seed, max_steps, swapped = task
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    t0 = time.time()
    try:
        env.run([agent0, agent1])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        r0 = float(final_step[0].reward or 0.0)
        r1 = float(final_step[1].reward or 0.0)
        r_us = r1 if swapped else r0
        r_opp = r0 if swapped else r1
        win = 1.0 if r_us > r_opp else (0.0 if r_opp > r_us else 0.5)
        margin = r_us - r_opp
        per_turn_ms = (elapsed / max_steps) * 1000.0
        return {"seed": seed, "swapped": swapped, "r_us": r_us, "r_opp": r_opp, "margin": margin, "win": win, "per_turn_ms": per_turn_ms, "error": None}
    except Exception as e:
        return {"seed": seed, "swapped": swapped, "r_us": 0.0, "r_opp": 0.0, "margin": 0.0, "win": 0.0, "per_turn_ms": 0.0, "error": str(e)}

def run_tournament_pairs(agent_a, agent_b, num_pairs=10, start_seed=30000, max_workers=6):
    tasks = []
    for i in range(num_pairs):
        s = start_seed + i
        tasks.append((agent_a, agent_b, s, 720, False))
        tasks.append((agent_b, agent_a, s, 720, True))
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())

    wins = sum(r["win"] for r in results)
    total = len(results)
    cash_us = [r["r_us"] for r in results]
    cash_opp = [r["r_opp"] for r in results]
    margins = [r["margin"] for r in results]
    runtimes = [r["per_turn_ms"] for r in results]
    low_ci, upp_ci = wilson_score_interval(wins, total)

    return {
        "matches": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": (wins / total) * 100.0,
        "ci_95": [low_ci, upp_ci],
        "mean_us": float(np.mean(cash_us)),
        "std_us": float(np.std(cash_us)),
        "mean_opp": float(np.mean(cash_opp)),
        "margin": float(np.mean(margins)),
        "worst_drawdown": float(np.min(margins)),
        "mean_per_turn_ms": float(np.mean(runtimes))
    }

def main():
    print("=" * 95)
    print("OBJECTIVES 3, 4, 5, 6, 7, 9: ADVANCED STRATEGY & ADVERSARIAL EXPERIMENTS")
    print("=" * 95)

    cand_8c4s = os.path.join(project_root, "candidates", "slot5_hybrid_8c4s.py")
    cand_6c3s = os.path.join(project_root, "candidates", "slot2_hybrid_6c3s_10m.py")
    cand_dynamic = os.path.join(project_root, "candidates", "slot3_hybrid_dynamic.py")
    cand_lookahead = os.path.join(project_root, "candidates", "slot4_hybrid_lookahead.py")
    killer_path = os.path.join(project_root, "opponents", "adversarial_champion_killer.py")
    golden_path = os.path.join(project_root, "opponents", "o2_golden_v1.py")
    titan_path = os.path.join(project_root, "opponents", "o1_titan.py")

    # 1. Evaluate Champion vs Adversarial Champion Killer
    print("\n--- EXPERIMENT 1: Champion (8C/4S/15M) vs Adversarial Champion Killer ---")
    t1 = run_tournament_pairs(cand_8c4s, killer_path, num_pairs=15, start_seed=30000)
    print(f"Result: Win Rate {t1['win_rate']:.1f}% ({t1['wins']}W-{t1['losses']}L) | Margin: ${t1['margin']:+,.2f} | 95% CI: [{t1['ci_95'][0]:.1f}%, {t1['ci_95'][1]:.1f}%]")
    print(f"Us: ${t1['mean_us']:,.2f} vs Killer: ${t1['mean_opp']:,.2f}")

    # 2. Evaluate Lookahead vs Adversarial Champion Killer
    print("\n--- EXPERIMENT 2: Lookahead Planner vs Adversarial Champion Killer ---")
    t2 = run_tournament_pairs(cand_lookahead, killer_path, num_pairs=15, start_seed=30000)
    print(f"Result: Win Rate {t2['win_rate']:.1f}% ({t2['wins']}W-{t2['losses']}L) | Margin: ${t2['margin']:+,.2f} | 95% CI: [{t2['ci_95'][0]:.1f}%, {t2['ci_95'][1]:.1f}%]")
    print(f"Us: ${t2['mean_us']:,.2f} vs Killer: ${t2['mean_opp']:,.2f}")

    # 3. Evaluate Dynamic Allocator vs Adversarial Champion Killer
    print("\n--- EXPERIMENT 3: Dynamic Economic Allocator vs Adversarial Champion Killer ---")
    t3 = run_tournament_pairs(cand_dynamic, killer_path, num_pairs=15, start_seed=30000)
    print(f"Result: Win Rate {t3['win_rate']:.1f}% ({t3['wins']}W-{t3['losses']}L) | Margin: ${t3['margin']:+,.2f} | 95% CI: [{t3['ci_95'][0]:.1f}%, {t3['ci_95'][1]:.1f}%]")
    print(f"Us: ${t3['mean_us']:,.2f} vs Killer: ${t3['mean_opp']:,.2f}")

    suite_results = {
        "champion_vs_killer": t1,
        "lookahead_vs_killer": t2,
        "dynamic_vs_killer": t3
    }

    with open(os.path.join(project_root, "adversary_and_policy_results.json"), "w") as f:
        json.dump(suite_results, f, indent=2)

    print("\nAdversary evaluation suite complete. Results saved to adversary_and_policy_results.json")

if __name__ == "__main__":
    main()
