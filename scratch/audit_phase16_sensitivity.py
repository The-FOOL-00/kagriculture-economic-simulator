"""
Phase 16: Sensitivity to Exact Opening Parameters
Tests whether Candidate H's economic advantage is brittle or robust to small perturbations:
- Melons: 11 vs 12 vs 13
- Workers: 5 vs 6
- Feed: 1 vs 2 vs 3 units JIT
Evaluates 10 matched seeds vs Frozen V2 for each variant using ProcessPoolExecutor.
"""

import sys
import os
import json
import copy
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import CANONICAL_JIT_TRACE

SEEDS = list(range(3000, 3010)) # 10 seeds per variant = 60 games total

class PerturbedHAgent:
    def __init__(self, melon_count=12, worker_count=5, feed_count=2):
        self.melon_count = melon_count
        self.worker_count = worker_count
        self.feed_count = feed_count
        
    def __call__(self, obs, config=None):
        step = obs.get("step")
        if step is None:
            step = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        else:
            step = int(step or 0)
            
        if step >= 712:
            return v2._terminal_action(obs)
            
        action = copy.deepcopy(CANONICAL_JIT_TRACE[min(step, len(CANONICAL_JIT_TRACE) - 1)])
        
        if step == 0:
            hires = [["HIRE"] for _ in range(self.worker_count)]
            animals = [["BUY_ANIMAL", "SHEEP", 2], ["BUY_ANIMAL", "COW", 2]]
            wheat_seeds = max(1, 19 - self.melon_count)
            seeds = [["BUY_SEED", "WHEAT", wheat_seeds], ["BUY_SEED", "MELON", self.melon_count]]
            action["market"] = hires + animals + seeds
        elif step == 1:
            if self.feed_count > 0:
                action["market"] = [["BUY_PRODUCT", "WHEAT", self.feed_count]]
            else:
                action["market"] = []
                
        return action

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

def evaluate_variant(args):
    variant_name, melon_c, worker_c, feed_c, seed = args
    cand_fn = PerturbedHAgent(melon_c, worker_c, feed_c)
    
    cfg = {"seed": seed, "episodeSteps": 720}
    env = make("kaggriculture", configuration=cfg)
    env.run([cand_fn, robust(v2.agent)])
    
    r_cand = float(env.steps[-1][0]["reward"] or 0)
    r_v2 = float(env.steps[-1][1]["reward"] or 0)
    margin = r_cand - r_v2
    win = 1.0 if r_cand > r_v2 else (0.5 if r_cand == r_v2 else 0.0)
    
    return {
        "variant": variant_name,
        "seed": seed,
        "r_cand": r_cand,
        "r_v2": r_v2,
        "margin": margin,
        "win": win
    }

def main():
    variants = [
        # Baseline
        ("Baseline (12M, 5W, 2F)", 12, 5, 2),
        # Melon variations
        ("11 Melons (11M, 5W, 2F)", 11, 5, 2),
        ("13 Melons (13M, 5W, 2F)", 13, 5, 2),
        # Worker variations
        ("6 Workers (12M, 6W, 2F)", 12, 6, 2),
        # Feed variations
        ("1 Feed JIT (12M, 5W, 1F)", 12, 5, 1),
        ("3 Feed JIT (12M, 5W, 3F)", 12, 5, 3),
    ]
    
    tasks = []
    for var_name, m_c, w_c, f_c in variants:
        for s in SEEDS:
            tasks.append((var_name, m_c, w_c, f_c, s))
            
    print(f"Running Phase 16 sensitivity sweep: {len(tasks)} games across {len(variants)} variants...")
    
    with ProcessPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(evaluate_variant, tasks))
        
    grouped = {}
    for r in results:
        v = r["variant"]
        if v not in grouped: grouped[v] = []
        grouped[v].append(r)
        
    summary = {}
    for v, records in grouped.items():
        margins = [r["margin"] for r in records]
        wins = [r["win"] for r in records]
        summary[v] = {
            "n_games": len(records),
            "win_rate_pct": float(np.mean(wins) * 100.0),
            "mean_margin": float(np.mean(margins)),
            "median_margin": float(np.median(margins)),
            "std_margin": float(np.std(margins, ddof=1)),
            "min_margin": float(np.min(margins)),
            "max_margin": float(np.max(margins))
        }
        
    print("\n--- PHASE 16 SENSITIVITY SUMMARY ---")
    print(json.dumps(summary, indent=2))
    
    with open("scratch/jit_melon_results/phase16_sensitivity_results.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
