# SPDX-License-Identifier: MIT
"""Background script to run PPO fine-tuning."""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR, SAFE_TRAIN_SEEDS
from candidates.v38_heuristic_ppo.train_ppo import train_ppo, PPO_CHECKPOINT_PATH, PPO_METRICS_PATH

def main():
    t0 = time.time()
    bc_checkpoint = os.path.join(SCRATCH_DIR, "bc_policy.pt")
    done_file = os.path.join(SCRATCH_DIR, "ppo_training.done")
    
    print("Starting PPO residual fine-tuning initialized from BC...")
    res = train_ppo(
        bc_init_path=bc_checkpoint,
        output_checkpoint=PPO_CHECKPOINT_PATH,
        output_metrics=PPO_METRICS_PATH,
        total_iterations=10,
        episodes_per_iter=4,
        lr=2e-4,
        clip_eps=0.2,
        entropy_coef=0.01,
        value_coef=0.5,
        seeds=SAFE_TRAIN_SEEDS[:4],
        opponents=["E2_A7", "E8_DMITRII"],
        use_safety_fallback=True
    )
    dt = time.time() - t0
    with open(done_file, "w") as f:
        f.write(f"DONE in {dt:.1f}s. Final WR: {res['final_win_rate']:.1f}% | Cash: ${res['final_cash']:.1f}\n")
    print(f"PPO training complete in {dt:.1f}s. Marker written to {done_file}.")

if __name__ == "__main__":
    main()
