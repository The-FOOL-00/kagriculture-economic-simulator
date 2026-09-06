import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import opponents.replay_crop_dusta as cd_opp
import opponents.replay_whyme_labs as whyme_opp

seeds = [215620170, 104816794]
print("=== RERUNNING CAUSAL DECOMPOSITION TEST HARNESS ===")
for s in seeds:
    # Match 1: V2 vs Whyme
    env = kaggle_environments.make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
    env.run([v2.agent, whyme_opp.agent])
    r0, r1 = env.steps[-1][0]["reward"], env.steps[-1][1]["reward"]
    print(f"Seed {s} | V2: ${r0:,.1f} vs Whyme: ${r1:,.1f}")

    # Match 2: Crop Dusta Replay vs Whyme
    env = kaggle_environments.make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
    env.run([cd_opp.agent, whyme_opp.agent])
    r0, r1 = env.steps[-1][0]["reward"], env.steps[-1][1]["reward"]
    print(f"Seed {s} | CD_REPLAY: ${r0:,.1f} vs Whyme: ${r1:,.1f}")

    # Match 3: Crop Dusta Replay vs V2
    env = kaggle_environments.make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
    env.run([cd_opp.agent, v2.agent])
    r0, r1 = env.steps[-1][0]["reward"], env.steps[-1][1]["reward"]
    print(f"Seed {s} | CD_REPLAY: ${r0:,.1f} vs V2: ${r1:,.1f}")
