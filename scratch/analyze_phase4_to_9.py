import sys
import os
import json
import numpy as np
from scipy import stats
from collections import defaultdict

def compute_bootstrap_ci(data, n_boot=10000, ci=0.95):
    np.random.seed(42)
    boot_means = [np.mean(np.random.choice(data, size=len(data), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1.0 - alpha) * 100))

def main():
    with open("scratch/final_b1_qualification_500seeds.json", "r") as f:
        data = json.load(f)

    seeds = [int(s) for s in sorted(data["Raw_Q50"].keys(), key=lambda x: int(x))]
    N = len(seeds)
    print(f"Loaded {N} seeds ({seeds[0]}..{seeds[-1]}).")

    q50_data = {s: data["Raw_Q50"][str(s)] for s in seeds}
    b1_data = {s: data["B_ONLY"][str(s)] for s in seeds}
    ab_data = {s: data["Frozen_Candidate"][str(s)] for s in seeds}

    # =========================================================================
    # PHASE 12: ACCOUNTING IDENTITY VERIFICATION
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 12: ACCOUNTING VERIFICATION")
    print("="*80)
    max_diff_q50 = max(q50_data[s]["diff"] for s in seeds)
    max_diff_b1 = max(b1_data[s]["diff"] for s in seeds)
    max_diff_ab = max(ab_data[s]["diff"] for s in seeds)
    print(f"Max accounting diff Q50: {max_diff_q50:.2e}")
    print(f"Max accounting diff B1:  {max_diff_b1:.2e}")
    print(f"Max accounting diff A+B: {max_diff_ab:.2e}")
    assert max(max_diff_q50, max_diff_b1, max_diff_ab) < 1e-6, "Machine precision accounting failed!"
    print("ALL 1,500 games pass exact accounting: start_cash + rev - exp == reward to machine precision.")

    deltas = np.array([b1_data[s]["reward"] - q50_data[s]["reward"] for s in seeds])
    mean_delta = float(np.mean(deltas))
    independent_mean = float(np.sum([b1_data[s]["reward"] - q50_data[s]["reward"] for s in seeds]) / N)
    print(f"Reported mean: {mean_delta:.4f}")
    print(f"Independent sum/N mean: {independent_mean:.4f}")
    assert abs(mean_delta - independent_mean) < 1e-9, "Independent mean verification failed!"

    # =========================================================================
    # PHASE 4: STATISTICAL TESTS
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 4: STATISTICAL TESTS (B_ONLY vs Raw_Q50)")
    print("="*80)
    median_delta = float(np.median(deltas))
    sd_delta = float(np.std(deltas, ddof=1))
    se_delta = sd_delta / np.sqrt(N)
    ci95_low, ci95_high = compute_bootstrap_ci(deltas, ci=0.95)
    ci99_low, ci99_high = compute_bootstrap_ci(deltas, ci=0.99)
    ttest_res = stats.ttest_rel([b1_data[s]["reward"] for s in seeds], [q50_data[s]["reward"] for s in seeds])
    # Wilcoxon signed rank test (exclude zero diffs)
    non_zero_deltas = deltas[deltas != 0]
    if len(non_zero_deltas) > 0:
        wilcoxon_res = stats.wilcoxon(non_zero_deltas)
        w_stat, w_p = wilcoxon_res.statistic, wilcoxon_res.pvalue
    else:
        w_stat, w_p = 0, 1.0

    wins = int(np.sum(deltas > 0))
    ties = int(np.sum(deltas == 0))
    losses = int(np.sum(deltas < 0))
    win_rate_inc = wins / N
    win_rate_exc = wins / (wins + losses) if (wins + losses) > 0 else 0.0

    p_neg = float(np.mean(deltas < 0))
    p_250 = float(np.mean(deltas < -250))
    p_500 = float(np.mean(deltas < -500))
    p_750 = float(np.mean(deltas < -750))
    p_1000 = float(np.mean(deltas < -1000))
    p_1500 = float(np.mean(deltas < -1500))
    p_2000 = float(np.mean(deltas < -2000))
    p_5000 = float(np.mean(deltas < -5000))

    print(f"N:                     {N}")
    print(f"Mean Delta:            +${mean_delta:.2f}")
    print(f"Median Delta:          +${median_delta:.2f}")
    print(f"Standard Deviation:    ${sd_delta:.2f}")
    print(f"Standard Error:        ${se_delta:.2f}")
    print(f"95% Bootstrap CI:      [+${ci95_low:.2f}, +${ci95_high:.2f}]")
    print(f"99% Bootstrap CI:      [+${ci99_low:.2f}, +${ci99_high:.2f}]")
    print(f"Paired t-test:         t = {ttest_res.statistic:.4f}, p = {ttest_res.pvalue:.4e}")
    print(f"Wilcoxon signed-rank:  W = {w_stat:.1f}, p = {w_p:.4e}")
    print(f"Wins / Ties / Losses:  {wins} / {ties} / {losses}")
    print(f"Win Rate (inc ties):   {win_rate_inc*100:.2f}%")
    print(f"Win Rate (exc ties):   {win_rate_exc*100:.2f}%")
    print(f"\nTail Probabilities:")
    print(f"P(delta < 0):          {p_neg*100:.2f}% ({losses}/{N})")
    print(f"P(delta < -250):       {p_250*100:.2f}% ({int(np.sum(deltas < -250))}/{N})")
    print(f"P(delta < -500):       {p_500*100:.2f}% ({int(np.sum(deltas < -500))}/{N})")
    print(f"P(delta < -750):       {p_750*100:.2f}% ({int(np.sum(deltas < -750))}/{N})")
    print(f"P(delta < -1000):      {p_1000*100:.2f}% ({int(np.sum(deltas < -1000))}/{N})")
    print(f"P(delta < -1500):      {p_1500*100:.2f}% ({int(np.sum(deltas < -1500))}/{N})")
    print(f"P(delta < -2000):      {p_2000*100:.2f}% ({int(np.sum(deltas < -2000))}/{N})")
    print(f"P(delta < -5000):      {p_5000*100:.2f}% ({int(np.sum(deltas < -5000))}/{N})")

    # =========================================================================
    # PHASE 5: TAIL-RISK TEST
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 5: TAIL-RISK PERCENTILES AND 20 WORST LOSSES")
    print("="*80)
    pcts = [0, 1, 5, 10, 25, 75, 90, 95, 99, 100]
    pct_vals = np.percentile(deltas, pcts)
    for p, v in zip(pcts, pct_vals):
        name = "minimum" if p == 0 else ("maximum" if p == 100 else f"{p}th percentile")
        print(f"{name:16s}: {v:+.2f}")

    # Inspect 20 worst losses
    loss_indices = np.argsort(deltas)[:20]
    print(f"\n20 Worst Losses Forensic Breakdown:")
    print(f"{'Seed':<8} {'Delta':<9} {'StrawRev':<9} {'WoolRev':<9} {'MelonRev':<9} {'MilkRev':<9} {'WheatRev':<9} {'FertExp':<9} {'DigAct':<7} {'MoveAct':<8} {'WaterAct':<9} {'HarvAct':<8} {'StrawDth':<9} {'AnimEsc':<8}")
    
    worst_losses_records = []
    for idx in loss_indices:
        s = seeds[idx]
        d = deltas[idx]
        b = b1_data[s]
        q = q50_data[s]
        
        b_led = b["ledger"]
        q_led = q["ledger"]
        b_act = b["actions_count"]
        q_act = q["actions_count"]
        
        d_straw = b_led.get("REV_STRAWBERRY", 0) - q_led.get("REV_STRAWBERRY", 0)
        d_wool = b_led.get("REV_WOOL", 0) - q_led.get("REV_WOOL", 0)
        d_melon = b_led.get("REV_MELON", 0) - q_led.get("REV_MELON", 0)
        d_milk = b_led.get("REV_MILK", 0) - q_led.get("REV_MILK", 0)
        d_wheat = b_led.get("REV_WHEAT", 0) - q_led.get("REV_WHEAT", 0)
        d_fert = b_led.get("EXP_FERT", 0) - q_led.get("EXP_FERT", 0)
        
        d_dig = b_act.get("DIG", 0) - q_act.get("DIG", 0)
        d_move = b["move_count"] - q["move_count"]
        d_water = b_act.get("WATER", 0) - q_act.get("WATER", 0)
        d_harv = b_act.get("HARVEST", 0) - q_act.get("HARVEST", 0)
        d_care = b_act.get("CARE", 0) - q_act.get("CARE", 0)
        d_feed = b_act.get("FEED", 0) - q_act.get("FEED", 0)
        d_straw_dth = b.get("strawberry_deaths", 0) - q.get("strawberry_deaths", 0)
        d_anim_esc = b.get("animal_escapes", 0) - q.get("animal_escapes", 0)
        
        rec = {
            "seed": s, "delta": d,
            "d_straw": d_straw, "d_wool": d_wool, "d_melon": d_melon, "d_milk": d_milk, "d_wheat": d_wheat,
            "d_fert": d_fert, "d_dig": d_dig, "d_move": d_move, "d_water": d_water, "d_harv": d_harv,
            "d_care": d_care, "d_feed": d_feed, "d_straw_dth": d_straw_dth, "d_anim_esc": d_anim_esc
        }
        worst_losses_records.append(rec)
        print(f"{s:<8} {d:<+9.2f} {d_straw:<+9.1f} {d_wool:<+9.1f} {d_melon:<+9.1f} {d_milk:<+9.1f} {d_wheat:<+9.1f} {d_fert:<+9.1f} {d_dig:<+7d} {d_move:<+8d} {d_water:<+9d} {d_harv:<+8d} {d_straw_dth:<+9d} {d_anim_esc:<+8d}")

    # =========================================================================
    # PHASE 6: REGIME STABILITY
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 6: REGIME STABILITY PARTITIONS")
    print("="*80)

    # 1. Q50 Terminal Reward Quartiles
    q50_rews = np.array([q50_data[s]["reward"] for s in seeds])
    q_cuts = np.percentile(q50_rews, [25, 50, 75])
    
    def get_quartile(val, cuts):
        if val <= cuts[0]: return 1
        elif val <= cuts[1]: return 2
        elif val <= cuts[2]: return 3
        else: return 4

    partitions = {
        "Q50 Capital Quartile": [get_quartile(q50_data[s]["reward"], q_cuts) for s in seeds],
        "Q50 Movement Quartile": [get_quartile(q50_data[s]["move_count"], np.percentile([q50_data[x]["move_count"] for x in seeds], [25, 50, 75])) for s in seeds],
        "Mature Strawberry Workload": [get_quartile(q50_data[s]["mature_strawberry_workload"], np.percentile([q50_data[x]["mature_strawberry_workload"] for x in seeds], [25, 50, 75])) for s in seeds],
        "Weed Workload": [get_quartile(q50_data[s]["weed_workload"], np.percentile([q50_data[x]["weed_workload"] for x in seeds], [25, 50, 75])) for s in seeds],
        "Productive Workload": [get_quartile(q50_data[s]["productive_workload"], np.percentile([q50_data[x]["productive_workload"] for x in seeds], [25, 50, 75])) for s in seeds],
    }

    for pname, pvals in partitions.items():
        print(f"\n--- Partition by {pname} ---")
        print(f"{'Quartile':<10} {'N':<6} {'Mean Delta':<12} {'Median':<10} {'Win Rate':<10} {'95% CI':<24} {'Worst Loss':<12} {'P(<-500)':<10} {'P(<-1000)':<10}")
        for q in [1, 2, 3, 4]:
            q_idx = [i for i, v in enumerate(pvals) if v == q]
            q_deltas = deltas[q_idx]
            q_n = len(q_deltas)
            q_mean = float(np.mean(q_deltas))
            q_med = float(np.median(q_deltas))
            q_wr = float(np.mean(q_deltas > 0)) * 100
            q_ci_low, q_ci_high = compute_bootstrap_ci(q_deltas, ci=0.95)
            q_worst = float(np.min(q_deltas))
            q_p500 = float(np.mean(q_deltas < -500)) * 100
            q_p1000 = float(np.mean(q_deltas < -1000)) * 100
            ci_str = f"[{q_ci_low:+.1f}, {q_ci_high:+.1f}]"
            print(f"Q{q:<9} {q_n:<6} {q_mean:<+12.2f} {q_med:<+10.2f} {q_wr:<9.1f}% {ci_str:<24} {q_worst:<+12.2f} {q_p500:<9.1f}% {q_p1000:<9.1f}%")

    # =========================================================================
    # PHASE 7: EFFECT CONCENTRATION
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 7: EFFECT CONCENTRATION")
    print("="*80)
    trimmed_5 = stats.trim_mean(deltas, 0.05)
    trimmed_10 = stats.trim_mean(deltas, 0.10)
    winsor_5 = np.mean(stats.mstats.winsorize(deltas, limits=[0.05, 0.05]))
    
    sorted_deltas = np.sort(deltas)
    bottom_10_mean = float(np.mean(sorted_deltas[:int(N*0.10)]))
    
    # Net gain and positive gain concentration
    total_net_gain = float(np.sum(deltas))
    top_10_deltas = sorted_deltas[int(N*0.90):]
    top_10_gain = float(np.sum(top_10_deltas))
    
    positive_deltas = deltas[deltas > 0]
    total_pos_gain = float(np.sum(positive_deltas))
    top_10_pos_deltas = np.sort(positive_deltas)[int(len(positive_deltas)*0.90):]
    top_10_pos_gain = float(np.sum(top_10_pos_deltas))

    pct_net_from_top10 = (top_10_gain / total_net_gain) * 100 if total_net_gain > 0 else 0
    pct_pos_from_top10 = (top_10_pos_gain / total_pos_gain) * 100 if total_pos_gain > 0 else 0

    print(f"Mean Delta:                  +${mean_delta:.2f}")
    print(f"Median Delta:                +${median_delta:.2f}")
    print(f"5% Trimmed Mean:             +${trimmed_5:.2f}")
    print(f"10% Trimmed Mean:            +${trimmed_10:.2f}")
    print(f"5% Winsorized Mean:          +${winsor_5:.2f}")
    print(f"Bottom 10% Mean:             ${bottom_10_mean:.2f}")
    print(f"Top 10% Contribution to Net: {pct_net_from_top10:.2f}% (${top_10_gain:.2f} / ${total_net_gain:.2f})")
    print(f"Top 10% of Positive Gains:   {pct_pos_from_top10:.2f}% (${top_10_pos_gain:.2f} / ${total_pos_gain:.2f})")

    # =========================================================================
    # PHASE 8: COMMODITY DOWNSIDE
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 8: COMMODITY DOWNSIDE (REVENUE DELTAS)")
    print("="*80)
    commodities = ["STRAWBERRY", "WHEAT", "WOOL", "MILK", "MELON"]
    print(f"{'Commodity':<12} {'Mean':<9} {'Median':<9} {'Win%':<7} {'Loss%':<7} {'Tie%':<7} {'Min':<9} {'P05':<9} {'P25':<9} {'P75':<9} {'P95':<9} {'Max':<9}")
    for comm in commodities:
        rev_key = f"REV_{comm}"
        comm_deltas = np.array([b1_data[s]["ledger"].get(rev_key, 0) - q50_data[s]["ledger"].get(rev_key, 0) for s in seeds])
        c_mean = float(np.mean(comm_deltas))
        c_med = float(np.median(comm_deltas))
        c_win = float(np.mean(comm_deltas > 0)) * 100
        c_loss = float(np.mean(comm_deltas < 0)) * 100
        c_tie = float(np.mean(comm_deltas == 0)) * 100
        c_min = float(np.min(comm_deltas))
        c_p05, c_p25, c_p75, c_p95 = np.percentile(comm_deltas, [5, 25, 75, 95])
        c_max = float(np.max(comm_deltas))
        print(f"{comm:<12} {c_mean:<+9.1f} {c_med:<+9.1f} {c_win:<6.1f}% {c_loss:<6.1f}% {c_tie:<6.1f}% {c_min:<+9.1f} {c_p05:<+9.1f} {c_p25:<+9.1f} {c_p75:<+9.1f} {c_p95:<+9.1f} {c_max:<+9.1f}")

    # Fertilizer expense delta
    fert_deltas = np.array([b1_data[s]["ledger"].get("EXP_FERT", 0) - q50_data[s]["ledger"].get("EXP_FERT", 0) for s in seeds])
    f_mean = float(np.mean(fert_deltas))
    f_med = float(np.median(fert_deltas))
    f_win = float(np.mean(fert_deltas < 0)) * 100 # lower expense is win
    f_loss = float(np.mean(fert_deltas > 0)) * 100
    f_tie = float(np.mean(fert_deltas == 0)) * 100
    f_min = float(np.min(fert_deltas))
    f_p05, f_p25, f_p75, f_p95 = np.percentile(fert_deltas, [5, 25, 75, 95])
    f_max = float(np.max(fert_deltas))
    print(f"{'FERTILIZER':<12} {f_mean:<+9.1f} {f_med:<+9.1f} {f_win:<6.1f}% {f_loss:<6.1f}% {f_tie:<6.1f}% {f_min:<+9.1f} {f_p05:<+9.1f} {f_p25:<+9.1f} {f_p75:<+9.1f} {f_p95:<+9.1f} {f_max:<+9.1f}")

    # =========================================================================
    # PHASE 9: MECHANISM CONFIRMATION
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 9: MECHANISM CONFIRMATION (PHYSICAL ACTION & STATE METRICS)")
    print("="*80)
    actions_to_check = ["DIG", "MOVE", "WATER", "HARVEST", "FEED", "CARE", "PLANT", "FERTILIZE"]
    print(f"{'Action/Metric':<25} {'Raw_Q50 Mean':<15} {'B_ONLY Mean':<15} {'Delta Mean':<15} {'Delta %':<10}")
    
    # Movement is special
    q_move_m = float(np.mean([q50_data[s]["move_count"] for s in seeds]))
    b_move_m = float(np.mean([b1_data[s]["move_count"] for s in seeds]))
    d_move_m = b_move_m - q_move_m
    pct_move = (d_move_m / q_move_m) * 100
    print(f"{'TOTAL MOVEMENT':<25} {q_move_m:<15.1f} {b_move_m:<15.1f} {d_move_m:<+15.1f} {pct_move:<+9.2f}%")

    for act in ["DIG", "WATER", "HARVEST", "FEED", "CARE", "PLANT", "FERTILIZE", "COLLECT_FERTILIZER"]:
        q_act_m = float(np.mean([q50_data[s]["actions_count"].get(act, 0) for s in seeds]))
        b_act_m = float(np.mean([b1_data[s]["actions_count"].get(act, 0) for s in seeds]))
        d_act_m = b_act_m - q_act_m
        pct_act = (d_act_m / q_act_m) * 100 if q_act_m > 0 else 0
        print(f"{act:<25} {q_act_m:<15.1f} {b_act_m:<15.1f} {d_act_m:<+15.1f} {pct_act:<+9.2f}%")

    q_dth_m = float(np.mean([q50_data[s].get("strawberry_deaths", 0) for s in seeds]))
    b_dth_m = float(np.mean([b1_data[s].get("strawberry_deaths", 0) for s in seeds]))
    print(f"{'Strawberry Deaths':<25} {q_dth_m:<15.2f} {b_dth_m:<15.2f} {b_dth_m - q_dth_m:<+15.2f}")

    q_esc_m = float(np.mean([q50_data[s].get("animal_escapes", 0) for s in seeds]))
    b_esc_m = float(np.mean([b1_data[s].get("animal_escapes", 0) for s in seeds]))
    print(f"{'Animal Escapes':<25} {q_esc_m:<15.2f} {b_esc_m:<15.2f} {b_esc_m - q_esc_m:<+15.2f}")

    # =========================================================================
    # PHASE 15: COMPARE B1 TO FROZEN A+B
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 15: B1 VS FROZEN A+B (ON THE EXACT SAME 500 PRISTINE SEEDS)")
    print("="*80)
    ab_deltas = np.array([ab_data[s]["reward"] - q50_data[s]["reward"] for s in seeds])
    b1_vs_ab = np.array([b1_data[s]["reward"] - ab_data[s]["reward"] for s in seeds])

    print(f"{'Metric':<25} {'B1 vs Q50':<18} {'A+B vs Q50':<18} {'B1 vs A+B':<18}")
    print(f"{'Mean Delta':<25} {mean_delta:<+18.2f} {float(np.mean(ab_deltas)):<+18.2f} {float(np.mean(b1_vs_ab)):<+18.2f}")
    print(f"{'Median Delta':<25} {median_delta:<+18.2f} {float(np.median(ab_deltas)):<+18.2f} {float(np.median(b1_vs_ab)):<+18.2f}")
    b1_ci = compute_bootstrap_ci(deltas, ci=0.95)
    ab_ci = compute_bootstrap_ci(ab_deltas, ci=0.95)
    b1_ab_ci = compute_bootstrap_ci(b1_vs_ab, ci=0.95)
    print(f"{'95% Bootstrap CI':<25} [{b1_ci[0]:+.1f}, {b1_ci[1]:+.1f}]      [{ab_ci[0]:+.1f}, {ab_ci[1]:+.1f}]      [{b1_ab_ci[0]:+.1f}, {b1_ab_ci[1]:+.1f}]")
    print(f"{'Win Rate (inc ties)':<25} {win_rate_inc*100:<17.1f}% {float(np.mean(ab_deltas > 0))*100:<17.1f}% {float(np.mean(b1_vs_ab > 0))*100:<17.1f}%")
    print(f"{'Worst Loss':<25} {float(np.min(deltas)):<+18.2f} {float(np.min(ab_deltas)):<+18.2f} {float(np.min(b1_vs_ab)):<+18.2f}")
    print(f"{'P(loss < -$500)':<25} {p_500*100:<17.2f}% {float(np.mean(ab_deltas < -500))*100:<17.2f}% {float(np.mean(b1_vs_ab < -500))*100:<17.2f}%")
    print(f"{'P(loss < -$1000)':<25} {p_1000*100:<17.2f}% {float(np.mean(ab_deltas < -1000))*100:<17.2f}% {float(np.mean(b1_vs_ab < -1000))*100:<17.2f}%")

if __name__ == "__main__":
    main()
