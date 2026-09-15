"""
Empirical and Mathematical Land Value Curves Generator
Calculates Expected Realizable Terminal Economic Value Per Tile (ETV) across time (Days 0 to 29)
for Strawberry, Melon, Wheat, and Pasture under varying labor, capital, and spatial configurations.
"""

import json
import numpy as np

# Environment constants
BOARD = 10
TPD = 24
DAYS = 30
BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

# Empirical realized prices from previous forensic runs
REALIZED_PRICES = {
    "WHEAT": 27.5,
    "STRAWBERRY": 183.5,
    "MELON": 128.0,
    "MILK": 123.4,
    "WOOL": 120.4,
    "FERTILIZER": 63.1
}

def strawberry_etv(plant_day, fertilized=True, price=183.5):
    """
    Strawberry: seed cost 100, first yield at day + 10, interval 2, max 4 yields.
    Yield per cycle: 2 if fertilized else 1.
    """
    seed_cost = 100.0
    first_yield_day = plant_day + 10
    if first_yield_day >= DAYS:
        return -seed_cost, 0
    
    # Calculate yield days: first_yield_day, +2, +4, +6
    yield_days = [first_yield_day + 2 * i for i in range(4)]
    realizable_cycles = sum(1 for yd in yield_days if yd < DAYS)
    
    yield_per_cycle = 2.0 if fertilized else 1.0
    gross_rev = realizable_cycles * yield_per_cycle * price
    net_val = gross_rev - seed_cost
    return net_val, realizable_cycles

def melon_etv(plant_day, fertilized=True, price=128.0):
    """
    Melon: seed cost 80, first yield at day + 10, max yield at day + 12 (max 6 melons).
    Non-ongoing: harvested once, tile is freed at harvest day!
    """
    seed_cost = 80.0
    harvest_day = plant_day + 11 # typically harvested around day + 11
    if harvest_day >= DAYS:
        return -seed_cost, 0
    
    # Melons watered on window days: 6 to 12
    # Yield is 5 to 6 melons
    yield_units = 5.5
    gross_rev = yield_units * price
    net_val = gross_rev - seed_cost
    return net_val, harvest_day

def wheat_etv(plant_day, feed_saving_price=30.0, market_price=27.5):
    """
    Wheat: seed cost 10, first yield at day + 2, max yield at day + 4.
    Matures in 2-4 days, yield 4.0 units.
    Non-ongoing: harvested, tile freed!
    """
    seed_cost = 10.0
    harvest_day = plant_day + 3
    if harvest_day >= DAYS:
        return -seed_cost, 0
    
    # Wheat value depends on whether it offsets feed purchase ($30) or is sold ($27.5)
    effective_price = 0.5 * feed_saving_price + 0.5 * market_price
    yield_units = 4.0
    gross_rev = yield_units * effective_price
    net_val = gross_rev - seed_cost
    return net_val, harvest_day

def pasture_etv(acquire_day, species="SHEEP", milk_price=123.4, wool_price=120.4, fert_price=63.1):
    """
    Pasture tile: holds Cow or Sheep.
    Cow: cost 400, first yield at day + 8, interval 2, max 6 held. Daily feed cost $28.
         Produces 2 milk/milking + 1 fertilizer/day.
    Sheep: cost 500, first yield at day + 6, interval 3, max 6 held. Daily feed cost $28.
           Produces 2.5 wool/shearing + 1 fertilizer/day.
    """
    feed_cost_per_day = 28.0
    fert_rev_per_day = 1.0 * fert_price
    net_daily_operating = fert_rev_per_day - feed_cost_per_day # +$35.1/day operating cash flow!
    
    days_active = DAYS - acquire_day
    if days_active <= 0:
        return 0.0
    
    if species == "COW":
        cost = 400.0
        first_yield = acquire_day + 8
        if first_yield >= DAYS:
            return fert_rev_per_day * days_active - feed_cost_per_day * days_active - cost
        milking_days = [first_yield + 2 * i for i in range(15) if first_yield + 2 * i < DAYS]
        milk_units = (6.0 if acquire_day == 0 else 2.0) + 2.0 * max(0, len(milking_days) - 1)
        gross_prod = milk_units * milk_price
        net_val = gross_prod + (net_daily_operating * days_active) - cost
        return net_val
    else:
        cost = 500.0
        first_yield = acquire_day + 6
        if first_yield >= DAYS:
            return fert_rev_per_day * days_active - feed_cost_per_day * days_active - cost
        shearing_days = [first_yield + 3 * i for i in range(15) if first_yield + 3 * i < DAYS]
        wool_units = len(shearing_days) * 2.5
        gross_prod = wool_units * wool_price
        net_val = gross_prod + (net_daily_operating * days_active) - cost
        return net_val

def generate_curves():
    curve_data = {
        "days": list(range(DAYS)),
        "strawberry_etv": [],
        "strawberry_cycles": [],
        "melon_etv": [],
        "wheat_etv": [],
        "cow_etv": [],
        "sheep_etv": []
    }
    
    for d in range(DAYS):
        s_val, s_cyc = strawberry_etv(d)
        m_val, m_hd = melon_etv(d)
        w_val, w_hd = wheat_etv(d)
        c_val = pasture_etv(d, "COW")
        sh_val = pasture_etv(d, "SHEEP")
        
        curve_data["strawberry_etv"].append(round(s_val, 1))
        curve_data["strawberry_cycles"].append(s_cyc)
        curve_data["melon_etv"].append(round(m_val, 1))
        curve_data["wheat_etv"].append(round(w_val, 1))
        curve_data["cow_etv"].append(round(c_val, 1))
        curve_data["sheep_etv"].append(round(sh_val, 1))
        
    return curve_data

if __name__ == "__main__":
    data = generate_curves()
    with open("scratch/land_value_curves.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Land Value Curves generated successfully:")
    print("Day | Straw ETV (cyc) | Melon ETV | Wheat ETV | Cow ETV | Sheep ETV")
    print("-" * 65)
    for d in [0, 4, 7, 8, 10, 12, 13, 14, 15, 16, 18, 20, 24, 26, 28]:
        print(f"{d:3d} | ${data['strawberry_etv'][d]:6.1f} ({data['strawberry_cycles'][d]}c)   | ${data['melon_etv'][d]:6.1f}   | ${data['wheat_etv'][d]:5.1f}   | ${data['cow_etv'][d]:6.1f} | ${data['sheep_etv'][d]:6.1f}")
