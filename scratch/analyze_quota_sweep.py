import json
import numpy as np
from collections import defaultdict
from scipy import stats

def analyze_sweep():
    with open("scratch/wheat_quota_sweep_50seeds_results.json") as f:
        sweep_data = json.load(f)

    # Also load M1 baseline data for paired tests
    with open("scratch/wheat_forensics_50seeds_results.json") as f:
        forensics_data = json.load(f)

    m1_by_seed = {r["seed"]: r for r in forensics_data if r["arm"] == "M1"}
    seeds = sorted(m1_by_seed.keys())
    n = len(seeds)

    # Group sweep data by quota and seed
    sweep_by_quota = defaultdict(dict)
    for r in sweep_data:
        sweep_by_quota[r["quota"]][r["seed"]] = r

    quotas = sorted(sweep_by_quota.keys())

    print(f"=== QUOTA SWEEP ANALYSIS ACROSS {len(quotas)} QUOTAS AND {n} SEEDS ===")

    # -------------------------------------------------------------
    # 1. PRIMARY METRIC: TERMINAL REWARD TABLE
    # -------------------------------------------------------------
    print("\n" + "="*95)
    print("PHASE 6 & 7: TERMINAL REWARD RESPONSE CURVE (50 MATCHED SEEDS)")
    print("="*95)
    
    m1_rews = np.array([m1_by_seed[s]["terminal_reward"] for s in seeds])
    m1_mean = np.mean(m1_rews)
    m1_median = np.median(m1_rews)
    m1_sd = np.std(m1_rews, ddof=1)

    print(f"M1 Certified Base: Mean = ${m1_mean:.2f} | Median = ${m1_median:.2f} | SD = ${m1_sd:.2f}")
    print("-" * 95)
    
    header = f"{'Quota Arm':<10} | {'Mean Reward':<12} | {'Delta vs M1':<13} | {'Median Delta':<13} | {'Std Dev':<10} | {'Win Rate':<9} | {'p-value':<9} | {'Planted Plots':<13}"
    print(header)
    print("-" * len(header))

    quota_metrics = {}
    for q in quotas:
        q_rews = np.array([sweep_by_quota[q][s]["terminal_reward"] for s in seeds])
        q_mean = np.mean(q_rews)
        q_median = np.median(q_rews)
        q_sd = np.std(q_rews, ddof=1)
        
        delta = q_rews - m1_rews
        d_mean = np.mean(delta)
        d_median = np.median(delta)
        win_rate = np.mean(delta > 0) * 100.0
        p_val = stats.ttest_rel(q_rews, m1_rews).pvalue
        
        q_plots = np.mean([sweep_by_quota[q][s]["wheat_planted_plots"] for s in seeds])
        
        quota_metrics[q] = {
            "mean": q_mean, "d_mean": d_mean, "d_median": d_median,
            "sd": q_sd, "win_rate": win_rate, "p_val": p_val, "plots": q_plots
        }
        print(f"Quota {q:<4} | ${q_mean:11.2f} | ${d_mean:+12.2f} | ${d_median:+12.2f} | ${q_sd:9.2f} | {win_rate:8.1f}% | {p_val:9.4f} | {q_plots:13.2f}")

    # -------------------------------------------------------------
    # 2. SECONDARY COMMODITY & COST METRICS
    # -------------------------------------------------------------
    print("\n" + "="*110)
    print("SECONDARY COMMODITY & FINANCIAL METRICS (MEAN PER EPISODE)")
    print("="*110)
    
    hdr2 = f"{'Quota':<6} | {'Wheat Sold':<10} | {'Wheat Harv':<10} | {'Straw Sold':<10} | {'Wool Sold':<10} | {'Milk Sold':<10} | {'Melon Sold':<10} | {'Fert Sold':<10} | {'Seed Exp':<9} | {'Feed Exp':<9} | {'Moves':<7}"
    print(hdr2)
    print("-" * len(hdr2))
    
    # M1 baseline row
    m1_w_sold = np.mean([m1_by_seed[s]["wheat_sold"] for s in seeds])
    m1_w_harv = np.mean([m1_by_seed[s]["wheat_units_harvested"] for s in seeds])
    m1_s_sold = np.mean([m1_by_seed[s]["straw_sold"] for s in seeds])
    m1_wool_sold = np.mean([m1_by_seed[s]["wool_sold"] for s in seeds])
    m1_milk_sold = np.mean([m1_by_seed[s]["milk_sold"] for s in seeds])
    m1_melon_sold = np.mean([m1_by_seed[s]["melon_sold"] for s in seeds])
    m1_fert_sold = np.mean([m1_by_seed[s]["fert_sold"] for s in seeds])
    m1_seed_exp = np.mean([m1_by_seed[s]["exp_seeds"] for s in seeds])
    m1_feed_exp = np.mean([m1_by_seed[s]["exp_feed"] for s in seeds])
    m1_moves = np.mean([m1_by_seed[s]["actions_count"]["MOVE"] for s in seeds])
    print(f"M1Base | {m1_w_sold:10.1f} | {m1_w_harv:10.1f} | {m1_s_sold:10.1f} | {m1_wool_sold:10.1f} | {m1_milk_sold:10.1f} | {m1_melon_sold:10.1f} | {m1_fert_sold:10.1f} | ${m1_seed_exp:8.0f} | ${m1_feed_exp:8.0f} | {m1_moves:7.0f}")

    for q in quotas:
        w_s = np.mean([sweep_by_quota[q][s]["wheat_sold"] for s in seeds])
        w_h = np.mean([sweep_by_quota[q][s]["wheat_harvested_units"] for s in seeds])
        s_s = np.mean([sweep_by_quota[q][s]["straw_sold"] for s in seeds])
        wool_s = np.mean([sweep_by_quota[q][s]["wool_sold"] for s in seeds])
        milk_s = np.mean([sweep_by_quota[q][s]["milk_sold"] for s in seeds])
        melon_s = np.mean([sweep_by_quota[q][s]["melon_sold"] for s in seeds])
        fert_s = np.mean([sweep_by_quota[q][s]["fert_sold"] for s in seeds])
        s_exp = np.mean([sweep_by_quota[q][s]["exp_seeds"] for s in seeds])
        f_exp = np.mean([sweep_by_quota[q][s]["exp_feed"] for s in seeds])
        moves = np.mean([sweep_by_quota[q][s]["moves"] for s in seeds])
        print(f"Q-{q:<4} | {w_s:10.1f} | {w_h:10.1f} | {s_s:10.1f} | {wool_s:10.1f} | {milk_s:10.1f} | {melon_s:10.1f} | {fert_s:10.1f} | ${s_exp:8.0f} | ${f_exp:8.0f} | {moves:7.0f}")

    # -------------------------------------------------------------
    # 3. PHASE 8: STRAWBERRY CANNIBALIZATION TEST PER QUOTA
    # -------------------------------------------------------------
    print("\n" + "="*95)
    print("PHASE 8: STRAWBERRY CANNIBALIZATION TEST PER QUOTA (PAIRED AGAINST M1)")
    print("="*95)
    print(f"{'Quota':<6} | {'Delta Straw Sold':<18} | {'p-value':<9} | {'Delta Straw Harv':<18} | {'p-value':<9} | {'Delta Fert Cycles':<18} | {'p-value':<9}")
    print("-" * 95)
    
    m1_s_sold_arr = np.array([m1_by_seed[s]["straw_sold"] for s in seeds])
    m1_s_harv_arr = np.array([m1_by_seed[s]["straw_harvested_units"] for s in seeds])
    m1_s_fert_arr = np.array([m1_by_seed[s]["straw_fertilized_events"] for s in seeds])

    for q in quotas:
        q_s_sold_arr = np.array([sweep_by_quota[q][s]["straw_sold"] for s in seeds])
        q_s_harv_arr = np.array([sweep_by_quota[q][s]["straw_harvested_units"] for s in seeds])
        q_s_fert_arr = np.array([sweep_by_quota[q][s]["straw_fertilized_events"] for s in seeds])
        
        d_sold = np.mean(q_s_sold_arr - m1_s_sold_arr)
        p_sold = stats.ttest_rel(q_s_sold_arr, m1_s_sold_arr).pvalue
        
        d_harv = np.mean(q_s_harv_arr - m1_s_harv_arr)
        p_harv = stats.ttest_rel(q_s_harv_arr, m1_s_harv_arr).pvalue
        
        d_fert = np.mean(q_s_fert_arr - m1_s_fert_arr)
        p_fert = stats.ttest_rel(q_s_fert_arr, m1_s_fert_arr).pvalue
        
        print(f"Q-{q:<4} | {d_sold:+18.2f}u | {p_sold:9.4f} | {d_harv:+18.2f}u | {p_harv:9.4f} | {d_fert:+18.2f}u | {p_fert:9.4f}")

    # -------------------------------------------------------------
    # 4. PHASE 9: ANIMAL FEED & LIVESTOCK INTERACTION PER QUOTA
    # -------------------------------------------------------------
    print("\n" + "="*95)
    print("PHASE 9: ANIMAL FEED & LIVESTOCK INTERACTION PER QUOTA")
    print("="*95)
    print(f"{'Quota':<6} | {'Wheat Rev Gain':<15} | {'Feed Cost Saved':<16} | {'Wool Delta':<12} | {'Milk Delta':<12}")
    print("-" * 95)
    
    m1_w_rev_arr = np.array([m1_by_seed[s]["wheat_rev"] for s in seeds])
    m1_feed_exp_arr = np.array([m1_by_seed[s]["exp_feed"] for s in seeds])
    m1_wool_arr = np.array([m1_by_seed[s]["wool_sold"] for s in seeds])
    m1_milk_arr = np.array([m1_by_seed[s]["milk_sold"] for s in seeds])

    for q in quotas:
        q_w_rev = np.mean([sweep_by_quota[q][s]["wheat_rev"] for s in seeds]) - np.mean(m1_w_rev_arr)
        q_feed_saved = np.mean(m1_feed_exp_arr) - np.mean([sweep_by_quota[q][s]["exp_feed"] for s in seeds])
        q_wool_d = np.mean([sweep_by_quota[q][s]["wool_sold"] for s in seeds]) - np.mean(m1_wool_arr)
        q_milk_d = np.mean([sweep_by_quota[q][s]["milk_sold"] for s in seeds]) - np.mean(m1_milk_arr)
        print(f"Q-{q:<4} | ${q_w_rev:+14.2f} | ${q_feed_saved:+15.2f} | {q_wool_d:+11.2f}u | {q_milk_d:+11.2f}u")

    # -------------------------------------------------------------
    # 5. PHASE 10: LABOR OPPORTUNITY COST PER QUOTA
    # -------------------------------------------------------------
    print("\n" + "="*95)
    print("PHASE 10: LABOR ACTIONS BREAKDOWN PER QUOTA")
    print("="*95)
    print(f"{'Quota':<6} | {'Move':<7} | {'Pass':<7} | {'Straw Harv':<11} | {'Animal Care':<12} | {'Animal Feed':<12}")
    print("-" * 95)
    m1_sh_acts = np.mean([m1_by_seed[s]["straw_harvest_actions"] for s in seeds])
    m1_ac_acts = np.mean([m1_by_seed[s]["animal_care_actions"] for s in seeds])
    m1_af_acts = np.mean([m1_by_seed[s]["animal_feed_actions"] for s in seeds])
    print(f"M1Base | {m1_moves:7.0f} | {np.mean([m1_by_seed[s]['actions_count']['PASS'] for s in seeds]):7.0f} | {m1_sh_acts:11.1f} | {m1_ac_acts:12.1f} | {m1_af_acts:12.1f}")
    
    for q in quotas:
        mv = np.mean([sweep_by_quota[q][s]["moves"] for s in seeds])
        ps = np.mean([sweep_by_quota[q][s]["passes"] for s in seeds])
        sha = np.mean([sweep_by_quota[q][s]["straw_harvest_actions"] for s in seeds])
        aca = np.mean([sweep_by_quota[q][s]["animal_care_actions"] for s in seeds])
        afa = np.mean([sweep_by_quota[q][s]["animal_feed_actions"] for s in seeds])
        print(f"Q-{q:<4} | {mv:7.0f} | {ps:7.0f} | {sha:11.1f} | {aca:12.1f} | {afa:12.1f}")

if __name__ == "__main__":
    analyze_sweep()
