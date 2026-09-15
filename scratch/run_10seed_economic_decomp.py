"""
Detailed 10-Seed Economic Aggregator
Prints clean, complete tabular decomposition of revenues, costs, and product yields.
"""

import sys
import os
import json
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scratch.economic_forensic_auditor import analyze_match_trace, v2_agent, cl_agent

def run_batch_study(seeds=list(range(1000, 1010))):
    v2_list = []
    cl_list = []
    
    for s in seeds:
        v2_list.append(analyze_match_trace(v2_agent, "Frozen V2", seed=s))
        cl_list.append(analyze_match_trace(cl_agent, "CL-Coordinated-V1", seed=s))
        
    v2_r = [x['final_reward'] for x in v2_list]
    cl_r = [x['final_reward'] for x in cl_list]
    margins = [v - c for v, c in zip(v2_r, cl_r)]
    
    print("=" * 95)
    print("10-SEED ECONOMIC FORENSIC BENCHMARK (Seeds 1000-1009 vs Starter)")
    print("=" * 95)
    print(f"Frozen V2 Mean Reward:        ${np.mean(v2_r):10,.2f} +/- ${np.std(v2_r):8,.2f}")
    print(f"CL-Coordinated-V1 Mean Reward: ${np.mean(cl_r):10,.2f} +/- ${np.std(cl_r):8,.2f}")
    print(f"Mean Advantage (V2 - CL):     +${np.mean(margins):10,.2f} ({(np.mean(v2_r)/np.mean(cl_r)-1)*100:+.1f}%)")
    print("-" * 95)
    
    # Financial Inflows and Outflows
    v2_inflow = [x['gross_cash_inflow'] for x in v2_list]
    cl_inflow = [x['gross_cash_inflow'] for x in cl_list]
    v2_outflow = [x['gross_cash_outflow'] for x in v2_list]
    cl_outflow = [x['gross_cash_outflow'] for x in cl_list]
    
    print(f"Gross Cash Inflow:  V2=${np.mean(v2_inflow):10,.2f} | CL=${np.mean(cl_inflow):10,.2f} | Delta=+${np.mean(v2_inflow)-np.mean(cl_inflow):10,.2f}")
    print(f"Gross Cash Outflow: V2=${np.mean(v2_outflow):10,.2f} | CL=${np.mean(cl_outflow):10,.2f} | Delta=+${np.mean(v2_outflow)-np.mean(cl_outflow):10,.2f}")
    print("-" * 95)
    
    print(f"{'PRODUCT':<15} | {'V2 UNITS':<10} | {'CL UNITS':<10} | {'UNIT DELTA':<10} | {'V2 REV ($)':<12} | {'CL REV ($)':<12} | {'REV DELTA ($)':<12}")
    print("-" * 95)
    items = ['STRAWBERRY', 'MILK', 'WOOL', 'MELON', 'FERTILIZER', 'WHEAT', 'TOMATO', 'CARROT', 'EGG']
    for it in items:
        v_u = np.mean([x['units_sold'].get(it, 0) for x in v2_list])
        c_u = np.mean([x['units_sold'].get(it, 0) for x in cl_list])
        v_rev = np.mean([x['inflows'].get(it, 0.0) for x in v2_list])
        c_rev = np.mean([x['inflows'].get(it, 0.0) for x in cl_list])
        if v_u > 0 or c_u > 0:
            print(f"{it:<15} | {v_u:10.1f} | {c_u:10.1f} | {v_u - c_u:+10.1f} | {v_rev:12,.1f} | {c_rev:12,.1f} | {v_rev - c_rev:+12,.1f}")
            
    print("-" * 95)
    print("WORKERS & EFFICIENCY:")
    v2_w = np.mean([x['final_workers'] for x in v2_list])
    cl_w = np.mean([x['final_workers'] for x in cl_list])
    v2_aw = np.mean([x['mean_workers'] for x in v2_list])
    cl_aw = np.mean([x['mean_workers'] for x in cl_list])
    print(f"Final Workers: V2={v2_w:4.1f} vs CL={cl_w:4.1f} | Active Avg Workers: V2={v2_aw:4.1f} vs CL={cl_aw:4.1f}")
    
    # Save structured summary to json
    summary = {
        "v2_mean_reward": float(np.mean(v2_r)),
        "cl_mean_reward": float(np.mean(cl_r)),
        "margin": float(np.mean(margins)),
        "v2_inflow": float(np.mean(v2_inflow)),
        "cl_inflow": float(np.mean(cl_inflow)),
        "v2_outflow": float(np.mean(v2_outflow)),
        "cl_outflow": float(np.mean(cl_outflow)),
        "items": {}
    }
    for it in items:
        summary["items"][it] = {
            "v2_units": float(np.mean([x['units_sold'].get(it, 0) for x in v2_list])),
            "cl_units": float(np.mean([x['units_sold'].get(it, 0) for x in cl_list])),
            "v2_rev": float(np.mean([x['inflows'].get(it, 0.0) for x in v2_list])),
            "cl_rev": float(np.mean([x['inflows'].get(it, 0.0) for x in cl_list])),
        }
    with open("scratch/economic_decomposition_10seeds.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved results to scratch/economic_decomposition_10seeds.json")

if __name__ == "__main__":
    run_batch_study()
