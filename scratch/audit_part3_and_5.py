import json
import numpy as np
from scipy import stats

def recompute_b1_numbers():
    with open("scratch/final_b1_qualification_500seeds.json", "r") as f:
        data = json.load(f)

    q50_data = data["Raw_Q50"]
    b1_data = data["B_ONLY"]
    comp_data = data["Compiled_B_ONLY"]

    seeds = sorted([int(s) for s in q50_data.keys()])
    assert len(seeds) == 500, f"Expected 500 seeds, found {len(seeds)}"
    assert seeds[0] == 865000 and seeds[-1] == 865499, f"Unexpected seed range: {seeds[0]}..{seeds[-1]}"

    q50_rewards = []
    b1_rewards = []
    comp_rewards = []
    deltas = []
    comp_deltas = []

    for s in seeds:
        s_str = str(s)
        rq = q50_data[s_str]["reward"]
        rb = b1_data[s_str]["reward"]
        
        q50_rewards.append(rq)
        b1_rewards.append(rb)
        deltas.append(rb - rq)

        if s_str in comp_data:
            rc = comp_data[s_str]["reward"]
            comp_rewards.append(rc)
            comp_deltas.append(rc - rq)

    # 1. Verify Compiled vs Modular identity across all available seeds in file
    comp_mismatches = sum(1 for i, s_str in enumerate(comp_data.keys()) if b1_data[s_str]["reward"] != comp_data[s_str]["reward"])
    print(f"Compiled vs Modular Reward Mismatches on {len(comp_data)} seeds: {comp_mismatches} / {len(comp_data)}")
    assert comp_mismatches == 0, "Compiled vs Modular mismatch on qualification cohort!"

    deltas = np.array(deltas)
    n = len(deltas)

    mean_delta = np.mean(deltas)
    median_delta = np.median(deltas)
    sd_delta = np.std(deltas, ddof=1)
    se_delta = sd_delta / np.sqrt(n)

    # Bootstrap CI
    np.random.seed(42)
    boot_means = [np.mean(np.random.choice(deltas, size=n, replace=True)) for _ in range(10000)]
    ci_95 = [np.percentile(boot_means, 2.5), np.percentile(boot_means, 97.5)]
    ci_99 = [np.percentile(boot_means, 0.5), np.percentile(boot_means, 99.5)]

    # Paired tests
    t_res = stats.ttest_1samp(deltas, 0.0)
    w_res = stats.wilcoxon(deltas[deltas != 0])

    wins = int(np.sum(deltas > 0))
    ties = int(np.sum(deltas == 0))
    losses = int(np.sum(deltas < 0))

    win_rate_inc = wins / n
    win_rate_exc = wins / (wins + losses) if (wins + losses) > 0 else 0.0

    worst_loss = np.min(deltas)
    best_gain = np.max(deltas)

    p_loss_500 = np.mean(deltas < -500)
    p_loss_1000 = np.mean(deltas < -1000)
    p_loss_2000 = np.mean(deltas < -2000)

    print("\n" + "="*80)
    print("PART 3: RECONSTRUCTED B1 NUMBERS (Seeds 865000-865499, N=500)")
    print("="*80)
    print(f"Mean Delta:            {mean_delta:+.2f} (Expected: +204.16)")
    print(f"Median Delta:          {median_delta:+.2f} (Expected: 0.00)")
    print(f"Std Dev (SD):          {sd_delta:.2f}")
    print(f"Standard Error (SE):   {se_delta:.2f}")
    print(f"95% Bootstrap CI:      [{ci_95[0]:.2f}, {ci_95[1]:.2f}] (Expected: [157.45, 252.80])")
    print(f"99% Bootstrap CI:      [{ci_99[0]:.2f}, {ci_99[1]:.2f}] (Expected: [143.04, 269.47])")
    print(f"Paired t-test:         t = {t_res.statistic:.4f}, p = {t_res.pvalue:.4e}")
    print(f"Wilcoxon test:         W = {w_res.statistic:.1f}, p = {w_res.pvalue:.4e}")
    print(f"Record (W/T/L):        {wins} / {ties} / {losses} (Expected: 214 / 192 / 94)")
    print(f"Win Rate (incl ties):  {win_rate_inc*100:.2f}% ({wins}/{n})")
    print(f"Win Rate (excl ties):  {win_rate_exc*100:.2f}% ({wins}/{wins+losses})")
    print(f"Worst Loss:            {worst_loss:.2f} (Expected: -1834)")
    print(f"Best Gain:             {best_gain:.2f}")
    print(f"P(delta < -500):       {p_loss_500*100:.2f}% ({np.sum(deltas < -500)}/{n}) (Expected: 4.20%)")
    print(f"P(delta < -1000):      {p_loss_1000*100:.2f}% ({np.sum(deltas < -1000)}/{n}) (Expected: 0.60%)")
    print(f"P(delta < -2000):      {p_loss_2000*100:.2f}% ({np.sum(deltas < -2000)}/{n}) (Expected: 0.00%)")

    # PART 5: Quantiles and Negative Seed Forensics
    print("\n" + "="*80)
    print("PART 5: B1 DELTA DISTRIBUTION QUANTILES & NEGATIVE TAIL FORENSICS")
    print("="*80)
    quantiles = {
        "min": np.min(deltas),
        "p01": np.percentile(deltas, 1),
        "p05": np.percentile(deltas, 5),
        "p10": np.percentile(deltas, 10),
        "p25": np.percentile(deltas, 25),
        "median": np.median(deltas),
        "p75": np.percentile(deltas, 75),
        "p90": np.percentile(deltas, 90),
        "p95": np.percentile(deltas, 95),
        "p99": np.percentile(deltas, 99),
        "max": np.max(deltas)
    }
    for q_name, val in quantiles.items():
        print(f"  {q_name:6s}: {val:+.2f}")

    # Forensic Analysis of ALL negative-delta seeds
    neg_indices = np.where(deltas < 0)[0]
    print(f"\nAnalyzing ALL {len(neg_indices)} Negative Delta Seeds:")
    
    categories = {
        "MARKET": 0,
        "HARVEST": 0,
        "STRAWBERRY": 0,
        "WHEAT": 0,
        "MILK": 0,
        "MELON": 0,
        "WOOL": 0,
        "MOVEMENT": 0,
        "LABOR": 0,
        "OTHER": 0
    }

    forensic_records = []
    for idx in neg_indices:
        s_str = str(seeds[idx])
        q_item = q50_data[s_str]
        b_item = b1_data[s_str]
        
        d_reward = b_item["reward"] - q_item["reward"]
        
        # Ledger difference
        rev_diff = {}
        for k in set(list(b_item["ledger"].keys()) + list(q_item["ledger"].keys())):
            rb = b_item["ledger"].get(k, 0.0)
            rq = q_item["ledger"].get(k, 0.0)
            if rb != rq:
                rev_diff[k] = rb - rq
                
        act_diff = {}
        for k in set(list(b_item["actions_count"].keys()) + list(q_item["actions_count"].keys())):
            ab = b_item["actions_count"].get(k, 0)
            aq = q_item["actions_count"].get(k, 0)
            if ab != aq:
                act_diff[k] = ab - aq

        move_diff = b_item.get("move_count", 0) - q_item.get("move_count", 0)
        straw_death_diff = b_item.get("strawberry_deaths", 0) - q_item.get("strawberry_deaths", 0)

        # Classification based on largest revenue or action deviation
        cat = "OTHER"
        if straw_death_diff > 0:
            cat = "STRAWBERRY"
        elif "REV_MELON" in rev_diff and rev_diff["REV_MELON"] < -100:
            cat = "MELON"
        elif "REV_STRAWBERRY" in rev_diff and rev_diff["REV_STRAWBERRY"] < -100:
            cat = "STRAWBERRY"
        elif "REV_WOOL" in rev_diff and rev_diff["REV_WOOL"] < -100:
            cat = "WOOL"
        elif "REV_MILK" in rev_diff and rev_diff["REV_MILK"] < -100:
            cat = "MILK"
        elif "REV_WHEAT" in rev_diff and rev_diff["REV_WHEAT"] < -50:
            cat = "WHEAT"
        elif any(k.startswith("EXP_") and rev_diff[k] > 100 for k in rev_diff):
            cat = "MARKET"
        elif abs(move_diff) > 20:
            cat = "MOVEMENT"
        elif act_diff.get("DIG", 0) != 0:
            cat = "HARVEST"
            
        categories[cat] += 1
        forensic_records.append({
            "seed": int(s_str),
            "delta": d_reward,
            "category": cat,
            "rev_diff": rev_diff,
            "act_diff": act_diff,
            "move_diff": move_diff,
            "straw_death_diff": straw_death_diff
        })

    print(f"\nCategorization of {len(neg_indices)} Negative Delta Seeds:")
    for cat, count in categories.items():
        pct = count / len(neg_indices) * 100
        print(f"  {cat:12s}: {count:2d} seeds ({pct:5.1f}%)")

    # Worst 10 losses forensic details
    forensic_records.sort(key=lambda x: x["delta"])
    print(f"\nWorst 10 Losses Forensic Breakdown:")
    for rec in forensic_records[:10]:
        print(f"  Seed {rec['seed']}: Delta={rec['delta']:+.2f} | Category={rec['category']} | StrawDeathsDiff={rec['straw_death_diff']} | MoveDiff={rec['move_diff']}")
        print(f"    Rev Diff: {rec['rev_diff']}")

    return {
        "mean_delta": mean_delta,
        "median_delta": median_delta,
        "sd_delta": sd_delta,
        "se_delta": se_delta,
        "ci_95": ci_95,
        "ci_99": ci_99,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "win_rate_inc": win_rate_inc,
        "win_rate_exc": win_rate_exc,
        "worst_loss": worst_loss,
        "best_gain": best_gain,
        "p_loss_500": p_loss_500,
        "p_loss_1000": p_loss_1000,
        "p_loss_2000": p_loss_2000,
        "quantiles": quantiles,
        "categories": categories
    }

if __name__ == "__main__":
    recompute_b1_numbers()
