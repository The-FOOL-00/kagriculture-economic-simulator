"""
Empirical Value-of-Time & Opportunity-Cost-of-Delay Telemetry
Computes the analytical and empirical Marginal Terminal Value (MTV) curves
and Opportunity Cost of Delay (Delta MTV / Delta Day) across all major production pipelines.
"""
import sys
import os
import json
import numpy as np

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

# In equilibrium / top-agent play, realized market prices typically average:
REALIZED_PRICES = {
    "STRAWBERRY": 183.5,
    "MELON": 128.0,
    "WOOL": 180.0,
    "MILK": 150.0,
    "FERTILIZER": 85.0,
    "WHEAT": 28.0
}

def compute_strawberry_mtv(plant_day, price=REALIZED_PRICES["STRAWBERRY"], fert=True):
    """
    Strawberry bushes require 10 days to first yield, then yield every 2 days up to 4 cycles.
    Base yield is 1 berry; fertilized yield is 2 berries.
    Seed cost: $100.
    Must finish yield before step 720 (day < 30).
    """
    seed_cost = 100.0
    first_yield_day = plant_day + 10
    if first_yield_day >= 30:
        return -seed_cost, 0
    
    # Days of potential yields: first_yield_day, first_yield_day+2, +4, +6
    yield_days = [first_yield_day + 2 * c for c in range(4) if first_yield_day + 2 * c < 30]
    n_cycles = len(yield_days)
    yield_per_cycle = 2.0 if fert else 1.0
    gross_rev = n_cycles * yield_per_cycle * price
    # Watering cost: 1 worker step per day until final harvest
    net_mtv = gross_rev - seed_cost
    return net_mtv, n_cycles

def compute_sheep_mtv(acq_day, p_wool=REALIZED_PRICES["WOOL"], p_fert=REALIZED_PRICES["FERTILIZER"], p_feed=REALIZED_PRICES["WHEAT"]):
    """
    Sheep cost $500. Takes 6 days to mature.
    Sheared every 3 days. When cared, yields 2.5 wool units per shear.
    Produces 1 fertilizer/day. Consumes 1 wheat/day.
    """
    cost = 500.0
    rem_days = max(0, 30 - acq_day)
    first_shear_day = acq_day + 6
    if first_shear_day >= 30:
        # No wool, only manure minus feed
        manure_profit = rem_days * (p_fert - p_feed)
        return manure_profit - cost, 0
    
    shear_days = [first_shear_day + 3 * c for c in range(10) if first_shear_day + 3 * c < 30]
    n_shears = len(shear_days)
    wool_rev = n_shears * 2.5 * p_wool
    manure_profit = rem_days * (p_fert - p_feed)
    net_mtv = wool_rev + manure_profit - cost
    return net_mtv, n_shears

def compute_cow_mtv(acq_day, p_milk=REALIZED_PRICES["MILK"], p_fert=REALIZED_PRICES["FERTILIZER"], p_feed=REALIZED_PRICES["WHEAT"]):
    """
    Cow costs $400. Takes 8 days to mature.
    Milked every 2 days. When cared, yields 2.0 milk units per milking.
    (Note: Day 0 cow yields 6 milk on day 8; subsequent yields are 2 milk).
    Produces 1 fertilizer/day. Consumes 1 wheat/day.
    """
    cost = 400.0
    rem_days = max(0, 30 - acq_day)
    first_milk_day = acq_day + 8
    if first_milk_day >= 30:
        manure_profit = rem_days * (p_fert - p_feed)
        return manure_profit - cost, 0
    
    milk_days = [first_milk_day + 2 * c for c in range(15) if first_milk_day + 2 * c < 30]
    n_milks = len(milk_days)
    # If bought day 0, first milk is 6 units, otherwise 2.0 units
    if acq_day == 0 and n_milks > 0:
        milk_rev = (6.0 + (n_milks - 1) * 2.0) * p_milk
    else:
        milk_rev = n_milks * 2.0 * p_milk
        
    manure_profit = rem_days * (p_fert - p_feed)
    net_mtv = milk_rev + manure_profit - cost
    return net_mtv, n_milks

def compute_melon_mtv(plant_day, price=REALIZED_PRICES["MELON"]):
    """
    Melon seed costs $80. Takes 10 days to first yield (day+10), reaches 5.5 units at day+11.
    Harvested once, freeing tile.
    """
    seed_cost = 80.0
    harvest_day = plant_day + 11
    if harvest_day >= 30:
        return -seed_cost, 0
    gross_rev = 5.5 * price
    return gross_rev - seed_cost, 1

def compute_wheat_mtv(plant_day, price=REALIZED_PRICES["WHEAT"]):
    """
    Wheat seed costs $10. Watered on day+1, day+2, day+3 to yield 4 units.
    Takes 3-4 days to reach full maturity (4 units).
    """
    seed_cost = 10.0
    harvest_day = plant_day + 3
    if harvest_day >= 30:
        return -seed_cost, 0
    gross_rev = 4.0 * price
    return gross_rev - seed_cost, 1

def compute_fertilizer_mtv(plant_day):
    """
    Marginal value of 1 unit of fertilizer applied to active strawberry bush vs sold.
    Market sale value: ~$85.
    Applied value: doubles berry yield (+1 berry/cycle) across remaining cycles of the bush.
    """
    # Active bush cycles remaining
    net_straw_val, n_cycles = compute_strawberry_mtv(plant_day, fert=True)
    unfert_straw_val, _ = compute_strawberry_mtv(plant_day, fert=False)
    delta_yield_rev = net_straw_val - unfert_straw_val
    return delta_yield_rev, REALIZED_PRICES["FERTILIZER"]

def compute_worker_mtv(hire_day):
    """
    Worker hiring fee: fib(n). For 11th hand, fee is ~$144-$233.
    Worker provides 24 steps/day.
    Each productive action generates on average ~$15-$25 of realized terminal wealth
    (watering strawberry creates $183.5/2 = ~$91/step; feeding animal preserves +$35/day).
    """
    rem_days = max(0, 30 - hire_day)
    rem_steps = rem_days * 24
    productive_steps = rem_steps * 0.45 # ~45% productive, rest movement/drop
    est_value_generated = productive_steps * 18.0
    return est_value_generated

def generate_value_curves():
    print("=" * 95)
    print("TEMPORAL ECONOMIC VALUE-OF-TIME CURVES & OPPORTUNITY COST OF DELAY")
    print("=" * 95)
    
    # 1. STRAWBERRY CURVE
    print("\n1. STRAWBERRY SEED INVESTMENT VALUE VS. PLANTING DAY:")
    print(f"{'Plant Day':<10} | {'Cycles':<8} | {'Net MTV ($)':<14} | {'Marginal ROI':<14} | {'1-Day Delay Loss ($)':<20}")
    print("-" * 75)
    prev_straw_mtv = None
    straw_data = {}
    for d in range(25):
        mtv, cycles = compute_strawberry_mtv(d)
        straw_data[d] = {"mtv": mtv, "cycles": cycles}
        delay_loss = (prev_straw_mtv - mtv) if prev_straw_mtv is not None else 0.0
        prev_straw_mtv = mtv
        roi = (mtv / 100.0) * 100.0
        if d in [0, 4, 7, 8, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
            print(f"Day {d:<6} | {cycles:<8} | ${mtv:12,.1f} | {roi:12.0f}% | -${delay_loss:18,.1f}")
            
    # 2. LIVESTOCK CURVES: SHEEP VS COW
    print("\n2. LIVESTOCK INVESTMENT VALUE VS. ACQUISITION DAY (SHEEP VS COW):")
    print(f"{'Acq Day':<8} | {'Sheep MTV':<12} | {'Sheep Shears':<14} | {'Cow MTV':<12} | {'Cow Milks':<12} | {'Optimal Pivot':<16} | {'Sheep Delay Loss':<18}")
    print("-" * 95)
    prev_sheep_mtv = None
    livestock_data = {}
    for d in range(25):
        s_mtv, s_cycles = compute_sheep_mtv(d)
        c_mtv, c_cycles = compute_cow_mtv(d)
        livestock_data[d] = {"sheep_mtv": s_mtv, "cow_mtv": c_mtv, "s_cycles": s_cycles, "c_cycles": c_cycles}
        s_loss = (prev_sheep_mtv - s_mtv) if prev_sheep_mtv is not None else 0.0
        prev_sheep_mtv = s_mtv
        pivot = "BUY COW" if c_mtv > s_mtv else "BUY SHEEP"
        if d in [0, 2, 4, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22]:
            print(f"Day {d:<4} | ${s_mtv:10,.1f} | {s_cycles:<14} | ${c_mtv:10,.1f} | {c_cycles:<12} | {pivot:<16} | -${s_loss:16,.1f}")

    # 3. WHEAT INVESTMENT VALUE VS. PLANTING DAY
    print("\n3. WHEAT INVESTMENT VALUE VS. PLANTING DAY (OPPORTUNITY COST ANALYSIS):")
    print(f"{'Plant Day':<10} | {'Wheat Net MTV':<15} | {'Melon/Straw Competing MTV':<25} | {'Opportunity Cost Verdict':<25}")
    print("-" * 85)
    wheat_data = {}
    for d in range(30):
        w_mtv, w_cycles = compute_wheat_mtv(d)
        wheat_data[d] = {"mtv": w_mtv, "cycles": w_cycles}
        if d <= 3:
            comp = "Essential feed bootstrap"
            verdict = "+$102.0 net (Essential)"
        elif 4 <= d <= 13:
            s_mtv, _ = compute_strawberry_mtv(d)
            comp = f"Straw MTV: ${s_mtv:,.0f}"
            verdict = f"-${s_mtv - w_mtv:,.0f} Opportunity Loss"
        elif 14 <= d <= 18:
            m_mtv, _ = compute_melon_mtv(d)
            comp = f"Melon MTV: ${m_mtv:,.0f}"
            verdict = f"-${m_mtv - w_mtv:,.0f} Opportunity Loss"
        elif 19 <= d <= 25:
            comp = "No new fruit can mature"
            verdict = "Negative labor congestion"
        elif 26 <= d <= 27:
            comp = "Vacated plot (no other crop can mature)"
            verdict = f"+${w_mtv:,.0f} Net Windfall (+1,020% ROI)"
        else:
            comp = "Immature crop"
            verdict = "-$10.0 Net Loss"
            
        if d in [0, 2, 4, 8, 12, 16, 20, 24, 26, 27, 28, 29]:
            print(f"Day {d:<6} | ${w_mtv:13,.1f} | {comp:<25} | {verdict:<25}")

    # Save data
    curves_out = {
        "strawberry": straw_data,
        "livestock": livestock_data,
        "wheat": wheat_data
    }
    with open("scratch/temporal_value_curves.json", "w") as f:
        json.dump(curves_out, f, indent=2)
    print("\nSaved analytical curves to scratch/temporal_value_curves.json")

if __name__ == "__main__":
    generate_value_curves()
