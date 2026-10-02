import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

sim = FastKagricultureSim(seed=250436)
obs = sim.reset()

v49_milk_sold = 0
v49_milk_revenue = 0
opp_milk_sold = 0
opp_milk_revenue = 0

milk_trace = []

for step in range(719):
    p_milk = obs[0]["market"]["prices"]["MILK"]
    i_milk = obs[0]["market"]["inventory"]["MILK"]
    
    a0 = v49_mod.agent(obs[0], sim.configuration)
    a1 = v44_mod.agent(obs[1], sim.configuration)
    
    # Check if either agent sold milk
    m0 = a0.get("market", [])
    m1 = a1.get("market", [])
    
    sold0 = sum(o[2] for o in m0 if len(o) >= 3 and o[0] == "SELL" and o[1] == "MILK")
    sold1 = sum(o[2] for o in m1 if len(o) >= 3 and o[0] == "SELL" and o[1] == "MILK")
    
    if sold0 > 0 or sold1 > 0 or step in [216, 288, 360, 432, 504, 576, 693, 704, 716]:
        shed0 = (obs[0].get("private") or {}).get("shed", {}).get("MILK", 0)
        shed1 = (obs[1].get("private") or {}).get("shed", {}).get("MILK", 0)
        milk_trace.append({
            "step": step,
            "milk_price": p_milk,
            "milk_inv": i_milk,
            "v49_sold": sold0,
            "v49_shed": shed0,
            "opp_sold": sold1,
            "opp_shed": shed1
        })
        
    obs, rewards, done, info = sim.step([a0, a1])
    if done:
        break

print(f"{'Step':<5} {'Price':<6} {'MktInv':<7} | {'V49 Sold':<9} {'V49 Shed':<9} | {'Opp Sold':<9} {'Opp Shed':<9}")
print("-" * 65)
for t in milk_trace:
    print(f"{t['step']:<5} ${t['milk_price']:<5} {t['milk_inv']:<7} | {t['v49_sold']:<9} {t['v49_shed']:<9} | {t['opp_sold']:<9} {t['opp_shed']:<9}")
