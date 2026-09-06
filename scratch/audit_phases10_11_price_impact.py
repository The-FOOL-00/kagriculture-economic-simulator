"""
Phases 10 & 11: Market Price-Impact & Timing Robustness Audit
Tests:
1. Baseline (alone / passive opponent)
2. Controlled Opponent Melon Dump:
   Opponent dumps 24 melons at steps [250, 255, 258, 260, 262, 264, 266]
Measures:
- Melon price before sale
- Melon price after sale
- V2 / H sale quantity
- Total melon revenue
- Final score
- PRICE-IMPACT LOSS (Score_alone - Score_with_dump)
- H PRICE-IMPACT PROTECTION (Loss_V2 - Loss_H)
- Decomposition of advantage
"""

import sys
import os
import json
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

DUMP_STEPS = [250, 255, 258, 260, 262, 264, 266]
SEEDS = [42, 100, 2026, 777, 999]

def make_dumper_agent(dump_step, dump_qty=24):
    """Opponent that plants/acquires and dumps melons at dump_step."""
    def agent(obs, config=None):
        step = obs.get("step") if obs.get("step") is not None else (obs.get("day", 0) * 24 + obs.get("hour", 0))
        action = {"farmer": ["PASS"], "hands": [], "market": []}
        if step == 0:
            action["market"] = [["BUY_SEED", "MELON", 4]]
        elif step == dump_step:
            action["market"] = [["SELL", "MELON", dump_qty]]
        return action
    return agent

def evaluate_impact(agent_fn, dump_step=None, dump_qty=24, seed=42):
    cfg = {"seed": seed, "episodeSteps": 720}
    env = make("kaggriculture", configuration=cfg)
    env.reset()
    
    opp_fn = make_dumper_agent(dump_step, dump_qty) if dump_step is not None else (lambda obs, cfg=None: {"farmer": ["PASS"], "hands": [], "market": []})
    
    melon_prices = {}
    melon_sales = []
    
    while not env.done:
        step = len(env.steps) - 1
        obs = env.steps[-1][0]["observation"]
        p_melon = obs.get("market", {}).get("prices", {}).get("MELON", 250)
        melon_prices[step] = p_melon
        
        obs0 = env.steps[-1][0]["observation"]
        obs1 = env.steps[-1][1]["observation"]
        m_before = obs0["farms"][0]["money"]
        
        act0 = agent_fn(obs0)
        act1 = opp_fn(obs1)
        
        if dump_step is not None and step == dump_step:
            env.state[1].observation.private['shed']['MELON'] = dump_qty
            
        env.step([act0, act1])
        
        obs0_after = env.steps[-1][0]["observation"]
        m_after = obs0_after["farms"][0]["money"]
        
        # Check if our agent sold melons
        for o in act0.get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == "MELON":
                melon_sales.append({
                    "step": step,
                    "qty": o[2],
                    "price_before": p_melon,
                    "delta_money": m_after - m_before
                })
                
    final_reward = float(env.steps[-1][0]["reward"] or 0)
    total_melon_rev = sum(s["delta_money"] for s in melon_sales)
    total_melon_sold = sum(s["qty"] for s in melon_sales)
    
    return {
        "final_reward": final_reward,
        "total_melon_rev": total_melon_rev,
        "total_melon_sold": total_melon_sold,
        "melon_sales": melon_sales,
        "price_at_264": melon_prices.get(264, 250)
    }

def main():
    results = {"alone": {}, "timing_sweep": {}}
    
    print("--- 1. BASELINE ALONE (NO OPPONENT INTERFERENCE) ---")
    v2_alone_scores = []
    h_alone_scores = []
    v2_alone_revs = []
    h_alone_revs = []
    
    for s in SEEDS:
        v2_res = evaluate_impact(v2.agent, dump_step=None, seed=s)
        h_res = evaluate_impact(agent_H_full_jit_pipeline, dump_step=None, seed=s)
        v2_alone_scores.append(v2_res["final_reward"])
        h_alone_scores.append(h_res["final_reward"])
        v2_alone_revs.append(v2_res["total_melon_rev"])
        h_alone_revs.append(h_res["total_melon_rev"])
        
    results["alone"] = {
        "v2_mean_score": float(np.mean(v2_alone_scores)),
        "h_mean_score": float(np.mean(h_alone_scores)),
        "mean_delta": float(np.mean(h_alone_scores) - np.mean(v2_alone_scores)),
        "v2_melon_rev": float(np.mean(v2_alone_revs)),
        "h_melon_rev": float(np.mean(h_alone_revs)),
        "melon_rev_delta": float(np.mean(h_alone_revs) - np.mean(v2_alone_revs))
    }
    print(f"Alone: V2 Score={results['alone']['v2_mean_score']:.1f}, H Score={results['alone']['h_mean_score']:.1f}, Delta={results['alone']['mean_delta']:+.1f}")
    print(f"Melon Rev: V2={results['alone']['v2_melon_rev']:.1f}, H={results['alone']['h_melon_rev']:.1f}, Delta={results['alone']['melon_rev_delta']:+.1f}")
    
    print("\n--- 2. TIMING SWEEP (OPPONENT DUMPS 24 MELONS AT VARIOUS STEPS) ---")
    timing_sweep = {}
    
    for step in DUMP_STEPS:
        v2_scores = []
        h_scores = []
        v2_revs = []
        h_revs = []
        p264_list = []
        
        for s in SEEDS:
            v2_res = evaluate_impact(v2.agent, dump_step=step, dump_qty=24, seed=s)
            h_res = evaluate_impact(agent_H_full_jit_pipeline, dump_step=step, dump_qty=24, seed=s)
            v2_scores.append(v2_res["final_reward"])
            h_scores.append(h_res["final_reward"])
            v2_revs.append(v2_res["total_melon_rev"])
            h_revs.append(h_res["total_melon_rev"])
            p264_list.append(v2_res["price_at_264"])
            
        v2_loss = results["alone"]["v2_mean_score"] - float(np.mean(v2_scores))
        h_loss = results["alone"]["h_mean_score"] - float(np.mean(h_scores))
        protection = v2_loss - h_loss
        h_v2_delta = float(np.mean(h_scores) - np.mean(v2_scores))
        
        timing_sweep[str(step)] = {
            "v2_mean_score": float(np.mean(v2_scores)),
            "h_mean_score": float(np.mean(h_scores)),
            "h_minus_v2_delta": h_v2_delta,
            "v2_price_impact_loss": v2_loss,
            "h_price_impact_loss": h_loss,
            "h_protection": protection,
            "v2_melon_rev": float(np.mean(v2_revs)),
            "h_melon_rev": float(np.mean(h_revs)),
            "melon_price_at_264": float(np.mean(p264_list))
        }
        print(f"Dump Step {step:3d} | V2 Loss: {v2_loss:+.1f} | H Loss: {h_loss:+.1f} | Protection: {protection:+.1f} | H-V2 Delta: {h_v2_delta:+.1f} | Price@264: {np.mean(p264_list):.1f}")
        
    results["timing_sweep"] = timing_sweep
    
    with open("scratch/jit_melon_results/phases10_11_price_impact.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
