import sys, os
sys.path.insert(0, os.path.abspath('external_repos/kaggriculture-v66-agent'))
from main import agent as v66_agent
import importlib.util
from kaggle_environments import make

spec = importlib.util.spec_from_file_location('v2', 'agents/slot4_control_frozen_v2.py')
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42})
env.run([v66_agent, v2.agent])

print("=== V66 MARKET TRANSACTIONS (STEPS 0-288) ===")
for step_idx in range(289):
    state0 = env.steps[step_idx][0]
    action0 = state0.get('action') or {}
    market_orders = action0.get('market') or []
    if market_orders:
        day = step_idx // 24
        hour = step_idx % 24
        print(f"Step {step_idx:3d} (Day {day:2d}, Hr {hour:2d}): {market_orders}")
