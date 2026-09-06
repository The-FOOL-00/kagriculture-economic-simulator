import sys
sys.path.insert(0, ".")
import json
import candidates.slot2_aethel_refined_v2 as v2

# Let's inspect V2's farm layout across the match
import kaggle_environments
env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})
env.run([v2.agent, v2.agent])

farm0 = env.steps[-1][0]["observation"]["farms"][0]
tiles0 = farm0["tiles"]

pastures_v2 = []
for y in range(10):
    for x in range(10):
        t = tiles0[y][x]
        if isinstance(t, dict) and t.get("kind") == "PASTURE":
            pastures_v2.append(((x, y), t.get("animal")))

print("=== V2 FINAL PASTURE POSITIONS ===")
for p, a in sorted(pastures_v2):
    print(f"  Tile {p}: {a}")

# Let's inspect Crop Dusta's replay pasture positions
with open("scratch/replays/Whyme_Labs_104824599.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

# Crop Dusta was Player 1
last_obs_p1 = rep["steps"][-1][1]["observation"]
farm_cd = (last_obs_p1.get("farms") or [{}, {}])[1]
tiles_cd = farm_cd["tiles"]

pastures_cd = []
for y in range(10):
    for x in range(10):
        t = tiles_cd[y][x]
        if isinstance(t, dict) and t.get("kind") == "PASTURE":
            pastures_cd.append(((x, y), t.get("animal")))

print("\n=== CROP DUSTA (104824599) FINAL PASTURE POSITIONS ===")
for p, a in sorted(pastures_cd):
    print(f"  Tile {p}: {a}")
