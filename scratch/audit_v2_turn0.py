import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})
env.reset()

act0 = v2.agent(env.state[0].observation)
print("=== V2 TURN 0 MARKET ACTIONS ===")
print(act0.get("market"))
print("=== V2 TURN 0 FARMER ACTION ===")
print(act0.get("farmer"))
