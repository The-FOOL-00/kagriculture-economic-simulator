"""
Breakthrough Test:
Run V2 with 12 melons planted on V2's OWN grid on Day 0!
Convert 5 wheat plantings on Day 0 to MELON plantings on V2's exact movement paths!
Verify whether V2 waters them, harvests them on Day 10/11, and what V2 scores!
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import copy
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

def create_v2_12melon_agent():
    trace = copy.deepcopy(v2._TRACE)
    
    # Step 0 market orders:
    # 5 hires, 2 cows, 2 sheep, 12 melons, 7 wheat, 2 feed
    trace[0]["market"] = [
        ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
        ["BUY_ANIMAL", "SHEEP", 2], ["BUY_ANIMAL", "COW", 2],
        ["BUY_SEED", "WHEAT", 7], ["BUY_SEED", "MELON", 12],
        ["BUY_PRODUCT", "WHEAT", 2]
    ]
    
    # Convert hiring on steps 1, 2, 5 to PASS (already hired at step 0)
    trace[1]["market"] = []
    trace[2]["market"] = []
    trace[5]["market"] = []
    
    # At step 23: buy 6 feed JIT so shed has feed for Day 1
    trace[23]["market"] = [["BUY_PRODUCT", "WHEAT", 6]]
    
    # Convert 5 wheat plants on Day 0 to MELON plants:
    # 1. Step 4: Farmer ['PLANT', 'WHEAT'] -> ['PLANT', 'MELON']
    trace[4]["farmer"] = ["PLANT", "MELON"]
    
    # 2. Step 6: Hand 2 ['PLANT', 'WHEAT'] -> ['PLANT', 'MELON']
    trace[6]["hands"][2] = ["PLANT", "MELON"]
    
    # 3. Step 7: Hand 0 ['PLANT', 'WHEAT'] -> ['PLANT', 'MELON']
    trace[7]["hands"][0] = ["PLANT", "MELON"]
    
    # 4. Step 9: Hand 2 ['PLANT', 'WHEAT'] -> ['PLANT', 'MELON']
    trace[9]["hands"][2] = ["PLANT", "MELON"]
    
    # 5. Step 14: Hand 2 ['PLANT', 'WHEAT'] -> ['PLANT', 'MELON']
    trace[14]["hands"][2] = ["PLANT", "MELON"]
    
    # Total melons planted = 7 (original) + 5 (converted) = 12 MELONS!
    # Total wheat planted = 10 (original) - 5 (converted) = 5 WHEAT!
    
    # Animal placements:
    # On Step 2, Hand 1 picks up sheep instead of cow:
    trace[2]["hands"][1] = ["PICKUP", "SHEEP", "1"]
    # On Step 10, Hand 3 places sheep instead of cow:
    trace[10]["hands"][3] = ["PLACE", "SHEEP"]
    
    def agent(obs, config=None):
        step = obs.get("step")
        if step is None:
            step = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        else:
            step = int(step or 0)
            
        if step >= 712:
            return v2._terminal_action(obs)
            
        action = copy.deepcopy(trace[min(step, len(trace) - 1)])
        
        # From Step 24 onwards, apply V2's market layer!
        if step >= 24:
            # Let V2's market layer manage sells/buys
            return v2.agent(obs, config)
        return action

    return agent

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

seed = 42
print(f"Running V2-12Melon grid test on seed {seed}...")
agent_cand = create_v2_12melon_agent()

env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
env.run([robust(agent_cand), robust(v2.agent)])

r_cand = float(env.steps[-1][0]["reward"] or 0)
r_v2 = float(env.steps[-1][1]["reward"] or 0)
margin = r_cand - r_v2

print(f"RESULT on Seed {seed}:")
print(f"Candidate Reward: {r_cand:10.1f}")
print(f"Frozen V2 Reward: {r_v2:10.1f}")
print(f"Margin (Cand - V2): {margin:+10.1f}")
