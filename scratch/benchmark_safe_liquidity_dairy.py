import copy
import json
import os
import sys
import math

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54
from test_safe_liquidity_dairy import SafeDairyPolicy, compile_safe_liquidity_dairy

def benchmark_safe_dairy():
    print("=" * 80)
    print("PHASE 12 EXPERIMENT: LIQUIDITY-GUARANTEED DAIRY VS DMITRII BASELINE")
    print("Target World: SMOOTHIE_SHOP + ICE_CREAM_SHOP")
    print("=" * 80)
    
    safe_tape = compile_safe_liquidity_dairy()
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"] + seeds_data.get("ICE_CREAM_SHOP+SMOOTHIE_SHOP", [])
    n_seeds = min(50, len(dairy_seeds))
    test_seeds = dairy_seeds[:n_seeds]
    
    results_base = []
    results_cand = []
    
    for idx, s in enumerate(test_seeds):
        # Seat 0
        pb0 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        pc0 = SafeDairyPolicy("extracted_agents/dmitrii_lb2800", safe_tape)
        g0 = kagsim.Game(s)
        g1 = kagsim.Game(s)
        while not g0.done: g0.step(pb0.act(g0.observe(0)), v54.agent(g0.observe(1)))
        while not g1.done: g1.step(pc0.act(g1.observe(0)), v54.agent(g1.observe(1)))
        results_base.append(g0.reward(0))
        results_cand.append(g1.reward(0))
        
        # Seat 1
        pb1 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        pc1 = SafeDairyPolicy("extracted_agents/dmitrii_lb2800", safe_tape)
        g2 = kagsim.Game(s)
        g3 = kagsim.Game(s)
        while not g2.done: g2.step(v54.agent(g2.observe(0)), pb1.act(g2.observe(1)))
        while not g3.done: g3.step(v54.agent(g3.observe(0)), pc1.act(g3.observe(1)))
        results_base.append(g2.reward(1))
        results_cand.append(g3.reward(1))

    n_matches = len(results_base)
    mean_base = sum(results_base) / n_matches
    mean_cand = sum(results_cand) / n_matches
    delta = mean_cand - mean_base
    
    diffs = [c - b for c, b in zip(results_cand, results_base)]
    diffs.sort()
    median_diff = diffs[n_matches // 2]
    
    var_diff = sum((d - delta) ** 2 for d in diffs) / (n_matches - 1)
    std_diff = math.sqrt(var_diff)
    se_diff = std_diff / math.sqrt(n_matches)
    ci95_lower = delta - 1.96 * se_diff
    ci95_upper = delta + 1.96 * se_diff
    
    wins = sum(1 for d in diffs if d > 0)
    ties = sum(1 for d in diffs if d == 0)
    losses = sum(1 for d in diffs if d < 0)
    
    print(f"\nRESULTS OVER {n_matches} MATCHES ({n_seeds} SEEDS, BOTH SEATS):")
    print(f"  Dmitrii Base Mean Cash:       ${mean_base:,.2f}")
    print(f"  Safe Liquidity Dairy Mean:    ${mean_cand:,.2f}")
    print(f"  Net Paired Delta:             ${delta:+,.2f}")
    print(f"  Median Delta:                 ${median_diff:+,.2f}")
    print(f"  95% Confidence Interval:      [${ci95_lower:+,.2f}, ${ci95_upper:+,.2f}]")
    print(f"  Candidate vs Base Record:     {wins}W / {ties}T / {losses}L (Win Rate: {wins/n_matches*100:.1f}%)")
    print(f"  Worst Delta:                  ${min(diffs):+,.2f}")
    print(f"  Best Delta:                   ${max(diffs):+,.2f}")
    print(f"  P(Delta < -$1,000):           {sum(1 for d in diffs if d < -1000)/n_matches*100:.1f}%")
    print(f"  P(Delta > +$1,000):           {sum(1 for d in diffs if d > 1000)/n_matches*100:.1f}%")

if __name__ == "__main__":
    benchmark_safe_dairy()
