"""
scratch/run_true_untouched_holdout.py
=====================================
Championship Experiment: True Untouched Symmetric Holdout (1,000 matches per comparison).
Evaluates Frozen V54++ vs Frozen Residual Candidate (candidates/v54_plus_residual.py),
as well as Canonical V66 and Canonical V54 across 500 fresh seeds (940,001 to 940,500)
with 2 seat swaps per seed (Seat 0 and Seat 1).
"""

import os
import sys
import copy
import json
import time
import hashlib
import numpy as np
from scipy import stats
from collections import defaultdict
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

# Global cache for worker processes
_WORKER_AGENTS = {}

def get_file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def _load_agent_module(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", getattr(mod, "kaggle_agent", None))

def worker_init():
    global _WORKER_AGENTS
    # Load candidate
    cand_path = os.path.join(BASE_DIR, "candidates", "v54_plus_residual.py")
    cand_agent = _load_agent_module("cand_mod_worker", cand_path)

    # Load V54++
    v54pp_path = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")
    v54pp_agent = _load_agent_module("v54pp_mod_worker", v54pp_path)

    # Load V66
    v66_path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
    v66_agent = _load_agent_module("v66_mod_worker", v66_path)

    # Load V54
    v54_path = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
    v54_agent = _load_agent_module("v54_mod_worker", v54_path)

    _WORKER_AGENTS = {
        "cand": cand_agent,
        "v54pp": v54pp_agent,
        "v66": v66_agent,
        "v54": v54_agent,
    }

def run_match_worker(args):
    global _WORKER_AGENTS
    if not _WORKER_AGENTS:
        worker_init()

    seed, seat_cand, mode = args
    if mode == "cand_vs_v54pp":
        agent_names = ("cand", "v54pp") if seat_cand == 0 else ("v54pp", "cand")
    elif mode == "cand_vs_v66":
        agent_names = ("cand", "v66") if seat_cand == 0 else ("v66", "cand")
    elif mode == "v54pp_vs_v66":
        agent_names = ("v54pp", "v66") if seat_cand == 0 else ("v66", "v54pp")
    elif mode == "cand_vs_v54":
        agent_names = ("cand", "v54") if seat_cand == 0 else ("v54", "cand")
    else:
        raise ValueError(f"Unknown mode: {mode}")

    a0_fn = _WORKER_AGENTS[agent_names[0]]
    a1_fn = _WORKER_AGENTS[agent_names[1]]

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    cand_seat = 0 if agent_names[0] == "cand" else (1 if agent_names[1] == "cand" else -1)

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        act0 = a0_fn(o0)
        act1 = a1_fn(o1)
        env.step([act0, act1])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    cand_reward = r0 if cand_seat == 0 else (r1 if cand_seat == 1 else None)
    opp_reward = r1 if cand_seat == 0 else (r0 if cand_seat == 1 else None)

    return {
        "seed": seed,
        "seat_cand": seat_cand,
        "mode": mode,
        "r0": r0,
        "r1": r1,
        "cand_reward": cand_reward,
        "opp_reward": opp_reward,
    }

def bootstrap_ci(arr, n_boot=5000, ci=0.95):
    if len(arr) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(42)
    boot = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return (float(np.percentile(boot, alpha * 100)), float(np.percentile(boot, (1.0 - alpha) * 100)))

def main():
    seeds = list(range(940001, 940501)) # 500 fresh untouched holdout seeds
    print(f"=== TRUE UNTOUCHED SYMMETRIC HOLDOUT: 500 seeds x 2 seats = 1,000 matches per comparison ===")
    print(f"Seeds: {seeds[0]} to {seeds[-1]}")

    # Freeze Hashes
    hashes = {
        "Canonical_V54": get_file_sha256(os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")),
        "Canonical_V66": get_file_sha256(os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")),
        "Frozen_V54pp": get_file_sha256(os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")),
        "Candidate_Residual": get_file_sha256(os.path.join(BASE_DIR, "candidates", "v54_plus_residual.py")),
    }
    print("\n--- FROZEN ARTIFACT SHA256 HASHES ---")
    for k, v in hashes.items():
        print(f"  {k:<20}: {v}")

    # 1. PRIMARY COMPARISON: Candidate vs Frozen V54++ (1,000 matches)
    tasks_primary = []
    for s in seeds:
        tasks_primary.append((s, 0, "cand_vs_v54pp"))
        tasks_primary.append((s, 1, "cand_vs_v54pp"))

    print(f"\n[1/4] Running Primary Comparison: Candidate vs Frozen V54++ ({len(tasks_primary)} matches)...")
    t0 = time.time()
    results_primary = []
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as executor:
        for i, res in enumerate(executor.map(run_match_worker, tasks_primary), 1):
            results_primary.append(res)
            if i % 250 == 0 or i == len(tasks_primary):
                print(f"  Completed {i}/{len(tasks_primary)} ({time.time()-t0:.1f}s)...")

    seed_data_primary = defaultdict(dict)
    for r in results_primary:
        seed_data_primary[r["seed"]][r["seat_cand"]] = r

    cand_rewards, v54pp_rewards, symmetric_deltas = [], [], []
    for s in seeds:
        m0 = seed_data_primary[s][0]
        m1 = seed_data_primary[s][1]
        delta_sym = 0.5 * ((m0["r0"] - m0["r1"]) + (m1["r1"] - m1["r0"]))
        c_mean = 0.5 * (m0["r0"] + m1["r1"])
        v_mean = 0.5 * (m0["r1"] + m1["r0"])
        cand_rewards.append(c_mean)
        v54pp_rewards.append(v_mean)
        symmetric_deltas.append(delta_sym)

    cand_rewards = np.array(cand_rewards)
    v54pp_rewards = np.array(v54pp_rewards)
    symmetric_deltas = np.array(symmetric_deltas)

    mean_delta = float(np.mean(symmetric_deltas))
    median_delta = float(np.median(symmetric_deltas))
    std_delta = float(np.std(symmetric_deltas, ddof=1))
    ci_low, ci_high = bootstrap_ci(symmetric_deltas)
    t_stat, p_val_t = stats.ttest_1samp(symmetric_deltas, 0.0)
    diff_nonzero = symmetric_deltas[symmetric_deltas != 0]
    w_stat, p_val_w = stats.wilcoxon(diff_nonzero) if len(diff_nonzero) > 0 else (0.0, 1.0)

    wins = int(np.sum(symmetric_deltas > 0))
    losses = int(np.sum(symmetric_deltas < 0))
    ties = int(np.sum(symmetric_deltas == 0))

    quantiles = {
        "p05": float(np.percentile(symmetric_deltas, 5)),
        "p25": float(np.percentile(symmetric_deltas, 25)),
        "p50": float(np.percentile(symmetric_deltas, 50)),
        "p75": float(np.percentile(symmetric_deltas, 75)),
        "p95": float(np.percentile(symmetric_deltas, 95)),
    }

    print("\n=======================================================")
    print("PRIMARY SUCCESS METRICS (Candidate vs Frozen V54++)")
    print("=======================================================")
    print(f"Mean Paired Delta : +${mean_delta:.2f}")
    print(f"Median Delta      : +${median_delta:.2f}")
    print(f"Sample Std Dev    : ${std_delta:.2f}")
    print(f"95% Bootstrap CI  : [${ci_low:.2f}, ${ci_high:.2f}]")
    print(f"W / L / T         : {wins} W / {losses} L / {ties} T (Win Rate: {wins/len(seeds)*100:.1f}%)")
    print(f"Paired t-test     : t = {t_stat:.3f}, p = {p_val_t:.4e}")
    print(f"Wilcoxon test     : W = {w_stat:.1f}, p = {p_val_w:.4e}")
    print(f"Quantiles (p05/25/50/75/95): {quantiles['p05']:.1f} / {quantiles['p25']:.1f} / {quantiles['p50']:.1f} / {quantiles['p75']:.1f} / {quantiles['p95']:.1f}")

    # Tail-Risk Metrics
    p_loss_100 = float(np.mean(symmetric_deltas < -100.0) * 100.0)
    p_loss_250 = float(np.mean(symmetric_deltas < -250.0) * 100.0)
    p_loss_500 = float(np.mean(symmetric_deltas < -500.0) * 100.0)
    p_loss_1000 = float(np.mean(symmetric_deltas < -1000.0) * 100.0)
    p_gain_100 = float(np.mean(symmetric_deltas > 100.0) * 100.0)
    p_gain_250 = float(np.mean(symmetric_deltas > 250.0) * 100.0)
    p_gain_500 = float(np.mean(symmetric_deltas > 500.0) * 100.0)
    p_gain_1000 = float(np.mean(symmetric_deltas > 1000.0) * 100.0)

    print("\n--- TAIL-RISK ANALYSIS ---")
    print(f"P(delta < -$100) : {p_loss_100:.1f}%   | P(delta > +$100) : {p_gain_100:.1f}%")
    print(f"P(delta < -$250) : {p_loss_250:.1f}%   | P(delta > +$250) : {p_gain_250:.1f}%")
    print(f"P(delta < -$500) : {p_loss_500:.1f}%   | P(delta > +$500) : {p_gain_500:.1f}%")
    print(f"P(delta < -$1000): {p_loss_1000:.1f}%   | P(delta > +$1000): {p_gain_1000:.1f}%")

    sorted_indices = np.argsort(symmetric_deltas)
    worst_20 = [(int(seeds[i]), float(symmetric_deltas[i])) for i in sorted_indices[:20]]
    best_20 = [(int(seeds[i]), float(symmetric_deltas[i])) for i in sorted_indices[-20:][::-1]]

    # 2. SECONDARY: Candidate vs Canonical V66 (1,000 matches)
    tasks_v66 = []
    for s in seeds:
        tasks_v66.append((s, 0, "cand_vs_v66"))
        tasks_v66.append((s, 1, "cand_vs_v66"))

    print(f"\n[2/4] Running Secondary Comparison: Candidate vs Canonical V66 ({len(tasks_v66)} matches)...")
    t0 = time.time()
    results_v66 = []
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as executor:
        for i, res in enumerate(executor.map(run_match_worker, tasks_v66), 1):
            results_v66.append(res)
            if i % 250 == 0 or i == len(tasks_v66):
                print(f"  Completed {i}/{len(tasks_v66)} ({time.time()-t0:.1f}s)...")

    seed_data_v66 = defaultdict(dict)
    for r in results_v66:
        seed_data_v66[r["seed"]][r["seat_cand"]] = r

    cand_v66_margins = []
    for s in seeds:
        m0 = seed_data_v66[s][0]
        m1 = seed_data_v66[s][1]
        sym_margin = 0.5 * ((m0["r0"] - m0["r1"]) + (m1["r1"] - m1["r0"]))
        cand_v66_margins.append(sym_margin)
    cand_v66_margins = np.array(cand_v66_margins)
    mean_cand_v66 = float(np.mean(cand_v66_margins))
    ci_low_v66, ci_high_v66 = bootstrap_ci(cand_v66_margins)
    w_v66 = int(np.sum(cand_v66_margins > 0))
    l_v66 = int(np.sum(cand_v66_margins < 0))
    t_v66 = int(np.sum(cand_v66_margins == 0))

    print(f"Candidate vs V66 Margin: +${mean_cand_v66:.2f} | 95% CI: [${ci_low_v66:.2f}, ${ci_high_v66:.2f}] | {w_v66}W/{l_v66}L/{t_v66}T")

    # 3. CONTROL: V54++ vs Canonical V66 (1,000 matches)
    tasks_v54pp_v66 = []
    for s in seeds:
        tasks_v54pp_v66.append((s, 0, "v54pp_vs_v66"))
        tasks_v54pp_v66.append((s, 1, "v54pp_vs_v66"))

    print(f"\n[3/4] Running Benchmark Control: V54++ vs Canonical V66 ({len(tasks_v54pp_v66)} matches)...")
    t0 = time.time()
    results_v54pp_v66 = []
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as executor:
        for i, res in enumerate(executor.map(run_match_worker, tasks_v54pp_v66), 1):
            results_v54pp_v66.append(res)
            if i % 250 == 0 or i == len(tasks_v54pp_v66):
                print(f"  Completed {i}/{len(tasks_v54pp_v66)} ({time.time()-t0:.1f}s)...")

    seed_data_v54pp_v66 = defaultdict(dict)
    for r in results_v54pp_v66:
        seed_data_v54pp_v66[r["seed"]][r["seat_cand"]] = r

    v54pp_v66_margins = []
    for s in seeds:
        m0 = seed_data_v54pp_v66[s][0]
        m1 = seed_data_v54pp_v66[s][1]
        sym_margin = 0.5 * ((m0["r0"] - m0["r1"]) + (m1["r1"] - m1["r0"]))
        v54pp_v66_margins.append(sym_margin)
    v54pp_v66_margins = np.array(v54pp_v66_margins)
    mean_v54pp_v66 = float(np.mean(v54pp_v66_margins))
    ci_low_v54pp, ci_high_v54pp = bootstrap_ci(v54pp_v66_margins)
    w_v54pp = int(np.sum(v54pp_v66_margins > 0))
    l_v54pp = int(np.sum(v54pp_v66_margins < 0))
    t_v54pp = int(np.sum(v54pp_v66_margins == 0))

    print(f"V54++ vs V66 Margin    : +${mean_v54pp_v66:.2f} | 95% CI: [${ci_low_v54pp:.2f}, ${ci_high_v54pp:.2f}] | {w_v54pp}W/{l_v54pp}L/{t_v54pp}T")

    # 4. SECONDARY: Candidate vs Canonical V54 (1,000 matches)
    tasks_v54 = []
    for s in seeds:
        tasks_v54.append((s, 0, "cand_vs_v54"))
        tasks_v54.append((s, 1, "cand_vs_v54"))

    print(f"\n[4/4] Running Secondary Comparison: Candidate vs Canonical V54 ({len(tasks_v54)} matches)...")
    t0 = time.time()
    results_v54 = []
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as executor:
        for i, res in enumerate(executor.map(run_match_worker, tasks_v54), 1):
            results_v54.append(res)
            if i % 250 == 0 or i == len(tasks_v54):
                print(f"  Completed {i}/{len(tasks_v54)} ({time.time()-t0:.1f}s)...")

    seed_data_v54 = defaultdict(dict)
    for r in results_v54:
        seed_data_v54[r["seed"]][r["seat_cand"]] = r

    cand_v54_margins = []
    for s in seeds:
        m0 = seed_data_v54[s][0]
        m1 = seed_data_v54[s][1]
        sym_margin = 0.5 * ((m0["r0"] - m0["r1"]) + (m1["r1"] - m1["r0"]))
        cand_v54_margins.append(sym_margin)
    cand_v54_margins = np.array(cand_v54_margins)
    mean_cand_v54 = float(np.mean(cand_v54_margins))
    ci_low_v54, ci_high_v54 = bootstrap_ci(cand_v54_margins)
    w_v54 = int(np.sum(cand_v54_margins > 0))
    l_v54 = int(np.sum(cand_v54_margins < 0))
    t_v54 = int(np.sum(cand_v54_margins == 0))

    print(f"Candidate vs V54 Margin: +${mean_cand_v54:.2f} | 95% CI: [${ci_low_v54:.2f}, ${ci_high_v54:.2f}] | {w_v54}W/{l_v54}L/{t_v54}T")

    # Regime Analysis: Low, Medium, High reward
    p33 = np.percentile(v54pp_rewards, 33.33)
    p66 = np.percentile(v54pp_rewards, 66.67)

    low_mask = v54pp_rewards <= p33
    med_mask = (v54pp_rewards > p33) & (v54pp_rewards <= p66)
    high_mask = v54pp_rewards > p66

    def regime_stats(mask, name):
        d = symmetric_deltas[mask]
        ci_l, ci_h = bootstrap_ci(d)
        return {
            "regime": name,
            "count": int(np.sum(mask)),
            "mean_delta": float(np.mean(d)),
            "median_delta": float(np.median(d)),
            "ci_95": [ci_l, ci_h],
            "win_rate": float(np.mean(d > 0) * 100.0),
        }

    regimes = [
        regime_stats(low_mask, "Low Reward (0-33%)"),
        regime_stats(med_mask, "Medium Reward (33-66%)"),
        regime_stats(high_mask, "High Reward (66-100%)"),
    ]

    print("\n--- PERFORMANCE BY SEED REGIME ---")
    for r in regimes:
        print(f"  {r['regime']:<25}: Mean Delta +${r['mean_delta']:6.2f} | 95% CI [{r['ci_95'][0]:6.2f}, {r['ci_95'][1]:6.2f}] | Win Rate {r['win_rate']:5.1f}%")

    out_file = os.path.join(BASE_DIR, "research", "residual_true_untouched_holdout_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "seeds": [seeds[0], seeds[-1]],
            "num_seeds": len(seeds),
            "matches_per_comparison": len(seeds) * 2,
            "hashes": hashes,
            "primary_vs_v54pp": {
                "mean_delta": mean_delta,
                "median_delta": median_delta,
                "std_delta": std_delta,
                "ci_95": [ci_low, ci_high],
                "quantiles": quantiles,
                "w_l_t": [wins, losses, ties],
                "p_val_ttest": p_val_t,
                "p_val_wilcoxon": p_val_w,
                "tail_risk": {
                    "p_loss_100": p_loss_100,
                    "p_loss_250": p_loss_250,
                    "p_loss_500": p_loss_500,
                    "p_loss_1000": p_loss_1000,
                    "p_gain_100": p_gain_100,
                    "p_gain_250": p_gain_250,
                    "p_gain_500": p_gain_500,
                    "p_gain_1000": p_gain_1000,
                },
                "worst_20": worst_20,
                "best_20": best_20,
            },
            "candidate_vs_v66": {
                "mean_margin": mean_cand_v66,
                "ci_95": [ci_low_v66, ci_high_v66],
                "w_l_t": [w_v66, l_v66, t_v66],
            },
            "v54pp_vs_v66": {
                "mean_margin": mean_v54pp_v66,
                "ci_95": [ci_low_v54pp, ci_high_v54pp],
                "w_l_t": [w_v54pp, l_v54pp, t_v54pp],
            },
            "candidate_vs_v54": {
                "mean_margin": mean_cand_v54,
                "ci_95": [ci_low_v54, ci_high_v54],
                "w_l_t": [w_v54, l_v54, t_v54],
            },
            "regime_analysis": regimes,
        }, f, indent=2)

    print(f"\nAll holdout results successfully saved to {out_file}")

if __name__ == "__main__":
    main()
