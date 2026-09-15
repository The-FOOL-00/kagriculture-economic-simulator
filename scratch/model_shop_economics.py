"""
scratch/model_shop_economics.py
Phase 4: Exact mathematical model of shop economics.
Derives for each shop:
- Demand per turn / per day
- Price support & total capacity
- Revenue per cycle vs opportunity cost
- Labor requirement and infrastructure cost
"""
import json
import math
import os
import sys

SHOPS = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": 10000, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": 10000, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": 10000, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": 10000, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "I0": 10000, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": 10000, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

def analyze_all_shops():
    print("=" * 80)
    print("PHASE 4: SHOP ECONOMIC PROFILE & DEMAND MODEL")
    print("=" * 80)
    
    # 1. Demand per shop if unlocked at step 72 (Day 3) vs step 144 (Day 6)
    # Total steps remaining from step 72: 720 - 72 = 648 steps. Consumes every 4 steps = 162 consumption events.
    # Total steps remaining from step 144: 720 - 144 = 576 steps. Consumes every 4 steps = 144 consumption events.
    
    print(f"{'Shop Name':18} | {'Products':28} | {'Mult':4} | {'Day3 Total Demand':18} | {'Day6 Total Demand':18}")
    print("-" * 90)
    
    shop_profiles = {}
    
    for shop, prods in SHOPS.items():
        mult = 2 if len(prods) == 1 else 1
        d3_units = 162 * mult
        d6_units = 144 * mult
        prods_str = ", ".join(prods)
        print(f"{shop:18} | {prods_str:28} | {mult:4d} | {d3_units:4d} units/prod     | {d6_units:4d} units/prod")
        
        # Calculate theoretical maximum absorption value at base price:
        base_rev_d3 = sum(MARKET_PARAMS[p]["base"] * d3_units for p in prods)
        base_rev_d6 = sum(MARKET_PARAMS[p]["base"] * d6_units for p in prods)
        
        shop_profiles[shop] = {
            "products": prods,
            "multiplier": mult,
            "day3_units_per_product": d3_units,
            "day6_units_per_product": d6_units,
            "day3_max_absorption_dollars": base_rev_d3,
            "day6_max_absorption_dollars": base_rev_d6,
        }
        
    print("\n--- THEORETICAL ABSORPTION CAPACITY (DOLLARS AT BASE PRICE) ---")
    print(f"{'Shop Name':18} | {'Day 3 Unlock ($)':18} | {'Day 6 Unlock ($)':18} | Key Demand Driver")
    print("-" * 75)
    for shop, prof in sorted(shop_profiles.items(), key=lambda x: -x[1]["day6_max_absorption_dollars"]):
        d3_val = prof["day3_max_absorption_dollars"]
        d6_val = prof["day6_max_absorption_dollars"]
        driver = "/".join(prof["products"])
        print(f"{shop:18} | ${d3_val:15,.2f} | ${d6_val:15,.2f} | {driver}")
        
    return shop_profiles

if __name__ == "__main__":
    analyze_all_shops()
