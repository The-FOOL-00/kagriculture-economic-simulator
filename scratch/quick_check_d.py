from kaggle_environments import make

cfg = {"episodeSteps": 720, "seed": 42}
env = make("kaggriculture", configuration=cfg, debug=True)
env.run(["candidates/counterstrategy_ablation/candidate_D.py", "opponents/live_flooder_v1.py"])
r0 = env.steps[-1][0].reward
r1 = env.steps[-1][1].reward
print(f"Candidate D (P0): ${r0}")
print(f"LiveFlooder (P1): ${r1}")
