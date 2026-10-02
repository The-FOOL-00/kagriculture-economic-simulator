import sys, os
sys.path.insert(0, os.path.abspath('.'))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
from research.final_synthesis.teammates.v24.main import agent as v24_agent
from research.final_synthesis.teammates.v27.main import agent as v27_agent

for opp_name, opp_agent in [('v24', v24_agent), ('v27', v27_agent)]:
    for seed in [250600, 250601]:
        for seat in [0, 1]:
            sim = FastKagricultureSim(seed=seed)
            obs = sim.reset(seed=seed)
            for step in range(719):
                a_cand = v49_mod.agent(obs[seat])
                a_opp = opp_agent(obs[1-seat])
                obs, r, done, info = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])
            cash49 = float(obs[seat]['farms'][seat]['money'])
            cash_opp = float(obs[1-seat]['farms'][1-seat]['money'])
            res = "V49 WIN" if cash49 > cash_opp else ("TIE" if cash49 == cash_opp else "V49 LOSS")
            print(f"Seed {seed} Seat {seat} vs {opp_name}: V49={cash49:.1f} {opp_name}={cash_opp:.1f} Diff={cash49 - cash_opp:+.1f} -> {res}")
