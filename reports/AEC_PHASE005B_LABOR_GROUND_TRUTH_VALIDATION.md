# SPDX-License-Identifier: MIT
# AEC Phase 005B: Labor Opportunity Engine Ground-Truth & Harvest Discovery
## Empirical Ground-Truth Validation & Counterfactual Audit Report

**Phase**: AEC Phase 005B  
**Component**: `LaborOpportunityCostEngine` (`aec/resource/labor_engine.py`)  
**Evaluation Scope**: Development Seeds `50000–50024`  
**Dataset Artifacts**:  
- `results/PHASE005_LABOR_GROUND_TRUTH.csv` (100 exact counterfactual records)  
- `results/PHASE005_LABOR_GROUND_TRUTH_SUMMARY.json`  
- `results/PHASE005_HARVEST_CANDIDATES.csv` (89,590 genuine harvest candidates)  
**Date**: September 2026  
**Status**: EMPIRICALLY AUDITED  

---

### 1. Executive Summary

Phase 005B executed an exhaustive, forensic ground-truth audit of the generic **Labor Opportunity-Cost Engine** against exact terminal game outcomes produced by the official C++ simulator (`kagsim`).

Key Findings:
1. **Independent Reconciliation of Phase 005 Claims**: The 888 historical diagnostic records were independently reproduced. Crucially, the 440 "approved" records in Phase 005 were **all Resource Conversion (`FEED`) records**, NOT harvest opportunities. Zero harvest records were evaluated or approved in Phase 005.
2. **Mathematical & Accounting Corrections**: Two major defects in the labor engine were identified and corrected:
   - *Biological Asset Double-Counting*: Unharvested mature crops on tiles were previously valued at 100% of product price, causing harvest actions to have $\Delta_{\text{assets}} = 0$ and hallucinating phantom opportunity cost.
   - *Transit Misclassification*: Worker movement (`MOVES`) was previously classified as idle (`is_idle_baseline = True`), bypassing simulation and returning $0.00 opportunity cost for active worker transit.
3. **Exact Simulator vs Labor Engine Comparison (100 Full-Game Counterfactuals)**:
   - **Overall Sign Agreement**: **47.0%** (47/100).
   - **Zero-Delta Invariance**: **100.0%** (25/25) agreement on neutral idle states.
   - **Terminal Harvest**: **64.0%** (16/25) sign agreement in late-game harvest execution.
   - **Compound Trajectory Desynchronization**: In full 720-step matches, isolated 1-turn worker diversions often disrupt the agent's long-term scheduling (e.g. unhandled backpack cargo), leading to negative terminal deltas (mean -$7,452.32) even when the immediate local action creates gross crop value (+$60.00).
4. **Dedicated Ground-Truth Test Battery**: All 12 mandatory scenarios (**GT-01 through GT-12**) pass deterministically. Full repository regression: **396/396 tests green** in 2.08s.

---

### 2. Independent Reproduction of Phase 005 Claims

The 888 evaluation records from `results/PHASE005_LABOR_DIAGNOSTIC.csv` were audited against raw historical patch records (`results/PHASE004B_PATCHES.csv`):

| Mechanism / Arm | Total Records | Assigned Workers in 004B | worker_id in CSV | Baseline PASS | Baseline Active | Approved | Rejected |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `RESOURCE_CONVERSION` | 576 | `[1]` (572), `[11]` (4) | 1 (576) | 548 | 28 | **440** | 136 |
| `DEPENDENCY_AWARE_MARKET_TIMING` | 304 | `[]` (304) | 0 (304)* | 128 | 176 | 0 | 304 |
| `EMERGENCY_FEED_PURCHASE` | 8 | `[1, 1]` (8) | 1 (8) | 8 | 0 | 0 | 8 |
| **Total** | **888** | — | — | **684** | **204** | **440** | **448** |

*\*Note: Market timing patches had no assigned workers (`[]`). The Phase 005 diagnostic replay script defaulted missing workers to worker 0 (Farmer), but evaluated candidate task value as $0.00, resulting in automatic rejection.*

#### Detailed Breakdown of the 576 Resource Conversion Records:
- **Idle Auxiliary Worker (`PASS`)**: 548 records.
  - **400 approved** at Level 1 (Local Exact Dependency, OC = $0.00).
  - **40 approved** at Level 2 (Peer Absorption Verified, OC = $0.00).
  - **108 rejected** at Level 3 (Candidate action was unexecutable no-op, netting $\Delta = 0.00$, previously hallucinating $130.00 OC).
- **Busy Auxiliary Worker (`Active`)**: 28 records.
  - 20 `BASE_1_157_CARE` (rejected at Level 3, mean OC = $18.60).
  - 4 `BASE_1_331_CARE` (rejected at Level 3, mean OC = $198.00).
  - 4 `BASE_1_650_FEED_ANIMAL` (rejected at Level 3, mean OC = $37.00).
- **Farmer Involvement**: 0 records (100% of RC patches targeted auxiliary Hand 1).
- **Peer Absorption**: 40 records (all approved at Level 2).

---

### 3. Exact Simulator Ground-Truth Results (Seeds 50000–50024)

Exact counterfactual game replays were executed in `kagsim` to compare exact terminal reward delta ($\Delta_{\text{exact}}$) against the engine's net incremental value ($\Delta_{\text{engine}}$):

| Ground-Truth Scenario Class | Total States | Sign Agreed | Sign Agreement % | Mean $\Delta_{\text{exact}}$ | Mean $\Delta_{\text{engine}}$ | Primary Causal Mechanism |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **IDLE_WORKER_HARVEST** | 25 | 6 | 24.0% | -$7,452.32 | +$60.00 | Local harvest creates +$60 cash; but unexpected cargo desynchronizes V3 agent loop. |
| **PRODUCTIVE_WORKER_DIVERSION** | 25 | 0 | 0.0% | -$7,669.40 | $0.00 | Missing 1 turn of watering/tending halves crop yield 2 days later; short rollout blind to compound decay. |
| **ZERO_DELTA_NEUTRAL** | 25 | 25 | 100.0% | $0.00 | $0.00 | Bit-exact neutral invariance preserved across all seeds. |
| **TERMINAL_HARVEST** | 25 | 16 | 64.0% | +$1,240.50 | +$60.00 | Late-game harvest realized directly into score before episode termination. |
| **Total Cohort Evaluation** | **100** | **47** | **47.0%** | -$3,470.30 | +$30.00 | Finite-horizon myopia vs long-term multi-turn policy coupling. |

#### Analysis of Economic Discrepancies:
1. **The Trajectory Splicing Gap**: In `IDLE_WORKER_HARVEST`, the labor engine evaluates the marginal 1-turn harvest action and finds +$60.00 direct value and $0.00 opportunity cost. When this single patch is injected into the full match, the baseline agent's subsequent steps do not expect cargo in Hand 1's backpack, leading to path blocks or delayed drop-offs. This proves that **harvest patches must be coupled with return routes (spliced trajectories)** rather than injected as isolated 1-turn actions.
2. **The Agricultural Horizon Gap**: In `PRODUCTIVE_WORKER_DIVERSION`, skipping a `WATER` turn produces zero immediate cash delta in a 6-step rollout, but permanently reduces wheat yield 48 steps later. The engine must use extended adaptive horizons when evaluating tasks that impact ongoing biological lifecycles.

---

### 4. Dedicated Ground-Truth Test Battery (GT-01 to GT-12)

All 12 dedicated tests in `tests/aec/test_phase005b_ground_truth.py` passed deterministically:

| Test ID | Test Name | Scenario Description | Expected Outcome | Result |
| :--- | :--- | :--- | :--- | :---: |
| **GT-01** | `test_gt01_exact_idle_worker_delta` | Idle worker (PASS) harvests mature CARROT ($60). | OC = 0.0, Net = 60.0, Rec = True | **PASS** |
| **GT-02** | `test_gt02_exact_productive_worker_displacement` | Worker displaced from harvesting mature CARROT to PASS. | OC = 60.0, Net = -60.0, Rec = False | **PASS** |
| **GT-03** | `test_gt03_peer_absorption` | H1 baseline duty absorbed by idle peer H2. | Level 2, OC = 0.0 | **PASS** |
| **GT-04** | `test_gt04_downstream_dependency` | Planting action unlocks downstream crop value. | downstream_val > 0.0 | **PASS** |
| **GT-05** | `test_gt05_terminal_deadline` | Crop planted with maturity day $\ge 30$ receives $0.00. | field_val == 0.0 | **PASS** |
| **GT-06** | `test_gt06_field_valuation_vs_actual_realization` | Unharvested mature crop on tile not counted as liquid cash. | field_val == 0.0 | **PASS** |
| **GT-07** | `test_gt07_no_double_counting` | Controlled: Candidate = $X, Baseline loss = $Y. | Net == X - Y | **PASS** |
| **GT-08** | `test_gt08_exact_sign_preservation` | Positive candidate $\to$ True; negative candidate $\to$ False. | Sign preserved | **PASS** |
| **GT-09** | `test_gt09_zero_delta_case` | Worker baseline PASS, candidate PASS. | OC = 0.0, Net = 0.0, Rec = False | **PASS** |
| **GT-10** | `test_gt10_deterministic_replay` | Identical inputs evaluated consecutively. | Bit-identical outputs | **PASS** |
| **GT-11** | `test_gt11_multiworker_attribution` | Farmer harvests while H1 passes; no cross-attribution. | affected_workers == [1] | **PASS** |
| **GT-12** | `test_gt12_cash_timing_interaction` | Negative cash outlay with no immediate return. | Net < 0.0, Rec = False | **PASS** |

Full test suite regression: **396/396 passed** in 2.08s.
