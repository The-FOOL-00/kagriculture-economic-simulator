import json
import numpy as np
import scipy.stats as stats

def analyze():
    with open("scratch/phase3_counterfactuals_50seeds.json") as f:
        data = json.load(f)

    n = len(data)
    print(f"=== PHASE 3 COUNTERFACTUALS ANALYSIS (N={n} SEEDS: 1000-1049) ===")

    arms = ["m1", "q50", "a1", "a2", "a3"]
    arm_labels = {
        "m1": "M1 Certified Parent",
        "q50": "Raw Quota 50",
        "a1": "CF A1 (Protect Opening 2 Sheep Slots)",
        "a2": "CF A2 (Protect ALL M1 Sheep Slots)",
        "a3": "CF A3 (Dynamic Shared Pasture Capacity Gating)"
    }

    m1_rews = np.array([d["m1"]["reward"] for d in data])

    header = f"{'Arm':<46} | {'Mean Rew':<10} | {'Delta vs M1':<12} | {'Median d':<10} | {'95% CI':<22} | {'p-val(t)':<9} {'p-val(W)':<9} | {'Win %':<6} | {'Catastrophic Losses (< -15k)':<28}"
    print(header)
    print("-" * len(header))

    arm_stats = {}
    for arm in arms:
        rews = np.array([d[arm]["reward"] for d in data])
        deltas = rews - m1_rews
        mean_r = np.mean(rews)
        mean_d = np.mean(deltas)
        med_d = np.median(deltas)
        sd_d = np.std(deltas, ddof=1)
        sem_d = sd_d / np.sqrt(n)
        ci_95 = [mean_d - 1.96 * sem_d, mean_d + 1.96 * sem_d]
        
        if arm == "m1":
            p_t, p_w = 1.0, 1.0
            win_pct = 0.0
            catastrophic = 0
        else:
            t_res, p_t = stats.ttest_1samp(deltas, 0.0)
            try:
                w_res, p_w = stats.wilcoxon(deltas)
            except Exception:
                p_w = 1.0
            win_pct = np.mean(deltas > 0) * 100
            catastrophic = int(np.sum(deltas < -15000))

        ci_str = f"[{ci_95[0]:+,.0f}, {ci_95[1]:+,.0f}]"
        print(f"{arm_labels[arm]:<46} | ${mean_r:9,.0f} | ${mean_d:+10,.0f} | ${med_d:+8,.0f} | {ci_str:<22} | {p_t:9.4f} {p_w:9.4f} | {win_pct:5.1f}% | {catastrophic:<28d}")

        # Secondary physical metrics
        wool = np.mean([d[arm]["sold"].get("WOOL", 0) for d in data])
        wheat = np.mean([d[arm]["sold"].get("WHEAT", 0) for d in data])
        straw = np.mean([d[arm]["sold"].get("STRAWBERRY", 0) for d in data])
        milk = np.mean([d[arm]["sold"].get("MILK", 0) for d in data])
        cows = np.mean([d[arm]["cow_count"] for d in data])
        sheep = np.mean([d[arm]["sheep_count"] for d in data])
        s_shed = np.mean([d[arm]["sheep_shed_days"] for d in data])
        c_shed = np.mean([d[arm]["cow_shed_days"] for d in data])
        moves = np.mean([d[arm]["worker_moves"] for d in data])
        idles = np.mean([d[arm]["worker_idles"] for d in data])
        conflicts = np.mean([d[arm]["conflicts"] for d in data])

        arm_stats[arm] = {
            "mean_r": mean_r, "mean_d": mean_d, "med_d": med_d, "sd_d": sd_d, "ci_95": ci_95,
            "p_t": p_t, "p_w": p_w, "win_pct": win_pct, "catastrophic": catastrophic,
            "wool": wool, "wheat": wheat, "straw": straw, "milk": milk,
            "cows": cows, "sheep": sheep, "s_shed": s_shed, "c_shed": c_shed,
            "moves": moves, "idles": idles, "conflicts": conflicts
        }

    print("\n" + "="*80)
    print("DETAILED PHYSICAL & LOGISTICS METRICS")
    print("="*80)
    p_header = f"{'Arm':<46} | {'Wool':<6} | {'Wheat':<6} | {'Straw':<6} | {'Milk':<6} | {'Cows':<5} {'Sheep':<5} | {'S-Shed':<6} | {'Conflicts':<10}"
    print(p_header)
    print("-" * len(p_header))
    for arm in arms:
        st = arm_stats[arm]
        print(f"{arm_labels[arm]:<46} | {st['wool']:6.1f} | {st['wheat']:6.1f} | {st['straw']:6.1f} | {st['milk']:6.1f} | {st['cows']:5.1f} {st['sheep']:5.1f} | {st['s_shed']:6.1f} | {st['conflicts']:10.2f}")

if __name__ == "__main__":
    analyze()
