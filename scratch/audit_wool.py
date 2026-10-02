import sys; sys.path.insert(0, '.')
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

for seed in [250621, 250617]:
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    print(f"\n{'='*70}\nWOOL & SHED AUDIT SEED {seed}\n{'='*70}")
    for step in range(719):
        s0_wool = sim.state[0].observation.private['shed'].get('WOOL', 0)
        s1_wool = sim.state[1].observation.private['shed'].get('WOOL', 0)
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        m0 = [x for x in a0.get('market', []) if x and x[0] == 'SELL' and x[1] == 'WOOL']
        m1 = [x for x in a1.get('market', []) if x and x[0] == 'SELL' and x[1] == 'WOOL']
        
        obs, _, done, _ = sim.step([a0, a1])
        s0_post = sim.state[0].observation.private['shed'].get('WOOL', 0)
        s1_post = sim.state[1].observation.private['shed'].get('WOOL', 0)
        if step in range(690, 700) or m0 or m1:
            if step in range(690, 700):
                print(f"Step {step:3d} | V49 shed WOOL: {s0_wool} -> {s0_post} (order: {m0}) | V44 shed WOOL: {s1_wool} -> {s1_post} (order: {m1})")
