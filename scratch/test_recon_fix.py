import sys
import os
from collections import defaultdict
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from scratch.run_pasture_causal_ablations_50seeds import MechanismAAgent
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

TRUE_ORIG_COMMIT = engine._commit_unit
TRUE_ORIG_HIRE = engine._do_hire
TRUE_ORIG_LAND = engine._do_buy_land
TRUE_ORIG_PROCESS = engine._process_market

def run_agent_exact(agent, seed=1250):
    ledger = defaultdict(float)
    current_f0 = [None]

    def my_commit(op, item, price, farm, private, market, shed_capacity=100):
        m_b = farm['money']
        res = TRUE_ORIG_COMMIT(op, item, price, farm, private, market, shed_capacity)
        if res and farm is current_f0[0]:
            delta = farm['money'] - m_b
            if op == 'SELL':
                ledger['REV_' + item] += delta
            elif op == 'BUY_PRODUCT':
                ledger['EXP_FEED_' + item] += abs(delta)
            elif op == 'BUY_SEED':
                ledger['EXP_SEED_' + item] += abs(delta)
            elif op == 'BUY_ANIMAL':
                ledger['EXP_ANIMAL_' + item] += abs(delta)
        return res

    def my_hire(farm, private, board_size, mult=engine.FARM_HAND_COST_MULT):
        m_b = farm['money']
        TRUE_ORIG_HIRE(farm, private, board_size, mult)
        if farm is current_f0[0]:
            ledger['EXP_HIRE'] += (m_b - farm['money'])

    def my_land(farm, board_size):
        m_b = farm['money']
        TRUE_ORIG_LAND(farm, board_size)
        if farm is current_f0[0]:
            ledger['EXP_LAND'] += (m_b - farm['money'])

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

    env_rew = float(steps[-1][0]["reward"])
    start_money = float(steps[0][0]["observation"]["farms"][0]["money"])

    total_rev = sum(v for k, v in ledger.items() if k.startswith("REV_"))
    total_exp = sum(v for k, v in ledger.items() if k.startswith("EXP_"))
    reconstructed = start_money + total_rev - total_exp
    diff = abs(reconstructed - env_rew)

    return {
        "env_reward": env_rew,
        "reconstructed": reconstructed,
        "diff": diff,
        "ledger": dict(ledger)
    }

if __name__ == "__main__":
    for name, ag in [("M1", m1_module.ClosedLoopEconomicV1()),
                     ("Q50", ParameterizedQuotaAgent(50)),
                     ("MechA", MechanismAAgent(50))]:
        res = run_agent_exact(ag, 1250)
        print(f"{name}: Env={res['env_reward']}, Recon={res['reconstructed']}, Diff={res['diff']}")
        revs = {k: round(v, 2) for k, v in res['ledger'].items() if k.startswith('REV_')}
        exps = {k: round(v, 2) for k, v in res['ledger'].items() if k.startswith('EXP_')}
        print(f"  Revs: {revs}")
        print(f"  Exps: {exps}")
