import json
import numpy as np
import scipy.stats as stats

def analyze():
    with open("scratch/phase7_validation_200seeds_results.json") as f:
        data = json.load(f)

    n = len(data)
    print(f"=== PHASE 7: FRESH 200-SEED VALIDATION (N={n} SEEDS: 1250-1449) ===")

    m1_rews = np.array([d["m1"]["reward"] for d in data])
    mecha_rews = np.array([d["mech_a"]["reward"] for d in data])
    deltas = mecha_rews - m1_rews

    mean_d = float(np.mean(deltas))
    med_d = float(np.median(deltas))
    sd_d = float(np.std(deltas, ddof=1))
    sem_d = sd_d / np.sqrt(n)
    
    ci_95 = [mean_d - 1.96 * sem_d, mean_d + 1.96 * sem_d]
    ci_99 = [mean_d - 2.576 * sem_d, mean_d + 2.576 * sem_d]

    t_stat, p_t = stats.ttest_1samp(deltas, 0.0)
    w_stat, p_w = stats.wilcoxon(deltas)

    win_rate = float(np.mean(deltas > 0) * 100)
    loss_rate = float(np.mean(deltas < 0) * 100)

    p25, p50, p75 = np.percentile(deltas, [25, 50, 75])

    print("\nPrimary Statistical Summary:")
    print(f"Mean Reward Delta:   ${mean_d:+10,.2f}")
    print(f"Median Reward Delta: ${med_d:+10,.2f}")
    print(f"Standard Deviation:  ${sd_d:10,.2f}")
    print(f"95% CI:              [${ci_95[0]:+,.2f}, ${ci_95[1]:+,.2f}]")
    print(f"99% CI:              [${ci_99[0]:+,.2f}, ${ci_99[1]:+,.2f}]")
    print(f"Paired t-test:       t = {t_stat:.4f}, p = {p_t:.4f}")
    print(f"Wilcoxon signed-rank:W = {w_stat:.1f}, p = {p_w:.4f}")
    print(f"Win Rate:            {win_rate:.1f}% ({np.sum(deltas > 0)} wins / {n})")
    print(f"Loss Rate:           {loss_rate:.1f}% ({np.sum(deltas < 0)} losses / {n})")
    print(f"Percentiles:         25th=${p25:+,.2f} | 50th=${p50:+,.2f} | 75th=${p75:+,.2f}")

    # Best 10 and Worst 10
    sorted_seeds = sorted([(d["seed"], mecha_rews[i] - m1_rews[i]) for i, d in enumerate(data)], key=lambda x: x[1])
    print("\nWorst 10 Deltas:")
    for s, d_val in sorted_seeds[:10]:
        print(f"  Seed {s}: ${d_val:+,.0f}")

    print("\nBest 10 Deltas:")
    for s, d_val in sorted_seeds[-10:][::-1]:
        print(f"  Seed {s}: ${d_val:+,.0f}")

    # Effect by seed quartile (based on baseline M1 performance)
    m1_quartiles = np.percentile(m1_rews, [25, 50, 75])
    q_masks = [
        m1_rews <= m1_quartiles[0],
        (m1_rews > m1_quartiles[0]) & (m1_rews <= m1_quartiles[1]),
        (m1_rews > m1_quartiles[1]) & (m1_rews <= m1_quartiles[2]),
        m1_rews > m1_quartiles[2]
    ]
    print("\nEffect by Baseline M1 Performance Quartile:")
    for q_idx, mask in enumerate(q_masks):
        q_deltas = deltas[mask]
        print(f"  Quartile {q_idx+1} (N={np.sum(mask)}): Mean Delta=${np.mean(q_deltas):+,.2f}, Median=${np.median(q_deltas):+,.2f}, Win Rate={np.mean(q_deltas > 0)*100:.1f}%")

    # Conditional on Day-6 collision
    # Collision definition: In M1, Day 6 cow buy could be 1 or 2, but when cash is high, does M1 buy 1 or 2?
    # More precisely: Does MechA cap cows at 4 in NW (i.e. did the intervention actually bite)?
    # When M1 cash on Day 6 was >= 1050, M1 buys 2 cows, placing Cow 5 into NW sheep slot (collision).
    collision_seeds = [i for i, d in enumerate(data) if d["m1"]["day6_cows_bought"] >= 2 or d["m1"]["cows_on_sheep_slots"] > 2]
    no_collision_seeds = [i for i, d in enumerate(data) if i not in collision_seeds]

    print(f"\nEffect Conditional on Pasture Collision:")
    print(f"  Collision Seeds (N={len(collision_seeds)}):    Mean Delta=${np.mean(deltas[collision_seeds]):+,.2f}, Median=${np.median(deltas[collision_seeds]):+,.2f}, Win={np.mean(deltas[collision_seeds]>0)*100:.1f}%")
    print(f"  No-Collision Seeds (N={len(no_collision_seeds)}): Mean Delta=${np.mean(deltas[no_collision_seeds]):+,.2f}, Median=${np.median(deltas[no_collision_seeds]):+,.2f}, Win={np.mean(deltas[no_collision_seeds]>0)*100:.1f}%")

    # Physical Commodity Deltas
    wool_m1 = np.array([d["m1"]["sold"].get("WOOL", 0) for d in data])
    wool_mecha = np.array([d["mech_a"]["sold"].get("WOOL", 0) for d in data])
    wheat_m1 = np.array([d["m1"]["sold"].get("WHEAT", 0) for d in data])
    wheat_mecha = np.array([d["mech_a"]["sold"].get("WHEAT", 0) for d in data])
    straw_m1 = np.array([d["m1"]["sold"].get("STRAWBERRY", 0) for d in data])
    straw_mecha = np.array([d["mech_a"]["sold"].get("STRAWBERRY", 0) for d in data])
    milk_m1 = np.array([d["m1"]["sold"].get("MILK", 0) for d in data])
    milk_mecha = np.array([d["mech_a"]["sold"].get("MILK", 0) for d in data])

    print("\nPhysical Commodity Deltas (MechA - M1):")
    print(f"  Wool Sold:       {np.mean(wool_mecha - wool_m1):+.2f} units (M1: {np.mean(wool_m1):.1f} vs MechA: {np.mean(wool_mecha):.1f})")
    print(f"  Wheat Sold:      {np.mean(wheat_mecha - wheat_m1):+.2f} units (M1: {np.mean(wheat_m1):.1f} vs MechA: {np.mean(wheat_mecha):.1f})")
    print(f"  Strawberry Sold: {np.mean(straw_mecha - straw_m1):+.2f} units (M1: {np.mean(straw_m1):.1f} vs MechA: {np.mean(straw_mecha):.1f})")
    print(f"  Milk Sold:       {np.mean(milk_mecha - milk_m1):+.2f} units (M1: {np.mean(milk_m1):.1f} vs MechA: {np.mean(milk_mecha):.1f})")

if __name__ == "__main__":
    analyze()
