import json
import os
import sys
import numpy as np
import scipy.stats as stats

def run_comprehensive_audit():
    with open("scratch/200seed_validation_raw.json") as f:
        data = json.load(f)

    seeds = sorted([int(s) for s in data["Baseline"].keys()])
    n_seeds = len(seeds)
    print(f"Loaded {n_seeds} seeds from scratch/200seed_validation_raw.json")

    rews_a = np.array([data["Baseline"][str(s)]["reward"] for s in seeds])
    rews_b = np.array([data["Gated_M1"][str(s)]["reward"] for s in seeds])
    diff_rew = rews_b - rews_a

    # ==========================================
    # PHASE 3: PRIMARY STATISTICAL TEST
    # ==========================================
    mean_a = float(np.mean(rews_a))
    mean_b = float(np.mean(rews_b))
    m_diff = float(np.mean(diff_rew))
    med_diff = float(np.median(diff_rew))
    std_diff = float(np.std(diff_rew, ddof=1))
    se_diff = std_diff / np.sqrt(n_seeds)

    # 100,000 bootstrap iterations
    np.random.seed(42)
    boot_means = np.array([np.mean(np.random.choice(diff_rew, size=n_seeds, replace=True)) for _ in range(100000)])
    ci_95 = (float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5)))
    ci_99 = (float(np.percentile(boot_means, 0.5)), float(np.percentile(boot_means, 99.5)))

    # Paired permutation test (100,000 permutations)
    signs = np.random.choice([-1, 1], size=(100000, n_seeds))
    perm_means = np.mean(diff_rew * signs, axis=1)
    perm_p = float(np.mean(np.abs(perm_means) >= np.abs(m_diff)))

    t_stat, t_p = stats.ttest_rel(rews_b, rews_a)
    cohens_d = m_diff / std_diff

    # Wilcoxon signed rank test
    wilc_stat, wilc_p = stats.wilcoxon(diff_rew)

    wins = int(np.sum(diff_rew > 0))
    losses = int(np.sum(diff_rew < 0))
    ties = int(np.sum(diff_rew == 0))
    win_rate = (wins / n_seeds) * 100.0

    min_diff = float(np.min(diff_rew))
    max_diff = float(np.max(diff_rew))
    q25 = float(np.percentile(diff_rew, 25))
    q75 = float(np.percentile(diff_rew, 75))
    iqr = q75 - q25

    print("PHASE 3 COMPLETE:")
    print(f"  Mean Delta: ${m_diff:,.2f} | Median: ${med_diff:,.2f} | SD: ${std_diff:,.2f} | SE: ${se_diff:,.2f}")
    print(f"  95% CI: [${ci_95[0]:,.2f}, ${ci_95[1]:,.2f}]")
    print(f"  99% CI: [${ci_99[0]:,.2f}, ${ci_99[1]:,.2f}]")
    print(f"  Permutation p: {perm_p:.5f} | t-test p: {t_p:.5f} | Wilcoxon p: {wilc_p:.5f}")
    print(f"  Cohen's d: {cohens_d:.4f} | Win Rate: {wins}/{n_seeds} ({win_rate:.1f}%)")

    # ==========================================
    # PHASE 4: PRACTICAL SIGNIFICANCE
    # ==========================================
    t_1pct = 0.01 * mean_a
    t_2pct = 0.02 * mean_a
    t_3pct = 0.03 * mean_a
    t_5pct = 0.05 * mean_a

    p_1pct = float(np.mean(boot_means >= t_1pct)) * 100.0
    p_2pct = float(np.mean(boot_means >= t_2pct)) * 100.0
    p_3pct = float(np.mean(boot_means >= t_3pct)) * 100.0
    p_5pct = float(np.mean(boot_means >= t_5pct)) * 100.0
    p_zero = float(np.mean(boot_means >= 0.0)) * 100.0

    print("PHASE 4 COMPLETE:")
    print(f"  P(M1 >= +1% [${t_1pct:,.0f}]): {p_1pct:.2f}%")
    print(f"  P(M1 >= +2% [${t_2pct:,.0f}]): {p_2pct:.2f}%")
    print(f"  P(M1 >= +3% [${t_3pct:,.0f}]): {p_3pct:.2f}%")
    print(f"  P(M1 >= +5% [${t_5pct:,.0f}]): {p_5pct:.2f}%")
    print(f"  P(M1 > $0): {p_zero:.2f}%")

    # ==========================================
    # PHASE 5: DISTRIBUTION & EXTREMES
    # ==========================================
    # Quantiles
    quantiles = [1, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99]
    q_table = {q: float(np.percentile(diff_rew, q)) for q in quantiles}

    # Histogram bins
    hist_counts, hist_edges = np.histogram(diff_rew, bins=10)
    hist_data = [{"bin_start": float(hist_edges[i]), "bin_end": float(hist_edges[i+1]), "count": int(hist_counts[i])} for i in range(len(hist_counts))]

    # Outliers: beyond Q1 - 1.5*IQR or Q3 + 1.5*IQR
    lower_whisker = max(min_diff, q25 - 1.5 * iqr)
    upper_whisker = min(max_diff, q75 + 1.5 * iqr)
    outliers = [float(x) for x in diff_rew if x < lower_whisker or x > upper_whisker]

    # Detailed metrics per seed for extreme analysis
    seed_details = []
    for s in seeds:
        b = data["Baseline"][str(s)]
        g = data["Gated_M1"][str(s)]
        
        # Count strawberry shops: BRUNCH_SPOT, ICE_CREAM_SHOP, SMOOTHIE_SHOP, FARMERS_MARKET
        sb = sum(1 for x in b["unlocked_shops"] if x in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        sg = sum(1 for x in g["unlocked_shops"] if x in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        # Count milk shops: PIZZA_SHOP, ICE_CREAM_SHOP, SMOOTHIE_SHOP
        mb = sum(1 for x in b["unlocked_shops"] if x in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
        mg = sum(1 for x in g["unlocked_shops"] if x in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
        
        d_rew = g["reward"] - b["reward"]
        d_str_rev = g["straw_rev"] - b["straw_rev"]
        d_mlk_rev = g["milk_rev"] - b["milk_rev"]
        d_woo_rev = g["wool_rev"] - b["wool_rev"]
        d_frt_rev = g["fert_rev"] - b["fert_rev"]
        d_mel_rev = g["melon_rev"] - b["melon_rev"]
        d_wht_rev = g["wheat_rev"] - b["wheat_rev"]
        d_exp = g["total_exp"] - b["total_exp"]
        
        seed_details.append({
            "seed": s, "d_rew": d_rew,
            "d_str_rev": d_str_rev, "d_mlk_rev": d_mlk_rev,
            "d_woo_rev": d_woo_rev, "d_frt_rev": d_frt_rev,
            "d_mel_rev": d_mel_rev, "d_wht_rev": d_wht_rev,
            "d_exp": d_exp,
            "d_str_shp": sg - sb, "d_mlk_shp": mg - mb,
            "term_sp_b": b["straw_avg_p"], "term_sp_g": g["straw_avg_p"],
            "term_mp_b": b["milk_avg_p"], "term_mp_g": g["milk_avg_p"],
        })

    sorted_seeds = sorted(seed_details, key=lambda x: x["d_rew"])
    worst_10 = sorted_seeds[:10]
    best_10 = sorted_seeds[-10:]

    # ==========================================
    # PHASE 6: STRATIFY BY TOWN-SHOP OUTCOME
    # ==========================================
    # Group 1: M1 gets more/equal strawberry + milk shops (sg - sb + mg - mb >= 0)
    # Group 2: M1 gets fewer strawberry + milk shops (sg - sb + mg - mb < 0)
    g1 = [x for x in seed_details if (x["d_str_shp"] + x["d_mlk_shp"]) >= 0]
    g2 = [x for x in seed_details if (x["d_str_shp"] + x["d_mlk_shp"]) < 0]

    d_rew_g1 = [x["d_rew"] for x in g1]
    d_rew_g2 = [x["d_rew"] for x in g2]

    m_rew_g1 = float(np.mean(d_rew_g1))
    med_rew_g1 = float(np.median(d_rew_g1))
    std_rew_g1 = float(np.std(d_rew_g1, ddof=1))
    win_g1 = float(np.sum(np.array(d_rew_g1) > 0)) / len(g1) * 100.0

    m_rew_g2 = float(np.mean(d_rew_g2))
    med_rew_g2 = float(np.median(d_rew_g2))
    std_rew_g2 = float(np.std(d_rew_g2, ddof=1))
    win_g2 = float(np.sum(np.array(d_rew_g2) > 0)) / len(g2) * 100.0

    mean_shop_diff_g1 = float(np.mean([x["d_str_shp"] + x["d_mlk_shp"] for x in g1]))
    mean_shop_diff_g2 = float(np.mean([x["d_str_shp"] + x["d_mlk_shp"] for x in g2]))

    mean_straw_p_diff_g1 = float(np.mean([x["term_sp_g"] - x["term_sp_b"] for x in g1]))
    mean_straw_p_diff_g2 = float(np.mean([x["term_sp_g"] - x["term_sp_b"] for x in g2]))

    mean_milk_p_diff_g1 = float(np.mean([x["term_mp_g"] - x["term_mp_b"] for x in g1]))
    mean_milk_p_diff_g2 = float(np.mean([x["term_mp_g"] - x["term_mp_b"] for x in g2]))

    # ==========================================
    # PHASE 7: STATISTICAL CONTROL (REGRESSION / ANCOVA)
    # ==========================================
    # Model: DeltaReward = b0 + b_milk * DeltaMilkShops + b_straw * DeltaStrawShops
    Y = np.array([x["d_rew"] for x in seed_details])
    X = np.column_stack([
        np.ones(len(seed_details)),
        [x["d_mlk_shp"] for x in seed_details],
        [x["d_str_shp"] for x in seed_details]
    ])
    beta, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)
    y_pred = X @ beta
    ss_tot = np.sum((Y - np.mean(Y))**2)
    ss_res = np.sum((Y - y_pred)**2)
    r2 = float(1 - (ss_res / ss_tot))

    df_e = len(Y) - X.shape[1]
    mse = ss_res / df_e
    var_beta = mse * np.linalg.inv(X.T @ X)
    se_beta = np.sqrt(np.diagonal(var_beta))
    t_vals = beta / se_beta
    p_vals = 2 * (1 - stats.t.cdf(np.abs(t_vals), df=df_e))

    # Partial R2 for each predictor
    # Intercept only
    ss_res_null = np.sum((Y - np.mean(Y))**2)
    # Without milk shops
    X_no_milk = np.column_stack([np.ones(len(Y)), [x["d_str_shp"] for x in seed_details]])
    beta_no_milk, _, _, _ = np.linalg.lstsq(X_no_milk, Y, rcond=None)
    ss_res_no_milk = np.sum((Y - X_no_milk @ beta_no_milk)**2)
    partial_r2_milk = (ss_res_no_milk - ss_res) / ss_res_no_milk

    # Without straw shops
    X_no_straw = np.column_stack([np.ones(len(Y)), [x["d_mlk_shp"] for x in seed_details]])
    beta_no_straw, _, _, _ = np.linalg.lstsq(X_no_straw, Y, rcond=None)
    ss_res_no_straw = np.sum((Y - X_no_straw @ beta_no_straw)**2)
    partial_r2_straw = (ss_res_no_straw - ss_res) / ss_res_no_straw

    # ==========================================
    # PHASE 9: NON-MARKET ECONOMIC ADVANTAGE RECONSTRUCTION
    # ==========================================
    nm_arr = np.array([x["d_frt_rev"] + x["d_woo_rev"] + x["d_mel_rev"] + x["d_wht_rev"] - x["d_exp"] for x in seed_details])
    nm_mean = float(np.mean(nm_arr))
    nm_med = float(np.median(nm_arr))
    nm_std = float(np.std(nm_arr, ddof=1))
    nm_se = nm_std / np.sqrt(n_seeds)
    boot_nm = np.array([np.mean(np.random.choice(nm_arr, size=n_seeds, replace=True)) for _ in range(100000)])
    nm_ci95 = (float(np.percentile(boot_nm, 2.5)), float(np.percentile(boot_nm, 97.5)))

    nm_components = {
        "fertilizer_rev_delta": float(np.mean([x["d_frt_rev"] for x in seed_details])),
        "wool_rev_delta": float(np.mean([x["d_woo_rev"] for x in seed_details])),
        "melon_rev_delta": float(np.mean([x["d_mel_rev"] for x in seed_details])),
        "wheat_rev_delta": float(np.mean([x["d_wht_rev"] for x in seed_details])),
        "expenditure_savings": float(-np.mean([x["d_exp"] for x in seed_details])),
        "total_non_market": nm_mean
    }

    # ==========================================
    # PHASE 10: ACTION PROFILES & HIDDEN COSTS
    # ==========================================
    actions_summary = {}
    action_keys = ["FERTILIZE", "WATER", "CARE", "FEED", "COLLECT_FERT", "HARVEST_STRAW", "HARVEST_OTHER", "DROP", "MOVE", "PASS"]
    for ak in action_keys:
        b_vals = [data["Baseline"][str(s)]["actions_count"].get(ak, 0) for s in seeds]
        g_vals = [data["Gated_M1"][str(s)]["actions_count"].get(ak, 0) for s in seeds]
        actions_summary[ak] = {
            "baseline_mean": float(np.mean(b_vals)),
            "gated_mean": float(np.mean(g_vals)),
            "delta": float(np.mean(g_vals) - np.mean(b_vals)),
            "p_val": float(stats.ttest_rel(g_vals, b_vals)[1])
        }

    # Physical sales & units
    commodities = ["STRAWBERRY", "MELON", "MILK", "WOOL", "WHEAT", "FERTILIZER"]
    units_sold_summary = {}
    for c in commodities:
        b_u = [data["Baseline"][str(s)]["qty_sold"].get(c, 0) for s in seeds]
        g_u = [data["Gated_M1"][str(s)]["qty_sold"].get(c, 0) for s in seeds]
        units_sold_summary[c] = {
            "baseline_units": float(np.mean(b_u)),
            "gated_units": float(np.mean(g_u)),
            "delta_units": float(np.mean(g_u) - np.mean(b_u)),
            "p_val": float(stats.ttest_rel(g_u, b_u)[1])
        }

    # Expenditures breakdown
    exp_keys = ["exp_animals", "exp_seeds", "exp_feed", "exp_land", "exp_hires", "total_exp"]
    exp_summary = {}
    for ek in exp_keys:
        b_e = [data["Baseline"][str(s)][ek] for s in seeds]
        g_e = [data["Gated_M1"][str(s)][ek] for s in seeds]
        exp_summary[ek] = {
            "baseline_exp": float(np.mean(b_e)),
            "gated_exp": float(np.mean(g_e)),
            "delta_exp": float(np.mean(g_e) - np.mean(b_e)),
            "p_val": float(stats.ttest_rel(g_e, b_e)[1])
        }

    # Shed logistics
    b_shed_max = [data["Baseline"][str(s)]["max_shed_fill"] for s in seeds]
    g_shed_max = [data["Gated_M1"][str(s)]["max_shed_fill"] for s in seeds]
    b_shed_term = [data["Baseline"][str(s)]["term_shed_inv"] for s in seeds]
    g_shed_term = [data["Gated_M1"][str(s)]["term_shed_inv"] for s in seeds]

    shed_summary = {
        "max_fill_baseline": float(np.mean(b_shed_max)),
        "max_fill_gated": float(np.mean(g_shed_max)),
        "max_fill_delta": float(np.mean(g_shed_max) - np.mean(b_shed_max)),
        "term_inv_baseline": float(np.mean(b_shed_term)),
        "term_inv_gated": float(np.mean(g_shed_term)),
        "term_inv_delta": float(np.mean(g_shed_term) - np.mean(b_shed_term))
    }

    # Save all summary statistics to JSON
    audit_results = {
        "n_seeds": n_seeds,
        "phase3_primary": {
            "baseline_mean": mean_a, "gated_mean": mean_b,
            "mean_delta": m_diff, "median_delta": med_diff,
            "std_delta": std_diff, "se_delta": se_diff,
            "ci_95": ci_95, "ci_99": ci_99,
            "perm_p": perm_p, "t_stat": float(t_stat), "t_p": float(t_p),
            "wilcoxon_stat": float(wilc_stat), "wilcoxon_p": float(wilc_p),
            "cohens_d": float(cohens_d),
            "min_diff": min_diff, "max_diff": max_diff,
            "q25": q25, "q75": q75, "iqr": float(iqr),
            "wins": wins, "losses": losses, "ties": ties, "win_rate": win_rate
        },
        "phase4_practical": {
            "t_1pct": t_1pct, "p_1pct": p_1pct,
            "t_2pct": t_2pct, "p_2pct": p_2pct,
            "t_3pct": t_3pct, "p_3pct": p_3pct,
            "t_5pct": t_5pct, "p_5pct": p_5pct,
            "p_zero": p_zero
        },
        "phase5_distribution": {
            "quantiles": q_table,
            "histogram": hist_data,
            "box_stats": {
                "min": min_diff, "q25": q25, "median": med_diff, "q75": q75, "max": max_diff,
                "lower_whisker": lower_whisker, "upper_whisker": upper_whisker,
                "outliers_count": len(outliers), "outliers": outliers
            },
            "worst_10": worst_10,
            "best_10": best_10
        },
        "phase6_stratified": {
            "g1_count": len(g1), "g1_mean_delta": m_rew_g1, "g1_med_delta": med_rew_g1, "g1_std_delta": std_rew_g1, "g1_win_rate": win_g1, "g1_shop_diff": mean_shop_diff_g1, "g1_straw_p_diff": mean_straw_p_diff_g1, "g1_milk_p_diff": mean_milk_p_diff_g1,
            "g2_count": len(g2), "g2_mean_delta": m_rew_g2, "g2_med_delta": med_rew_g2, "g2_std_delta": std_rew_g2, "g2_win_rate": win_g2, "g2_shop_diff": mean_shop_diff_g2, "g2_straw_p_diff": mean_straw_p_diff_g2, "g2_milk_p_diff": mean_milk_p_diff_g2
        },
        "phase7_regression": {
            "intercept": float(beta[0]), "intercept_se": float(se_beta[0]), "intercept_t": float(t_vals[0]), "intercept_p": float(p_vals[0]),
            "b_milk": float(beta[1]), "b_milk_se": float(se_beta[1]), "b_milk_t": float(t_vals[1]), "b_milk_p": float(p_vals[1]), "partial_r2_milk": float(partial_r2_milk),
            "b_straw": float(beta[2]), "b_straw_se": float(se_beta[2]), "b_straw_t": float(t_vals[2]), "b_straw_p": float(p_vals[2]), "partial_r2_straw": float(partial_r2_straw),
            "r_squared": r2
        },
        "phase9_non_market": {
            "mean": nm_mean, "median": nm_med, "std": nm_std, "se": nm_se, "ci95": nm_ci95,
            "components": nm_components
        },
        "phase10_actions": actions_summary,
        "phase10_units": units_sold_summary,
        "phase10_expenditures": exp_summary,
        "phase10_shed": shed_summary
    }

    with open("scratch/comprehensive_200seed_metrics.json", "w") as f:
        json.dump(audit_results, f, indent=2)

    print("\nSaved comprehensive audit metrics to scratch/comprehensive_200seed_metrics.json")

if __name__ == "__main__":
    run_comprehensive_audit()
