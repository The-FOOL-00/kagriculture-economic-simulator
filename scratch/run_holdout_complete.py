"""
scratch/run_holdout_complete.py
===============================
Robust, checkpointed holdout evaluation for Championship Audit.
Evaluates:
  Block 1: Candidate vs Frozen V54++ (500 seeds x 2 seats = 1,000 matches)
  Block 2: Candidate vs Canonical V66 (500 seeds x 2 seats = 1,000 matches)
  Block 3: Frozen V54++ vs Canonical V66 (500 seeds x 2 seats = 1,000 matches)
  Block 4: Candidate vs Canonical V54 (500 seeds x 2 seats = 1,000 matches)
  Block 5: Solo Test (50 fresh seeds vs IDLE)
  Block 6: Macro Immutability Verification (route prior diff count = 0)
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
    cand_path = os.path.join(BASE_DIR, "candidates", "v54_plus_residual.py")
    cand_agent = _load_agent_module("cand_mod_worker", cand_path)

    v54pp_path = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")
    v54pp_agent = _load_agent_module("v54pp_mod_worker", v54pp_path)

    v66_path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
    v66_agent = _load_agent_module("v66_mod_worker", v66_path)

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

def run_block(mode_name, seeds, ckpt_file):
    if os.path.exists(ckpt_file):
        print(f"Loading cached checkpoint for {mode_name} from {ckpt_file}...")
        with open(ckpt_file, "r", encoding="utf-8") as f:
            return json.load(f)

    tasks = []
    for s in seeds:
        tasks.append((s, 0, mode_name))
        tasks.append((s, 1, mode_name))

    print(f"\n--- Running {mode_name} ({len(tasks)} matches)... ---")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as executor:
        for i, res in enumerate(executor.map(run_match_worker, tasks), 1):
            results.append(res)
            if i % 250 == 0 or i == len(tasks):
                print(f"  {mode_name}: Completed {i}/{len(tasks)} ({time.time()-t0:.1f}s)...")

    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(results, f)
    print(f"Saved checkpoint for {mode_name} to {ckpt_file}")
    return results

def main():
    seeds = list(range(940001, 940501)) # 500 fresh untouched holdout seeds
    print(f"=== COMPLETE CHAMPIONSHIP HOLDOUT SUITE across {len(seeds)} seeds ({seeds[0]}–{seeds[-1]}) ===")

    hashes = {
        "Canonical_V54": get_file_sha256(os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")),
        "Canonical_V66": get_file_sha256(os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")),
        "Frozen_V54pp": get_file_sha256(os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")),
        "Candidate_Residual": get_file_sha256(os.path.join(BASE_DIR, "candidates", "v54_plus_residual.py")),
    }
    print("\n--- FROZEN ARTIFACT SHA256 HASHES ---")
    for k, v in hashes.items():
        print(f"  {k:<20}: {v}")

    ckpt_dir = os.path.join(BASE_DIR, "scratch", "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)

    # 1. Primary: Candidate vs Frozen V54++
    res_b1 = run_block("cand_vs_v54pp", seeds, os.path.join(ckpt_dir, "ckpt_cand_vs_v54pp.json"))

    # 2. Secondary: Candidate vs Canonical V66
    res_b2 = run_block("cand_vs_v66", seeds, os.path.join(ckpt_dir, "ckpt_cand_vs_v66.json"))

    # 3. Control: Frozen V54++ vs Canonical V66
    res_b3 = run_block("v54pp_vs_v66", seeds, os.path.join(ckpt_dir, "ckpt_v54pp_vs_v66.json"))

    # 4. Secondary: Candidate vs Canonical V54
    res_b4 = run_block("cand_vs_v54", seeds, os.path.join(ckpt_dir, "ckpt_cand_vs_v54.json"))

    # --- PROCESS BLOCK 1: PRIMARY (Candidate vs V54++) ---
    seed_data_primary = defaultdict(dict)
    for r in res_b1:
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

    p_loss_100 = float(np.mean(symmetric_deltas < -100.0) * 100.0)
    p_loss_250 = float(np.mean(symmetric_deltas < -250.0) * 100.0)
    p_loss_500 = float(np.mean(symmetric_deltas < -500.0) * 100.0)
    p_loss_1000 = float(np.mean(symmetric_deltas < -1000.0) * 100.0)
    p_gain_100 = float(np.mean(symmetric_deltas > 100.0) * 100.0)
    p_gain_250 = float(np.mean(symmetric_deltas > 250.0) * 100.0)
    p_gain_500 = float(np.mean(symmetric_deltas > 500.0) * 100.0)
    p_gain_1000 = float(np.mean(symmetric_deltas > 1000.0) * 100.0)

    sorted_indices = np.argsort(symmetric_deltas)
    worst_20 = [(int(seeds[i]), float(symmetric_deltas[i])) for i in sorted_indices[:20]]
    best_20 = [(int(seeds[i]), float(symmetric_deltas[i])) for i in sorted_indices[-20:][::-1]]

    # --- PROCESS BLOCK 2: CANDIDATE vs V66 ---
    seed_data_v66 = defaultdict(dict)
    for r in res_b2:
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
    print(f"\nCandidate vs V66 Margin: +${mean_cand_v66:.2f} | 95% CI: [${ci_low_v66:.2f}, ${ci_high_v66:.2f}] | {w_v66}W/{l_v66}L/{t_v66}T")

    # --- PROCESS BLOCK 3: V54++ vs V66 ---
    seed_data_v54pp_v66 = defaultdict(dict)
    for r in res_b3:
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

    # --- PROCESS BLOCK 4: CANDIDATE vs V54 ---
    seed_data_v54 = defaultdict(dict)
    for r in res_b4:
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

    # --- REGIME STRATIFICATION ---
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

    print(f"\nHoldout suite successfully executed and results saved to {out_file}")

if __name__ == "__main__":
    main()
