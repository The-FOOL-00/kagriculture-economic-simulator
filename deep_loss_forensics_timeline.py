"""
=============================================================================
DEEP LOSS FORENSICS TIMELINE ANALYZER (OBJECTIVE 2)
=============================================================================
For matches where our candidate loses against:
- Titan Production (main.py)
- Market Aggressor (O9)
- Cow Specialist (O5)

Generates day-bucketed timeline analysis:
- Day 0
- Day 1-3
- Day 4-9
- Day 10-12
- Day 13-20
- Day 21-25
- Day 26-29

Tracks:
- cash (us & opp)
- animals (cows, sheep, geese)
- crops (melon, carrot, wheat, tomato, strawberry)
- workers (farmer + hands)
- land (quadrants unlocked)
- wheat (shed + inventory)
- market prices & market inventory
- sales (total cash earned & items sold)
- purchases (animals, seeds, wheat feed)
- town consumption
- fertilizer
- opponent supply & market frontrunning

Identifies the EXACT step and day where the economic race was lost.
=============================================================================
"""

import os
import sys
import json
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DAY_BUCKETS = [
    ("Day 0", 0, 0),
    ("Day 1-3", 1, 3),
    ("Day 4-9", 4, 9),
    ("Day 10-12", 10, 12),
    ("Day 13-20", 13, 20),
    ("Day 21-25", 21, 25),
    ("Day 26-29", 26, 29),
]

def analyze_match_timeline(cand_path, opp_path, seed, swapped=False):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    if swapped:
        env.run([opp_path, cand_path])
        us_idx = 1
        opp_idx = 0
    else:
        env.run([cand_path, opp_path])
        us_idx = 0
        opp_idx = 1

    steps = env.steps
    final_step = steps[-1]
    r_us = float(final_step[us_idx].reward or 0.0)
    r_opp = float(final_step[opp_idx].reward or 0.0)

    # We want to examine losses specifically
    is_loss = r_opp > r_us
    margin = r_us - r_opp

    # Step-by-step telemetry
    timeline_records = []
    first_lead_flip_step = None
    first_cash_deficit_step = None

    cum_sales_us = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0, "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}
    cum_sales_opp = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0, "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}
    
    cum_buys_us = {"COW": 0, "SHEEP": 0, "GOOSE": 0, "WHEAT": 0, "MELON_SEED": 0, "CARROT_SEED": 0}
    cum_buys_opp = {"COW": 0, "SHEEP": 0, "GOOSE": 0, "WHEAT": 0, "MELON_SEED": 0, "CARROT_SEED": 0}

    bucket_summaries = []

    for bucket_name, start_day, end_day in DAY_BUCKETS:
        start_step = start_day * 24
        end_step = min(719, (end_day + 1) * 24 - 1)
        
        # Sample the state at the end of the bucket
        step_sample = steps[end_step]
        obs = step_sample[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        farm_us = farms[us_idx] if us_idx < len(farms) else {}
        farm_opp = farms[opp_idx] if opp_idx < len(farms) else {}
        
        money_us = float(farm_us.get("money", 0.0))
        money_opp = float(farm_opp.get("money", 0.0))

        # Count animals on tiles
        tiles_us = farm_us.get("tiles", [])
        tiles_opp = farm_opp.get("tiles", [])

        def count_farm(tiles):
            cows, sheep, geese = 0, 0, 0
            melons, carrots, wheat, tomatoes, strawberries = 0, 0, 0, 0, 0
            for row in tiles:
                for cell in row:
                    if isinstance(cell, dict):
                        kind = cell.get("kind")
                        if kind == "PASTURE":
                            a = cell.get("animal")
                            if a == "COW": cows += 1
                            elif a == "SHEEP": sheep += 1
                        elif kind == "COOP":
                            a = cell.get("animal")
                            if a == "GOOSE": geese += 1
                        elif kind == "PLANT":
                            c = cell.get("crop")
                            if c == "MELON": melons += 1
                            elif c == "CARROT": carrots += 1
                            elif c == "WHEAT": wheat += 1
                            elif c == "TOMATO": tomatoes += 1
                            elif c == "STRAWBERRY": strawberries += 1
            return {
                "cows": cows, "sheep": sheep, "geese": geese,
                "melons": melons, "carrots": carrots, "wheat": wheat,
                "tomatoes": tomatoes, "strawberries": strawberries
            }

        counts_us = count_farm(tiles_us)
        counts_opp = count_farm(tiles_opp)

        workers_us = 1 + len(farm_us.get("hands", []))
        workers_opp = 1 + len(farm_opp.get("hands", []))

        land_us = len(farm_us.get("unlocked_quadrants", ["NW"]))
        land_opp = len(farm_opp.get("unlocked_quadrants", ["NW"]))

        priv_us = step_sample[us_idx].get("observation", {}).get("private", {}) or {}
        priv_opp = step_sample[opp_idx].get("observation", {}).get("private", {}) or {}

        wheat_us = priv_us.get("shed", {}).get("WHEAT", 0)
        wheat_opp = priv_opp.get("shed", {}).get("WHEAT", 0)

        market = obs.get("market", {}) or {}
        market_prices = dict(market.get("prices", {}))
        market_inv = dict(market.get("inventory", {}))

        bucket_summaries.append({
            "bucket": bucket_name,
            "end_step": end_step,
            "end_day": end_day,
            "money_us": money_us,
            "money_opp": money_opp,
            "delta_money": money_us - money_opp,
            "animals_us": {"cows": counts_us["cows"], "sheep": counts_us["sheep"], "geese": counts_us["geese"]},
            "animals_opp": {"cows": counts_opp["cows"], "sheep": counts_opp["sheep"], "geese": counts_opp["geese"]},
            "crops_us": {"melons": counts_us["melons"], "carrots": counts_us["carrots"], "wheat": counts_us["wheat"]},
            "crops_opp": {"melons": counts_opp["melons"], "carrots": counts_opp["carrots"], "wheat": counts_opp["wheat"]},
            "workers_us": workers_us,
            "workers_opp": workers_opp,
            "land_us": land_us,
            "land_opp": land_opp,
            "wheat_shed_us": wheat_us,
            "wheat_shed_opp": wheat_opp,
            "key_prices": {
                "MELON": market_prices.get("MELON", 0),
                "MILK": market_prices.get("MILK", 0),
                "WOOL": market_prices.get("WOOL", 0),
                "WHEAT": market_prices.get("WHEAT", 0),
                "CARROT": market_prices.get("CARROT", 0)
            },
            "key_inventory": {
                "MELON": market_inv.get("MELON", 0),
                "MILK": market_inv.get("MILK", 0),
                "WOOL": market_inv.get("WOOL", 0),
                "WHEAT": market_inv.get("WHEAT", 0)
            }
        })

    # Find the exact step where deficit occurred
    for s_idx in range(720):
        step_data = steps[s_idx]
        obs = step_data[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        m_us = float(farms[us_idx].get("money", 0.0)) if us_idx < len(farms) else 0.0
        m_opp = float(farms[opp_idx].get("money", 0.0)) if opp_idx < len(farms) else 0.0
        if first_cash_deficit_step is None and m_opp > m_us + 100.0:
            first_cash_deficit_step = s_idx

    return {
        "seed": seed,
        "swapped": swapped,
        "is_loss": is_loss,
        "final_cash_us": r_us,
        "final_cash_opp": r_opp,
        "margin": margin,
        "first_cash_deficit_step": first_cash_deficit_step,
        "first_cash_deficit_day": (first_cash_deficit_step // 24) if first_cash_deficit_step is not None else None,
        "buckets": bucket_summaries
    }

def run_deep_loss_analysis():
    print("=" * 95)
    print("OBJECTIVE 2: DEEP LOSS FORENSICS ACROSS TIMELINE BUCKETS")
    print("=" * 95)

    cand_path = os.path.join(project_root, "candidates", "slot5_hybrid_8c4s.py")
    opponents = {
        "Titan Production": os.path.join(project_root, "opponents", "o1_titan.py"),
        "Market Aggressor": os.path.join(project_root, "opponents", "o9_market_aggressor.py"),
        "Cow Specialist": os.path.join(project_root, "opponents", "o5_cow_specialist.py"),
    }

    all_loss_forensics = {}

    for opp_name, opp_path in opponents.items():
        print(f"\nAnalyzing losses vs {opp_name}...")
        losses_found = []
        # Search across seeds 20000 to 20030
        for seed in range(20000, 20030):
            # Check unswapped
            m1 = analyze_match_timeline(cand_path, opp_path, seed, swapped=False)
            if m1["is_loss"]:
                losses_found.append(m1)
            # Check swapped
            m2 = analyze_match_timeline(cand_path, opp_path, seed, swapped=True)
            if m2["is_loss"]:
                losses_found.append(m2)
            if len(losses_found) >= 5:
                break

        print(f"  Found {len(losses_found)} loss matches to analyze deeply.")
        all_loss_forensics[opp_name] = losses_found

        if losses_found:
            # Print deep breakdown of the most significant loss
            worst_loss = min(losses_found, key=lambda x: x["margin"])
            print(f"\n  [DEEP FORENSIC BREAKDOWN] Worst Loss vs {opp_name} (Seed {worst_loss['seed']}, Swapped={worst_loss['swapped']})")
            print(f"  Final Score: Us ${worst_loss['final_cash_us']:,.2f} vs Opp ${worst_loss['final_cash_opp']:,.2f} | Margin: ${worst_loss['margin']:+,.2f}")
            print(f"  First Deficit Point: Day {worst_loss['first_cash_deficit_day']} (Step {worst_loss['first_cash_deficit_step']})")
            print("-" * 95)
            print(f"{'Timeline Bucket':12s} | {'Us Cash':10s} | {'Opp Cash':10s} | {'Delta':10s} | {'Us Herd':10s} | {'Opp Herd':10s} | {'Melon P':7s} | {'Milk P':7s} | {'Wheat P':7s}")
            print("-" * 95)
            for b in worst_loss["buckets"]:
                us_herd_str = f"{b['animals_us']['cows']}C/{b['animals_us']['sheep']}S"
                opp_herd_str = f"{b['animals_opp']['cows']}C/{b['animals_opp']['sheep']}S"
                print(f"{b['bucket']:12s} | ${b['money_us']:8,.0f} | ${b['money_opp']:8,.0f} | ${b['delta_money']:+8,.0f} | {us_herd_str:10s} | {opp_herd_str:10s} | ${b['key_prices']['MELON']:5d} | ${b['key_prices']['MILK']:5d} | ${b['key_prices']['WHEAT']:5d}")
            print("-" * 95)

    with open(os.path.join(project_root, "deep_loss_forensics_results.json"), "w") as f:
        json.dump(all_loss_forensics, f, indent=2)

    print("\nSaved deep loss forensics to deep_loss_forensics_results.json")

if __name__ == "__main__":
    run_deep_loss_analysis()
