import json
import numpy as np

with open("scratch/jit_melon_results/dev_tournament_results.json", "r") as f:
    dev_data = json.load(f)

with open("scratch/jit_melon_results/holdout_results.json", "r") as f:
    hold_data = json.load(f)

all_h = [r for r in dev_data + hold_data if r["treatment"] == "H"]
print(f"Total H games analyzed for price robustness: {len(all_h)}")

# Stratify by melon_price_264
prices = [r["melon_price_264"] for r in all_h]
p_low = np.percentile(prices, 33.3)
p_high = np.percentile(prices, 66.7)

print(f"Melon price thresholds: Low <= ${p_low:.1f}, Normal: ${p_low:.1f}-${p_high:.1f}, High > ${p_high:.1f}")

regimes = {
    "Low Melon Price": [r for r in all_h if r["melon_price_264"] <= p_low],
    "Normal Melon Price": [r for r in all_h if p_low < r["melon_price_264"] <= p_high],
    "High Melon Price": [r for r in all_h if r["melon_price_264"] > p_high]
}

print("\n=== PERFORMANCE STRATIFIED BY MELON PRICE REGIME ===")
print("Regime              | N   | Mean Price | Cand Score | Opp Score  | Margin     | Win Rate")
print("-" * 85)
for name, games in regimes.items():
    if not games: continue
    mean_p = np.mean([g["melon_price_264"] for g in games])
    cand_s = np.mean([g["reward_us"] for g in games])
    opp_s = np.mean([g["reward_opp"] for g in games])
    margin = np.mean([g["margin"] for g in games])
    wr = np.mean([g["win"] for g in games]) * 100.0
    print(f"{name:19s} | {len(games):3d} | ${mean_p:8.1f}  | ${cand_s:8.1f} | ${opp_s:8.1f} | ${margin:+9.1f} | {wr:5.1f}%")

# Stratify by feed price at Step 264
feed_prices = [r["wheat_price_264"] for r in all_h]
fp_low = np.percentile(feed_prices, 33.3)
fp_high = np.percentile(feed_prices, 66.7)
feed_regimes = {
    "Low Feed Price": [r for r in all_h if r["wheat_price_264"] <= fp_low],
    "Normal Feed Price": [r for r in all_h if fp_low < r["wheat_price_264"] <= fp_high],
    "High Feed Price": [r for r in all_h if r["wheat_price_264"] > fp_high]
}
print("\n=== PERFORMANCE STRATIFIED BY FEED PRICE REGIME ===")
print("Regime              | N   | Mean Price | Cand Score | Opp Score  | Margin     | Win Rate")
print("-" * 85)
for name, games in feed_regimes.items():
    if not games: continue
    mean_p = np.mean([g["wheat_price_264"] for g in games])
    cand_s = np.mean([g["reward_us"] for g in games])
    opp_s = np.mean([g["reward_opp"] for g in games])
    margin = np.mean([g["margin"] for g in games])
    wr = np.mean([g["win"] for g in games]) * 100.0
    print(f"{name:19s} | {len(games):3d} | ${mean_p:8.1f}  | ${cand_s:8.1f} | ${opp_s:8.1f} | ${margin:+9.1f} | {wr:5.1f}%")
