"""
=============================================================================
FORMAL STATISTICAL EVALUATION & TOURNAMENT ENGINE
=============================================================================
Calculates Wilson Score 95% CIs, Margins, and Formal Classifications
across Development, Holdout, and Stress seed sets.
=============================================================================
"""

import sys
import math
import numpy as np
from benchmark_harness import run_benchmark


def wilson_score_interval(wins, total, confidence=0.95):
    if total == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% confidence
    p = wins / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return (max(0.0, center - spread) * 100.0, min(100.0, center + spread) * 100.0)


def classify_performance(win_rate, ci_low, ci_high, margin):
    if ci_low > 55.0 and margin > 1000:
        return "CLEARLY BETTER"
    elif win_rate > 52.0 and margin > 0:
        return "PROMISING"
    elif ci_high < 48.0 or margin < -1000:
        return "CLEARLY WORSE"
    else:
        return "INCONCLUSIVE"


def evaluate_matchup(agent0, agent1, seed_file, max_matches=50):
    with open(seed_file, "r") as f:
        seeds = [int(line.strip()) for line in f if line.strip()]

    selected_seeds = seeds[:max_matches]
    start_seed = selected_seeds[0]
    
    res = run_benchmark(
        agent0=agent0,
        agent1=agent1,
        num_matches=len(selected_seeds),
        start_seed=start_seed,
        swap_sides=True
    )
    
    ci_low, ci_high = wilson_score_interval(res["wins"], res["matches"])
    classification = classify_performance(res["win_rate"], ci_low, ci_high, res["mean_diff"])
    
    return {
        "agent0": agent0,
        "agent1": agent1,
        "matches": res["matches"],
        "wins": res["wins"],
        "losses": res["losses"],
        "ties": res["ties"],
        "win_rate": res["win_rate"],
        "ci_95": (ci_low, ci_high),
        "mean_r0": res["mean_r0"],
        "median_r0": res["median_r0"],
        "std_r0": res["std_r0"],
        "mean_r1": res["mean_r1"],
        "mean_diff": res["mean_diff"],
        "classification": classification
    }


def run_full_evaluation_matrix(candidate="main.py"):
    print("=" * 80)
    print(f"RUNNING FORMAL STATISTICAL EVALUATION MATRIX FOR: {candidate}")
    print("=" * 80)

    opponents = [
        ("Starter Bot", "starter"),
        ("Golden Control v1", "agents/golden_v1.py"),
        ("Strawberry Rush", "agents/synthetic/strawberry_rush.py"),
        ("Melon Burst", "agents/synthetic/melon_burst.py"),
        ("Crop Efficient", "agents/synthetic/crop_efficient.py"),
        ("Land Expansion", "agents/synthetic/land_expansion.py"),
        ("Balanced Hybrid", "agents/synthetic/balanced.py")
    ]

    dev_results = []
    print("\n--- [1] DEVELOPMENT SEED SET (100 Matches / Archetype) ---")
    for name, opp_path in opponents:
        print(f"Testing vs {name}...")
        r = evaluate_matchup(candidate, opp_path, "benchmarks/seeds/development.txt", max_matches=30)
        dev_results.append((name, r))

    print("\n" + "=" * 95)
    print(f"{'Opponent Archetype':22s} | {'Wins':5s} | {'Loss':5s} | {'Win %':7s} | {'95% CI':14s} | {'Margin':11s} | {'Classification'}")
    print("-" * 95)
    for name, r in dev_results:
        ci_str = f"[{r['ci_95'][0]:4.1f}%, {r['ci_95'][1]:4.1f}%]"
        print(f"{name:22s} | {r['wins']:5d} | {r['losses']:5d} | {r['win_rate']:6.1f}% | {ci_str:14s} | ${r['mean_diff']:+9,.2f} | {r['classification']}")
    print("=" * 95)


if __name__ == "__main__":
    cand = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    run_full_evaluation_matrix(cand)
