"""
scratch/shop_economic_oracle.py
Phase 6 & Phase 19: Theoretical Frontier & Shop Economic Oracle.
Calculates:
- Maximum feasible final cash under each shop world
- Audits the ~$143k upper bound
- Analyzes bottleneck constraints (land, labor, capital, market price depression)
"""
import collections
import json
import math
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

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

def shape(f, x, T):
    if x <= 0:
        return 0.0
    u = x / T
    if f == "linear":
        return u
    if f == "sq":
        return u * u
    if f == "sqrt":
        return math.sqrt(u)
    if f == "log":
        return math.log1p(u)
    if f == "hinge":
        return u if u <= 1.0 else 1.0 + 8.0 * (u - 1.0) ** 2
    return u

def price_at_sales(item, net_sales):
    """Calculates realized price when net_sales are sold into the market."""
    p = MARKET_PARAMS[item]
    base = p["base"]
    T = p["T"]
    I0 = p["I0"]
    # net_sales increases inventory from I0 to I0 + net_sales
    if net_sales <= 0:
        return base
    f = p["above_func"]
    amp = p["above_target"] * base / shape(f, T, T)
    price = base - amp * shape(f, net_sales, T)
    return max(1, int(round(price)))

def revenue_from_sales(item, total_units, shop_absorbed_units):
    """
    Units absorbed by town shop consume inventory at step intervals,
    preventing market glut. The net market sales = max(0, total_units - shop_absorbed_units).
    All sales made while inventory is absorbed get higher prices.
    """
    net_sales = max(0, total_units - shop_absorbed_units)
    # Average price for net_sales:
    # Integral of price from 0 to net_sales
    avg_price = (price_at_sales(item, 0) + price_at_sales(item, net_sales)) / 2.0
    # Shop absorbed units are sold at or above base price!
    rev_shop = shop_absorbed_units * MARKET_PARAMS[item]["base"]
    rev_market = net_sales * avg_price
    return rev_shop + rev_market

def compute_oracle():
    print("=" * 80)
    print("ECONOMIC ORACLE: THEORETICAL CEILINGS BY SHOP PAIR")
    print("=" * 80)
    
    # Baseline autarky without shops (pure market absorption ceiling)
    # Base production capacity:
    # - 8 Cows (4 pastures): produces ~88 milk, ~176 fertilizer. Feed: 176 wheat.
    # - 6 Sheep (3 pastures): produces ~48 wool, ~144 fertilizer. Feed: 144 wheat.
    # - 3 Geese (3 coops): produces ~78 eggs, ~78 fertilizer. Feed: 78 wheat.
    # - Total animal feed: 398 wheat.
    # - Crops: ~30-40 Strawberries, ~20 Melons, ~40-50 Wheat tiles.
    
    # Let's compute the incremental cash added by each shop pair over generic baseline
    # Generic baseline cash in Dmitrii is ~$96.5k.
    # How much extra price support does each shop pair provide?
    
    shop_pairs = []
    shop_names = list(SHOPS.keys())
    
    for s0 in shop_names:
        for s1 in shop_names:
            shop_pairs.append((s0, s1))
            
    pair_values = {}
    for s0, s1 in shop_pairs:
        # Day 3 shop (s0): 162 consumption cycles * multiplier
        m0 = 2 if len(SHOPS[s0]) == 1 else 1
        d3_units = 162 * m0
        # Day 6 shop (s1): 144 consumption cycles * multiplier
        m1 = 2 if len(SHOPS[s1]) == 1 else 1
        d6_units = 144 * m1
        
        # Total absorption dollars:
        val0 = sum(MARKET_PARAMS[p]["base"] * d3_units for p in SHOPS[s0])
        val1 = sum(MARKET_PARAMS[p]["base"] * d6_units for p in SHOPS[s1])
        total_absorption = val0 + val1
        
        # Product overlaps (synergy):
        prods0 = set(SHOPS[s0])
        prods1 = set(SHOPS[s1])
        overlap = prods0.intersection(prods1)
        
        pair_values[(s0, s1)] = {
            "val0": val0,
            "val1": val1,
            "total_absorption": total_absorption,
            "overlap": list(overlap),
            "prods": list(prods0.union(prods1))
        }
        
    print(f"{'Shop Pair':38} | {'Total Shop Absorption ($)':26} | {'Shared Synergy':20}")
    print("-" * 90)
    for pair, data in sorted(pair_values.items(), key=lambda x: -x[1]["total_absorption"])[:25]:
        pair_str = f"{pair[0]} + {pair[1]}"
        overlap_str = ", ".join(data["overlap"]) if data["overlap"] else "None (Independent)"
        print(f"{pair_str:38} | ${data['total_absorption']:23,.2f} | {overlap_str}")
        
    out_file = os.path.join(BASE_DIR, "results", "oracle_shop_pair_capacities.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump({f"{k[0]}|{k[1]}": v for k, v in pair_values.items()}, f, indent=2)
    print(f"\nSaved oracle pair capacities to {out_file}")

if __name__ == "__main__":
    compute_oracle()
