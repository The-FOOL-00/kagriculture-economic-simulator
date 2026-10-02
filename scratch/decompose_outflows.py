import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

for s in (250621, 250617):
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset(seed=s)
    
    outflow_categories0 = defaultdict(float)
    outflow_categories1 = defaultdict(float)
    c0_prev = 3000.0
    c1_prev = 3000.0
    
    for step in range(719):
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        
        # Track what actions cost money:
        # Market operations:
        # HIRE, BUY_LAND, BUY_ANIMAL, BUY_SEED, BUY_PRODUCT
        obs, _, done, _ = sim.step([a0, a1])
        c0 = float(obs[0]['farms'][0]['money'])
        c1 = float(obs[1]['farms'][1]['money'])
        
        d0 = c0 - c0_prev
        d1 = c1 - c1_prev
        
        # Record specific transactions at each step
        if a0 and isinstance(a0, dict):
            for m in a0.get('market', []):
                if m and len(m) > 0:
                    op = m[0]
                    if op in ("HIRE", "BUY_LAND", "BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
                        # We can track where money went
                        pass
        c0_prev = c0
        c1_prev = c1
        
    print(f"\n=======================================================")
    print(f"EXACT OUTFLOW COMPARISON FOR SEED {s}")
    print(f"=======================================================")

    # Let's re-run with exact per-step delta tracking
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset(seed=s)
    c0_prev = 3000.0
    c1_prev = 3000.0
    
    step_diffs = []
    for step in range(719):
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        obs, _, done, _ = sim.step([a0, a1])
        c0 = float(obs[0]['farms'][0]['money'])
        c1 = float(obs[1]['farms'][1]['money'])
        
        d0 = c0 - c0_prev
        d1 = c1 - c1_prev
        
        # Net change difference at this turn
        net_diff = d0 - d1 # if negative, V49 lost ground to V44 this turn
        if abs(net_diff) > 0.01:
            step_diffs.append((step, d0, d1, net_diff, c0, c1, c0 - c1))
            
        c0_prev = c0
        c1_prev = c1
        
    print(f"Steps where V49 and V44 cash delta differed (total {len(step_diffs)} steps):")
    # Sort by absolute net_diff
    top_diffs = sorted(step_diffs, key=lambda x: abs(x[3]), reverse=True)
    for t in top_diffs[:15]:
        print(f"  Step {t[0]:3d}: d(V49)=${t[1]:>+9.1f} | d(V44)=${t[2]:>+9.1f} | NetDiff=${t[3]:>+8.1f} | Marg=${t[6]:>+7.1f}")
