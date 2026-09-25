# SPDX-License-Identifier: MIT
"""Background script to run Behavioral Cloning training."""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR
from candidates.v38_heuristic_ppo.train_bc import train_behavioral_cloning, BC_CHECKPOINT_PATH, BC_METRICS_PATH

def main():
    t0 = time.time()
    done_file = os.path.join(SCRATCH_DIR, "bc_training.done")
    dataset_file = os.path.join(SCRATCH_DIR, "expert_counterfactual_dataset.json")
    
    print("Starting Behavioral Cloning training...")
    res = train_behavioral_cloning(
        dataset_path=dataset_file,
        checkpoint_out=BC_CHECKPOINT_PATH,
        metrics_out=BC_METRICS_PATH,
        epochs=60,
        lr=1e-3,
        batch_size=16
    )
    dt = time.time() - t0
    with open(done_file, "w") as f:
        f.write(f"DONE in {dt:.1f}s. Best Val Acc: {res['best_val_acc']*100:.2f}%\n")
    print(f"BC Training complete in {dt:.1f}s. Marker written to {done_file}.")

if __name__ == "__main__":
    main()
