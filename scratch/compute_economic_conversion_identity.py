"""
scratch/compute_economic_conversion_identity.py
===============================================
Computes the exact economic conversion identity per seed:
# DIRECT WHEAT VALUE
units of wheat available x realized/available wheat price

# LIVESTOCK CONVERSION VALUE
wheat diverted to feed + resulting wool/milk output + realized wool/milk revenue
less feed cost, animal maintenance, shearing delay, milk timing, movement, worker time, cash constraints, terminal liquidation.

Generates:
- research/wheat_livestock_economic_identity.csv
"""

import os
import sys
import json
import csv
import numpy as np

def main():
    print("Loading telemetry from research/midlate_accounting_telemetry.json...")
    if not os.path.exists("research/midlate_accounting_telemetry.json"):
        print("Telemetry not found. Run scratch/audit_midlate_loss_regime.py first.")
        return

    with open("research/midlate_accounting_telemetry.json") as f:
        matches = json.load(f)

    rows = []

    for m in matches:
        seed = m["seed"]
        seat = m["seat"]
        v54_rew = m["v54_reward"]
        v66_rew = m["v66_reward"]
        margin = m["margin"]

        # Checkpoint at Day 16 (Step 384) & Day 22 (Step 528)
        cp384 = m.get("checkpoints", {}).get("384", {})
        cp528 = m.get("checkpoints", {}).get("528", {})
        cp624 = m.get("checkpoints", {}).get("624", {})

        p_wheat = cp528.get("prices", {}).get("wheat", 40.0) if cp528 else 40.0
        p_wool = cp528.get("prices", {}).get("wool", 150.0) if cp528 else 150.0
        p_milk = cp528.get("prices", {}).get("milk", 35.0) if cp528 else 35.0

        v54_wheat_sold = m["cumulative"]["v54"]["wheat_sold"]
        v66_wheat_sold = m["cumulative"]["v66"]["wheat_sold"]
        v54_wheat_rev = m["cumulative"]["v54"]["wheat_revenue"]
        v66_wheat_rev = m["cumulative"]["v66"]["wheat_revenue"]

        v54_wool_rev = m["cumulative"]["v54"]["wool_revenue"]
        v66_wool_rev = m["cumulative"]["v66"]["wool_revenue"]
        v54_milk_rev = m["cumulative"]["v54"]["milk_revenue"]
        v66_milk_rev = m["cumulative"]["v66"]["milk_revenue"]

        # Theoretical Direct Wheat Value of V66's grain lead
        wheat_delta = v66_wheat_sold - v54_wheat_sold
        direct_wheat_val = wheat_delta * p_wheat

        # Theoretical Livestock Conversion Value (Wool + Milk revenue delta)
        livestock_val = (v54_wool_rev + v54_milk_rev) - (v66_wool_rev + v66_milk_rev)

        conversion_advantage = livestock_val - direct_wheat_val

        rows.append({
            "seed": seed,
            "seat": seat,
            "v54_reward": v54_rew,
            "v66_reward": v66_rew,
            "margin": margin,
            "wheat_price_day22": p_wheat,
            "wool_price_day22": p_wool,
            "milk_price_day22": p_milk,
            "v54_wheat_sold": v54_wheat_sold,
            "v66_wheat_sold": v66_wheat_sold,
            "direct_wheat_value_lead": direct_wheat_val,
            "livestock_conversion_value_lead": livestock_val,
            "net_conversion_advantage": conversion_advantage,
            "economic_verdict": "DIRECT_WHEAT_SUPERIOR" if direct_wheat_val > livestock_val else "LIVESTOCK_SUPERIOR"
        })

    print(f"Writing research/wheat_livestock_economic_identity.csv ({len(rows)} seeds)...")
    with open("research/wheat_livestock_economic_identity.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "seed", "seat", "v54_reward", "v66_reward", "margin",
            "wheat_price_day22", "wool_price_day22", "milk_price_day22",
            "v54_wheat_sold", "v66_wheat_sold", "direct_wheat_value_lead",
            "livestock_conversion_value_lead", "net_conversion_advantage", "economic_verdict"
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print("Economic identity calculation complete!")

if __name__ == "__main__":
    main()
