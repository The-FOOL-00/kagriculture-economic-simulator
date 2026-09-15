import sys
import os
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.abspath('.'))

from scratch.run_phase2_to_5_study import evaluate_seed_suite

def main():
    seeds = list(range(1250, 1450)) # 200 discovery seeds
    print(f"Running Phase 2-5 evaluation across {len(seeds)} seeds...", flush=True)
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(evaluate_seed_suite, seeds))
        
    with open("scratch/phase2_to_5_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Finished Phase 2-5 evaluation. Saved to scratch/phase2_to_5_results.json.", flush=True)

if __name__ == "__main__":
    main()
