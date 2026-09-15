"""
scratch/test_solo_eval.py
=========================
Evaluates V54++ and Arm C4 solo against IDLE across 25 fresh seeds (Seeds 2500 to 2524).
"""

import os
import sys
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import importlib.util
from kaggle_environments import make

BASE_DIR = os.path.abspath(".")
CANDIDATE_PATHS = {
    "V54++": os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py"),
}

for p in [os.path.dirname(CANDIDATE_PATHS["V54++"]), os.path.join(BASE_DIR, "scratch")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from midlate_counterfactual_arms import get_arm_agent

def idle_agent(obs, configuration=None):
    return {"farmer": ["PASS"], "market": []}

def get_v54():
    spec = importlib.util.spec_from_file_location("v54_solo", CANDIDATE_PATHS["V54++"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent")

def run_solo_match(args):
    agent_type, seed = args
    if agent_type == "C4":
        fn = get_arm_agent("C4")
    else:
        fn = get_v54()
        
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = fn(o0, env.configuration)
        a1 = idle_agent(o1, env.configuration)
        env.step([a0, a1])
        
    return {
        "agent": agent_type,
        "seed": seed,
        "reward": float(env.state[0].reward)
    }

def bootstrap_ci(deltas, n_boot=2000, alpha=0.05):
    means = []
    arr = np.array(deltas)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    return float(np.percentile(means, 100 * (alpha / 2))), float(np.percentile(means, 100 * (1 - alpha / 2)))

def main():
    seeds = list(range(2500, 2525))
    tasks = [("V54++", s) for s in seeds] + [("C4", s) for s in seeds]
    
    print(f"Running Solo vs IDLE for V54++ and C4 across {len(seeds)} seeds...")
    results = {"V54++": [], "C4": []}
    with ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(run_solo_match, tasks):
            results[res["agent"]].append(res)
            
    for agent_name in ["V54++", "C4"]:
        rews = [r["reward"] for r in results[agent_name]]
        arr = np.array(rews)
        ci_l, ci_h = bootstrap_ci(rews)
        print(f"\n{agent_name} Solo Performance (25 Seeds vs IDLE):")
        print(f"  Mean Reward:   ${np.mean(arr):,.2f}")
        print(f"  Median Reward: ${np.median(arr):,.2f}")
        print(f"  Std:           ${np.std(arr):,.2f}")
        print(f"  95% CI:        [${ci_l:,.2f}, ${ci_h:,.2f}]")
        
    # Paired delta: C4 - V54++
    v54_dict = {r["seed"]: r["reward"] for r in results["V54++"]}
    c4_dict = {r["seed"]: r["reward"] for r in results["C4"]}
    deltas = [c4_dict[s] - v54_dict[s] for s in seeds]
    d_arr = np.array(deltas)
    d_ci_l, d_ci_h = bootstrap_ci(deltas)
    print(f"\nPaired Solo Delta (C4 - V54++):")
    print(f"  Mean Delta:    ${np.mean(d_arr):+,.2f}")
    print(f"  Median Delta:  ${np.median(d_arr):+,.2f}")
    print(f"  95% CI:        [${d_ci_l:+,.2f}, ${d_ci_h:+,.2f}]")

if __name__ == "__main__":
    main()
