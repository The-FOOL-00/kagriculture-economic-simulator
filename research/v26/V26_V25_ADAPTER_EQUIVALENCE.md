# V26 — V25 P3 ADAPTER EQUIVALENCE AUDIT

## 1. Objective
Confirm that the formal `V25P3BackboneAdapter` (`aec/backbone/v25_p3_adapter.py`) achieves bit-exact action-level equivalence against the standalone V25 P3 candidate (`candidates/v25_p3_unified.py`) across 100% of tested game turns, with guaranteed zero AEC intervention logic.

---

## 2. Test Protocol & Environment
* **Baseline Payload**: `candidates/v25_p3_unified.py` (SHA-256: `13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179`, byte-identical to `e4eb8a4` blob)
* **Test Adapter**: `V25P3BackboneAdapter` (`aec/backbone/v25_p3_adapter.py`)
* **Test Suite**: `tests/aec/test_v26_backbone_adapters.py::test_v25_p3_adapter_exact_equivalence`
* **Test Seed**: `249376` (50 game steps lockstep evaluation)
* **Kaggle Environment Engine**: `1.32.7`

---

## 3. Results Ledger

| Step Range | Total Turns Evaluated | Action Divergences | Market Order Divergences | In-Place Chore Divergences | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Steps 0–49** | 50 | **0** | **0** | **0** | **100% BIT-EXACT MATCH** |

### Per-Turn Action Verification:
- **Step 0 (Optimized Wash)**: Both produce `[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]`.
- **Steps 1–49 (Unified Macro Planning)**: Both produce identical route steps with zero-inventory in-place chore dispatch (`WATER` on dry crops, `DIG` on weeds for idling `PASS` units).
- **Invariants Enforced**: Repeated call on the same step raises `RuntimeError`.
- **Identity Certified**: `V25_P3_UNIFIED` (Version: `1.0.0-v25-p3`).

---

## 4. State Isolation & Snapshot Certification
- `test_v25_p3_state_isolation_and_snapshot` passed:
  Taking a snapshot at Step 1, creating a `V25P3Continuation` instance, evaluating 5 forward shadow simulation turns, and restoring state produces bit-exact execution on subsequent live calls.

---

## 5. Verdict
`V25P3BackboneAdapter` is certified as an exact, non-intrusive wrapper around the promoted V25 Unified Macro Planner.
