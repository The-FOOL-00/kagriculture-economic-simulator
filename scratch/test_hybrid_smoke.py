import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.hybrid_arch_v1 as hybrid

SEEDS = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 201, 202, 203, 204, 205, 206, 207, 208, 209, 215620170]

print(f"{'Seed':<10} | {'Hybrid (P0)':<15} | {'V2 (P1)':<15} | {'Margin':<15}")
print("-" * 60)

h_scores = []
v_scores = []

for seed in SEEDS:
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    h_agent = hybrid.HybridArchV1Agent()
    v_agent = v2.agent
    
    for step in range(719):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        act0 = h_agent(obs0)
        act1 = v_agent(obs1)
        env.step([act0, act1])
        
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    h_scores.append(r0)
    v_scores.append(r1)
    print(f"{seed:<10} | ${r0:13,.1f} | ${r1:13,.1f} | ${r0 - r1:+13,.1f}")

print("=" * 60)
print(f"Hybrid Mean: ${sum(h_scores)/len(h_scores):,.1f} vs V2 Mean: ${sum(v_scores)/len(v_scores):,.1f}")
print(f"Net Margin: ${sum(h_scores)/len(h_scores) - sum(v_scores)/len(v_scores):+,.1f}")
