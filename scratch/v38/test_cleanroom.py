import sys
import os

print("Python version:", sys.version)
from kaggle_environments import make

# Test loading V38 agent
agent_path = os.path.abspath("candidates/v38_heuristic_ppo/main.py")
print("Agent path:", agent_path)
print("Agent path exists:", os.path.exists(agent_path))

env = make("kaggriculture", configuration={"episodeSteps": 100}, debug=True)
res = env.run([agent_path, "candidates/v30_a7_standalone/main.py"])
print("Run finished successfully!")
print("Steps executed:", len(res))
print("Final status:", [r["status"] for r in res[-1]])
print("Final rewards:", [r["reward"] for r in res[-1]])
