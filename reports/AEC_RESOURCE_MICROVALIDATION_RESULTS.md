# AEC Phase 002B: Resource Micro-Validation Empirical Results Report
**Mechanisms Evaluated:** `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE`  
**Evaluation Type:** Deterministic Historical/Development Replay Micro-Validation  
**Strict Status:** Quarantined — Empirical Safety Evaluation (Non-Prospective)  
**Execution Timestamp:** 2026-09-17T23:15:00+05:30  
**Git Commit Target:** `test(aec): micro-validate resource conversion and emergency feed purchase`  

---

## 1. Executive Summary

In accordance with preregistration [`reports/AEC_RESOURCE_MICROVALIDATION_PREREG.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_RESOURCE_MICROVALIDATION_PREREG.md), Phase 002B executed an empirical micro-validation of the `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE` mechanisms across 200 matches (25 development seeds $\times$ 2 seat configurations $\times$ 4 experimental arms = 143,800 turns).

### Key Empirical Findings:

1. **`RESOURCE_CONVERSION` — Safe Fail-Closed, Zero Commits:**
   - Evaluated 101,551 candidate proposals across 50 matches.
   - 40,972 passed safety checks, 60,579 failed safety checks (primarily shed capacity and liquidity bounds).
   - Commits: **0**.
   - **Root Cause:** In [`aec/patches/generator.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/patches/generator.py#L229), candidates generated under `fam == "RESOURCE_CONVERSION"` specify `conversion_metadata` but leave physical mutations (`market_mutations`, `worker_mutations`) empty. Counterfactual simulation evaluates a zero-action patch identically to the baseline trajectory ($0.0$ margin advantage), causing the `WinModel` evaluator to correctly reject with `NO_CANDIDATE_CERTIFIED_SUPERIOR` (33,499 abstentions).
   - **Safety Evaluation:** 100% fail-closed. Zero unauthorized state mutations, zero invariant violations, zero regressions.

2. **`EMERGENCY_FEED_PURCHASE` — Active Commits, Endgame Flaw Detected:**
   - Evaluated 6,187 candidate proposals; 3,524 passed safety checks; committed **12 times** across 6 distinct seeds (50000, 50002, 50004, 50013, 50015, 50018).
   - In mid-game (e.g. Seed 50000 Step 252, Seed 50002 Step 368), purchases mitigated feed deficits safely.
   - **Catastrophic Terminal Blindness:** On Seeds 50004, 50013, 50018 at Step 697 (with only 23 turns remaining before terminal step 720), the feed security monitor flagged a feed deficit and executed an emergency wheat purchase despite active `E8_TERMINAL_TRANSITION`. This spent critical cash right before final liquidation, leading to a substantial margin degradation in Arm C (Mean Terminal Margin dropped from `+$86.92` to `-$313.32`).
   - **Safety Evaluation:** **NOT READY FOR PROSPECTIVE TRIAL.** Fails empirical safety due to terminal-blind intervention causing economic degradation.

---

## 2. Experimental Design & Cohort Selection

### 2.1 Replay Cohort
- **Partition:** Historical/Development Benchmark Partition `50000–50024` ($N = 25$ seeds).
- **Seat Configurations:** Seat 0 and Seat 1 per seed ($25 \times 2 = 50$ matches per arm).
- **Total Turns per Arm:** 36,000 game turns (720 turns/match $\times$ 50 matches).
- **Holdout Isolation:** Seeds `340050–340199` and `214200–214249` were strictly unexecuted (0 accesses).
- **Prior Experiments:** Cohorts `EXP-AEC-001`, `EXP-AEC-002`, `EXP-AEC-003` were strictly untouched.

### 2.2 Mechanism Arms
1. **Arm A (`CONTROL`):** Frozen V3 + AEC Reconnect + Market Timing. Both resource mechanisms quarantined.
2. **Arm B (`RESOURCE_CONVERSION_ONLY`):** Arm A + `RESOURCE_CONVERSION` unquarantined.
3. **Arm C (`EMERGENCY_FEED_ONLY`):** Arm A + `EMERGENCY_FEED_PURCHASE` unquarantined.
4. **Arm D (`COMBINED_RESOURCE`):** Arm A + both resource mechanisms unquarantined.

---

## 3. Comprehensive Empirical Results Table

| Metric | Arm A (`CONTROL`) | Arm B (`RESOURCE_CONVERSION`) | Arm C (`EMERGENCY_FEED`) | Arm D (`COMBINED`) |
| :--- | :---: | :---: | :---: | :---: |
| **Total Matches** | 50 | 50 | 50 | 50 |
| **Total Turns Evaluated** | 36,000 | 36,000 | 36,000 | 36,000 |
| **Mean Terminal Margin ($)** | **+$86.92** | **+$86.92** | **-$313.32** | **-$313.32** |
| **Std Dev Terminal Margin ($)** | 254.15 | 254.15 | 1248.73 | 1248.73 |
| **Median Terminal Margin ($)** | +$17.00 | +$17.00 | +$18.00 | +$18.00 |
| **Total Candidate Patches** | 1,685 | 101,551 | 6,187 | 106,053 |
| **Candidates Passing Safety** | 664 | 40,972 | 3,524 | 43,832 |
| **Candidates Failing Safety** | 1,021 | 60,579 | 2,663 | 62,221 |
| **Total Patches Committed** | **78** | **78** | **90** | **90** |
| - *Market Timing Commits* | 78 | 78 | 78 | 78 |
| - *Resource Conversion Commits* | 0 | **0** | 0 | **0** |
| - *Emergency Feed Commits* | 0 | 0 | **12** | **12** |
| **Mean AEC Latency (ms/step)** | 1.14 ms | 9.19 ms | 1.54 ms | 10.01 ms |
| **p95 AEC Latency (ms/step)** | 3.57 ms | 17.07 ms | 4.73 ms | 19.60 ms |
| **Total Arm Wall-Clock Time** | 68.5 s | 362.0 s | 85.4 s | 393.7 s |

---

## 4. Mechanism-Specific Analyses

### 4.1 `RESOURCE_CONVERSION` Analysis

- **Opportunities Detected:** 35,650 turns had active inventory conversion candidates (milk $\to$ butter/cheese, wheat $\to$ flour/bread, fruit $\to$ jam).
- **Safety Checker Operation:**
  - 60,579 candidates were safely rejected by the Safety Verifier prior to counterfactual evaluation.
  - Rejection drivers: Lack of immediate shed capacity for converted outputs, insufficient cash buffer for processing fees, or downstream inventory commitments.
- **Counterfactual Evaluation & Abstention:**
  - 40,972 candidates satisfied all statutory safety invariants.
  - Of these, 33,499 evaluations resulted in `NO_CANDIDATE_CERTIFIED_SUPERIOR`.
  - **Mechanistic Cause:** The conversion DAG successfully detects opportunities and models recipes, but the patch generation stage does not yet synthesize concrete worker travel routes to processing stations or discrete building interaction actions. Consequently, simulated rollouts produced no physical state delta relative to baseline.
  - **Invariance Conclusion:** The compiler's fail-closed design operated flawlessly: zero speculative or ungrounded patches were committed.

### 4.2 `EMERGENCY_FEED_PURCHASE` Analysis

- **Opportunities Detected:** 6,187 emergency feed candidates generated when inventory was depleted while livestock was present.
- **Commits:** Exactly 12 commits occurred across 6 seeds:
  - Seed 50000 (Seats 0, 1) @ Step 252: Committed `BUY_PRODUCT` wheat. Safe mid-game feed bridge.
  - Seed 50002 (Seats 0, 1) @ Step 368: Committed `BUY_PRODUCT` wheat. Feed deficit resolved.
  - Seed 50004 (Seats 0, 1) @ Step 697: Committed `BUY_PRODUCT` wheat. **Endgame defect.**
  - Seed 50013 (Seats 0, 1) @ Step 697: Committed `BUY_PRODUCT` wheat. **Endgame defect.**
  - Seed 50015 (Seats 0, 1) @ Step 368: Committed `BUY_PRODUCT` wheat. Safe mid-game feed bridge.
  - Seed 50018 (Seats 0, 1) @ Step 697: Committed `BUY_PRODUCT` wheat. **Endgame defect.**
- **The Step 697 Failure Mode:**
  At step 697, the game is 23 turns from completion. The feed security engine evaluated the livestock count, saw zero wheat in inventory, and dispatched an order to buy wheat. However:
  1. The animal feed consumption cycle had already concluded its economically productive phase (no further wool/egg harvests would mature before step 720).
  2. Cash spent on wheat reduced net terminal cash.
  3. Market orders competed with final inventory liquidations.
  4. On Seed 50004, terminal margin dropped from `+$1,280.00` to `-$2,108.00` (a `-$3,388.00` swing).
- **Preregistration Failure Criterion Met:** The preregistered criterion requires feed purchases near terminal to be safely suppressed (Case EF-9). The mechanism failed this criterion under live historical replay.

---

## 5. Decision Abstention Taxonomy

Across all 144,000 turn evaluations across the 4 arms, abstention reasons were logged deterministically:

| Abstention Reason | Arm A | Arm B | Arm C | Arm D | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `NO_EVENT_FAST_PATH` | 550 | 550 | 550 | 550 | Fast-path skip when no compiler events triggered |
| `NO_OPPORTUNITIES_FOUND` | 27,642 | 350 | 23,896 | 50 | No mechanism opportunities detected in state |
| `NO_FEASIBLE_CANDIDATE_PATCHES` | 6,545 | 1,351 | 5,798 | 628 | Candidates eliminated by hard safety constraints |
| `NO_CANDIDATE_CERTIFIED_SUPERIOR` | 1,013 | 33,499 | 5,494 | 34,510 | Candidates simulated but failed win margin threshold |
| `SCIENTIFIC_QUARANTINE` | 122 | 122 | 122 | 122 | Hard-coded quarantine stops on isolated mechanisms |

---

## 6. Computational Performance & Overhead

All performance metrics were recorded per-turn inside the compiled evaluation harness:

- **Arm A (Baseline AEC):** Mean `1.14 ms`, p95 `3.57 ms`. Negligible computational impact.
- **Arm B (Resource Conversion):** Mean `9.19 ms`, p95 `17.07 ms`. Increased due to evaluating multiple multi-step conversion recipes across 101,551 candidates.
- **Arm C (Emergency Feed):** Mean `1.54 ms`, p95 `4.73 ms`. Fast feed security calculation.
- **Arm D (Combined):** Mean `10.01 ms`, p95 `19.60 ms`. Well within the per-turn budget limit of 100 ms.

---

## 7. Descriptive Economic Classification

> [!CAUTION]
> **GOVERNANCE NOTICE:** The economic results above are strictly descriptive micro-validation observations on development seeds `50000–50024`. They DO NOT represent competitive performance claims or leaderboard evidence. No thresholds were tuned, and neither mechanism will be deployed to competition play.
