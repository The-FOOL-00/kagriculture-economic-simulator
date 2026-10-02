import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def make_generic_blocked_repair_agent():
    # Maintain per-worker blocked queue
    worker_queues = {}
    
    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0))
        seat = int(obs.get("player", 0))
        farm = obs["farms"][seat]
        tiles = farm["tiles"]
        
        # Get baseline action
        base_act = v49_mod.agent(obs, cfg)
        if not isinstance(base_act, dict):
            return base_act
            
        farmer_act = list(base_act.get("farmer", ["PASS"]))
        hands_act = [list(h) for h in base_act.get("hands", [])]
        
        # Let's inspect farmer action
        fx, fy = farm["farmer"]
        tile = tiles[fy][fx]
        
        # If farmer has a queued action and is on the right tile, attempt replay
        # Otherwise, check if farmer's current action is blocked by a weed
        if farmer_act[0] in ("PLANT", "WATER", "HARVEST") and isinstance(tile, dict) and tile.get("kind") == "WEED":
            # Action is blocked by weed! Clear blocker first by DIG
            farmer_act = ["DIG"]
            
        for i, h_act in enumerate(hands_act):
            if i < len(farm["hands"]):
                hx, hy = farm["hands"][i]
                h_tile = tiles[hy][hx]
                if h_act and h_act[0] in ("PLANT", "WATER", "HARVEST") and isinstance(h_tile, dict) and h_tile.get("kind") == "WEED":
                    hands_act[i] = ["DIG"]
                    
        return {
            "farmer": farmer_act,
            "hands": hands_act,
            "market": base_act.get("market", [])
        }
    return _agent

print("Testing Generic Blocked Action Repair vs Baseline V49 across 16 matches...")
repair_agent = make_generic_blocked_repair_agent()

deltas = []
for s in [250400 + i for i in range(16)]:
    sim_base = FastKagricultureSim(seed=s)
    sim_test = FastKagricultureSim(seed=s)
    
    obs_b = sim_base.reset()
    obs_t = sim_test.reset()
    
    # Baseline
    for step in range(719):
        a0 = v49_mod.agent(obs_b[0], sim_base.configuration)
        a1 = v44_mod.agent(obs_b[1], sim_base.configuration)
        obs_b, _, done, _ = sim_base.step([a0, a1])
        if done:
            break
            
    # Test
    for step in range(719):
        a0 = repair_agent(obs_t[0], sim_test.configuration)
        a1 = v44_mod.agent(obs_t[1], sim_test.configuration)
        obs_t, _, done, _ = sim_test.step([a0, a1])
        if done:
            break
            
    margin_b = float(obs_b[0]["farms"][0]["money"]) - float(obs_b[0]["farms"][1]["money"])
    margin_t = float(obs_t[0]["farms"][0]["money"]) - float(obs_t[0]["farms"][1]["money"])
    delta = margin_t - margin_b
    deltas.append(delta)
    print(f"Seed {s}: Baseline Margin = ${margin_b:>9.2f} | Repair Margin = ${margin_t:>9.2f} | Delta = ${delta:>+9.2f}")

print(f"\nMean Paired Delta: ${sum(deltas)/len(deltas):>+9.2f}")
