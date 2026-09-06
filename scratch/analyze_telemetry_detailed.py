import json
import os

with open("scratch/telemetry_arch_base_seed215.json", "r") as f:
    arch_trace = json.load(f)

with open("scratch/telemetry_v2_seed215.json", "r") as f:
    v2_trace = json.load(f)

print("="*80)
print("PHASE 3 & 4: DAY-0 (STEPS 0..24) DETAILED STATE COMPARISON")
print("="*80)
print(f"{'Step':<5} | {'ARCH Money':<12} | {'V2 Money':<12} | {'ARCH Past':<10} | {'V2 Past':<10} | {'ARCH Cows':<10} | {'V2 Cows':<10} | {'ARCH Hands':<10} | {'V2 Hands':<10}")
print("-" * 95)
for i in range(25):
    at = arch_trace[i]
    vt = v2_trace[i]
    print(f"{i:<5} | ${at['money_after']:<11,.0f} | ${vt['money_after']:<11,.0f} | {at['pastures_built']:<10} | {vt['pastures_built']:<10} | {at['cows_placed']:<10} | {vt['cows_placed']:<10} | {at['num_hands']:<10} | {vt['num_hands']:<10}")

print("\n" + "="*80)
print("DAY 0 ACTION COMPARISON (STEPS 0..5)")
print("="*80)
for i in range(6):
    print(f"\n--- STEP {i} ---")
    print(f"ARCH Action: {arch_trace[i]['action']}")
    print(f"V2 Action:   {v2_trace[i]['action']}")

print("\n" + "="*80)
print("PHASE 5: PASTURE CONSTRUCTION AUDIT ACROSS 720 TURNS")
print("="*80)
arch_past_steps = []
v2_past_steps = []
prev_ap = 0
prev_vp = 0
for i, (at, vt) in enumerate(zip(arch_trace, v2_trace)):
    if at["pastures_built"] > prev_ap:
        arch_past_steps.append((i, at["pastures_built"]))
        prev_ap = at["pastures_built"]
    if vt["pastures_built"] > prev_vp:
        v2_past_steps.append((i, vt["pastures_built"]))
        prev_vp = vt["pastures_built"]

print(f"ARCH Total Pastures Built: {prev_ap} / 16 target")
print(f"ARCH Pasture Build Steps: {arch_past_steps}")
print(f"V2 Total Pastures Built:   {prev_vp} / 14 target")
print(f"V2 Pasture Build Steps:   {v2_past_steps}")

print("\n" + "="*80)
print("PHASE 7: QUADRANT UNLOCK AUDIT")
print("="*80)
arch_quad_steps = []
v2_quad_steps = []
prev_aq = 1
prev_vq = 1
for i, (at, vt) in enumerate(zip(arch_trace, v2_trace)):
    if len(at["unlocked_quads"]) > prev_aq:
        arch_quad_steps.append((i, at["unlocked_quads"]))
        prev_aq = len(at["unlocked_quads"])
    if len(vt["unlocked_quads"]) > prev_vq:
        v2_quad_steps.append((i, vt["unlocked_quads"]))
        prev_vq = len(vt["unlocked_quads"])

print(f"ARCH Quadrant Unlock Milestones: {arch_quad_steps}")
print(f"V2 Quadrant Unlock Milestones:   {v2_quad_steps}")

print("\n" + "="*80)
print("PHASE 8: LIVESTOCK PLACEMENT AUDIT")
print("="*80)
print(f"ARCH Final Cows: {arch_trace[-1]['cows_placed']}, Sheep: {arch_trace[-1]['sheep_placed']}")
print(f"V2 Final Cows:   {v2_trace[-1]['cows_placed']}, Sheep: {v2_trace[-1]['sheep_placed']}")

print("\n" + "="*80)
print("PHASE 10: FINANCIAL CHECKPOINTS LEDGER")
print("="*80)
checkpoints = [0, 1, 5, 13, 24, 48, 72, 100, 121, 122, 123, 153, 158, 168, 197, 198, 199, 200, 201, 213, 240, 256, 266, 306, 360, 500, 650, 719]
print(f"{'Step':<6} | {'ARCH Money':<12} | {'V2 Money':<12} | {'ARCH Quads':<12} | {'V2 Quads':<12} | {'ARCH Past':<10} | {'V2 Past':<10} | {'ARCH Milk':<10} | {'V2 Milk':<10}")
print("-" * 105)
for cp in checkpoints:
    at = arch_trace[cp]
    vt = v2_trace[cp]
    am = at["shed"].get("MILK", 0)
    vm = vt["shed"].get("MILK", 0)
    aq = ",".join(at["unlocked_quads"])
    vq = ",".join(vt["unlocked_quads"])
    print(f"{cp:<6} | ${at['money_after']:<11,.0f} | ${vt['money_after']:<11,.0f} | {aq:<12} | {vq:<12} | {at['pastures_built']:<10} | {vt['pastures_built']:<10} | {am:<10} | {vm:<10}")
