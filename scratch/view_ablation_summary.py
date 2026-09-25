import json
import numpy as np

with open("candidates/v32_hmeh/reports/ablation_results.json") as f:
    data = json.load(f)

a7_cash = np.array([r["cash"] for r in data["A7"]])

print(f"{'Policy':<10} | {'Mean Cash':<12} | {'Median Cash':<12} | {'P25 Cash':<12} | {'P75 Cash':<12} | {'Mean Delta':<12} | {'Win Rate':<10} | {'Paired vs A7':<12}")
print("-" * 105)

for pol in ["A7", "HMEH-0", "HMEH-1", "HMEH-2", "HMEH-3", "HMEH-4"]:
    res = data[pol]
    cash = np.array([r["cash"] for r in res])
    delta = np.array([r["delta"] for r in res])
    wins = np.array([r["win"] for r in res])
    paired_vs_a7 = np.mean(cash - a7_cash)
    print(f"{pol:<10} | ${np.mean(cash):>10,.2f} | ${np.median(cash):>10,.2f} | ${np.percentile(cash, 25):>10,.2f} | ${np.percentile(cash, 75):>10,.2f} | ${np.mean(delta):>+10,.2f} | {np.mean(wins)*100:>8.1f}% | ${paired_vs_a7:>+10,.2f}")
