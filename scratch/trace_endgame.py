import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def inspect_milk_timeline(seed, seat, opp_seat):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    events = []
    
    for step in range(719):
        f49 = obs[seat]["farms"][seat]
        f44 = obs[opp_seat]["farms"][opp_seat]
        
        c49 = float(f49["money"])
        c44 = float(f44["money"])
        
        # Check if milk was sold this turn
        a49 = v49_mod.agent(obs[seat])
        a44 = v44_mod.agent(obs[opp_seat])
        
        s49_milk = sum(int(m[2]) for m in a49.get("market", []) if m and m[0] == "SELL" and m[1] == "MILK")
        s44_milk = sum(int(m[2]) for m in a44.get("market", []) if m and m[0] == "SELL" and m[1] == "MILK")
        
        if s49_milk > 0 or s44_milk > 0 or step >= 700:
            events.append({
                "step": step,
                "cash49": c49,
                "cash44": c44,
                "margin": c49 - c44,
                "s49_milk": s49_milk,
                "s44_milk": s44_milk,
                "shed49_milk": f49.get("shed", {}).get("MILK", 0),
                "shed44_milk": f44.get("shed", {}).get("MILK", 0),
            })
            
        obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
        if done: break
        
    return events

print("=== SEED 250621 (LOSS MARGIN -$82) LATE GAME TRACE ===")
events_621 = inspect_milk_timeline(250621, 0, 1)
for e in events_621[-25:]:
    print(f"Step {e['step']:3d} | V49: ${e['cash49']:>9.2f} | V44: ${e['cash44']:>9.2f} | Margin: ${e['margin']:>+8.2f} | SoldMilk(49/44): {e['s49_milk']:>2}/{e['s44_milk']:>2} | ShedMilk(49/44): {e['shed49_milk']:>2}/{e['shed44_milk']:>2}")

print("\n=== SEED 250617 (LOSS MARGIN -$862) LATE GAME TRACE ===")
events_617 = inspect_milk_timeline(250617, 0, 1)
for e in events_617[-25:]:
    print(f"Step {e['step']:3d} | V49: ${e['cash49']:>9.2f} | V44: ${e['cash44']:>9.2f} | Margin: ${e['margin']:>+8.2f} | SoldMilk(49/44): {e['s49_milk']:>2}/{e['s44_milk']:>2} | ShedMilk(49/44): {e['shed49_milk']:>2}/{e['shed44_milk']:>2}")
