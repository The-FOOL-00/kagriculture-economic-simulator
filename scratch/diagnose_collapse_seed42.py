import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([prime_agent, v2_agent])

print("Match finished! P0 Reward:", env.state[0].reward, "P1 Reward:", env.state[1].reward)

# Print checkpoints every 3 days
for d in range(0, 30, 3):
    step_idx = min(719, d * 24 + 23)
    obs0 = env.steps[step_idx][0]['observation']
    f0 = obs0['farms'][0]
    p0 = obs0.get('private', {})
    print(f"Day {d:2d} (Step {step_idx:3d}): Money=${f0['money']:,.0f} | Quads={f0['unlocked_quadrants']} | Shed={p0.get('shed', {})} | Seeds={p0.get('seeds', {})}")
