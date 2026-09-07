import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

pass_ag = lambda obs, cfg=None: {}

for s in [42, 100, 2026]:
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
    env.run([prime_agent, pass_ag])
    r_pass = env.state[0].reward
    
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
    env.run([prime_agent, v2_agent])
    r_p0 = env.state[0].reward
    r_p1 = env.state[1].reward
    
    print(f"Seed {s:4d} | Prime vs Pass: {r_pass:,.1f} | Prime vs V2: Prime={r_p0:,.1f} vs V2={r_p1:,.1f} (Margin: {r_p0 - r_p1:+,.1f})")
