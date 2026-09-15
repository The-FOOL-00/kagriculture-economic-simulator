import json
import os

path = 'replays/live_tournament/episode_107543042.json'
print("Episode file exists?", os.path.exists(path))

with open(path, 'r') as f:
    ep = json.load(f)

print(f"Top-level keys in replay: {list(ep.keys())}")
# Let's inspect steps 287, 288, 289 (Day 11 end / Day 12 start)
# Steps are in ep['steps']
steps = ep.get('steps', [])
print(f"Total steps in replay: {len(steps)}")

# Identify players
# In Kaggle replays, steps[0] has observation and players info
# Let's see who is player 0 and player 1
info0 = steps[0][0]
info1 = steps[0][1]
print("Step 0 p0 submission/info:", info0.get('info', {}))
print("Step 0 p1 submission/info:", info1.get('info', {}))

# Let's find Eldritch (56146971) and ORiginators (56120608)
# Look at step 288 (Day 12 dawn: 288 // 24 = 12, hour = 0)
s288 = steps[288]
obs = s288[0]['observation']
farms = obs.get('farms', [])
print(f"Farms count: {len(farms)}")

for p_idx, f in enumerate(farms):
    money = f.get('money')
    hands = f.get('hands', [])
    units = f.get('units', None)
    print(f"Player {p_idx} at Step 288 (Day 12 Hour 0):")
    print(f"  Money: ${money}")
    print(f"  Hands count: {len(hands)}, Hands: {hands}")
    print(f"  Units key exists? {units is not None} (value: {units})")

# Trace Day 12 (steps 288 to 311)
print("\n--- DAY 12 TRACE (Steps 288 to 311) ---")
for s_idx in range(288, 312):
    step_data = steps[s_idx]
    # actions submitted for this step were in step_data[p]['action']
    act0 = step_data[0].get('action', {})
    act1 = step_data[1].get('action', {})
    obs = step_data[0].get('observation', {})
    f0 = obs.get('farms', [])[0]
    f1 = obs.get('farms', [])[1]
    
    # Check hires in market
    hires0 = [m for m in act0.get('market', []) if m and m[0] == 'HIRE']
    hires1 = [m for m in act1.get('market', []) if m and m[0] == 'HIRE']
    
    if hires0 or hires1 or s_idx in [288, 289, 290]:
        print(f"Step {s_idx:3d} (Hr {s_idx%24:2d}):")
        print(f"  P0: Cash=${f0.get('money'):.1f}, Hands={len(f0.get('hands', []))}, Market={act0.get('market')}")
        print(f"  P1: Cash=${f1.get('money'):.1f}, Hands={len(f1.get('hands', []))}, Market={act1.get('market')}")

# Final scores and town shops
final_step = steps[-1]
final_obs = final_step[0]['observation']
print("\n--- FINAL EPISODE SUMMARY ---")
print(f"Final Rewards: P0={final_step[0].get('reward')}, P1={final_step[1].get('reward')}")
print(f"Town unlocked shops: {final_obs.get('town', {}).get('unlocked_shops')}")
