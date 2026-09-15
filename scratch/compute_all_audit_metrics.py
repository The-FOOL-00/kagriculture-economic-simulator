"""
Compute All Audit Metrics from Deep Telemetry JSON
Steps 2, 3, 4, 6, 7, 11, 12, 13, 14, 15
"""
import json
import numpy as np
from collections import defaultdict
import os

def dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def compute_spatial_metrics(coords):
    n = len(coords)
    if n == 0:
        return {
            "count": 0,
            "mean_pairwise": 0.0,
            "median_pairwise": 0.0,
            "max_pairwise": 0.0,
            "mean_nn": 0.0,
            "median_nn": 0.0,
            "bbox_area": 0,
            "cc_count": 0,
            "largest_cc_size": 0
        }
    if n == 1:
        return {
            "count": 1,
            "mean_pairwise": 0.0,
            "median_pairwise": 0.0,
            "max_pairwise": 0.0,
            "mean_nn": 0.0,
            "median_nn": 0.0,
            "bbox_area": 1,
            "cc_count": 1,
            "largest_cc_size": 1
        }
    
    pw_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            pw_dists.append(dist(coords[i], coords[j]))
            
    nn_dists = []
    for i in range(n):
        min_d = min(dist(coords[i], coords[j]) for j in range(n) if i != j)
        nn_dists.append(min_d)
        
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    bbox_area = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
    
    adj = defaultdict(list)
    coord_set = set(coords)
    for c in coords:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nb = (c[0] + dx, c[1] + dy)
            if nb in coord_set:
                adj[c].append(nb)
                
    visited = set()
    cc_sizes = []
    for c in coords:
        if c not in visited:
            comp = []
            queue = [c]
            visited.add(c)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for nb in adj[curr]:
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            cc_sizes.append(len(comp))
            
    return {
        "count": n,
        "mean_pairwise": float(np.mean(pw_dists)),
        "median_pairwise": float(np.median(pw_dists)),
        "max_pairwise": float(np.max(pw_dists)),
        "mean_nn": float(np.mean(nn_dists)),
        "median_nn": float(np.median(nn_dists)),
        "bbox_area": int(bbox_area),
        "cc_count": len(cc_sizes),
        "largest_cc_size": max(cc_sizes) if cc_sizes else 0
    }

def analyze_all(json_path="scratch/deep_telemetry_seeds1000_1009.json"):
    with open(json_path, "r") as f:
        data = json.load(f)

    agents = ["CL", "V2"]
    seeds = sorted(list(data["CL"].keys()), key=lambda x: int(x))

    print("================================================================================")
    print("SECTION 1 & 4: REWARDS & HARVEST CONTROLS (SEEDS 1000-1009)")
    print("================================================================================")
    header = f"{'Seed':<6} | {'CL Rew':<9} {'V2 Rew':<9} | {'CL Straw':<8} {'V2 Straw':<8} {'Delta':<6} | {'CL Bush':<7} {'V2 Bush':<7} | {'CL Y/Bush':<9} {'V2 Y/Bush':<9}"
    print(header)
    print("-" * len(header))

    cl_rewards, v2_rewards = [], []
    cl_straws, v2_straws = [], []
    cl_bushes, v2_bushes = [], []
    cl_ypb, v2_ypb = [], []

    for s in seeds:
        cl_r = data["CL"][s]["reward"]
        v2_r = data["V2"][s]["reward"]
        cl_st = data["CL"][s]["crop_harvest_totals"].get("STRAWBERRY", 0)
        v2_st = data["V2"][s]["crop_harvest_totals"].get("STRAWBERRY", 0)
        cl_b = len(data["CL"][s]["bushes"])
        v2_b = len(data["V2"][s]["bushes"])
        cl_y = cl_st / cl_b if cl_b > 0 else 0
        v2_y = v2_st / v2_b if v2_b > 0 else 0

        cl_rewards.append(cl_r)
        v2_rewards.append(v2_r)
        cl_straws.append(cl_st)
        v2_straws.append(v2_st)
        cl_bushes.append(cl_b)
        v2_bushes.append(v2_b)
        cl_ypb.append(cl_y)
        v2_ypb.append(v2_y)

        print(f"{s:<6} | {cl_r:<9.0f} {v2_r:<9.0f} | {cl_st:<8} {v2_st:<8} {v2_st - cl_st:<+6} | {cl_b:<7} {v2_b:<7} | {cl_y:<9.2f} {v2_y:<9.2f}")

    print("-" * len(header))
    print(f"MEAN   | {np.mean(cl_rewards):<9.1f} {np.mean(v2_rewards):<9.1f} | {np.mean(cl_straws):<8.1f} {np.mean(v2_straws):<8.1f} {np.mean(v2_straws)-np.mean(cl_straws):<+6.1f} | {np.mean(cl_bushes):<7.1f} {np.mean(v2_bushes):<7.1f} | {np.mean(cl_ypb):<9.2f} {np.mean(v2_ypb):<9.2f}")

    print("\n================================================================================")
    print("SECTION 2: PLANTING CURVES & TIMING (DAY 0 TO 29)")
    print("================================================================================")
    # Count plantings by day for Strawberry, Melon, Total, Succession
    cl_straw_by_day = defaultdict(list)
    v2_straw_by_day = defaultdict(list)
    cl_melon_by_day = defaultdict(list)
    v2_melon_by_day = defaultdict(list)
    cl_succ_by_day = defaultdict(list)
    v2_succ_by_day = defaultdict(list)
    cl_total_by_day = defaultdict(list)
    v2_total_by_day = defaultdict(list)

    cl_straw_plant_days = []
    v2_straw_plant_days = []
    cl_melon_plant_days = []
    v2_melon_plant_days = []

    for s in seeds:
        for a, s_by_d, m_by_d, succ_by_d, tot_by_d, s_days, m_days in [
            ("CL", cl_straw_by_day, cl_melon_by_day, cl_succ_by_day, cl_total_by_day, cl_straw_plant_days, cl_melon_plant_days),
            ("V2", v2_straw_by_day, v2_melon_by_day, v2_succ_by_day, v2_total_by_day, v2_straw_plant_days, v2_melon_plant_days)
        ]:
            daily_s = defaultdict(int)
            daily_m = defaultdict(int)
            daily_succ = defaultdict(int)
            daily_tot = defaultdict(int)
            for p in data[a][s]["plant_events"]:
                d = p["day"]
                daily_tot[d] += 1
                if p["is_succession"]:
                    daily_succ[d] += 1
                if p["crop"] == "STRAWBERRY":
                    daily_s[d] += 1
                    s_days.append(d)
                elif p["crop"] == "MELON":
                    daily_m[d] += 1
                    m_days.append(d)
            for d in range(30):
                s_by_d[d].append(daily_s[d])
                m_by_d[d].append(daily_m[d])
                succ_by_d[d].append(daily_succ[d])
                tot_by_d[d].append(daily_tot[d])

    print(f"{'Day':<4} | {'CL Straw':<10} {'V2 Straw':<10} | {'CL Melon':<10} {'V2 Melon':<10} | {'CL Succ':<9} {'V2 Succ':<9} | {'CL Tot':<8} {'V2 Tot':<8}")
    print("-" * 85)
    for d in range(30):
        print(f"{d:<4} | {np.mean(cl_straw_by_day[d]):<10.2f} {np.mean(v2_straw_by_day[d]):<10.2f} | {np.mean(cl_melon_by_day[d]):<10.2f} {np.mean(v2_melon_by_day[d]):<10.2f} | {np.mean(cl_succ_by_day[d]):<9.2f} {np.mean(v2_succ_by_day[d]):<9.2f} | {np.mean(cl_total_by_day[d]):<8.2f} {np.mean(v2_total_by_day[d]):<8.2f}")

    print("\nTIMING SUMMARY:")
    print(f"Strawberry Mean Planting Day: CL={np.mean(cl_straw_plant_days):.2f} (std={np.std(cl_straw_plant_days):.2f}, med={np.median(cl_straw_plant_days):.1f}) vs V2={np.mean(v2_straw_plant_days):.2f} (std={np.std(v2_straw_plant_days):.2f}, med={np.median(v2_straw_plant_days):.1f})")
    print(f"Melon Mean Planting Day:      CL={np.mean(cl_melon_plant_days):.2f} (std={np.std(cl_melon_plant_days):.2f}, med={np.median(cl_melon_plant_days):.1f}) vs V2={np.mean(v2_melon_plant_days):.2f} (std={np.std(v2_melon_plant_days):.2f}, med={np.median(v2_melon_plant_days):.1f})")

    # Fraction planted on Days 11-13
    cl_s_11_13 = sum(1 for d in cl_straw_plant_days if 11 <= d <= 13) / len(cl_straw_plant_days) if cl_straw_plant_days else 0
    v2_s_11_13 = sum(1 for d in v2_straw_plant_days if 11 <= d <= 13) / len(v2_straw_plant_days) if v2_straw_plant_days else 0
    cl_m_11_13 = sum(1 for d in cl_melon_plant_days if 11 <= d <= 13) / len(cl_melon_plant_days) if cl_melon_plant_days else 0
    v2_m_11_13 = sum(1 for d in v2_melon_plant_days if 11 <= d <= 13) / len(v2_melon_plant_days) if v2_melon_plant_days else 0

    print(f"Fraction Strawberry Planted Days 11-13: CL={cl_s_11_13*100:.1f}% vs V2={v2_s_11_13*100:.1f}%")
    print(f"Fraction Melon Planted Days 11-13:      CL={cl_m_11_13*100:.1f}% vs V2={v2_m_11_13*100:.1f}%")

    print("\n================================================================================")
    print("SECTION 3: SPATIAL DENSITY AUDIT (COORDINATE METRICS)")
    print("================================================================================")
    # Collect coordinates for each seed
    metrics_straw = {"CL": defaultdict(list), "V2": defaultdict(list)}
    metrics_melon = {"CL": defaultdict(list), "V2": defaultdict(list)}
    metrics_combo = {"CL": defaultdict(list), "V2": defaultdict(list)}

    for s in seeds:
        for a in ["CL", "V2"]:
            s_coords = [p["coordinate"] for p in data[a][s]["plant_events"] if p["crop"] == "STRAWBERRY"]
            m_coords = [p["coordinate"] for p in data[a][s]["plant_events"] if p["crop"] == "MELON"]
            c_coords = s_coords + m_coords

            sm = compute_spatial_metrics([tuple(c) for c in s_coords])
            mm = compute_spatial_metrics([tuple(c) for c in m_coords])
            cm = compute_spatial_metrics([tuple(c) for c in c_coords])

            for k, v in sm.items(): metrics_straw[a][k].append(v)
            for k, v in mm.items(): metrics_melon[a][k].append(v)
            for k, v in cm.items(): metrics_combo[a][k].append(v)

    print(f"{'Crop Set':<12} | {'Metric':<18} | {'CL Mean':<10} {'V2 Mean':<10} {'Ratio (V2/CL)':<14}")
    print("-" * 65)
    for name, m_dict in [("STRAWBERRY", metrics_straw), ("MELON", metrics_melon), ("COMBO (S+M)", metrics_combo)]:
        for metric in ["mean_pairwise", "median_pairwise", "mean_nn", "median_nn", "max_pairwise", "bbox_area", "cc_count", "largest_cc_size"]:
            cl_val = np.mean(m_dict["CL"][metric])
            v2_val = np.mean(m_dict["V2"][metric])
            ratio = v2_val / cl_val if cl_val > 0 else 0
            print(f"{name:<12} | {metric:<18} | {cl_val:<10.2f} {v2_val:<10.2f} {ratio:<14.2f}")
        print("-" * 65)

    print("\n================================================================================")
    print("SECTION 6 & 7: WATERING TRAVEL & EFFICIENCY AUDIT")
    print("================================================================================")
    cl_trav_w = [data["CL"][s]["mean_travel_water"] for s in seeds]
    v2_trav_w = [data["V2"][s]["mean_travel_water"] for s in seeds]
    cl_trav_sw = [data["CL"][s]["mean_travel_straw_water"] for s in seeds]
    v2_trav_sw = [data["V2"][s]["mean_travel_straw_water"] for s in seeds]

    print(f"Mean Travel Dist per Water Action:       CL={np.mean(cl_trav_w):.2f} vs V2={np.mean(v2_trav_w):.2f} (Delta={np.mean(v2_trav_w)-np.mean(cl_trav_w):+.2f})")
    print(f"Mean Travel Dist per Strawberry Water:   CL={np.mean(cl_trav_sw):.2f} vs V2={np.mean(v2_trav_sw):.2f} (Delta={np.mean(v2_trav_sw)-np.mean(cl_trav_sw):+.2f})")

    # Strawberry watering coverage & production-day synchronization
    cl_prod_day_water = []
    v2_prod_day_water = []
    cl_off_day_water = []
    v2_off_day_water = []
    cl_total_water_ticks = []
    v2_total_water_ticks = []

    for s in seeds:
        for b in data["CL"][s]["bushes"].values():
            cl_prod_day_water.append(b["water_on_prod_days"])
            cl_off_day_water.append(b["water_on_off_days"])
            cl_total_water_ticks.append(b["water_ticks"])
        for b in data["V2"][s]["bushes"].values():
            v2_prod_day_water.append(b["water_on_prod_days"])
            v2_off_day_water.append(b["water_on_off_days"])
            v2_total_water_ticks.append(b["water_ticks"])

    print(f"Watering per Bush (Total Ticks):         CL={np.mean(cl_total_water_ticks):.2f} vs V2={np.mean(v2_total_water_ticks):.2f}")
    print(f"Watering per Bush on Production Days:    CL={np.mean(cl_prod_day_water):.2f} vs V2={np.mean(v2_prod_day_water):.2f} (Max possible=4)")
    print(f"Watering per Bush on Off-Days:           CL={np.mean(cl_off_day_water):.2f} vs V2={np.mean(v2_off_day_water):.2f}")

    print("\n================================================================================")
    print("SECTION 11, 12, 13, 14, 15: LIFECYCLE, HARVEST LATENCY, FERTILIZER & CONFOUNDS")
    print("================================================================================")
    # Fertilizer
    cl_fert_frac = np.mean([sum(1 for b in data["CL"][s]["bushes"].values() if b["fertilized_at_least_once"]) / len(data["CL"][s]["bushes"]) for s in seeds])
    v2_fert_frac = np.mean([sum(1 for b in data["V2"][s]["bushes"].values() if b["fertilized_at_least_once"]) / len(data["V2"][s]["bushes"]) for s in seeds])
    print(f"Fraction of Bushes Fertilized:           CL={cl_fert_frac*100:.1f}% vs V2={v2_fert_frac*100:.1f}%")

    # Harvest latency / mature steps
    cl_steps_gt_0 = np.mean([np.mean([b["steps_with_yield_gt_0"] for b in data["CL"][s]["bushes"].values()]) for s in seeds])
    v2_steps_gt_0 = np.mean([np.mean([b["steps_with_yield_gt_0"] for b in data["V2"][s]["bushes"].values()]) for s in seeds])
    cl_steps_cap_4 = np.mean([np.mean([b["steps_at_capacity_4"] for b in data["CL"][s]["bushes"].values()]) for s in seeds])
    v2_steps_cap_4 = np.mean([np.mean([b["steps_at_capacity_4"] for b in data["V2"][s]["bushes"].values()]) for s in seeds])

    print(f"Mean Steps Bush Sits With Yield > 0:     CL={cl_steps_gt_0:.1f} vs V2={v2_steps_gt_0:.1f}")
    print(f"Mean Steps Bush Sits Capped At 4:        CL={cl_steps_cap_4:.1f} vs V2={v2_steps_cap_4:.1f}")

    # Cash and workers at strawberry planting
    cl_cash_at_plant = []
    v2_cash_at_plant = []
    cl_workers_at_plant = []
    v2_workers_at_plant = []
    cl_cows_at_plant = []
    v2_cows_at_plant = []
    cl_sheep_at_plant = []
    v2_sheep_at_plant = []

    for s in seeds:
        for p in data["CL"][s]["plant_events"]:
            if p["crop"] == "STRAWBERRY":
                cl_cash_at_plant.append(p["cash_before"])
                cl_workers_at_plant.append(p["num_workers"])
                cl_cows_at_plant.append(p["cow_count"])
                cl_sheep_at_plant.append(p["sheep_count"])
        for p in data["V2"][s]["plant_events"]:
            if p["crop"] == "STRAWBERRY":
                v2_cash_at_plant.append(p["cash_before"])
                v2_workers_at_plant.append(p["num_workers"])
                v2_cows_at_plant.append(p["cow_count"])
                v2_sheep_at_plant.append(p["sheep_count"])

    print(f"Cash immediately before Straw Planting:  CL=${np.mean(cl_cash_at_plant):.1f} vs V2=${np.mean(v2_cash_at_plant):.1f}")
    print(f"Workers available at Straw Planting:     CL={np.mean(cl_workers_at_plant):.2f} vs V2={np.mean(v2_workers_at_plant):.2f}")
    print(f"Cows present at Straw Planting:          CL={np.mean(cl_cows_at_plant):.2f} vs V2={np.mean(v2_cows_at_plant):.2f}")
    print(f"Sheep present at Straw Planting:         CL={np.mean(cl_sheep_at_plant):.2f} vs V2={np.mean(v2_sheep_at_plant):.2f}")

if __name__ == "__main__":
    analyze_all()
