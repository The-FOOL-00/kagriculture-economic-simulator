import sys
import os
import json
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))
from scratch.qualification_counterfactual_suite import (
    BaseQ50Agent,
    U1_SafeWindowUrgencyAgent,
    B1_WeedSuppressionOnlyAgent,
    L_MinimalAgent
)

def run_causal_breakdown_top10():
    with open('scratch/worst_25_detailed_analysis.json') as f:
        w25 = json.load(f)

    top10_seeds = [e['seed'] for e in w25[:10]]
    print("=" * 80)
    print("CAUSAL ATTRIBUTION OF THE 10 WORST LOSSES")
    print("Running 4 Factorial Arms (Q50, A_only Urgency, B_only Weed Gate, AB Minimal) on each seed:")
    print("=" * 80)

    breakdown = {}
    for seed in top10_seeds:
        cfg = {"episodeSteps": 720, "seed": seed}
        
        # 1. Q50
        env_q = kaggle_environments.make("kaggriculture", configuration=cfg)
        r_q = env_q.run([BaseQ50Agent(50), "starter"])[-1][0]["reward"]

        # 2. A_only (Urgency sorting only)
        env_a = kaggle_environments.make("kaggriculture", configuration=cfg)
        r_a = env_a.run([U1_SafeWindowUrgencyAgent(50), "starter"])[-1][0]["reward"]

        # 3. B_only (Weed gating only)
        env_b = kaggle_environments.make("kaggriculture", configuration=cfg)
        r_b = env_b.run([B1_WeedSuppressionOnlyAgent(50), "starter"])[-1][0]["reward"]

        # 4. AB (Both = Frozen Candidate)
        env_ab = kaggle_environments.make("kaggriculture", configuration=cfg)
        r_ab = env_ab.run([L_MinimalAgent(50), "starter"])[-1][0]["reward"]

        delta_ab = r_ab - r_q
        delta_a = r_a - r_q
        delta_b = r_b - r_q

        # Classify which component caused the loss:
        # If delta_a is negative and delta_b is ~0 -> A (Urgency sorting)
        # If delta_b is negative and delta_a is ~0 -> B (Weed suppression)
        # If both negative -> A + B
        # If both ~0 and only AB negative -> Interaction
        component_cause = "Unknown"
        if delta_b < -1000 and delta_a > -500:
            component_cause = "B (Weed Suppression Gating)"
        elif delta_a < -1000 and delta_b > -500:
            component_cause = "A (Urgency Sorting)"
        elif delta_a < -1000 and delta_b < -1000:
            component_cause = "Both A & B independently negative"
        elif delta_ab < -1000 and delta_a >= -500 and delta_b >= -500:
            component_cause = "Super-Destructive Negative Interaction (A x B)"
        else:
            component_cause = f"Mixed (A:{delta_a:+.0f}, B:{delta_b:+.0f})"

        breakdown[seed] = {
            "seed": seed,
            "q50_reward": r_q,
            "cand_reward": r_ab,
            "delta_ab": delta_ab,
            "delta_a": delta_a,
            "delta_b": delta_b,
            "component_cause": component_cause
        }
        print(f"Seed {seed}: Delta(AB) = ${delta_ab:+.2f} | Delta(A) = ${delta_a:+.2f} | Delta(B) = ${delta_b:+.2f} -> Driver: {component_cause}")

    with open('scratch/top10_causal_breakdown.json', 'w') as f:
        json.dump(breakdown, f, indent=2)

if __name__ == '__main__':
    run_causal_breakdown_top10()
