import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

for step in range(150):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    if step >= 115 and step <= 130:
        print(f"Step {step:3d} (D{step//24} H{step%24:2d}): Money=${farm0.get('money'):6.1f} | Hands={len(farm0.get('hands', []))} | Farmer={farm0.get('farmer')} | Shed={priv0.get('shed')} | Seeds={priv0.get('seeds')}")
        print(f"  Farmer: {act0.get('farmer')} | Market: {act0.get('market')}")
        print(f"  Hands: {act0.get('hands')}")
    
    env.step([act0, act1])
