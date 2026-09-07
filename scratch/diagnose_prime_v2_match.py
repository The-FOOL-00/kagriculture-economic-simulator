import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([prime_agent, v2_agent])

# Inspect state at end of game
p0 = env.state[0]
p1 = env.state[1]
print("Player 0 (Prime) final reward:", p0.reward)
print("Player 1 (V2) final reward:", p1.reward)

# Inspect steps around Day 0, Day 5, Day 10, Day 15, Day 20, Day 25, Day 29
for step_idx in [23, 119, 239, 263, 359, 479, 599, 719]:
    state_step = env.steps[step_idx]
    obs0 = state_step[0]['observation']
    obs1 = state_step[1]['observation']
    f0 = obs0['farms'][0]
    f1 = obs0['farms'][1]
    day = obs0.get('day', step_idx // 24)
    hour = obs0.get('hour', step_idx % 24)
    print(f"\n--- Step {step_idx} (Day {day} Hour {hour}) ---")
    print(f"P0 Money: ${f0['money']:,.1f} | Quads: {f0.get('unlocked_quadrants', [])} | Hands: {len(f0.get('hands', []))}")
    print(f"P1 Money: ${f1['money']:,.1f} | Quads: {f1.get('unlocked_quadrants', [])} | Hands: {len(f1.get('hands', []))}")
    print(f"P0 Shed: {obs0.get('private', {}).get('shed', {})}")
    print(f"P1 Shed: {obs1.get('private', {}).get('shed', {})}")
    
    # Count animals
    def count_animals(farm):
        cows, sheep = 0, 0
        for r in farm.get('tiles', []):
            for t in r:
                if isinstance(t, dict) and t.get('kind') == 'PASTURE':
                    atype = t.get('animal')
                    if atype == 'COW': cows += 1
                    elif atype == 'SHEEP': sheep += 1
        return cows, sheep

        
    p0_c, p0_s = count_animals(f0)
    p1_c, p1_s = count_animals(f1)
    print(f"P0 Animals: Cow={p0_c}, Sheep={p0_s} | P1 Animals: Cow={p1_c}, Sheep={p1_s}")
    
    mkt = obs0.get('market', {})
    print(f"Market Prices: Wheat={mkt.get('WHEAT', {}).get('price', 0):.1f}, Mel={mkt.get('MELON', {}).get('price', 0):.1f}, Wool={mkt.get('WOOL', {}).get('price', 0):.1f}, Milk={mkt.get('MILK', {}).get('price', 0):.1f}")


