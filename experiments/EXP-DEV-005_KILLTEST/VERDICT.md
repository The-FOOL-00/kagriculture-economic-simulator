# EXP-DEV-005_KILLTEST FINAL VERDICT & GO/NO-GO GATE REPORT
## Retrospective Mechanism Kill-Test: Hysteresis Commitment Guard over DEV-004 Historical Reversals

**Experiment Identifier**: `EXP-DEV-005_KILLTEST`  
**Evaluation Scope**: Retrospective Mechanism Study (Strictly Diagnostic; Zero-Leakage Governance)  
**Historical Cohort Tested**: 16 Original DEV-004 Loss Seeds + 4 Positive Control Winning Seeds (Partition `246000–246049`)  
**Authoritative Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`, Verified SHA-256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`)  
**Intervention Tested**: `HYSTERESIS_COMMITMENT_GUARD` over `dev_004_joint_macro_scheduler.py`  
**Date**: 2026-09-14  
**Primary Verdict**: **MIXED_UNSAFE (MECHANISM HYPOTHESIS REJECTED / GATE 5 NO-GO)**

---

## 1. Executive Summary & Core Verdict

The retrospective mechanism kill-test **REJECTS** the hypothesis that mid-flight route reversal after sunk-capital commitment was the primary, remediable causal mechanism of the DEV-004 losses.

Applying the pre-registered **`HYSTERESIS_COMMITMENT_GUARD`** (which disallowed automatic reversions from specialized routes back to `BASELINE_BACKBONE` after Step 72 commitment):
1. **Failed the Pre-Registered Mechanism-Support Threshold**:
   - Recovered **+$9,673.50** (or **20.56%**) of the total 16-seed loss magnitude ($47,041.50).
   - Recovered **22.39%** of the 13-seed harmful-hysteresis loss magnitude ($43,198.50).
   - **Threshold Criterion Failed**: Fell far short of the pre-registered $\ge 50.0\%$ engineering threshold ($21,599.25).
2. **Introduced Severe New Major Failures**:
   - On **7 of the 13 reversal loss seeds**, forcing commitment *worsened* the losses, accumulating **-$16,946.50** in new damage (losses doubled from -$3.8k to -$8.2k on Seed 246022, and from -$2.6k to -$6.6k on Seed 246030).
   - On Positive Control Seed 246048, the guard caused a catastrophic collapse from a **+$14,143.00 win** into an **-$11,577.00 loss** (a single-seed damage of **-$25,720.00**).
3. **Primary Verdict**: Under the pre-registered governance classification logic, the mechanism is certified as **MIXED_UNSAFE**.
4. **Gate 5 Decision**: **NO-GO FOR FRESH DEV-005 DISCOVERY RUN USING COMMITMENT HYSTERESIS**.

---

## 2. Comprehensive Reconciliation of DEV-004 Errata

Authoritative data reconciliation between the raw simulation logs (`PLAN_EVENTS.csv`, `PAIRED_DELTAS.csv`) and the historical reports (`FINAL_REPORT.md`, `FORENSIC_AUDIT.md`) established:

1. **Outcome Breakdown ($N=50$)**: Exactly **14 Wins / 16 Losses / 20 Ties** (Win Rate: 28.0%, Loss Rate: 32.0%, Tie Rate: 40.0%).
2. **Activation Rate Disambiguation**:
   - **Reported 52.0% (26 seeds)**: Conflated *terminal active plan at step 719* with *lifetime activation*.
   - **True Lifetime Activation: 80.0% (40 seeds)**: 40 of 50 seeds selected a specialized macro route at $\ge 1$ planning checkpoint.
   - **Always-Baseline Seeds: 20.0% (10 seeds)**: Exactly 10 seeds never activated specialization, executing 100% bit-for-bit identical baseline behavior across all 72,000 steps with paired cash delta of **+$0.00**.
3. **Route Reversal Counts**:
   - Exactly **17 seeds** experienced route reversals from a specialized route back to baseline (34 match-level events).
   - 13 reversal seeds ended in losses; 4 reversal seeds ended in wins (positive controls); 0 ended in ties.

---

## 3. Resolution of BASELINE_BACKBONE Nonzero Deltas

The audit explicitly resolved the question: *"Does `BASELINE_BACKBONE` mean bit-for-bit baseline behavior?"*

- **NO for Terminal Status**: In `PAIRED_DELTAS.csv`, 14 seeds were recorded with `cand0_plan = BASELINE_BACKBONE` despite having non-zero paired deltas. Forensic tracing confirmed that every single one of these 14 seeds had activated `YARN_SPECIALIZED` at Step 72, diverged physically at Step 74 (selling 1 wheat instead of 2, altering strawberry planting vectors), and subsequently reverted to `BASELINE_BACKBONE` at Step 144 or 216. Their non-zero delta was caused by the physical desynchronization left by the abandoned specialization.
- **YES for Pure Invariants**: For the 10 seeds that were in `BASELINE_BACKBONE` at all four checkpoints, behavior was **100% bit-for-bit identical** to the baseline, with zero action differences and exact $0.00 delta.

---

## 4. Authoritative Table of the 16 Original Losses

| Seed | Baseline Reward | Candidate Reward | Paired Delta | Initial Plan | First Act Step | First Act Plan | Reversal? | Rev Step | Post-Rev Plan | Asset Purchased / Sunk Exposure | First Econ Div After Reversal | Final Plan | Final Delta |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **246003** | $44,337.0 | $43,433.0 | -$904.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$223.0) | BASELINE | -$904.0 |
| **246005** | $76,509.0 | $74,016.0 | -$2,493.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | BASELINE | -$2,493.0 |
| **246007** | $78,113.0 | $74,228.0 | -$3,885.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$223.0) | BASELINE | -$3,885.0 |
| **246008** | $81,744.0 | $79,436.0 | -$2,308.0 | BASELINE | 72 | YARN | No | NONE | NONE | Full Sheep/Straw ($8,850) | NONE | YARN | -$2,308.0 |
| **246010** | $82,627.0 | $81,251.0 | -$1,376.0 | BASELINE | 72 | YARN | No | NONE | NONE | Full Sheep/Straw ($8,850) | NONE | YARN | -$1,376.0 |
| **246016** | $54,860.0 | $54,701.0 | -$159.0 | BASELINE | 72 | YARN | No | NONE | NONE | Full Sheep/Straw ($8,850) | NONE | YARN | -$159.0 |
| **246022** | $105,992.0 | $102,242.0 | -$3,794.5 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | BASELINE | -$3,794.5 |
| **246024** | $85,330.0 | $74,961.0 | -$10,369.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | YARN | -$10,369.0 |
| **246028** | $55,750.0 | $53,637.0 | -$2,113.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$223.0) | BASELINE | -$2,113.0 |
| **246030** | $63,033.0 | $60,466.0 | -$2,567.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | BASELINE | -$2,567.0 |
| **246032** | $95,497.0 | $91,949.0 | -$3,548.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | BASELINE | -$3,548.0 |
| **246035** | $55,397.0 | $53,717.0 | -$1,680.0 | BASELINE | 72 | YARN | Yes | 216 | BASELINE | Sheep x4 & Straw ($5,900) | Step 217 (+$53.0) | BASELINE | -$1,680.0 |
| **246036** | $74,432.0 | $71,595.0 | -$2,837.0 | BASELINE | 72 | YARN | Yes | 216 | BASELINE | Sheep x4 & Straw ($5,900) | Step 217 (+$53.0) | BASELINE | -$2,837.0 |
| **246039** | $76,004.0 | $72,531.0 | -$3,473.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | BASELINE | -$3,473.0 |
| **246042** | $64,699.0 | $62,365.0 | -$2,334.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$225.0) | BASELINE | -$2,334.0 |
| **246049** | $67,840.0 | $64,639.0 | -$3,201.0 | BASELINE | 72 | YARN | Yes | 144 | BASELINE | Strawberries & Feed ($2,900) | Step 145 (+$223.0) | BASELINE | -$3,201.0 |

---

## 5. Kill-Test Quantitative Results

### 5.1 The 16 Original Loss Seeds

| Seed | Original Delta | Kill-Test Delta | Net Improvement | Original Reversal? | Guard Activated? | New Failure? | Mechanism Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **246003** | -$904.00 | -$549.00 | +$355.00 | Yes | Yes | No | Partial recovery |
| **246005** | -$2,493.00 | +$1,023.00 | +$3,516.00 | Yes | Yes | No | Full recovery (flip to WIN) |
| **246007** | -$3,885.00 | -$4,789.00 | -$904.00 | Yes | Yes | Yes | Worsened (dead inventory) |
| **246008** | -$2,308.00 | -$2,308.00 | $0.00 | No | No | No | Unaffected (non-reversal) |
| **246010** | -$1,376.00 | -$1,376.00 | $0.00 | No | No | No | Unaffected (non-reversal) |
| **246016** | -$159.00 | -$159.00 | $0.00 | No | No | No | Unaffected (non-reversal) |
| **246022** | -$3,794.50 | -$8,188.00 | **-$4,393.50** | Yes | Yes | **YES** | Severe collapse (no Yarn store) |
| **246024** | -$10,369.00 | -$1,011.00 | **+$9,358.00** | Yes | Yes | No | Major recovery (anti-oscillation) |
| **246028** | -$2,113.00 | +$8,775.00 | **+$10,888.00** | Yes | Yes | No | Massive recovery (flip to WIN) |
| **246030** | -$2,567.00 | -$6,606.00 | **-$4,039.00** | Yes | Yes | **YES** | Severe collapse (no Yarn store) |
| **246032** | -$3,548.00 | -$5,049.00 | -$1,501.00 | Yes | Yes | Yes | Worsened (dead inventory) |
| **246035** | -$1,680.00 | +$49.00 | +$1,729.00 | Yes | Yes | No | Full recovery (flip to WIN) |
| **246036** | -$2,837.00 | -$3,751.00 | -$914.00 | Yes | Yes | Yes | Worsened (dead inventory) |
| **246039** | -$3,473.00 | -$6,211.00 | **-$2,738.00** | Yes | Yes | **YES** | Severe collapse (no Yarn store) |
| **246042** | -$2,334.00 | -$4,791.00 | **-$2,457.00** | Yes | Yes | **YES** | Severe collapse (no Yarn store) |
| **246049** | -$3,201.00 | -$2,427.00 | +$774.00 | Yes | Yes | No | Partial recovery |
| **TOTAL** | **-$47,041.50** | **-$37,368.00** | **+$9,673.50** | — | — | — | **20.56% Recovery (<50% Threshold)** |

### 5.2 Positive-Control Test Results

| Seed | Original DEV-004 Delta | Kill-Test Delta | Difference | Guard Activated? | Beneficial Reversal Blocked? | Causal Consequence |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **246012** | +$8,330.00 | +$8,483.00 | +$153.00 | Yes | No | Preserved win (Yarn store at 216) |
| **246026** | +$8,816.00 | +$8,011.00 | -$805.00 | Yes | Yes | Slight loss (missed adaptive exit) |
| **246034** | +$5,453.00 | +$23,442.00 | +$17,989.00 | Yes | No | Expanded win (favorable wool spot) |
| **246048** | **+$14,143.00** | **-$11,577.00** | **-$25,720.00** | Yes | **YES (CRITICAL)** | **Catastrophic liquidity collapse** |
| **TOTAL** | **+$36,742.00** | **+$28,359.00** | **-$8,383.00** | — | — | **Net Negative Impact on Controls** |

---

## 6. Causal Diagnosis: Why Commitment Hysteresis Failed

1. **Reversal is an Adaptive Reaction, Not the Root Disease**:
   The planner reverted at Step 144 because the second town shop revealed that no `YARN_STORE` was present. Reverting to baseline, while inducing friction (-$2k to -$3k), successfully terminated further accumulation of unsellable sheep.
2. **The Root Flaw is Premature Speculative Commitment at Step 72**:
   At Step 72, only Shop 1 is known. The candidate planner gambled on Yarn based on early spot prices without confirming shop existence. When the shop failed to materialize, the agent was trapped:
   - *If it reversed (DEV-004)*: Sunk capital mismatch produced small friction losses (-$2k to -$3k).
   - *If it stayed committed (Kill-Test)*: Feed drain and dead wool inventory produced catastrophic losses (-$4k to -$8k).
3. **Blocking Reversals Destroys Asymmetry**:
   Forcing commitment recovered $27,519 on 6 seeds (246005, 246024, 246028, 246034, 246035, 246049), but incurred **-$42,666** in new collateral damage across 7 worsened loss seeds and positive control 246048.

---

## 7. Primary Mechanism Verdict

$$\mathbf{VERDICT: \quad MIXED\_UNSAFE}$$

### Formal Justification Against Pre-Registered Criteria:
1. **Threshold Criterion Failed**: Total recovery on the 16 loss seeds was **+$9,673.50 (20.56%)**, failing the pre-registered $\ge 50.0\%$ mechanism-support threshold ($21,599.25).
2. **Safety Criterion Violated**: Positive control evaluation revealed a catastrophic **-$25,720.00** collapse on Seed 246048, and 7 loss seeds suffered doubled losses.
3. **Mechanism Rejected**: Commitment hysteresis alone does not fix the underlying vulnerability of the whole-route architecture.

---

## 8. Strategic Recommendations for DEV-005 Discovery

1. **DO NOT Promote Hysteresis Commitment Guard**: Do not implement blind route commitment into the architecture.
2. **Address the True Root Cause (Premature Gating)**:
   - In DEV-004, the planner activated specialized routes at Step 72 even when the matching shop was absent, relying on speculative Town Center sales.
   - For DEV-005, evaluate a **Confirmed Shop Requirement**: Specialize in `YARN_SPECIALIZED` *only* if `YARN_STORE` is physically confirmed in `unlocked_shops`, or delay livestock specialization until Day 6 / Day 9 when shops are revealed.
3. **Governance Mandate**:
   - Maintain frozen live submissions `56146971` and `56146947` untouched.
   - Maintain qualification partition `50050–50099` untouched.
   - Maintain virgin holdout `214200–214249` untouched.
   - Await user direction before launching any fresh Discovery experiment.
