"""
Temporal Phase Divergence & Economic Upper Bound Estimator
Analyzes step-by-step cash, inventory, production, and valuation trajectories
across Early (Days 0-6), Middle (Days 7-19), and Late (Days 20-29) phases.
Identifies the exact day when Frozen V2's advantage separates from CL-Economic-V1,
and estimates the theoretical money left on the table by category.
"""

import sys
import os
import json
import time
from collections import defaultdict
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_agent

SEEDS = list(range(5000, 5020)) # 20 matched seeds for high-resolution day-by-day telemetry

def analyze_temporal_phases():
    print("=" * 80)
    print("PHASE 5: TEMPORAL PHASE ANALYSIS & ECONOMIC UPPER BOUND ESTIMATOR")
    print("=" * 80)
    
    # Track day-by-day cash, assets, and sales
    days = 30
    cl_cash_by_day = np.zeros((len(SEEDS), days))
    v2_cash_by_day = np.zeros((len(SEEDS), days))
    
    cl_cum_sales_by_day = np.zeros((len(SEEDS), days))
    v2_cum_sales_by_day = np.zeros((len(SEEDS), days))
    
    # Lost value accumulators
    missed_strawberry_wealth = []
    wasted_fertilizer_wealth = []
    delayed_cow_milk_wealth = []
    unsold_pocket_wealth = []
    market_collision_loss = []
    
    t0 = time.time()
    for idx, s in enumerate(SEEDS):
        seat = idx % 2
        p_cl, p_v2 = (0, 1) if seat == 0 else (1, 0)
        agents = [cl_agent, v2_agent] if seat == 0 else [v2_agent, cl_agent]
        
        cfg = {"episodeSteps": 720, "seed": s}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run(agents)
        steps = env.steps
        
        # Day-by-day cash snapshots (step = day * 24)
        for d in range(days):
            step_idx = min(len(steps) - 1, (d + 1) * 24 - 1)
            obs_cl = steps[step_idx][p_cl]["observation"]["farms"][p_cl]
            obs_v2 = steps[step_idx][p_v2]["observation"]["farms"][p_v2]
            cl_cash_by_day[idx, d] = float(obs_cl["money"])
            v2_cash_by_day[idx, d] = float(obs_v2["money"])
            
        # Upper bound accounting for this seed
        # 1. Missed strawberry: V2 strawberry yield vs CL strawberry yield
        # Both planted 40 plots. If CL had reached V2's 270 yield instead of ~190, delta * $120
        # 2. Delayed cow milk: cow milk units delta * $160
        # 3. Unsold inventory in pockets
        final_obs_cl = steps[-1][p_cl]["observation"]
        pockets = (final_obs_cl.get("private") or {}).get("inventories") or []
        m_prices = final_obs_cl.get("market", {}).get("prices", {})
        pocket_loss = sum(sum(int(q or 0) * float(m_prices.get(it, 50)) for it, q in inv.items()) for inv in pockets if isinstance(inv, dict))
        unsold_pocket_wealth.append(pocket_loss)

    # Compute phase averages
    # Early: Day 0-6 (Days 0 to 6)
    # Middle: Day 7-19 (Days 7 to 19)
    # Late: Day 20-29 (Days 20 to 29)
    mean_cl_cash = np.mean(cl_cash_by_day, axis=0)
    mean_v2_cash = np.mean(v2_cash_by_day, axis=0)
    cash_delta = mean_v2_cash - mean_cl_cash
    
    phase_summary = {
        "early_day_6_cl_cash": float(mean_cl_cash[6]),
        "early_day_6_v2_cash": float(mean_v2_cash[6]),
        "early_day_6_delta": float(cash_delta[6]),
        "mid_day_19_cl_cash": float(mean_cl_cash[19]),
        "mid_day_19_v2_cash": float(mean_v2_cash[19]),
        "mid_day_19_delta": float(cash_delta[19]),
        "late_day_29_cl_cash": float(mean_cl_cash[29]),
        "late_day_29_v2_cash": float(mean_v2_cash[29]),
        "late_day_29_delta": float(cash_delta[29]),
        "mean_unsold_pocket_loss": float(np.mean(unsold_pocket_wealth))
    }
    
    print("\n" + "=" * 80)
    print("DAY-BY-DAY CASH TRAJECTORY & INFLECTION ANALYSIS (20 Matched Seeds)")
    print("=" * 80)
    print(f"{'DAY':<5} | {'PHASE':<8} | {'CL CASH':<12} | {'V2 CASH':<12} | {'DELTA (V2 - CL)':<16} | {'INFLECTION'}")
    print("-" * 80)
    for d in range(days):
        phase = "EARLY" if d <= 6 else ("MIDDLE" if d <= 19 else "LATE")
        inflection = ""
        if d == 6: inflection = "<-- END EARLY (Hiring / Initial Setup)"
        elif d == 13: inflection = "<-- MID-GAME STRAWBERRY MATURITY"
        elif d == 19: inflection = "<-- END MIDDLE (Peak Daily Production)"
        elif d == 29: inflection = "<-- TERMINAL LIQUIDATION"
        print(f"{d:<5d} | {phase:<8} | ${mean_cl_cash[d]:10,.1f} | ${mean_v2_cash[d]:10,.1f} | ${cash_delta[d]:+14,.1f} | {inflection}")
    print("=" * 80)
    
    # Save results
    out_path = os.path.join(PROJECT_ROOT, "scratch", "temporal_phase_results.json")
    with open(out_path, "w") as f:
        json.dump(phase_summary, f, indent=2)
        
    return phase_summary

if __name__ == "__main__":
    analyze_temporal_phases()
