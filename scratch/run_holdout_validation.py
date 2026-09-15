"""
scratch/run_holdout_validation.py
=================================
Rigorous Holdout & Solo Validation Harness:
  - Holdout: 500 completely fresh seeds (910,001 to 910,500) x 2 seat swaps = 1,000 matches
  - Opponents: Canonical V66, Canonical V54, Baseline V54++
  - Solo Benchmark: 50 fresh seeds (920,001 to 920,050) vs IDLE
  - Statistics: Mean, Median, SD, 95% CI, Paired t-test, Wilcoxon, W/L/T, Tail loss/gain, Commodity deltas
"""

import os
import sys
import copy
import json
import time
import numpy as np
from collections import defaultdict
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
    os.path.join(BASE_DIR, "candidates"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util

_AGENTS = {}

def get_agent(name: str):
    if name == "IDLE":
        return lambda obs, conf=None: {"farmer": ["PASS"], "hands": [], "market": []}
    if name not in _AGENTS:
        if name == "V54++":
            path = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")
        elif name == "V54_residual":
            path = os.path.join(BASE_DIR, "candidates", "v54_plus_residual.py")
        elif name == "V66":
            path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
        elif name == "V54":
            path = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
        else:
            raise ValueError(f"Unknown agent name: {name}")

        spec = importlib.util.spec_from_file_location(name.replace("+", "p") + "_hld", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _AGENTS[name] = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
    return _AGENTS[name]

def run_match(task):
    seed, a0_name, a1_name = task
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    fn0 = get_agent(a0_name)
    fn1 = get_agent(a1_name)

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    sales0 = defaultdict(float)
    sales1 = defaultdict(float)

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = fn0(o0)
        a1 = fn1(o1)
        # track market sales
        for ord in (a0 or {}).get("market", []) or []:
            if len(ord) >= 3 and ord[0] == "SELL":
                sales0[ord[1]] += float(ord[2])
        for ord in (a1 or {}).get("market", []) or []:
            if len(ord) >= 3 and ord[0] == "SELL":
                sales1[ord[1]] += float(ord[2])
        env.step([a0, a1])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    return {
        "seed": seed,
        "a0": a0_name,
        "a1": a1_name,
        "reward_0": r0,
        "reward_1": r1,
        "margin": r0 - r1,
        "sales_0": dict(sales0),
        "sales_1": dict(sales1),
    }

def bootstrap_ci(arr, n_boot=2000, ci=0.95):
    if len(arr) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(42)
    boot = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return (float(np.percentile(boot, alpha * 100)), float(np.percentile(boot, (1.0 - alpha) * 100)))

def run_evaluation(candidate_name: str, opponent_names: list, seeds: list, max_workers: int = 12):
    results_by_opp = {}

    for opp in opponent_names:
        tasks = []
        # Symmetric 2 seat swaps: (seat 0 and seat 1)
        for seed in seeds:
            tasks.append((seed, candidate_name, opp))
            tasks.append((seed, opp, candidate_name))

        print(f"Running {len(tasks)} matches: {candidate_name} vs {opp} across {len(seeds)} seeds...")
        t0 = time.time()
        match_records = []

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for i, res in enumerate(executor.map(run_match, tasks), 1):
                # normalize candidate as player 0 margin
                if res["a0"] == candidate_name:
                    cand_reward = res["reward_0"]
                    opp_reward = res["reward_1"]
                    margin = cand_reward - opp_reward
                    seat = 0
                else:
                    cand_reward = res["reward_1"]
                    opp_reward = res["reward_0"]
                    margin = cand_reward - opp_reward
                    seat = 1

                match_records.append({
                    "seed": res["seed"],
                    "seat": seat,
                    "candidate_reward": cand_reward,
                    "opponent_reward": opp_reward,
                    "margin": margin,
                })
                if i % 200 == 0 or i == len(tasks):
                    print(f"  [{opp}] Completed {i}/{len(tasks)} ({time.time()-t0:.1f}s)...")

        cand_rewards = np.array([m["candidate_reward"] for m in match_records])
        opp_rewards = np.array([m["opponent_reward"] for m in match_records])
        margins = np.array([m["margin"] for m in match_records])

        # Paired t-test & Wilcoxon
        ttest_p = float(stats.ttest_1samp(margins, 0.0).pvalue)
        try:
            wilcoxon_p = float(stats.wilcoxon(margins).pvalue)
        except Exception:
            wilcoxon_p = 1.0

        ci_low, ci_high = bootstrap_ci(margins)

        results_by_opp[opp] = {
            "matches": len(match_records),
            "candidate_mean": float(np.mean(cand_rewards)),
            "opponent_mean": float(np.mean(opp_rewards)),
            "margin_mean": float(np.mean(margins)),
            "margin_median": float(np.median(margins)),
            "margin_sd": float(np.std(margins)),
            "ci_95": [ci_low, ci_high],
            "ttest_p": ttest_p,
            "wilcoxon_p": wilcoxon_p,
            "wins": int(np.sum(margins > 0)),
            "losses": int(np.sum(margins < 0)),
            "ties": int(np.sum(margins == 0)),
            "win_rate": float(np.mean(margins > 0) * 100.0),
            "tail_loss_5k": float(np.mean(margins < -5000.0) * 100.0),
            "tail_loss_10k": float(np.mean(margins < -10000.0) * 100.0),
            "tail_gain_5k": float(np.mean(margins > 5000.0) * 100.0),
        }

    return results_by_opp

def run_solo(candidate_name: str, seeds: list, max_workers: int = 12):
    tasks = [(seed, candidate_name, "IDLE") for seed in seeds]
    print(f"\nRunning Solo Benchmark: {candidate_name} vs IDLE across {len(seeds)} seeds...")
    t0 = time.time()
    rewards = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for res in executor.map(run_match, tasks):
            rewards.append(res["reward_0"])

    rewards = np.array(rewards)
    ci_low, ci_high = bootstrap_ci(rewards)
    print(f"Solo Benchmark completed in {time.time()-t0:.1f}s.")
    return {
        "seeds": len(rewards),
        "mean": float(np.mean(rewards)),
        "median": float(np.median(rewards)),
        "sd": float(np.std(rewards)),
        "ci_95": [ci_low, ci_high],
    }
