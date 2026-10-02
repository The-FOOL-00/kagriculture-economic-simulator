# V37 Determinism Audit

## 1. Test Methodology

The candidate agent from `submission_final_v35/main.py` was executed across two independent, sequential 720-step episodes under identical environment configurations (Seed `249676`, safe development cohort).

For each run:
1. Every step's emitted action dictionary was serialized into canonical JSON.
2. An end-to-end SHA-256 action digest was computed across all 720 steps.
3. Final rewards and cash totals were recorded.
4. Step-by-step element equality was asserted.

---

## 2. Determinism Audit Results

| Metric | Run 1 | Run 2 | Result |
| :--- | :--- | :--- | :---: |
| **Terminal Cash** | $148,390.00 | $148,390.00 | **EXACT MATCH** |
| **Action Sequence Digest (SHA-256)** | `6c8bebb9620ebe...` | `6c8bebb9620ebe...` | **BIT-IDENTICAL** |
| **Step-by-Step Action Mismatches** | 0 / 720 | 0 / 720 | **0 MISMATCHES** |
| **Unhandled Exceptions** | 0 | 0 | **NONE** |

---

## 3. Determinism Verdict

**PASS**. The staged candidate is strictly deterministic with zero stochastic drift, zero unseeded randomness, and zero non-deterministic state accumulation.
