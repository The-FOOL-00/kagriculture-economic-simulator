import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

def run_h2h_match(args):
    seed, p0_type, p1_type = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    agent0 = ClosedLoopEconomicV1() if p0_type == "CL" else v2_mod.agent
    agent1 = ClosedLoopEconomicV1() if p1_type == "CL" else v2_mod.agent
    
    env.run([agent0, agent1])
    steps = env.steps
    total_steps = len(steps)
    
    def extract_player_data(p_idx):
        harvest_counts = Counter()
        harvest_ops_count = Counter()
        sales_realized = Counter()
        revenue_realized = Counter()
        
        for s_idx in range(1, total_steps):
            prev_f = steps[s_idx - 1][0]["observation"]["farms"][p_idx]
            act = steps[s_idx][p_idx].get("action") or {}
            all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
            workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
            
            # Unit actions
            for w_idx, a in enumerate(all_acts):
                if a and a[0] == "HARVEST":
                    pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                    t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                    if isinstance(t, dict):
                        k = t.get("kind")
                        yu = int(t.get("yield_units", 0) or 0)
                        if k == "PLANT":
                            c = t.get("crop", "UNKNOWN")
                            harvest_ops_count[c] += 1
                            harvest_counts[c] += yu
                        elif k == "PASTURE":
                            an = t.get("animal", "UNKNOWN")
                            harvest_ops_count[an] += 1
                            harvest_counts[an] += yu
            
            # Market sales: compare money delta or inspect market orders
            # In kaggriculture, let's track transaction revenue
            m_orders = act.get("market") or []
            # Market prices at this step
            prices = steps[s_idx - 1][0]["observation"].get("market", {}).get("prices", {})
            for mo in m_orders:
                if isinstance(mo, list) and len(mo) >= 3 and mo[0] == "SELL":
                    item = mo[1]
                    qty = int(mo[2])
                    p_val = float(prices.get(item, 100))
                    sales_realized[item] += qty
                    revenue_realized[item] += qty * p_val

        rew = float(steps[-1][p_idx].get("reward") or 0.0)
        return {
            "reward": rew,
            "harvest_ops": dict(harvest_ops_count),
            "total_harvest_ops": sum(harvest_ops_count.values()),
            "harvested_units": dict(harvest_counts),
            "sales_realized": dict(sales_realized),
            "revenue_realized": dict(revenue_realized)
        }

    p0_res = extract_player_data(0)
    p1_res = extract_player_data(1)
    
    return {
        "seed": seed,
        "p0_type": p0_type,
        "p1_type": p1_type,
        "p0": p0_res,
        "p1": p1_res
    }

if __name__ == "__main__":
    seeds = list(range(1000, 1010))
    tasks = []
    # Seat 0 CL vs Seat 1 V2
    for s in seeds:
        tasks.append((s, "CL", "V2"))
    # Seat 0 V2 vs Seat 1 CL (fair paired evaluation)
    for s in seeds:
        tasks.append((s, "V2", "CL"))
        
    print(f"Running Direct H2H Audit ({len(tasks)} matches across {len(seeds)} seeds)...")
    results = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_h2h_match, t) for t in tasks]
        for f in as_completed(futs):
            results.append(f.result())
            
    with open("scratch/audit_h2h_exact_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    # Aggregate CL vs V2 across both seat assignments
    cl_rewards, v2_rewards = [], []
    cl_straw, v2_straw = [], []
    cl_wool, v2_wool = [], []
    cl_wheat, v2_wheat = [], []
    cl_melon, v2_melon = [], []
    cl_milk, v2_milk = [], []
    
    cl_rev_straw, v2_rev_straw = [], []
    cl_rev_wool, v2_rev_wool = [], []
    cl_rev_wheat, v2_rev_wheat = [], []
    cl_rev_melon, v2_rev_melon = [], []
    
    cl_harv_ops, v2_harv_ops = [], []
    
    for r in results:
        if r["p0_type"] == "CL":
            cl_p = r["p0"]
            v2_p = r["p1"]
        else:
            v2_p = r["p0"]
            cl_p = r["p1"]
            
        cl_rewards.append(cl_p["reward"])
        v2_rewards.append(v2_p["reward"])
        
        cl_straw.append(cl_p["harvested_units"].get("STRAWBERRY", 0))
        v2_straw.append(v2_p["harvested_units"].get("STRAWBERRY", 0))
        
        cl_wool.append(cl_p["harvested_units"].get("SHEEP", 0))
        v2_wool.append(v2_p["harvested_units"].get("SHEEP", 0))
        
        cl_wheat.append(cl_p["harvested_units"].get("WHEAT", 0))
        v2_wheat.append(v2_p["harvested_units"].get("WHEAT", 0))
        
        cl_melon.append(cl_p["harvested_units"].get("MELON", 0))
        v2_melon.append(v2_p["harvested_units"].get("MELON", 0))
        
        cl_milk.append(cl_p["harvested_units"].get("COW", 0))
        v2_milk.append(v2_p["harvested_units"].get("COW", 0))
        
        cl_rev_straw.append(cl_p["revenue_realized"].get("STRAWBERRY", 0))
        v2_rev_straw.append(v2_p["revenue_realized"].get("STRAWBERRY", 0))
        
        cl_rev_wool.append(cl_p["revenue_realized"].get("WOOL", 0))
        v2_rev_wool.append(v2_p["revenue_realized"].get("WOOL", 0))
        
        cl_rev_wheat.append(cl_p["revenue_realized"].get("WHEAT", 0))
        v2_rev_wheat.append(v2_p["revenue_realized"].get("WHEAT", 0))
        
        cl_rev_melon.append(cl_p["revenue_realized"].get("MELON", 0))
        v2_rev_melon.append(v2_p["revenue_realized"].get("MELON", 0))
        
        cl_harv_ops.append(cl_p["total_harvest_ops"])
        v2_harv_ops.append(v2_p["total_harvest_ops"])

    print("\n" + "="*80)
    print("DIRECT H2H PHYSICAL & REVENUE GAP AUDIT (20 Matches: 10 seeds x 2 seats)")
    print("="*80)
    print(f"CL Mean Reward: ${np.mean(cl_rewards):.2f} ± ${np.std(cl_rewards):.2f}")
    print(f"V2 Mean Reward: ${np.mean(v2_rewards):.2f} ± ${np.std(v2_rewards):.2f}")
    print(f"Mean H2H Margin (CL - V2): ${np.mean(cl_rewards) - np.mean(v2_rewards):.2f}")
    print(f"Win Rate: {np.mean([1 if c > v else 0 for c, v in zip(cl_rewards, v2_rewards)]) * 100:.1f}%")
    print("\nPhysical Harvested Units:")
    print(f"Strawberry: CL {np.mean(cl_straw):.1f} vs V2 {np.mean(v2_straw):.1f} | Delta (V2 - CL): {np.mean(v2_straw) - np.mean(cl_straw):+.1f} units")
    print(f"Wool:       CL {np.mean(cl_wool):.1f} vs V2 {np.mean(v2_wool):.1f} | Delta (V2 - CL): {np.mean(v2_wool) - np.mean(cl_wool):+.1f} units")
    print(f"Wheat:      CL {np.mean(cl_wheat):.1f} vs V2 {np.mean(v2_wheat):.1f} | Delta (V2 - CL): {np.mean(v2_wheat) - np.mean(cl_wheat):+.1f} units")
    print(f"Melon:      CL {np.mean(cl_melon):.1f} vs V2 {np.mean(v2_melon):.1f} | Delta (V2 - CL): {np.mean(v2_melon) - np.mean(cl_melon):+.1f} units")
    print(f"Milk:       CL {np.mean(cl_milk):.1f} vs V2 {np.mean(v2_milk):.1f} | Delta (V2 - CL): {np.mean(v2_milk) - np.mean(cl_milk):+.1f} units")
    print(f"Harvest Ops:CL {np.mean(cl_harv_ops):.1f} vs V2 {np.mean(v2_harv_ops):.1f} | Delta (V2 - CL): {np.mean(v2_harv_ops) - np.mean(cl_harv_ops):+.1f} actions")
