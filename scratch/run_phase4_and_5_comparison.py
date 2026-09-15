import sys
import os
import json
import numpy as np
from collections import defaultdict
from scipy import stats
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from scratch.run_pasture_causal_ablations_50seeds import MechanismAAgent
from scratch.conditional_policy_agents import (
    PolicyC1Agent, PolicyC2Agent, PolicyC3Agent, PolicyC4Agent, PolicyC5Agent, SheepFirstAgent
)
from scratch.run_phase2_to_5_study import run_single_agent

def evaluate_seed_policies(seed):
    # Evaluates C1, C2, C3, C4, C5, SheepFirst on a given seed
    c1 = run_single_agent(PolicyC1Agent(50), seed)
    c5 = run_single_agent(PolicyC5Agent(50), seed)
    sheep_first = run_single_agent(SheepFirstAgent(50), seed)
    
    return {
        "seed": seed,
        "c1": c1,
        "c5": c5,
        "sheep_first": sheep_first
    }

def main():
    seeds = list(range(1250, 1450)) # 200 discovery seeds
    print(f"Running Policy C1, C5, SheepFirst evaluation across {len(seeds)} seeds...", flush=True)
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(evaluate_seed_policies, seeds))
        
    with open("scratch/conditional_policies_200seeds_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Finished conditional policy evaluation. Saved to scratch/conditional_policies_200seeds_results.json.", flush=True)

if __name__ == "__main__":
    main()
