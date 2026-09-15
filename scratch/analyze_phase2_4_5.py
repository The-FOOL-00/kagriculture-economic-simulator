import json
import numpy as np
import scipy.stats as stats
from collections import defaultdict

def run_analysis():
    with open("scratch/raw_telemetry_150seeds.json") as f:
        data = json.load(f)

    # Separate into Seeds 1000-1049 (Discovery 50 seeds) and 1050-1149 (Validation 100 seeds)
    seeds_50 = [d for d in data if 1000 <= d["seed"] < 1050]
    seeds_100 = [d for d in data if 1050 <= d["seed"] < 1150]

    print(f"Loaded {len(seeds_50)} discovery seeds and {len(seeds_100)} validation seeds.")

    # ==============================================================
    # PHASE 2: CAUSAL CHAIN DECOMPOSITION
    # ==============================================================
    print("\n" + "="*80)
    print("PHASE 2: ECONOMIC CAUSAL CHAIN FROM RAW TELEMETRY")
    print("="*80)

    for group_name, group_data in [("Discovery Seeds 1000-1049 (N=50)", seeds_50), ("Validation Seeds 1050-1149 (N=100)", seeds_100)]:
        print(f"\n--- {group_name} ---")
        
        m1_rew = [d["m1"]["reward"] for d in group_data]
        q50_rew = [d["q50"]["reward"] for d in group_data]
        mecha_rew = [d["mech_a"]["reward"] for d in group_data]

        delta_q50 = np.array([q - m for q, m in zip(q50_rew, m1_rew)])
        delta_mecha = np.array([a - m for a, m in zip(mecha_rew, m1_rew)])

        wool_m1 = np.array([d["m1"]["total_wool_sold"] for d in group_data])
        wool_q50 = np.array([d["q50"]["total_wool_sold"] for d in group_data])
        wool_mecha = np.array([d["mech_a"]["total_wool_sold"] for d in group_data])

        wheat_m1 = np.array([d["m1"]["total_wheat_sold"] for d in group_data])
        wheat_q50 = np.array([d["q50"]["total_wheat_sold"] for d in group_data])
        wheat_mecha = np.array([d["mech_a"]["total_wheat_sold"] for d in group_data])

        straw_m1 = np.array([d["m1"]["total_straw_sold"] for d in group_data])
        straw_q50 = np.array([d["q50"]["total_straw_sold"] for d in group_data])
        straw_mecha = np.array([d["mech_a"]["total_straw_sold"] for d in group_data])

        milk_m1 = np.array([d["m1"]["total_milk_sold"] for d in group_data])
        milk_q50 = np.array([d["q50"]["total_milk_sold"] for d in group_data])
        milk_mecha = np.array([d["mech_a"]["total_milk_sold"] for d in group_data])

        # Pasture collision counts (cows placed on sheep slots)
        q50_collisions = [len(d["q50"]["cows_on_sheep_slots"]) for d in group_data]
        mecha_collisions = [len(d["mech_a"]["cows_on_sheep_slots"]) for d in group_data]
        m1_collisions = [len(d["m1"]["cows_on_sheep_slots"]) for d in group_data]

        print(f"M1 Mean Reward:       ${np.mean(m1_rew):10,.1f}")
        print(f"Q50 Mean Reward:      ${np.mean(q50_rew):10,.1f} (Delta: ${np.mean(delta_q50):+10,.1f}, Win: {np.mean(delta_q50 > 0)*100:5.1f}%)")
        print(f"MechA Mean Reward:    ${np.mean(mecha_rew):10,.1f} (Delta: ${np.mean(delta_mecha):+10,.1f}, Win: {np.mean(delta_mecha > 0)*100:5.1f}%)")
        print(f"Wool Sold (M1/Q50/A): {np.mean(wool_m1):5.1f} / {np.mean(wool_q50):5.1f} (d={np.mean(wool_q50-wool_m1):+4.1f}) / {np.mean(wool_mecha):5.1f} (d={np.mean(wool_mecha-wool_m1):+4.1f})")
        print(f"Wheat Sold (M1/Q50/A):{np.mean(wheat_m1):5.1f} / {np.mean(wheat_q50):5.1f} (d={np.mean(wheat_q50-wheat_m1):+4.1f}) / {np.mean(wheat_mecha):5.1f} (d={np.mean(wheat_mecha-wheat_m1):+4.1f})")
        print(f"Straw Sold (M1/Q50/A):{np.mean(straw_m1):5.1f} / {np.mean(straw_q50):5.1f} (d={np.mean(straw_q50-straw_m1):+4.1f}) / {np.mean(straw_mecha):5.1f} (d={np.mean(straw_mecha-straw_m1):+4.1f})")
        print(f"Milk Sold (M1/Q50/A): {np.mean(milk_m1):5.1f} / {np.mean(milk_q50):5.1f} (d={np.mean(milk_q50-milk_m1):+4.1f}) / {np.mean(milk_mecha):5.1f} (d={np.mean(milk_mecha-milk_m1):+4.1f})")
        print(f"Cows on Sheep Slots:  M1={np.mean(m1_collisions):.2f} | Q50={np.mean(q50_collisions):.2f} | MechA={np.mean(mecha_collisions):.2f}")

    # Causal breakdown: Where MechA helps vs hurts
    print("\n=== WHERE MECHANISM A HELPS VS HURTS (TOP 5 SEEDS) ===")
    deltas_a = [(d["seed"], d["mech_a"]["reward"] - d["m1"]["reward"], d["q50"]["reward"] - d["m1"]["reward"], 
                 d["mech_a"]["total_wool_sold"] - d["m1"]["total_wool_sold"], 
                 d["mech_a"]["total_wheat_sold"] - d["m1"]["total_wheat_sold"],
                 d["mech_a"]["total_straw_sold"] - d["m1"]["total_straw_sold"],
                 len(d["q50"]["cows_on_sheep_slots"]), len(d["mech_a"]["cows_on_sheep_slots"])) 
                for d in data]
    
    deltas_a.sort(key=lambda x: x[1], reverse=True)
    print("Top 5 Biggest Wins for MechA vs M1:")
    print(f"{'Seed':<6} | {'Delta A':<10} {'Delta Q50':<10} | {'Wool Diff':<10} {'Wheat Diff':<10} {'Straw Diff':<10} | {'Collisions Q50 -> A'}")
    for row in deltas_a[:5]:
        print(f"{row[0]:<6} | ${row[1]:<+9,.0f} ${row[2]:<+9,.0f} | {row[3]:<+10d} {row[4]:<+10d} {row[5]:<+10d} | {row[6]} -> {row[7]}")

    print("\nTop 5 Biggest Losses for MechA vs M1:")
    for row in deltas_a[-5:]:
        print(f"{row[0]:<6} | ${row[1]:<+9,.0f} ${row[2]:<+9,.0f} | {row[3]:<+10d} {row[4]:<+10d} {row[5]:<+10d} | {row[6]} -> {row[7]}")

    # ==============================================================
    # PHASE 4: MINIMAL STATE VARIABLE & CORRELATION ANALYSIS
    # ==============================================================
    print("\n" + "="*80)
    print("PHASE 4: MINIMAL STATE VARIABLE SEARCH (ON 100 VALIDATION SEEDS)")
    print("="*80)

    # Metrics on 100 validation seeds for Q50:
    wool_loss_q50 = np.array([d["m1"]["total_wool_sold"] - d["q50"]["total_wool_sold"] for d in seeds_100])
    
    # Candidate predictors:
    var_cows_d6 = np.array([d["q50"]["daily_cows_on_field"]["6"] for d in seeds_100])
    var_cows_d8 = np.array([d["q50"]["daily_cows_on_field"]["8"] for d in seeds_100])
    var_collisions = np.array([len(d["q50"]["cows_on_sheep_slots"]) for d in seeds_100])
    var_cash_d6 = np.array([d["q50"]["hourly_cash"]["D6H0"] for d in seeds_100])
    var_sheep_d9 = np.array([d["q50"]["daily_sheep_on_field"]["9"] for d in seeds_100])
    var_sheep_deploy_gap = np.array([d["m1"]["daily_sheep_on_field"]["9"] - d["q50"]["daily_sheep_on_field"]["9"] for d in seeds_100])

    candidates_var = [
        ("Cows present on field on Day 6", var_cows_d6),
        ("Cows present on field on Day 8", var_cows_d8),
        ("Cows placed on Sheep-designated slots", var_collisions),
        ("Day 6 Hour 0 Cash Balance", var_cash_d6),
        ("Sheep deployed on field on Day 9", -var_sheep_d9), # higher deployment = lower loss
        ("Day 9 Sheep Deployment Gap (M1 - Q50)", var_sheep_deploy_gap)
    ]

    print(f"{'Candidate State Variable':<45} | {'Pearson r':<12} {'p-value':<12} | {'Spearman rho':<12} {'p-value'}")
    print("-" * 95)
    for name, v in candidates_var:
        pr, pp = stats.pearsonr(v, wool_loss_q50)
        sr, sp = stats.spearmanr(v, wool_loss_q50)
        print(f"{name:<45} | {pr:10.3f}   {pp:10.4e} | {sr:10.3f}     {sp:10.4e}")

    # ==============================================================
    # PHASE 5: EXPECTED SHEEP ASSUMPTION & SHADOW VALUE
    # ==============================================================
    print("\n" + "="*80)
    print("PHASE 5: EXPECTED SHEEP SCHEDULE & ECONOMIC SHADOW VALUE")
    print("="*80)

    # Check empirical sheep purchase probability by day
    for day in range(6, 13):
        n_buys_m1 = sum(1 for d in seeds_100 for o in d["m1"]["buy_animal_orders"] if o["day"] == day and o["animal"] == "SHEEP")
        n_buys_q50 = sum(1 for d in seeds_100 for o in d["q50"]["buy_animal_orders"] if o["day"] == day and o["animal"] == "SHEEP")
        total_bought_m1 = sum(o["qty"] for d in seeds_100 for o in d["m1"]["buy_animal_orders"] if o["day"] == day and o["animal"] == "SHEEP")
        total_bought_q50 = sum(o["qty"] for d in seeds_100 for o in d["q50"]["buy_animal_orders"] if o["day"] == day and o["animal"] == "SHEEP")
        print(f"Day {day:2d}: M1 Sheep Buys={n_buys_m1:2d} ({total_bought_m1:3d} sheep) | Q50 Sheep Buys={n_buys_q50:2d} ({total_bought_q50:3d} sheep)")

if __name__ == "__main__":
    run_analysis()
