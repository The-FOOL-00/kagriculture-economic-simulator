import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps")
print("=== DAY 0 SETUP (Steps 0-24) for Yuyajk (P1) vs V2 (P0) ===")
for s in range(25):
    act0 = steps[s][0].get("action", {})
    act1 = steps[s][1].get("action", {})
    # Check buys and farm actions
    m0 = act0.get("market", [])
    m1 = act1.get("market", [])
    if m0 or m1 or s in [0, 1, 2, 3]:
        print(f"Step {s:2d} | P0(V2): {act0.get('farmer')} | market: {m0}")
        print(f"        | P1(Yuyajk): {act1.get('farmer')} | market: {m1}")

print("\n=== CROP SEEDS BOUGHT (Steps 0-120) ===")
p0_seeds = {}
p1_seeds = {}
for s in range(120):
    for p_idx, s_dict in [(0, p0_seeds), (1, p1_seeds)]:
        act = steps[s][p_idx].get("action", {})
        for m in act.get("market", []):
            if len(m) > 1 and "SEED" in str(m[1]):
                s_dict[m[1]] = s_dict.get(m[1], 0) + (m[2] if len(m) > 2 else 1)

print("P0 (V2) Seeds bought Days 0-5:", p0_seeds)
print("P1 (Yuyajk) Seeds bought Days 0-5:", p1_seeds)
