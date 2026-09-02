# SPDX-License-Identifier: MIT
"""
2x2 Causal Factorial Benchmark Suite:
Evaluating Candidates A, B, C, D across 100 Paired Matches per Cell (50 Seeds x Both Seats),
Calculating Main Effects, Interaction Effect, and Statistical Metrics.
"""

import os
import sys
import json
import time
import math
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

# 50 Paired Seeds for Rigorous 100-Game Evaluation per Cell
SEEDS_DEV = [
    1, 2, 3, 5, 7, 10, 11, 13, 17, 19,
    21, 23, 25, 29, 30, 31, 33, 37, 41, 42,
    43, 47, 50, 53, 59, 60, 61, 67, 71, 73,
    77, 79, 83, 88, 89, 97, 99, 101, 103, 107,
    109, 111, 113, 123, 127, 131, 137, 139, 149, 150
]

def _run_single_match_worker(args):
    agent_a_path, agent_b_path, seed, seat = args
    agents = [agent_a_path, agent_b_path] if seat == 0 else [agent_b_path, agent_a_path]
    t0 = time.time()
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
        "elapsed": elapsed
    }

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
    median_margin = sorted_margins[total // 2] if total > 0 else 0.0
    
    variance = sum((x - mean_margin) ** 2 for x in margins) / total if total > 0 else 0.0
    std_dev = math.sqrt(variance)
    
    p0_matches = [m for m in matches if m["seat"] == "P0"]
    p1_matches = [m for m in matches if m["seat"] == "P1"]
    
    p0_wr = (sum(1 for m in p0_matches if m["is_win"]) / len(p0_matches)) * 100.0 if p0_matches else 0.0
    p1_wr = (sum(1 for m in p1_matches if m["is_win"]) / len(p1_matches)) * 100.0 if p1_matches else 0.0
    
    worst_loss = min(margins) if margins else 0.0
    catastrophic = sum(1 for m in matches if m["margin"] < -10000)
    crashes = sum(1 for m in matches if m["cand_status"] != "DONE")
    avg_runtime = sum(m["elapsed"] for m in matches) / total if total > 0 else 0.0

    print(f"[{cand_name:28s} vs {opp_name:15s}] {wins:3d}W - {losses:3d}L - {ties:2d}T ({win_rate:5.1f}% WR) | Mean Margin: {mean_margin:+8.1f} | Median: {median_margin:+8.1f} | P0: {p0_wr:5.1f}% | P1: {p1_wr:5.1f}% | Worst: {worst_loss:+8.1f}", flush=True)

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
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "worst_loss": worst_loss,
        "catastrophic_count": catastrophic,
        "crashes": crashes,
        "avg_runtime": avg_runtime,
        "matches": matches
    }

def main():
    print("=" * 100, flush=True)
    print("STARTING 2x2 CAUSAL FACTORIAL EXPERIMENT SUITE (100 MATCHES PER CELL)", flush=True)
    print("=" * 100, flush=True)

    candidates = {
        "A_Aethel_V1": os.path.abspath("agents/candidate_a_aethel_v1.py"),
        "B_Aethel_MC": os.path.abspath("agents/candidate_b_aethel_mc.py"),
        "C_Aethel_T712": os.path.abspath("agents/candidate_c_aethel_t712.py"),
        "D_Aethel_Refined": os.path.abspath("agents/candidate_d_aethel_refined.py"),
    }
    
    anchor_opp = os.path.abspath("replays/raw/reference_agents/closer_cleo.py")

    workers = min(16, os.cpu_count() or 4)
    print(f"Running across {len(SEEDS_DEV)} paired seeds (100 symmetric matches per cell) with {workers} parallel processes...\n", flush=True)

    factorial_results = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for name, path in candidates.items():
            res = run_cell_evaluation(pool, path, anchor_opp, SEEDS_DEV, cand_name=name, opp_name="Aethel_Anchor")
            factorial_results[name] = res

        # Also run direct head-to-head D vs A, D vs B, D vs C
        print("\n--- Direct Head-to-Head Cross-Validations ---", flush=True)
        h2h_d_vs_a = run_cell_evaluation(pool, candidates["D_Aethel_Refined"], candidates["A_Aethel_V1"], SEEDS_DEV, cand_name="D_Aethel_Refined", opp_name="A_Aethel_V1")
        h2h_d_vs_b = run_cell_evaluation(pool, candidates["D_Aethel_Refined"], candidates["B_Aethel_MC"], SEEDS_DEV, cand_name="D_Aethel_Refined", opp_name="B_Aethel_MC")
        h2h_d_vs_c = run_cell_evaluation(pool, candidates["D_Aethel_Refined"], candidates["C_Aethel_T712"], SEEDS_DEV, cand_name="D_Aethel_Refined", opp_name="C_Aethel_T712")
        factorial_results["H2H_D_vs_A"] = h2h_d_vs_a
        factorial_results["H2H_D_vs_B"] = h2h_d_vs_b
        factorial_results["H2H_D_vs_C"] = h2h_d_vs_c

    # Calculate 2x2 Factorial Causal Attribution Metrics
    margin_a = factorial_results["A_Aethel_V1"]["mean_margin"]
    margin_b = factorial_results["B_Aethel_MC"]["mean_margin"]
    margin_c = factorial_results["C_Aethel_T712"]["mean_margin"]
    margin_d = factorial_results["D_Aethel_Refined"]["mean_margin"]

    delta_mc = margin_b - margin_a
    delta_t712 = margin_c - margin_a
    interaction = (margin_d - margin_a) - (delta_mc + delta_t712)

    print("\n" + "=" * 100, flush=True)
    print("2x2 CAUSAL FACTORIAL ATTRIBUTION SUMMARY", flush=True)
    print("=" * 100, flush=True)
    print(f"Cell A (Baseline Aethel V1)           Mean Margin: {margin_a:+8.2f} coins | WR: {factorial_results['A_Aethel_V1']['win_rate']:.1f}%")
    print(f"Cell B (Aethel + Market Controller)   Mean Margin: {margin_b:+8.2f} coins | WR: {factorial_results['B_Aethel_MC']['win_rate']:.1f}%")
    print(f"Cell C (Aethel + Step-712 Terminal)   Mean Margin: {margin_c:+8.2f} coins | WR: {factorial_results['C_Aethel_T712']['win_rate']:.1f}%")
    print(f"Cell D (Aethel-Refined Synthesis)     Mean Margin: {margin_d:+8.2f} coins | WR: {factorial_results['D_Aethel_Refined']['win_rate']:.1f}%")
    print("-" * 100, flush=True)
    print(f"Main Effect of Market Controller (delta_M)  : {delta_mc:+8.2f} coins")
    print(f"Main Effect of Step-712 Terminal (delta_T)  : {delta_t712:+8.2f} coins")
    print(f"Linear Additive Expectation (delta_M+delta_T): {delta_mc + delta_t712:+8.2f} coins")
    print(f"Actual Combined Effect (D - A)              : {margin_d - margin_a:+8.2f} coins")
    print(f"Interaction Effect (I = Actual - Linear)    : {interaction:+8.2f} coins", flush=True)
    
    if abs(interaction) <= 50:
        synergy_verdict = "STRICTLY ADDITIVE (No interference)"
    elif interaction > 50:
        synergy_verdict = "POSITIVE SYNERGY (Super-additive)"
    else:
        synergy_verdict = "SUB-ADDITIVE (Mild interference)"
    print(f"Causal Synergy Classification               : {synergy_verdict}")
    print("=" * 100, flush=True)

    summary_payload = {
        "factorial_cells": factorial_results,
        "causal_attribution": {
            "margin_a": margin_a,
            "margin_b": margin_b,
            "margin_c": margin_c,
            "margin_d": margin_d,
            "delta_mc": delta_mc,
            "delta_t712": delta_t712,
            "interaction_effect": interaction,
            "synergy_verdict": synergy_verdict
        }
    }
    
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/causal_factorial_100games_results.json", "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    print("\nSaved full 100-match factorial results to scratch/causal_factorial_100games_results.json", flush=True)

if __name__ == "__main__":
    main()
