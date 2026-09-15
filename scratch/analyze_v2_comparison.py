import json
import numpy as np

def compare_v2():
    with open("scratch/200seed_validation_raw.json") as f:
        data = json.load(f)
    with open("scratch/v2_200seed_raw.json") as f:
        data_v2 = json.load(f)

    seeds = sorted([int(s) for s in data["Baseline"].keys()])
    n_seeds = len(seeds)
    print(f"Comparing CL Baseline, Gated M1, and Frozen V2 across {n_seeds} Matched Seeds (1000-1199)...")

    # Metrics to compare:
    # 1. Terminal Reward
    # 2. Strawberry (sold and revenue)
    # 3. Wool (sold and revenue)
    # 4. Milk (sold and revenue)
    # 5. Wheat (sold and revenue)
    # 6. Melon (sold and revenue)
    # 7. Fertilizer (sold and revenue)
    # 8. Total Expenditures

    commodities = ["STRAWBERRY", "WOOL", "MILK", "WHEAT", "MELON", "FERTILIZER"]

    rews_base = [data["Baseline"][str(s)]["reward"] for s in seeds]
    rews_gated = [data["Gated_M1"][str(s)]["reward"] for s in seeds]
    rews_v2 = [data_v2[str(s)]["reward"] for s in seeds]

    print("\n" + "=" * 95)
    print(f"{'METRIC':<26} | {'CL BASELINE':<18} | {'GATED M1':<18} | {'FROZEN V2':<18} | {'GAP (V2 - M1)':<12}")
    print("=" * 95)

    print(f"{'Terminal Reward ($)':<26} | ${np.mean(rews_base):>16,.2f} | ${np.mean(rews_gated):>16,.2f} | ${np.mean(rews_v2):>16,.2f} | ${np.mean(rews_v2) - np.mean(rews_gated):>+10,.2f}")
    print(f"{'Median Reward ($)':<26} | ${np.median(rews_base):>16,.2f} | ${np.median(rews_gated):>16,.2f} | ${np.median(rews_v2):>16,.2f} | ${np.median(rews_v2) - np.median(rews_gated):>+10,.2f}")

    print("-" * 95)
    print("PHYSICAL UNITS SOLD (MEAN UNITS / MATCH):")
    for c in commodities:
        u_base = np.mean([data["Baseline"][str(s)]["qty_sold"].get(c, 0) for s in seeds])
        u_gated = np.mean([data["Gated_M1"][str(s)]["qty_sold"].get(c, 0) for s in seeds])
        u_v2 = np.mean([data_v2[str(s)]["qty_sold"].get(c, 0) for s in seeds])
        print(f"  {c:<24} | {u_base:>17.2f}u | {u_gated:>17.2f}u | {u_v2:>17.2f}u | {u_v2 - u_gated:>+10.2f}u")

    print("-" * 95)
    print("REALIZED CASH REVENUE (MEAN $ / MATCH):")
    rev_keys = {
        "STRAWBERRY": "straw_rev", "WOOL": "wool_rev", "MILK": "milk_rev",
        "WHEAT": "wheat_rev", "MELON": "melon_rev", "FERTILIZER": "fert_rev"
    }
    for c, rk in rev_keys.items():
        r_base = np.mean([data["Baseline"][str(s)][rk] for s in seeds])
        r_gated = np.mean([data["Gated_M1"][str(s)][rk] for s in seeds])
        r_v2 = np.mean([data_v2[str(s)][rk] for s in seeds])
        print(f"  {c:<24} | ${r_base:>16,.2f} | ${r_gated:>16,.2f} | ${r_v2:>16,.2f} | ${r_v2 - r_gated:>+10,.2f}")

    print("-" * 95)
    exp_base = np.mean([data["Baseline"][str(s)]["total_exp"] for s in seeds])
    exp_gated = np.mean([data["Gated_M1"][str(s)]["total_exp"] for s in seeds])
    exp_v2 = np.mean([data_v2[str(s)]["total_exp"] for s in seeds])
    print(f"{'Total Expenditures ($)':<26} | ${exp_base:>16,.2f} | ${exp_gated:>16,.2f} | ${exp_v2:>16,.2f} | ${exp_v2 - exp_gated:>+10,.2f}")

    # Action counts
    print("-" * 95)
    print("KEY WORKER ACTIONS (MEAN ACTIONS / MATCH):")
    for ak in ["MOVE", "FERTILIZE", "WATER", "FEED", "CARE", "COLLECT_FERT", "PASS"]:
        a_base = np.mean([data["Baseline"][str(s)]["actions_count"].get(ak, 0) for s in seeds])
        a_gated = np.mean([data["Gated_M1"][str(s)]["actions_count"].get(ak, 0) for s in seeds])
        a_v2 = np.mean([data_v2[str(s)]["actions_count"].get(ak, 0) for s in seeds])
        print(f"  {ak:<24} | {a_base:>17.1f} | {a_gated:>17.1f} | {a_v2:>17.1f} | {a_v2 - a_gated:>+10.1f}")
    print("=" * 95)

if __name__ == "__main__":
    compare_v2()
