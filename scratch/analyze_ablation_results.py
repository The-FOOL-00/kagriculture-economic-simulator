import json
import numpy as np
import scipy.stats as stats

def analyze_ablations():
    with open("scratch/v2_mechanism_ablations_50seeds_raw.json") as f:
        data = json.load(f)

    seeds = sorted([int(s) for s in data["M1_Baseline"].keys()])
    n_seeds = len(seeds)

    arms = ["M1_Baseline", "M1_SheepTiming", "M1_PocketBatching", "M1_WheatExpansion"]
    labels = {
        "M1_Baseline": "M1 Baseline (Certified)",
        "M1_SheepTiming": "Mech 1: Sheep Timing (Days 5-8)",
        "M1_PocketBatching": "Mech 2: Pocket Batching (>=4u)",
        "M1_WheatExpansion": "Mech 3: Wheat Expansion (Quota 60)"
    }

    rews = {a: np.array([data[a][str(s)]["reward"] for s in seeds]) for a in arms}
    base_rews = rews["M1_Baseline"]

    print("=" * 115)
    print(f"PHASE 11 & 12: SINGLE-MECHANISM ABLATION RESULTS (N={n_seeds} SEEDS, 1000-1049)")
    print("=" * 115)
    print(f"{'Arm / Candidate':<36} | {'Mean Reward':<14} | {'Delta vs M1':<14} | {'Median Delta':<14} | {'Win Rate':<10} | {'p-value':<10} | {'Gate'}")
    print("-" * 115)

    for a in arms:
        m_rew = np.mean(rews[a])
        med_rew = np.median(rews[a])
        if a == "M1_Baseline":
            print(f"{labels[a]:<36} | ${m_rew:>12,.2f} | {'$0.00':>14} | {'$0.00':>14} | {'---':>10} | {'---':>10} | BASE")
            continue

        diff = rews[a] - base_rews
        m_diff = np.mean(diff)
        med_diff = np.median(diff)
        wins = int(np.sum(diff > 0))
        wr = (wins / n_seeds) * 100.0
        t_stat, p_val = stats.ttest_rel(rews[a], base_rews)

        # Classify gate
        if p_val < 0.05 and m_diff > 0:
            gate = "GREEN"
        elif m_diff > 0 or p_val < 0.20:
            gate = "YELLOW"
        else:
            gate = "RED"

        print(f"{labels[a]:<36} | ${m_rew:>12,.2f} | ${m_diff:>+12,.2f} | ${med_diff:>+12,.2f} | {wr:>8.1f}% | {p_val:>9.4f} | {gate}")

    print("-" * 115)
    print("\nCOMMODITY SALES BREAKDOWN (MEAN UNITS SOLD ACROSS 50 SEEDS):")
    print(f"{'Arm':<32} | {'STRAWBERRY':<12} | {'WOOL':<10} | {'WHEAT':<10} | {'MELON':<10} | {'FERTILIZER':<12} | {'MOVES':<8}")
    print("-" * 105)
    for a in arms:
        straw_u = np.mean([data[a][str(s)]["qty_sold"].get("STRAWBERRY", 0) for s in seeds])
        wool_u = np.mean([data[a][str(s)]["qty_sold"].get("WOOL", 0) for s in seeds])
        wheat_u = np.mean([data[a][str(s)]["qty_sold"].get("WHEAT", 0) for s in seeds])
        melon_u = np.mean([data[a][str(s)]["qty_sold"].get("MELON", 0) for s in seeds])
        fert_u = np.mean([data[a][str(s)]["qty_sold"].get("FERTILIZER", 0) for s in seeds])
        moves = np.mean([data[a][str(s)]["moves"] for s in seeds])
        print(f"{labels[a]:<32} | {straw_u:>10.2f}u | {wool_u:>8.2f}u | {wheat_u:>8.2f}u | {melon_u:>8.2f}u | {fert_u:>10.2f}u | {moves:>8.1f}")

    print("\nCOMMODITY REVENUE BREAKDOWN (MEAN $ ACROSS 50 SEEDS):")
    print(f"{'Arm':<32} | {'STRAWBERRY':<14} | {'WOOL':<12} | {'WHEAT':<12} | {'MELON':<12} | {'FERTILIZER':<12}")
    print("-" * 105)
    for a in arms:
        straw_r = np.mean([data[a][str(s)]["rev_by_item"].get("STRAWBERRY", 0) for s in seeds])
        wool_r = np.mean([data[a][str(s)]["rev_by_item"].get("WOOL", 0) for s in seeds])
        wheat_r = np.mean([data[a][str(s)]["rev_by_item"].get("WHEAT", 0) for s in seeds])
        melon_r = np.mean([data[a][str(s)]["rev_by_item"].get("MELON", 0) for s in seeds])
        fert_r = np.mean([data[a][str(s)]["rev_by_item"].get("FERTILIZER", 0) for s in seeds])
        print(f"{labels[a]:<32} | ${straw_r:>12,.2f} | ${wool_r:>10,.2f} | ${wheat_r:>10,.2f} | ${melon_r:>10,.2f} | ${fert_r:>10,.2f}")

if __name__ == "__main__":
    analyze_ablations()
