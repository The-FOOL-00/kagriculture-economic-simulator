import json
import numpy as np

def analyze_phase10():
    with open("scratch/50seed_hostile_audit_raw.json") as f:
        data = json.load(f)

    arms = ["A_Baseline", "B_Gated_M1", "C_Prio_M3", "D_Pair_M1_M3"]
    seeds = sorted([int(s) for s in data["A_Baseline"].keys()])
    n_seeds = len(seeds)

    print("=" * 80)
    print(f"PHASE 10: M1 + M3 FACTORIAL INTERACTION ACROSS 50 SEEDS (N={n_seeds})")
    print("=" * 80)

    # 1. Action Counts
    action_types = ["FERTILIZE", "WATER", "CARE", "FEED", "COLLECT_FERT", "HARVEST_STRAW", "HARVEST_OTHER", "DROP", "MOVE", "PASS"]
    
    print("\n--- Worker Action Allocations (Mean Actions / Seed) ---")
    header = f"{'Action Type':<16} | " + " | ".join([f"{arm:>14}" for arm in arms])
    print(header)
    print("-" * len(header))

    for at in action_types:
        row = [f"{at:<16}"]
        for arm in arms:
            vals = [data[arm][str(s)]["actions_count"].get(at, 0) for s in seeds]
            row.append(f"{np.mean(vals):>14.1f}")
        print(" | ".join(row))

    # 2. Key Economic & Physical Metrics
    metrics = [
        ("Terminal Reward ($)", "reward", "${:,.1f}"),
        ("Strawberry Sold (u)", "straw_sold", "{:.2f}"),
        ("Strawberry Rev ($)", "straw_rev", "${:,.1f}"),
        ("Milk Rev ($)", "milk_rev", "${:,.1f}"),
        ("Fertilizer Rev ($)", "fert_rev", "${:,.1f}"),
        ("Total Gross Rev ($)", "total_rev", "${:,.1f}"),
        ("Total Exp ($)", "total_exp", "${:,.1f}"),
        ("Max Shed Fill (u)", "max_shed_fill", "{:.1f}"),
        ("Term Shed Inv (u)", "term_shed_inv", "{:.1f}"),
    ]

    print("\n--- Key Economic & Physical Outcomes ---")
    header2 = f"{'Metric':<22} | " + " | ".join([f"{arm:>14}" for arm in arms])
    print(header2)
    print("-" * len(header2))

    for lbl, k, fmt in metrics:
        row = [f"{lbl:<22}"]
        for arm in arms:
            vals = [data[arm][str(s)][k] for s in seeds]
            row.append(f"{fmt.format(np.mean(vals)):>14}")
        print(" | ".join(row))

    # 3. Factorial 2x2 Interaction Analysis
    # M1 effect, M3 effect, and Interaction effect on Reward and Strawberry Sold
    # Y = b0 + b1 * M1 + b2 * M3 + b12 * (M1 * M3)
    # where M1 in {0, 1}, M3 in {0, 1}
    # b0 = Y_A
    # b1 = Y_B - Y_A
    # b2 = Y_C - Y_A
    # b12 = (Y_D - Y_B) - (Y_C - Y_A) = Y_D - Y_C - Y_B + Y_A
    print("\n--- 2x2 Factorial Interaction Decomposition (Ols Contrast) ---")
    for target, lbl in [("reward", "Terminal Reward ($)"), ("straw_sold", "Strawberry Sold (u)")]:
        ya = np.array([data["A_Baseline"][str(s)][target] for s in seeds])
        yb = np.array([data["B_Gated_M1"][str(s)][target] for s in seeds])
        yc = np.array([data["C_Prio_M3"][str(s)][target] for s in seeds])
        yd = np.array([data["D_Pair_M1_M3"][str(s)][target] for s in seeds])

        main_m1 = np.mean(yb - ya)
        main_m3 = np.mean(yc - ya)
        pair_effect = np.mean(yd - ya)
        interaction = np.mean(yd - yb - yc + ya)

        print(f"\n{lbl}:")
        print(f"  Baseline (A):              {np.mean(ya):>10.2f}")
        print(f"  Main Effect of M1 (B - A): {main_m1:>+10.2f}")
        print(f"  Main Effect of M3 (C - A): {main_m3:>+10.2f}")
        print(f"  Joint Pair (D - A):        {pair_effect:>+10.2f}")
        print(f"  Interaction (D - B - C + A):{interaction:>+10.2f}")

if __name__ == "__main__":
    analyze_phase10()
