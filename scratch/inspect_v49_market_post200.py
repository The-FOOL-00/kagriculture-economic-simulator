import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

sim = FastKagricultureSim(seed=250436)
obs = sim.reset()

market_orders_by_step = {}

for step in range(719):
    a0 = v49_mod.agent(obs[0], sim.configuration)
    a1 = v44_mod.agent(obs[1], sim.configuration)
    
    mkt = a0.get("market", [])
    if mkt:
        market_orders_by_step[step] = mkt
        
    obs, rewards, done, info = sim.step([a0, a1])
    if done:
        break

print(f"Total steps with market orders by V49: {len(market_orders_by_step)}")
for s, orders in sorted(market_orders_by_step.items()):
    if s >= 200:
        print(f"Step {s:3d}: {orders}")
