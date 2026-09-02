# SPDX-License-Identifier: MIT
"""
Corrected 2x2 Causal Factorial Benchmark Suite:
Evaluating True Candidates A, B, C, D across 100 Paired Seeds (200 Symmetric Matches per Cell),
Against Anchor and in Direct Pairwise Head-to-Head Matches,
Using kaggle-environments 1.32.7.
"""

import os
import sys
import json
import time
import math
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments
from kaggle_environments import make

# Verify engine version
ENGINE_VERSION = kaggle_environments.__version__
assert ENGINE_VERSION == "1.32.7", f"Expected engine 1.32.7, got {ENGINE_VERSION}"

# 100 Deterministic Paired Seeds for 200 Matches per Cell (Symmetric P0 and P1)
SEEDS_DEV_100 = [
    1, 2, 3, 5, 7, 10, 11, 13, 17, 19,
    21, 23, 25, 29, 30, 31, 33, 37, 41, 42,
    43, 47, 50, 53, 59, 60, 61, 67, 71, 73,
    77, 79, 83, 88, 89, 97, 99, 101, 103, 107,
    109, 111, 113, 123, 127, 131, 137, 139, 149, 150,
    151, 153, 157, 159, 163, 167, 173, 179, 181, 191,
    193, 197, 199, 211, 223, 227, 229, 233, 239, 241,
    251, 257, 263, 269, 271, 277, 281, 283, 293, 307,
    311, 313, 317, 331, 337, 347, 349, 353, 359, 367,
    373, 379, 383, 389, 397, 401, 409, 419, 421, 431
]

def _run_single_match_worker(args):
    agent_a_path, agent_b_path, seed, seat = args
    agents = [agent_a_path, agent_b_path] if seat == 0 else [agent_b_path, agent_a_path]
    t0 = time.time()
    try:
        env = make("kaggriculture", configuration={"seed": seed})
        env.run(agents)
        elapsed = time.time() - t0
        
        cand_idx = seat
        opp_idx = 1 - seat
        cand_reward = float(env.steps[-1][cand_idx]["reward"] or 0)
        opp_reward = float(env.steps[-1][opp_idx]["reward"] or 0)
        margin = cand_reward - opp_reward
        
        cand_status = env.steps[-1][cand_idx].get("status", "DONE")
        opp_status = env.steps[-1][opp_idx].get("status", "DONE")
        
        # Check for invalid actions
        invalid_count = 0
        for step in env.steps:
            for p in (0, 1):
                if step[p].get("status") in ("INVALID", "ERROR"):
                    invalid_count += 1
        
        return {
            "seed": seed,
            "seat": f"P{seat}",
            "cand_reward": cand_reward,
            "opp_reward": opp_reward,
            "margin": margin,
            "is_win": margin > 0,
            "is_loss": margin < 0,
            "is_tie": margin == 0,
            "cand_status": cand_status,
            "opp_status": opp_status,
            "invalid_count": invalid_count,
            "elapsed": elapsed,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed,
            "seat": f"P{seat}",
            "cand_reward": 0.0,
            "opp_reward": 0.0,
            "margin": 0.0,
            "is_win": False,
            "is_loss": False,
            "is_tie": True,
            "cand_status": "ERROR",
            "opp_status": "ERROR",
            "invalid_count": 0,
            "elapsed": time.time() - t0,
            "error": str(e)
        }

def compute_percentile(sorted_list, p):
    if not sorted_list:
        return 0.0
    k = (len(sorted_list) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_list[int(k)]
    d0 = sorted_list[int(f)] * (c - k)
    d1 = sorted_list[int(c)] * (k - f)
    return d0 + d1

def run_cell_evaluation(pool, cand_path, opp_path, seeds, cand_name="Cand", opp_name="Opp"):
    work_items = [(cand_path, opp_path, seed, seat) for seed in seeds for seat in (0, 1)]
    matches = list(pool.map(_run_single_match_worker, work_items))
    
    total = len(matches)
    wins = sum(1 for m in matches if m["is_win"])
    losses = sum(1 for m in matches if m["is_loss"])
    ties = sum(1 for m in matches if m["is_tie"])
    win_rate = (wins / total) * 100.0 if total > 0 else 0.0
    
    margins = [m["margin"] for m in matches]
    mean_margin = sum(margins) / total if total > 0 else 0.0
    sorted_margins = sorted(margins)
    median_margin = compute_percentile(sorted_margins, 0.50)
    
    variance = sum((x - mean_margin) ** 2 for x in margins) / (total - 1) if total > 1 else 0.0
    std_dev = math.sqrt(variance)
    std_error = std_dev / math.sqrt(total) if total > 0 else 0.0
    ci95 = 1.96 * std_error
    
    p10 = compute_percentile(sorted_margins, 0.10)
    p25 = compute_percentile(sorted_margins, 0.25)
    p75 = compute_percentile(sorted_margins, 0.75)
    p90 = compute_percentile(sorted_margins, 0.90)
    min_margin = sorted_margins[0] if sorted_margins else 0.0
    max_margin = sorted_margins[-1] if sorted_margins else 0.0
    
    p0_matches = [m for m in matches if m["seat"] == "P0"]
    p1_matches = [m for m in matches if m["seat"] == "P1"]
    
    p0_wr = (sum(1 for m in p0_matches if m["is_win"]) / len(p0_matches)) * 100.0 if p0_matches else 0.0
    p1_wr = (sum(1 for m in p1_matches if m["is_win"]) / len(p1_matches)) * 100.0 if p1_matches else 0.0
    
    catastrophic = sum(1 for m in matches if m["margin"] < -10000)
    invalid_actions = sum(m["invalid_count"] for m in matches)
    exceptions = sum(1 for m in matches if m["cand_status"] != "DONE" or m["error"] is not None)
    avg_runtime = sum(m["elapsed"] for m in matches) / total if total > 0 else 0.0

    print(f"[{cand_name:24s} vs {opp_name:18s}] {wins:3d}W - {losses:3d}L - {ties:2d}T ({win_rate:5.1f}% WR) | Mean: {mean_margin:+8.1f} (±{ci95:5.1f}) | Median: {median_margin:+8.1f} | P0: {p0_wr:5.1f}% | P1: {p1_wr:5.1f}% | Worst: {min_margin:+8.1f}", flush=True)

    return {
        "candidate": cand_name,
        "opponent": opp_name,
        "games": total,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "mean_margin": mean_margin,
        "median_margin": median_margin,
        "std_dev": std_dev,
        "std_error": std_error,
        "ci95": ci95,
        "min_margin": min_margin,
        "max_margin": max_margin,
        "p10": p10,
        "p25": p25,
        "p75": p75,
        "p90": p90,
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "catastrophic_count": catastrophic,
        "invalid_action_count": invalid_actions,
        "exception_count": exceptions,
        "avg_runtime": avg_runtime,
        "matches": matches
    }

def main():
    print("=" * 100, flush=True)
    print(f"STARTING CORRECTED 2x2 CAUSAL FACTORIAL EXPERIMENT SUITE (ENGINE: {ENGINE_VERSION})")
    print(f"Evaluation: 100 Paired Seeds x 2 Seats = 200 Matches per Matchup")
    print("=" * 100, flush=True)

    candidates = {
        "Cell_A_Base": os.path.abspath("agents/candidate_a_aethel_v1.py"),
        "Cell_B_MC": os.path.abspath("agents/candidate_b_aethel_mc.py"),
        "Cell_C_T712": os.path.abspath("agents/candidate_c_aethel_t712.py"),
        "Cell_D_Refined": os.path.abspath("agents/candidate_d_aethel_refined.py"),
    }
    
    anchor_opp = os.path.abspath("replays/raw/reference_agents/closer_cleo.py")

    workers = min(16, os.cpu_count() or 4)
    print(f"Running across {len(SEEDS_DEV_100)} seeds ({len(SEEDS_DEV_100)*2} symmetric games per cell) with {workers} workers...\n", flush=True)

    results = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        print("--- 1. FACTORIAL CELLS VS IMMUTABLE AETHEL ANCHOR (Closer Cleo) ---", flush=True)
        for name, path in candidates.items():
            res = run_cell_evaluation(pool, path, anchor_opp, SEEDS_DEV_100, cand_name=name, opp_name="Aethel_Anchor")
            results[name] = res

        print("\n--- 2. DIRECT PAIRWISE HEAD-TO-HEAD MATCHUPS ---", flush=True)
        # B vs A: Direct Market Controller effect at T717
        results["H2H_B_vs_A"] = run_cell_evaluation(pool, candidates["Cell_B_MC"], candidates["Cell_A_Base"], SEEDS_DEV_100, cand_name="B_MC_Only", opp_name="A_Base")
        # C vs A: Direct Terminal 712 effect at MC=OFF
        results["H2H_C_vs_A"] = run_cell_evaluation(pool, candidates["Cell_C_T712"], candidates["Cell_A_Base"], SEEDS_DEV_100, cand_name="C_T712_Only", opp_name="A_Base")
        # D vs B: Direct Terminal 712 effect at MC=ON
        results["H2H_D_vs_B"] = run_cell_evaluation(pool, candidates["Cell_D_Refined"], candidates["Cell_B_MC"], SEEDS_DEV_100, cand_name="D_Refined", opp_name="B_MC")
        # D vs C: Direct Market Controller effect at T712
        results["H2H_D_vs_C"] = run_cell_evaluation(pool, candidates["Cell_D_Refined"], candidates["Cell_C_T712"], SEEDS_DEV_100, cand_name="D_Refined", opp_name="C_T712")
        # D vs A: Direct Combined effect
        results["H2H_D_vs_A"] = run_cell_evaluation(pool, candidates["Cell_D_Refined"], candidates["Cell_A_Base"], SEEDS_DEV_100, cand_name="D_Refined", opp_name="A_Base")

    # 3. Calculate Causal Decomposition
    # Against Anchor:
    mA = results["Cell_A_Base"]["mean_margin"]
    mB = results["Cell_B_MC"]["mean_margin"]
    mC = results["Cell_C_T712"]["mean_margin"]
    mD = results["Cell_D_Refined"]["mean_margin"]

    delta_m_anchor = mB - mA
    delta_t_anchor = mC - mA
    combined_anchor = mD - mA
    interaction_anchor = mD - mB - mC + mA

    # Direct Head-to-Head:
    h2h_delta_m_at_t717 = results["H2H_B_vs_A"]["mean_margin"]
    h2h_delta_t_at_mcoff = results["H2H_C_vs_A"]["mean_margin"]
    h2h_delta_t_at_mcon = results["H2H_D_vs_B"]["mean_margin"]
    h2h_delta_m_at_t712 = results["H2H_D_vs_C"]["mean_margin"]
    h2h_combined = results["H2H_D_vs_A"]["mean_margin"]
    h2h_interaction = h2h_delta_t_at_mcon - h2h_delta_t_at_mcoff

    print("\n" + "=" * 100, flush=True)
    print("CORRECTED 2x2 CAUSAL FACTORIAL DECOMPOSITION SUMMARY")
    print("=" * 100, flush=True)
    print("A. BENCHMARK AGAINST COMMON ANCHOR (Closer Cleo):")
    print(f"  Cell A (MC=OFF, T=717): Mean Margin: {mA:+8.2f} (±{results['Cell_A_Base']['ci95']:.1f}) | WR: {results['Cell_A_Base']['win_rate']:.1f}%")
    print(f"  Cell B (MC=ON,  T=717): Mean Margin: {mB:+8.2f} (±{results['Cell_B_MC']['ci95']:.1f}) | WR: {results['Cell_B_MC']['win_rate']:.1f}%")
    print(f"  Cell C (MC=OFF, T=712): Mean Margin: {mC:+8.2f} (±{results['Cell_C_T712']['ci95']:.1f}) | WR: {results['Cell_C_T712']['win_rate']:.1f}%")
    print(f"  Cell D (MC=ON,  T=712): Mean Margin: {mD:+8.2f} (±{results['Cell_D_Refined']['ci95']:.1f}) | WR: {results['Cell_D_Refined']['win_rate']:.1f}%")
    print("-" * 100)
    print(f"  Market Main Effect (Delta_M = B - A)          : {delta_m_anchor:+8.2f} coins")
    print(f"  Terminal Main Effect (Delta_T = C - A)        : {delta_t_anchor:+8.2f} coins")
    print(f"  Linear Sum (Delta_M + Delta_T)                : {delta_m_anchor + delta_t_anchor:+8.2f} coins")
    print(f"  Actual Combined (D - A)                       : {combined_anchor:+8.2f} coins")
    print(f"  Interaction Effect (D - B - C + A)            : {interaction_anchor:+8.2f} coins")
    print("\nB. DIRECT HEAD-TO-HEAD PAIRWISE MEASUREMENTS:")
    print(f"  Market Effect at T717 (B vs A)                : {h2h_delta_m_at_t717:+8.2f} coins | WR: {results['H2H_B_vs_A']['win_rate']:.1f}%")
    print(f"  Terminal Effect at MC=OFF (C vs A)            : {h2h_delta_t_at_mcoff:+8.2f} coins | WR: {results['H2H_C_vs_A']['win_rate']:.1f}%")
    print(f"  Terminal Effect at MC=ON (D vs B)             : {h2h_delta_t_at_mcon:+8.2f} coins | WR: {results['H2H_D_vs_B']['win_rate']:.1f}%")
    print(f"  Market Effect at T712 (D vs C)                : {h2h_delta_m_at_t712:+8.2f} coins | WR: {results['H2H_D_vs_C']['win_rate']:.1f}%")
    print(f"  Combined Effect (D vs A)                      : {h2h_combined:+8.2f} coins | WR: {results['H2H_D_vs_A']['win_rate']:.1f}%")
    print(f"  Head-to-Head Interaction (D - B - C + A)      : {h2h_interaction:+8.2f} coins")
    print("=" * 100, flush=True)

    summary_payload = {
        "engine_version": ENGINE_VERSION,
        "num_seeds": len(SEEDS_DEV_100),
        "total_games_per_cell": len(SEEDS_DEV_100) * 2,
        "seeds": SEEDS_DEV_100,
        "cells": results,
        "causal_decomposition": {
            "anchor_benchmark": {
                "margin_a": mA,
                "margin_b": mB,
                "margin_c": mC,
                "margin_d": mD,
                "delta_m": delta_m_anchor,
                "delta_t": delta_t_anchor,
                "combined": combined_anchor,
                "interaction": interaction_anchor
            },
            "direct_h2h": {
                "b_vs_a_delta_m_t717": h2h_delta_m_at_t717,
                "c_vs_a_delta_t_mcoff": h2h_delta_t_at_mcoff,
                "d_vs_b_delta_t_mcon": h2h_delta_t_at_mcon,
                "d_vs_c_delta_m_t712": h2h_delta_m_at_t712,
                "d_vs_a_combined": h2h_combined,
                "h2h_interaction": h2h_interaction
            }
        }
    }

    out_file = "scratch/corrected_causal_factorial_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    print(f"\nSaved complete corrected factorial results to {out_file}", flush=True)

if __name__ == "__main__":
    main()
