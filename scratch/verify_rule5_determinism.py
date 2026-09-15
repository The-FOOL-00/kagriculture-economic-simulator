import hashlib
import json
import kagsim

def run_experiment(seed):
    game = kagsim.Game(seed)
    
    # Let's perform non-trivial actions: planting, watering, buying seeds, selling
    # Day 0: Buy wheat seeds, plant, water
    states = []
    actions = []
    
    for t in range(720):
        # Read observation
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        
        # Decide action for seat 0
        p0_act = {"farmer": ["PASS"], "hands": [], "market": []}
        p1_act = {"farmer": ["PASS"], "hands": [], "market": []}
        
        if t == 0:
            p0_act["market"] = [["BUY_SEED", "WHEAT", 5]]
        elif 1 <= t <= 5:
            p0_act["farmer"] = ["PLANT", "WHEAT"]
        elif 6 <= t <= 10:
            p0_act["farmer"] = ["WATER"]
        elif t == 24:
            p0_act["farmer"] = ["HARVEST"]
        elif t == 25:
            p0_act["market"] = [["SELL", "WHEAT", 1]]
            
        actions.append({"t": t, "a0": p0_act, "a1": p1_act})
        game.step(p0_act, p1_act)
        
        # Record state snapshot
        snap = {
            "t": t,
            "step": game.step_count,
            "bank0": game.reward(0),
            "bank1": game.reward(1),
            "market": game.observe(0).get("market"),
            "farm0_money": game.observe(0)["farms"][0].get("money"),
            "farm0_inv": game.observe(0)["farms"][0].get("inventory"),
            "farm0_tiles": game.observe(0)["farms"][0].get("tiles"),
        }
        states.append(snap)
        
    final_reward = (game.reward(0), game.reward(1))
    return actions, states, final_reward

print("Running Run 1 (seed 42)...")
acts1, states1, rew1 = run_experiment(42)

print("Running Run 2 (seed 42)...")
acts2, states2, rew2 = run_experiment(42)

# Check bit-for-bit identity
raw1 = json.dumps(states1, sort_keys=True)
raw2 = json.dumps(states2, sort_keys=True)

h1 = hashlib.sha256(raw1.encode('utf-8')).hexdigest()
h2 = hashlib.sha256(raw2.encode('utf-8')).hexdigest()

act_raw1 = json.dumps(acts1, sort_keys=True)
act_raw2 = json.dumps(acts2, sort_keys=True)
act_h1 = hashlib.sha256(act_raw1.encode('utf-8')).hexdigest()
act_h2 = hashlib.sha256(act_raw2.encode('utf-8')).hexdigest()

print("\n=== Determinism Results ===")
print(f"Run 1 State Hash:  {h1}")
print(f"Run 2 State Hash:  {h2}")
print(f"Hashes Match:      {h1 == h2}")
print(f"Action Hash Match: {act_h1 == act_h2}")
print(f"Final Rewards 1:   {rew1}")
print(f"Final Rewards 2:   {rew2}")
print(f"Rewards Match:     {rew1 == rew2}")

# Write raw test outputs
out_data = {
    "seed": 42,
    "steps": 720,
    "action_hash_run1": act_h1,
    "action_hash_run2": act_h2,
    "state_hash_run1": h1,
    "state_hash_run2": h2,
    "hashes_identical": h1 == h2,
    "final_reward_run1": rew1,
    "final_reward_run2": rew2,
    "run1_sample_step_300": states1[300],
    "run2_sample_step_300": states2[300]
}
with open(r"forensic_verification\simulator_tests\determinism_test.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2)

print("Saved forensic_verification/simulator_tests/determinism_test.json")
