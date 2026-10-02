import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

losses = [
    {"name": "L1", "seed": 250617, "seat": 0, "opp_seat": 1},
    {"name": "L2", "seed": 250617, "seat": 1, "opp_seat": 0},
    {"name": "L3", "seed": 250621, "seat": 0, "opp_seat": 1},
    {"name": "L4", "seed": 250621, "seat": 1, "opp_seat": 0},
]

near_wins = [
    {"name": "W_616_0", "seed": 250616, "seat": 0, "opp_seat": 1},
    {"name": "W_616_1", "seed": 250616, "seat": 1, "opp_seat": 0},
    {"name": "W_631_0", "seed": 250631, "seat": 0, "opp_seat": 1},
    {"name": "W_631_1", "seed": 250631, "seat": 1, "opp_seat": 0},
]

def make_sorted_market_agent(start_step=648):
    def _agent(obs, cfg=None):
        act = v49_mod.agent(obs, cfg)
        step = int(obs.get("step", 0))
        if step < start_step or not isinstance(act, dict):
            return act
            
        mkt = act.get("market", [])
        if not mkt:
            return act
            
        # Get market prices
        prices = obs.get("market", {}).get("prices", {})
        
        # Separate sell orders from non-sell orders
        sells = []
        others = []
        for o in mkt:
            if o and len(o) >= 3 and o[0] == "SELL":
                item = o[1]
                p = prices.get(item, 0)
                sells.append((p, o))
            else:
                others.append(o)
                
        # Sort sells by descending price
        sells.sort(key=lambda x: -x[0])
        sorted_mkt = [o for p, o in sells] + others
        
        return {
            "farmer": act.get("farmer", ["PASS"]),
            "hands": act.get("hands", []),
            "market": sorted_mkt[:10]
        }
    return _agent

for start_step in (600, 648, 672, 696):
    print(f"\n=======================================================")
    print(f"TESTING DESCENDING PRICE MARKET SORT FROM STEP {start_step}")
    print(f"=======================================================")
    agent_sorted = make_sorted_market_agent(start_step)
    
    # Test on 4 losses
    print("--- 4 Losses ---")
    for l in losses:
        # Base
        sim = FastKagricultureSim(seed=l["seed"])
        obs = sim.reset(seed=l["seed"])
        for _ in range(719):
            a0 = v49_mod.agent(obs[l["seat"]])
            a1 = v44_mod.agent(obs[l["opp_seat"]])
            obs, _, done, _ = sim.step([a0, a1] if l["seat"] == 0 else [a1, a0])
        m_base = float(obs[l["seat"]]["farms"][l["seat"]]["money"]) - float(obs[l["opp_seat"]]["farms"][l["opp_seat"]]["money"])
        
        # Cand
        sim = FastKagricultureSim(seed=l["seed"])
        obs = sim.reset(seed=l["seed"])
        for _ in range(719):
            a0 = agent_sorted(obs[l["seat"]])
            a1 = v44_mod.agent(obs[l["opp_seat"]])
            obs, _, done, _ = sim.step([a0, a1] if l["seat"] == 0 else [a1, a0])
        m_cand = float(obs[l["seat"]]["farms"][l["seat"]]["money"]) - float(obs[l["opp_seat"]]["farms"][l["opp_seat"]]["money"])
        
        print(f"  {l['name']} (Seed {l['seed']} Seat {l['seat']}): Base Margin = ${m_base:>+8.1f} | Cand = ${m_cand:>+8.1f} | Delta = ${m_cand - m_base:>+7.1f} | Win = {m_cand > 0}")

    # Test on Near-Wins (Safety Check)
    print("--- Near Wins Safety Check ---")
    for w in near_wins:
        # Base
        sim = FastKagricultureSim(seed=w["seed"])
        obs = sim.reset(seed=w["seed"])
        for _ in range(719):
            a0 = v49_mod.agent(obs[w["seat"]])
            a1 = v44_mod.agent(obs[w["opp_seat"]])
            obs, _, done, _ = sim.step([a0, a1] if w["seat"] == 0 else [a1, a0])
        m_base = float(obs[w["seat"]]["farms"][w["seat"]]["money"]) - float(obs[w["opp_seat"]]["farms"][w["opp_seat"]]["money"])
        
        # Cand
        sim = FastKagricultureSim(seed=w["seed"])
        obs = sim.reset(seed=w["seed"])
        for _ in range(719):
            a0 = agent_sorted(obs[w["seat"]])
            a1 = v44_mod.agent(obs[w["opp_seat"]])
            obs, _, done, _ = sim.step([a0, a1] if w["seat"] == 0 else [a1, a0])
        m_cand = float(obs[w["seat"]]["farms"][w["seat"]]["money"]) - float(obs[w["opp_seat"]]["farms"][w["opp_seat"]]["money"])
        
        print(f"  {w['name']} (Seed {w['seed']} Seat {w['seat']}): Base Margin = ${m_base:>+8.1f} | Cand = ${m_cand:>+8.1f} | Delta = ${m_cand - m_base:>+7.1f} | Win = {m_cand > 0}")
