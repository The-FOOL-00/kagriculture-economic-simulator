import json
import numpy as np
from collections import defaultdict

def analyze_bridge():
    with open("scratch/50seed_hostile_audit_raw.json") as f:
        data = json.load(f)

    # 10-seed analysis (seeds 1000-1009)
    seeds10 = [str(s) for s in range(1000, 1010)]
    
    print("=" * 80)
    print("PHASE 3: EXACT ACCOUNTING BRIDGE ACROSS SEEDS 1000-1009 (N=10)")
    print("=" * 80)
    
    items = ["STRAWBERRY", "MILK", "WOOL", "MELON", "WHEAT", "FERTILIZER", "EGG"]
    exp_keys = ["exp_animals", "exp_seeds", "exp_feed", "exp_hires"]

    for s in seeds10:
        base = data["A_Baseline"][s]
        gated = data["B_Gated_M1"][s]

        d_rew = gated["reward"] - base["reward"]
        d_tot_rev = gated["total_rev"] - base["total_rev"]
        d_tot_exp = gated["total_exp"] - base["total_exp"]

        print(f"\nSeed {s}: Delta Reward = ${d_rew:>+10,.2f}")
        print(f"  Delta Total Rev = ${d_tot_rev:>+10,.2f}, Delta Total Exp = ${d_tot_exp:>+10,.2f}, Check: ${d_tot_rev - d_tot_exp:>+10,.2f}")
        
        # Itemized rev
        for it in items:
            br = base["rev_by_item"].get(it, 0.0)
            gr = gated["rev_by_item"].get(it, 0.0)
            bq = base["qty_sold"].get(it, 0)
            gq = gated["qty_sold"].get(it, 0)
            bp = br / bq if bq > 0 else 0.0
            gp = gr / gq if gq > 0 else 0.0
            if abs(gr - br) > 100:
                print(f"    {it:<11}: Rev Delta=${gr - br:>+9,.2f} | Qty: Base={bq} Gated={gq} (d={gq-bq:>+2}) | AvgP: Base=${bp:.1f} Gated=${gp:.1f} (d=${gp-bp:>+5.1f})")

    # Means over 10 seeds
    print("\n" + "=" * 80)
    print("10-SEED AVERAGE ACCOUNTING BRIDGE:")
    print("=" * 80)
    mean_d_rew = np.mean([data["B_Gated_M1"][s]["reward"] - data["A_Baseline"][s]["reward"] for s in seeds10])
    mean_d_tot_rev = np.mean([data["B_Gated_M1"][s]["total_rev"] - data["A_Baseline"][s]["total_rev"] for s in seeds10])
    mean_d_tot_exp = np.mean([data["B_Gated_M1"][s]["total_exp"] - data["A_Baseline"][s]["total_exp"] for s in seeds10])

    print(f"Mean Delta Reward:       ${mean_d_rew:>+10,.2f}")
    print(f"Mean Delta Total Rev:    ${mean_d_tot_rev:>+10,.2f}")
    print(f"Mean Delta Total Exp:    ${mean_d_tot_exp:>+10,.2f}")
    print(f"Reconstructed Delta:     ${mean_d_tot_rev - mean_d_tot_exp:>+10,.2f}")
    print(f"Unexplained Residual:    ${mean_d_rew - (mean_d_tot_rev - mean_d_tot_exp):>+10,.2f}")

    print("\nItemized Revenue Deltas (10-seed means):")
    for it in items:
        br_m = np.mean([data["A_Baseline"][s]["rev_by_item"].get(it, 0.0) for s in seeds10])
        gr_m = np.mean([data["B_Gated_M1"][s]["rev_by_item"].get(it, 0.0) for s in seeds10])
        bq_m = np.mean([data["A_Baseline"][s]["qty_sold"].get(it, 0) for s in seeds10])
        gq_m = np.mean([data["B_Gated_M1"][s]["qty_sold"].get(it, 0) for s in seeds10])
        bp_m = br_m / bq_m if bq_m > 0 else 0.0
        gp_m = gr_m / gq_m if gq_m > 0 else 0.0
        print(f"  {it:<11}: Rev Delta=${gr_m - br_m:>+9,.2f} | Qty: {bq_m:.1f} -> {gq_m:.1f} ({gq_m-bq_m:>+4.1f}) | Avg Price: ${bp_m:.1f} -> ${gp_m:.1f} ({gp_m-bp_m:>+5.1f})")

    print("\nItemized Expenditure Deltas (10-seed means):")
    for exp_k in exp_keys:
        be_m = np.mean([data["A_Baseline"][s][exp_k] for s in seeds10])
        ge_m = np.mean([data["B_Gated_M1"][s][exp_k] for s in seeds10])
        print(f"  {exp_k:<15}: Delta=${ge_m - be_m:>+9,.2f} (Base=${be_m:,.1f}, Gated=${ge_m:,.1f})")

if __name__ == "__main__":
    analyze_bridge()
