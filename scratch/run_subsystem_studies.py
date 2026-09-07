import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
import candidates.candidate_v2_adaptive_overlay as overlay_mod

SEEDS = [42, 101, 215, 333, 404]

def evaluate_agent(agent_fn, name, opp="starter", seeds=SEEDS):
    scores = []
    margins = []
    for s in seeds:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env.run([agent_fn, opp])
        r0 = env.steps[-1][0]["reward"]
        r1 = env.steps[-1][1]["reward"]
        scores.append(r0)
        margins.append(r0 - r1)
    mean_s = float(np.mean(scores))
    mean_m = float(np.mean(margins))
    print(f"  {name:<35}: Mean Score = ${mean_s:>10.2f}, Mean Margin = ${mean_m:>10.2f}")
    return {"mean_score": mean_s, "mean_margin": mean_m, "scores": scores}

def test_market_variants():
    print("\n--- Phase 7: Market Overlay Variants vs. Opponent 'Market Aggressor' ---")
    
    # 1. Original V2
    r_orig = evaluate_agent(v2_mod.agent, "1. Original V2 Market", opp="opponents/o9_market_aggressor.py")
    
    # 2. Adaptive Overlay (Price Floor + Solvency Guard)
    r_overlay = evaluate_agent(overlay_mod.agent, "2. Adaptive Overlay (Guarded)", opp="opponents/o9_market_aggressor.py")
    
    # 3. Aggressive Sell-Delay Guard
    def delay_guard_agent(obs, config=None):
        act = overlay_mod.agent(obs, config)
        step = int(obs.get("step", 0) or 0)
        if step < 680:
            prices = ((obs.get("market") or {}).get("prices") or {})
            # Only sell if price >= 0.80 base
            filtered = []
            for o in act.get("market", []) or []:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    item = o[1]
                    base_p = overlay_mod._BASE_PRICES.get(item, 100)
                    cur_p = float(prices.get(item, base_p) or base_p)
                    if cur_p >= 0.80 * base_p:
                        filtered.append(o)
                else:
                    filtered.append(o)
            act["market"] = filtered[:10]
        return act
        
    r_delay = evaluate_agent(delay_guard_agent, "3. Aggressive Delay Guard (0.80x)", opp="opponents/o9_market_aggressor.py")
    
    return {
        "original": r_orig,
        "overlay": r_overlay,
        "aggressive_delay": r_delay
    }

def test_labor_capacity():
    print("\n--- Phase 9: Labor Capacity Evaluation on Standard Seeds ---")
    
    # Baseline V2 (6 workers)
    r_v2 = evaluate_agent(v2_mod.agent, "Baseline V2 (6 Workers)")
    
    # Overlay (6 workers + solvency check)
    r_overlay = evaluate_agent(overlay_mod.agent, "Adaptive Overlay")
    
    return {
        "v2": r_v2,
        "overlay": r_overlay
    }

if __name__ == "__main__":
    print("================================================================================")
    print("PHASES 7, 8, 9, 10: SUBSYSTEM ADAPTATION STUDIES")
    print("================================================================================")
    mkt = test_market_variants()
    labor = test_labor_capacity()
    
    results = {
        "market": mkt,
        "labor": labor
    }
    with open('scratch/subsystem_adaptation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSaved subsystem adaptation results to scratch/subsystem_adaptation_results.json")
