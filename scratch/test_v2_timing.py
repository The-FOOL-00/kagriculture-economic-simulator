import time, os, sys
PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path: sys.path.insert(0, PROJECT_ROOT)
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

t0 = time.time()
env = kaggle_environments.make("kaggriculture", configuration={"seed": 1000})
steps = env.run([v2_agent, "starter"])
rew = steps[-1][0]["reward"]
print(f"Single match took {time.time()-t0:.2f}s, reward={rew}")
