"""
Market Dynamics Analytical Model
Faithful implementation of C++ sim.hpp market pricing, shop drain, and multi-unit slippage.
"""
import math
from typing import Dict, List, Tuple

# Items
ITEMS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
ITEM_IDS = {name: i for i, name in enumerate(ITEMS)}

# Shape enum
F_LINEAR = 0
F_SQ = 1
F_SQRT = 2
F_LOG = 3
F_LOG10 = 4
F_HINGE = 5

MARKET_PARAMS = [
    # base, I0, T, below_f, below_t, above_f, above_t
    ( 25.0, 10000, 400.0, F_SQRT,  0.80, F_LOG,    0.20), # WHEAT
    ( 35.0, 10000, 450.0, F_HINGE, 1.00, F_SQRT,   0.70), # CARROT
    ( 60.0, 10000, 200.0, F_HINGE, 0.40, F_SQRT,   0.60), # TOMATO
    (120.0, 10000, 100.0, F_SQRT,  0.70, F_LINEAR, 1.60), # STRAWBERRY
    (250.0, 10000, 300.0, F_LOG,   0.20, F_SQ,     3.60), # MELON
    ( 50.0, 10000, 332.0, F_HINGE, 0.40, F_LOG,    0.20), # EGG
    (160.0, 10000, 122.0, F_SQRT,  0.60, F_LINEAR, 1.60), # MILK
    (200.0, 10000, 105.0, F_LOG,   0.20, F_SQ,     3.20), # WOOL
    (100.0, 10000, 200.0, F_LINEAR,0.40, F_LINEAR, 0.40), # FERTILIZER
]

def shape(f: int, x: float, T: float = 0.0) -> float:
    if x < 0.0:
        x = 0.0
    if f == F_LINEAR:
        return x
    elif f == F_SQ:
        return x * x
    elif f == F_SQRT:
        return math.sqrt(x)
    elif f == F_LOG:
        return math.log(1.0 + x)
    elif f == F_LOG10:
        return math.log10(1.0 + x)
    elif f == F_HINGE:
        if T <= 0.0:
            return x
        u = x / T
        e = u - 1.0
        if e < 0.0:
            e = 0.0
        return u + 8.0 * e * e
    return x

# Precompute amplitudes
MARKET_AMPS = []
for i, p in enumerate(MARKET_PARAMS):
    base, I0, T, below_f, below_t, above_f, above_t = p
    below_amp = below_t * base / shape(below_f, T, T)
    above_amp = above_t * base / shape(above_f, T, T)
    MARKET_AMPS.append((below_amp, above_amp))

def market_price(item_idx: int, inv: int) -> int:
    base, I0, T, below_f, below_t, above_f, above_t = MARKET_PARAMS[item_idx]
    below_amp, above_amp = MARKET_AMPS[item_idx]
    if inv < I0:
        price = base + below_amp * shape(below_f, float(I0 - inv), T)
    else:
        price = base - above_amp * shape(above_f, float(inv - I0), T)
    # Python round() implements round-half-to-even identical to std::nearbyint
    v = int(round(price))
    return max(1, v)

# Shop definitions
# 1u << item
SHOP_ITEMS = {
    'BAKERY': {'EGG': 1, 'WHEAT': 1},
    'BRUNCH_SPOT': {'EGG': 1, 'WHEAT': 1, 'STRAWBERRY': 1},
    'FARMERS_MARKET': {'WHEAT': 1, 'CARROT': 1, 'TOMATO': 1, 'STRAWBERRY': 1},
    'ICE_CREAM_SHOP': {'STRAWBERRY': 1, 'MILK': 1, 'WHEAT': 1},
    'PET_CAFE': {'CARROT': 2}, # 2x multiplier
    'PIZZA_SHOP': {'MILK': 1, 'TOMATO': 1, 'WHEAT': 1},
    'SMOOTHIE_SHOP': {'STRAWBERRY': 1, 'MILK': 1},
    'YARN_STORE': {'WOOL': 2}, # 2x multiplier
}

def simulate_sale(item_name: str, start_inv: int, quantity: int) -> Tuple[int, float, List[int]]:
    """
    Simulates selling quantity units sequentially matching process_market()
    Returns (total_revenue, avg_price, unit_prices)
    """
    item_idx = ITEM_IDS[item_name]
    inv = start_inv
    unit_prices = []
    total_rev = 0
    for _ in range(quantity):
        p = market_price(item_idx, inv)
        unit_prices.append(p)
        total_rev += p
        if p > 1:
            inv += 1
    avg_price = total_rev / quantity if quantity > 0 else 0.0
    return total_rev, avg_price, unit_prices

def run_price_impact_analysis():
    print("="*80)
    print("PHASE 2: MARKET DYNAMICS AND SLIPPAGE ANALYSIS")
    print("="*80)
    
    quantities = [1, 10, 25, 50, 100, 200, 400]
    
    for name in ITEMS:
        item_idx = ITEM_IDS[name]
        base_p = MARKET_PARAMS[item_idx][0]
        T = MARKET_PARAMS[item_idx][2]
        below_amp, above_amp = MARKET_AMPS[item_idx]
        
        # Determine crash point: inventory where price hits 1
        crash_surplus = None
        for s in range(1, 1000):
            if market_price(item_idx, 10000 + s) == 1:
                crash_surplus = s
                break
                
        # Determine 2x price deficit: inventory where price reaches 2 * base
        double_deficit = None
        for d in range(1, 1000):
            if market_price(item_idx, 10000 - d) >= 2 * base_p:
                double_deficit = d
                break
                
        print(f"\n--- {name} (Base Price: ${base_p:.0f}, Threshold T: {T:.0f}) ---")
        print(f"Crash to $1 at Surplus: +{crash_surplus} units" if crash_surplus else "Crash to $1: >1000 units")
        print(f"Double Price (2x) at Deficit: -{double_deficit} units" if double_deficit else "Double Price (2x): >1000 units")
        
        # Sells from base inventory (10,000)
        print("Sells from Initial Inventory (10,000):")
        print(f"{'Qty':<6} | {'Tot Rev':<10} | {'Avg Price':<10} | {'Final Price':<12} | {'Slip %':<8}")
        print("-" * 55)
        for q in quantities:
            rev, avg_p, prices = simulate_sale(name, 10000, q)
            final_p = prices[-1]
            slip = (1.0 - (avg_p / base_p)) * 100.0
            print(f"{q:<6} | ${rev:<9,.0f} | ${avg_p:<9.2f} | ${final_p:<11.1f} | {slip:>6.1f}%")

if __name__ == '__main__':
    run_price_impact_analysis()
