# V26 — V3 ADAPTER EQUIVALENCE AUDIT

## 1. Objective
Confirm that the formal `V3BackboneAdapter` (`aec/backbone/v3_adapter.py`) achieves bit-exact action-level and telemetry-level equivalence against the frozen V3 submission payload (`submission_Vj_kc_v3.tar.gz`) across 100% of tested game turns.

---

## 2. Test Protocol & Environment
* **Baseline Payload**: `submission_Vj_kc_v3.tar.gz` (SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)
* **Test Adapter**: `V3BackboneAdapter` (`aec/backbone/v3_adapter.py`)
* **Test Suite**: `tests/aec/test_v26_backbone_adapters.py::test_v3_adapter_exact_equivalence`
* **Test Seed**: `249376` (50 game steps lockstep evaluation)
* **Kaggle Environment Engine**: `1.32.7`

---

## 3. Results Ledger

| Step Range | Total Turns Evaluated | Action Divergences | Market Order Divergences | Hand Alignment Divergences | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Steps 0–49** | 50 | **0** | **0** | **0** | **100% BIT-EXACT MATCH** |

### Per-Turn Action Verification:
- **Step 0 (Opening Wash)**: Both produce `[['BUY_PRODUCT', 'WHEAT', 50], ['SELL', 'WHEAT', 50]]`.
- **Steps 1–49 (Routes, Seeds, Labor)**: Exact equality on `farmer`, `hands`, and `market` lists.
- **Invariants Enforced**: Repeated call on the same step raises `RuntimeError`.
- **Identity Certified**: `V3_STANDALONE` (Version: `1.0.0-v3-frozen`).

---

## 4. Verdict
`V3BackboneAdapter` strictly preserves original V3 behavior with zero semantic degradation or state drift.
