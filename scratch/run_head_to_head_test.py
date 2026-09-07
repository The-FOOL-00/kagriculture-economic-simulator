import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from scratch.test_hybrid_features import HybridCandidate
from candidates.candidate_cl_aethel_prime import agent as prime_agent
import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as v1

h = HybridCandidate()
def hybrid_agent(obs, cfg=None): return h(obs, cfg)

seeds = [42, 100, 2024, 104816794, 104817623]

print("="*80)
print("HEAD-TO-HEAD MATCHES: HYBRID vs FROZEN V2")
print("="*80)
for s in seeds:
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
    env.run([hybrid_agent, v2.agent])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    print(f"Seed {s:9d}: Hybrid (P0) = ${r0:,.1f} | V2 (P1) = ${r1:,.1f} | Margin = ${r0 - r1:>+10,.1f}")

print("\n" + "="*80)
print("HEAD-TO-HEAD MATCHES: HYBRID vs FROZEN V1")
print("="*80)
for s in seeds:
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
    env.run([hybrid_agent, v1.agent])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    print(f"Seed {s:9d}: Hybrid (P0) = ${r0:,.1f} | V1 (P1) = ${r1:,.1f} | Margin = ${r0 - r1:>+10,.1f}")

print("\n" + "="*80)
print("HEAD-TO-HEAD MATCHES: PRIME vs FROZEN V2 (CONTROL)")
print("="*80)
for s in seeds:
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
    env.run([prime_agent, v2.agent])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    print(f"Seed {s:9d}: Prime (P0)  = ${r0:,.1f} | V2 (P1) = ${r1:,.1f} | Margin = ${r0 - r1:>+10,.1f}")
