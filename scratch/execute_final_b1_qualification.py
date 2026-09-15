import sys
import os
import json
import hashlib
from collections import defaultdict
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.qualification_counterfactual_suite import BaseQ50Agent
import candidates.research_b_only_v1 as b1_modular
import candidates.compiled_research_b_only_v1 as b1_compiled
import candidates.candidate_cl_labor_minimal_v1 as candidate_module
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

TRUE_ORIG_COMMIT = engine._commit_unit
TRUE_ORIG_HIRE = engine._do_hire
TRUE_ORIG_LAND = engine._do_buy_land
TRUE_ORIG_PROCESS = engine._process_market
TRUE_ORIG_DECAY = engine._decay_plants
TRUE_ORIG_REFRESH_ANIMALS = engine._daily_refresh_animals

def get_action_verb(act):
    if isinstance(act, list) and act:
        return str(act[0])
    elif isinstance(act, str):
        return act.split()[0] if act else "PASS"
    return "PASS"

def run_simulation_job(args):
    pol_name, seed = args

    if pol_name == "Raw_Q50":
        agent = BaseQ50Agent(50)
    elif pol_name == "B_ONLY":
        agent = b1_modular.ResearchBOnlyV1()
    elif pol_name == "Compiled_B_ONLY":
        agent = b1_compiled.ResearchBOnlyV1()
    elif pol_name == "Frozen_Candidate":
        agent = candidate_module.ClosedLoopLaborMinimalV1(50)
    else:
        raise ValueError(f"Unknown policy {pol_name}")

    ledger = defaultdict(float)
    actions_count = defaultdict(int)
    strawberry_deaths = 0
    animal_escapes = 0
    action_stream = []
    transaction_stream = []
    current_f0 = [None]
    
    # Workload counters
    mature_strawberry_workload = 0
    weed_workload = 0

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
            transaction_stream.append((op, item, float(price), float(delta)))
        return res

    def my_hire(farm, private, board_size, mult=engine.FARM_HAND_COST_MULT):
        m_b = farm['money']
        TRUE_ORIG_HIRE(farm, private, board_size, mult)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_HIRE'] += delta
            transaction_stream.append(('HIRE', 'HAND', 0.0, float(delta)))

    def my_land(farm, board_size):
        m_b = farm['money']
        TRUE_ORIG_LAND(farm, board_size)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_LAND'] += delta
            transaction_stream.append(('BUY_LAND', 'LAND', 0.0, float(delta)))

    def my_process_market(state, env):
        current_f0[0] = state[0].observation.farms[0]
        TRUE_ORIG_PROCESS(state, env)

    non_local_deaths = [0]
    def my_decay(farm, step):
        if farm is current_f0[0]:
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                        mls = t.get("max_lifespan_step", -1)
                        if mls >= 0 and step >= mls and (step - mls) % 2 == 0:
                            if t.get("yield_units", 0) <= 1:
                                non_local_deaths[0] += 1
        TRUE_ORIG_DECAY(farm, step)

    non_local_escapes = [0]
    def my_refresh_animals(farm, day):
        if farm is current_f0[0]:
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict) and "animal" in t:
                        if not t.get("fed_today", False):
                            if t.get("consecutive_unfed", 0) >= 1:
                                non_local_escapes[0] += 1
        TRUE_ORIG_REFRESH_ANIMALS(farm, day)

    engine._commit_unit = my_commit
    engine._do_hire = my_hire
    engine._do_buy_land = my_land
    engine._process_market = my_process_market
    engine._decay_plants = my_decay
    engine._daily_refresh_animals = my_refresh_animals

    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
    finally:
        engine._commit_unit = TRUE_ORIG_COMMIT
        engine._do_hire = TRUE_ORIG_HIRE
        engine._do_buy_land = TRUE_ORIG_LAND
        engine._process_market = TRUE_ORIG_PROCESS
        engine._decay_plants = TRUE_ORIG_DECAY
        engine._daily_refresh_animals = TRUE_ORIG_REFRESH_ANIMALS

    strawberry_deaths = non_local_deaths[0]
    animal_escapes = non_local_escapes[0]

    # Process step actions and workload
    for st in steps:
        obs = st[0].get("observation") or {}
        farms = obs.get("farms") or []
        if farms:
            f0 = farms[0]
            tiles = f0.get("tiles") or []
            for r in tiles:
                for t in r:
                    if isinstance(t, dict):
                        if t.get("kind") == "WEED":
                            weed_workload += 1
                        elif t.get("crop") == "STRAWBERRY":
                            stage = t.get("stage", 0)
                            if stage >= 2 or t.get("yield_units", 0) > 0:
                                mature_strawberry_workload += 1

        act = st[0].get("action") or {}
        f_act = act.get("farmer") or "PASS"
        action_stream.append(str(f_act))
        actions_count[get_action_verb(f_act)] += 1
        for h_act in act.get("hands") or []:
            action_stream.append(str(h_act))
            actions_count[get_action_verb(h_act)] += 1

    env_rew = float(steps[-1][0]["reward"])
    start_money = float(steps[0][0]["observation"]["farms"][0]["money"])
    total_rev = sum(v for k, v in ledger.items() if k.startswith("REV_"))
    total_exp = sum(v for k, v in ledger.items() if k.startswith("EXP_"))
    reconstructed = start_money + total_rev - total_exp
    diff = abs(reconstructed - env_rew)
    assert diff < 1e-6, f"Accounting mismatch on seed {seed}: recon={reconstructed}, env={env_rew}, diff={diff}"

    # Hashes for behavioral equivalence
    action_hash = hashlib.sha256(json.dumps(action_stream).encode('utf-8')).hexdigest()
    trans_hash = hashlib.sha256(json.dumps(transaction_stream).encode('utf-8')).hexdigest()
    
    # Terminal farm state
    final_farm = steps[-1][0]["observation"]["farms"][0]
    state_str = json.dumps({
        "money": final_farm.get("money"),
        "shed": final_farm.get("shed"),
        "tiles": final_farm.get("tiles")
    }, sort_keys=True)
    state_hash = hashlib.sha256(state_str.encode('utf-8')).hexdigest()

    # Total movement
    move_count = actions_count['NORTH'] + actions_count['SOUTH'] + actions_count['EAST'] + actions_count['WEST']
    productive_workload = (
        actions_count['WATER'] + actions_count['HARVEST'] + actions_count['FEED'] + 
        actions_count['CARE'] + actions_count['FERTILIZE'] + actions_count['PLANT']
    )

    return {
        "policy": pol_name,
        "seed": seed,
        "reward": env_rew,
        "diff": diff,
        "ledger": dict(ledger),
        "actions_count": dict(actions_count),
        "move_count": move_count,
        "productive_workload": productive_workload,
        "mature_strawberry_workload": mature_strawberry_workload,
        "weed_workload": weed_workload,
        "strawberry_deaths": strawberry_deaths,
        "animal_escapes": animal_escapes,
        "action_hash": action_hash,
        "trans_hash": trans_hash,
        "state_hash": state_hash,
        "final_money": final_farm.get("money")
    }

def main():
    holdout_seeds = list(range(865000, 865500)) # N=500 untouched seeds
    print(f"Starting Final Holdout Evaluation on N={len(holdout_seeds)} seeds ({holdout_seeds[0]}..{holdout_seeds[-1]})...")

    # We evaluate Raw_Q50, B_ONLY, and Frozen_Candidate on all 500 seeds
    # And Compiled_B_ONLY on the first 50 seeds for behavioral hashing
    jobs = []
    for s in holdout_seeds:
        jobs.append(("Raw_Q50", s))
        jobs.append(("B_ONLY", s))
        jobs.append(("Frozen_Candidate", s))
    for s in holdout_seeds[:50]:
        jobs.append(("Compiled_B_ONLY", s))

    print(f"Total simulations to run: {len(jobs)}...")
    results = defaultdict(dict)
    
    with ProcessPoolExecutor(max_workers=11) as executor:
        for i, res in enumerate(executor.map(run_simulation_job, jobs, chunksize=10)):
            results[res["policy"]][res["seed"]] = res
            if (i + 1) % 100 == 0:
                print(f"Completed {i + 1} / {len(jobs)} simulations...")

    out_file = "scratch/final_b1_qualification_500seeds.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"All simulations complete! Results saved to {out_file}")

if __name__ == "__main__":
    main()
