"""
scratch/run_holdout_gauntlet.py
===============================
Official Holdout Gauntlet for Candidate Residual Modification:
Candidate: V54++ with Aggressive Preemption (deficit=2000, delta=4.0, batch=12)
Partition: 500 completely fresh seeds (910,001 to 910,500) x 2 seat swaps = 1,000 matches per matchup.
Evaluations:
  1. Candidate vs V54++ (Direct Paired Head-to-Head)
  2. Candidate vs V66
  3. Baseline V54++ vs V66 (Control)
  4. Candidate vs V54
  5. Solo benchmark (50 fresh seeds vs IDLE)
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

def get_agent_factory(name: str):
    if name == "IDLE":
        return lambda: (lambda obs, conf=None: {"farmer": ["PASS"], "hands": [], "market": []})
    if name == "V54++":
        from scratch.instrumented_v54_plus import InstrumentedV54Plus
        return lambda: InstrumentedV54Plus()
    if name == "V54_cand_agg_preempt":
        from scratch.instrumented_v54_plus import InstrumentedV54Plus
        return lambda: InstrumentedV54Plus(switches={"aggressive_preempt": True})
    if name == "V66":
        path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
        spec = importlib.util.spec_from_file_location("v66_agent", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        agent_fn = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
        return lambda: agent_fn
    if name == "V54":
        path = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
        spec = importlib.util.spec_from_file_location("v54_agent", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        agent_fn = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
        return lambda: agent_fn
    raise ValueError(f"Unknown agent: {name}")

def run_match_task(task):
    seed, a0_name, a1_name = task
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    fn0 = get_agent_factory(a0_name)()
    fn1 = get_agent_factory(a1_name)()

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = fn0(o0)
        a1 = fn1(o1)
        env.step([a0, a1])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    return {
        "seed": seed,
        "a0": a0_name,
        "a1": a1_name,
        "r0": r0,
        "r1": r1,
        "margin": r0 - r1,
    }

def bootstrap_ci(arr, n_boot=2000, ci=0.95):
    if len(arr) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(12345)
    boot = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return (float(np.percentile(boot, alpha * 100)), float(np.percentile(boot, (1.0 - alpha) * 100)))

def run_symmetric_matchup(agent_a: str, agent_b: str, seeds: list, max_workers: int = 12):
    tasks = []
    for seed in seeds:
        tasks.append((seed, agent_a, agent_b))
        tasks.append((seed, agent_b, agent_a))

    print(f"\nRunning {len(tasks)} matches: {agent_a} vs {agent_b} across {len(seeds)} fresh seeds...")
    t0 = time.time()
    results = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for i, res in enumerate(executor.map(run_match_task, tasks), 1):
            if res["a0"] == agent_a:
                r_a = res["r0"]
                r_b = res["r1"]
                seat = 0
            else:
                r_a = res["r1"]
                r_b = res["r0"]
                seat = 1
            margin = r_a - r_b
            results.append({
                "seed": res["seed"],
                "seat": seat,
                "reward_a": r_a,
                "reward_b": r_b,
                "margin": margin,
            })
            if i % 250 == 0 or i == len(tasks):
                elapsed = time.time() - t0
                print(f"  Completed {i}/{len(tasks)} ({elapsed:.1f}s, {elapsed/i:.2f}s/match)...")

    margins = np.array([m["margin"] for m in results])
    rewards_a = np.array([m["reward_a"] for m in results])
    rewards_b = np.array([m["reward_b"] for m in results])

    ttest_p = float(stats.ttest_1samp(margins, 0.0).pvalue)
    try:
        wilcoxon_p = float(stats.wilcoxon(margins).pvalue)
    except Exception:
        wilcoxon_p = 1.0

    ci_low, ci_high = bootstrap_ci(margins)

    summary = {
        "agent_a": agent_a,
        "agent_b": agent_b,
        "total_matches": len(results),
        "mean_reward_a": float(np.mean(rewards_a)),
        "mean_reward_b": float(np.mean(rewards_b)),
        "mean_margin": float(np.mean(margins)),
        "median_margin": float(np.median(margins)),
        "sd_margin": float(np.std(margins)),
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

    print(f"Result {agent_a} vs {agent_b}:")
    print(
        f"  Mean Margin: {summary['mean_margin']:+.1f} | Median: {summary['median_margin']:+.1f} | "
        f"95% CI: [{summary['ci_95'][0]:+.1f}, {summary['ci_95'][1]:+.1f}] | "
        f"Win Rate: {summary['win_rate']:.1f}% ({summary['wins']}/{summary['losses']}/{summary['ties']}) | "
        f"p-val: {summary['ttest_p']:.4f}"
    )
    return summary

def main():
    # 500 completely fresh holdout seeds: 910,001 to 910,500
    seeds_holdout = list(range(910001, 910501))
    seeds_solo = list(range(920001, 920051)) # 50 fresh solo seeds

    print(f"=== LAUNCHING HOLDOUT GAUNTLET ({len(seeds_holdout)} seeds x 2 seats = 1,000 matches) ===")

    # 1. Direct paired Head-to-Head: Candidate vs Baseline V54++
    h2h = run_symmetric_matchup("V54_cand_agg_preempt", "V54++", seeds_holdout)

    # 2. Candidate vs V66
    cand_vs_v66 = run_symmetric_matchup("V54_cand_agg_preempt", "V66", seeds_holdout)

    # 3. Control: V54++ vs V66
    v54p_vs_v66 = run_symmetric_matchup("V54++", "V66", seeds_holdout)

    # 4. Candidate vs V54
    cand_vs_v54 = run_symmetric_matchup("V54_cand_agg_preempt", "V54", seeds_holdout)

    # 5. Solo benchmarks: Candidate vs IDLE and V54++ vs IDLE
    solo_cand = run_symmetric_matchup("V54_cand_agg_preempt", "IDLE", seeds_solo[:25])
    solo_v54p = run_symmetric_matchup("V54++", "IDLE", seeds_solo[:25])

    holdout_report = {
        "metadata": {
            "seeds_holdout": [seeds_holdout[0], seeds_holdout[-1]],
            "seeds_solo": [seeds_solo[0], seeds_solo[-1]],
            "num_holdout_seeds": len(seeds_holdout),
            "total_matches_per_matchup": len(seeds_holdout) * 2,
        },
        "h2h_candidate_vs_v54p": h2h,
        "candidate_vs_v66": cand_vs_v66,
        "v54p_vs_v66_control": v54p_vs_v66,
        "candidate_vs_v54": cand_vs_v54,
        "solo_candidate": solo_cand,
        "solo_v54p": solo_v54p,
    }

    out_file = os.path.join(BASE_DIR, "research", "residual_holdout_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(holdout_report, f, indent=2)
    print(f"\nHoldout report saved to {out_file}")

if __name__ == "__main__":
    main()
