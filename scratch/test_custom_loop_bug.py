import json
from kaggle_environments import make

print("=== TESTING CUSTOM STEP LOOP (env.step) vs OFFICIAL RUN (env.run) ===")

env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
env.reset()

print("Initial step after reset:")
print("  env.state[0].observation.step:", getattr(env.state[0].observation, "step", None))
print("  env.state[1].observation.step:", getattr(env.state[1].observation, "step", None))

env.step([{}, {}])
print("\nAfter 1st env.step([{}, {}]):")
print("  env.state[0].observation.step:", getattr(env.state[0].observation, "step", None))
print("  env.state[1].observation.step:", getattr(env.state[1].observation, "step", None))

env.step([{}, {}])
print("\nAfter 2nd env.step([{}, {}]):")
print("  env.state[0].observation.step:", getattr(env.state[0].observation, "step", None))
print("  env.state[1].observation.step:", getattr(env.state[1].observation, "step", None))
print("  env.state[0].observation.day/hour:", env.state[0].observation.day, env.state[0].observation.hour)
print("  env.state[1].observation.day/hour:", env.state[1].observation.day, env.state[1].observation.hour)
