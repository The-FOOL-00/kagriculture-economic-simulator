import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

sim = FastKagricultureSim(seed=250621)
obs = sim.reset(seed=250621)

diffs = []
for step in range(698):
    p0 = sim.state[0].observation.private
    p1 = sim.state[1].observation.private
    s0 = dict(p0['shed'])
    s1 = dict(p1['shed'])
    if s0 != s1:
        diffs.append((step, {k: (s0.get(k, 0), s1.get(k, 0)) for k in set(s0)|set(s1) if s0.get(k, 0) != s1.get(k, 0)}))
    a0 = v49_mod.agent(obs[0])
    a1 = v44_mod.agent(obs[1])
    obs, _, done, _ = sim.step([a0, a1])

print(f"Total steps with shed differences: {len(diffs)}")
for d in diffs[:10]:
    print(f"Step {d[0]}: {d[1]}")
if len(diffs) > 10:
    print("...")
    for d in diffs[-5:]:
        print(f"Step {d[0]}: {d[1]}")
