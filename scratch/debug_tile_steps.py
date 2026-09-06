import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

for step in range(120):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    if step >= 114 and step <= 118:
        print(f"\n--- STEP {step} ---")
        print(f"Farmer pos: {farm0['farmer']}, inv: {obs0['private']['inventories'][0]}")
        for y in range(5):
            for x in range(5):
                t = farm0['tiles'][y][x]
                if t is not None and t != 'LOCKED':
                    print(f"  Tile ({x}, {y}): {t}")
        print(f"Farmer Action: {act0['farmer']}")
    
    env.step([act0, act1])
