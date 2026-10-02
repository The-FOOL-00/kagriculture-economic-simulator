# V32 P12: Adversarial Stress & Boundary Audit (V32_P12_ADVERSARIAL_AUDIT)

**Phase:** V32 P12 (Sparse Options & Resynchronization)  
**Experiment ID:** P12-09_OPTION_ADVERSARIAL  
**Date:** 2026-09-24  
**Audit Outcome:** **10 / 10 SCENARIOS PASSED (100% FAIL-SAFE ABSTENTION TO A7)**  
**Mandatory Invariant:** When uncertain, stressed, or out of bounds: DO NOTHING. Follow A7.

---

## 1. Executive Summary

A core requirement of Phase P12 (Section 45, 50, 59) is that the sparse option architecture must be completely bulletproof to environmental stress, market shocks, opponent aggression, and internal state corruption. The controller must never force an option under marginal or adversarial conditions.

Under Experiment **P12-09**, 10 distinct adversarial stress boundary tests were executed against `SparseOptionController`. In every test, the candidate policy demonstrated perfect fail-safe behavior: zero illegal actions, zero unhandled exceptions, zero forced options, and 100% bit-identical fallback to the protected A7 incumbent.

---

## 2. Adversarial Test Matrix & Forensic Results

| Test # | Stress Scenario | Injected Condition | Expected Behavior | Observed Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **01** | `LOW_CASH_INSOLVENCY` | Money = $10.00 | Reject options; preserve runway | Abstained to A7; 0 options fired | **PASSED** |
| **02** | `PRICE_CRASH_COLLAPSE` | Spot prices crushed by -80% | Suppress sales; hold inventory | Abstained to A7; 0 options fired | **PASSED** |
| **03** | `OPPONENT_GLUT_FLOOD` | 100 units dumped in market | Prevent liquidation into flooded market | Abstained to A7; 0 options fired | **PASSED** |
| **04** | `EARLY_STEP_OUT_OF_BOUNDS` | Step = 10 (early quarantine) | Enforce step $\ge 24$ floor | Abstained to A7; 0 options fired | **PASSED** |
| **05** | `TERMINAL_WINDOW_QUARANTINE` | Step = 715 (terminal quarantine) | Enforce P11 terminal freeze | Abstained to A7; 0 options fired | **PASSED** |
| **06** | `INJECTED_DESYNC_STATE` | Worker displacement = 10 tiles | Lock controller in A7-recovery | Abstained to A7; 0 options fired | **PASSED** |
| **07** | `EXACT_CASH_NO_BUFFER` | Money = $1,000 (no safety margin)| Reject option; require buffer | Abstained to A7; 0 options fired | **PASSED** |
| **08** | `EMPTY_SHED_ZERO_STOCK` | Shed inventory = 0 | Reject liquidation/opportunistic sales | Abstained to A7; 0 options fired | **PASSED** |
| **09** | `ALL_QUADS_UNLOCKED` | Quadrants = 4 (maximum capacity)| Reject land expansion | Abstained to A7; 0 options fired | **PASSED** |
| **10** | `ZERO_RUNWAY_STRESS` | Money = $50.00, Hires today = 3 | Reject capex; prioritize wages | Abstained to A7; 0 options fired | **PASSED** |

---

## 3. Structural Defense Invariants Verified

1. **Gate G8 & Physical Sync Guard:** When `ResyncState.status == SyncStatus.DESYNCED`, the controller unconditionally disables candidate detection and routes execution exclusively through A7.
2. **Capital Buffer Guard:** Capex options (`O01 EXPAND_LAND`) enforce a strict $14,000.00 liquidity threshold, guaranteeing that the $4,000 land purchase can never cause wage default or worker starvation.
3. **Macroeconomic Absorption Guard:** Land expansion requires `"BAKERY" in unlocked_shops`, ensuring that the expanded grain and berry harvest is absorbed by town consumption rather than dumped into a collapsed open market.
4. **Legality & Order Clamping:** `SafetyEnforcer` guarantees that any malformed or out-of-order market intent is clamped to legal limits ($\le 10$ orders) with fail-closed fallback to A7 on any error.

---

## 4. Audit Conclusion

The candidate policy passes all requirements of **Gate G3 (No Unacceptable Tail Loss)** and **Gate G12 (A7 Remains Exact Fallback)** under adversarial testing.
