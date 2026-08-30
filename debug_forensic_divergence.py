import sys, os
project_root = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, project_root)

from kaggle_environments import make
import importlib.util

# 1. Load previous scratch lab agent
prev_scratch = r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain\1a3b82a1-c6f0-4548-874b-0e3add7eb4e8\scratch\strategies_lab.py"
spec = importlib.util.spec_from_file_location("strat_lab", prev_scratch)
strat_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strat_mod)
prev_agent = strat_mod.StrategyFactory.create_agent("HYBRID", target_cows=6, target_sheep=3, target_melons=10)

# 2. Load our hybrid_6c3s_10m.py
hybrid_mod = importlib.util.spec_from_file_location("h1", "agents/hybrid_6c3s_10m.py")
h1 = importlib.util.module_from_spec(hybrid_mod)
hybrid_mod.loader.exec_module(h1)
our_agent = h1.agent

titan_path = "main.py"

print("=" * 80)
print("RUNNING FORENSIC SINGLE-MATCH COMPARISON ON SEED 10001")
print("=" * 80)

# Test previous scratch agent vs Titan
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=True)
env.run([prev_agent, titan_path])
r0_prev = env.steps[-1][0].reward
r1_titan = env.steps[-1][1].reward
print(f"Previous Scratch Agent vs Titan: Scratch=${r0_prev:,.2f} | Titan=${r1_titan:,.2f}")

# Test our standalone agent vs Titan
env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=True)
env2.run([our_agent, titan_path])
r0_our = env2.steps[-1][0].reward
r1_titan2 = env2.steps[-1][1].reward
print(f"Our Standalone Agent vs Titan:   Our=${r0_our:,.2f} | Titan=${r1_titan2:,.2f}")

# Print state transitions of our agent vs scratch agent across key days (Day 1, 5, 10, 15, 20, 25, 29)
print("\n--- Day-by-Day Inspection of Our Agent ---")
for step_idx in [24*d for d in [0, 1, 5, 10, 15, 20, 25, 28, 29]]:
    if step_idx < len(env2.steps):
        st = env2.steps[step_idx]
        obs = st[0].observation
        p0_farm = obs['farms'][0]
        priv0 = obs['private']
        print(f"Day {obs['day']:2d} (Step {obs['step']:3d}): Money=${p0_farm['money']:8.1f} | Hands={len(p0_farm['hands'])} | Quads={p0_farm['unlocked_quadrants']} | Shed={priv0['shed']}")
