"""
Analyze Reconstructed Telemetry of V54 and V66
Extracts exact comparative averages and behavioral differences.
"""
import json, statistics
from collections import defaultdict

data = json.load(open("scratch/v54_v66_telemetry.json"))

def mean(lst):
    return statistics.mean(lst) if lst else 0.0

for agent in ["V54", "V66"]:
    records = data[agent]
    n = len(records)
    print(f"\n{'='*70}\nEXACT RECONSTRUCTION SUMMARY: {agent} (N={n} Seeds)\n{'='*70}")
    print(f"Mean Solo Reward: {mean([r['reward'] for r in records]):,.0f}")
    
    # 1. Labor
    hires_per_day = defaultdict(list)
    total_hires = []
    for r in records:
        tot = sum(r["hires_by_day"].values())
        total_hires.append(tot)
        for d, h in r["hires_by_day"].items():
            hires_per_day[int(d)].append(h)
            
    print("\n--- LABOR DEPLOYMENT ---")
    print(f"Total Worker-Days: {mean(total_hires):.1f}")
    sample_days = [0, 1, 2, 5, 6, 10, 11, 15, 20, 25, 29]
    for d in sample_days:
        print(f"  Day {d:2d} Workers: {mean(hires_per_day[d]):.1f}")
        
    # 2. Crops
    crops_b = defaultdict(list)
    crops_p = defaultdict(list)
    for r in records:
        for c in ["MELON", "WHEAT", "STRAWBERRY", "CARROT"]:
            crops_b[c].append(r["crops_bought"].get(c, 0))
            crops_p[c].append(r["crops_planted"].get(c, 0))
            
    print("\n--- CROP LIFECYCLE ---")
    for c in ["MELON", "WHEAT", "STRAWBERRY", "CARROT"]:
        print(f"  {c:12s}: Bought={mean(crops_b[c]):.1f}, Planted={mean(crops_p[c]):.1f}")
        
    # 3. Livestock
    cows_b = [r["animals_bought"].get("COW", 0) for r in records]
    sheep_b = [r["animals_bought"].get("SHEEP", 0) for r in records]
    cows_p = [r["animals_placed"].get("COW", 0) for r in records]
    sheep_p = [r["animals_placed"].get("SHEEP", 0) for r in records]
    feeds = [r["feeds"] for r in records]
    cares = [r["cares"] for r in records]
    fert = [r["fert_collected"] for r in records]
    print("\n--- LIVESTOCK LIFECYCLE ---")
    print(f"  Cows: Bought={mean(cows_b):.1f}, Placed={mean(cows_p):.1f}")
    print(f"  Sheep: Bought={mean(sheep_b):.1f}, Placed={mean(sheep_p):.1f}")
    print(f"  Feeds={mean(feeds):.1f}, Cares={mean(cares):.1f}, Fert Collected={mean(fert):.1f}")
    
    # 4. Sales and Quantities
    sales_qty = defaultdict(list)
    sales_rev = defaultdict(list)
    for r in records:
        for prod in ["MILK", "WOOL", "FERTILIZER", "WHEAT", "STRAWBERRY", "MELON", "CARROT"]:
            sales_qty[prod].append(r["sales_by_prod"].get(prod, 0))
            sales_rev[prod].append(r["sales_rev_by_prod"].get(prod, 0.0))
            
    print("\n--- SALES QUANTITIES & REVENUE ---")
    for prod in ["STRAWBERRY", "WHEAT", "MILK", "FERTILIZER", "WOOL", "MELON", "CARROT"]:
        print(f"  {prod:12s}: Qty={mean(sales_qty[prod]):.1f} | Rev=${mean(sales_rev[prod]):,.0f}")
        
    # 5. Cash Milestones
    print("\n--- CASH MILESTONES ---")
    for d in [0, 1, 3, 5, 10, 15, 20, 25, 29]:
        cash_d = [r["cash_milestones"].get(str(d), r["cash_milestones"].get(d, 0)) for r in records]
        print(f"  Day {d:2d} Cash: ${mean(cash_d):,.0f}")
        
    # 6. Land Unlocks
    land_steps = [r["land_unlocked"] for r in records]
    print(f"\n--- LAND UNLOCKS ---\n  {land_steps[0]}")
