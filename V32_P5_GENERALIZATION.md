# V32 P5 — GENERALIZATION & HOLDOUT GOVERNANCE GATE

## 1. FORMAL GATE STATUS: **REFUSED (GATE CLOSED)**

In strict adherence to Section 29 and Section 30 of the V32 P5 Protocol:

> **"Generalization is downstream of closed-loop recovery.**
> **Do not run it simply because action accuracy improved.**
> **Require:**
> **1. first-divergence improvement**
> **2. closed-loop economic improvement**
> **3. reproducibility**
> **4. no catastrophic tails**
> **5. no leakage**
> **Only then run the untouched confirmation cohort.**
> **Protected holdouts remain untouched unless a later explicit promotion review authorizes them."**

---

## 2. GATE CRITERIA EVALUATION

| Criterion | Requirement | Arm 2 Result | Gate Status |
|:---|:---|:---:|:---:|
| **1. First Divergence Delay** | Delay divergence past Step 0/1 | Delayed from Step 0 to Step 2 | **PASS** |
| **2. Economic Recovery** | Statistically significant cash improvement | $0.00 mean cash (Regime unchanged) | **FAIL** |
| **3. Reproducibility** | Deterministic closed-loop execution | 100% bit-identical trajectories across runs | **PASS** |
| **4. Tail Safety** | Elimination of catastrophic $0 regimes | $0 terminal cash persists across seeds | **FAIL** |
| **5. Anti-Leakage Audit** | Zero trace replay, zero test leakage | Strict static and semantic compliance | **PASS** |

### Formal Ruling:
Because **Criterion 2 (Economic Recovery)** and **Criterion 4 (Tail Safety)** were NOT satisfied, the Generalization Gate is **CLOSED**.

---

## 3. STRICT HOLDOUT QUARANTINE ENFORCEMENT

No confirmation seeds and no protected holdouts were accessed, evaluated, or probed during P5.
The following seed ranges remain 100% virgin and protected:
- `249685–249694` (P3-CONFIRM / P4-CONFIRM)
- `249695–249734` (V32-CONFIRM / EXP-1)
- `214200–214249` (GATE0 virgin holdout)
- `340090–340199` (Protected tournament remainder)
