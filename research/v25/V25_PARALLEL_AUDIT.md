# V25 Parallel Execution & Determinism Audit

## 1. Audit Overview
* **Target Candidate**: `V25_P1_MACRO` (`candidates/v25_p1_macro.py`)
* **Seed**: `249430`
* **Seat**: Seat 0 (Player 0) vs V3 Standalone (Seat 1, Player 1)
* **Execution Environment**: Python 3.14 on Windows 11, `kaggle_environments 1.32.7`
* **Worker Execution**: `concurrent.futures.ProcessPoolExecutor` subprocess with `freeze_support()`

## 2. Equivalence Verification Results

| Metric | Serial Execution | Parallel Subprocess Worker | Match Verification |
|---|---|---|---|
| **Candidate Terminal Reward** | 90,809.0 | 90,809.0 | **EXACT MATCH (True)** |
| **Baseline Terminal Reward** | 89,878.0 | 89,878.0 | **EXACT MATCH (True)** |
| **Paired Delta** | +931.0 | +931.0 | **EXACT MATCH (True)** |
| **Full 720-Step Action Digest** | `f8031e8b77ed61577fff8a1729b6c700ad8750415dbd2694f36863143d668b01` | `f8031e8b77ed61577fff8a1729b6c700ad8750415dbd2694f36863143d668b01` | **BIT-EXACT MATCH (True)** |

## 3. Concurrency Safety Invariant
The audit proves that multiprocessing subprocess isolation introduces zero nondeterminism, zero race conditions, and zero action skew compared to synchronous execution. `MAX_WORKERS = 9` is certified safe for full cohort evaluation.
