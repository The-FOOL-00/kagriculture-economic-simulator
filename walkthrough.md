# Walkthrough: AEC Phase 002B — Resource Micro-Validation
## Preregistered Empirical Micro-Validation: `RESOURCE_CONVERSION` & `EMERGENCY_FEED_PURCHASE`

### Executive Summary

We have completed **Phase 002B: Preregistered Micro-Validation for `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE`**.

This phase executed a controlled, deterministic evaluation on historical/development replays to establish empirical safety and mechanism isolation before any prospective cohort trials.

### Authoritative Scientific Governance:
- **Strictly Non-Prospective:** Zero prospective tournament cohorts or leaderboard submissions executed.
- **Zero Parameter Tuning:** No parameters or thresholds were tuned against replay outcomes.
- **Protected Holdout Partition:** Seeds `340050–340199` (150 seeds) and Gate 0.3 Holdout `214200–214249` (50 seeds) remain **100% untouched and unexecuted (0 accesses)**.
- **Historical Experiments:** Cohorts `EXP-AEC-001` (`340000–340049`), `EXP-AEC-002` (`340200–340249`), and `EXP-AEC-003` (`340250–340299`) remain frozen and untouched.
- **Frozen Control Backbone SHA-256:** `submission_Vj_kc_v3.tar.gz` verified byte-identical (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
- **Quarantine Invariance:** Both mechanisms remain strictly **QUARANTINED** in `aec/config.py`.

---

### 1. Empirical Replay Experiment Summary

The micro-validation protocol was preregistered in [`reports/AEC_RESOURCE_MICROVALIDATION_PREREG.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_RESOURCE_MICROVALIDATION_PREREG.md) prior to executing replay matches.

- **Replay Population:** Historical/Development Benchmark Partition `50000–50024` ($N = 25$ seeds $\times$ 2 seats $\times$ 4 arms = 200 matches = 144,000 turn evaluations).
- **Experimental Arms:**
  - Arm A (`CONTROL`): Baseline V3 + AEC Market Timing (both resource mechanisms quarantined).
  - Arm B (`RESOURCE_CONVERSION_ONLY`): Arm A + `RESOURCE_CONVERSION` unquarantined.
  - Arm C (`EMERGENCY_FEED_ONLY`): Arm A + `EMERGENCY_FEED_PURCHASE` unquarantined.
  - Arm D (`COMBINED_RESOURCE`): Arm A + both resource mechanisms unquarantined.

#### Empirical Results Overview:
| Metric | Arm A (`CONTROL`) | Arm B (`RESOURCE_CONVERSION`) | Arm C (`EMERGENCY_FEED`) | Arm D (`COMBINED`) |
| :--- | :---: | :---: | :---: | :---: |
| Matches / Turns | 50 / 36,000 | 50 / 36,000 | 50 / 36,000 | 50 / 36,000 |
| Mean Margin ($) | **+$86.92** | **+$86.92** | **-$313.32** | **-$313.32** |
| Total Candidates | 1,685 | 101,551 | 6,187 | 106,053 |
| Candidates Passing Safety | 664 | 40,972 | 3,524 | 43,832 |
| Candidates Failing Safety | 1,021 | 60,579 | 2,663 | 62,221 |
| Total Commits | **78** | **78** | **90** | **90** |
| - *Market Timing Commits* | 78 | 78 | 78 | 78 |
| - *Resource Conversion Commits* | 0 | **0** | 0 | **0** |
| - *Emergency Feed Commits* | 0 | 0 | **12** | **12** |
| Mean Latency (ms/step) | 1.14 ms | 9.19 ms | 1.54 ms | 10.01 ms |
| p95 Latency (ms/step) | 3.57 ms | 17.07 ms | 4.73 ms | 19.60 ms |

---

### 2. Scientific Diagnoses & Empirical Findings

1. **`RESOURCE_CONVERSION`: 100% Fail-Closed Safe, Incomplete Action Synthesis**
   - Evaluated 101,551 candidates across 50 matches; 40,972 passed safety, 60,579 failed safety (capacity/liquidity checks).
   - Commits = **0**.
   - Root cause: In [`aec/patches/generator.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/patches/generator.py#L229), `RESOURCE_CONVERSION` candidates set `conversion_metadata` without populating physical market or worker mutations. Under counterfactual simulation, this null-action patch matched baseline exactly ($0.0$ margin advantage), correctly triggering `NO_CANDIDATE_CERTIFIED_SUPERIOR` (33,499 abstentions).
   - Status: Safe, non-regressive, fail-closed, but action synthesis pipeline lacks discrete execution semantics.

2. **`EMERGENCY_FEED_PURCHASE`: Active Commits, Terminal-Blind Defect Discovered**
   - Evaluated 6,187 candidates; 3,524 passed safety; committed 12 times across 6 distinct seeds.
   - Mid-game executions (e.g. Step 252, Step 368) successfully resolved feed deficits.
   - **Terminal Failure:** On Seeds 50004, 50013, 50018 at Step 697 (23 turns before final step 720), the feed security monitor flagged a feed deficit under active `E8_TERMINAL_TRANSITION` and purchased wheat. With insufficient time remaining for livestock to produce harvestable yields, these purchases wasted liquid cash and degraded terminal margins (Arm C mean margin dropped to `-$313.32`, with Seed 50004 dropping by `-$3,388.00`).
   - Conformance: **Failed preregistered Case EF-9** (terminal-aware logic must prevent pointless near-terminal purchases).

---

### 3. Readiness Classifications

Pursuant to Section 21 of the scientific mandate:
- **`RESOURCE_CONVERSION`:** **`INCONCLUSIVE / DEVELOPMENT ONLY`** (Quarantined)
- **`EMERGENCY_FEED_PURCHASE`:** **`NOT_READY`** (Quarantined)
- **Controlled Prospective Trial Ready:** **NO** (Neither mechanism is ready for prospective cohort evaluation).
- **Both mechanisms remain in QUARANTINE in `aec/config.py`.**

---

### 4. Verification Suite & Artifacts

- **Full Pytest Regression Suite:** **257 / 257 Passed** in 0.83s:
  - 233 baseline regression tests.
  - 24 new adversarial micro-validation cases ([`tests/aec/test_resource_micro_validation_cases.py`](file:///c:/Users/Sundareswaran/Kagriculture/tests/aec/test_resource_micro_validation_cases.py)) covering all mandated cases RC-1 to RC-12 and EF-1 to EF-12.
- **Determinism Check:** 5 repeated evaluations of Seed 50007 confirmed bit-for-bit identical decisions, candidate counts, and margin ($7.00).
- **Reports Created:**
  - [`reports/AEC_RESOURCE_MICROVALIDATION_PREREG.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_RESOURCE_MICROVALIDATION_PREREG.md) (Preregistration protocol)
  - [`reports/AEC_RESOURCE_MICROVALIDATION_RESULTS.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_RESOURCE_MICROVALIDATION_RESULTS.md) (Empirical replay results)
  - [`reports/AEC_RESOURCE_MICROVALIDATION_AUDIT.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_RESOURCE_MICROVALIDATION_AUDIT.md) (Invariant & attribution audit)
  - [`reports/AEC_RESOURCE_MICROVALIDATION_READINESS.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_RESOURCE_MICROVALIDATION_READINESS.md) (Readiness classification)
- **Git Commit:** `a38f8a6` (`test(aec): micro-validate resource conversion and emergency feed purchase`).
