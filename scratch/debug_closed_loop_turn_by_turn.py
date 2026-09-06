import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()

env.reset()

for step in range(30):
    obs0 = env.state[0].observation
    obs1 = env.state[1].observation
    
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(obs1)
    
    print(f"\n=== STEP {step} ===")
    print(f"Money={farm0.get('money')}, Farmer={farm0.get('farmer')}, Hands={farm0.get('hands')}")
    print(f"Shed={priv0.get('shed')}, Seeds={priv0.get('seeds')}")
    print(f"Farmer Action: {act0.get('farmer')}")
    print(f"Hands Actions: {act0.get('hands')}")
    print(f"Market Actions: {act0.get('market')}")
    
    env.step([act0, act1])
