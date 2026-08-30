import os
import math
import json
import kaggle_environments
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    MARKET_PARAMS, market_price, _shape, HINGE_GAIN, ANIMALS, PRODUCTS, SHOPS,
    TOWN_CENTER_PRODUCTS, MAX_SHOP_INSTANCES
)

def run_verification():
    print(f"kaggle-environments version: {kaggle_environments.__version__}")
    print("=" * 70)
    print("PART 5 & 6: CURRENT 1.32.7 MARKET PARAMETERS & PRICING")
    print("=" * 70)
    
    rows = []
    for p in PRODUCTS:
        mp = MARKET_PARAMS[p]
        T = mp["T"]
        I0 = mp["I0"]
        base = mp["base"]
        
        p_scarcity2 = market_price(p, I0 - 2 * T)
        p_scarcity1 = market_price(p, I0 - T)
        p_base = market_price(p, I0)
        p_glut1 = market_price(p, I0 + T)
        p_glut2 = market_price(p, I0 + 2 * T)
        
        row = {
            "Product": p,
            "Base": base,
            "I0": I0,
            "T": T,
            "Below_Func": mp["below_func"],
            "Below_Target": mp["below_target"],
            "Above_Func": mp["above_func"],
            "Above_Target": mp["above_target"],
            "P(I0-2T)": p_scarcity2,
            "P(I0-T)": p_scarcity1,
            "P(I0)": p_base,
            "P(I0+T)": p_glut1,
            "P(I0+2T)": p_glut2,
        }
        rows.append(row)
        
    print(f"{'Product':<12} | {'Base':<5} | {'I0':<6} | {'T':<5} | {'Below Func':<10} | {'Below Tgt':<9} | {'Above Func':<10} | {'Above Tgt':<9} | {'P(I0-2T)':<8} | {'P(I0-T)':<8} | {'P(I0)':<6} | {'P(I0+T)':<8} | {'P(I0+2T)':<8}")
    print("-" * 130)
    for r in rows:
        print(f"{r['Product']:<12} | {r['Base']:5d} | {r['I0']:6d} | {r['T']:5d} | {r['Below_Func']:<10} | {r['Below_Target']:<9.2f} | {r['Above_Func']:<10} | {r['Above_Target']:<9.2f} | ${r['P(I0-2T)']:<7d} | ${r['P(I0-T)']:<7d} | ${r['P(I0)']:<5d} | ${r['P(I0+T)']:<7d} | ${r['P(I0+2T)']:<7d}")

    print("\n" + "=" * 70)
    print("PART 6: DEMAND MECHANICS SPECIFICATIONS")
    print("=" * 70)
    print(f"Town Center Sell Interval: 24 turns (once per day at step % 24 == 0)")
    print(f"Town Center Consumes: 1 unit of each product in {TOWN_CENTER_PRODUCTS}")
    print(f"Town Shop Unlock Interval: 3 days (days 3, 6, 9, 12, 15, 18, 21, 24)")
    print(f"Town Shop Selection: Uniform random WITH REPLACEMENT from {sorted(list(SHOPS.keys()))}")
    print(f"Town Shop Max Instances: {MAX_SHOP_INSTANCES}")
    print(f"Town Shop Sell Interval: 4 turns (steps 0, 4, 8, 12, 16, 20 per day)")
    print("Town Shop Demands:")
    for shop, prods in SHOPS.items():
        mult = 2 if len(prods) == 1 else 1
        print(f"  - {shop:<18}: consumes {mult}x {prods} every 4 turns")

    print("\n" + "=" * 70)
    print("ANIMALS AND COSTS")
    print("=" * 70)
    for a, info in ANIMALS.items():
        print(f"  - {a:<8}: Cost=${info['cost']}, Structure={info['structure']}, FirstYieldDay={info['first_yield_day']}, Interval={info['interval']}, MaxHeld={info['max_held']}, Product={info['product']}")

if __name__ == "__main__":
    run_verification()
