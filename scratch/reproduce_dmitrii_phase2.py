"""
scratch/reproduce_dmitrii_phase2.py
Phase 2: Independent reproduction of Dmitrii-LB2800 baseline.
200 fresh CRN seeds (seeds 40000..40199), both seats = 400 symmetric matches per opponent.
Opponents:
1. compiled_v54_plus_residual.py
2. compiled_v54_plus_shop.py
"""
import copy
import importlib.util
import json
import math
import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import compiled_v54_plus_residual
import compiled_v54_plus_shop

# Load Dmitrii LB2800
DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, DMITRII_DIR)
spec_dmitrii = importlib.util.spec_from_file_location("dmitrii_agent", os.path.join(DMITRII_DIR, "main.py"))
mod_dmitrii = importlib.util.module_from_spec(spec_dmitrii)
spec_dmitrii.loader.exec_module(mod_dmitrii)

def play_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return float(game.reward(0)), float(game.reward(1))

def compute_stats(dmitrii_scores, opp_scores, margins, p0_margins, p1_margins):
    n = len(margins)
    mean_d = sum(dmitrii_scores) / n
    mean_o = sum(opp_scores) / n
    mean_m = sum(margins) / n
    
    sorted_d = sorted(dmitrii_scores)
    sorted_o = sorted(opp_scores)
    sorted_m = sorted(margins)
    
    median_d = sorted_d[n // 2]
    median_o = sorted_o[n // 2]
    median_m = sorted_m[n // 2]
    
    var_m = sum((x - mean_m) ** 2 for x in margins) / (n - 1) if n > 1 else 0.0
    std_m = math.sqrt(var_m)
    se_m = std_m / math.sqrt(n) if n > 0 else 0.0
    
    ci95 = (mean_m - 1.96 * se_m, mean_m + 1.96 * se_m)
    ci99 = (mean_m - 2.576 * se_m, mean_m + 2.576 * se_m)
    
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)
    ties = sum(1 for m in margins if m == 0)
    win_rate = wins / n
    
    p0_wins = sum(1 for m in p0_margins if m > 0)
    p0_wr = p0_wins / len(p0_margins) if p0_margins else 0.0
    p1_wins = sum(1 for m in p1_margins if m > 0)
    p1_wr = p1_wins / len(p1_margins) if p1_margins else 0.0
    
    tail_losses_100 = sum(1 for m in margins if m < -100) / n
    tail_losses_500 = sum(1 for m in margins if m < -500) / n
    tail_losses_1000 = sum(1 for m in margins if m < -1000) / n
    tail_gains_1000 = sum(1 for m in margins if m > 1000) / n
    tail_gains_5000 = sum(1 for m in margins if m > 5000) / n
    tail_gains_10000 = sum(1 for m in margins if m > 10000) / n
    
    worst_loss = min(margins)
    best_win = max(margins)
    
    return {
        "N": n,
        "dmitrii_mean": mean_d,
        "dmitrii_median": median_d,
        "opp_mean": mean_o,
        "opp_median": median_o,
        "mean_margin": mean_m,
        "median_margin": median_m,
        "std_margin": std_m,
        "se_margin": se_m,
        "ci95": ci95,
        "ci99": ci99,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "p0_win_rate": p0_wr,
        "p1_win_rate": p1_wr,
        "tail_losses_100": tail_losses_100,
        "tail_losses_500": tail_losses_500,
        "tail_losses_1000": tail_losses_1000,
        "tail_gains_1000": tail_gains_1000,
        "tail_gains_5000": tail_gains_5000,
        "tail_gains_10000": tail_gains_10000,
        "worst_loss": worst_loss,
        "best_win": best_win
    }

def print_report(name, stats):
    print("=" * 80)
    print(f"BENCHMARK REPORT: DMITRII LB2800 vs {name}")
    print("=" * 80)
    print(f"Total Matches       : {stats['N']} ({stats['N']//2} seeds x 2 seats)")
    print(f"Dmitrii Mean Cash   : ${stats['dmitrii_mean']:,.2f}  (Median: ${stats['dmitrii_median']:,.2f})")
    print(f"Opponent Mean Cash  : ${stats['opp_mean']:,.2f}  (Median: ${stats['opp_median']:,.2f})")
    print(f"Paired Net Margin   : {stats['mean_margin']:+,.2f}  (Median: {stats['median_margin']:+,.2f})")
    print(f"StdDev / SE         : ${stats['std_margin']:,.2f} / ${stats['se_margin']:,.2f}")
    print(f"95% Confidence Int  : [${stats['ci95'][0]:+,.2f}, ${stats['ci95'][1]:+,.2f}]")
    print(f"99% Confidence Int  : [${stats['ci99'][0]:+,.2f}, ${stats['ci99'][1]:+,.2f}]")
    print(f"Win / Loss / Tie    : {stats['wins']} / {stats['losses']} / {stats['ties']}")
    print(f"Overall Win Rate    : {stats['win_rate']*100:.2f}%")
    print(f"P0 (Seat 0) Win Rate: {stats['p0_win_rate']*100:.2f}%")
    print(f"P1 (Seat 1) Win Rate: {stats['p1_win_rate']*100:.2f}%")
    print(f"Tail Risks:")
    print(f"  P(delta < -100)   : {stats['tail_losses_100']*100:.1f}%")
    print(f"  P(delta < -500)   : {stats['tail_losses_500']*100:.1f}%")
    print(f"  P(delta < -1000)  : {stats['tail_losses_1000']*100:.1f}%")
    print(f"  P(delta > +1000)  : {stats['tail_gains_1000']*100:.1f}%")
    print(f"  P(delta > +5000)  : {stats['tail_gains_5000']*100:.1f}%")
    print(f"  P(delta > +10000) : {stats['tail_gains_10000']*100:.1f}%")
    print(f"Worst Loss          : {stats['worst_loss']:+,.2f}")
    print(f"Best Win            : {stats['best_win']:+,.2f}")
    print("=" * 80)

def main():
    seeds = list(range(40000, 40200)) # 200 fresh seeds
    opponents = [
        ("compiled_v54_plus_residual", compiled_v54_plus_residual.agent),
        ("compiled_v54_plus_shop", compiled_v54_plus_shop.agent)
    ]
    
    results = {}
    
    for opp_name, opp_agent in opponents:
        print(f"\nEvaluating vs {opp_name} across {len(seeds)} seeds (400 matches)...")
        t0 = time.time()
        d_scores, o_scores, margins, p0_margins, p1_margins = [], [], [], [], []
        
        for idx, s in enumerate(seeds):
            # Seat 0: Dmitrii, Seat 1: Opponent
            r_d0, r_o1 = play_match(mod_dmitrii.agent, opp_agent, s)
            m0 = r_d0 - r_o1
            d_scores.append(r_d0)
            o_scores.append(r_o1)
            margins.append(m0)
            p0_margins.append(m0)
            
            # Seat 1: Dmitrii, Seat 0: Opponent
            r_o0, r_d1 = play_match(opp_agent, mod_dmitrii.agent, s)
            m1 = r_d1 - r_o0
            d_scores.append(r_d1)
            o_scores.append(r_o0)
            margins.append(m1)
            p1_margins.append(m1)
            
        elapsed = time.time() - t0
        print(f"Completed in {elapsed:.2f}s ({len(margins)/elapsed:.1f} matches/s)")
        stats = compute_stats(d_scores, o_scores, margins, p0_margins, p1_margins)
        print_report(opp_name, stats)
        results[opp_name] = stats
        
    out_file = os.path.join(BASE_DIR, "results", "phase2_dmitrii_reproduction.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_file}")

if __name__ == "__main__":
    main()
