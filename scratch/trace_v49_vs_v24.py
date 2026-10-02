import sys, os
sys.path.insert(0, os.path.abspath('.'))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
from research.final_synthesis.teammates.v24.main import agent as v24_agent

seed = 250600
sim = FastKagricultureSim(seed=seed)
obs = sim.reset(seed=seed)

divergences = []
first_diff_step = None

for step in range(719):
    a0 = v49_mod.agent(obs[0])
    a1 = v24_agent(obs[1])
    
    # Check if a0 and a1 have different action structures
    # Note that seat 0 and seat 1 coordinates might be symmetric or identical depending on board layout
    # In kaggriculture, both farms have their own coordinate frames (farmer, hands, tiles)
    obs, r, done, info = sim.step([a0, a1])
    
    c0 = float(obs[0]['farms'][0]['money'])
    c1 = float(obs[1]['farms'][1]['money'])
    
    if (step < 100 and step % 10 == 0) or step in (5, 6, 29, 54, 57, 84, 91, 144, 216, 300, 400, 500, 600, 700, 718):
        shed0 = dict(obs[0]['private']['shed'])
        shed1 = dict(obs[1]['private']['shed'])
        print(f"Step {step:3d} (Day {step//24:2d} Hr {step%24:2d}): Cash V49={c0:8.1f} | v24={c1:8.1f} | Diff={c1-c0:+7.1f} | Shed0={shed0} | Shed1={shed1}")

print(f"\nFinal Cash at Step 718: V49={c0:.1f}, v24={c1:.1f}, Diff={c1-c0:+.1f}")
