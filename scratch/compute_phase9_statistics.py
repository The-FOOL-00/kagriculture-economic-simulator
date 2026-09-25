# SPDX-License-Identifier: MIT
"""Compute exact statistical figures for Phase 9."""

import json
from collections import Counter
import numpy as np
from scipy import stats

with open("benchmark_results.json", "r") as f:
    data = json.load(f)

legs = data["raw_legs"]
a7_map = {(l["seed"], l["opponent"], l["seat"]): l for l in legs if l["policy"] == "A7_BASELINE"}
v35_map = {(l["seed"], l["opponent"], l["seat"]): l for l in legs if l["policy"] == "V35_FULL"}

keys = sorted(a7_map.keys())
n = len(keys)

# Binary Decisive Win Definition: Win = 1.0 (cand > opp), Non-Win = 0.0 or 0.5 (cand <= opp)
a7_decisive_win = np.array([1 if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] else 0 for k in keys])
v35_decisive_win = np.array([1 if v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"] else 0 for k in keys])

# Tournament Points Definition: Win = 1.0, Tie = 0.5, Loss = 0.0
a7_tourney_pts = np.array([a7_map[k]["win"] for k in keys])
v35_tourney_pts = np.array([v35_map[k]["win"] for k in keys])

# Cash deltas
cash_deltas = np.array([v35_map[k]["cand_cash"] - a7_map[k]["cand_cash"] for k in keys])

# Paired Differences
diff_decisive = v35_decisive_win - a7_decisive_win
diff_tourney = v35_tourney_pts - a7_tourney_pts

# Discordant Pair Table (Decisive Win)
# cell [0,0]: A7 non-win, V35 non-win
# cell [0,1]: A7 non-win, V35 win (c)
# cell [1,0]: A7 win, V35 non-win (b)
# cell [1,1]: A7 win, V35 win
n_00 = sum((a7_decisive_win == 0) & (v35_decisive_win == 0))
n_01 = sum((a7_decisive_win == 0) & (v35_decisive_win == 1)) # rescues
n_10 = sum((a7_decisive_win == 1) & (v35_decisive_win == 0)) # casualties
n_11 = sum((a7_decisive_win == 1) & (v35_decisive_win == 1))

# McNemar Exact Test (Binomial distribution on discordant pairs)
b = n_10
c = n_01
n_discordant = b + c
if n_discordant > 0:
    mcnemar_exact_p = float(2 * stats.binom.cdf(min(b, c), n_discordant, 0.5))
    mcnemar_chi2 = float((abs(b - c) - 1)**2 / n_discordant)
    mcnemar_asymptotic_p = float(1 - stats.chi2.cdf(mcnemar_chi2, df=1))
else:
    mcnemar_exact_p = 1.0
    mcnemar_chi2 = 0.0
    mcnemar_asymptotic_p = 1.0

# Paired Bootstrap (10,000 resamples)
rng = np.random.default_rng(42)
B = 10000

boot_tourney_diffs = []
boot_decisive_diffs = []
boot_cash_diffs = []

for _ in range(B):
    idx = rng.integers(0, n, size=n)
    boot_tourney_diffs.append(np.mean(diff_tourney[idx]))
    boot_decisive_diffs.append(np.mean(diff_decisive[idx]))
    boot_cash_diffs.append(np.mean(cash_deltas[idx]))

results = {
    "sample_size": n,
    "bootstrap_resamples": B,
    "tourney_points_delta": {
        "mean": float(np.mean(diff_tourney)),
        "ci_95_lower": float(np.percentile(boot_tourney_diffs, 2.5)),
        "ci_95_upper": float(np.percentile(boot_tourney_diffs, 97.5)),
    },
    "decisive_win_delta": {
        "mean": float(np.mean(diff_decisive)),
        "ci_95_lower": float(np.percentile(boot_decisive_diffs, 2.5)),
        "ci_95_upper": float(np.percentile(boot_decisive_diffs, 97.5)),
    },
    "paired_cash_delta": {
        "mean": float(np.mean(cash_deltas)),
        "median": float(np.median(cash_deltas)),
        "ci_95_lower": float(np.percentile(boot_cash_diffs, 2.5)),
        "ci_95_upper": float(np.percentile(boot_cash_diffs, 97.5)),
    },
    "contingency_table": {
        "A7_win_V35_win": int(n_11),
        "A7_win_V35_non_win": int(n_10),
        "A7_non_win_V35_win": int(n_01),
        "A7_non_win_V35_non_win": int(n_00),
    },
    "mcnemar": {
        "b_casualties": int(b),
        "c_rescues": int(c),
        "chi2_continuity_corrected": mcnemar_chi2,
        "asymptotic_p_value": mcnemar_asymptotic_p,
        "exact_binomial_p_value": mcnemar_exact_p,
    }
}

with open("scratch/phase9_stats_output.json", "w") as f:
    json.dump(results, f, indent=2)

print("Phase 9 Statistics Computed Successfully:")
print(f"Tournament Win Rate Delta: {results['tourney_points_delta']['mean']*100:+.2f}% [95% CI: {results['tourney_points_delta']['ci_95_lower']*100:+.2f}%, {results['tourney_points_delta']['ci_95_upper']*100:+.2f}%]")
print(f"Decisive Win Rate Delta: {results['decisive_win_delta']['mean']*100:+.2f}% [95% CI: {results['decisive_win_delta']['ci_95_lower']*100:+.2f}%, {results['decisive_win_delta']['ci_95_upper']*100:+.2f}%]")
print(f"Discordant Pairs: b (casualties) = {b}, c (rescues) = {c}")
print(f"McNemar Exact Binomial p-value: {mcnemar_exact_p:.6e}")
