"""
scratch/validate_midlate_conversion.py
======================================
Harness for Discovery Validation, Untouched Holdout Validation, and Solo Validation:
1. Discovery Validation: >= 500 fresh seeds against Canonical V66.
2. Untouched Holdout Validation: >= 500 fresh seeds x 2 seats against V54++ and V66.
3. Solo Validation: 25-50 fresh seeds vs IDLE.
Computes paired t-test, Wilcoxon, bootstrap CIs, win/loss/tie, tail risk distribution.
Outputs:
- research/midlate_validation_results.json
"""

import os
import sys
import copy
import time
import json
import numpy as np
from scipy import stats
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import importlib.util
from kaggle_environments import make

BASE_DIR = os.path.abspath(".")
CANDIDATE_PATHS = {
    "V54++": os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py"),
    "V66": os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py"),
}

for p in [os.path.dirname(CANDIDATE_PATHS["V54++"]), os.path.dirname(CANDIDATE_PATHS["V66"]), os.path.join(BASE_DIR, "scratch")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from midlate_counterfactual_arms import get_arm_agent

def idle_agent(obs, configuration=None):
    return {"farmer": ["PASS"], "market": []}

def run_single_eval_match(args):
    agent_a_spec, agent_b_spec, seed, seat = args
    
    # Load agent A
    if isinstance(agent_a_spec, str) and agent_a_spec.startswith("arm:"):
        fn_a = get_arm_agent(agent_a_spec.split(":")[1])
    elif agent_a_spec == "IDLE":
        fn_a = idle_agent
    else:
        spec_a = importlib.util.spec_from_file_location("agent_a", CANDIDATE_PATHS[agent_a_spec])
        mod_a = importlib.util.module_from_spec(spec_a)
        spec_a.loader.exec_module(mod_a)
        fn_a = getattr(mod_a, "agent", getattr(mod_a, "kaggle_agent", None))
        
    # Load agent B
    if isinstance(agent_b_spec, str) and agent_b_spec.startswith("arm:"):
        fn_b = get_arm_agent(agent_b_spec.split(":")[1])
    elif agent_b_spec == "IDLE":
        fn_b = idle_agent
    else:
        spec_b = importlib.util.spec_from_file_location("agent_b", CANDIDATE_PATHS[agent_b_spec])
        mod_b = importlib.util.module_from_spec(spec_b)
        spec_b.loader.exec_module(mod_b)
        fn_b = getattr(mod_b, "agent", getattr(mod_b, "kaggle_agent", None))
        
    p0 = fn_a if seat == 0 else fn_b
    p1 = fn_b if seat == 0 else fn_a
    idx_a = seat
    idx_b = 1 - seat
    
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = p0(o0, env.configuration)
        a1 = p1(o1, env.configuration)
        env.step([a0, a1])
        
    rew_a = float(env.state[idx_a].reward)
    rew_b = float(env.state[idx_b].reward)
    
    return {
        "seed": seed,
        "seat": seat,
        "reward_a": rew_a,
        "reward_b": rew_b,
        "margin": rew_a - rew_b
    }

def bootstrap_ci(deltas, n_boot=2000, alpha=0.05):
    if len(deltas) == 0:
        return 0.0, 0.0
    means = []
    arr = np.array(deltas)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    return float(np.percentile(means, 100 * (alpha / 2))), float(np.percentile(means, 100 * (1 - alpha / 2)))

def run_suite(agent_a_spec, agent_b_spec, seeds, symmetric=True):
    tasks = []
    for s in seeds:
        tasks.append((agent_a_spec, agent_b_spec, s, 0))
        if symmetric:
            tasks.append((agent_a_spec, agent_b_spec, s, 1))
            
    results = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(run_single_eval_match, tasks):
            results.append(res)
            
    margins = [r["margin"] for r in results]
    arr = np.array(margins)
    ci_low, ci_high = bootstrap_ci(margins)
    
    # Statistical tests
    ttest_stat, ttest_p = stats.ttest_1samp(arr, 0.0) if len(arr) > 1 else (0.0, 1.0)
    try:
        wilc_stat, wilc_p = stats.wilcoxon(arr) if len(arr) > 1 and not np.all(arr == 0) else (0.0, 1.0)
    except Exception:
        wilc_stat, wilc_p = 0.0, 1.0
        
    return {
        "n_matches": len(results),
        "mean_margin": float(np.mean(arr)),
        "median_margin": float(np.median(arr)),
        "std_margin": float(np.std(arr)),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ttest_p": float(ttest_p),
        "wilcoxon_p": float(wilc_p),
        "wins": int(np.sum(arr > 0)),
        "losses": int(np.sum(arr < 0)),
        "ties": int(np.sum(arr == 0)),
        "p_loss_500": float(np.mean(arr < -500.0)),
        "p_loss_1000": float(np.mean(arr < -1000.0)),
        "p_gain_2000": float(np.mean(arr > 2000.0)),
        "raw_matches": results
    }

if __name__ == "__main__":
    print("Validation harness module ready.")
