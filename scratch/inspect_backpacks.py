import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def inspect_inventories_at_step(seed, target_steps=[700, 704, 707, 711, 715, 718]):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    print(f"\n==========================================")
    print(f"INSPECTING SEED {seed} INVENTORIES")
    print(f"==========================================")
    
    for step in range(719):
        if step in target_steps:
            # Let's inspect internal state from sim.state
            priv0 = sim.state[0].observation.get("private", {}) or {}
            priv1 = sim.state[1].observation.get("private", {}) or {}
            farm0 = obs[0]["farms"][0]
            farm1 = obs[1]["farms"][1]
            
            # Count total items carried by hands and farmer
            def get_carried(farm, priv):
                invs = {}
                f_inv = priv.get("farmer_inventory", {})
                if f_inv: invs["farmer"] = dict(f_inv)
                for i, h_inv in enumerate(priv.get("hands_inventory", [])):
                    if h_inv: invs[f"hand_{i}"] = dict(h_inv)
                return invs
                
            c0 = float(farm0["money"])
            c1 = float(farm1["money"])
            print(f"--- STEP {step} (Margin: ${c0-c1:+.1f}) ---")
            print(f"  V49 (P0): Cash = ${c0:.1f}, Shed = {dict(farm0.get('shed', {}) or {})}")
            print(f"    Carried = {get_carried(farm0, priv0)}")
            print(f"  V44 (P1): Cash = ${c1:.1f}, Shed = {dict(farm1.get('shed', {}) or {})}")
            print(f"    Carried = {get_carried(farm1, priv1)}")
            
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        obs, _, done, _ = sim.step([a0, a1])
        if done: break

inspect_inventories_at_step(250621)
inspect_inventories_at_step(250617)
