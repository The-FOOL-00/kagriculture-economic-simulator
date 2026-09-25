"""
Exact Mechanism Comparison: A7 vs V3 vs V22R1
Decomposes economic trajectory and mechanisms across identical seeds.
"""
import sys, os, json
sys.path.insert(0, ".")

from kaggle_environments import make
from scripts.v32_common import load_agent, telemetry

SEEDS = [249675, 249676, 249677, 249678, 249679]

def run_pair(agent0_name, agent1_name, seed):
    a0 = load_agent(agent0_name)
    a1 = load_agent(agent1_name)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    
    # Run
    steps = env.run([lambda obs: a0.act(obs), lambda obs: a1.act(obs)])
    tel = telemetry(env)
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    return r0, r1, tel

print(f"{'Seed':<8} | {'A7 (Seat 0)':<12} {'V3 (Seat 1)':<12} {'Delta (A7 - V3)':<15}")
print("-" * 55)
for s in SEEDS:
    r0, r1, tel = run_pair("E2_A7", "E0_V3", s)
    w0 = tel["first_wash"][0]
    w1 = tel["first_wash"][1]
    print(f"{s:<8} | {r0:<12.1f} {r1:<12.1f} {r0 - r1:<+15.1f}")
    if s == SEEDS[0]:
        print(f"  Step 0 Wash: A7={w0} vs V3={w1}")
        print(f"  Total Hires: A7={tel['hires'][0]} vs V3={tel['hires'][1]}")
        print(f"  Total Plants: A7={tel['plant'][0]} vs V3={tel['plant'][1]}")
        print(f"  Total Sales: A7={tel['sell_qty'][0]} vs V3={tel['sell_qty'][1]}")

print("\n" + "="*55)
print(f"{'Seed':<8} | {'V22R1 (Seat 0)':<15} {'V3 (Seat 1)':<12} {'Delta (V22R1 - V3)':<15}")
print("-" * 55)
for s in SEEDS:
    r0, r1, tel = run_pair("E1_V22R1", "E0_V3", s)
    print(f"{s:<8} | {r0:<15.1f} {r1:<12.1f} {r0 - r1:<+15.1f}")
