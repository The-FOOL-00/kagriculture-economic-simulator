import json
import csv
import numpy as np

# 1. Load RAW_RESULTS.json
with open("experiments/EXP-AEC-001/RAW_RESULTS.json", "r") as f:
    raw_results = json.load(f)

print(f"Loaded {len(raw_results)} seeds from RAW_RESULTS.json")

# Inspect seeds
reconstructed_data = []
for seed_str in sorted(raw_results.keys(), key=lambda x: int(x)):
    seed_data = raw_results[seed_str]
    seed = int(seed_str)
    m_a = seed_data["match_a"]
    m_b = seed_data["match_b"]
    
    aec_a = m_a["aec_score"]
    ctrl_a = m_a["ctrl_score"]
    margin_a = aec_a - ctrl_a
    winner_a = "AEC" if margin_a > 0 else ("V3" if margin_a < 0 else "TIE")
    
    aec_b = m_b["aec_score"]
    ctrl_b = m_b["ctrl_score"]
    margin_b = aec_b - ctrl_b
    winner_b = "AEC" if margin_b > 0 else ("V3" if margin_b < 0 else "TIE")
    
    delta_paired = 0.5 * (margin_a + margin_b)
    mean_treat = 0.5 * (aec_a + aec_b)
    mean_ctrl = 0.5 * (ctrl_a + ctrl_b)
    
    commits_a = sum(m_a.get("commits_by_mechanism", {}).values())
    commits_b = sum(m_b.get("commits_by_mechanism", {}).values())
    total_commits = commits_a + commits_b
    
    reconstructed_data.append({
        "seed": seed,
        "aec_score_a": aec_a,
        "ctrl_score_a": ctrl_a,
        "margin_a": margin_a,
        "winner_a": winner_a,
        "aec_score_b": aec_b,
        "ctrl_score_b": ctrl_b,
        "margin_b": margin_b,
        "winner_b": winner_b,
        "delta_paired": delta_paired,
        "mean_treat": mean_treat,
        "mean_ctrl": mean_ctrl,
        "commits_a": commits_a,
        "commits_b": commits_b,
        "total_commits": total_commits
    })

# Check asymmetry / non-zero margins
non_zero = [r for r in reconstructed_data if r["margin_a"] != 0 or r["margin_b"] != 0 or r["delta_paired"] != 0]
print(f"Number of seeds with non-zero margin in match A or B: {len(non_zero)}")
for r in non_zero:
    print(f"Seed {r['seed']}:")
    print(f"  Match A: AEC={r['aec_score_a']}, V3={r['ctrl_score_a']}, margin={r['margin_a']}, winner={r['winner_a']}")
    print(f"  Match B: AEC={r['aec_score_b']}, V3={r['ctrl_score_b']}, margin={r['margin_b']}, winner={r['winner_b']}")
    print(f"  Paired Delta: {r['delta_paired']}, Commits: A={r['commits_a']}, B={r['commits_b']}")
