# Walkthrough: EXP-AEC-004 Preregistration & Prospective Trial Infrastructure

## Emergency Feed Purchase Isolated Prospective Validation

### Executive Summary

We have completed the formal preregistration and trial execution infrastructure for **`EXP-AEC-004`**, the isolated prospective evaluation of `EMERGENCY_FEED_PURCHASE` within the Kagriculture Adaptive Economic Compiler (AEC) architecture.

This protocol builds directly upon:
1. **EXP-AEC-003 Prospective Validation:** Confirmed that `DEPENDENCY_AWARE_MARKET_TIMING` achieves statistical superiority against frozen V3 ($+\$57.36$ margin delta, $+56.00\text{ pp}$ win-rate delta).
2. **Phase 002C Terminal Remediation:** Excision of arbitrary economic thresholds (`$150.00` buffer and `-$50.00` margin degradation gate) and replacement with exact, game-derived obligation schedules $R(t)$ and causal purpose analysis.
3. **Quarantine Discipline:** `RESOURCE_CONVERSION` remains strictly quarantined awaiting Phase 003 Multi-Worker Logistics. This trial evaluates `EMERGENCY_FEED_PURCHASE` in complete isolation.

---

### Authoritative Scientific Governance Conformance:
- **Strictly Non-Prospective in this Phase:** Zero prospective matches executed on seeds `340300–340349`.
- **Zero Arbitrary Tuning:** Protocol frozen prior to observing any treatment outcomes.
- **Protected Holdout Covenant:**
  - Primary Locked Holdout (`340050–340199`, 150 seeds): **100% untouched (0 touches)**, separated by 101 seeds.
  - Secondary Locked Holdout (`214200–214249`, 50 seeds): **100% untouched (0 touches)**.
- **Historical Experiments Preserved:** `EXP-AEC-001`, `EXP-AEC-002`, and `EXP-AEC-003` archives intact.
- **Frozen V3 Chassis SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` byte-identical.
- **Quarantine Invariance:** `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE` remain quarantined in standard `aec/config.py`.

---

### 1. Key Artifacts Established

1. **Preregistration Protocol:**
   - [`reports/EXP_AEC_004_EMERGENCY_FEED_PREREGISTRATION.md`](file:///C:/Users/Sundareswaran/Kagriculture/reports/EXP_AEC_004_EMERGENCY_FEED_PREREGISTRATION.md)
   - Binding protocol `PREREG-EXP-AEC-004-20260918-FINAL` specifying hypotheses ($H_0: \mu_\Delta < \$0.00$ vs $H_1: \mu_\Delta \ge \$0.00$), paired mirror CRN design ($N = 50$, 100 matches), 8 hard acceptance gates, and fail-closed stopping invariants.

2. **Independent Cohort Audit:**
   - [`reports/EXP_AEC_004_COHORT_AUDIT.md`](file:///C:/Users/Sundareswaran/Kagriculture/reports/EXP_AEC_004_COHORT_AUDIT.md)
   - Certified seeds `340300–340349` as 100% virgin with zero prior executions, zero development exposures, and strict separation from holdouts.

3. **Prelaunch Scientific Audit:**
   - [`reports/EXP_AEC_004_PRELAUNCH_AUDIT.md`](file:///C:/Users/Sundareswaran/Kagriculture/reports/EXP_AEC_004_PRELAUNCH_AUDIT.md)
   - Certified 16/16 prelaunch gates passed. Verified single-mechanism isolation matrix.

4. **Execution Manifest & Immutable Configurations:**
   - [`experiments/EXP-AEC-004/CONFIG_CONTROL.json`](file:///C:/Users/Sundareswaran/Kagriculture/experiments/EXP-AEC-004/CONFIG_CONTROL.json) (Control: validated AEC baseline, feed quarantined)
   - [`experiments/EXP-AEC-004/CONFIG_TREATMENT.json`](file:///C:/Users/Sundareswaran/Kagriculture/experiments/EXP-AEC-004/CONFIG_TREATMENT.json) (Treatment: validated AEC baseline + feed active, conversion quarantined)
   - [`experiments/EXP-AEC-004/EXECUTION_MANIFEST.json`](file:///C:/Users/Sundareswaran/Kagriculture/experiments/EXP-AEC-004/EXECUTION_MANIFEST.json) (Status: `FROZEN_NOT_LAUNCHED`)
   - [`experiments/EXP-AEC-004/PRELAUNCH_CHECKLIST.md`](file:///C:/Users/Sundareswaran/Kagriculture/experiments/EXP-AEC-004/PRELAUNCH_CHECKLIST.md)

5. **Fail-Closed Runner & Preflight Harness:**
   - [`experiments/EXP-AEC-004/run_experiment.py`](file:///C:/Users/Sundareswaran/Kagriculture/experiments/EXP-AEC-004/run_experiment.py)
   - Single-process sequential execution with preflight verification, multi-layer quarantine assertion, atomic checkpointing, and developmental smoke testing.

6. **Automated Isolation Test Suite:**
   - [`tests/aec/test_exp_aec_004_isolation.py`](file:///C:/Users/Sundareswaran/Kagriculture/tests/aec/test_exp_aec_004_isolation.py)
   - 7 automated tests verifying mechanism isolation, resource conversion quarantine, cohort disjointness, V3 hash, manifest integrity, and runner holdout guards.

7. **Readiness & Freeze Certification:**
   - [`reports/EXP_AEC_004_READINESS.md`](file:///C:/Users/Sundareswaran/Kagriculture/reports/EXP_AEC_004_READINESS.md)

---

### 2. Verification Results

| Test Category | Command | Result | Details |
| :--- | :--- | :---: | :--- |
| **Isolation Test Suite** | `pytest tests/aec/test_exp_aec_004_isolation.py -v` | **7 / 7 PASSED** | All isolation invariants certified |
| **Full Regression Suite** | `pytest tests/ -q` | **297 / 297 PASSED** | 0 regressions across full codebase |
| **Runner Preflight** | `python run_experiment.py --preflight-only` | **PREFLIGHT_PASS: TRUE** | Hash and config consistency certified |
| **Runner Halting Mode** | `python run_experiment.py` | **EXECUTION HALTED** | Fails closed without execution directive |
| **Development Smoke Test** | `python run_experiment.py --smoke-only --smoke-seed 50015` | **SMOKE_TEST_PASS: TRUE** | 4 feed rescues in Treat, 0 in Ctrl, 0 safety violations |

---

### 3. Statutory Readiness Classification

**`READY FOR SEPARATE PROSPECTIVE EXECUTION`**
