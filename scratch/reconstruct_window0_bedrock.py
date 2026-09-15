import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

def reconstruct_window0(seed=50007):
    policy = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    game = kagsim.Game(seed)
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    
    # Run to step 144 (exact start of Day 6)
    for step in range(144):
        obs = game.observe(0)
        act = policy.act(obs)
        game.step(act, idle)
        
    obs144 = game.observe(0)
    farm = obs144["farms"][0]
    private = obs144["private"]
    town = obs144["town"]
    market = obs144["market"]
    
    # Analyze tiles
    tiles = farm["tiles"]
    plants = []
    pastures = []
    coops = []
    weeds = []
    empty = []
    locked = []
    
    for y in range(10):
        for x in range(10):
            t = tiles[y][x]
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            pos = (x, y)
            if kind == "PLANT":
                plants.append({
                    "pos": pos,
                    "crop": t.get("crop"),
                    "planted_day": t.get("planted_day"),
                    "yield_units": t.get("yield_units"),
                    "consecutive_unwatered": t.get("consecutive_unwatered"),
                    "fertilized_until_day": t.get("fertilized_until_day")
                })
            elif kind == "PASTURE":
                pastures.append({
                    "pos": pos,
                    "animal": t.get("animal"),
                    "placed_day": t.get("placed_day"),
                    "yield_units": t.get("yield_units"),
                    "consecutive_unfed": t.get("consecutive_unfed"),
                    "fed_today": t.get("fed_today"),
                    "cared_today": t.get("cared_today"),
                    "fertilizer_available": t.get("fertilizer_available"),
                    "pending_care_bonus": t.get("pending_care_bonus")
                })
            elif kind == "COOP":
                coops.append({"pos": pos, "animal": t.get("animal")})
            elif kind == "WEED":
                weeds.append(pos)
            elif kind == "EMPTY":
                empty.append(pos)
            elif kind == "LOCKED":
                locked.append(pos)
                
    result = {
        "step": 144,
        "day": 6,
        "turn": 0,
        "money": farm["money"],
        "farmer_pos": farm["farmer"],
        "hands_pos": farm["hands"],
        "unlocked_quadrants": farm["unlocked_quadrants"],
        "shed": private["shed"],
        "seeds": private["seeds"],
        "inventories": private["inventories"],
        "unlocked_shops": town["unlocked_shops"],
        "market_prices": market["prices"],
        "market_inventory": market["inventory"],
        "plants_count": len(plants),
        "plants": plants,
        "pastures_count": len(pastures),
        "pastures": pastures,
        "coops_count": len(coops),
        "coops": coops,
        "empty_count": len(empty),
        "weeds_count": len(weeds),
        "locked_count": len(locked)
    }
    
    print("=" * 70)
    print("DMITRII WINDOW-0 STATE RECONSTRUCTION AT STEP 144 (DAY 6, TURN 0)")
    print("=" * 70)
    print(f"Money:               ${result['money']:.2f}")
    print(f"Farmer Pos:          {result['farmer_pos']}")
    print(f"Hands Count:         {len(result['hands_pos'])}")
    print(f"Unlocked Quadrants:  {result['unlocked_quadrants']}")
    print(f"Shed Inventory:      {result['shed']}")
    print(f"Seeds Inventory:     {result['seeds']}")
    print(f"Unlocked Shops:      {result['unlocked_shops']}")
    print(f"\nTile Breakdown (Total 100 tiles):")
    print(f"  Plants:            {result['plants_count']} ({sum(1 for p in plants if p['crop']=='STRAWBERRY')} Strawberry, {sum(1 for p in plants if p['crop']=='WHEAT')} Wheat)")
    print(f"  Pastures:          {result['pastures_count']} ({sum(1 for p in pastures if p['animal']=='COW')} Cow, {sum(1 for p in pastures if p['animal']=='SHEEP')} Sheep)")
    print(f"  Coops:             {result['coops_count']}")
    print(f"  Weeds:             {result['weeds_count']}")
    print(f"  Empty:             {result['empty_count']}")
    print(f"  Locked:            {result['locked_count']}")
    
    print("\nPasture Animals Detail:")
    for p in pastures:
        print(f"  Pos {p['pos']}: {p['animal']} (Placed Day {p['placed_day']}, Yield {p['yield_units']}, FertAvail {p['fertilizer_available']})")
        
    out_path = "scratch/window0_bedrock_state.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved complete bedrock state to {out_path}")
    return result

if __name__ == "__main__":
    reconstruct_window0()
