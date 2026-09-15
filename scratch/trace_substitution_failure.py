import copy
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

def debug_naive_substitution(seed=50000):
    with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
        tapes = json.load(f)
        
    tape0 = copy.deepcopy(tapes[0])
    sub_tape = copy.deepcopy(tapes[0])
    
    for step in range(144, 719):
        act = sub_tape[step]
        for order in act.get("market", []):
            if order and order[0] == "BUY_ANIMAL" and len(order) >= 2 and order[1] == "SHEEP":
                order[1] = "COW"
            elif order and order[0] == "SELL" and len(order) >= 2 and order[1] == "WOOL":
                order[1] = "MILK"
        workers = [act.get("farmer", ["PASS"])] + act.get("hands", [])
        for w in workers:
            if not w: continue
            if w[0] in ("PICKUP", "PLACE") and len(w) >= 2:
                if w[1] == "SHEEP": w[1] = "COW"
                elif w[1] == "WOOL": w[1] = "MILK"
                
    # Run both and compare
    def run_policy(tape, s):
        policy = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        policy.tapes = [tape] + policy.tapes[1:]
        # Force plan 0
        game = kagsim.Game(s)
        idle = {"farmer": ["PASS"], "hands": [], "market": []}
        step = 0
        
        unfed_events = []
        production = {"MILK": 0, "WOOL": 0}
        
        while not game.done:
            obs = game.observe(0)
            farm = obs["farms"][0]
            
            # Check pastures for unfed or yield
            for y in range(10):
                for x in range(10):
                    t = farm["tiles"][y][x]
                    if isinstance(t, dict) and t.get("kind") == "PASTURE":
                        if t.get("consecutive_unfed", 0) > 0 and step % 24 == 0:
                            unfed_events.append((step // 24, (x, y), t.get("animal"), t.get("consecutive_unfed")))
                            
            act = policy.act(obs)
            game.step(act, idle)
            step += 1
            
        final_obs = game.observe(0)
        return final_obs["farms"][0]["money"], unfed_events
        
    cash0, unfed0 = run_policy(tape0, seed)
    cash_sub, unfed_sub = run_policy(sub_tape, seed)
    
    print(f"Seed {seed}:")
    print(f"  Plan 0 Cash:             ${cash0:.2f} (Unfed events: {len(unfed0)})")
    print(f"  Substituted Tape Cash:   ${cash_sub:.2f} (Unfed events: {len(unfed_sub)})")
    print(f"  Delta:                   ${cash_sub - cash0:.2f}")
    if unfed_sub:
        print("  Sample unfed events in substituted tape:")
        for u in unfed_sub[:10]:
            print(f"    Day {u[0]}, tile {u[1]}, animal {u[2]}, consecutive_unfed {u[3]}")

if __name__ == "__main__":
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"]
    for s in dairy_seeds[:3]:
        debug_naive_substitution(s)
