import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def track_game(seed):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    
    trace = []
    for step in range(350):
        # We are seat 0, V44 is seat 1
        opp_farm = obs[0]["farms"][1]
        v49_farm = obs[0]["farms"][0]
        
        # count animals on opp farm
        opp_cows = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        opp_sheep = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        opp_geese = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "GOOSE")
        opp_pastures = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("kind") == "PASTURE")
        opp_coops = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("kind") == "COOP")
        
        v49_cows = sum(1 for r in v49_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        v49_geese = sum(1 for r in v49_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "GOOSE")
        
        prices = obs[0]["market"]["prices"]
        inv = obs[0]["market"]["inventory"]
        shops = obs[0]["town"]["unlocked_shops"]
        
        if step in [140, 144, 150, 155, 160, 168, 175, 180, 192, 216, 240, 264, 288, 300]:
            trace.append({
                "step": step,
                "opp_money": opp_farm["money"],
                "v49_money": v49_farm["money"],
                "opp_cows": opp_cows,
                "opp_sheep": opp_sheep,
                "opp_geese": opp_geese,
                "opp_pastures": opp_pastures,
                "v49_cows": v49_cows,
                "v49_geese": v49_geese,
                "milk_price": prices["MILK"],
                "milk_inv": inv["MILK"],
                "egg_price": prices["EGG"],
                "egg_inv": inv["EGG"],
                "shops": list(shops)
            })
            
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        obs, rewards, done, info = sim.step([a0, a1])
        if done:
            break
    return trace

t_416 = track_game(250416)
t_436 = track_game(250436)

print(f"{'Step':<5} | {'250416 Opp C/G':<15} {'250416 Mkt Milk':<16} {'250416 Shops':<25} | {'250436 Opp C/G':<15} {'250436 Mkt Milk':<16} {'250436 Shops':<25}")
print("-" * 105)
for r416, r436 in zip(t_416, t_436):
    s = r416['step']
    c_g_416 = f"{r416['opp_cows']}C / {r416['opp_geese']}G"
    m_416 = f"${r416['milk_price']} (I={r416['milk_inv']})"
    sh_416 = str(r416['shops'])
    
    c_g_436 = f"{r436['opp_cows']}C / {r436['opp_geese']}G"
    m_436 = f"${r436['milk_price']} (I={r436['milk_inv']})"
    sh_436 = str(r436['shops'])
    
    print(f"{s:<5} | {c_g_416:<15} {m_416:<16} {sh_416:<25} | {c_g_436:<15} {m_436:<16} {sh_436:<25}")
