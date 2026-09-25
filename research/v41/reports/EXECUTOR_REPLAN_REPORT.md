# V41 State-Aware Executor & Replanning Architecture Report

**Document ID:** `research/v41/reports/EXECUTOR_REPLAN_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Scope:** Architectural specification, implementation details, safety verification, and formal Golden Property validation of the `StateAwareExecutor`.

---

## 1. Executive Summary

In direct fulfillment of Sections 6, 7, and 8 of the V41 directive, we engineered `StateAwareExecutor` (`research/v41/executor/safe_executor.py`).

The fundamental architectural principle is:
> The RL agent may propose strategy. It may never blindly mutate the mechanical state of the incumbent controller. When the RL policy abstains (or fails confidence thresholds), execution must be 100% bit-for-bit identical to the incumbent baseline.

---

## 2. Core Architecture

```text
                     OBSERVATION
                          │
                          ▼
            V41 STATE-AWARE SAFE EXECUTOR
                          │
           ┌──────────────┴──────────────┐
           │                             │
    INTERVENTION == 0             INTERVENTION > 0
    (Golden Abstention)           (Candidate Proposal)
           │                             │
           ▼                             ▼
    V35 / V39 BASELINE           LEGALITY & SAFETY
       ACTION TAPE                     MASKING
           │                             │
           │                      ┌──────┴──────┐
           │                      │             │
           │                   INVALID        VALID
           │                      │             │
           │                      ▼             ▼
           │                 FAIL-CLOSED    APPLY ATOMIC /
           │                  FALLBACK      REPLANNED DELTA
           │                      │             │
           └──────────────┬───────┘             │
                          │                     │
                          └──────────┬──────────┘
                                     │
                                     ▼
                            FINAL ACTION BASKET
                                     │
                                     ▼
                                ENVIRONMENT
```

---

## 3. The Golden Property Verification

### Formal Invariant Definition
Let $\mathcal{A}_{\text{V35}}(s_t)$ denote the action dictionary produced by `V35OpeningController` at state $s_t$, and $\mathcal{A}_{\text{V41}}(s_t, a_t=0)$ denote the action dictionary produced by `StateAwareExecutor` under zero intervention. Then:

$$\forall t \in [0, 718], \quad \mathcal{A}_{\text{V41}}(s_t, 0) \equiv \mathcal{A}_{\text{V35}}(s_t)$$

Similarly for the V39-enhanced mode:

$$\forall t \in [0, 718], \quad \mathcal{A}_{\text{V41, v39}}(s_t, 0) \equiv \mathcal{A}_{\text{V39}}(s_t)$$

### Empirical Verification Test Results (`test_golden_property.py`)
Executed across 4 distinct seeds (`249635`, `249636`, `249637`, `249638`) against `E8_DMITRII`:

| Test Mode | Seed | Evaluated Turns | Discrepancies | Baseline Cash | V41 (Intervention=0) Cash | Verification Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V35 Baseline** | 249635 | 719 | 0 | $75,128.00 | $75,128.00 | **PASS (100% Bit-Identical)** |
| **V35 Baseline** | 249636 | 719 | 0 | $125,499.00 | $125,499.00 | **PASS (100% Bit-Identical)** |
| **V35 Baseline** | 249637 | 719 | 0 | $127,369.00 | $127,369.00 | **PASS (100% Bit-Identical)** |
| **V35 Baseline** | 249638 | 719 | 0 | $114,132.00 | $114,132.00 | **PASS (100% Bit-Identical)** |
| **V39 Baseline** | 249635 | 719 | 0 | $75,123.00 | $75,123.00 | **PASS (100% Bit-Identical)** |
| **V39 Baseline** | 249636 | 719 | 0 | $125,500.00 | $125,500.00 | **PASS (100% Bit-Identical)** |
| **V39 Baseline** | 249637 | 719 | 0 | $127,138.00 | $127,138.00 | **PASS (100% Bit-Identical)** |
| **V39 Baseline** | 249638 | 719 | 0 | $114,132.00 | $114,132.00 | **PASS (100% Bit-Identical)** |
| **TOTAL** | — | **5,752 turns** | **0** | — | — | **ZERO DISCREPANCIES** |

---

## 4. Fail-Closed Safety Guarantees

The `StateAwareExecutor` implements three nested layers of safety protection:
1. **Dynamic Action Masking:** Interventions are verified against physical inventory, shed stock, liquidity buffers, and temporal windows before execution.
2. **Atomic Invariant Clamping:** All generated orders respect the hard 10-order cap, shed stock limits, and cash balance floors.
3. **Fail-Closed Fallback:** If any step encounters an unexpected condition, exception, or invariant violation, the executor discards the proposed mutation and immediately yields the untouched baseline action.
