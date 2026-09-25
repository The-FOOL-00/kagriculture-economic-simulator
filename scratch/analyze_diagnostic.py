import json
import os
import sys
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
with open(os.path.join(REPO_ROOT, "results", "v32_p5_rollout_diagnostic.json")) as f:
    episodes = json.load(f)

print("=== STEP INTERVAL ANALYSIS ===")
intervals = [
    (0, 0, "Step 0"),
    (1, 10, "Steps 1-10"),
    (11, 24, "Steps 11-24"),
    (25, 48, "Steps 25-48"),
    (49, 72, "Steps 49-72"),
    (73, 144, "Steps 73-144"),
    (145, 288, "Steps 145-288"),
    (289, 480, "Steps 289-480"),
    (481, 719, "Steps 481-719"),
]

for start, end, label in intervals:
    act_matches = []
    f_dists = []
    money_diffs = []
    pos_diffs = []
    for ep in episodes:
        for m in ep["step_metrics"]:
            if start <= m["step"] <= end:
                act_matches.append(1.0 if m["act_match"] else 0.0)
                f_dists.append(m["f_dist"])
                money_diffs.append(m["money_diff"])
                pos_diffs.append(m["pos_diff"])
    mean_match = np.mean(act_matches) * 100
    mean_f_dist = np.mean(f_dists)
    mean_money_diff = np.mean(money_diffs)
    mean_pos_diff = np.mean(pos_diffs)
    print(f"{label:<15} | Act Match: {mean_match:5.1f}% | Feature Dist: {mean_f_dist:6.2f} | Money Diff: ${mean_money_diff:8.1f} | Pos Diff: {mean_pos_diff:4.1f}")

print("\n=== DETAILED EARLY-HORIZON ANALYSIS (STEPS 0 to 24) ===")
print(f"{'Step':<5} | {'Teacher Farmer':<15} | {'Policy Farmer':<15} | {'Teacher Mkt':<25} | {'Policy Mkt':<25} | {'Feat Dist':<10} | {'Money Delta'}")
print("-" * 120)

ep0 = episodes[0]
for t in range(25):
    m = ep0["step_metrics"][t]
    tf = str(m["t_act"].get("farmer", []))
    pf = str(m["p_act"].get("farmer", []))
    tm = str(m["t_act"].get("market", [])[:2])
    pm = str(m["p_act"].get("market", [])[:2])
    fd = f"{m['f_dist']:.3f}"
    md = f"${m['money_diff']:.1f}"
    print(f"{t:<5} | {tf:<15} | {pf:<15} | {tm:<25} | {pm:<25} | {fd:<10} | {md}")
