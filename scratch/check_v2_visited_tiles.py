import sys
import os
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

env = make("kaggriculture", configuration={"seed": 42, "episodeSteps": 270})
env.run([robust(v2.agent), robust(v2.agent)])

# Track all tiles where WATER or HARVEST is executed in V2
visited_tiles = {}
for s in range(24, 265):
    step_data = env.steps[s]
    farm = step_data[0]["observation"]["farms"][0]
    farmer_pos = tuple(farm["farmer"])
    hand_pos = [tuple(h) for h in farm["hands"]]
    act = step_data[0].get("action", {})
    
    farmer_act = act.get("farmer", ["PASS"])
    if farmer_act and farmer_act[0] in ("WATER", "HARVEST", "PLANT"):
        visited_tiles[farmer_pos] = visited_tiles.get(farmer_pos, []) + [(s, "farmer", farmer_act[0])]
        
    hands_act = act.get("hands", [])
    for idx, ha in enumerate(hands_act):
        if ha and ha[0] in ("WATER", "HARVEST", "PLANT"):
            pos = hand_pos[idx] if idx < len(hand_pos) else None
            if pos:
                visited_tiles[pos] = visited_tiles.get(pos, []) + [(s, f"hand_{idx}", ha[0])]

print(f"Total tiles visited for crop actions between Step 24 and 264: {len(visited_tiles)}")
for pos, actions in sorted(visited_tiles.items()):
    action_types = set(a[2] for a in actions)
    print(f"Tile {pos}: {len(actions)} actions ({', '.join(action_types)}) - Steps {[a[0] for a in actions][:6]}...")
