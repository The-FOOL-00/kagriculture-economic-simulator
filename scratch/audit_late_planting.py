import json
import numpy as np

with open("scratch/strawberry_lifecycle_ledger.json") as f:
    ledger = json.load(f)

print("="*80)
print("SECTION 11: INDEPENDENT LATE-PLANTING AUDIT (SEEDS 1000-1009)")
print("="*80)

for agent in ["CL", "V2"]:
    seeds = ledger[agent]
    n_seeds = len(seeds)
    late_bushes_d15 = []
    late_bushes_d14 = []
    cycles_lost = []
    units_harvested_late = []
    seed_cost_late = []

    for s, bushes in seeds.items():
        count_d15 = 0
        count_d14 = 0
        s_cycles_lost = 0
        s_units = 0
        for b in bushes:
            P = b["planting_day"]
            if P >= 15:
                count_d15 += 1
                # Potential cycles before day 30:
                # Cycle 1: P+9, Cycle 2: P+11, Cycle 3: P+13, Cycle 4: P+15
                max_possible = sum(1 for c in range(4) if P + 9 + 2*c <= 29)
                lost_cycles = 4 - max_possible
                s_cycles_lost += lost_cycles
                s_units += b["units_harvested"]
            if P >= 14:
                count_d14 += 1
        late_bushes_d15.append(count_d15)
        late_bushes_d14.append(count_d14)
        cycles_lost.append(s_cycles_lost)
        units_harvested_late.append(s_units)

    print(f"\n--- {agent} ---")
    print(f"Bushes planted Day >= 14: mean = {np.mean(late_bushes_d14):.2f}, per seed = {late_bushes_d14}")
    print(f"Bushes planted Day >= 15: mean = {np.mean(late_bushes_d15):.2f}, per seed = {late_bushes_d15}")
    print(f"Cycles structurally lost due to Day 30 horizon: mean = {np.mean(cycles_lost):.2f}")
    print(f"Yield harvested from Day >= 15 plantings: mean = {np.mean(units_harvested_late):.2f}")
    # Net economic return of Day >= 15 plantings:
    # Seed cost = $100. Base strawberry revenue = $120.
    seed_cost = np.mean(late_bushes_d15) * 100
    rev = np.mean(units_harvested_late) * 120
    print(f"Estimated seed capital spent on Day >= 15: ${seed_cost:.1f}")
    print(f"Estimated gross revenue from Day >= 15: ${rev:.1f}")
    print(f"Net margin: ${rev - seed_cost:+.1f}")
