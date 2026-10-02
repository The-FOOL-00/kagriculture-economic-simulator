# PHASE018 BASELINE FREEZE

**Phase**: PHASE018 — Targeted Candidate-Funnel Repair & Boundary-Safe Tranche Construction
**Date**: 2026-09-19
**Status**: FROZEN (pre-treatment)

---

## 1. V3 Chassis Integrity

| Field | Value |
| :--- | :--- |
| Tarball | `submission_Vj_kc_v3.tar.gz` |
| Expected SHA256 | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| Actual SHA256 (`sha256sum`) | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| Verdict | **PASS — byte-identical** |

Verified 2026-09-19 before any Phase018 edit. Must be re-verified after execution.

## 2. Git Provenance

| Field | Value |
| :--- | :--- |
| HEAD | `4361700dc064d7027072530864872fc2c0b1d0b3` (`phase015-final-report`) |
| Branch | `main` (ahead of `origin/main` by 39 commits; no push authorized) |

### 2.1 Working-tree state at freeze

- `git diff` (raw): 469 files differ, dominated by **CRLF line-ending normalization noise**
  (worktree CRLF vs blob LF; `core.autocrlf` unset).
- `git diff -w` (real content delta vs HEAD): **4 tracked files**, which constitute the
  uncommitted Phase016 implementation delta:
  - `aec/counterfactual/horizon.py` (+adaptive horizon selection)
  - `aec/counterfactual/simulator.py` (+V3 continuation / divergence telemetry)
  - `aec/integration/executor.py` (+macro probe integration / escalation telemetry)
  - `aec/market/tranche_synthesizer.py` (+atomic order partitioning fix)
- **Untracked** Phase016/017 additions (102 untracked paths total, selected):
  - `aec/counterfactual/macro_detector.py` (MacroRegimeTransitionDetector)
  - `aec/counterfactual/v3_continuation.py` (V3ContinuationPolicy)
  - `tests/aec/test_phase016_macro_regime.py`
  - `tests/aec/test_phase017_counterfactual_fidelity.py`
  - `scripts/run_phase016_pilot.py`, `scripts/run_phase017_attribution_audit.py`
  - `results/PHASE016_PILOT_*.json/csv`, `results/PHASE017_ATTRIBUTION_*`
  - `PHASE016_*.md`, `PHASE017_*.md` reports

Phase018 commits must be path-isolated (new files + Phase018-owned edits only) and must
not sweep the pre-existing CRLF noise or Phase016/017 uncommitted work into scope.

## 3. Live Empirical Foundation (control, unchanged)

```text
V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN
```

- Constructor: `aec.config.build_robust_qualified_config()` (`frozen_mode=True`,
  `enable_asset_holding_trigger=False`, `enable_tranche_synthesizer=False`).
- `ENABLED_FOUNDATION_MECHANISMS` = the 3 mechanisms above. No change in Phase018.

## 4. Phase016 Evaluator (authoritative, must remain intact)

| Component | Location | Freeze status |
| :--- | :--- | :--- |
| `MacroRegimeTransitionDetector` | `aec/counterfactual/macro_detector.py` | present, unmodified by Phase018 |
| `MacroRegimeFingerprint` | `aec/counterfactual/macro_detector.py` | present, unmodified by Phase018 |
| `V3ContinuationPolicy` | `aec/counterfactual/v3_continuation.py` | present, unmodified by Phase018 |
| `select_adaptive_horizon` | `aec/counterfactual/horizon.py` | present, unmodified by Phase018 |
| Probe + escalation wiring | `aec/integration/executor.py` §6 | present, unmodified by Phase018 |
| `test_phase016_macro_regime.py` | `tests/aec/` | passing (in 714) |
| `test_phase017_counterfactual_fidelity.py` (7/7) | `tests/aec/` | passing (in 714) |

Phase018 must not modify, bypass, or weaken any of the above.

## 5. Phase017 Treatment Configuration (diagnostic baseline)

- Constructor: `aec.config.build_phase015_treatment_config()`
  (`RESEARCH_MODE`, `frozen_mode=False`, both Phase015 flags True).
- Mechanisms: foundation + `ASSET_HOLDING_VALUATION_TRIGGER` +
  `AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER`, evaluated under the Phase016 macro-aware
  evaluator with exact state restoration and safety certificate.

## 6. Phase015 Quarantine (verified)

- `AECConfig` defaults: `enable_asset_holding_trigger=False`,
  `enable_tranche_synthesizer=False`.
- `build_robust_qualified_config()` and `build_research_full_config()` both leave
  Phase015 flags False; only the explicit `build_phase015_treatment_config()` opts in.
- Phase015 mechanisms participate solely in isolated experimental arms.

## 7. Test Baseline

| Field | Value |
| :--- | :--- |
| Runner | Windows CPython 3.14.3, pytest 9.0.3 (`PYTHONPATH=external_repos/kaggriculture-cppsim;.`) |
| Note | Linux `python3` cannot import the `cp314-win_amd64` `kagsim` extension; the Windows interpreter is the canonical runner for sim-dependent tests and all pilots |
| Result | **714 passed, 0 failed, 0 skipped** (2.37 s) |

## 8. Reproduced Phase017 Telemetry Summary

Source artifacts (read-only, not regenerated):
`results/PHASE016_PILOT_SUMMARY.json`, `results/PHASE017_ATTRIBUTION_SUMMARY.json`,
`PHASE017_FINAL_REPORT.md`.

| Metric | Value |
| :--- | :--- |
| Cohort | fresh seeds `249286..249295` (20 CRN mirror matches) |
| Mean paired terminal-margin delta | **-$884.20** |
| 95% CI | [-$1,493.73, -$274.67] |
| Record | 1W / 9L / 0T |
| Worst seed | `249292` (-$2,159); best `249291` (+$54) |
| Proposed / simulated / escalated / committed | 6,508 / 2,082 / 736 / 54 |
| `AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER` | 6,206 candidates / 52 commits / -$884.20 net |
| `DEPENDENCY_AWARE_MARKET_TIMING` | 44 candidates / 2 commits / +$3.18 net |
| Measured overblocking | 0% (0 false rejections) |
| Macro escalation precision / recall | 98.10% / 100% |
| Seed 249288 funnel-crowding loss | -$1,561 (0 treatment commits; foundation +$1,485 commit displaced) |
| Safety violations | 0 |
| Mean / p95 / max latency | 75.17 / 205.63 / 377.18 ms |

A live re-execution reproducibility check (`scripts/run_phase018_baseline_repro.py` →
`results/PHASE018_BASELINE_REPRO_*`) was executed from this frozen state:

| Check | Phase017 record | Re-execution | Verdict |
|---|---|---|---|
| Candidates / sims / esc / commits | 6508 / 2082 / 736 / 54 | 6508 / 2082 / 736 / 54 | **exact** |
| O1 / O2 / O3 / O4 | 410 / 394 / 124 / 400 | 410 / 394 / 124 / 400 | **exact** |
| Precision (722/736) | 98.10% | 98.10% | **exact** |
| All 10 paired seed margins | — | identical incl. 249288 (-$1,561), 249292 (-$2,159) | **exact** |

**Baseline REPRODUCIBLE.** The re-execution ran with Repair A code present but
default-off, additionally proving Repair A does not perturb legacy behavior at
full-match fidelity. Treatment experiments are unblocked.

## 9. Seed Governance for Phase018

| Class | Seeds |
| :--- | :--- |
| Protected (never touch) | `214200..214249`, `340050..340199`, `340300..340349` |
| Consumed (never reuse) | `249000..249230`, `249231..249240` (G3 pilot), `249241..249275` (P14), `249276..249285` (P15), `249286..249295` (P16/P17) |
| **Phase018 fresh pilot cohort** | **`249296..249305`** (10 seeds, 20 mirror matches per arm; verified zero prior references in workspace) |
| Reserve (do not use unless arm rerun required) | `249306..249315` |

## 10. Freeze Declaration

Baseline state above was verified before any Phase018 treatment edit. Treatment
experiments (Arms A/B/C/D) may proceed only against the frozen foundation, the frozen
Phase016 evaluator, and the preregistered fresh cohort `249296..249305`.
