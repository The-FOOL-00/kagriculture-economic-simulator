import json
import numpy as np
from scipy import stats

def analyze():
    with open("scratch/clean_discovery_841000_raw_results.json") as f:
        data = json.load(f)

    seeds = [int(s) for s in data["Raw_Q50"].keys()]
    seeds.sort()
    n = len(seeds)

    policies = list(data.keys())
    q50_data = data["Raw_Q50"]
    q50_rews = np.array([q50_data[str(s)]["reward"] for s in seeds])

    print("=" * 120)
    print(f"HEAD-TO-HEAD SUMMARY ON PRISTINE DISCOVERY SEEDS 841000-841099 (N={n})")
    print("=" * 120)

    summary = {}
    for pol in policies:
        p_data = data[pol]
        p_rews = np.array([p_data[str(s)]["reward"] for s in seeds])
        deltas = p_rews - q50_rews if pol != "Raw_Q50" else p_rews

        mean_v = float(np.mean(deltas))
        med_v = float(np.median(deltas))
        sd_v = float(np.std(deltas, ddof=1))

        rng = np.random.default_rng(42)
        boot = [np.mean(rng.choice(deltas, size=n, replace=True)) for _ in range(10000)]
        ci95 = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

        wins = int(np.sum(deltas > 0)) if pol != "Raw_Q50" else 0
        ties = int(np.sum(deltas == 0)) if pol != "Raw_Q50" else 0
        losses = int(np.sum(deltas < 0)) if pol != "Raw_Q50" else 0
        win_rate = (wins / n) * 100
        win_rate_excl = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0

        min_d = float(np.min(deltas)) if pol != "Raw_Q50" else float(np.min(p_rews))
        p05 = float(np.percentile(deltas, 5)) if pol != "Raw_Q50" else float(np.percentile(p_rews, 5))
        max_d = float(np.max(deltas)) if pol != "Raw_Q50" else float(np.max(p_rews))

        p_lt_0 = float(np.mean(deltas < 0) * 100) if pol != "Raw_Q50" else 0.0
        p_lt_500 = float(np.mean(deltas < -500) * 100) if pol != "Raw_Q50" else 0.0
        p_lt_1000 = float(np.mean(deltas < -1000) * 100) if pol != "Raw_Q50" else 0.0

        if pol != "Raw_Q50":
            t_stat, p_val_t = stats.ttest_1samp(deltas, 0.0)
            try:
                w_stat, p_val_w = stats.wilcoxon(deltas, alternative="two-sided")
            except:
                w_stat, p_val_w = 0, 1.0
        else:
            t_stat, p_val_t, w_stat, p_val_w = 0, 1.0, 0, 1.0

        summary[pol] = {
            "mean_delta": mean_v if pol != "Raw_Q50" else 0.0,
            "mean_reward": float(np.mean(p_rews)),
            "median_delta": med_v if pol != "Raw_Q50" else 0.0,
            "sd_delta": sd_v if pol != "Raw_Q50" else float(np.std(p_rews)),
            "ci95": ci95 if pol != "Raw_Q50" else [0, 0],
            "win_rate": win_rate,
            "win_rate_excl": win_rate_excl,
            "wins": wins, "ties": ties, "losses": losses,
            "min_delta": min_d,
            "p05": p05,
            "max_delta": max_d,
            "p_lt_0": p_lt_0,
            "p_lt_500": p_lt_500,
            "p_lt_1000": p_lt_1000,
            "p_val_t": float(p_val_t),
            "p_val_w": float(p_val_w)
        }

    fmt = "{:<10s} | {:<12s} | {:<12s} | {:<10s} | {:<16s} | {:<10s} | {:<10s} | {:<10s} | {:<10s}"
    print(fmt.format("Policy", "Mean Delta", "Median Delta", "SD Delta", "95% Paired CI", "Win (Excl)", "Min Delta", "p05 Delta", "p-value (t)"))
    print("-" * 120)
    for pol in policies:
        if pol == "Raw_Q50":
            print(f"{pol:<10s} | {'$0.00 (Ref)':<12s} | {'$0.00':<12s} | {summary[pol]['sd_delta']:10,.0f} | {'—':<16s} | {'—':<10s} | {summary[pol]['min_delta']:10,.0f} | {summary[pol]['p05']:10,.0f} | —")
        else:
            s = summary[pol]
            ci_str = f"[{s['ci95'][0]:+.0f}, {s['ci95'][1]:+.0f}]"
            print(fmt.format(
                pol,
                f"${s['mean_delta']:+,.2f}",
                f"${s['median_delta']:+,.2f}",
                f"${s['sd_delta']:,.2f}",
                ci_str,
                f"{s['win_rate_excl']:.1f}%",
                f"${s['min_delta']:+,.2f}",
                f"${s['p05']:+,.2f}",
                f"{s['p_val_t']:.5f}"
            ))

    # Phase 4: B1 Conditional Quartile Stability Analysis
    print("\n" + "=" * 100)
    print("PHASE 4: B1 (WEED GATING ONLY) CONDITIONAL STABILITY ACROSS BASELINE QUARTILES")
    print("=" * 100)
    
    b1_records = []
    for s in seeds:
        s_str = str(s)
        q_r = q50_data[s_str]["reward"]
        b1_r = data["B1"][s_str]["reward"]
        d = b1_r - q_r
        b1_records.append({
            "seed": s, "q_rew": q_r, "b1_rew": b1_r, "delta": d,
            "moves_q": q50_data[s_str]["moves"], "moves_b1": data["B1"][s_str]["moves"],
            "weeds_q": q50_data[s_str]["avg_weeds"],
            "dig_q": q50_data[s_str]["dig"], "dig_b1": data["B1"][s_str]["dig"],
            "straw_q": q50_data[s_str]["sold_qty"].get("STRAWBERRY", 0),
            "straw_b1": data["B1"][s_str]["sold_qty"].get("STRAWBERRY", 0),
        })

    b1_records.sort(key=lambda x: x["q_rew"])
    q_size = n // 4
    b1_quartiles = {
        "Q1 (Struggling)": b1_records[:q_size],
        "Q2 (Lower-Mid)": b1_records[q_size:2*q_size],
        "Q3 (Upper-Mid)": b1_records[2*q_size:3*q_size],
        "Q4 (Prosperous)": b1_records[3*q_size:]
    }

    for q_name, part in b1_quartiles.items():
        deltas = np.array([r["delta"] for r in part])
        m_d = float(np.mean(deltas))
        med_d = float(np.median(deltas))
        sd_d = float(np.std(deltas, ddof=1))
        wins = int(np.sum(deltas > 0))
        losses = int(np.sum(deltas < 0))
        ties = int(np.sum(deltas == 0))
        w_excl = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
        min_loss = float(np.min(deltas))
        p_lt_500 = float(np.mean(deltas < -500) * 100)
        p_lt_1000 = float(np.mean(deltas < -1000) * 100)

        rng = np.random.default_rng(42)
        boot = [np.mean(rng.choice(deltas, size=len(deltas), replace=True)) for _ in range(10000)]
        ci95 = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

        print(f"\n{q_name} (N={len(part)}, Baseline: [${part[0]['q_rew']:,.0f}, ${part[-1]['q_rew']:,.0f}]):")
        print(f"  Mean Delta:        ${m_d:+,.2f} (95% CI: [${ci95[0]:+,.2f}, ${ci95[1]:+,.2f}])")
        print(f"  Median Delta:      ${med_d:+,.2f} | SD: ${sd_d:,.2f}")
        print(f"  Win / Tie / Loss:  {wins} / {ties} / {losses} (Win Rate excl ties: {w_excl:.1f}%)")
        print(f"  Losses < -$500:    {p_lt_500:.1f}% | Losses < -$1,000: {p_lt_1000:.1f}%")
        print(f"  Worst Loss:        ${min_loss:+,.2f}")

    # Phase 5: Worst-Loss Forensics for B1
    print("\n" + "=" * 100)
    print("PHASE 5: FORENSICS OF THE WORST B1 LOSSES")
    print("=" * 100)
    b1_records.sort(key=lambda x: x["delta"])
    worst_b1 = b1_records[:10]
    for rank, r in enumerate(worst_b1, 1):
        s_str = str(r["seed"])
        q_item = q50_data[s_str]
        b1_item = data["B1"][s_str]
        print(f"Rank {rank:2d} | Seed {r['seed']} | Delta: ${r['delta']:+9.2f} (Cand: ${r['b1_rew']:9.2f}, Q50: ${r['q_rew']:9.2f})")
        print(f"  Straw Sold: Q50={q_item['sold_qty'].get('STRAWBERRY', 0):2d} u, B1={b1_item['sold_qty'].get('STRAWBERRY', 0):2d} u (Diff {b1_item['sold_qty'].get('STRAWBERRY', 0) - q_item['sold_qty'].get('STRAWBERRY', 0):+2d} u)")
        print(f"  Moves:      Q50={q_item['moves']:4d}, B1={b1_item['moves']:4d} (Diff {b1_item['moves'] - q_item['moves']:+3d})")
        print(f"  Digs:       Q50={q_item['dig']:3d}, B1={b1_item['dig']:3d} (Diff {b1_item['dig'] - q_item['dig']:+3d})")
        print(f"  Harvests:   Q50={q_item['harvest']:3d}, B1={b1_item['harvest']:3d} (Diff {b1_item['harvest'] - q_item['harvest']:+3d})")
        print(f"  Waters:     Q50={q_item['water']:3d}, B1={b1_item['water']:3d} (Diff {b1_item['water'] - q_item['water']:+3d})")
        print(f"  Deaths:     Q50={q_item['straw_deaths']}, B1={b1_item['straw_deaths']}")
        print(f"  Miss Water: Q50={q_item['missed_water']}, B1={b1_item['missed_water']}")

    out = {
        "summary": summary,
        "b1_quartiles": b1_quartiles,
        "worst_b1": worst_b1
    }
    with open("scratch/clean_discovery_841000_analysis.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

if __name__ == "__main__":
    analyze()
