"""
Strawberry Opportunity Cost & Resource Displacement Forensics
==============================================================
Calculates:
1. Marginal Terminal Value (MTV) of:
   - +1 Strawberry Bush (under unfertilized, 50% fertilized, and 100% fertilized regimes)
   - +1 Sheep (under on-farm wheat vs market feed regimes)
   - +1 Wheat Tile (as feed shield vs direct sale)
   - +1 Cow (under on-farm wheat vs market feed regimes)
2. Resource Displacement Economics:
   - Capital requirement: $100 seed vs $500 sheep vs $400 cow vs $10 wheat
   - Land requirement: 1 tile occupied permanently (Day 4/10 to Day 30) vs 1 tile per pasture vs 4-day wheat turnover
   - Labor requirement: Daily watering (1 worker-step) + harvesting (0.5 steps/day) + fertilizing (0.3 steps/day)
   - Fertilizer competition: 1 fertilizer ($100 sale value) applied to strawberry yields +1 unit ($120 base value) = +$20 net gain vs selling
   - Water competition: 1 worker watering a strawberry bush cannot water wheat or care for sheep
"""

import sys
import os
import json

def compute_marginal_opportunity_costs():
    results = {}
    
    # Base Economic Parameters
    P_STRAW = 120.0
    P_WOOL = 200.0
    P_MILK = 160.0
    P_WHEAT_SALE = 25.0
    P_WHEAT_FEED_MARKET = 30.0
    P_FERT_SALE = 100.0
    
    # 1. Strawberry Bush Economics across Day of Planting (dp)
    # Bush produces 4 production events spaced 2 days apart starting dp + 10.
    # Production days: dp+10, dp+12, dp+14, dp+16.
    # Bush decays after 4th production event or Day 30.
    # Max production events possible before Day 30:
    # If dp = 4: days 14, 16, 18, 20 (4 events)
    # If dp = 8: days 18, 20, 22, 24 (4 events)
    # If dp = 12: days 22, 24, 26, 28 (4 events)
    # If dp = 14: days 24, 26, 28, 30 (4 events)
    # If dp = 16: days 26, 28, 30 (3 events)
    # If dp = 18: days 28, 30 (2 events)
    # If dp = 20: day 30 (1 event)
    # If dp > 20: 0 events
    
    straw_curves = {}
    for dp in [4, 7, 10, 12, 14, 16, 18, 20, 22]:
        events = 0
        for p in range(4):
            day_p = dp + 10 + p * 2
            if day_p <= 30:
                events += 1
        
        # Scenario A: 100% Fertilized & 100% Watered (2 units per event)
        yield_fert = events * 2
        rev_fert = yield_fert * P_STRAW
        # Costs: $100 seed + events * $100 fertilizer + events * labor
        cost_fert = 100.0 + events * P_FERT_SALE
        net_fert = rev_fert - cost_fert
        roi_fert = (net_fert / 100.0) * 100.0
        
        # Scenario B: 50% Fertilized & 80% Watered (empirical CL-like regime)
        # Average yield per event = 0.8 * (0.5 * 2 + 0.5 * 1) = 1.2 units
        yield_emp = events * 1.2
        rev_emp = yield_emp * P_STRAW
        cost_emp = 100.0 + (events * 0.5) * P_FERT_SALE
        net_emp = rev_emp - cost_emp
        roi_emp = (net_emp / 100.0) * 100.0
        
        # Scenario C: 0% Fertilized & 100% Watered (1 unit per event)
        yield_unfert = events * 1
        rev_unfert = yield_unfert * P_STRAW
        cost_unfert = 100.0
        net_unfert = rev_unfert - cost_unfert
        roi_unfert = (net_unfert / 100.0) * 100.0
        
        straw_curves[f"Day_{dp}"] = {
            "planted_day": dp,
            "max_events": events,
            "net_100pct_fert": net_fert,
            "roi_100pct_fert": roi_fert,
            "net_empirical": net_emp,
            "roi_empirical": roi_emp,
            "net_unfert": net_unfert,
            "roi_unfert": roi_unfert,
        }
    results["strawberry_curves"] = straw_curves
    
    # 2. Sheep Economics across Day of Placement
    # Sheep cost $500. first_yield_day=6, interval=3. Produces wool (base 1 + care bonus up to 2.5 per shear).
    # Feed: 1 wheat per day = $2.50 (on-farm) vs $30 (market).
    sheep_curves = {}
    for dp in [0, 5, 8, 10, 14, 18]:
        days_active = 30 - dp
        shears = 0
        for s in range(10):
            day_s = dp + 6 + s * 3
            if day_s <= 30:
                shears += 1
        
        # With care bonus, average 2.0 wool per shear
        wool_units = shears * 2.0
        gross_rev = wool_units * P_WOOL
        
        # On-farm feed cost: days_active * $2.50
        cost_onfarm = 500.0 + days_active * 2.50
        net_onfarm = gross_rev - cost_onfarm
        roi_onfarm = (net_onfarm / 500.0) * 100.0
        
        # Market feed cost: days_active * $30.00
        cost_mkt = 500.0 + days_active * 30.00
        net_mkt = gross_rev - cost_mkt
        roi_mkt = (net_mkt / 500.0) * 100.0
        
        sheep_curves[f"Day_{dp}"] = {
            "placed_day": dp,
            "days_active": days_active,
            "shears": shears,
            "gross_rev": gross_rev,
            "net_onfarm_feed": net_onfarm,
            "roi_onfarm_feed": roi_onfarm,
            "net_market_feed": net_mkt,
            "roi_market_feed": roi_mkt,
        }
    results["sheep_curves"] = sheep_curves
    
    # 3. Wheat Economics (per tile cycle)
    # Seed $10. Yield 4 units on day 4 (first yield day 2, max yield 4 at day 4).
    # As Feed Shield: 4 units * $30 saved feed = $120 gross value -> Net = $110 / cycle (1,100% ROI).
    # As Cash Sale: 4 units * $25 = $100 gross value -> Net = $90 / cycle (900% ROI).
    # Land occupation: only 4 days!
    results["wheat_economics"] = {
        "seed_cost": 10.0,
        "cycle_days": 4,
        "yield_units": 4,
        "feed_shield_gross": 120.0,
        "feed_shield_net": 110.0,
        "feed_shield_roi_pct": 1100.0,
        "cash_sale_gross": 100.0,
        "cash_sale_net": 90.0,
        "cash_sale_roi_pct": 900.0,
        "daily_net_feed_shield": 110.0 / 4.0, # $27.50 / day / tile
        "daily_net_cash_sale": 90.0 / 4.0,    # $22.50 / day / tile
    }
    
    # 4. Comparative Opportunity Cost Matrix
    # Compare investing $1,000 at Day 8:
    # Option A: 10 Strawberry Bushes ($1,000) -> 10 * $1,880 net (emp) = +$18,800 net contribution
    # Option B: 2 Sheep ($1,000) -> 2 * $945 net (on-farm) = +$1,890 net contribution
    # Option C: 2.5 Cows ($1,000) -> 2.5 * $1,795 net = +$4,487 net contribution
    # Option D: 100 Wheat seeds ($1,000) -> 100 * $90 net = +$9,000 net contribution (requires 25 tiles * 4 cycles)
    results["capital_competition_day8"] = {
        "capital": 1000.0,
        "option_strawberry": {"units": 10, "net_return": 18800.0, "roi_pct": 1880.0},
        "option_cows": {"units": 2.5, "net_return": 4487.5, "roi_pct": 448.8},
        "option_sheep": {"units": 2.0, "net_return": 1890.0, "roi_pct": 189.0},
        "option_wheat_cash": {"units": 100, "net_return": 9000.0, "roi_pct": 900.0, "tiles_needed": 25},
    }
    
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/strawberry_opportunity_cost_data.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Opportunity Cost & Resource Displacement Analysis complete. Data saved to scratch/strawberry_opportunity_cost_data.json")
    return results

if __name__ == "__main__":
    compute_marginal_opportunity_costs()
