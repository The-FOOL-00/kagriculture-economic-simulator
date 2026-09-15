import json
import numpy as np

with open("scratch/strawberry_lifecycle_ledger.json") as f:
    ledger = json.load(f)

# Analyze CL vs V2 fertilization
print("="*80)
print("SECTION 4 & 6: INDEPENDENT FERTILIZER AUDIT & ENGINE MECHANICS DERIVATION")
print("="*80)

for agent in ["CL", "V2"]:
    total_bushes = 0
    total_fert_actions = 0
    fert_by_age = {}
    fert_by_day = {}
    immature_fert_count_age9 = 0   # age < 9 days
    immature_fert_count_rule = 0   # D <= P + 6 (cannot reach cycle 1)
    mature_fert_count = 0
    effective_fert_count = 0
    wasted_fert_count = 0

    cycle_fertilized_count = [0, 0, 0, 0] # cycles 1, 2, 3, 4 where is_fert was True
    cycle_watered_count = [0, 0, 0, 0]
    cycle_total_count = [0, 0, 0, 0]

    seeds = sorted(list(ledger[agent].keys()), key=lambda x: int(x))
    for s in seeds:
        bushes = ledger[agent][s]
        total_bushes += len(bushes)
        for b in bushes:
            P = b["planting_day"]
            # Analyze each fertilization event
            for fe in b["fertilization_events"]:
                total_fert_actions += 1
                f_day = fe["day"]
                age = f_day - P
                fert_by_age[age] = fert_by_age.get(age, 0) + 1
                fert_by_day[f_day] = fert_by_day.get(f_day, 0) + 1

                if age < 9:
                    immature_fert_count_age9 += 1
                if f_day <= P + 6:
                    immature_fert_count_rule += 1
                else:
                    mature_fert_count += 1

            # Analyze production nights
            for pn in b["production_nights"]:
                c = pn["cycle"] - 1
                cycle_total_count[c] += 1
                if pn["was_watered"]:
                    cycle_watered_count[c] += 1
                if pn["is_fertilized"]:
                    cycle_fertilized_count[c] += 1

    n_seeds = len(seeds)
    print(f"\n--- AGENT: {agent} (Average across {n_seeds} seeds) ---")
    print(f"Total strawberry bushes: {total_bushes} (mean {total_bushes/n_seeds:.1f}/seed)")
    print(f"Total strawberry fertilizer actions: {total_fert_actions} (mean {total_fert_actions/n_seeds:.1f}/seed)")
    print(f"Fertilizer on age < 9 days: {immature_fert_count_age9} (mean {immature_fert_count_age9/n_seeds:.1f}/seed, {immature_fert_count_age9/max(1,total_fert_actions)*100:.1f}%)")
    print(f"Fertilizer on D <= P + 6 (expired before cycle 1): {immature_fert_count_rule} (mean {immature_fert_count_rule/n_seeds:.1f}/seed, {immature_fert_count_rule/max(1,total_fert_actions)*100:.1f}%)")
    print(f"Fertilizer on D >= P + 7 (can influence cycle 1+): {mature_fert_count} (mean {mature_fert_count/n_seeds:.1f}/seed)")
    
    print("\nFertilization by bush age (age = fert_day - planted_day):")
    for age in sorted(fert_by_age.keys()):
        print(f"  Age {age:2d}: {fert_by_age[age]:3d} actions ({fert_by_age[age]/n_seeds:.1f}/seed)")

    print("\nProduction Night Realization (Cycle 1..4):")
    for c in range(4):
        tot = cycle_total_count[c] / n_seeds
        wat = cycle_watered_count[c] / n_seeds
        fert = cycle_fertilized_count[c] / n_seeds
        print(f"  Cycle {c+1}: Total = {tot:.1f} | Watered = {wat:.1f} ({wat/max(0.01,tot)*100:.1f}%) | Watered+Fertilized (+2 yield) = {fert:.1f} ({fert/max(0.01,tot)*100:.1f}%)")

print("\n" + "="*80)
