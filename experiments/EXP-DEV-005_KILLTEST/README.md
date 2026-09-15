# EXP-DEV-005_KILLTEST PRE-REGISTRATION & PROTOCOL MANIFEST
## Retrospective Mechanism Kill-Test: Hysteresis Commitment Guard over DEV-004 Historical Reversals

**Experiment Identifier**: `EXP-DEV-005_KILLTEST`  
**Classification**: Retrospective Mechanism Study (Diagnostic Only)  
**Governing Mandate**: Zero-Leakage Governance / Pre-Registration Gate  
**Date**: 2026-09-14  
**Authoritative Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)  
**Baseline Verified SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`  
**Treatment Candidate**: `HysteresisCommitmentGuardScheduler` over `dev_004_joint_macro_scheduler.py`  
**Simulator Engine**: `kagsim.Game` (v1.32.7)  
**Design**: Paired Common Random Numbers (CRN), Seat-Swapped (Match 0: Cand 0 / Base 1; Match 1: Base 0 / Cand 1)

---

## 1. Context & Governance Constraints

1. **Retrospective Mechanism Study Only**:
   - This experiment tests the specific mechanistic claim: *"Mid-flight route reversal after sunk-capital commitment is the primary causal driver of losses in DEV-004."*
   - It is strictly an internal mechanism test. It does **not** constitute new Discovery evidence, Qualification evidence, generalization evidence, leaderboard evidence, or Kaggle superiority evidence.
2. **Forbidden Actions**:
   - DO NOT execute fresh Discovery seeds.
   - DO NOT access Qualification partition `50050–50099`.
   - DO NOT access Virgin Final Holdout `214200–214249`.
   - DO NOT access DEV-003 consumed partition `245000–245049`.
   - DO NOT modify or submit live submissions `56146971` or `56146947`.
   - Partition `246000–246049` (DEV-004 consumed partition) is reused **exclusively** for this retrospective mechanism audit.

---

## 2. Pre-Registered Intervention: `HYSTERESIS_COMMITMENT_GUARD`

### 2.1 The Single Structural Change
The intervention consists of **exactly ONE structural change** to the checkpoint decision rule:
- Once a candidate enters a specialized route (`active_plan != "BASELINE_BACKBONE"` at Step 72 or later) and initiates physical execution, the candidate may **not** automatically revert to `BASELINE_BACKBONE` at subsequent checkpoints (Steps 144, 216, 288) solely because the short-horizon projected advantage drops below the opportunity hurdle (`best_candidate_delta < TAU`).

### 2.2 Pre-Specified Hard Safety Exception
Reversion to `BASELINE_BACKBONE` is permitted **only** if the following pre-specified hard safety condition is met:
- **Liquidity Insolvency Floor**: Working capital at the decision checkpoint drops below the frozen minimum liquidity threshold ($L_{\text{min}} = 100.0$ coins).
  $$\text{If } \text{money} < L_{\text{min}}, \text{ allow emergency exit to } \text{BASELINE\_BACKBONE}.$$

### 2.3 Structural Invariant Discipline
No other architectural modifications are permitted:
- No new crop heuristics.
- No new livestock heuristics.
- No new market rules or shop pull adjustments.
- No new terminal rules.
- No new worker-routing rules.
- No parameter tuning of $\tau$ ($1500.0$), $L_{\text{min}}$ ($100.0$), or $F_{\text{switch}}$ ($200.0$).
- No crop caps.

---

## 3. Pre-Registered Cohorts

### 3.1 Primary Test Set: The 16 Original DEV-004 Loss Seeds
The test is evaluated first on the exact 16 seeds where DEV-004 suffered a negative paired delta:
```
246003, 246005, 246007, 246008, 246010, 246016, 
246022, 246024, 246028, 246030, 246032, 246035, 
246036, 246039, 246042, 246049
```
- Original 16-seed total loss magnitude: **-$47,041.50**
- Original 13-reversal loss magnitude: **-$43,198.50**

### 3.2 Positive-Control Set: The 4 Reversal Winning Seeds
The intervention is evaluated on all 4 winning seeds from DEV-004 where route reversal occurred:
```
246012 (+$8,330.00), 246026 (+$8,816.00), 246034 (+$5,453.00), 246048 (+$14,143.00)
```
- Total positive control win volume: **+$36,742.00**
- Purpose: Ensure that the commitment guard does not eliminate beneficial, adaptive route abandonment.

---

## 4. Pre-Registered Endpoints & Decision Thresholds

### 4.1 Primary Endpoint
- **Aggregate Net Reduction in Loss Magnitude** on the 16 original loss seeds:
  $$\Delta \text{Loss} = \sum_{i=1}^{16} \Delta_{\text{killtest}}^{(i)} - \sum_{i=1}^{16} \Delta_{\text{DEV-004}}^{(i)}$$

### 4.2 Mechanism-Support Threshold
- **Threshold**: Recovery of **$\ge 50.0\%$** of the original harmful-hysteresis loss magnitude.
  $$\text{Required Recovery} \ge 0.50 \times \$43,198.50 = \$21,599.25$$
- *Note*: This 50% threshold is a pre-specified engineering mechanism-support threshold, **not** a statistical significance criterion.

### 4.3 Classification Logic (Pre-Registered)
1. **`SUPPORTED`**:
   - Material aggregate recovery occurs on the 16 loss seeds, **AND**
   - $\ge 50.0\%$ of harmful-hysteresis loss magnitude is recovered ($\ge \$21,599.25$), **AND**
   - Positive-control evaluation does not introduce comparable new losses by blocking good reversals, **AND**
   - Forensic tracing attributes recovery specifically to the eliminated asset mismatch.
2. **`NOT_SUPPORTED`**:
   - $< 50.0\%$ recovery, and no major safety trade-off is introduced.
3. **`MIXED_UNSAFE`**:
   - The guard recovers some losses, but creates comparable or major new failures (in either loss seeds or positive controls).
4. **`UNRESOLVED`**:
   - Causal tracing cannot isolate the mechanism from confounding simulator variations.
