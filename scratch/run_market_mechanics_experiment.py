"""
Validated Market Mechanics Causal Experiment
Evaluates 4 isolated market policy variants against Baseline (CL-Economic-V1) across 100 seeds:
- Standalone vs Starter (100 matches)
- Direct Head-to-Head vs Frozen V2 (100 matches, alternating seats)

Variants:
1. Baseline: CL-Economic-V1 (Current market dumping)
2. Variant 1: Impact-Sorted Selling Only (Sort SELL orders by gross revenue impact)
3. Variant 2: Demand-Cycle Batching Only (Hold sales until step % 4 == 0)
4. Variant 3: Impact-Sorted + Demand-Cycle Batching (V1 + V2)
5. Variant 4: Demand-Cycle Batching + Terminal Ramp (Batch on step % 4 == 0, ramp after step 680)
"""

import sys
import os
import json
import time
import copy
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import (
    ClosedLoopEconomicV1, agent as cl_agent,
    SELLABLE, BASE_PRICES
)

SEEDS = list(range(5000, 5100))

# ---------------------------------------------------------------------------
# Market Policy Subclasses
# ---------------------------------------------------------------------------

# Variant 1: Impact-Sorted Selling Only
class MarketVariant1_ImpactSort(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Separate sells and other orders
        sells = [o for o in orders if o and o[0] == "SELL"]
        others = [o for o in orders if o and o[0] != "SELL"]
        
        # Sort sells by gross impact (quantity * current market price)
        m_prices = (obs.get("market") or {}).get("prices") or {}
        def _impact(o):
            item = o[1]
            qty = int(o[2]) if len(o) > 2 else 1
            p = float(m_prices.get(item, BASE_PRICES.get(item, 50)))
            return qty * p
            
        sells.sort(key=_impact, reverse=True)
        # Place highest impact sells first
        return (sells + others)[:10]


# Variant 2: Demand-Cycle Batching Only (Hold sales until step % 4 == 0)
class MarketVariant2_DemandBatch(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # If not a town demand step (step % 4 != 0) and not terminal (step < 680), suppress sells
        if step % 4 != 0 and step < 680:
            # keep buys/hires, drop sells unless cash is desperately low (< 100)
            if money >= 100:
                orders = [o for o in orders if o and o[0] != "SELL"]
        return orders[:10]


# Variant 3: Impact-Sorted + Demand-Cycle Batching
class MarketVariant3_ImpactAndBatch(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        sells = [o for o in orders if o and o[0] == "SELL"]
        others = [o for o in orders if o and o[0] != "SELL"]
        
        # Suppress sells if off-cycle and solvent
        if step % 4 != 0 and step < 680 and money >= 100:
            sells = []
            
        m_prices = (obs.get("market") or {}).get("prices") or {}
        def _impact(o):
            item = o[1]
            qty = int(o[2]) if len(o) > 2 else 1
            p = float(m_prices.get(item, BASE_PRICES.get(item, 50)))
            return qty * p
            
        sells.sort(key=_impact, reverse=True)
        return (sells + others)[:10]


# Variant 4: Demand-Cycle Batching + Inventory Reservation Ramp
class MarketVariant4_BatchAndRamp(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        sells = [o for o in orders if o and o[0] == "SELL"]
        others = [o for o in orders if o and o[0] != "SELL"]
        
        # Only sell on step % 4 == 0 or terminal ramp
        if step % 4 != 0 and step < 680 and money >= 150:
            sells = []
            
        m_prices = (obs.get("market") or {}).get("prices") or {}
        def _impact(o):
            item = o[1]
            qty = int(o[2]) if len(o) > 2 else 1
            p = float(m_prices.get(item, BASE_PRICES.get(item, 50)))
            return qty * p
            
        sells.sort(key=_impact, reverse=True)
        return (sells + others)[:10]


VARIANTS = {
    "Baseline (CL-Economic-V1)": ClosedLoopEconomicV1,
    "Variant 1 (Impact Sort Only)": MarketVariant1_ImpactSort,
    "Variant 2 (Demand Batch Only)": MarketVariant2_DemandBatch,
    "Variant 3 (Impact + Batch)": MarketVariant3_ImpactAndBatch,
    "Variant 4 (Batch + Ramp)": MarketVariant4_BatchAndRamp,
}

def _run_h2h(v_name, seed, seat):
    cls = VARIANTS[v_name]
    cand = cls()
    agents = [cand, v2_agent] if seat == 0 else [v2_agent, cand]
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    try:
        env.run(agents)
        r0 = float(env.steps[-1][0].get("reward") or 0.0)
        r1 = float(env.steps[-1][1].get("reward") or 0.0)
        cand_r = r0 if seat == 0 else r1
        v2_r = r1 if seat == 0 else r0
        return {"variant": v_name, "seed": seed, "cand_reward": cand_r, "v2_reward": v2_r, "margin": cand_r - v2_r}
    except Exception as e:
        return {"variant": v_name, "seed": seed, "cand_reward": 0.0, "v2_reward": 0.0, "margin": 0.0}

def _run_standalone(v_name, seed):
    cls = VARIANTS[v_name]
    cand = cls()
    agents = [cand, "starter"]
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    try:
        env.run(agents)
        r = float(env.steps[-1][0].get("reward") or 0.0)
        return {"variant": v_name, "seed": seed, "reward": r}
    except Exception as e:
        return {"variant": v_name, "seed": seed, "reward": 0.0}

def run_market_experiment(seeds=range(5000, 5100), max_workers=10):
    print("=" * 85)
    print("PHASE 3: VALIDATED MARKET MECHANICS CAUSAL EXPERIMENT (100 SEEDS)")
    print("=" * 85)
    
    summary_results = []
    
    for v_name in VARIANTS:
        print(f"\nEvaluating {v_name}...")
        t0 = time.time()
        
        # 1. Standalone
        standalone_tasks = [(v_name, s) for s in seeds]
        standalone_res = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_standalone, vn, s) for vn, s in standalone_tasks]
            for f in as_completed(futures):
                standalone_res.append(f.result())
        sa_rews = np.array([r["reward"] for r in standalone_res])
        
        # 2. H2H vs Frozen V2 (alternating seats)
        h2h_tasks = [(v_name, s, i % 2) for i, s in enumerate(seeds)]
        h2h_res = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_h2h, vn, s, seat) for vn, s, seat in h2h_tasks]
            for f in as_completed(futures):
                h2h_res.append(f.result())
        cand_h2h = np.array([r["cand_reward"] for r in h2h_res])
        v2_h2h = np.array([r["v2_reward"] for r in h2h_res])
        margins = np.array([r["margin"] for r in h2h_res])
        
        elapsed = time.time() - t0
        
        row = {
            "variant": v_name,
            "standalone_mean": float(np.mean(sa_rews)),
            "standalone_std": float(np.std(sa_rews)),
            "cand_h2h_mean": float(np.mean(cand_h2h)),
            "v2_h2h_mean": float(np.mean(v2_h2h)),
            "h2h_margin": float(np.mean(margins)),
            "median_margin": float(np.median(margins)),
            "elapsed": elapsed
        }
        summary_results.append(row)
        print(f"  Done in {elapsed:.1f}s. Standalone: ${row['standalone_mean']:,.1f}, H2H Margin: ${row['h2h_margin']:,.1f}")

    out_path = os.path.join(PROJECT_ROOT, "scratch", "market_mechanics_experiment_results.json")
    with open(out_path, "w") as f:
        json.dump(summary_results, f, indent=2)
        
    print("\n" + "=" * 105)
    print("VALIDATED MARKET MECHANICS EXPERIMENTAL MATRIX (N = 100 Seeds)")
    print("=" * 105)
    print(f"{'VARIANT':<32} | {'STANDALONE ($)':<16} | {'CAND H2H ($)':<14} | {'V2 H2H ($)':<14} | {'NET MARGIN ($)':<16} | {'MARGIN LIFT':<12}")
    print("-" * 105)
    base_margin = summary_results[0]["h2h_margin"]
    for r in summary_results:
        lift = r["h2h_margin"] - base_margin
        print(f"{r['variant']:<32} | ${r['standalone_mean']:14,.1f} | ${r['cand_h2h_mean']:12,.1f} | ${r['v2_h2h_mean']:12,.1f} | ${r['h2h_margin']:14,.1f} | {lift:+10,.1f}")
    print("=" * 105)
    
    return summary_results

if __name__ == "__main__":
    run_market_experiment()
