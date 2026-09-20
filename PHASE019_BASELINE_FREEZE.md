# PHASE019 BASELINE FREEZE

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Status**: FROZEN (pre-treatment)

---

## 1. V3 Chassis Integrity

| Field | Value |
| :--- | :--- |
| Tarball | `submission_Vj_kc_v3.tar.gz` |
| Expected SHA256 | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| Actual SHA256 (`sha256sum`) | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| Verdict | **PASS — byte-identical** |

Verified 2026-09-20 before any Phase019 edit. Immutability guaranteed.

---

## 2. Git Provenance

| Field | Value |
| :--- | :--- |
| HEAD | `d89ab7480d02f3661b0a3e749518c7236f907a7c` (`phase018-final-report`) |
| Branch | `main` (ahead of `origin/main` by 50 commits; no push authorized) |

### 2.1 Working-Tree State at Freeze
- Tracked modifications vs HEAD:
  - `aec/counterfactual/horizon.py` (+macro escalation parameter)
  - `aec/counterfactual/simulator.py` (+V3 dynamic continuation & divergence telemetry)
  *Note*: Both files contain the authoritative Phase016 macro-aware evaluator implementation preserved cleanly across Phase016, Phase017, and Phase018.
- 0 diffs in `aec/counterfactual/` semantics vs Phase016 baseline.

---

## 3. Live Empirical Foundation (Control, Unchanged)

```text
V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN
```

- Constructor: `aec.config.build_robust_qualified_config()` (`frozen_mode=True`, `enable_asset_holding_trigger=False`, `enable_tranche_synthesizer=False`).
- `ENABLED_FOUNDATION_MECHANISMS` = the 3 mechanisms above.
- Live foundation remains strictly unmodified.

---

## 4. Phase016 Macro-Aware Evaluator Baseline

| Component | Location | Freeze Status |
| :--- | :--- | :--- |
| `MacroRegimeTransitionDetector` | `aec/counterfactual/macro_detector.py` | Present, 0 diff |
| `MacroRegimeFingerprint` | `aec/counterfactual/macro_detector.py` | Present, 0 diff |
| `V3ContinuationPolicy` | `aec/counterfactual/v3_continuation.py` | Present, 0 diff |
| `select_adaptive_horizon` | `aec/counterfactual/horizon.py` | Present, 0 diff |
| Probe + escalation wiring | `aec/integration/executor.py` §6 | Present, 0 diff |
| Exact state snapshot/restore | `aec/counterfactual/v3_continuation.py` | Verified byte-identical |

Phase019 will NOT modify, weaken, bypass, or shortcut the Phase016 evaluator.

---

## 5. Phase018 Final Status & Adopted Infrastructure

Phase018 evaluated funnel reservation, boundary-safe quantities, and trigger variants across 260 CRN mirror matches:
- **Funnel Reservation (`enable_funnel_reservation`)**: Rescued foundation selection from crowding out (0 → 14 commits on fresh cohort); adopted as flag-gated infrastructure.
- **Market Patch Discrimination (`enable_market_patch_discrimination`)**: Unlocked multi-candidate exact evaluation by removing S7 dominance collapse; adopted as research infrastructure.
- **Boundary-Safe Quantities**: Falsified (near-gate safe sales sub-hurdle by construction; missing large anchor in tails).
- **Trigger Variants**: Null / vacuous / negative.
- **Phase015 Tranche Mechanism**: Remains negative across all fresh cohorts (-$1,311 Arm A; -$1,228 B2; -$636 Arm C). Confirmed in scientific quarantine.

---

## 6. Current Decision Policy & Limits

- **Simulation Budget**: `max_simulations = 8`, `max_candidates = 8`.
- **Hurdle**: `delta_terminal_margin > 15.0` (or `delta_our_money > 20.0` with non-negative margin).
- **WinModel**: Sigmoid heuristic `1.0 / (1.0 + exp(-projected_margin / 1000.0))`. Strictly monotonic in projected margin.
- **Commit Gate**: Greedy max-select among certified candidates:
  `if cert.commit_decision and (best_eval_result is None or eval_res.expected_p_win > best_eval_result.expected_p_win)`
- **Abstention**: Occurs when no candidate satisfies safety, hurdle, and authorization checks.

---

## 7. Test Baseline

| Metric | Value |
| :--- | :--- |
| Test suite | `tests/aec/` |
| Runner | Windows CPython 3.14.3, pytest 9.0.3 |
| Result | **765 passed, 0 failed, 0 skipped** (3.31s) |

---

## 8. Reserve Seeds Status

- Phase017 cohort: `249286..249295` (consumed)
- Phase018 cohorts: `249296..249335` (consumed)
- Phase019 prospective reserve begins at: **`249336`** (untouched)
