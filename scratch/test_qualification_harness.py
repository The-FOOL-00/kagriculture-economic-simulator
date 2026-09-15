import sys
import os
import json
import hashlib
from collections import defaultdict
import numpy as np
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

def run_pilot():
    print("Testing pilot simulation with full instrumentation...")
    seed = 865000

    ledger = defaultdict(float)
    actions_count = defaultdict(int)
    strawberry_deaths = [0]
    animal_escapes = [0]
    action_stream = []
    transaction_stream = []
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
            transaction_stream.append((op, item, price, delta))
        return res

    def my_hire(farm, private, board_size, mult=engine.FARM_HAND_COST_MULT):
        m_b = farm['money']
        TRUE_ORIG_HIRE(farm, private, board_size, mult)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_HIRE'] += delta
            transaction_stream.append(('HIRE', 'HAND', delta))

    def my_land(farm, board_size):
        m_b = farm['money']
        TRUE_ORIG_LAND(farm, board_size)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_LAND'] += delta
            transaction_stream.append(('BUY_LAND', 'LAND', delta))

    def my_process_market(state, env):
        current_f0[0] = state[0].observation.farms[0]
        TRUE_ORIG_PROCESS(state, env)

    def my_decay(farm, step):
        if farm is current_f0[0]:
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                        mls = t.get("max_lifespan_step", -1)
                        if mls >= 0 and step >= mls and (step - mls) % 2 == 0:
                            if t.get("yield_units", 0) <= 1:
                                strawberry_deaths[0] += 1
        TRUE_ORIG_DECAY(farm, step)

    def my_refresh_animals(farm, day):
        if farm is current_f0[0]:
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict) and "animal" in t:
                        if not t.get("fed_today", False):
                            if t.get("consecutive_unfed", 0) >= 1:
                                animal_escapes[0] += 1
        TRUE_ORIG_REFRESH_ANIMALS(farm, day)

    engine._commit_unit = my_commit
    engine._do_hire = my_hire
    engine._do_buy_land = my_land
    engine._process_market = my_process_market
    engine._decay_plants = my_decay
    engine._daily_refresh_animals = my_refresh_animals

    agent = b1_modular.ResearchBOnlyV1()

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

    def get_action_verb(act):
        if isinstance(act, list) and act:
            return str(act[0])
        elif isinstance(act, str):
            return act.split()[0] if act else "PASS"
        return "PASS"

    for st in steps:
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

    print(f"Seed: {seed}")
    print(f"Reward: {env_rew}")
    print(f"Reconstructed: {reconstructed}, Diff: {diff}")
    print(f"Strawberry deaths: {strawberry_deaths[0]}, Animal escapes: {animal_escapes[0]}")
    print(f"Action counts: {dict(actions_count)}")
    assert diff < 1e-6, "Accounting mismatch!"
    print("Pilot test completed successfully with 100% accounting fidelity!")

if __name__ == "__main__":
    run_pilot()
