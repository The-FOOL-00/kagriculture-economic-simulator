import sys
sys.path.insert(0, ".")
import json
import copy
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

# Load Crop Dusta trace from replay with CORRECT indexing:
with open("scratch/replays/Whyme_Labs_104824599.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

# Correct indexing: step t action was submitted in response to step t observation, stored in steps[t+1]
cd_trace_aligned = [s[1].get("action", {}) for s in rep["steps"][1:]]
if len(cd_trace_aligned) < 720:
    cd_trace_aligned.extend([{"farmer": ["PASS"], "hands": [], "market": []}] * (720 - len(cd_trace_aligned)))

print(f"Aligned trace length: {len(cd_trace_aligned)}")
print(f"Turn 0 action: {cd_trace_aligned[0]}")
print(f"Turn 1 action: {cd_trace_aligned[1]}")
print(f"Turn 122 action: {cd_trace_aligned[122]}")

def aligned_cd_agent(obs, cfg=None):
    step = min(int(obs.get("step", 0) or 0), 719)
    return copy.deepcopy(cd_trace_aligned[step])

seeds = [215620170, 101, 102, 103, 104]

print("\n" + "="*80)
print("TESTING ALIGNED CROP DUSTA REPLAY ACROSS SEEDS")
print("="*80)

for s in seeds:
    env = kaggle_environments.make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
    env.run([aligned_cd_agent, v2.agent])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    
    # Check pastures and quads
    obs0 = env.steps[-1][0]["observation"]
    farm0 = obs0["farms"][0]
    tiles0 = farm0["tiles"]
    past0 = sum(1 for row in tiles0 for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
    cows0 = sum(1 for row in tiles0 for t in row if isinstance(t, dict) and t.get("animal") == "COW")
    sheep0 = sum(1 for row in tiles0 for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
    quads0 = farm0.get("unlocked_quadrants", [])
    
    print(f"Seed {s:10d} | ALIGNED CD: ${r0:10,.1f} | V2: ${r1:10,.1f} | Pastures: {past0:2d}/16 | Cows: {cows0:2d} | Sheep: {sheep0:2d} | Quads: {quads0}")
