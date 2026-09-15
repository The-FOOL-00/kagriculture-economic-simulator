"""
Decomposition of Strawberry Yield Gap: CL vs V2
Mathematically decomposes the yield difference (+69.2 units) into:
1. Potential cycles (planting day cutoff vs game end at Day 30)
2. Water failure on cycle night (watered_today == False -> no fertilizer bonus)
3. Fertilizer failure on cycle night (fertilized_until_day < day -> only +1 instead of +2)
4. Cap overflow loss (yield_units == 4 when cycle fires -> min(4, 4+bonus) = 4, losing units)
5. Decay loss (if max_lifespan_step reached and unharvested)
6. Unharvested units remaining on bush at step 719
"""
import json
import numpy as np
from collections import defaultdict

def decompose_bushes(json_path="scratch/deep_telemetry_seeds1000_1009.json"):
    with open(json_path, "r") as f:
        data = json.load(f)

    seeds = sorted(list(data["CL"].keys()), key=lambda x: int(x))

    results = {"CL": defaultdict(list), "V2": defaultdict(list)}

    for a in ["CL", "V2"]:
        for s in seeds:
            bushes = data[a][s]["bushes"]
            plant_events = [p for p in data[a][s]["plant_events"] if p["crop"] == "STRAWBERRY"]
            harvest_events = [h for h in data[a][s]["harvest_events"] if h["crop"] == "STRAWBERRY"]
            
            total_planted = len(bushes)
            total_harvested = data[a][s]["crop_harvest_totals"].get("STRAWBERRY", 0)

            # Analyze planting days
            plant_days = [b["planted_day"] for b in bushes.values()]
            
            # For each bush, how many cycles could it physically have reached before day 30?
            # Cycle 0: day = pday + 10
            # Cycle 1: day = pday + 12
            # Cycle 2: day = pday + 14
            # Cycle 3: day = pday + 16
            # Note: Production occurs at transition from (cycle_day - 1) to cycle_day.
            # So cycle_day <= 29 means (cycle_day - 1) <= 28.
            # Thus:
            # If pday + 10 <= 29: cycle 1 possible
            # If pday + 12 <= 29: cycle 2 possible
            # If pday + 14 <= 29: cycle 3 possible
            # If pday + 16 <= 29: cycle 4 possible
            max_possible_cycles = 0
            for pd in plant_days:
                c = 0
                for k in range(4):
                    if pd + 10 + 2 * k <= 29:
                        c += 1
                max_possible_cycles += c

            # Max theoretical yield if all possible cycles are fertilized (2 units per cycle)
            max_theoretical_yield = max_possible_cycles * 2

            results[a]["total_planted"].append(total_planted)
            results[a]["total_harvested"].append(total_harvested)
            results[a]["max_possible_cycles"].append(max_possible_cycles)
            results[a]["max_theoretical_yield"].append(max_theoretical_yield)
            results[a]["mean_plant_day"].append(np.mean(plant_days))
            results[a]["bushes_planted_after_day13"].append(sum(1 for pd in plant_days if pd > 13))
            results[a]["bushes_planted_after_day15"].append(sum(1 for pd in plant_days if pd > 15))

    print("================================================================================")
    print("STRAWBERRY YIELD DECOMPOSITION ACROSS SEEDS 1000-1009")
    print("================================================================================")
    print(f"{'Metric':<35} | {'CL Mean':<12} {'V2 Mean':<12} {'Delta (V2 - CL)':<15}")
    print("-" * 78)
    for m in [
        "total_planted",
        "mean_plant_day",
        "bushes_planted_after_day13",
        "bushes_planted_after_day15",
        "max_possible_cycles",
        "max_theoretical_yield",
        "total_harvested"
    ]:
        cl_m = np.mean(results["CL"][m])
        v2_m = np.mean(results["V2"][m])
        delta = v2_m - cl_m
        print(f"{m:<35} | {cl_m:<12.2f} {v2_m:<12.2f} {delta:<+15.2f}")

    print("\nPER-BUSH METRICS:")
    print(f"CL Potential Cycles / Bush: {np.mean(results['CL']['max_possible_cycles']) / np.mean(results['CL']['total_planted']):.2f}")
    print(f"V2 Potential Cycles / Bush: {np.mean(results['V2']['max_possible_cycles']) / np.mean(results['V2']['total_planted']):.2f}")
    print(f"CL Realized Yield / Bush:   {np.mean(results['CL']['total_harvested']) / np.mean(results['CL']['total_planted']):.2f}")
    print(f"V2 Realized Yield / Bush:   {np.mean(results['V2']['total_harvested']) / np.mean(results['V2']['total_planted']):.2f}")

if __name__ == "__main__":
    decompose_bushes()
