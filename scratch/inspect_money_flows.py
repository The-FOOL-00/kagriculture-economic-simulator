import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([prime_agent, v2_agent])

# Check price received and total revenue earned by P0 and P1
# We can track farm money changes step by step
revenue_by_item_p0 = {}
revenue_by_item_p1 = {}

for step_idx in range(1, 720):
    prev_s = env.steps[step_idx - 1]
    curr_s = env.steps[step_idx]
    
    for p_idx in [0, 1]:
        prev_m = prev_s[p_idx]['observation']['farms'][p_idx]['money']
        curr_m = curr_s[p_idx]['observation']['farms'][p_idx]['money']
        delta_m = curr_m - prev_m
        
        act = prev_s[p_idx].get('action', {})
        m_orders = act.get('market', []) or act.get('market_orders', [])
        sells = [o for o in m_orders if o[0] == 'SELL']
        if sells and delta_m > 0:
            # Money increased from sales!
            # Print big jumps
            day = curr_s[p_idx]['observation']['day']
            hour = curr_s[p_idx]['observation']['hour']
            # print(f"Step {step_idx} (D{day} H{hour}) P{p_idx}: Delta=${delta_m:,.1f} | Sells={sells}")

# Let's inspect total money earned across the game:
# Sum of all positive deltas:
p0_pos_deltas = sum(max(0, env.steps[s][0]['observation']['farms'][0]['money'] - env.steps[s-1][0]['observation']['farms'][0]['money']) for s in range(1, 720))
p1_pos_deltas = sum(max(0, env.steps[s][1]['observation']['farms'][1]['money'] - env.steps[s-1][1]['observation']['farms'][1]['money']) for s in range(1, 720))
p0_neg_deltas = sum(max(0, env.steps[s-1][0]['observation']['farms'][0]['money'] - env.steps[s][0]['observation']['farms'][0]['money']) for s in range(1, 720))
p1_neg_deltas = sum(max(0, env.steps[s-1][1]['observation']['farms'][1]['money'] - env.steps[s][1]['observation']['farms'][1]['money']) for s in range(1, 720))

print(f"P0: Total Inflows=${p0_pos_deltas:,.1f} | Total Outflows=${p0_neg_deltas:,.1f} | Net=${p0_pos_deltas - p0_neg_deltas:,.1f} | Final={env.state[0].reward}")
print(f"P1: Total Inflows=${p1_pos_deltas:,.1f} | Total Outflows=${p1_neg_deltas:,.1f} | Net=${p1_pos_deltas - p1_neg_deltas:,.1f} | Final={env.state[1].reward}")
