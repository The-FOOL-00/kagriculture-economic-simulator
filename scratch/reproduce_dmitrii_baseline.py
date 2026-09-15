import os
import sys
import time
import math
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import compiled_v54_plus_residual
import main as dmitrii_main

def run_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return float(game.reward(0)), float(game.reward(1))

def main():
    print("============================================================")
    print("PHASE 2: INDEPENDENT DMITRII-LB2800 REPRODUCTION (200 SEEDS)")
    print("============================================================")
    seeds = list(range(40000, 40200))
    n_seeds = len(seeds)
    print(f"Running {n_seeds} seeds, 2 seats each = {2 * n_seeds} matches...")
    
    dmitrii_agent = dmitrii_main.agent
    v54_agent = compiled_v54_plus_residual.agent
    
    results = []
    t0 = time.time()
    
    for idx, seed in enumerate(seeds):
        # Seat 0: Dmitrii as P0, V54 as P1
        r0, r1 = run_match(dmitrii_agent, v54_agent, seed)
        results.append({"seed": seed, "dmitrii_seat": 0, "dmitrii_cash": r0, "opp_cash": r1, "win": r0 > r1, "margin": r0 - r1})
        
        # Seat 1: V54 as P0, Dmitrii as P1
        r0, r1 = run_match(v54_agent, dmitrii_agent, seed)
        results.append({"seed": seed, "dmitrii_seat": 1, "dmitrii_cash": r1, "opp_cash": r0, "win": r1 > r0, "margin": r1 - r0})
        
        if (idx + 1) % 50 == 0 or (idx + 1) == n_seeds:
            print(f"  Completed {idx + 1}/{n_seeds} seeds ({len(results)} matches) in {time.time() - t0:.1f}s")
            
    total_time = time.time() - t0
    
    dmitrii_cashes = [r["dmitrii_cash"] for r in results]
    opp_cashes = [r["opp_cash"] for r in results]
    margins = [r["margin"] for r in results]
    wins = [r["win"] for r in results]
    
    p0_results = [r for r in results if r["dmitrii_seat"] == 0]
    p1_results = [r for r in results if r["dmitrii_seat"] == 1]
    
    p0_wr = np.mean([r["win"] for r in p0_results]) * 100
    p1_wr = np.mean([r["win"] for r in p1_results]) * 100
    overall_wr = np.mean(wins) * 100
    
    mean_dmitrii = np.mean(dmitrii_cashes)
    mean_opp = np.mean(opp_cashes)
    mean_margin = np.mean(margins)
    std_margin = np.std(margins, ddof=1)
    se_margin = std_margin / math.sqrt(len(margins))
    ci95 = (mean_margin - 1.96 * se_margin, mean_margin + 1.96 * se_margin)
    
    print("\n--- RESULTS SUMMARY ---")
    print(f"Matches Played: {len(results)} in {total_time:.2f}s ({len(results)/total_time:.1f} matches/s)")
    print(f"Mean Dmitrii Cash: ${mean_dmitrii:,.2f}")
    print(f"Mean Opponent Cash: ${mean_opp:,.2f}")
    print(f"Net Paired Margin: +${mean_margin:,.2f}")
    print(f"95% CI: [${ci95[0]:,.2f}, ${ci95[1]:,.2f}]")
    print(f"Win Rate: {overall_wr:.2f}% ({sum(wins)} wins, {len(wins) - sum(wins)} losses)")
    print(f"Seat Symmetry: P0 WR = {p0_wr:.2f}% | P1 WR = {p1_wr:.2f}%")
    print(f"Worst Loss Margin: ${min(margins):,.2f}")
    print(f"Best Win Margin: +${max(margins):,.2f}")
    print("============================================================\n")

if __name__ == "__main__":
    main()
