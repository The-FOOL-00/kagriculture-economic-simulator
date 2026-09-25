# SPDX-License-Identifier: MIT
"""Background script for expert dataset generation."""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR, SAFE_TRAIN_SEEDS
from candidates.v38_heuristic_ppo.dataset import generate_expert_dataset

def main():
    t0 = time.time()
    out_file = os.path.join(SCRATCH_DIR, "expert_counterfactual_dataset.json")
    done_file = os.path.join(SCRATCH_DIR, "dataset_gen.done")
    
    seeds = SAFE_TRAIN_SEEDS[:4]  # 249635..249638
    opponents = ["E2_A7", "E8_DMITRII"]
    steps = [48, 72, 144, 216, 288, 360, 480, 576]
    
    print(f"Starting Dataset Generation: seeds={seeds}, opps={opponents}, steps={steps}")
    res = generate_expert_dataset(
        seeds=seeds,
        opponents=opponents,
        steps=steps,
        horizon=4,
        output_path=out_file,
        min_advantage_threshold=50.0,
        num_workers=4
    )
    dt = time.time() - t0
    with open(done_file, "w") as f:
        f.write(f"DONE in {dt:.1f}s. Records: {res['metadata']['num_records']}\n")
    print(f"Completed in {dt:.1f}s. Marker written to {done_file}.")

if __name__ == "__main__":
    main()
