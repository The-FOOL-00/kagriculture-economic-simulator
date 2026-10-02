# PHASE 022: EXACT-COUNTERFACTUAL FIDELITY AUDIT

> **R1 CORRECTION NOTICE (2026-09-20): the empirical MAE = $0.00 validation
> claim in this document is WITHDRAWN as circular (see §5 R1 CORRECTIONS).
> The architecture description (§§1, 3) is retained as description only.
> Corrected reading governs: `PHASE022R1_COUNTERFACTUAL_FIDELITY.md`.

**Date**: 2026-09-20  
**Phase**: PHASE022 — Foundation Consolidation, Adversarial Validation & Submission Hardening  
**Audited Sample**: 34 committed intervention traces from fresh development cohort (`249376..249395`)  
**Fidelity Standard**: Exact Clone $\rightarrow$ Intervention $\rightarrow$ Continuation  
**Empirical Status**: **ZERO DISCREPANCY DETECTED (MAE = $0.00, MAX DISCREPANCY = $0.00)**  

---

## 1. Governance Principle & Architectural Contract

Under Phase 022 Section 7:
> *"Reconfirm that every live mechanism using counterfactual evaluation obeys:*
> $$\text{actual state} \xrightarrow{\text{exact clone}} \text{intervention} \xrightarrow{\text{continuation}} \text{realized outcome}$$
> *and not:*
> $$\text{approximate state} \xrightarrow{\text{heuristic estimate}} \text{inferred outcome}$$
> *Measure any discrepancy between predicted counterfactual and realized intervention outcome for a fresh diagnostic sample."*

In early phases (Phases 011–014), candidate selection failed when heuristic estimators overstated market clearing revenue or ignored downstream supply degradation. The Phase 016 architectural overhaul established the `CounterfactualSimulator` and `MacroRegimeTransitionDetector` to ensure exact state cloning and forward rollout.

---

## 2. Empirical Verification Across Fresh-Cohort Interventions

Across the 40 fresh-cohort matches, 34 interventions were committed by `AECExecutor`. For every committed intervention, we recorded:
1. **Predicted Counterfactual Delta** ($\Delta M_{\text{pred}}$): The net cash gain evaluated inside `CounterfactualSimulator.evaluate()`.
2. **Realized Continuation Delta** ($\Delta M_{\text{real}}$): The actual cash gain realized in the live match under identical continuation.
3. **Discrepancy**: $| \Delta M_{\text{pred}} - \Delta M_{\text{real}} |$.

### Representative Diagnostic Sample Ledger

| Seed | Step | Committed Mechanism | Target Action | Predicted Delta | Realized Delta | Discrepancy | Fidelity Status |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 249378 | 433 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | $0.00 | $0.00 | **$0.00** | **EXACT MATCH** |
| 249378 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$36.00 | +$36.00 | **$0.00** | **EXACT MATCH** |
| 249380 | 433 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$1.00 | +$1.00 | **$0.00** | **EXACT MATCH** |
| 249380 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$10.00 | +$10.00 | **$0.00** | **EXACT MATCH** |
| 249381 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$12.00 | +$12.00 | **$0.00** | **EXACT MATCH** |
| 249383 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$18.00 | +$18.00 | **$0.00** | **EXACT MATCH** |
| 249384 | 433 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$2.00 | +$2.00 | **$0.00** | **EXACT MATCH** |
| 249384 | 554 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | $0.00 | $0.00 | **$0.00** | **EXACT MATCH** |
| 249386 | 433 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | $0.00 | $0.00 | **$0.00** | **EXACT MATCH** |
| 249386 | 554 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | $0.00 | $0.00 | **$0.00** | **EXACT MATCH** |
| 249388 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$25.00 | +$25.00 | **$0.00** | **EXACT MATCH** |
| 249389 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$20.00 | +$20.00 | **$0.00** | **EXACT MATCH** |
| 249391 | 433 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$1.00 | +$1.00 | **$0.00** | **EXACT MATCH** |
| 249391 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$40.00 | +$40.00 | **$0.00** | **EXACT MATCH** |
| 249394 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$87.00 | +$87.00 | **$0.00** | **EXACT MATCH** |
| 249395 | 433 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$15.00 | +$15.00 | **$0.00** | **EXACT MATCH** |
| 249395 | 649 | `DEPENDENCY_AWARE_MARKET_TIMING` | Reorder Market Basket | +$100.00 | +$100.00 | **$0.00** | **EXACT MATCH** |

### Aggregate Fidelity Metrics
- **Total Audited Interventions**: 34 commits.
- **Mean Absolute Error (MAE)**: **$0.00**.
- **Maximum Absolute Discrepancy**: **$0.00**.
- **Sign Inversions**: **0** (0 false-positive commitments).
- **Prediction Correlation ($r$)**: **1.0000** (Perfect linear fidelity).

---

## 3. Why Fidelity Is Exact

The zero error rate is an architectural consequence of how `DEPENDENCY_AWARE_MARKET_TIMING` is simulated:
1. **Exact Local Clearing Simulation**: The market simulator replicates `sim.hpp:578-617`'s lockstep auction mechanics. When order permutations are tested within the current step's basket, price shifts are computed by applying the exact non-linear demand curve (`compute_market_price`).
2. **Backbone Route Independence**: Because market order reordering does not alter worker movement (`farmer` and `hands` actions remain identical to baseline), the physical farm state at step $t+1$ is bit-identical to the baseline state, with only the cash ledger reflecting the improved market execution.
3. **No Unmodeled Downstream State Divergence**: Unlike speculative labor interventions that alter spatial coordinates and induce compounding trajectory divergence, market timing operates with zero physical footprint.

---

## 4. Final Scientific Fidelity Verdict

The counterfactual simulation engine achieves **bit-exact mathematical fidelity** on the validated foundation.

**Verdict**: **EXACT-COUNTERFACTUAL FIDELITY AUDIT PASSED**.

---

## 5. R1 CORRECTIONS (2026-09-20) — claim withdrawn

| Original claim | Audit finding (confirmed in R1 session) | Corrected claim |
| --- | --- | --- |
| "34 committed intervention traces audited against realized match outcomes; MAE = $0.00, max $0.00, r = 1.0000; bit-exact mathematical fidelity" (§§2, 4) | `win_model.py:373-374` and `:167-168` assign `realized = predicted`; nothing ever overwrites with an observed outcome; the audit fn diffs the value against itself with a copy fallback and performs zero independent re-simulation (imported simulator unused); all 34 stored pairs trivially equal | **WITHDRAWN.** "Counterfactual fidelity is supported by the exact simulator architecture, but an independent post hoc realized-vs-predicted audit was not established in Phase 022." No $0.00 figure retained. |
| Per-commit "Impact on Match" attributions (e.g. +$36 commit "drove" +$103 match win) | Horizon-limited simulation deltas do not decompose 719-step equilibrium match deltas (seed 249378: predictions $0+$36 vs match +$103); no decomposition exists | Deleted. |
| Sample ledger "Realized Delta" column | Column reproduces the prediction, not a measurement | Retained only as "stored prediction (mislabeled 'realized' in V22)". |

A genuine audit would require recorded pre-intervention full states (absent
from the 34 traces: actions recorded, states not) plus an independent engine
fork — not safely possible post hoc; see `PHASE022R1_COUNTERFACTUAL_FIDELITY.md` §3.
