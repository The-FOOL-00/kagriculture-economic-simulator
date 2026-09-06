import json
import os
import sys

replay_path = "scratch/replays/Whyme_Labs_104824599.json"
if not os.path.exists(replay_path):
    print(f"Error: {replay_path} not found!")
    sys.exit(1)

with open(replay_path, "r", encoding="utf-8") as f:
    rep = json.load(f)

print(f"Replay: {replay_path}")
print(f"Total steps in replay: {len(rep['steps'])}")
info = rep.get("info", {})
print(f"Episode Info: {info}")
if "agents" in rep:
    print(f"Agents in replay: {rep['agents']}")

# Let's inspect step 0, 1, 2, 3
print("\n--- Step 0 inspection ---")
s0 = rep["steps"][0]
print(f"Step 0 Player 0 status: {s0[0].get('status')}, action: {s0[0].get('action')}")
print(f"Step 0 Player 1 status: {s0[1].get('status')}, action: {s0[1].get('action')}")
obs0_p0 = s0[0].get("observation", {})
print(f"Step 0 Obs P0: step={obs0_p0.get('step')}, player={obs0_p0.get('player')}")
obs0_p1 = s0[1].get("observation", {})
print(f"Step 0 Obs P1: step={obs0_p1.get('step')}, player={obs0_p1.get('player')}")

print("\n--- Step 1 inspection ---")
s1 = rep["steps"][1]
print(f"Step 1 Player 0 action: {s1[0].get('action')}")
print(f"Step 1 Player 1 action: {s1[1].get('action')}")
obs1_p0 = s1[0].get("observation", {})
print(f"Step 1 Obs P0: step={obs1_p0.get('step')}, player={obs1_p0.get('player')}")
print(f"Step 1 Obs P1: step={obs1_p1.get('step')}, player={obs1_p1.get('player')}")

print("\n--- Step 2 inspection ---")
s2 = rep["steps"][2]
print(f"Step 2 Player 0 action: {s2[0].get('action')}")
print(f"Step 2 Player 1 action: {s2[1].get('action')}")

# Final step rewards
s_last = rep["steps"][-1]
print(f"\nFinal Step ({len(rep['steps'])-1}) Rewards:")
print(f"Player 0 Reward: {s_last[0].get('reward')}")
print(f"Player 1 Reward: {s_last[1].get('reward')}")
