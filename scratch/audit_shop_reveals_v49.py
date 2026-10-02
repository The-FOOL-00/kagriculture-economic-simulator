import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod
import kaggle_environments.envs.kaggriculture.kaggriculture as kg

SEEDS = [250416, 250436, 250439]

def audit_seed(seed: int):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    
    events = []
    prev_shops = []
    
    for step in range(719):
        current_shops = list(obs[0]["town"]["unlocked_shops"])
        if len(current_shops) > len(prev_shops):
            new_shop = current_shops[-1]
            day = step // 24
            hour = step % 24
            mkt = obs[0]["market"]
            
            # Shop info
            products = kg.SHOPS.get(new_shop, [])
            freq = 4 # townShopSellInterval
            mult = 2 if len(products) == 1 else 1
            remaining_steps = 719 - step
            consumption_ticks = remaining_steps // freq
            
            # V49 action at this step
            a0 = v49_mod.agent(obs[0], sim.configuration)
            
            events.append({
                "step": step,
                "day": day,
                "hour": hour,
                "new_shop": new_shop,
                "all_shops": list(current_shops),
                "demand_commodities": products,
                "multiplier": mult,
                "consumption_interval": freq,
                "remaining_steps": remaining_steps,
                "remaining_ticks": consumption_ticks,
                "total_demand_per_commodity": mult * consumption_ticks,
                "market_prices": {p: mkt["prices"].get(p) for p in products},
                "market_inventory": {p: mkt["inventory"].get(p) for p in products},
                "v49_action": a0
            })
            prev_shops = list(current_shops)
            
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        obs, rewards, done, info = sim.step([a0, a1])
        if done:
            break
            
    return events

timeline_data = {}
for s in SEEDS:
    evs = audit_seed(s)
    timeline_data[str(s)] = evs
    print(f"\nSeed {s} Unlocks:")
    for e in evs:
        print(f"  Step {e['step']:3d} (Day {e['day']:2d} h{e['hour']:2d}): New Shop = {e['new_shop']:<16} Consumes: {e['demand_commodities']} (Total {e['total_demand_per_commodity']} units each over {e['remaining_ticks']} ticks)")

os.makedirs("research/v55/analysis", exist_ok=True)
with open("research/v55/analysis/SHOP_REVEAL_TIMELINE.json", "w") as f:
    json.dump(timeline_data, f, indent=2)

print("\nSaved research/v55/analysis/SHOP_REVEAL_TIMELINE.json")
