import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

sim = FastKagricultureSim(seed=250621)
obs = sim.reset(seed=250621)

for step in range(719):
    c0 = float(obs[0]['farms'][0]['money'])
    c1 = float(obs[1]['farms'][1]['money'])
    a0 = v49_mod.agent(obs[0])
    a1 = v44_mod.agent(obs[1])
    
    if 696 <= step <= 702:
        print(f"=== STEP {step} ===")
        print(f"  Pre-step Cash: V49=${c0:.1f}, V44=${c1:.1f}, Margin=${c0-c1:+.1f}")
        print(f"  V49 Market Action: {a0.get('market', [])}")
        print(f"  V44 Market Action: {a1.get('market', [])}")
        f0 = a0.get('farmer')
        f1 = a1.get('farmer')
        h0 = [f"H{i}:{h}" for i, h in enumerate(a0.get('hands', [])) if h and h[0] != 'PASS']
        h1 = [f"H{i}:{h}" for i, h in enumerate(a1.get('hands', [])) if h and h[0] != 'PASS']
        print(f"  V49 Units: Farmer {f0} | {h0}")
        print(f"  V44 Units: Farmer {f1} | {h1}")
        
    obs, _, done, _ = sim.step([a0, a1])
