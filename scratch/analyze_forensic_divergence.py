"""
scratch/analyze_forensic_divergence.py
Step-by-step divergence and micro-scheduling causal analyzer.
"""

import json
import sys

def analyze_seed_divergence(seed_str, data):
    v2_traj = data[seed_str]["v2"]["trajectory"]
    cl_traj = data[seed_str]["cl"]["trajectory"]
    v2_reward = data[seed_str]["v2"]["final_reward"]
    cl_reward = data[seed_str]["cl"]["final_reward"]
    
    print(f"\n{'='*90}")
    print(f"SEED {seed_str}: V2 = ${v2_reward:,.1f} vs CL_ARCH = ${cl_reward:,.1f} (Margin: ${cl_reward - v2_reward:,.1f})")
    print(f"{'='*90}")
    
    first_divergence = None
    divergences = []
    
    # 1. Step-by-step scan for first divergence
    for t in range(len(v2_traj)):
        v2_snap = v2_traj[t]
        cl_snap = cl_traj[t]
        
        # Compare market orders
        m_diff = (v2_snap["market_orders"] != cl_snap["market_orders"])
        # Compare farmer action
        f_diff = (v2_snap["farmer_action"] != cl_snap["farmer_action"])
        # Compare hands actions
        h_diff = (v2_snap["hands_actions"] != cl_snap["hands_actions"])
        # Compare crops
        c_diff = (v2_snap["crops"] != cl_snap["crops"])
        
        if m_diff or f_diff or h_diff or c_diff:
            if first_divergence is None:
                first_divergence = (t, v2_snap, cl_snap, m_diff, f_diff, h_diff, c_diff)
            divergences.append((t, v2_snap, cl_snap))
            
    print(f"\n[PHASE 3: FIRST DIVERGENCE IDENTIFIED AT STEP {first_divergence[0]}]")
    t, v2_s, cl_s, m_diff, f_diff, h_diff, c_diff = first_divergence
    day = t // 24
    hour = t % 24
    print(f"Step {t} (Day {day}, Hour {hour}):")
    print(f"  V2 Farmer Action:      {v2_s['farmer_action']} | Pos: {v2_s['worker_positions'][0] if v2_s['worker_positions'] else None}")
    print(f"  CL Farmer Action:      {cl_s['farmer_action']} | Pos: {cl_s['worker_positions'][0] if cl_s['worker_positions'] else None}")
    print(f"  V2 Hands Actions:      {v2_s['hands_actions']}")
    print(f"  CL Hands Actions:      {cl_s['hands_actions']}")
    print(f"  V2 Market Orders:      {v2_s['market_orders']}")
    print(f"  CL Market Orders:      {cl_s['market_orders']}")
    print(f"  V2 Money: ${v2_s['money']:,.1f} | CL Money: ${cl_s['money']:,.1f}")
    
    # Trace first 10 steps of divergence
    print("\n--- FIRST 10 TURNS CHRONOLOGY (Steps 0 to 9) ---")
    for step in range(min(10, len(v2_traj))):
        v_s = v2_traj[step]
        c_s = cl_traj[step]
        print(f"Step {step:2d} (H{step%24:2d}):")
        print(f"   V2: FarmAct={v_s['farmer_action']} HandsAct={v_s['hands_actions']} | Market={v_s['market_orders'][:2]}")
        print(f"   CL: FarmAct={c_s['farmer_action']} HandsAct={c_s['hands_actions']} | Market={c_s['market_orders'][:2]}")
        print(f"   V2 Crops: {len(v_s['crops'])} plants | CL Crops: {len(c_s['crops'])} plants")
        print(f"   V2 Pastures: {len(v_s['pastures'])} | CL Pastures: {len(c_s['pastures'])}")


def analyze_melon_wave(seed_str, data):
    v2_traj = data[seed_str]["v2"]["trajectory"]
    cl_traj = data[seed_str]["cl"]["trajectory"]
    
    print(f"\n{'='*90}")
    print(f"PHASE 5: THE DAY 10-11 MELON WAVE FORENSIC RECONSTRUCTION (SEED {seed_str})")
    print(f"{'='*90}")
    
    # Trace Melons in V2
    print("\n[V2 MELON LIFECYCLE (Days 0 to 12)]")
    v2_melon_tiles = set()
    for t in range(len(v2_traj)):
        for pos, c in v2_traj[t]["crops"].items():
            if c["crop"] == "MELON" and c["planted_day"] == 0:
                v2_melon_tiles.add(pos)
                
    print(f"V2 Day-0 Melon Tiles ({len(v2_melon_tiles)}): {sorted(list(v2_melon_tiles))}")
    
    for day in range(13):
        step_noon = day * 24 + 12
        if step_noon >= len(v2_traj): break
        v_s = v2_traj[step_noon]
        c_s = cl_traj[step_noon]
        
        v_melons = {pos: c for pos, c in v_s["crops"].items() if c["crop"] == "MELON" and c["planted_day"] == 0}
        c_melons = {pos: c for pos, c in c_s["crops"].items() if c["crop"] == "MELON" and c["planted_day"] == 0}
        
        v_yields = [c["yield_units"] for c in v_melons.values()]
        c_yields = [c["yield_units"] for c in c_melons.values()]
        
        v_watered = sum(1 for c in v_melons.values() if c["watered_today"])
        c_watered = sum(1 for c in c_melons.values() if c["watered_today"])
        
        v_shed_melon = v_s["shed"].get("MELON", 0)
        c_shed_melon = c_s["shed"].get("MELON", 0)
        
        print(f"Day {day:2d} (Step {step_noon:3d}):")
        print(f"  V2: Melons Active={len(v_melons)} | Watered={v_watered}/{len(v_melons)} | Avg Yield={sum(v_yields)/max(1,len(v_yields)):.1f} | Max Yield={max(v_yields) if v_yields else 0} | Shed Melons={v_shed_melon} | Money=${v_s['money']:,.1f}")
        print(f"  CL: Melons Active={len(c_melons)} | Watered={c_watered}/{len(c_melons)} | Avg Yield={sum(c_yields)/max(1,len(c_yields)):.1f} | Max Yield={max(c_yields) if c_yields else 0} | Shed Melons={c_shed_melon} | Money=${c_s['money']:,.1f}")
        

def analyze_worker_utilization(seed_str, data):
    v2_traj = data[seed_str]["v2"]["trajectory"]
    cl_traj = data[seed_str]["cl"]["trajectory"]
    
    print(f"\n{'='*90}")
    print(f"PHASE 8: WORKER UTILIZATION & ACTION AUDIT (SEED {seed_str})")
    print(f"{'='*90}")
    
    def compute_stats(traj):
        stats = {
            "total_worker_steps": 0,
            "moves": 0,
            "passes": 0,
            "water": 0,
            "plant": 0,
            "harvest": 0,
            "feed": 0,
            "care": 0,
            "build": 0,
            "dig": 0,
            "drop": 0,
            "pickup": 0,
            "fertilizer_collect": 0,
            "productive_steps": 0
        }
        
        for snap in traj:
            all_acts = [snap["farmer_action"]] + snap["hands_actions"]
            for act in all_acts:
                stats["total_worker_steps"] += 1
                if not act or len(act) == 0:
                    stats["passes"] += 1
                    continue
                op = act[0]
                if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    stats["moves"] += 1
                elif op == "PASS":
                    stats["passes"] += 1
                elif op == "WATER":
                    stats["water"] += 1
                    stats["productive_steps"] += 1
                elif op == "PLANT":
                    stats["plant"] += 1
                    stats["productive_steps"] += 1
                elif op == "HARVEST":
                    stats["harvest"] += 1
                    stats["productive_steps"] += 1
                elif op == "FEED":
                    stats["feed"] += 1
                    stats["productive_steps"] += 1
                elif op == "CARE":
                    stats["care"] += 1
                    stats["productive_steps"] += 1
                elif op == "BUILD_PASTURE":
                    stats["build"] += 1
                    stats["productive_steps"] += 1
                elif op == "DIG":
                    stats["dig"] += 1
                    stats["productive_steps"] += 1
                elif op == "DROP":
                    stats["drop"] += 1
                    stats["productive_steps"] += 1
                elif op == "PICKUP":
                    stats["pickup"] += 1
                    stats["productive_steps"] += 1
                elif op == "COLLECT_FERTILIZER":
                    stats["fertilizer_collect"] += 1
                    stats["productive_steps"] += 1
                else:
                    stats["passes"] += 1
                    
        stats["productive_ratio"] = stats["productive_steps"] / max(1, stats["total_worker_steps"])
        stats["move_ratio"] = stats["moves"] / max(1, stats["total_worker_steps"])
        stats["idle_ratio"] = stats["passes"] / max(1, stats["total_worker_steps"])
        return stats

    v2_stats = compute_stats(v2_traj)
    cl_stats = compute_stats(cl_traj)
    
    print(f"{'Metric':<25} | {'Frozen V2':<15} | {'Closed-Loop Arch':<15} | {'Difference':<15}")
    print(f"{'-'*75}")
    for k in v2_stats:
        if "ratio" in k:
            print(f"{k:<25} | {v2_stats[k]*100:13.2f}% | {cl_stats[k]*100:13.2f}% | {(cl_stats[k]-v2_stats[k])*100:+13.2f}%")
        else:
            print(f"{k:<25} | {v2_stats[k]:14,d} | {cl_stats[k]:14,d} | {cl_stats[k]-v2_stats[k]:+14,d}")


def analyze_revenue_sources(seed_str, data):
    v2_traj = data[seed_str]["v2"]["trajectory"]
    cl_traj = data[seed_str]["cl"]["trajectory"]
    
    print(f"\n{'='*90}")
    print(f"REVENUE & COMMODITY VOLUME BREAKDOWN (SEED {seed_str})")
    print(f"{'='*90}")
    
    def compute_sales(traj):
        sales = {}
        for snap in traj:
            for o in snap["market_orders"]:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    item = o[1]
                    qty = int(o[2] or 0)
                    sales[item] = sales.get(item, 0) + qty
        return sales

    v2_sales = compute_sales(v2_traj)
    cl_sales = compute_sales(cl_traj)
    
    all_items = sorted(list(set(list(v2_sales.keys()) + list(cl_sales.keys()))))
    print(f"{'Commodity':<15} | {'V2 Sold Units':<15} | {'CL Sold Units':<15} | {'Delta Units':<15}")
    print(f"{'-'*65}")
    for item in all_items:
        v_qty = v2_sales.get(item, 0)
        c_qty = cl_sales.get(item, 0)
        print(f"{item:<15} | {v_qty:14,d} | {c_qty:14,d} | {c_qty - v_qty:+14,d}")


def main():
    with open("scratch/forensic_telemetry_dump.json", "r") as f:
        data = json.load(f)
        
    for seed in ["215620170", "108"]:
        analyze_seed_divergence(seed, data)
        analyze_melon_wave(seed, data)
        analyze_revenue_sources(seed, data)
        analyze_worker_utilization(seed, data)


if __name__ == "__main__":
    main()
