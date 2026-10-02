import concurrent.futures
import csv
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod
import candidates.v44_economic_portfolio.main as v44_mod
from research.final_synthesis.teammates.v24.main import agent as v24_agent
from research.final_synthesis.teammates.v27.main import agent as v27_agent
import research.final_synthesis.final_candidate.main as final_cand_mod

CANDIDATE_AGENT = final_cand_mod.agent

FRESH_SEEDS = [250600 + i for i in range(32)]
OPPONENTS = [
    "V49",
    "V24",
    "V27",
    "V48",
    "V44",
    "dmitrii_lb2800",
    "tetsutani_pasture",
    "kaitofukami_v48_3009",
    "indarkarhana_top10",
    "saiteja_mega_3000",
]

# Preload all agents once in main thread
PRELOADED_AGENTS = {}
print("Pre-loading all 10 agents in main thread...")
for opp in OPPONENTS:
    if opp == "V49": PRELOADED_AGENTS[opp] = v49_mod.agent
    elif opp == "V24": PRELOADED_AGENTS[opp] = v24_agent
    elif opp == "V27": PRELOADED_AGENTS[opp] = v27_agent
    elif opp == "V48": PRELOADED_AGENTS[opp] = v48_mod.agent
    elif opp == "V44": PRELOADED_AGENTS[opp] = v44_mod.agent
    else:
        PRELOADED_AGENTS[opp] = load_elite_agent(opp)
    print(f"  Loaded {opp} successfully.")

def run_single_leg(task: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, opp_name = task
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    cand = CANDIDATE_AGENT
    opp = PRELOADED_AGENTS[opp_name]

    for step in range(719):
        a_cand = cand(obs[seat])
        a_opp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    cash_cand = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    delta = cash_cand - cash_opp
    win = cash_cand > cash_opp
    loss = cash_cand < cash_opp
    tie = cash_cand == cash_opp

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "cash_cand": cash_cand,
        "cash_opp": cash_opp,
        "delta": delta,
        "win": win,
        "loss": loss,
        "tie": tie,
    }

def main():
    print("=" * 80)
    print("FINAL META-SYNTHESIS: FULL BENCHMARK MATRIX (640 LEGS)")
    print(f"Candidate: research/final_synthesis/final_candidate/main.py")
    print(f"Opponents: {len(OPPONENTS)} opponents x 32 seeds x 2 seats = {len(OPPONENTS)*32*2} total legs")
    print("=" * 80)

    tasks = [(s, seat, opp) for opp in OPPONENTS for s in FRESH_SEEDS for seat in (0, 1)]
    
    t0 = time.time()
    results_by_opp = {opp: [] for opp in OPPONENTS}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(run_single_leg, t): t for t in tasks}
        completed = 0
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            results_by_opp[res["opp"]].append(res)
            completed += 1
            if completed % 64 == 0 or completed == len(tasks):
                print(f"Progress: {completed}/{len(tasks)} legs completed ({time.time() - t0:.1f}s)...")

    elapsed = time.time() - t0
    print(f"\nAll {len(tasks)} legs finished in {elapsed:.1f}s ({len(tasks)/elapsed:.1f} legs/s)!\n")

    summary_rows = []
    print(f"{'Opponent':22s} | {'Legs':5s} | {'Wins':5s} | {'Losses':6s} | {'Ties':4s} | {'WinRate%':8s} | {'MeanDelta':10s} | {'MedDelta':10s} | {'Casualties':10s}")
    print("-" * 95)

    total_wins = total_losses = total_ties = 0

    for opp in OPPONENTS:
        legs = results_by_opp[opp]
        n_legs = len(legs)
        wins = sum(1 for r in legs if r["win"])
        losses = sum(1 for r in legs if r["loss"])
        ties = sum(1 for r in legs if r["tie"])
        wr = 100.0 * wins / n_legs
        deltas = [r["delta"] for r in legs]
        mean_d = float(np.mean(deltas))
        med_d = float(np.median(deltas))
        casualties = 0

        total_wins += wins
        total_losses += losses
        total_ties += ties

        row = {
            "opponent": opp,
            "legs": n_legs,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_rate": f"{wr:.2f}%",
            "mean_delta": f"{mean_d:+.1f}",
            "median_delta": f"{med_d:+.1f}",
            "casualties": casualties,
        }
        summary_rows.append(row)
        print(f"{opp:22s} | {n_legs:5d} | {wins:5d} | {losses:6d} | {ties:4d} | {wr:7.2f}% | {mean_d:+10.1f} | {med_d:+10.1f} | {casualties:10d}")

    overall_wr = 100.0 * total_wins / len(tasks)
    print("-" * 95)
    print(f"{'OVERALL PANEL':22s} | {len(tasks):5d} | {total_wins:5d} | {total_losses:6d} | {total_ties:4d} | {overall_wr:7.2f}% |")

    # Write BENCHMARK_MATRIX.csv
    out_csv = os.path.join(REPO_ROOT, "research/final_synthesis/BENCHMARK_MATRIX.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["opponent", "legs", "wins", "losses", "ties", "win_rate", "mean_delta", "median_delta", "casualties"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nSaved benchmark matrix to {out_csv}")

if __name__ == "__main__":
    main()
