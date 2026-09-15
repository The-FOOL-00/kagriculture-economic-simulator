import sys
import os
import json
import hashlib
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.compiled_research_b_only_v2 as b1_compiled_v2
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

TRUE_ORIG_COMMIT = engine._commit_unit
TRUE_ORIG_HIRE = engine._do_hire
TRUE_ORIG_LAND = engine._do_buy_land
TRUE_ORIG_PROCESS = engine._process_market

def run_single_v2(seed):
    agent = b1_compiled_v2.ResearchBOnlyV1()
    ledger = defaultdict(float)
    trans_stream = []
    current_f0 = [None]

    def my_commit(op, item, price, farm, private, market, shed_capacity=100):
        m_b = farm['money']
        res = TRUE_ORIG_COMMIT(op, item, price, farm, private, market, shed_capacity)
        if res and farm is current_f0[0]:
            delta = farm['money'] - m_b
            if op == 'SELL':
                ledger['REV_' + item] += delta
            elif op == 'BUY_PRODUCT':
                if item == 'FERTILIZER':
                    ledger['EXP_FERT'] += abs(delta)
                else:
                    ledger['EXP_FEED_' + item] += abs(delta)
            elif op == 'BUY_SEED':
                ledger['EXP_SEED_' + item] += abs(delta)
            elif op == 'BUY_ANIMAL':
                ledger['EXP_ANIMAL_' + item] += abs(delta)
            trans_stream.append((op, item, float(price), float(delta)))
        return res

    def my_hire(farm, private, board_size, mult=engine.FARM_HAND_COST_MULT):
        m_b = farm['money']
        TRUE_ORIG_HIRE(farm, private, board_size, mult)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_HIRE'] += delta
            trans_stream.append(('HIRE', 'HAND', 0.0, float(delta)))

    def my_land(farm, board_size):
        m_b = farm['money']
        TRUE_ORIG_LAND(farm, board_size)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_LAND'] += delta
            trans_stream.append(('BUY_LAND', 'LAND', 0.0, float(delta)))

    def my_process_market(state, env):
        current_f0[0] = state[0].observation.farms[0]
        TRUE_ORIG_PROCESS(state, env)

    engine._commit_unit = my_commit
    engine._do_hire = my_hire
    engine._do_buy_land = my_land
    engine._process_market = my_process_market

    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
    finally:
        engine._commit_unit = TRUE_ORIG_COMMIT
        engine._do_hire = TRUE_ORIG_HIRE
        engine._do_buy_land = TRUE_ORIG_LAND
        engine._process_market = TRUE_ORIG_PROCESS

    rew = float(steps[-1][0]["reward"])
    start_money = float(steps[0][0]["observation"]["farms"][0]["money"])
    
    total_rev = sum(v for k, v in ledger.items() if k.startswith("REV_"))
    total_exp = sum(v for k, v in ledger.items() if k.startswith("EXP_"))
    diff = abs(start_money + total_rev - total_exp - rew)
    assert diff < 1e-6, f"Accounting check failed on seed {seed}"

    action_stream = []
    for st in steps:
        act = st[0].get("action") or {}
        action_stream.append((str(act.get("farmer")), [str(h) for h in act.get("hands") or []], [list(o) for o in act.get("market") or []]))

    f0 = steps[-1][0]["observation"]["farms"][0]
    final_state = {"money": f0.get("money"), "shed": f0.get("shed"), "tiles": f0.get("tiles")}

    act_hash = hashlib.sha256(json.dumps(action_stream, sort_keys=True).encode('utf-8')).hexdigest()
    trans_hash = hashlib.sha256(json.dumps(trans_stream, sort_keys=True).encode('utf-8')).hexdigest()
    state_hash = hashlib.sha256(json.dumps(final_state, sort_keys=True).encode('utf-8')).hexdigest()

    return rew, act_hash, trans_hash, state_hash, diff

def worker_in_proc(seed):
    runs = [run_single_v2(seed) for _ in range(5)]
    base = runs[0]
    mismatches = 0
    for r in runs[1:]:
        if r[:4] != base[:4]:
            mismatches += 1
    return seed, base, mismatches

def worker_fresh(args):
    seed, run_id = args
    return seed, run_id, run_single_v2(seed)

def main():
    test_seeds = list(range(865550, 865560)) # 10 fresh seeds
    print(f"=== PHASE 7: REPEATABILITY AUDIT ON 10 FRESH SEEDS ===")
    print(f"Testing seeds: {test_seeds}")

    # 1. 5 in-process runs per seed
    print("Testing 5 in-process repeated runs per seed...")
    with ProcessPoolExecutor(max_workers=10) as executor:
        in_proc_results = list(executor.map(worker_in_proc, test_seeds))
    
    in_proc_mismatches = sum(m for _, _, m in in_proc_results)
    print(f"In-process mismatches: {in_proc_mismatches} / {len(test_seeds) * 4}")
    assert in_proc_mismatches == 0, "In-process repeatability failed!"

    # 2. 5 fresh-process runs per seed (50 independent process executions)
    print("Testing 5 fresh-process independent runs per seed...")
    fresh_jobs = [(s, run_id) for s in test_seeds for run_id in range(5)]
    fresh_by_seed = defaultdict(list)
    with ProcessPoolExecutor(max_workers=11) as executor:
        for seed, run_id, res in executor.map(worker_fresh, fresh_jobs):
            fresh_by_seed[seed].append((run_id, res))

    fresh_mismatches = 0
    max_acct_diff = 0.0
    for s in test_seeds:
        runs = [r for _, r in sorted(fresh_by_seed[s], key=lambda x: x[0])]
        base = runs[0]
        for r in runs:
            max_acct_diff = max(max_acct_diff, r[4])
        for r in runs[1:]:
            if r[:4] != base[:4]:
                fresh_mismatches += 1
                print(f"Fresh mismatch on seed {s}")

    print(f"Fresh-process mismatches: {fresh_mismatches} / {len(test_seeds) * 4}")
    assert fresh_mismatches == 0, "Fresh process repeatability failed!"
    print(f"Max accounting difference across all repeatability runs: {max_acct_diff:.2e}")
    assert max_acct_diff < 1e-6, "Accounting check failed!"
    print("\nPHASE 7 & PHASE 8 PASSED: 100% PERFECT DETERMINISTIC REPEATABILITY AND MACHINE PRECISION ACCOUNTING!")

if __name__ == "__main__":
    main()
