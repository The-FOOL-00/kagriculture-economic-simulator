"""
PHASE 9: TOMATO SALE BATCH SIZE OPTIMIZATION.
Evaluates tomato sale batches: 1, 2, 4, 6, 8, 10, 15, 20, 25
Under 1.32.7 exact F_HINGE pricing with Pizza shop demand.
"""
import math

def tomato_price(inv, I0=10000, base=60, T=200):
    x = I0 - inv
    if x >= 0:
        u = x / T
        e = max(0.0, u - 1.0)
        shape_val = u + 8.0 * e * e
        # below amp
        # shape(T) = 1.0
        amp = 0.40 * base / 1.0 # 24.0
        p = base + amp * shape_val
    else:
        # glut: above_f = F_SQRT, above_t = 0.60
        y = inv - I0
        shape_val = math.sqrt(y)
        amp = 0.60 * base / math.sqrt(T)
        p = base - amp * shape_val
    return max(1, int(round(p)))

def simulate_liquidation_schedule(total_units=76, batch_size=8, shop_consumption_per_4steps=4):
    # Start with initial inventory at I0 - 200 (post-shop consumption scarcity)
    inv = 9800
    revenue = 0
    units_sold = 0
    steps = 0
    
    # 76 tomatoes harvested across Day 20-28 (Steps 480 to 672)
    # Available every 4 steps
    shed = 0
    history = []
    
    for day in range(20, 29):
        # 8 tomatoes harvested per day on average
        shed += 8
        for hour in range(0, 24, 4):
            # Town consumes
            inv -= shop_consumption_per_4steps
            
            # Sell up to batch_size
            can_sell = min(shed, batch_size)
            if can_sell > 0:
                sale_rev = 0
                for _ in range(can_sell):
                    p = tomato_price(inv)
                    sale_rev += p
                    inv += 1
                shed -= can_sell
                units_sold += can_sell
                revenue += sale_rev
                history.append((can_sell, sale_rev / can_sell))
                
    # Terminal liquidation of any remaining shed
    if shed > 0:
        sale_rev = 0
        for _ in range(shed):
            p = tomato_price(inv)
            sale_rev += p
            inv += 1
        units_sold += shed
        revenue += sale_rev
        
    avg_realized_price = revenue / total_units if total_units else 0
    return revenue, avg_realized_price

def run_phase9_sweep():
    print("=" * 70)
    print("PHASE 9: TOMATO SALE BATCH SIZE SWEEP (76 TOTAL TOMATOES)")
    print("=" * 70)
    print(f"{'Batch Size':<12} | {'Total Revenue':<15} | {'Avg Realized Price':<20} | {'Delta vs Batch 1':<18}")
    print("-" * 70)
    
    base_rev, _ = simulate_liquidation_schedule(batch_size=1)
    
    best_b = None
    best_rev = -1
    
    for b in [1, 2, 4, 6, 8, 10, 15, 20, 25]:
        rev, avg_p = simulate_liquidation_schedule(batch_size=b)
        delta = rev - base_rev
        print(f"{b:<12} | ${rev:<14,.0f} | ${avg_p:<19.2f} | ${delta:<+17,.0f}")
        if rev > best_rev:
            best_rev = rev
            best_b = b
            
    print("-" * 70)
    print(f"Optimal Tomato Batch Size: {best_b} units (Total Rev: ${best_rev:,.0f})")

if __name__ == "__main__":
    run_phase9_sweep()
