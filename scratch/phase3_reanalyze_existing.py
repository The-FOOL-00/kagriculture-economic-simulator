import json
import numpy as np
from scipy import stats

def reanalyze_existing_data():
    with open("scratch/audit3_per_seed_data.json") as f:
        data = json.load(f)

    records = data["per_seed_data"]
    n = len(records)

    deltas_b = np.array([r["delta_b"] for r in records])
    deltas_a = np.array([r["delta_a"] for r in records])
    deltas_ab = np.array([r["delta_ab"] for r in records])

    def calc_metrics(arr, name):
        mean_v = float(np.mean(arr))
        med_v = float(np.median(arr))
        sd_v = float(np.std(arr, ddof=1))
        
        # Bootstrap CIs
        rng = np.random.default_rng(42)
        boot = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(10000)]
        ci95 = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
        ci99 = [float(np.percentile(boot, 0.5)), float(np.percentile(boot, 99.5))]

        wins = int(np.sum(arr > 0))
        ties = int(np.sum(arr == 0))
        losses = int(np.sum(arr < 0))
        win_rate = (wins / n) * 100
        win_rate_excl = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0

        min_v = float(np.min(arr))
        p05 = float(np.percentile(arr, 5))
        p25 = float(np.percentile(arr, 25))
        p75 = float(np.percentile(arr, 75))
        p95 = float(np.percentile(arr, 95))
        max_v = float(np.max(arr))

        p_lt_0 = float(np.mean(arr < 0) * 100)
        p_lt_500 = float(np.mean(arr < -500) * 100)
        p_lt_1000 = float(np.mean(arr < -1000) * 100)
        p_lt_2000 = float(np.mean(arr < -2000) * 100)
        p_lt_5000 = float(np.mean(arr < -5000) * 100)

        t_stat, p_val_t = stats.ttest_1samp(arr, 0.0)
        w_stat, p_val_w = stats.wilcoxon(arr, alternative="two-sided")

        return {
            "name": name,
            "mean": mean_v,
            "median": med_v,
            "sd": sd_v,
            "ci95": ci95,
            "ci99": ci99,
            "wins": wins,
            "ties": ties,
            "losses": losses,
            "win_rate": win_rate,
            "win_rate_excl": win_rate_excl,
            "min": min_v,
            "p05": p05,
            "p25": p25,
            "p75": p75,
            "p95": p95,
            "max": max_v,
            "p_lt_0": p_lt_0,
            "p_lt_500": p_lt_500,
            "p_lt_1000": p_lt_1000,
            "p_lt_2000": p_lt_2000,
            "p_lt_5000": p_lt_5000,
            "t_stat": float(t_stat),
            "p_val_t": float(p_val_t),
            "w_stat": float(w_stat),
            "p_val_w": float(p_val_w)
        }

    m_b = calc_metrics(deltas_b, "B_ONLY (Weed Gating Only)")
    m_a = calc_metrics(deltas_a, "A_ONLY (Urgency Sorting Only)")
    m_ab = calc_metrics(deltas_ab, "A+B (Frozen L_Minimal)")

    print("=" * 110)
    print("PHASE 3: HEAD-TO-HEAD COMPARISON ON EXISTING DISCOVERY SEEDS (1300-1399, N=100)")
    print("=" * 110)
    fmt = "{:<28s} | {:<12s} | {:<12s} | {:<12s}"
    print(fmt.format("Metric", "B_ONLY", "A_ONLY", "A+B (L_Minimal)"))
    print("-" * 110)
    print(fmt.format("Mean Delta vs Q50", f"${m_b['mean']:+,.2f}", f"${m_a['mean']:+,.2f}", f"${m_ab['mean']:+,.2f}"))
    print(fmt.format("Median Delta", f"${m_b['median']:+,.2f}", f"${m_a['median']:+,.2f}", f"${m_ab['median']:+,.2f}"))
    print(fmt.format("Standard Deviation", f"${m_b['sd']:,.2f}", f"${m_a['sd']:,.2f}", f"${m_ab['sd']:,.2f}"))
    print(fmt.format("95% Paired CI", f"[${m_b['ci95'][0]:+.0f}, ${m_b['ci95'][1]:+.0f}]", f"[${m_a['ci95'][0]:+.0f}, ${m_a['ci95'][1]:+.0f}]", f"[${m_ab['ci95'][0]:+.0f}, ${m_ab['ci95'][1]:+.0f}]"))
    print(fmt.format("99% Paired CI", f"[${m_b['ci99'][0]:+.0f}, ${m_b['ci99'][1]:+.0f}]", f"[${m_a['ci99'][0]:+.0f}, ${m_a['ci99'][1]:+.0f}]", f"[${m_ab['ci99'][0]:+.0f}, ${m_ab['ci99'][1]:+.0f}]"))
    print(fmt.format("Win / Tie / Loss", f"{m_b['wins']}/{m_b['ties']}/{m_b['losses']}", f"{m_a['wins']}/{m_a['ties']}/{m_a['losses']}", f"{m_ab['wins']}/{m_ab['ties']}/{m_ab['losses']}"))
    print(fmt.format("Win Rate (incl ties)", f"{m_b['win_rate']:.1f}%", f"{m_a['win_rate']:.1f}%", f"{m_ab['win_rate']:.1f}%"))
    print(fmt.format("Win Rate (excl ties)", f"{m_b['win_rate_excl']:.1f}%", f"{m_a['win_rate_excl']:.1f}%", f"{m_ab['win_rate_excl']:.1f}%"))
    print(fmt.format("Paired t-test p-value", f"{m_b['p_val_t']:.6f}", f"{m_a['p_val_t']:.6f}", f"{m_ab['p_val_t']:.6f}"))
    print(fmt.format("Wilcoxon p-value", f"{m_b['p_val_w']:.6f}", f"{m_a['p_val_w']:.6f}", f"{m_ab['p_val_w']:.6f}"))
    print("-" * 110)
    print("TAIL RISK COMPARISON:")
    print(fmt.format("Worst Loss (Min Delta)", f"${m_b['min']:+,.2f}", f"${m_a['min']:+,.2f}", f"${m_ab['min']:+,.2f}"))
    print(fmt.format("5th Percentile (p05)", f"${m_b['p05']:+,.2f}", f"${m_a['p05']:+,.2f}", f"${m_ab['p05']:+,.2f}"))
    print(fmt.format("25th Percentile (p25)", f"${m_b['p25']:+,.2f}", f"${m_a['p25']:+,.2f}", f"${m_ab['p25']:+,.2f}"))
    print(fmt.format("75th Percentile (p75)", f"${m_b['p75']:+,.2f}", f"${m_a['p75']:+,.2f}", f"${m_ab['p75']:+,.2f}"))
    print(fmt.format("95th Percentile (p95)", f"${m_b['p95']:+,.2f}", f"${m_a['p95']:+,.2f}", f"${m_ab['p95']:+,.2f}"))
    print(fmt.format("Maximum Gain (Max Delta)", f"${m_b['max']:+,.2f}", f"${m_a['max']:+,.2f}", f"${m_ab['max']:+,.2f}"))
    print("-" * 110)
    print("LOSS PROBABILITIES:")
    print(fmt.format("P(Delta < $0)", f"{m_b['p_lt_0']:.1f}%", f"{m_a['p_lt_0']:.1f}%", f"{m_ab['p_lt_0']:.1f}%"))
    print(fmt.format("P(Delta < -$500)", f"{m_b['p_lt_500']:.1f}%", f"{m_a['p_lt_500']:.1f}%", f"{m_ab['p_lt_500']:.1f}%"))
    print(fmt.format("P(Delta < -$1,000)", f"{m_b['p_lt_1000']:.1f}%", f"{m_a['p_lt_1000']:.1f}%", f"{m_ab['p_lt_1000']:.1f}%"))
    print(fmt.format("P(Delta < -$2,000)", f"{m_b['p_lt_2000']:.1f}%", f"{m_a['p_lt_2000']:.1f}%", f"{m_ab['p_lt_2000']:.1f}%"))
    print(fmt.format("P(Delta < -$5,000)", f"{m_b['p_lt_5000']:.1f}%", f"{m_a['p_lt_5000']:.1f}%", f"{m_ab['p_lt_5000']:.1f}%"))
    print("=" * 110)

    out = {"m_b": m_b, "m_a": m_a, "m_ab": m_ab}
    with open("scratch/phase3_reanalysis_results.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    reanalyze_existing_data()
