import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def run_capacity_safe_experiment(seed: int, seat: int = 0):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    opp_seat = 1 - seat
    
    for step in range(719):
        if seat == 0:
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = v44_mod.agent(obs[1], sim.configuration)
        else:
            a0 = v44_mod.agent(obs[0], sim.configuration)
            a1 = v49_mod.agent(obs[1], sim.configuration)
            
        act = a0 if seat == 0 else a1
        mkt = act.get("market", [])
        
        # Check shed capacity
        shed = (obs[seat].get("private") or {}).get("shed", {})
        shed_total = sum(v for k, v in shed.items())
        
        shops = list(obs[seat]["town"]["unlocked_shops"])
        has_milk_shop = any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops)
        p_milk = obs[seat]["market"]["prices"]["MILK"]
        
        # Capacity-safe post-reveal holding rule
        if step >= 216 and isinstance(act, dict):
            new_mkt = []
            for o in mkt:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == "MILK":
                    # Only hold if shed has plenty of headroom (< 40 units) AND milk price is low (< 140) AND milk shop exists
                    if has_milk_shop and p_milk < 140 and shed_total < 40 and step < 650:
                        continue # hold milk temporarily
                new_mkt.append(o)
            act["market"] = new_mkt
            
        actions = [act, a1] if seat == 0 else [a0, act]
        obs, rewards, done, info = sim.step(actions)
        if done:
            break
            
    v49_cash = float(obs[seat]["farms"][seat]["money"])
    opp_cash = float(obs[seat]["farms"][opp_seat]["money"])
    return v49_cash - opp_cash

print("Testing Capacity-Safe Milk Holding Rule:")
for s in [250416, 250436, 250439, 250413, 250414]:
    margin_safe = run_capacity_safe_experiment(s, 0)
    print(f"Seed {s}: Margin = ${margin_safe:>9.2f}")
