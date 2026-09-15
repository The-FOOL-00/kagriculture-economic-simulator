"""
scratch/benchmark_dmitrii_tarzan.py
===================================
Benchmarking submission_dmitrii_lb2800 (Tarzan) on local C++ simulator.
Evaluates:
1. Standalone execution test
2. Solo vs IDLE on 20 seeds
3. Head-to-Head vs V54++ Residual Baseline on 20 seeds (2 seats each = 40 matches)
"""
import copy
import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_residual

TARZAN_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, TARZAN_DIR)

# Import Tarzan
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
    seeds = [11, 23, 47, 100, 200, 300, 400, 500, 600, 700,
             1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
    idle = lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}
    
    print("=" * 70)
    print("BENCHMARKING DMITRII LB2800 (TARZAN)")
    print(f"Evaluation over {len(seeds)} seeds across both seats")
    print("=" * 70)
    
    # 1. Solo vs IDLE
    print("\n--- 1. SOLO VS IDLE ---")
    tarzan_solo = []
    v54_solo = []
    for s in seeds:
        # Re-import / re-instantiate if needed, or make fresh closures
        r_t, _ = play_match(mod_tarzan.agent, idle, s)
        r_v, _ = play_match(v54_plus_residual.agent, idle, s)
        tarzan_solo.append(r_t)
        v54_solo.append(r_v)
        
    print(f"Tarzan Solo Mean : ${sum(tarzan_solo)/len(tarzan_solo):,.2f}")
    print(f"V54++  Solo Mean : ${sum(v54_solo)/len(v54_solo):,.2f}")
    print(f"Solo Net Delta   : {sum(tarzan_solo)/len(tarzan_solo) - sum(v54_solo)/len(v54_solo):+,.2f}")
    
    # 2. Head-to-Head: Tarzan vs V54++ Residual Baseline
    print("\n--- 2. HEAD-TO-HEAD: TARZAN VS V54++ RESIDUAL ---")
    margins = []
    t_scores = []
    v_scores = []
    wins, losses, ties = 0, 0, 0
    
    for s in seeds:
        # Seat 0: Tarzan, Seat 1: V54++
        r0, r1 = play_match(mod_tarzan.agent, v54_plus_residual.agent, s)
        m0 = r0 - r1
        margins.append(m0)
        t_scores.append(r0)
        v_scores.append(r1)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1
        else: ties += 1
        
        # Seat 1: Tarzan, Seat 0: V54++
        r1, r0 = play_match(v54_plus_residual.agent, mod_tarzan.agent, s)
        m1 = r0 - r1
        margins.append(m1)
        t_scores.append(r0)
        v_scores.append(r1)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1
        else: ties += 1
        
    print(f"Tarzan H2H Mean : ${sum(t_scores)/len(t_scores):,.2f}")
    print(f"V54++  H2H Mean : ${sum(v_scores)/len(v_scores):,.2f}")
    print(f"Net Margin      : {sum(margins)/len(margins):+,.2f}")
    print(f"Win / Loss / Tie: {wins} / {losses} / {ties} ({wins/len(margins)*100:.1f}% Win Rate)")
    print("=" * 70)

if __name__ == "__main__":
    run()
