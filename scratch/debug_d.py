from kaggle_environments import make

cfg = {"episodeSteps": 720, "seed": 42}
env = make("kaggriculture", configuration=cfg, debug=True)
env.run(["candidates/counterstrategy_ablation/candidate_D.py", "candidates/slot2_aethel_refined_v2.py"])

for step_num in [0, 1, 24, 100, 200, 500, 710, 719]:
    s = env.steps[step_num]
    print(f"Step {step_num:3d} | D Reward: ${s[0].reward:10.1f} | D Status: {s[0].status:7s} | V2 Reward: ${s[1].reward:10.1f}")
    if step_num in [0, 1, 24]:
        print(f"   D Action: {s[0].action}")
