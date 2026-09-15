import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import main as dmitrii_main

def trace_dmitrii_timeline(seed=50000):
    game = kagsim.Game(seed)
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    
    dmitrii_agent = dmitrii_main.agent
    
    events = []
    
    prev_cash = None
    prev_animals = {}
    prev_hands = 0
    
    step = 0
    while not game.done:
        obs = game.observe(0)
        day = step // 24
        turn = step % 24
        
        # Check plan id
        plan_id = getattr(dmitrii_main, "current_plan", None)
        
        private = obs["private"]
        farm = obs["farms"][0]
        cash = farm["money"]
        shed = private["shed"]
        hands_cnt = len(farm["hands"])
        
        # Count animals in pastures/coops
        pasture_animals = {"COW": 0, "SHEEP": 0}
        coop_geese = 0
        for y in range(10):
            for x in range(10):
                t = farm["tiles"][y][x]
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE":
                        for a in t.get("animals", []):
                            pasture_animals[a] = pasture_animals.get(a, 0) + 1
                    elif t.get("kind") == "COOP":
                        coop_geese += len(t.get("animals", []))
                        
        if step == 0 or step % 24 == 0 or hands_cnt != prev_hands or pasture_animals != prev_animals:
            events.append({
                "step": step,
                "day": day,
                "turn": turn,
                "cash": cash,
                "hands": hands_cnt,
                "pasture_animals": dict(pasture_animals),
                "coop_geese": coop_geese,
                "shed_feed": shed.get("WHEAT", 0),
                "shed_fert": shed.get("FERTILIZER", 0),
                "shed_straw": shed.get("STRAWBERRY", 0),
                "shed_milk": shed.get("MILK", 0),
                "shed_wool": shed.get("WOOL", 0),
                "shed_egg": shed.get("EGG", 0),
            })
            prev_hands = hands_cnt
            prev_animals = dict(pasture_animals)
            
        act = dmitrii_agent(obs)
        game.step(act, idle)
        step += 1
        
    final_obs = game.observe(0)
    print(f"Final cash: ${final_obs['farms'][0]['money']:.2f}")
    
    print("\n--- KEY TIMELINE MILESTONES ---")
    for e in events:
        print(f"Day {e['day']:02d} (Step {e['step']:03d}): Cash ${e['cash']:8.2f} | Hands {e['hands']} | Animals: {e['pasture_animals']}, Geese: {e['coop_geese']} | Shed: Fert={e['shed_fert']}, Straw={e['shed_straw']}, Milk={e['shed_milk']}, Wool={e['shed_wool']}, Egg={e['shed_egg']}")

if __name__ == "__main__":
    trace_dmitrii_timeline()
