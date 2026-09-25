"""
Compare Declarative Backbone vs V54 and V66 on the 10-seed comparison audit
"""
import json

with open("scratch/audit_10seed_results.json") as f:
    data = json.load(f)

print("10-Seed Comparative Forensics:")
print(f"{'Seed':<6} | {'IDLE r0':<10} | {'V54 r0':<10} {'V54 r1':<10} | {'V66 r0':<10} {'V66 r1':<10}")
print("-" * 65)

idle_runs = data.get("IDLE", [])
v54_runs = data.get("V54", [])
v66_runs = data.get("V66", [])

for i in range(len(idle_runs)):
    d_idle = idle_runs[i]
    d_v54 = v54_runs[i]
    d_v66 = v66_runs[i]
    seed = d_idle["seed"]
    print(f"{seed:<6} | {d_idle['r0']:<10.0f} | {d_v54['r0']:<10.0f} {d_v54['r1']:<10.0f} | {d_v66['r0']:<10.0f} {d_v66['r1']:<10.0f}")

print("\n--- Why did V54 achieve 120k-140k? ---")
# Check day 10, day 15, day 20 cash
for name, runs in [("V54 Opponent Run", v54_runs)]:
    print(f"\n{name} Progression:")
    for r in runs[:3]:
        print(f"Seed {r['seed']}: Day10 cash=${r.get('day10_cash',0):.0f} Day15 cash=${r.get('day15_cash',0):.0f} Day20 cash=${r.get('day20_cash',0):.0f} Animals placed={r.get('animals_placed')} Land={r.get('land_unlocked')}")
