import json
import numpy as np
from collections import defaultdict
from scipy import stats

def analyze():
    with open("scratch/wheat_forensics_50seeds_results.json") as f:
        data = json.load(f)

    # Group by arm
    arms = defaultdict(dict)
    for row in data:
        arms[row["arm"]][row["seed"]] = row

    seeds = sorted(arms["M1"].keys())
    n = len(seeds)

    print(f"=== LOADED {n} SEEDS FOR M1, M1_Wheat, and V2 ===")

    # -------------------------------------------------------------
    # PHASE 3: MASS BALANCE
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 3: FULL WHEAT MASS BALANCE (MEAN PER SEED OVER 50 SEEDS)")
    print("="*80)

    metrics_mb = [
        ("Wheat Planted Plots", "wheat_planted_plots"),
        ("Wheat Planting Events", "wheat_planting_events"),
        ("Failed Planting Attempts", "failed_wheat_planting"),
        ("Wheat Harvest Events", "wheat_harvest_events"),
        ("Wheat Units Harvested", "wheat_units_harvested"),
        ("Wheat Units Purchased (Feed)", "wheat_units_purchased"),
        ("Total Inflow (Harvested + Purchased)", "total_inflow"),
        ("Wheat Units Eaten (Feed)", "wheat_units_eaten"),
        ("Wheat Units Sold", "wheat_units_sold"),
        ("Terminal Wheat in Shed", "terminal_shed_wheat"),
        ("Terminal Wheat in Pockets", "terminal_pocket_wheat"),
        ("Total Outflow (Eaten+Sold+Shed+Pockets)", "total_outflow"),
        ("Unexplained Residual (Inflow - Outflow)", "residual"),
        ("Unharvested Yield Remaining on Tiles", "unharvested_wheat_yield")
    ]

    header = f"{'Metric':<40} | {'M1 Baseline':<12} | {'M1 Wheat Exp':<12} | {'Delta (Exp-M1)':<14} | {'Frozen V2':<12}"
    print(header)
    print("-" * len(header))

    mb_summary = {}
    for label, key in metrics_mb:
        m1_vals = [arms["M1"][s][key] for s in seeds]
        exp_vals = [arms["M1_Wheat"][s][key] for s in seeds]
        v2_vals = [arms["V2"][s][key] for s in seeds]
        
        m1_m = np.mean(m1_vals)
        exp_m = np.mean(exp_vals)
        delta_m = exp_m - m1_m
        v2_m = np.mean(v2_vals)
        
        mb_summary[key] = {"M1": m1_m, "M1_Wheat": exp_m, "Delta": delta_m, "V2": v2_m}
        print(f"{label:<40} | {m1_m:12.2f} | {exp_m:12.2f} | {delta_m:+14.2f} | {v2_m:12.2f}")

    # Check individual seed residuals
    max_res_m1 = max(abs(arms["M1"][s]["residual"]) for s in seeds)
    max_res_exp = max(abs(arms["M1_Wheat"][s]["residual"]) for s in seeds)
    max_res_v2 = max(abs(arms["V2"][s]["residual"]) for s in seeds)
    print(f"\nMax Absolute Residual across all 50 seeds: M1={max_res_m1}, M1_Wheat={max_res_exp}, V2={max_res_v2}")

    # -------------------------------------------------------------
    # PHASE 4: NET WHEAT ECONOMIC CONTRIBUTION
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 4: NET WHEAT ECONOMIC CONTRIBUTION")
    print("="*80)

    delta_w_seed_spent = np.mean([arms["M1_Wheat"][s]["wheat_seed_spent"] - arms["M1"][s]["wheat_seed_spent"] for s in seeds])
    delta_w_plant_acts = np.mean([arms["M1_Wheat"][s]["wheat_planting_events"] - arms["M1"][s]["wheat_planting_events"] for s in seeds])
    delta_w_harv_acts = np.mean([arms["M1_Wheat"][s]["wheat_harvest_actions"] - arms["M1"][s]["wheat_harvest_actions"] for s in seeds])
    delta_w_rev = np.mean([arms["M1_Wheat"][s]["wheat_rev"] - arms["M1"][s]["wheat_rev"] for s in seeds])
    
    # Feed purchase avoided: feed bought * 30
    feed_spent_m1 = np.mean([arms["M1"][s]["exp_feed"] for s in seeds])
    feed_spent_exp = np.mean([arms["M1_Wheat"][s]["exp_feed"] for s in seeds])
    delta_feed_avoided = feed_spent_m1 - feed_spent_exp

    # Additional movement turns
    moves_m1 = np.mean([arms["M1"][s]["actions_count"]["MOVE"] for s in seeds])
    moves_exp = np.mean([arms["M1_Wheat"][s]["actions_count"]["MOVE"] for s in seeds])
    delta_moves = moves_exp - moves_m1

    # Total productive labor delta
    total_w_labor = delta_w_plant_acts + delta_w_harv_acts

    # Direct net cash = Delta wheat revenue + Delta feed savings - Delta seed expenditure
    direct_net_wheat_cash = delta_w_rev + delta_feed_avoided - delta_w_seed_spent

    print(f"Additional Wheat Seed Spending:       ${delta_w_seed_spent:+.2f}")
    print(f"Additional Wheat Planting Labor:      {delta_w_plant_acts:+.2f} actions")
    print(f"Additional Wheat Harvesting Labor:    {delta_w_harv_acts:+.2f} actions")
    print(f"Total Direct Wheat Labor:             {total_w_labor:+.2f} actions")
    print(f"Additional Worker Movement:           {delta_moves:+.2f} moves")
    print(f"Additional Wheat Sale Revenue:        ${delta_w_rev:+.2f}")
    print(f"Additional Feed Purchases Avoided:    ${delta_feed_avoided:+.2f}")
    print(f"DIRECT NET WHEAT CASH CONTRIBUTION:   ${direct_net_wheat_cash:+.2f}")

    # Total reward delta
    rew_m1 = np.array([arms["M1"][s]["terminal_reward"] for s in seeds])
    rew_exp = np.array([arms["M1_Wheat"][s]["terminal_reward"] for s in seeds])
    rew_v2 = np.array([arms["V2"][s]["terminal_reward"] for s in seeds])
    delta_rew = rew_exp - rew_m1
    print(f"\nTerminal Reward M1:                   ${np.mean(rew_m1):.2f} (Median: ${np.median(rew_m1):.2f})")
    print(f"Terminal Reward M1_Wheat:             ${np.mean(rew_exp):.2f} (Median: ${np.median(rew_exp):.2f})")
    print(f"Terminal Reward Delta (Mean):         ${np.mean(delta_rew):+.2f}")
    print(f"Terminal Reward Delta (Median):       ${np.median(delta_rew):+.2f}")
    print(f"Win Rate:                             {np.mean(delta_rew > 0)*100:.1f}%")
    t_stat, p_val = stats.ttest_rel(rew_exp, rew_m1)
    print(f"Paired t-test p-value:                {p_val:.4f}")

    # -------------------------------------------------------------
    # PHASE 5: PLANTING WAVE TABLE (M1 vs V2 vs M1_Wheat)
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 5: PLANTING WAVE DECONSTRUCTION (DAYS 0-29)")
    print("="*80)

    # Let's inspect daily planting distribution across arms
    days_all = range(30)
    print(f"{'Day Range / Wave':<20} | {'M1 Planted':<12} | {'WheatExp Planted':<16} | {'V2 Planted':<12} | {'V2 Harvest Yield':<16}")
    print("-" * 85)

    wave_bins = [
        ("Wave 1 (Day 0-2)", range(0, 3)),
        ("Wave 2 (Day 3-9)", range(3, 10)),
        ("Wave 3 (Day 10-18)", range(10, 19)),
        ("Wave 4 (Day 19-24)", range(19, 25)),
        ("Wave 5 (Day 25-29)", range(25, 30)),
    ]

    for w_name, d_range in wave_bins:
        m1_w = sum(np.mean([arms["M1"][s]["wheat_plantings_by_day"].get(str(d), arms["M1"][s]["wheat_plantings_by_day"].get(d, 0)) for s in seeds]) for d in d_range)
        exp_w = sum(np.mean([arms["M1_Wheat"][s]["wheat_plantings_by_day"].get(str(d), arms["M1_Wheat"][s]["wheat_plantings_by_day"].get(d, 0)) for s in seeds]) for d in d_range)
        v2_w = sum(np.mean([arms["V2"][s]["wheat_plantings_by_day"].get(str(d), arms["V2"][s]["wheat_plantings_by_day"].get(d, 0)) for s in seeds]) for d in d_range)
        v2_hy = sum(np.mean([arms["V2"][s]["wheat_harvest_yield_by_day"].get(str(d), arms["V2"][s]["wheat_harvest_yield_by_day"].get(d, 0)) for s in seeds]) for d in d_range)
        print(f"{w_name:<20} | {m1_w:12.2f} | {exp_w:16.2f} | {v2_w:12.2f} | {v2_hy:16.2f}")

    # -------------------------------------------------------------
    # PHASE 8: STRAWBERRY CANNIBALIZATION TEST
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 8: STRAWBERRY CANNIBALIZATION TEST (50 SEEDS)")
    print("="*80)

    straw_sold_m1 = np.array([arms["M1"][s]["straw_sold"] for s in seeds])
    straw_sold_exp = np.array([arms["M1_Wheat"][s]["straw_sold"] for s in seeds])
    d_straw_sold = straw_sold_exp - straw_sold_m1

    straw_harv_m1 = np.array([arms["M1"][s]["straw_harvested_units"] for s in seeds])
    straw_harv_exp = np.array([arms["M1_Wheat"][s]["straw_harvested_units"] for s in seeds])
    d_straw_harv = straw_harv_exp - straw_harv_m1

    straw_pl_m1 = np.array([arms["M1"][s]["straw_planted_events"] for s in seeds])
    straw_pl_exp = np.array([arms["M1_Wheat"][s]["straw_planted_events"] for s in seeds])
    d_straw_pl = straw_pl_exp - straw_pl_m1

    straw_fert_m1 = np.array([arms["M1"][s]["straw_fertilized_events"] for s in seeds])
    straw_fert_exp = np.array([arms["M1_Wheat"][s]["straw_fertilized_events"] for s in seeds])
    d_straw_fert = straw_fert_exp - straw_fert_m1

    print(f"Strawberry Sold:        M1 = {np.mean(straw_sold_m1):.2f}u, Exp = {np.mean(straw_sold_exp):.2f}u, Delta = {np.mean(d_straw_sold):+.2f}u (p = {stats.ttest_rel(straw_sold_exp, straw_sold_m1).pvalue:.4f})")
    print(f"Strawberry Harvested:   M1 = {np.mean(straw_harv_m1):.2f}u, Exp = {np.mean(straw_harv_exp):.2f}u, Delta = {np.mean(d_straw_harv):+.2f}u (p = {stats.ttest_rel(straw_harv_exp, straw_harv_m1).pvalue:.4f})")
    print(f"Strawberry Plantings:   M1 = {np.mean(straw_pl_m1):.2f}u, Exp = {np.mean(straw_pl_exp):.2f}u, Delta = {np.mean(d_straw_pl):+.2f}u (p = {stats.ttest_rel(straw_pl_exp, straw_pl_m1).pvalue:.4f})")
    print(f"Strawberry Fert Cycles: M1 = {np.mean(straw_fert_m1):.2f}u, Exp = {np.mean(straw_fert_exp):.2f}u, Delta = {np.mean(d_straw_fert):+.2f}u (p = {stats.ttest_rel(straw_fert_exp, straw_fert_m1).pvalue:.4f})")

    # -------------------------------------------------------------
    # PHASE 9: ANIMAL FEED INTERACTION
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 9: ANIMAL FEED & LIVESTOCK INTERACTION")
    print("="*80)

    wool_sold_m1 = np.array([arms["M1"][s]["wool_sold"] for s in seeds])
    wool_sold_exp = np.array([arms["M1_Wheat"][s]["wool_sold"] for s in seeds])
    d_wool = wool_sold_exp - wool_sold_m1

    milk_sold_m1 = np.array([arms["M1"][s]["milk_sold"] for s in seeds])
    milk_sold_exp = np.array([arms["M1_Wheat"][s]["milk_sold"] for s in seeds])
    d_milk = milk_sold_exp - milk_sold_m1

    fert_sold_m1 = np.array([arms["M1"][s]["fert_sold"] for s in seeds])
    fert_sold_exp = np.array([arms["M1_Wheat"][s]["fert_sold"] for s in seeds])
    d_fert = fert_sold_exp - fert_sold_m1

    melon_sold_m1 = np.array([arms["M1"][s]["melon_sold"] for s in seeds])
    melon_sold_exp = np.array([arms["M1_Wheat"][s]["melon_sold"] for s in seeds])
    d_melon = melon_sold_exp - melon_sold_m1

    print(f"Wheat Sold Gain:        {np.mean([arms['M1_Wheat'][s]['wheat_sold'] - arms['M1'][s]['wheat_sold'] for s in seeds]):+.2f}u (+${np.mean([arms['M1_Wheat'][s]['wheat_rev'] - arms['M1'][s]['wheat_rev'] for s in seeds]):+.2f})")
    print(f"Feed Expense Reduction: ${delta_feed_avoided:+.2f} ({np.mean([arms['M1'][s]['wheat_units_purchased'] - arms['M1_Wheat'][s]['wheat_units_purchased'] for s in seeds]):+.2f}u feed avoided)")
    print(f"Wool Output Delta:      {np.mean(d_wool):+.2f}u (p = {stats.ttest_rel(wool_sold_exp, wool_sold_m1).pvalue:.4f})")
    print(f"Milk Output Delta:      {np.mean(d_milk):+.2f}u (p = {stats.ttest_rel(milk_sold_exp, milk_sold_m1).pvalue:.4f})")
    print(f"Fertilizer Sold Delta:  {np.mean(d_fert):+.2f}u (p = {stats.ttest_rel(fert_sold_exp, fert_sold_m1).pvalue:.4f})")
    print(f"Melon Sold Delta:       {np.mean(d_melon):+.2f}u (p = {stats.ttest_rel(melon_sold_exp, melon_sold_m1).pvalue:.4f})")

    # -------------------------------------------------------------
    # PHASE 10: LABOR OPPORTUNITY COST
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 10: LABOR OPPORTUNITY COST (ACTIONS PER EPISODE)")
    print("="*80)

    action_keys = [
        "PLANT", "HARVEST", "WATER", "FERTILIZE", "FEED", "CARE",
        "COLLECT_FERTILIZER", "DROP", "MOVE", "PASS"
    ]
    print(f"{'Action':<20} | {'M1 Mean':<10} | {'Exp Mean':<10} | {'Delta':<10} | {'V2 Mean':<10}")
    print("-" * 65)
    for ak in action_keys:
        m1_a = np.mean([arms["M1"][s]["actions_count"].get(ak, 0) for s in seeds])
        exp_a = np.mean([arms["M1_Wheat"][s]["actions_count"].get(ak, 0) for s in seeds])
        v2_a = np.mean([arms["V2"][s]["actions_count"].get(ak, 0) for s in seeds])
        print(f"{ak:<20} | {m1_a:10.1f} | {exp_a:10.1f} | {exp_a - m1_a:+10.1f} | {v2_a:10.1f}")

    print("\nGranular Target Actions:")
    for gak, name in [
        ("straw_harvest_actions", "Strawberry Harvest Actions"),
        ("wheat_harvest_actions", "Wheat Harvest Actions"),
        ("animal_care_actions", "Animal Care Actions"),
        ("animal_feed_actions", "Animal Feed Actions")
    ]:
        m1_ga = np.mean([arms["M1"][s][gak] for s in seeds])
        exp_ga = np.mean([arms["M1_Wheat"][s][gak] for s in seeds])
        v2_ga = np.mean([arms["V2"][s][gak] for s in seeds])
        print(f"{name:<28} | {m1_ga:10.1f} | {exp_ga:10.1f} | {exp_ga - m1_ga:+10.1f} | {v2_ga:10.1f}")

    # -------------------------------------------------------------
    # PHASE 11: LAND / SUCCESSION INTERACTION
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 11: LAND & SUCCESSION PREDECESSOR FORENSICS")
    print("="*80)

    preds_all = set()
    for s in seeds:
        preds_all.update(arms["M1"][s]["predecessors_of_wheat"].keys())
        preds_all.update(arms["M1_Wheat"][s]["predecessors_of_wheat"].keys())

    print(f"{'Predecessor Tile Type':<30} | {'M1 Plots':<10} | {'Exp Plots':<10} | {'Delta Plots':<12}")
    print("-" * 68)
    for p_type in sorted(preds_all):
        m1_p = np.mean([arms["M1"][s]["predecessors_of_wheat"].get(p_type, 0) for s in seeds])
        exp_p = np.mean([arms["M1_Wheat"][s]["predecessors_of_wheat"].get(p_type, 0) for s in seeds])
        print(f"{p_type:<30} | {m1_p:10.2f} | {exp_p:10.2f} | {exp_p - m1_p:+12.2f}")

    # -------------------------------------------------------------
    # PHASE 12: SEED-BY-SEED DIVERGENCE (10 BIGGEST WINS & LOSSES)
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 12: SEED-BY-SEED DIVERGENCE (10 BIGGEST WINS & 10 BIGGEST LOSSES)")
    print("="*80)

    deltas_by_seed = []
    for s in seeds:
        m1_r = arms["M1"][s]
        exp_r = arms["M1_Wheat"][s]
        deltas_by_seed.append({
            "seed": s,
            "d_rew": exp_r["terminal_reward"] - m1_r["terminal_reward"],
            "d_w_sold": exp_r["wheat_sold"] - m1_r["wheat_sold"],
            "d_straw": exp_r["straw_sold"] - m1_r["straw_sold"],
            "d_wool": exp_r["wool_sold"] - m1_r["wool_sold"],
            "d_milk": exp_r["milk_sold"] - m1_r["milk_sold"],
            "d_melon": exp_r["melon_sold"] - m1_r["melon_sold"],
            "d_fert": exp_r["fert_sold"] - m1_r["fert_sold"],
            "d_moves": exp_r["actions_count"]["MOVE"] - m1_r["actions_count"]["MOVE"],
            "d_seed_exp": exp_r["exp_seeds"] - m1_r["exp_seeds"],
            "d_feed_exp": exp_r["exp_feed"] - m1_r["exp_feed"],
            "d_w_plots": exp_r["wheat_planted_plots"] - m1_r["wheat_planted_plots"]
        })

    deltas_by_seed.sort(key=lambda x: x["d_rew"], reverse=True)

    print("\nTOP 10 BIGGEST WINS FOR WHEAT EXPANSION:")
    hdr = f"{'Seed':<6} | {'Delta Rew':<11} | {'D_Wheat':<8} | {'D_Straw':<8} | {'D_Wool':<8} | {'D_Milk':<8} | {'D_Melon':<8} | {'D_Fert':<8} | {'D_Moves':<8} | {'D_Plots':<8}"
    print(hdr)
    print("-" * len(hdr))
    for r in deltas_by_seed[:10]:
        print(f"{r['seed']:<6} | {r['d_rew']:+11.2f} | {r['d_w_sold']:+8.1f} | {r['d_straw']:+8.1f} | {r['d_wool']:+8.1f} | {r['d_milk']:+8.1f} | {r['d_melon']:+8.1f} | {r['d_fert']:+8.1f} | {r['d_moves']:+8.0f} | {r['d_w_plots']:+8.1f}")

    print("\nTOP 10 BIGGEST LOSSES FOR WHEAT EXPANSION:")
    print(hdr)
    print("-" * len(hdr))
    for r in deltas_by_seed[-10:]:
        print(f"{r['seed']:<6} | {r['d_rew']:+11.2f} | {r['d_w_sold']:+8.1f} | {r['d_straw']:+8.1f} | {r['d_wool']:+8.1f} | {r['d_milk']:+8.1f} | {r['d_melon']:+8.1f} | {r['d_fert']:+8.1f} | {r['d_moves']:+8.0f} | {r['d_w_plots']:+8.1f}")

if __name__ == "__main__":
    analyze()
