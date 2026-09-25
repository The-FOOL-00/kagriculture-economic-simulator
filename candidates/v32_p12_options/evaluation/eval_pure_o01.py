# SPDX-License-Identifier: MIT
"""
Evaluates SparseOptionController with ONLY O01 (EXPAND_LAND) active.
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v32_p12_options.option_library import OPTION_LIBRARY, OptionStatus
from candidates.v32_p12_options.evaluation.run_experiment_p12_02 import run_p12_02_leg

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Strictly isolate O01
    for opt_id, opt in OPTION_LIBRARY.items():
        if opt_id != "O01":
            opt.promotion_status = OptionStatus.QUARANTINED

    seeds = [249635, 249636, 249637, 249675, 249676]
    opponents = ["E2_A7", "E8_DMITRII"]
    tasks = [
        {"seed": s, "opponent_id": o, "seat": seat}
        for s in seeds for o in opponents for seat in [0, 1]
    ]

    print(f"Evaluating pure O01 (EXPAND_LAND) across {len(tasks)} legs on 10 workers...")
    t0 = time.time()

    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        future_map = {pool.submit(run_p12_02_leg, t): t for t in tasks}
        completed = 0
        for fut in as_completed(future_map):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(tasks)}] Seed {res['seed']} Opp {res['opponent'][:6]} Seat {res['seat']} -> "
                  f"A7: ${res['a7_cash']:7.1f} | Cand: ${res['cand_cash']:7.1f} | "
                  f"Delta: {res['paired_delta']:+8.1f} | Acts: {res['options_activated']}",
                  flush=True)

    elapsed = time.time() - t0
    print(f"\nEvaluation finished in {elapsed:.2f}s!")

    deltas = [r["paired_delta"] for r in results]
    print(f"\nPURE O01 (EXPAND_LAND) SUMMARY ({len(results)} legs):")
    print(f"  Mean Paired Delta:   {np.mean(deltas):+8.2f}")
    print(f"  Median Paired Delta: {np.median(deltas):+8.2f}")
    print(f"  Min Paired Delta:    {np.min(deltas):+8.2f}")
    print(f"  Max Paired Delta:    {np.max(deltas):+8.2f}")
    print(f"  Positive Legs:       {sum(1 for d in deltas if d > 0)} / {len(deltas)} ({sum(1 for d in deltas if d > 0)/len(deltas)*100:.1f}%)")
    print(f"  Zero Delta (A7 abstention): {sum(1 for d in deltas if d == 0)} / {len(deltas)}")
    print(f"  Negative Legs:       {sum(1 for d in deltas if d < 0)} / {len(deltas)}")

    out_path = "candidates/v32_p12_options/reports/p12_pure_o01_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
