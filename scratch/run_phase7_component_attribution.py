import sys
import os
import json
from collections import defaultdict
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import (
    BaseQ50Agent,
    U1_SafeWindowUrgencyAgent,
    B1_WeedSuppressionOnlyAgent,
    L_MinimalAgent
)

def run_job(args):
    pol_name, seed = args
    if pol_name == "Raw_Q50":
        agent = BaseQ50Agent(50)
    elif pol_name == "A_only":
        agent = U1_SafeWindowUrgencyAgent(50)
    elif pol_name == "B_only":
        agent = B1_WeedSuppressionOnlyAgent(50)
    elif pol_name == "A_plus_B":
        agent = L_MinimalAgent(50)
    else:
        raise ValueError(f"Unknown policy {pol_name}")

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    env_rew = float(steps[-1][0]["reward"])
    return pol_name, seed, env_rew

def main():
    seeds = list(range(1300, 1400)) # N=100 pristine discovery-block seeds
    policies = ["Raw_Q50", "A_only", "B_only", "A_plus_B"]
    print(f"Running Phase 7 Component Attribution on fresh discovery seeds 1300-1399 (N={len(seeds)})...", flush=True)

    jobs = [(p, s) for p in policies for s in seeds]
    results = defaultdict(dict)

    with ProcessPoolExecutor(max_workers=11) as executor:
        for i, (pol, seed, rew) in enumerate(executor.map(run_job, jobs, chunksize=4)):
            results[pol][seed] = rew
            if (i + 1) % 50 == 0:
                print(f"Completed {i + 1}/{len(jobs)} runs...", flush=True)

    q50_rews = np.array([results["Raw_Q50"][s] for s in seeds])
    a_rews = np.array([results["A_only"][s] for s in seeds])
    b_rews = np.array([results["B_only"][s] for s in seeds])
    ab_rews = np.array([results["A_plus_B"][s] for s in seeds])

    d_a = a_rews - q50_rews
    d_b = b_rews - q50_rews
    d_ab = ab_rews - q50_rews

    effect_a = float(np.mean(d_a))
    effect_b = float(np.mean(d_b))
    effect_ab = float(np.mean(d_ab))
    interaction = effect_ab - (effect_a + effect_b)

    print("\n" + "="*80, flush=True)
    print("PHASE 7: COMPONENT ATTRIBUTION RESULTS (Seeds 1300-1399, N=100)", flush=True)
    print("="*80, flush=True)
    print(f"Raw Q50 Mean:        ${np.mean(q50_rews):.2f}", flush=True)
    print(f"A_only (Urgency):    ${np.mean(a_rews):.2f} (Delta vs Q50: ${effect_a:+.2f}, Win rate: {np.mean(d_a > 0)*100:.1f}%)", flush=True)
    print(f"B_only (Weed Gate):  ${np.mean(b_rews):.2f} (Delta vs Q50: ${effect_b:+.2f}, Win rate: {np.mean(d_b > 0)*100:.1f}%)", flush=True)
    print(f"A+B (L_Minimal):     ${np.mean(ab_rews):.2f} (Delta vs Q50: ${effect_ab:+.2f}, Win rate: {np.mean(d_ab > 0)*100:.1f}%)", flush=True)
    print(f"\nLinear Sum (A + B):  ${effect_a + effect_b:+.2f}", flush=True)
    print(f"Interaction (A, B):  ${interaction:+.2f}", flush=True)
    print("="*80, flush=True)

    out = {
        "seeds": seeds,
        "mean_q50": float(np.mean(q50_rews)),
        "effect_a": effect_a,
        "effect_b": effect_b,
        "effect_ab": effect_ab,
        "interaction": interaction,
        "win_rate_a": float(np.mean(d_a > 0)*100),
        "win_rate_b": float(np.mean(d_b > 0)*100),
        "win_rate_ab": float(np.mean(d_ab > 0)*100),
    }
    with open("scratch/phase7_component_attribution_results.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
