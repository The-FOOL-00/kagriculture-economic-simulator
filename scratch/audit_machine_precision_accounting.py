import json
import numpy as np

def run_accounting():
    with open("scratch/phase7_validation_200seeds_results.json") as f:
        data = json.load(f)

    print("=== PHASE 8: MACHINE-PRECISION ACCOUNTING BRIDGE ===")

    # In Kaggriculture:
    # Terminal reward = final cash on hand!
    # Because final cash on hand is:
    # Starting Cash ($1,500) 
    # + All Market Sales Revenue (Wheat + Wool + Milk + Straw + Melon + Carrot + Tomato + Egg + Fert)
    # - All Market Seed Purchases (Wheat + Straw + Melon + Carrot + Tomato)
    # - All Market Product Purchases (Wheat Feed)
    # - All Market Animal Purchases (Cow + Sheep + Goose)
    # - All Worker Hiring Costs
    # - All Land Expansion Costs
    
    # Let's verify this identity for M1 and MechA across all 200 seeds:
    deltas_rew = []
    deltas_wheat_rev = []
    deltas_wool_rev = []
    deltas_straw_rev = []
    deltas_milk_rev = []
    deltas_wheat_seed = []
    deltas_cow_exp = []
    deltas_sheep_exp = []

    for d in data:
        m1 = d["m1"]
        a = d["mech_a"]
        
        d_rew = a["reward"] - m1["reward"]
        deltas_rew.append(d_rew)

        # Commodity physical deltas
        d_wheat = a["sold"].get("WHEAT", 0) - m1["sold"].get("WHEAT", 0)
        d_wool = a["sold"].get("WOOL", 0) - m1["sold"].get("WOOL", 0)
        d_straw = a["sold"].get("STRAWBERRY", 0) - m1["sold"].get("STRAWBERRY", 0)
        d_milk = a["sold"].get("MILK", 0) - m1["sold"].get("MILK", 0)

        deltas_wheat_rev.append(d_wheat)
        deltas_wool_rev.append(d_wool)
        deltas_straw_rev.append(d_straw)
        deltas_milk_rev.append(d_milk)

        # Expenditure deltas
        d_w_seed = a["spent"].get("SEED_WHEAT", 0) - m1["spent"].get("SEED_WHEAT", 0)
        d_cow_exp = a["spent"].get("BUY_COW", 0) - m1["spent"].get("BUY_COW", 0)
        d_sheep_exp = a["spent"].get("BUY_SHEEP", 0) - m1["spent"].get("BUY_SHEEP", 0)

        deltas_wheat_seed.append(d_w_seed)
        deltas_cow_exp.append(d_cow_exp)
        deltas_sheep_exp.append(d_sheep_exp)

    mean_rew = np.mean(deltas_rew)
    mean_w = np.mean(deltas_wheat_rev)
    mean_wl = np.mean(deltas_wool_rev)
    mean_st = np.mean(deltas_straw_rev)
    mean_mk = np.mean(deltas_milk_rev)
    mean_ws = np.mean(deltas_wheat_seed)
    mean_ce = np.mean(deltas_cow_exp)
    mean_se = np.mean(deltas_sheep_exp)

    # Market base prices:
    # Wheat: $25 (elastic)
    # Wool: $200 (elastic)
    # Milk: $160 (elastic)
    # Strawberry: $120 (elastic)

    print(f"Mean Observed Reward Delta:           ${mean_rew:+10.2f}")
    print(f"Physical Commodity Contributions:")
    print(f"  Wheat Sold Delta:       {mean_w:+6.2f} units (Est Gross @ ~$25: ${mean_w * 25:+8.2f})")
    print(f"  Wool Sold Delta:        {mean_wl:+6.2f} units (Est Gross @ ~$200:${mean_wl * 200:+8.2f})")
    print(f"  Strawberry Sold Delta:  {mean_st:+6.2f} units (Est Gross @ ~$120:${mean_st * 120:+8.2f})")
    print(f"  Milk Sold Delta:        {mean_mk:+6.2f} units (Est Gross @ ~$160:${mean_mk * 160:+8.2f})")
    print(f"Expenditure Deltas:")
    print(f"  Wheat Seed Expenditure: ${mean_ws:+8.2f}")
    print(f"  Cow Purchase Spending:  ${mean_ce:+8.2f}")
    print(f"  Sheep Purchase Spending:${mean_se:+8.2f}")
    
    # Net Est Commodity Lift = Wheat + Milk - Wool - Straw - Seed:
    est_net = (mean_w * 25) + (mean_mk * 160) + (mean_wl * 200) + (mean_st * 120) - mean_ws
    print(f"Estimated Net Commodity Value:        ${est_net:+10.2f}")

if __name__ == "__main__":
    run_accounting()
