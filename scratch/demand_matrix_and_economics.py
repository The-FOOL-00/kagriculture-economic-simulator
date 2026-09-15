"""
PHASE 1 & 2: DEMAND MATRIX & COMMODITY PRODUCTION ECONOMICS
Calculates the exact theoretical and empirical demand matrix across all 8 shops
and computes the Net Economic Value (NEV) for all 6 production commodities.
"""
import sys
import os

SHOP_DEFS = {
    'PET_CAFE': {'CARROT': 2},
    'YARN_STORE': {'WOOL': 2},
    'PIZZA_SHOP': {'MILK': 1, 'TOMATO': 1, 'WHEAT': 1},
    'ICE_CREAM_SHOP': {'STRAWBERRY': 1, 'MILK': 1, 'WHEAT': 1},
    'SMOOTHIE_SHOP': {'STRAWBERRY': 1, 'MILK': 1},
    'BAKERY': {'EGG': 1, 'WHEAT': 1},
    'BRUNCH_SPOT': {'EGG': 1, 'WHEAT': 1, 'STRAWBERRY': 1},
    'FARMERS_MARKET': {'WHEAT': 1, 'CARROT': 1, 'TOMATO': 1, 'STRAWBERRY': 1},
}

PRODUCTS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']

def compute_demand_matrix():
    print("="*90)
    print("PHASE 2: SHOP DEMAND MATRIX (720-STEP TOTAL CONSUMPTION PER SHOP UNLOCKED AT DAY 3 / DAY 6)")
    print("="*90)
    
    # Drain opportunities:
    # Day 3 (Step 72..719): 162 pulls
    # Day 6 (Step 144..719): 144 pulls
    # Average across Day 3 and Day 6 unlocks = 153 pulls
    pulls_d3 = (720 - 72) // 4
    pulls_d6 = (720 - 144) // 4
    
    print(f"{'Shop Archetype':<16} | {'WHEAT':<6} | {'CARROT':<6} | {'TOMATO':<6} | {'STRAWB':<6} | {'MELON':<6} | {'EGG':<6} | {'MILK':<6} | {'WOOL':<6}")
    print("-" * 90)
    
    for shop, items in SHOP_DEFS.items():
        row_d3 = {p: 0 for p in PRODUCTS}
        row_d6 = {p: 0 for p in PRODUCTS}
        for it, mult in items.items():
            row_d3[it] = pulls_d3 * mult
            row_d6[it] = pulls_d6 * mult
        
        # Display average consumption for single instance
        avg_row = {p: (row_d3[p] + row_d6[p]) // 2 for p in PRODUCTS}
        print(f"{shop:<16} | {avg_row['WHEAT']:<6} | {avg_row['CARROT']:<6} | {avg_row['TOMATO']:<6} | {avg_row['STRAWBERRY']:<6} | {avg_row['MELON']:<6} | {avg_row['EGG']:<6} | {avg_row['MILK']:<6} | {avg_row['WOOL']:<6}")

def compute_production_economics():
    print("\n" + "="*90)
    print("PHASE 1: COMMODITY PRODUCTION ECONOMICS & NET ECONOMIC VALUE (NEV)")
    print("="*90)
    
    # Parameters per commodity:
    # (Seed/Buy Cost, Maturation Days, Harvest Interval, Max Harvests, Units per harvest (fert), Feed/day, Base Price, Peak Demand Price, No-Demand Crash Price)
    economics = [
        # Name, Cost, MatDays, Interval, MaxH, Units/H, Feed/Day, P_base, P_peak, P_crash
        ("WHEAT", 10, 3, 0, 1, 6, 0, 25, 43, 20),
        ("CARROT", 20, 3, 0, 1, 4, 0, 35, 136, 12),
        ("TOMATO", 50, 8, 1, 4, 2, 0, 60, 189, 9),
        ("STRAWBERRY", 100, 10, 2, 4, 2, 0, 120, 274, 1),
        ("MELON", 80, 11, 0, 1, 6, 0, 250, 280, 1),
        ("EGG (Goose)", 300, 4, 1, 20, 1, 25, 50, 70, 40),
        ("MILK (Cow)", 400, 8, 2, 10, 1.5, 25, 160, 319, 1),
        ("WOOL (Sheep)", 500, 6, 3, 7, 1.5, 25, 200, 255, 1),
    ]
    
    print(f"{'Commodity':<14} | {'Input Cost':<10} | {'Cycle/Days':<10} | {'Yield (Units)':<13} | {'Rev (Base)':<11} | {'Rev (Peak)':<11} | {'Rev (Crash)':<11} | {'NEV (Peak)':<11} | {'NEV (Crash)':<11}")
    print("-" * 110)
    
    for name, cost, mat, interval, max_h, units_h, feed, p_base, p_peak, p_crash in economics:
        total_yield = max_h * units_h
        feed_total = feed * (mat + max_h * max(1, interval))
        total_cost = cost + feed_total
        
        rev_base = total_yield * p_base
        rev_peak = total_yield * p_peak
        rev_crash = total_yield * p_crash
        
        nev_peak = rev_peak - total_cost
        nev_crash = rev_crash - total_cost
        
        print(f"{name:<14} | ${total_cost:<9.0f} | {mat:<10} | {total_yield:<13.1f} | ${rev_base:<10.0f} | ${rev_peak:<10.0f} | ${rev_crash:<10.0f} | ${nev_peak:<10.0f} | ${nev_crash:<10.0f}")

if __name__ == "__main__":
    compute_demand_matrix()
    compute_production_economics()
