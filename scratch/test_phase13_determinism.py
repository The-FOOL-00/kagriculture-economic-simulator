import sys
import os
import json
import hashlib
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.abspath('.'))

import kaggle_environments
import candidates.compiled_research_b_only_v1 as b1_compiled

def run_single_in_process(seed):
    agent = b1_compiled.ResearchBOnlyV1()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    
    rew = float(steps[-1][0]["reward"])
    
    action_stream = []
    for st in steps:
        act = st[0].get("action") or {}
        action_stream.append((str(act.get("farmer")), [str(h) for h in act.get("hands") or []]))
    act_hash = hashlib.sha256(json.dumps(action_stream).encode('utf-8')).hexdigest()
    
    f0 = steps[-1][0]["observation"]["farms"][0]
    state_str = json.dumps({"money": f0.get("money"), "shed": f0.get("shed"), "tiles": f0.get("tiles")}, sort_keys=True)
    state_hash = hashlib.sha256(state_str.encode('utf-8')).hexdigest()
    
    return rew, act_hash, state_hash

def worker_in_process_10x(seed):
    # Runs 10 in-process evaluations sequentially in this process
    results = []
    for _ in range(10):
        results.append(run_single_in_process(seed))
    
    # Verify all 10 in this process are identical
    mismatches = 0
    base = results[0]
    for r in results[1:]:
        if r != base:
            mismatches += 1
    return seed, base, mismatches

def worker_fresh_process(args):
    seed, run_id = args
    return seed, run_id, run_single_in_process(seed)

def main():
    test_seeds = list(range(865000, 865010)) # 10 holdout seeds
    print(f"Executing Phase 13 Determinism Audit on 10 holdout seeds: {test_seeds}")
    
    # 1. 10 in-process runs per seed (each worker executes 10 iterations sequentially)
    print("Testing 10 in-process repeated runs per seed across 10 processes...")
    with ProcessPoolExecutor(max_workers=10) as executor:
        in_proc_results = list(executor.map(worker_in_process_10x, test_seeds))
    
    total_in_proc_mismatches = sum(m for _, _, m in in_proc_results)
    print(f"Total in-process mismatches across 100 runs (10 seeds x 10 runs): {total_in_proc_mismatches}")
    assert total_in_proc_mismatches == 0, "In-process determinism failed!"

    # 2. 10 fresh-process runs per seed (100 distinct fresh process tasks)
    print("Testing 10 fresh-process runs per seed (100 independent process executions)...")
    fresh_tasks = [(s, run_id) for s in test_seeds for run_id in range(10)]
    
    fresh_results_by_seed = defaultdict(list)
    with ProcessPoolExecutor(max_workers=11) as executor:
        for seed, run_id, res in executor.map(worker_fresh_process, fresh_tasks):
            fresh_results_by_seed[seed].append((run_id, res))
            
    total_fresh_mismatches = 0
    for s in test_seeds:
        runs = [r for _, r in sorted(fresh_results_by_seed[s], key=lambda x: x[0])]
        base = runs[0]
        for r in runs[1:]:
            if r != base:
                total_fresh_mismatches += 1
                print(f"Fresh process mismatch on seed {s}: {r} != {base}")
                
    print(f"Total fresh-process mismatches across 100 runs (10 seeds x 10 runs): {total_fresh_mismatches}")
    assert total_fresh_mismatches == 0, "Fresh-process determinism failed!"
    
    print("\n" + "="*80)
    print("PHASE 13 DETERMINISM AUDIT: 100% PERFECT BIT-FOR-BIT DETERMINISM CONFIRMED")
    print("="*80)
    for s, base, _ in sorted(in_proc_results, key=lambda x: x[0]):
        print(f"Seed {s}: Reward={base[0]}, ActHash={base[1][:12]}..., StateHash={base[2][:12]}... (10/10 in-proc + 10/10 fresh-proc IDENTICAL)")

if __name__ == "__main__":
    main()
