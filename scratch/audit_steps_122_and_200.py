import json

with open("scratch/telemetry_arch_base_seed215.json", "r") as f:
    arch_trace = json.load(f)

print("="*80)
print("INSPECTING STEPS 120..126 IN ARCH_BASE")
print("="*80)
for s in range(120, 127):
    st = arch_trace[s]
    print(f"Step {s}: Money Before=${st['money_before']}, Money After=${st['money_after']}, Quads={st['unlocked_quads']}")
    print(f"  Action Market: {st['action'].get('market')}")
    print(f"  Farmer Action: {st['action'].get('farmer')}")

print("\n" + "="*80)
print("INSPECTING STEPS 196..205 IN ARCH_BASE")
print("="*80)
for s in range(196, 206):
    st = arch_trace[s]
    print(f"Step {s}: Money Before=${st['money_before']}, Money After=${st['money_after']}, Quads={st['unlocked_quads']}")
    print(f"  Action Market: {st['action'].get('market')}")
    print(f"  Farmer Action: {st['action'].get('farmer')}")
