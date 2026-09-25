import json

with open("candidates/v32_hmeh/reports/ablation_results.json") as f:
    data = json.load(f)

a7_dict = {(r["seed"], r["seat"]): r["cash"] for r in data["A7"]}

stages = ["A7", "HMEH-0", "HMEH-1", "HMEH-2", "HMEH-3", "HMEH-4"]
stage_dicts = {st: {(r["seed"], r["seat"]): r["cash"] for r in data[st]} for st in stages}

print("=" * 95)
print("PAIRED DELTA MATRIX ACROSS ALL 10 DEV SEEDS (249675-249684) x 2 SEATS (20 LEGS)")
print("=" * 95)

for st in stages:
    diffs = []
    cashes = []
    wins = []
    res_list = data[st]
    w_count = sum(1 for r in res_list if r["win"] == 1.0)
    for key in sorted(a7_dict.keys()):
        c = stage_dicts[st][key]
        cashes.append(c)
        diffs.append(c - a7_dict[key])
    import numpy as np
    cashes = np.array(cashes)
    diffs = np.array(diffs)
    print(f"{st:<8} | Mean: ${np.mean(cashes):>10,.2f} | Med: ${np.median(cashes):>10,.2f} | P25: ${np.percentile(cashes, 25):>10,.2f} | P75: ${np.percentile(cashes, 75):>10,.2f} | Paired vs A7: ${np.mean(diffs):>+9,.2f} | W/L: {w_count:>2}/20")

print("\nPer-Seed Breakdown for HMEH-0 vs A7:")
print(f"{'Seed':<8} {'Seat':<5} {'A7 Cash':>12} {'HMEH-0 Cash':>12} {'Paired Delta':>14}")
print("-" * 55)
for key in sorted(a7_dict.keys()):
    a7_c = a7_dict[key]
    h0_c = stage_dicts["HMEH-0"][key]
    print(f"{key[0]:<8} {key[1]:<5} ${a7_c:>11,.2f} ${h0_c:>11,.2f} ${h0_c - a7_c:>+13,.2f}")
