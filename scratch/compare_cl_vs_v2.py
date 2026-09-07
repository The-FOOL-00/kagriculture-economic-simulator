import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel import agent as cl_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

pass_agent = lambda obs, cfg=None: {}

def run_agent(ag, n=3):
    rewards = []
    for seed in range(n):
        env = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed})
        env.reset()
        env.run([ag, pass_agent])
        rewards.append(env.state[0].reward)
    return rewards

print('Running 3 seeds each...')
cl_r = run_agent(cl_agent)
v2_r = run_agent(v2_agent)
print('CL-Aethel v3 rewards:', cl_r, '| mean:', sum(cl_r)/len(cl_r))
print('V2 rewards:          ', v2_r, '| mean:', sum(v2_r)/len(v2_r))
