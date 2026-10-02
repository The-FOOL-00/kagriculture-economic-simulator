import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim

sim = FastKagricultureSim(seed=250436)
obs0, obs1 = sim.reset()
for s in range(220):
    if s in [214, 215, 216, 217]:
        print(f"Step {s}: shops = {obs0.town['unlocked_shops']}, milk_inv = {obs0.market['inventory']['MILK']}, milk_price = {obs0.market['prices']['MILK']}")
    [obs0, obs1], _, done, _ = sim.step([{}, {}])
