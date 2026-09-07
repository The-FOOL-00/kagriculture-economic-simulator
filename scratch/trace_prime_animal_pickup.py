import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})

for step_idx in range(260):
    env.step([prime_agent(env.state[0]['observation']), {}])

for step_idx in range(260, 360):
    env.step([prime_agent(env.state[0]['observation']), {}])
    obs = env.state[0]['observation']
    shed = obs['private']['shed']
    c_shed = shed.get('COW', 0)
    s_shed = shed.get('SHEEP', 0)
    if c_shed > 0 or s_shed > 0:
        day = obs['day']
        hour = obs['hour']
        act = env.steps[-1][0]['action']
        f_act = act.get('farmer')
        h_acts = act.get('hands')
        print(f"Step {step_idx:3d} (D{day:2d} H{hour:2d}): Shed Cow={c_shed} Sheep={s_shed} | Farmer={f_act} | Hand0={h_acts[0] if h_acts else None} | Hand1={h_acts[1] if len(h_acts)>1 else None}")

