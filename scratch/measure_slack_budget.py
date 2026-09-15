"""
SLACK BUDGET INSTRUMENTATION HARNESS
Measures at every step t in [0, 719]:
A. Unused worker action capacity (PASS actions)
B. Unused market-order capacity (10 - len(market))
C. Shed free capacity (100 - total_shed) & headroom to 96
D. Spare land (unlocked tiles that are None)
E. Cash & liquidity headroom vs mandatory obligations
Across Discovery seeds 50000-50049.
"""
import os
import sys
import json
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2

def run_slack_budget_audit(seeds):
    # Aggregators by day (0 to 29)
    day_passes = defaultdict(list)
    day_worker_counts = defaultdict(list)
    day_free_orders = defaultdict(list)
    day_free_shed = defaultdict(list)
    day_empty_tiles = defaultdict(list)
    day_cash = defaultdict(list)
    empty_tile_coords_by_day = defaultdict(lambda: defaultdict(int))
    
    for s in seeds:
        agent0 = ClosedLoopAgentV2()
        agent1 = ClosedLoopAgentV2()
        g = kagsim.Game(s)
        
        step = 0
        while not g.done:
            obs0 = g.observe(0)
            day = step // 24
            hour = step % 24
            
            # 1. Measure land state
            farm0 = obs0['farms'][0]
            empty_count = 0
            for y in range(10):
                for x in range(10):
                    t = farm0['tiles'][y][x]
                    if t is None:
                        empty_count += 1
                        empty_tile_coords_by_day[day][(x, y)] += 1
            day_empty_tiles[day].append(empty_count)
            
            # 2. Measure shed state
            shed = obs0['private']['shed']
            total_shed = sum(shed.values())
            day_free_shed[day].append(100 - total_shed)
            
            # 3. Measure cash
            cash = farm0['money']
            day_cash[day].append(cash)
            
            # 4. Get act0
            act0 = agent0.act(obs0)
            
            # 5. Measure worker actions and PASS
            f_act = act0.get('farmer', ['PASS'])
            h_acts = act0.get('hands', [])
            all_unit_acts = [f_act] + h_acts
            worker_count = len(all_unit_acts)
            passes = sum(1 for a in all_unit_acts if a and a[0] == 'PASS')
            
            day_passes[day].append(passes)
            day_worker_counts[day].append(worker_count)
            
            # 6. Measure market order capacity
            m_orders = act0.get('market', [])
            free_orders = max(0, 10 - len(m_orders))
            day_free_orders[day].append(free_orders)
            
            # Step game
            act1 = agent1.act(g.observe(1))
            g.step(act0, act1)
            step += 1
            
    # Compute summary metrics
    days = list(range(30))
    summary = {
        "num_seeds": len(seeds),
        "days": {}
    }
    
    for d in days:
        passes_arr = day_passes[d]
        workers_arr = day_worker_counts[d]
        free_orders_arr = day_free_orders[d]
        free_shed_arr = day_free_shed[d]
        empty_tiles_arr = day_empty_tiles[d]
        cash_arr = day_cash[d]
        
        summary["days"][d] = {
            "mean_workers": round(sum(workers_arr) / len(workers_arr), 1),
            "mean_passes_per_step": round(sum(passes_arr) / len(passes_arr), 2),
            "total_passes_per_day": round(sum(passes_arr) / (len(seeds) * 1.0), 1),
            "min_passes_in_day": min(sum(day_passes[d][i*24:(i+1)*24]) for i in range(len(seeds))),
            "max_passes_in_day": max(sum(day_passes[d][i*24:(i+1)*24]) for i in range(len(seeds))),
            "mean_free_orders_per_step": round(sum(free_orders_arr) / len(free_orders_arr), 2),
            "mean_free_shed": round(sum(free_shed_arr) / len(free_shed_arr), 1),
            "min_free_shed": min(free_shed_arr),
            "mean_empty_tiles": round(sum(empty_tiles_arr) / len(empty_tiles_arr), 2),
            "max_empty_tiles": max(empty_tiles_arr),
            "mean_cash": round(sum(cash_arr) / len(cash_arr), 1)
        }
        
    out_path = os.path.join(BASE_DIR, "scratch", "slack_budget_summary.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Slack budget summary written to {out_path}")
    
    # Print formatted table for key days
    print("\n" + "=" * 105)
    print(f"{'Day':4s} | {'Workers':7s} | {'Passes/Day':10s} | {'Min Pass/D':10s} | {'Free Orders':11s} | {'Free Shed':9s} | {'Min Free Shed':13s} | {'Empty Tiles':11s} | {'Cash':10s}")
    print("-" * 105)
    for d in [0, 5, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]:
        row = summary["days"][d]
        print(f"{d:4d} | {row['mean_workers']:7.1f} | {row['total_passes_per_day']:10.1f} | {row['min_passes_in_day']:10d} | {row['mean_free_orders_per_step']:11.2f} | {row['mean_free_shed']:9.1f} | {row['min_free_shed']:13d} | {row['mean_empty_tiles']:11.2f} | ${row['mean_cash']:9.0f}")
    print("=" * 105)

if __name__ == "__main__":
    discovery_seeds = list(range(50000, 50050))
    run_slack_budget_audit(discovery_seeds)
