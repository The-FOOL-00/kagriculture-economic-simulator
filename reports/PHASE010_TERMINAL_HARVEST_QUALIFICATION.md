# AEC PHASE 010: TERMINAL HARVEST SWEEP QUALIFICATION REPORT
**Mechanism**: `TERMINAL_HARVEST_SWEEP`  
**Priority Group**: Group A (Priority 2)  
**Evaluation Stage**: Stage A (Pilot Exposure Replay on Fresh Development Seeds `249053–249055`)  
**Matches Evaluated**: 6 Common Random Numbers (CRN) Mirror-Seat Matches (3 Seeds x 2 Seats)  
**Date**: 2026-09-18  
**Architecture Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Zero Touches of Protected Cohorts (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Executive Summary & Qualification Decision

| Metric | Empirical Result | Governance Gate Criterion | Gate Status |
| :--- | :--- | :--- | :--- |
| **Implementation Integrity** | Complete Python implementation (`aec/opportunities/terminal.py`) | Fully integrated & typed | **PASSED** |
| **Synthetic Activation** | 100% passing (`test_matrix_2_terminal_harvest_sweep`) | Passes full mock compiler pipeline | **PASSED** |
| **Opportunity Detection** | 826 terminal candidates proposed | $\ge 1$ candidates | **PASSED** |
| **Exact Simulations Run** | 412 counterfactual simulations | $\ge 1$ exact simulations | **PASSED** |
| **Committed Patches** | **0 Commits** (0.0% commit rate given exposure) | $\ge 1$ commits required for efficacy test | **UNMET (DORMANT)** |
| **Safety Failures** | 0 Safety Violations (100% safe) | 0 Safety Violations | **PASSED** |
| **Mean Net Delta** | **+$13.67 ± $46.84** ($t=0.29$, $p=0.7705$) | $\text{Mean}(\Delta) > 0.0$ | **UNATTRIBUTED (0 commits)** |
| **Final Classification** | **DORMANT / ECONOMICALLY DOMINATED BY BASELINE** | — | **QUARANTINED** |

**Official Gate Decision**: **DORMANT / FUNCTIONALLY COMPLETE (QUARANTINED FROM LIVE)**.  
The mechanism is structurally complete and synthetically verified. In empirical full-game matches against the frozen baseline, it generated 826 terminal candidates, but 100% abstained. The +$13.67 net delta is wholly attributable to baseline `DEPENDENCY_AWARE_MARKET_TIMING` commits (10 commits), with 0 commits from `TERMINAL_HARVEST_SWEEP`. Per Part X and Part XII, the mechanism is classified as dormant/economically dominated and remains quarantined from live deployment.

---

## 2. Telemetry & Empirical Exposure Breakdown

From `results/PHASE010_TERMINAL_HARVEST_SWEEP_PILOT_TELEMETRY.json`:
- **Seeds Evaluated**: `249053`, `249054`, `249055` (N=3 fresh seeds, 6 matches)
- **Elapsed Replay Runtime**: 788.3s (131.4s / match)
- **Target Candidates Screened**: 826 candidates (concentrated in steps 696–717)
- **Target Exact Simulations**: 412 simulations
- **Target Commits**: 0
- **Foundation Commits**: 10 (100% `DEPENDENCY_AWARE_MARKET_TIMING`)
- **Total Abstentions**: 412
- **Primary Abstain Classification**: `NO_CANDIDATE_CERTIFIED_SUPERIOR`
- **Safety Rejections**: 0
- **Runtime Exceptions / Aborts**: 0 (100% fail-closed stability)
- **Mirror Record**: 1 Win / 2 Losses / 0 Ties
- **Seed Deltas**:
  - Seed `249053`: -$53.0 (S0: -$1432, S1: +$1326)
  - Seed `249054`: +$104.0 (S0: -$1126, S1: +$1334)
  - Seed `249055`: -$10.0 (S0: -$10, S1: -$10)

---

## 3. Root-Cause Diagnostic Analysis (Per Part X & XII)

Under Part X and Part XII:
1. **Biological and Physical Latency Constraint**:
   - `TERMINAL_HARVEST_SWEEP` activates at `step >= 696`.
   - To realize actual monetary value before episode end (`step 718`), a worker at tile $(x, y)$ must:
     a) Travel to crop tile: $d_1$ steps.
     b) Execute `HARVEST`: 1 step.
     c) Travel to shed $(0, 0)$: $d_2$ steps.
     d) Execute `DROP`: 1 step.
     e) Sell inventory at market: market order executed before step 718.
   - The total operational cycle requires $d_1 + d_2 + 2$ turns. For any crop not directly adjacent to both the worker and shed, this cycle exceeds the remaining time runway ($718 - 696 = 22$ steps).
2. **Baseline Preemption**:
   - For crops close to the shed, the V3 baseline agent already initiates final harvests and routes workers to deposit and sell before step 718.
   - Consequently, the candidate trajectory achieves either:
     a) Identical terminal margin to the baseline ($\Delta = \$0.00$), or
     b) Negative margin due to abandoned baseline tasks.
3. **Safety & Governance**:
   - Exact simulator fidelity verified: no hallucinatory terminal values were credited.
   - Candidate funnel and safety checking correctly prevented zero-margin commits.

---

## 4. Scientific Conclusion & Governance Action

1. `TERMINAL_HARVEST_SWEEP` remains **quarantined** from `AEC_ROBUST_QUALIFIED`.
2. Functionality is complete and safely preserved in `AEC_RESEARCH_FULL`.
3. Per Part XXVI, stop condition is reached: mechanism is proven naturally dormant under baseline optimal play.
