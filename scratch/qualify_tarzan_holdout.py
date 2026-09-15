"""
scratch/qualify_tarzan_holdout.py
=================================
Large paired holdout qualification of Tarzan (dmitrii_lb2800) vs V54++ Residual Control.
50 paired seeds x 2 seats = 100 total matches.
Computes mean, median, std, 95% CI, win rate, and tail metrics.
"""
import math
import os
import sys
import importlib.util

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_residual

TARZAN_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, TARZAN_DIR)

spec_tarzan = importlib.util.spec_from_file_location("tarzan_agent", os.path.join(TARZAN_DIR, "main.py"))
mod_tarzan = importlib.util.module_from_spec(spec_tarzan)
spec_tarzan.loader.exec_module(mod_tarzan)

def play_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return game.reward(0), game.reward(1)

def run():
    # 50 diverse seeds
    seeds = [1000 + i * 31 for i in range(50)]
    
    print("=" * 75)
    print("QUALIFICATION HOLDOUT: TARZAN (DMITRII LB2800) VS V54++ RESIDUAL CONTROL")
    print(f"50 Paired Seeds x 2 Seats = {len(seeds) * 2} Matches")
    print("=" * 75)
    
    margins = []
    tarzan_scores = []
    v54_scores = []
    wins, losses, ties = 0, 0, 0
    
    for i, s in enumerate(seeds):
        # Seat 0: Tarzan, Seat 1: V54++
        r0, r1 = play_match(mod_tarzan.agent, v54_plus_residual.agent, s)
        m0 = r0 - r1
        margins.append(m0)
        tarzan_scores.append(r0)
        v54_scores.append(r1)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1
        else: ties += 1
        
        # Seat 1: Tarzan, Seat 0: V54++
        r1, r0 = play_match(v54_plus_residual.agent, mod_tarzan.agent, s)
        m1 = r0 - r1
        margins.append(m1)
        tarzan_scores.append(r0)
        v54_scores.append(r1)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1
        else: ties += 1
        
        if (i + 1) % 10 == 0:
            print(f"Completed {i+1}/50 seeds ({(i+1)*2} matches)... current mean margin: {sum(margins)/len(margins):+,.2f}")
            
    n = len(margins)
    mean_margin = sum(margins) / n
    tarzan_mean = sum(tarzan_scores) / n
    v54_mean = sum(v54_scores) / n
    sorted_margins = sorted(margins)
    median_margin = sorted_margins[n // 2]
    
    variance = sum((m - mean_margin) ** 2 for m in margins) / (n - 1)
    std_dev = math.sqrt(variance)
    se = std_dev / math.sqrt(n)
    ci95_low = mean_margin - 1.96 * se
    ci95_high = mean_margin + 1.96 * se
    ci99_low = mean_margin - 2.576 * se
    ci99_high = mean_margin + 2.576 * se
    
    # Tail probabilities
    p_neg_100 = sum(1 for m in margins if m < -100) / n * 100
    p_neg_500 = sum(1 for m in margins if m < -500) / n * 100
    p_neg_1000 = sum(1 for m in margins if m < -1000) / n * 100
    p_pos_1000 = sum(1 for m in margins if m > 1000) / n * 100
    p_pos_5000 = sum(1 for m in margins if m > 5000) / n * 100
    p_pos_10000 = sum(1 for m in margins if m > 10000) / n * 100
    
    print("\n" + "=" * 75)
    print("FINAL QUALIFICATION REPORT: TARZAN VS V54++ RESIDUAL")
    print("=" * 75)
    print(f"N (Matches)             : {n}")
    print(f"Tarzan Mean Cash        : ${tarzan_mean:,.2f}")
    print(f"V54++ Mean Cash         : ${v54_mean:,.2f}")
    print(f"Mean Paired Margin      : {mean_margin:+,.2f}")
    print(f"Median Paired Margin    : {median_margin:+,.2f}")
    print(f"Standard Deviation      : ${std_dev:,.2f}")
    print(f"Standard Error (SE)     : ${se:,.2f}")
    print(f"95% Confidence Interval : [{ci95_low:+,.2f}, {ci95_high:+,.2f}]")
    print(f"99% Confidence Interval : [{ci99_low:+,.2f}, {ci99_high:+,.2f}]")
    print(f"Win Rate                : {wins}/{n} ({wins/n*100:.1f}%)")
    print(f"Loss Rate               : {losses}/{n} ({losses/n*100:.1f}%)")
    print(f"Tie Rate                : {ties}/{n} ({ties/n*100:.1f}%)")
    print(f"Worst Loss (Min Margin) : {min(margins):+,.2f}")
    print(f"Best Win   (Max Margin) : {max(margins):+,.2f}")
    print("\nTail Risk / Upside Distribution:")
    print(f"  P(delta < -100)       : {p_neg_100:.1f}%")
    print(f"  P(delta < -500)       : {p_neg_500:.1f}%")
    print(f"  P(delta < -1000)      : {p_neg_1000:.1f}%")
    print(f"  P(delta > +1000)      : {p_pos_1000:.1f}%")
    print(f"  P(delta > +5000)      : {p_pos_5000:.1f}%")
    print(f"  P(delta > +10000)     : {p_pos_10000:.1f}%")
    print("=" * 75)

if __name__ == "__main__":
    run()
