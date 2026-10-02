import sys; sys.path.insert(0, '.')
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

for seed in [250621, 250617]:
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    print(f"\n{'='*70}\nTRAJECTORY FOR SEED {seed}\n{'='*70}")
    for step in range(719):
        c0 = float(obs[0]['farms'][0]['money'])
        c1 = float(obs[1]['farms'][1]['money'])
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        m0 = a0.get('market', [])
        m1 = a1.get('market', [])
        
        obs, _, done, _ = sim.step([a0, a1])
        c0_next = float(obs[0]['farms'][0]['money'])
        c1_next = float(obs[1]['farms'][1]['money'])
        marg_prev = c0 - c1
        marg_next = c0_next - c1_next
        if step >= 690 and (marg_prev != marg_next or m0 or m1 or step in (717, 718)):
            print(f"Step {step:3d} | Marg: {marg_prev:>+7.1f} -> {marg_next:>+7.1f} (delta {marg_next-marg_prev:>+7.1f}) | 49 cash: {c0_next:.1f} | 44 cash: {c1_next:.1f}")
            if m0: print(f"   V49 mkt: {m0}")
            if m1: print(f"   V44 mkt: {m1}")
