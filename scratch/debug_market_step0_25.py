import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

for step in range(25):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    print(f"Step {step:2d}: Money=${farm0['money']:5.1f} | Shed wheat={priv0['shed'].get('WHEAT')} | Market Act={act0.get('market')}")
    env.step([act0, act1])
