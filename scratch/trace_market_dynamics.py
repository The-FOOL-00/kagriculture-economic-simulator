import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import main as dmitrii_main
import compiled_v54_plus_residual as v54

def trace_market_dynamics(seed=50027):
    game = kagsim.Game(seed)
    
    dmitrii_agent = dmitrii_main.agent
    v54_agent = v54.agent
    
    step = 0
    records = []
    
    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        
        m_inv = obs0["market"]["inventory"]
        m_pri = obs0["market"]["prices"]
        shed0 = obs0["private"]["shed"]
        
        act0 = dmitrii_agent(obs0)
        act1 = v54_agent(obs1)
        
        # Check if dmitrii or v54 sells MILK or WOOL
        d_sells = [o for o in act0.get("market", []) if len(o) >= 3 and o[0] == "SELL" and o[1] in ("MILK", "WOOL", "STRAWBERRY")]
        v_sells = [o for o in act1.get("market", []) if len(o) >= 3 and o[0] == "SELL" and o[1] in ("MILK", "WOOL", "STRAWBERRY")]
        
        if d_sells or v_sells or step % 72 == 0:
            records.append({
                "step": step,
                "day": step // 24,
                "turn": step % 24,
                "milk_inv": m_inv["MILK"],
                "milk_pri": m_pri["MILK"],
                "wool_inv": m_inv["WOOL"],
                "wool_pri": m_pri["WOOL"],
                "straw_inv": m_inv["STRAWBERRY"],
                "straw_pri": m_pri["STRAWBERRY"],
                "d_sells": d_sells,
                "v_sells": v_sells,
            })
            
        game.step(act0, act1)
        step += 1
        
    print(f"=== MARKET TRACE FOR SEED {seed} (Competitive) ===")
    for r in records[:35]:
        print(f"Step {r['step']:03d} (D{r['day']:02d}:T{r['turn']:02d}): Milk Inv={r['milk_inv']}, Pri=${r['milk_pri']:3d} | Wool Inv={r['wool_inv']}, Pri=${r['wool_pri']:3d} | D_Sell={r['d_sells']} | V_Sell={r['v_sells']}")

if __name__ == "__main__":
    trace_market_dynamics(50027)
