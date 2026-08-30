import os
import sys
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
ab_file = os.path.join(project_root, "scratch", "clean_ablations", "apex_no_2day_feed.py")
base_file = os.path.join(project_root, "scratch", "clean_ablations", "apex_base.py")

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 50000}, debug=True)
env.run([ab_file, base_file])

r0 = env.steps[-1][0].reward
r1 = env.steps[-1][1].reward
print(f"Ab Reward: {r0}, Base Reward: {r1}")
