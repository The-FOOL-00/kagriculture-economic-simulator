# V26 — AEC INFRASTRUCTURE NULL PARITY AUDIT

## 1. Objective & Empirical Standard
Per Section 11 and Section 12 of the V26 Protocol:
* **ARM 2 Purpose**: Test whether the backbone-aware AEC infrastructure itself perturbs the V25 backbone when no candidate interventions commit.
* **Mandatory Parity Invariant**: On every turn where no intervention commits:
  $$\text{Action}(\text{V25\_AEC\_INFRA\_ONLY}) \equiv \text{Action}(\text{V25\_STANDALONE})$$
* **Standard**: Zero unexplained divergence across all evaluated turns. Any divergence constitutes an infrastructure implementation failure.

---

## 2. Test Setup & Execution
* **Control Arm (ARM 1)**: `V25P3BackboneAdapter` executing standalone `candidates/v25_p3_unified.py`.
* **Treatment Arm (ARM 2)**: `AECExecutor` wrapping `V25P3BackboneAdapter` with `enabled_mechanisms=()`.
* **Test Suite**: `tests/aec/test_v26_null_parity.py::test_v25_aec_infra_only_null_parity`
* **Test Seed**: `249376` (50 game steps evaluated)
* **Kaggle Environment Engine**: `1.32.7`

---

## 3. Results Ledger

| Step Range | Turns Evaluated | Interventions Committed | Pure V25 vs AEC Infra Discrepancies | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Step 0** | 1 | 0 | 0 (`[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]`) | **EXACT MATCH** |
| **Steps 1–49** | 49 | 0 | 0 (Identical `farmer`, `hands`, `market`) | **EXACT MATCH** |
| **Total** | **50** | **0** | **0** | **100% BIT-EXACT PARITY** |

---

## 4. Key Findings
1. **Zero Intrusion**: When intervention mechanisms are gated off, the AEC supervisory pipeline (Event Bus, Economic IR builder, Opponent pressure model, Macro controller) operates in 100% passive monitoring mode without altering actions.
2. **Opening Preserved**: P3's optimized 30-unit opening wheat wash is transmitted with exact fidelity.
3. **In-Place Chore Preservation**: Units executing zero-inventory chores (`WATER` on dry crops, `DIG` on weeds) maintain exact coordinates and action parity.

---

## 5. Certification
ARM 2 null parity is certified as **PASSED**. The backbone-aware AEC infrastructure does not perturb or degrade the underlying V25 backbone.

## 6. Full-tournament addendum (2026-09-21)

The completed 4-arm tournament extended this check to 40 full-length matches
(cohort `249470..249489` × 2 seats): ARM2 vs ARM1 agree on terminal reward
**and** full action-stream digest in **40/40 pairs, 0 mismatches**
(mean paired Δ identical at −$218.75). Additionally, all 18 zero-commit
ARM3 matches reproduce the ARM1 action digest bit-exactly, confirming the
abstain path is behaviorally transparent.
