"""
=============================================================================
SEARCH STRATEGY SPACE: LARGE-SCALE SYSTEMATIC MULTI-DIMENSIONAL OPTIMIZER
=============================================================================
Explores the full strategy parameter space across:
- Herd Composition: Cows (0-10), Sheep (0-6), Geese (0-6)
- Crop Fleet: Melons (0-30), Carrots, Wheat, Strawberries
- Land Expansion Timing: Day 0, Day 2, Day 5, Day 8, Day 12, None
- Labor Economics: 1-8 dynamic Fibonacci hands
- Market Execution: Batch size (6-20), Modulo-4 town sync, Frontrunning
- Liquidity Flow Simulation: First 12 days cash balance & solvency
=============================================================================
"""

import os
import sys
import time
import copy
import json
import itertools
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import CROPS, ANIMALS, PRODUCTS, compute_market_price, fib_hire_cost
from tournament_engine import run_paired_tournament
from candidates.slot5_hybrid_8c4s import Hybrid6C3S10MAgent

# ---------------------------------------------------------------------------
# 1. Capital Flow & Liquidity Simulator (Days 0 to 12)
# ---------------------------------------------------------------------------
def simulate_day0_12_liquidity(target_cows, target_sheep, target_geese, target_melons, day0_land=True):
    """
    Simulates cash balance and liquidity buffer day by day for the opening 12 days.
    Returns whether the strategy avoids bankruptcy and maintains animal feed.
    """
    money = 3000.0
    shed = {"WHEAT": 0, "COW": 0, "SHEEP": 0, "GOOSE": 0}
    cows_placed = 0
    sheep_placed = 0
    geese_placed = 0
    melon_seeds_planted = 0
    daily_logs = []

    # Day 0
    hires_day0 = 3
    hire_cost_day0 = sum(fib_hire_cost(i) for i in range(hires_day0))
    money -= hire_cost_day0

    if day0_land:
        money -= 1000.0  # NE Land

    # Buy animals on Day 0
    buy_cows = min(target_cows, int(max(0, money - 300) // 600))
    money -= buy_cows * 600
    cows_placed += buy_cows

    buy_sheep = min(target_sheep, int(max(0, money - 200) // 500))
    money -= buy_sheep * 500
    sheep_placed += buy_sheep

    buy_geese = min(target_geese, int(max(0, money - 100) // 300))
    money -= buy_geese * 300
    geese_placed += buy_geese

    # Feed buffer
    total_animals = cows_placed + sheep_placed + geese_placed
    feed_needed = total_animals * 3
    buy_wheat = min(feed_needed, int(max(0, money - 50) // 25))
    money -= buy_wheat * 25
    shed["WHEAT"] += buy_wheat

    # Melon seeds
    buy_melons = min(target_melons, int(max(0, money - 20) // 80))
    money -= buy_melons * 80
    melon_seeds_planted += buy_melons

    daily_logs.append({
        "day": 0,
        "money": money,
        "cows": cows_placed,
        "sheep": sheep_placed,
        "geese": geese_placed,
        "wheat": shed["WHEAT"],
        "melons": melon_seeds_planted
    })

    # Days 1 to 12 simulation
    solvent = True
    for d in range(1, 13):
        # Labor hire
        hires = 4 if d >= 4 else 3
        hire_cost = sum(fib_hire_cost(i) for i in range(hires))
        money -= hire_cost

        # Feed animals (1 wheat per animal)
        if shed["WHEAT"] < total_animals:
            # Must buy wheat from market
            wheat_deficit = total_animals - shed["WHEAT"]
            cost_wheat = wheat_deficit * 25
            if money < cost_wheat:
                solvent = False
            money -= cost_wheat
            shed["WHEAT"] = 0
        else:
            shed["WHEAT"] -= total_animals

        # Fertilizer yield (1 per animal per day)
        fert_rev = total_animals * 60  # Approx market spot price
        money += fert_rev

        # Animal yields
        # Geese yield eggs starting day 4
        if d >= 4 and geese_placed > 0:
            money += geese_placed * 4 * 35  # Eggs

        # Sheep yield wool starting day 6, every 3 days
        if d >= 6 and (d - 6) % 3 == 0 and sheep_placed > 0:
            money += sheep_placed * 6 * 120  # Wool

        # Cows yield milk starting day 8, every 2 days
        if d >= 8 and (d - 8) % 2 == 0 and cows_placed > 0:
            money += cows_placed * 6 * 100  # Milk

        # Melon harvest on Day 12
        if d == 12 and melon_seeds_planted > 0:
            money += melon_seeds_planted * 6 * 70  # Melon harvest cash infusion

        # Try to complete animal herd
        if cows_placed < target_cows and money >= 750:
            cows_placed += 1
            total_animals += 1
            money -= 600
        if sheep_placed < target_sheep and money >= 650:
            sheep_placed += 1
            total_animals += 1
            money -= 500

        daily_logs.append({
            "day": d,
            "money": money,
            "cows": cows_placed,
            "sheep": sheep_placed,
            "geese": geese_placed,
            "wheat": shed["WHEAT"],
            "solvent": solvent
        })

        if money < 0:
            solvent = False

    return {
        "solvent": solvent,
        "final_day12_money": money,
        "cows_reached": cows_placed,
        "sheep_reached": sheep_placed,
        "geese_reached": geese_placed,
        "daily_logs": daily_logs
    }

# ---------------------------------------------------------------------------
# 2. Parameter Grid Definitions
# ---------------------------------------------------------------------------
COW_VALUES = [0, 4, 6, 8, 10]
SHEEP_VALUES = [0, 2, 3, 4, 6]
GOOSE_VALUES = [0, 2, 4]
MELON_VALUES = [0, 5, 8, 10, 12, 15, 20, 25, 30]
BATCH_SIZES = [8, 12, 14, 18]

def build_parameter_candidates():
    candidates = []
    
    # Core Livestock / Melon Sweep
    for c in [4, 6, 8, 10]:
        for s in [2, 3, 4, 6]:
            for m in [8, 10, 12, 15, 20]:
                candidates.append({
                    "id": f"sweep_C{c}_S{s}_G0_M{m}_B14",
                    "cows": c, "sheep": s, "geese": 0, "melons": m, "batch": 14, "cycle2_m": 0
                })

    # Goose Hybrids
    for g in [2, 4]:
        candidates.append({"id": f"sweep_C6_S3_G{g}_M10_B14", "cows": 6, "sheep": 3, "geese": g, "melons": 10, "batch": 14, "cycle2_m": 0})
        candidates.append({"id": f"sweep_C4_S2_G{g}_M15_B14", "cows": 4, "sheep": 2, "geese": g, "melons": 15, "batch": 14, "cycle2_m": 0})

    # Melon Heavy vs Melon Zero
    candidates.append({"id": "sweep_C8_S4_G0_M0_B14", "cows": 8, "sheep": 4, "geese": 0, "melons": 0, "batch": 14, "cycle2_m": 0})
    candidates.append({"id": "sweep_C8_S4_G0_M25_B14", "cows": 8, "sheep": 4, "geese": 0, "melons": 25, "batch": 14, "cycle2_m": 0})
    candidates.append({"id": "sweep_C8_S4_G0_M30_B14", "cows": 8, "sheep": 4, "geese": 0, "melons": 30, "batch": 14, "cycle2_m": 0})

    # Batch Size Variations
    for b in [8, 12, 18]:
        candidates.append({"id": f"sweep_C8_S4_G0_M15_B{b}", "cows": 8, "sheep": 4, "geese": 0, "melons": 15, "batch": b, "cycle2_m": 0})

    return candidates

if __name__ == "__main__":
    print("=" * 80)
    print("STRATEGY PARAMETER SPACE SEARCH & LIQUIDITY ANALYSIS")
    print("=" * 80)

    # 1. Evaluate Liquidity Flow
    print("\n--- 1. LIQUIDITY PIPELINE AUDIT (Day 0 - Day 12) ---")
    configs_to_test = [
        ("6C/3S/10M Baseline", 6, 3, 0, 10),
        ("8C/4S/10M High-Cap", 8, 4, 0, 10),
        ("8C/4S/15M Heavy-Melon", 8, 4, 0, 15),
        ("10C/6S/10M Extreme-Livestock", 10, 6, 0, 10),
        ("4C/2S/4G/10M Goose-Hybrid", 4, 2, 4, 10),
    ]

    for name, c, s, g, m in configs_to_test:
        sim = simulate_day0_12_liquidity(c, s, g, m, day0_land=True)
        status = "SOLVENT" if sim["solvent"] else "INSOLVENT / CASH CRUNCH"
        print(f"  {name:30s} | Status: {status:20s} | Day 12 Cash: ${sim['final_day12_money']:8,.0f} | Herd: {sim['cows_reached']}C/{sim['sheep_reached']}S/{sim['geese_reached']}G")

    # 2. Generate Search Grid
    all_cands = build_parameter_candidates()
    print(f"\nGenerated {len(all_cands)} targeted candidate configurations.")
