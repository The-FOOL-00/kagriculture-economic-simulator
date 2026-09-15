import json
import os
import sys
import numpy as np
import scipy.stats as stats

def bootstrap_stats(data, n_boot=10000):
    boot_means = np.array([np.mean(np.random.choice(data, size=len(data), replace=True)) for _ in range(n_boot)])
    ci_95 = (np.percentile(boot_means, 2.5), np.percentile(boot_means, 97.5))
    ci_99 = (np.percentile(boot_means, 0.5), np.percentile(boot_means, 99.5))
    return boot_means, ci_95, ci_99

def permutation_test(a, b, n_perm=10000):
    diff = np.array(a) - np.array(b)
    obs = np.mean(diff)
    cnt = 0
    for _ in range(n_perm):
        s = np.random.choice([-1, 1], size=len(diff))
        if abs(np.mean(diff * s)) >= abs(obs):
            cnt += 1
    return cnt / n_perm

def analyze_200seeds(json_path="scratch/200seed_validation_raw.json"):
    with open(json_path) as f:
        data = json.load(f)

    seeds = sorted([int(s) for s in data["Baseline"].keys()])
    n_seeds = len(seeds)
    print("=" * 90)
    print(f"DEFINITIVE 200-SEED STANDARD-ENGINE VALIDATION OF M1 FERTILIZER GATING (N={n_seeds})")
    print("=" * 90)

    rews_a = np.array([data["Baseline"][str(s)]["reward"] for s in seeds])
    rews_b = np.array([data["Gated_M1"][str(s)]["reward"] for s in seeds])
    diff_rew = rews_b - rews_a

    # Phase 3 Primary Statistical Test
    mean_a = np.mean(rews_a)
    mean_b = np.mean(rews_b)
    m_diff = np.mean(diff_rew)
    med_diff = np.median(diff_rew)
    std_diff = np.std(diff_rew, ddof=1)
    se_diff = std_diff / np.sqrt(n_seeds)

    boot_means, ci_95, ci_99 = bootstrap_stats(diff_rew)
    perm_p = permutation_test(rews_b, rews_a)
    t_stat, t_p = stats.ttest_rel(rews_b, rews_a)
    cohens_d = m_diff / std_diff

    wins = int(np.sum(diff_rew > 0))
    losses = int(np.sum(diff_rew < 0))
    ties = int(np.sum(diff_rew == 0))
    win_rate = (wins / n_seeds) * 100

    q25, q75 = np.percentile(diff_rew, [25, 75])
    min_diff, max_diff = np.min(diff_rew), np.max(diff_rew)

    print("\n--- PHASE 3: PRIMARY REWARD STATISTICS ---")
    print(f"Baseline Mean Reward:          ${mean_a:>12,.2f}")
    print(f"Gated M1 Mean Reward:          ${mean_b:>12,.2f}")
    print(f"Mean Delta Reward (M1 - Base): ${m_diff:>12,.2f}")
    print(f"Median Delta Reward:           ${med_diff:>12,.2f}")
    print(f"Standard Deviation:            ${std_diff:>12,.2f}")
    print(f"Standard Error of Mean:        ${se_diff:>12,.2f}")
    print(f"95% Bootstrap CI:              [${ci_95[0]:>10,.2f}, ${ci_95[1]:>10,.2f}]")
    print(f"99% Bootstrap CI:              [${ci_99[0]:>10,.2f}, ${ci_99[1]:>10,.2f}]")
    print(f"Paired Permutation Test p:     {perm_p:.4f}")
    print(f"Paired t-test t / p:           t = {t_stat:>+.3f}, p = {t_p:.4f}")
    print(f"Paired Effect Size (Cohen's d):{cohens_d:>+8.4f}")
    print(f"Min / 25th / 75th / Max:       ${min_diff:>,.0f} / ${q25:>,.0f} / ${q75:>,.0f} / ${max_diff:>,.0f}")
    print(f"Record:                        {wins} Wins ({win_rate:.1f}%) / {losses} Losses / {ties} Ties")

    # Phase 4 Practical Significance
    print("\n--- PHASE 4: PRACTICAL SIGNIFICANCE PROBABILITIES ---")
    thresholds = [
        ("+1% Baseline", 0.01 * mean_a),
        ("+2% Baseline", 0.02 * mean_a),
        ("+3% Baseline", 0.03 * mean_a),
        ("+5% Baseline", 0.05 * mean_a),
        ("> $0 (Any Gain)", 0.0)
    ]
    for lbl, thresh in thresholds:
        prob = np.mean(boot_means >= thresh) * 100
        print(f"  P(Expected M1 Advantage >= {lbl:<15} [${thresh:>6,.0f}]): {prob:>6.2f}%")

    # Phase 5 Distribution Analysis & Extremes
    print("\n--- PHASE 5: DISTRIBUTION QUANTILE TABLE ---")
    quantiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    for q in quantiles:
        print(f"  {q:>2}th Percentile: ${np.percentile(diff_rew, q):>10,.2f}")

    # Best and Worst 10 Seeds
    seed_details = []
    for s in seeds:
        b = data["Baseline"][str(s)]
        g = data["Gated_M1"][str(s)]
        
        sb = sum(1 for x in b["unlocked_shops"] if x in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        sg = sum(1 for x in g["unlocked_shops"] if x in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
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
            "seed": s, "d_rew": d_rew, "d_str_rev": d_str_rev, "d_mlk_rev": d_mlk_rev,
            "d_woo_rev": d_woo_rev, "d_frt_rev": d_frt_rev, "d_mel_rev": d_mel_rev, "d_wht_rev": d_wht_rev,
            "d_exp": d_exp, "d_str_shp": sg - sb, "d_mlk_shp": mg - mb,
            "term_sp": g["straw_avg_p"], "term_mp": g["milk_avg_p"]
        })

    sorted_by_rew = sorted(seed_details, key=lambda x: x["d_rew"])
    
    print("\n--- 10 WORST SEEDS FOR M1 ---")
    print(f"{'Seed':<6} | {'DeltaRew':<11} | {'DeltaStraw':<11} | {'DeltaMilk':<11} | {'DeltaWool':<10} | {'DeltaFert':<10} | {'dShops(S/M)'}")
    print("-" * 75)
    for x in sorted_by_rew[:10]:
        print(f"{x['seed']:<6} | ${x['d_rew']:>+9,.0f} | ${x['d_str_rev']:>+9,.0f} | ${x['d_mlk_rev']:>+9,.0f} | ${x['d_woo_rev']:>+8,.0f} | ${x['d_frt_rev']:>+8,.0f} | {x['d_str_shp']:>+2}/{x['d_mlk_shp']:>+2}")

    print("\n--- 10 BEST SEEDS FOR M1 ---")
    print(f"{'Seed':<6} | {'DeltaRew':<11} | {'DeltaStraw':<11} | {'DeltaMilk':<11} | {'DeltaWool':<10} | {'DeltaFert':<10} | {'dShops(S/M)'}")
    print("-" * 75)
    for x in sorted_by_rew[-10:]:
        print(f"{x['seed']:<6} | ${x['d_rew']:>+9,.0f} | ${x['d_str_rev']:>+9,.0f} | ${x['d_mlk_rev']:>+9,.0f} | ${x['d_woo_rev']:>+8,.0f} | ${x['d_frt_rev']:>+8,.0f} | {x['d_str_shp']:>+2}/{x['d_mlk_shp']:>+2}")

    # Phase 6 Town-Shop Stratification
    print("\n--- PHASE 6: STRATIFICATION BY TOWN-SHOP OUTCOME ---")
    g1 = [x for x in seed_details if (x["d_str_shp"] + x["d_mlk_shp"]) >= 0]
    g2 = [x for x in seed_details if (x["d_str_shp"] + x["d_mlk_shp"]) < 0]
    
    m_rew_g1 = np.mean([x["d_rew"] for x in g1])
    m_rew_g2 = np.mean([x["d_rew"] for x in g2])
    win_g1 = np.sum([x["d_rew"] > 0 for x in g1]) / len(g1) * 100
    win_g2 = np.sum([x["d_rew"] > 0 for x in g2]) / len(g2) * 100
    
    print(f"Group 1 (Equal or MORE S+M Shops, N={len(g1)}): Mean Delta=${m_rew_g1:>+9,.2f} | Win Rate={win_g1:.1f}%")
    print(f"Group 2 (FEWER S+M Shops, N={len(g2)}):         Mean Delta=${m_rew_g2:>+9,.2f} | Win Rate={win_g2:.1f}%")

    # Phase 7 Statistical Control / OLS Regression
    print("\n--- PHASE 7: ANCOVA / OLS REGRESSION (SHOP-CONTROLLED STRATEGY VALUE) ---")
    # DeltaReward = b0 + b_milk * d_milk_shp + b_straw * d_str_shp
    Y = np.array([x["d_rew"] for x in seed_details])
    X = np.column_stack([
        np.ones(len(seed_details)),
        [x["d_mlk_shp"] for x in seed_details],
        [x["d_str_shp"] for x in seed_details]
    ])
    # OLS solution
    beta, residuals, rank, s = np.linalg.lstsq(X, Y, rcond=None)
    y_pred = X @ beta
    ss_tot = np.sum((Y - np.mean(Y))**2)
    ss_res = np.sum((Y - y_pred)**2)
    r2 = 1 - (ss_res / ss_tot)
    
    # Standard errors of coefficients
    df_e = len(Y) - X.shape[1]
    mse = ss_res / df_e
    var_beta = mse * np.linalg.inv(X.T @ X)
    se_beta = np.sqrt(np.diagonal(var_beta))
    t_vals = beta / se_beta
    p_vals = 2 * (1 - stats.t.cdf(np.abs(t_vals), df=df_e))
    
    print(f"Regression Model: DeltaReward = b0 + b_milk * DeltaMilkShops + b_straw * DeltaStrawShops")
    print(f"  Intercept b0 (True Controlled Strategy Value): ${beta[0]:>+9,.2f} (SE=${se_beta[0]:>7,.1f}, t={t_vals[0]:>+.2f}, p={p_vals[0]:.4f})")
    print(f"  Milk Shop Coeff (b_milk):                      ${beta[1]:>+9,.2f} (SE=${se_beta[1]:>7,.1f}, t={t_vals[1]:>+.2f}, p={p_vals[1]:.4f})")
    print(f"  Straw Shop Coeff (b_straw):                    ${beta[2]:>+9,.2f} (SE=${se_beta[2]:>7,.1f}, t={t_vals[2]:>+.2f}, p={p_vals[2]:.4f})")
    print(f"  Model R-squared:                               {r2:.4f} ({r2*100:.1f}% variance explained by shop draws)")

    # Phase 9 Non-Market Economic Advantage
    print("\n--- PHASE 9: NON-MARKET ECONOMIC ADVANTAGE RECONSTRUCTION (200 SEEDS) ---")
    non_market_deltas = []
    d_frt_list = []
    d_woo_list = []
    d_mel_list = []
    d_wht_list = []
    d_exp_list = []
    for s in seeds:
        b = data["Baseline"][str(s)]
        g = data["Gated_M1"][str(s)]
        d_frt = g["fert_rev"] - b["fert_rev"]
        d_woo = g["wool_rev"] - b["wool_rev"]
        d_mel = g["melon_rev"] - b["melon_rev"]
        d_wht = g["wheat_rev"] - b["wheat_rev"]
        d_exp = g["total_exp"] - b["total_exp"]
        nm = d_frt + d_woo + d_mel + d_wht - d_exp
        non_market_deltas.append(nm)
        d_frt_list.append(d_frt)
        d_woo_list.append(d_woo)
        d_mel_list.append(d_mel)
        d_wht_list.append(d_wht)
        d_exp_list.append(d_exp)

    nm_mean = np.mean(non_market_deltas)
    nm_se = np.std(non_market_deltas, ddof=1) / np.sqrt(n_seeds)
    _, nm_ci95, _ = bootstrap_stats(non_market_deltas)
    
    print(f"Total Non-Market Economic Advantage: ${nm_mean:>+9,.2f} (SE=${nm_se:>6,.1f}, 95% CI [${nm_ci95[0]:>+7,.1f}, ${nm_ci95[1]:>+7,.1f}])")
    print(f"  - Fertilizer Cash Revenue Delta:    ${np.mean(d_frt_list):>+9,.2f}")
    print(f"  - Wool Cash Revenue Delta:          ${np.mean(d_woo_list):>+9,.2f}")
    print(f"  - Melon Cash Revenue Delta:         ${np.mean(d_mel_list):>+9,.2f}")
    print(f"  - Wheat Cash Revenue Delta:         ${np.mean(d_wht_list):>+9,.2f}")
    print(f"  - Net Expenditure Savings:          ${-np.mean(d_exp_list):>+9,.2f}")

    # Phase 10 Hidden Cost / Action Profile
    print("\n--- PHASE 10: ACTION ALLOCATION PROFILE (MEANS PER SEED) ---")
    acts = ["FERTILIZE", "WATER", "CARE", "FEED", "COLLECT_FERT", "HARVEST_STRAW", "HARVEST_OTHER", "DROP", "MOVE", "PASS"]
    print(f"{'Action Type':<16} | {'Baseline':<12} | {'Gated M1':<12} | {'Delta':<10}")
    print("-" * 55)
    for a in acts:
        b_cnt = np.mean([data["Baseline"][str(s)]["actions_count"].get(a, 0) for s in seeds])
        g_cnt = np.mean([data["Gated_M1"][str(s)]["actions_count"].get(a, 0) for s in seeds])
        print(f"{a:<16} | {b_cnt:>12.1f} | {g_cnt:>12.1f} | {g_cnt - b_cnt:>+10.1f}")

    # Phase 11 Strawberry Core Physical Metrics
    print("\n--- PHASE 11: CORE STRAWBERRY PHYSICAL METRICS ---")
    b_harv = np.mean([data["Baseline"][str(s)]["straw_harvested"] for s in seeds])
    g_harv = np.mean([data["Gated_M1"][str(s)]["straw_harvested"] for s in seeds])
    b_sold = np.mean([data["Baseline"][str(s)]["straw_sold"] for s in seeds])
    g_sold = np.mean([data["Gated_M1"][str(s)]["straw_sold"] for s in seeds])
    print(f"Strawberry Harvested: Baseline={b_harv:.2f}u, Gated={g_harv:.2f}u (Delta = {g_harv - b_harv:>+5.2f}u)")
    print(f"Strawberry Sold:      Baseline={b_sold:.2f}u, Gated={g_sold:.2f}u (Delta = {g_sold - b_sold:>+5.2f}u)")

if __name__ == "__main__":
    analyze_200seeds()
