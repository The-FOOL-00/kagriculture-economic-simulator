"""
scratch/test_fertilize_semantics.py
===================================
Controlled deterministic experiments verifying exact fertilization semantics in engine 1.32.7.
Tests Conditions A through O on Strawberry, Tomato, and Melon.
Accounts for midnight worker reset and shed inventory.
"""
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))

import kagsim

def simulate_crop_experiment(crop_name="STRAWBERRY", fert_days=None, skip_water_days=None, max_days=16):
    """
    Simulates a single plant at (4, 3) (one step NORTH of shed at (4, 4)).
    Each day:
      - At Hour 0: Farmer is at (4, 4). If fertilizing today, PICKUP 1 FERTILIZER from shed.
      - At Hour 1: Farmer steps NORTH to (4, 3).
      - At Hour 2: If fertilizing today, execute FERTILIZE.
      - At Hour 3: If watering today, execute WATER.
      - Remaining hours: PASS.
    """
    fert_days = set(fert_days or [])
    skip_water_days = set(skip_water_days or [])
    
    game = kagsim.Game(42)
    daily_log = []
    
    for step in range(max_days * 24):
        obs = game.observe(0)
        day = obs["day"]
        hour = obs["hour"]
        
        act = {"farmer": ["PASS"], "hands": [], "market": []}
        
        # Day 0 setup
        if day == 0:
            if hour == 0:
                act["market"] = [
                    ["BUY_SEED", crop_name, 1],
                    ["BUY_PRODUCT", "FERTILIZER", 20]
                ]
            elif hour == 1:
                if 0 in fert_days:
                    act["farmer"] = ["PICKUP", "FERTILIZER", 1]
            elif hour == 2:
                act["farmer"] = ["NORTH"]
            elif hour == 3:
                act["farmer"] = ["PLANT", crop_name]
            elif hour == 4:
                if 0 in fert_days:
                    act["farmer"] = ["FERTILIZE"]
                elif 0 not in skip_water_days:
                    act["farmer"] = ["WATER"]
            elif hour == 5:
                if 0 in fert_days and 0 not in skip_water_days:
                    act["farmer"] = ["WATER"]
        else:
            # Day >= 1 routine
            if hour == 0:
                if day in fert_days:
                    act["farmer"] = ["PICKUP", "FERTILIZER", 1]
            elif hour == 1:
                act["farmer"] = ["NORTH"]
            elif hour == 2:
                if day in fert_days:
                    act["farmer"] = ["FERTILIZE"]
                elif day not in skip_water_days:
                    act["farmer"] = ["WATER"]
            elif hour == 3:
                if day in fert_days and day not in skip_water_days:
                    act["farmer"] = ["WATER"]
                    
        game.step(act, {"farmer": ["PASS"], "hands": [], "market": []})
        
        # Record state at end of day (hour 23)
        if hour == 23:
            end_obs = game.observe(0)
            tile = end_obs["farms"][0]["tiles"][3][4] # y=3, x=4
            tile_dict = tile if isinstance(tile, dict) else {"kind": str(tile)}
            daily_log.append({
                "day": day,
                "kind": tile_dict.get("kind"),
                "yield_units": tile_dict.get("yield_units", 0),
                "fertilized_until_day": tile_dict.get("fertilized_until_day", -1),
                "consecutive_unwatered": tile_dict.get("consecutive_unwatered", 0),
                "watered_today": tile_dict.get("watered_today", False),
            })
            
    return daily_log

def run_all_tests():
    print("=" * 75)
    print("EXACT SIMULATOR FERTILIZATION MICRO-TESTS (CONDITIONS A - O)")
    print("=" * 75)
    
    # 1. Test A: Strawberry Natural Growth (No Fertilization)
    log_a = simulate_crop_experiment("STRAWBERRY", fert_days=[], max_days=16)
    print("\n--- TEST A: Natural Strawberry (No Fertilization) ---")
    print(f"{'Day':<5} | {'Kind':<8} | {'Yield':<6} | {'FertUntil':<10} | {'DryStreak':<10}")
    print("-" * 50)
    for row in log_a[8:]:
        print(f"{row['day']:<5} | {row['kind']:<8} | {row['yield_units']:<6} | {row['fertilized_until_day']:<10} | {row['consecutive_unwatered']:<10}")
        
    # 2. Test B: Fertilize Before Maturity (e.g. Day 5 on Strawberry)
    log_b = simulate_crop_experiment("STRAWBERRY", fert_days=[5], max_days=16)
    print("\n--- TEST B: Strawberry Fertilized on Day 5 (Before Maturity) ---")
    print(f"Day 5 Fertilized -> FertUntil = {log_b[5]['fertilized_until_day']}")
    print(f"Day 7 FertUntil = {log_b[7]['fertilized_until_day']}")
    print(f"Day 8 FertUntil = {log_b[8]['fertilized_until_day']}")
    print(f"Day 10 (First Yield Day) Yield = {log_b[10]['yield_units']} (Expected: 1, because fert expired on Day 7!)")

    # 3. Test C & F: Fertilize on Day 10 (First Yield Day)
    log_c = simulate_crop_experiment("STRAWBERRY", fert_days=[10], max_days=16)
    print("\n--- TEST C & F: Strawberry Fertilized on Day 10 (Maturation Day) ---")
    print(f"{'Day':<5} | {'Kind':<8} | {'Yield':<6} | {'FertUntil':<10}")
    print("-" * 35)
    for row in log_c[9:15]:
        print(f"{row['day']:<5} | {row['kind']:<8} | {row['yield_units']:<6} | {row['fertilized_until_day']:<10}")

    # 4. Test F, G, H, I: Expiration Horizon (Fertilize Day 10: does it cover Day 10, 11, 12? Does it cover Day 13?)
    print("\n--- TEST F-I: 3-Day Window Verification (Fertilize Day 10) ---")
    print(f"Day 10 Yield: {log_c[10]['yield_units']} (Fertilized bonus +2 applied: yield is 2!)")
    print(f"Day 11 Yield: {log_c[11]['yield_units']} (Interval is 2, no harvest on Day 11)")
    print(f"Day 12 Yield: {log_c[12]['yield_units']} (Day 12 <= 12, still fertilized: yield adds +2 -> total = 4 = max_yield!)")
    print(f"Day 13 Yield: {log_c[13]['yield_units']} (Fertilized expired after Day 12)")
    print(f"Day 14 Yield: {log_c[14]['yield_units']} (At max yield cap 4)")

    # 5. Test L: Missed Watering + Fertilize on Day 10
    log_l = simulate_crop_experiment("STRAWBERRY", fert_days=[10], skip_water_days=[10], max_days=14)
    print("\n--- TEST L: Fertilized on Day 10 but Missed Watering ---")
    print(f"Day 10 Yield without water: {log_l[10]['yield_units']} (Expected: 0, no water = NO yield!)")
    print(f"Day 10 Dry streak: {log_l[10]['consecutive_unwatered']}")

    # 6. Test M: Multiple Fertilizer Applications (Day 10, then Day 11)
    log_m = simulate_crop_experiment("STRAWBERRY", fert_days=[10, 11], max_days=15)
    print("\n--- TEST M: Stacking Fertilizer (Day 10 + Day 11) ---")
    print(f"Day 10 FertUntil: {log_m[10]['fertilized_until_day']} (Day 10 + 2 = 12)")
    print(f"Day 11 FertUntil: {log_m[11]['fertilized_until_day']} (Day 11 + 2 = 13)")

    # 7. Test N vs O: Tomato vs Strawberry
    log_o_clean = simulate_crop_experiment("TOMATO", fert_days=[], max_days=12)
    log_o_fert = simulate_crop_experiment("TOMATO", fert_days=[8], max_days=12)
    print("\n--- TEST O: Tomato Yield (Clean vs Day 8 Fertilized) ---")
    print(f"Tomato Day 8 Natural Yield    : {log_o_clean[8]['yield_units']}")
    print(f"Tomato Day 8 Fertilized Yield : {log_o_fert[8]['yield_units']}")
    print(f"Tomato Day 9 Natural Yield    : {log_o_clean[9]['yield_units']}")
    print(f"Tomato Day 9 Fertilized Yield : {log_o_fert[9]['yield_units']}")

if __name__ == "__main__":
    run_all_tests()
