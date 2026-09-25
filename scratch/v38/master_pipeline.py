# SPDX-License-Identifier: MIT
"""Master autonomous pipeline runner for V38 execution."""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR
from scratch.v38.audit_dataset import audit
from scratch.v38.run_bc_training import main as run_bc
from scratch.v38.run_ppo_training import main as run_ppo
from scratch.v38.run_causal_analysis import run_causal_forensics
from scratch.v38.run_adversarial import run_adversarial_suite
from scratch.v38.run_tournaments import main as run_tournaments

def main():
    t_start = time.time()
    print("==================================================================")
    print("             V38 AUTONOMOUS RESEARCH PIPELINE                     ")
    print("==================================================================")
    
    # 1. Dataset Audit
    print("\n--- PHASE 9: DATASET AUDIT ---")
    audit()
    
    # 2. Behavioral Cloning Training
    print("\n--- PHASE 10: BEHAVIORAL CLONING WARM-START ---")
    run_bc()
    
    # 3. PPO Residual Training
    print("\n--- PHASE 11: PPO RESIDUAL FINE-TUNING ---")
    run_ppo()
    
    # 4. Intervention Forensics & Causal Validation
    print("\n--- PHASE 13 & 14: CAUSAL & INTERVENTION FORENSICS ---")
    run_causal_forensics()
    
    # 5. Adversarial Stress Suite
    print("\n--- PHASE 17: ADVERSARIAL STRESS SUITE ---")
    run_adversarial_suite()
    
    # 6. Benchmark Tournaments (Dev, Fresh, Ablation)
    print("\n--- PHASE 12, 19, 21, 22: BENCHMARK TOURNAMENTS ---")
    run_tournaments()
    
    elapsed = time.time() - t_start
    done_file = os.path.join(SCRATCH_DIR, "pipeline_complete.done")
    with open(done_file, "w") as f:
        f.write(f"V38 PIPELINE COMPLETE in {elapsed:.1f}s\n")
    print(f"\nALL PHASES COMPLETED SUCCESSFULLY in {elapsed:.1f}s. Marker written to {done_file}.")

if __name__ == "__main__":
    main()
