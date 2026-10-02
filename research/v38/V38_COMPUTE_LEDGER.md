# V38 Compute Ledger

| Job ID | Timestamp (UTC) | Command / Task | Worker Cores / Hardware | Duration (s) | Status | Output Artifact | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| INIT | 2026-09-25 05:25 | V38 Initialization & Audit | Local CPU (AMD64) | — | COMPLETED | Workspace & Ledger | Safe seeds configured |
| TASK-129 | 2026-09-25 05:27 | Expert Dataset Generation (`run_dataset_gen.py`) | 4 CPU Workers | 1330s | COMPLETED | `scratch/v38/expert_counterfactual_dataset.json` | 128 decision states |
| TASK-BC | 2026-09-25 05:50 | Behavioral Cloning Training (`run_bc_training.py`) | Local CPU (PyTorch) | 5s | COMPLETED | `scratch/v38/bc_policy.pt` | Val Acc: 87.5%, Heuristic Agr: 100% |
| TASK-341 | 2026-09-25 05:52 | Bounded Residual PPO Training (`run_ppo_training.py`) | Local CPU (PyTorch) | 230s | COMPLETED | `scratch/v38/ppo_policy.pt` | 10 iterations, Val Loss: 1.64 -> 0.09 |
| TASK-392 | 2026-09-25 05:58 | Adversarial Stress Suite (`run_adversarial.py`) | Local CPU (AMD64) | 430s | COMPLETED | `scratch/v38/adversarial_results.json` | 72 matches vs SYN_AGG, DMITRII, A7 |
| TASK-466 | 2026-09-25 06:06 | Benchmark Tournaments (`run_tournaments.py`) | 4 CPU Workers | 602s | COMPLETED | `scratch/v38/tournament_*_results.json` | 264 matches (Dev 120, Fresh 120, Ablation 24) |
| TASK-CLEAN | 2026-09-25 06:19 | Cleanroom Kaggle Environments Execution | Local CPU | 5s | COMPLETED | `scratch/v38/test_cleanroom.py` | Verified zero-dependency execution in env.run |
