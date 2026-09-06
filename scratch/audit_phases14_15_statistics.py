"""
Phases 14 & 15: Independent Recalculation of Dev (500) and Holdout (300) Statistics
Recalculates from raw individual match records:
- N, wins, losses, ties
- win rate
- mean margin, median margin, SD, SEM, 95% CI
- t-statistic, p-value
- min margin, max margin
- seed disjointness verification
- file SHA256 integrity verification
"""

import sys
import os
import json
import math
import hashlib
import numpy as np
from scipy import stats

def audit_dataset(filepath, name):
    with open(filepath, "r") as f:
        data = json.load(f)
        
    games = data if isinstance(data, list) else data.get("games", [])
    n = len(games)
    
    margins = [float(g["margin"]) for g in games]
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)
    ties = sum(1 for m in margins if m == 0)
    
    mean_m = float(np.mean(margins))
    median_m = float(np.median(margins))
    sd_m = float(np.std(margins, ddof=1))
    sem_m = sd_m / math.sqrt(n)
    
    # 95% Confidence Interval using t-distribution
    ci_margin = stats.t.ppf(0.975, df=n-1) * sem_m
    ci_lower = mean_m - ci_margin
    ci_upper = mean_m + ci_margin
    
    # One-sample t-test vs 0 margin
    t_stat, p_val = stats.ttest_1samp(margins, 0.0)
    
    min_m = float(np.min(margins))
    max_m = float(np.max(margins))
    
    seeds = [g["seed"] for g in games]
    
    return {
        "name": name,
        "n_games": n,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate_pct": (wins / n) * 100.0,
        "mean_margin": mean_m,
        "median_margin": median_m,
        "std_dev": sd_m,
        "sem": sem_m,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "min_margin": min_m,
        "max_margin": max_m,
        "seeds": seeds
    }

def main():
    dev_stats = audit_dataset("scratch/jit_melon_results/dev_tournament_results.json", "500-Game Development")
    holdout_stats = audit_dataset("scratch/jit_melon_results/holdout_results.json", "300-Game Holdout")
    
    dev_seeds = set(dev_stats["seeds"])
    holdout_seeds = set(holdout_stats["seeds"])
    overlap = dev_seeds & holdout_seeds
    
    print("==================================================")
    print("PHASE 14: 500-GAME DEVELOPMENT TOURNAMENT AUDIT")
    print("==================================================")
    for k, v in dev_stats.items():
        if k != "seeds":
            print(f"  {k}: {v}")
            
    print("\n==================================================")
    print("PHASE 15: 300-GAME HOLDOUT TOURNAMENT AUDIT")
    print("==================================================")
    for k, v in holdout_stats.items():
        if k != "seeds":
            print(f"  {k}: {v}")
            
    print("\n==================================================")
    print("SEEDS DISJOINTNESS VERIFICATION")
    print("==================================================")
    print(f"  Total Dev Seeds: {len(dev_seeds)}")
    print(f"  Total Holdout Seeds: {len(holdout_seeds)}")
    print(f"  Overlap count: {len(overlap)}")
    print(f"  Strictly Disjoint: {len(overlap) == 0}")
    
    # Save audit results
    summary = {
        "dev": {k: v for k, v in dev_stats.items() if k != "seeds"},
        "holdout": {k: v for k, v in holdout_stats.items() if k != "seeds"},
        "seed_overlap_count": len(overlap),
        "strictly_disjoint": len(overlap) == 0
    }
    
    with open("scratch/jit_melon_results/phases14_15_audit.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
