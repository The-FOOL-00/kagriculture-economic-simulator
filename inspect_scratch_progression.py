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

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=True)
env.run([prev_agent, "main.py"])

print("=== INSPECTING PREVIOUS SCRATCH LAB AGENT ===")
for step_idx in [24*d for d in [0, 1, 2, 5, 10, 12, 15, 20, 25, 28, 29]]:
    if step_idx < len(env.steps):
        st = env.steps[step_idx]
        obs = st[0].observation
        p0_farm = obs['farms'][0]
        priv0 = obs['private']
        print(f"Day {obs['day']:2d} (Step {obs['step']:3d}): Money=${p0_farm['money']:8.1f} | Hands={len(p0_farm['hands'])} | Quads={p0_farm['unlocked_quadrants']} | Shed={priv0['shed']}")
