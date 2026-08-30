import json
import kaggle_environments
from kaggle_environments import make

print("Testing full 720-turn episode in official env.run()...")

p0_run_records = []
p1_run_records = []

def agent0_run(obs, cfg):
    p0_run_records.append({
        "step_in_obs": "step" in obs,
        "step_val": obs.get("step"),
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "player": obs.get("player"),
        "keys": sorted(list(obs.keys()))
    })
    return []

def agent1_run(obs, cfg):
    p1_run_records.append({
        "step_in_obs": "step" in obs,
        "step_val": obs.get("step"),
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "player": obs.get("player"),
        "keys": sorted(list(obs.keys()))
    })
    return []

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=True)
env.run([agent0_run, agent1_run])

print(f"Recorded turns in env.run: P0={len(p0_run_records)}, P1={len(p1_run_records)}")

# Check every single turn
p0_none_step = [i for i, r in enumerate(p0_run_records) if r["step_val"] is None]
p1_none_step = [i for i, r in enumerate(p1_run_records) if r["step_val"] is None]
p0_clock_mismatch = []
p1_clock_mismatch = []

for i in range(len(p0_run_records)):
    calc_turn_0 = p0_run_records[i]["day"] * 24 + p0_run_records[i]["hour"]
    if p0_run_records[i]["step_val"] is not None and p0_run_records[i]["step_val"] != calc_turn_0:
        p0_clock_mismatch.append((i, p0_run_records[i]["step_val"], calc_turn_0))

for i in range(len(p1_run_records)):
    calc_turn_1 = p1_run_records[i]["day"] * 24 + p1_run_records[i]["hour"]
    if p1_run_records[i]["step_val"] is not None and p1_run_records[i]["step_val"] != calc_turn_1:
        p1_clock_mismatch.append((i, p1_run_records[i]["step_val"], calc_turn_1))

print("=== OFFICIAL env.run RESULTS ===")
print(f"P0 None step count: {len(p0_none_step)} / {len(p0_run_records)}")
print(f"P1 None step count: {len(p1_none_step)} / {len(p1_run_records)}")
print(f"P0 clock mismatches (day*24+hour vs step): {len(p0_clock_mismatch)}")
print(f"P1 clock mismatches (day*24+hour vs step): {len(p1_clock_mismatch)}")
if len(p1_none_step) > 0:
    print(f"First 5 P1 None step turns: {p1_none_step[:5]}")
else:
    print(f"Sample P0 turn 0: step={p0_run_records[0]['step_val']}, day={p0_run_records[0]['day']}, hour={p0_run_records[0]['hour']}")
    print(f"Sample P1 turn 0: step={p1_run_records[0]['step_val']}, day={p1_run_records[0]['day']}, hour={p1_run_records[0]['hour']}")
    print(f"Sample P0 turn 719: step={p0_run_records[-1]['step_val']}, day={p0_run_records[-1]['day']}, hour={p0_run_records[-1]['hour']}")
    print(f"Sample P1 turn 719: step={p1_run_records[-1]['step_val']}, day={p1_run_records[-1]['day']}, hour={p1_run_records[-1]['hour']}")

print("\nTesting manual env.step() loop across 720 turns...")
env_manual = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=True)
env_manual.reset()

manual_p0_steps = []
manual_p1_steps = []

for t in range(720):
    if env_manual.done:
        break
    obs0 = env_manual.state[0].observation
    obs1 = env_manual.state[1].observation
    s0 = obs0.get("step") if isinstance(obs0, dict) else getattr(obs0, "step", None)
    s1 = obs1.get("step") if isinstance(obs1, dict) else getattr(obs1, "step", None)
    d0 = obs0.get("day") if isinstance(obs0, dict) else getattr(obs0, "day", None)
    h0 = obs0.get("hour") if isinstance(obs0, dict) else getattr(obs0, "hour", None)
    d1 = obs1.get("day") if isinstance(obs1, dict) else getattr(obs1, "day", None)
    h1 = obs1.get("hour") if isinstance(obs1, dict) else getattr(obs1, "hour", None)
    manual_p0_steps.append((s0, d0, h0, (d0 or 0) * 24 + (h0 or 0)))
    manual_p1_steps.append((s1, d1, h1, (d1 or 0) * 24 + (h1 or 0)))
    env_manual.step([[], []])

manual_p0_none = [i for i, r in enumerate(manual_p0_steps) if r[0] is None]
manual_p1_none = [i for i, r in enumerate(manual_p1_steps) if r[0] is None]

print("=== MANUAL env.step() RESULTS ===")
print(f"Manual P0 None step count: {len(manual_p0_none)} / {len(manual_p0_steps)}")
print(f"Manual P1 None step count: {len(manual_p1_none)} / {len(manual_p1_steps)}")
print(f"First 3 turns P0 in manual step: {manual_p0_steps[:3]}")
print(f"First 3 turns P1 in manual step: {manual_p1_steps[:3]}")

# Also test if there is any scenario in env.run where player 1 receives step as None under different configurations
