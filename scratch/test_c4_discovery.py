"""
scratch/test_c4_discovery.py
============================
Evaluates Arm C4 against V54++ head-to-head and against V66 on fresh seeds:
Seeds 2000 to 2099 (100 fresh seeds x 2 seats = 200 matches).
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
    "V66": os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py"),
}

for p in [os.path.dirname(CANDIDATE_PATHS["V54++"]), os.path.join(BASE_DIR, "scratch")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from midlate_counterfactual_arms import get_arm_agent

def get_v54():
    spec = importlib.util.spec_from_file_location("v54_eval", CANDIDATE_PATHS["V54++"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent")

def get_v66():
    spec = importlib.util.spec_from_file_location("v66_eval", CANDIDATE_PATHS["V66"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent")

def run_h2h(args):
    seed, seat = args
    fn_c4 = get_arm_agent("C4")
    fn_v54 = get_v54()
    
    p0 = fn_c4 if seat == 0 else fn_v54
    p1 = fn_v54 if seat == 0 else fn_c4
    c4_idx = seat
    v54_idx = 1 - seat
    
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = p0(o0, env.configuration)
        a1 = p1(o1, env.configuration)
        env.step([a0, a1])
        
    rew_c4 = float(env.state[c4_idx].reward)
    rew_v54 = float(env.state[v54_idx].reward)
    
    return {
        "seed": seed,
        "seat": seat,
        "rew_c4": rew_c4,
        "rew_v54": rew_v54,
        "margin": rew_c4 - rew_v54
    }

def bootstrap_ci(deltas, n_boot=2000, alpha=0.05):
    means = []
    arr = np.array(deltas)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    return float(np.percentile(means, 100 * (alpha / 2))), float(np.percentile(means, 100 * (1 - alpha / 2)))

def main():
    seeds = list(range(2000, 2100))
    tasks = [(s, seat) for s in seeds for seat in [0, 1]]
    
    print(f"Running Arm C4 vs V54++ across {len(tasks)} matches (100 fresh seeds x 2 seats)...")
    results = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        for idx, res in enumerate(executor.map(run_h2h, tasks)):
            results.append(res)
            if (idx + 1) % 50 == 0 or (idx + 1) == len(tasks):
                print(f"Done [{idx+1}/{len(tasks)}]")
                
    margins = [r["margin"] for r in results]
    arr = np.array(margins)
    ci_low, ci_high = bootstrap_ci(margins)
    
    print("\n==========================================")
    print("ARM C4 vs FROZEN V54++ HEAD-TO-HEAD RESULT")
    print("==========================================")
    print(f"Matches: {len(margins)}")
    print(f"Mean Margin: {np.mean(arr):+.2f}")
    print(f"Median Margin: {np.median(arr):+.2f}")
    print(f"Std Margin: {np.std(arr):.2f}")
    print(f"95% Bootstrap CI: [{ci_low:+.2f}, {ci_high:+.2f}]")
    print(f"Wins: {np.sum(arr > 0)}, Losses: {np.sum(arr < 0)}, Ties: {np.sum(arr == 0)}")
    print(f"P(margin < -500): {np.mean(arr < -500)*100:.1f}%")
    print(f"P(margin < -1000): {np.mean(arr < -1000)*100:.1f}%")
    print(f"P(margin > +2000): {np.mean(arr > 2000)*100:.1f}%")

if __name__ == "__main__":
    main()
