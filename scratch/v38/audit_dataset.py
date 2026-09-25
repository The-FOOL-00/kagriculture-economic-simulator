# SPDX-License-Identifier: MIT
"""Script to audit expert dataset quality, class balance, and seed splits."""

import json
import os
import sys
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR, MACRO_ACTIONS
from candidates.v38_heuristic_ppo.dataset import DATASET_FILE

def audit():
    if not os.path.exists(DATASET_FILE):
        print(f"Dataset {DATASET_FILE} not found!")
        return
        
    with open(DATASET_FILE, "r") as f:
        data = json.load(f)
        
    records = data["records"]
    n = len(records)
    print(f"Auditing {n} records...")
    
    # 1. Seed distribution
    seeds = {}
    for r in records:
        s = r["seed"]
        seeds[s] = seeds.get(s, 0) + 1
        
    # 2. Opponent distribution
    opps = {}
    for r in records:
        o = r["opponent"]
        opps[o] = opps.get(o, 0) + 1
        
    # 3. Macro option target distribution
    options = {}
    for r in records:
        opt = r["best_option"]
        options[opt] = options.get(opt, 0) + 1
        
    # 4. Raw best option distribution (before advantage threshold filtering)
    raw_options = {}
    for r in records:
        ropt = r["raw_best_option"]
        raw_options[ropt] = raw_options.get(ropt, 0) + 1
        
    # 5. Advantage distribution
    deltas = [r["best_delta"] for r in records]
    pos_deltas = [d for d in deltas if d > 0]
    large_deltas = [d for d in deltas if d >= 50.0]
    
    # 6. Duplicate states check (L2 distance < 1e-4)
    state_vecs = np.array([r["state_vector"] for r in records])
    duplicates = 0
    for i in range(min(50, n)):
        for j in range(i + 1, min(50, n)):
            if np.linalg.norm(state_vecs[i] - state_vecs[j]) < 1e-4:
                duplicates += 1
                
    audit_report = {
        "total_records": n,
        "seed_counts": seeds,
        "opponent_counts": opps,
        "supervised_target_distribution": {
            f"{k} ({MACRO_ACTIONS.get(k, 'UNKNOWN')})": v for k, v in sorted(options.items())
        },
        "raw_best_distribution": {
            f"{k} ({MACRO_ACTIONS.get(k, 'UNKNOWN')})": v for k, v in sorted(raw_options.items())
        },
        "positive_advantage_count": len(pos_deltas),
        "positive_advantage_pct": len(pos_deltas) / max(1, n) * 100.0,
        "large_advantage_count": len(large_deltas),
        "mean_best_delta": float(np.mean(deltas)),
        "max_best_delta": float(np.max(deltas)),
        "min_best_delta": float(np.min(deltas)),
        "duplicate_pairs_in_sample": duplicates
    }
    
    report_file = os.path.join(SCRATCH_DIR, "dataset_audit_report.json")
    with open(report_file, "w") as f:
        json.dump(audit_report, f, indent=2)
        
    print("Dataset Audit Summary:")
    print(json.dumps(audit_report, indent=2))
    return audit_report

if __name__ == "__main__":
    audit()
