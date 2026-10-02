import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def inspect_actions_window(seed, seat, opp_seat, start_step=690, end_step=718):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    print(f"\n=======================================================")
    print(f"DISSECTING SEED {seed} STEPS {start_step}..{end_step}")
    print(f"=======================================================")
    
    for step in range(719):
        f49 = obs[seat]["farms"][seat]
        f44 = obs[opp_seat]["farms"][opp_seat]
        c49 = float(f49["money"])
        c44 = float(f44["money"])
        
        a49 = v49_mod.agent(obs[seat])
        a44 = v44_mod.agent(obs[opp_seat])
        
        if start_step <= step <= end_step:
            m49 = a49.get("market", [])
            m44 = a44.get("market", [])
            f49_act = a49.get("farmer", ["PASS"])
            f44_act = a44.get("farmer", ["PASS"])
            h49_acts = a49.get("hands", [])
            h44_acts = a44.get("hands", [])
            
            # Print if market action or non-pass worker action
            print(f"Step {step:3d} | Cash 49: ${c49:>8.1f} | 44: ${c44:>8.1f} | Marg: ${c49-c44:>+7.1f}")
            if m49 or m44:
                print(f"    Mkt 49: {m49}")
                print(f"    Mkt 44: {m44}")
            # Check harvests
            h49_harv = [f"H{i}:{h}" for i, h in enumerate(h49_acts) if h and h[0] in ("HARVEST", "DROP", "PICKUP")]
            h44_harv = [f"H{i}:{h}" for i, h in enumerate(h44_acts) if h and h[0] in ("HARVEST", "DROP", "PICKUP")]
            if h49_harv or h44_harv or f49_act[0] in ("HARVEST", "DROP", "PICKUP") or f44_act[0] in ("HARVEST", "DROP", "PICKUP"):
                print(f"    Units 49: Farmer {f49_act} | {h49_harv}")
                print(f"    Units 44: Farmer {f44_act} | {h44_harv}")
                
        obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
        if done: break

inspect_actions_window(250621, 0, 1, 695, 715)
inspect_actions_window(250617, 0, 1, 700, 715)
