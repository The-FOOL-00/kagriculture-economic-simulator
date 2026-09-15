import json
import numpy as np

def analyze_instrumented_data():
    with open("scratch/instrumented_validation_500seeds.json") as f:
        data = json.load(f)

    q50 = data["Raw_Q50"]
    cand = data["Frozen_Candidate"]
    seeds = sorted([int(s) for s in q50.keys()])
    n = len(seeds)

    print("="*100)
    print("PHASE 6: CAUSAL LABOR REDEPLOYMENT & MECHANISM VERIFICATION (N=500)")
    print("="*100)

    metrics = [
        ("DIG Actions", "dig"),
        ("Movement Steps", "move"),
        ("WATER Actions", "water"),
        ("HARVEST Actions", "harvest"),
        ("CARE Actions", "care"),
        ("FEED Actions", "feed"),
        ("PLANT Actions", "plant"),
        ("Worker Idle Steps", "idle"),
        ("Worker Utilization (%)", "utilization"),
        ("Missed-Water Events (Mature Straw)", "missed_water"),
        ("Strawberry Death Events (to Weed)", "strawberry_deaths"),
        ("Strawberry Cap-Loss Events", "cap_loss_events"),
        ("Strawberry Units Lost to Capping", "cap_units_lost"),
        ("Wool Sold (Units)", "wool"),
        ("Milk Sold (Units)", "milk"),
        ("Strawberry Sold (Units)", "strawberry"),
        ("Wheat Sold (Units)", "wheat"),
        ("Melon Sold (Units)", "melon"),
        ("Fertilizer Sold (Units)", "fertilizer"),
    ]

    print(f"{'Physical Metric':<35} | {'Raw Q50 Mean':<14} | {'Candidate Mean':<14} | {'Mean Paired Delta':<18} | {'Median Delta':<14}")
    print("-" * 105)

    mech_summary = {}

    for name, key in metrics:
        q_vals = np.array([q50[str(s)][key] for s in seeds], dtype=float)
        c_vals = np.array([cand[str(s)][key] for s in seeds], dtype=float)
        if key == "utilization":
            q_vals *= 100.0
            c_vals *= 100.0
        diffs = c_vals - q_vals
        mean_q = float(np.mean(q_vals))
        mean_c = float(np.mean(c_vals))
        mean_d = float(np.mean(diffs))
        med_d = float(np.median(diffs))
        mech_summary[key] = {"q50": mean_q, "cand": mean_c, "delta": mean_d, "med_delta": med_d}
        print(f"{name:<35} | {mean_q:14.2f} | {mean_c:14.2f} | {mean_d:+18.2f} | {med_d:+14.2f}")

    print("\n" + "="*100)
    print("PHASE 5: CONDITIONAL STABILITY PARTITIONS (N=500)")
    print("="*100)

    rew_deltas = np.array([cand[str(s)]["reward"] - q50[str(s)]["reward"] for s in seeds])

    def print_partition(title, partition_key, is_cand_val=False):
        print(f"\n--- Partition by: {title} ---")
        vals = np.array([q50[str(s)][partition_key] for s in seeds], dtype=float)
        p25, p50, p75 = np.percentile(vals, [25, 50, 75])
        
        q1_mask = vals <= p25
        q2_mask = (vals > p25) & (vals <= p50)
        q3_mask = (vals > p50) & (vals <= p75)
        q4_mask = vals > p75

        print(f"{'Quartile Bracket':<30} | {'Range / Threshold':<20} | {'Mean Delta ($)':<15} | {'Median Delta ($)':<16} | {'Win Rate (%)':<12}")
        print("-" * 100)

        part_summary = {}
        for q_name, mask, rng_str in [
            ("Q1 (Lowest 25%)", q1_mask, f"<= {p25:.1f}"),
            ("Q2 (25% - 50%)", q2_mask, f"{p25:.1f} - {p50:.1f}"),
            ("Q3 (50% - 75%)", q3_mask, f"{p50:.1f} - {p75:.1f}"),
            ("Q4 (Highest 25%)", q4_mask, f"> {p75:.1f}")
        ]:
            sub_d = rew_deltas[mask]
            m_d = float(np.mean(sub_d)) if len(sub_d) > 0 else 0.0
            med_d = float(np.median(sub_d)) if len(sub_d) > 0 else 0.0
            wr = float(np.mean(sub_d > 0) * 100) if len(sub_d) > 0 else 0.0
            part_summary[q_name] = {"mean": m_d, "median": med_d, "win_rate": wr, "n": int(np.sum(mask))}
            print(f"{q_name:<30} | {rng_str:<20} | ${m_d:+14.2f} | ${med_d:+15.2f} | {wr:11.1f}%")
        return part_summary

    stability_results = {}
    stability_results["q50_reward"] = print_partition("1. Baseline Q50 Reward", "reward")
    stability_results["strawberry_qty"] = print_partition("2. Strawberry Quantity Sold", "strawberry")
    stability_results["wheat_qty"] = print_partition("3. Wheat Quantity Sold", "wheat")
    stability_results["worker_movement"] = print_partition("4. Worker Movement Steps", "move")
    stability_results["mature_straw"] = print_partition("5. Number of Mature Strawberry Hours", "mature_straw_hours")
    stability_results["peripheral_weeds"] = print_partition("6. Peripheral Weed Tasks Seen", "peripheral_weeds")
    stability_results["watering_conflicts"] = print_partition("7. Number of Watering Conflicts", "water_conflicts")
    stability_results["animal_conflicts"] = print_partition("8. Animal Care Conflicts", "animal_conflicts")

    out = {
        "mechanisms": mech_summary,
        "stability": stability_results
    }
    with open("scratch/phase5_and_6_summary.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    analyze_instrumented_data()
