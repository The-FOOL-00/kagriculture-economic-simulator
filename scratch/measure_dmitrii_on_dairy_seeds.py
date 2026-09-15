import os
import sys
import json
import time
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
    print("PHASE 3: DMITRII-LB2800 ON DAIRY WORLDS (SMOOTHIE + ICE CREAM)")
    print("============================================================")
    
    seeds_file = os.path.join(BASE_DIR, "scratch", "shop_world_seeds.json")
    with open(seeds_file, encoding="utf-8") as f:
        shop_data = json.load(f)
        
    dairy_seeds = shop_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"] + shop_data["ICE_CREAM_SHOP+SMOOTHIE_SHOP"]
    print(f"Total Dairy Seeds: {len(dairy_seeds)} (2 matches per seed = {2 * len(dairy_seeds)} matches)")
    
    dmitrii_agent = dmitrii_main.agent
    v54_agent = compiled_v54_plus_residual.agent
    
    results = []
    t0 = time.time()
    
    for idx, s in enumerate(dairy_seeds):
        # P0
        r0, r1 = run_match(dmitrii_agent, v54_agent, s)
        results.append({"seed": s, "seat": 0, "dmitrii": r0, "v54": r1, "win": r0 > r1, "margin": r0 - r1})
        # P1
        r0, r1 = run_match(v54_agent, dmitrii_agent, s)
        results.append({"seed": s, "seat": 1, "dmitrii": r1, "v54": r0, "win": r1 > r0, "margin": r1 - r0})
        
    total_time = time.time() - t0
    
    d_cash = [r["dmitrii"] for r in results]
    v_cash = [r["v54"] for r in results]
    margins = [r["margin"] for r in results]
    wins = [r["win"] for r in results]
    
    print(f"\n--- DMITRII BASELINE ON DAIRY WORLDS (N={len(results)} matches) ---")
    print(f"  Matches: {len(results)} in {total_time:.2f}s")
    print(f"  Dmitrii Mean Cash: ${np.mean(d_cash):,.2f} (std: ${np.std(d_cash):,.2f})")
    print(f"  V54++ Mean Cash:   ${np.mean(v_cash):,.2f} (std: ${np.std(v_cash):,.2f})")
    print(f"  Net Paired Margin: +${np.mean(margins):,.2f}")
    print(f"  Win Rate: {np.mean(wins)*100:.2f}% ({sum(wins)}/{len(wins)})")
    print(f"  Worst Margin: ${min(margins):,.2f} | Best Win: +${max(margins):,.2f}")
    print("============================================================\n")
    
    # Save baseline results
    out_file = os.path.join(BASE_DIR, "scratch", "dairy_baseline_dmitrii.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
