# EXP-AEC-003 — Formal Scientific Audit Decision

**Experiment Identifier:** `EXP-AEC-003`  
**Protocol Specification:** `PREREG-EXP-AEC-003-20260917-FINAL`  
**Cohort Range:** Seeds `340250–340299` ($N=50$, 100 matches, 71,900 steps)  
**Baseline Backbone:** Frozen V3 (`submission_Vj_kc_v3.tar.gz`, SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Auditor:** Independent Scientific Audit Agent  
**Date of Decision:** 2026-09-17  

---

## 1. Official Audit Decision

```
================================================================================
                    CRITICAL AUDIT DECISION CERTIFICATION

      VERDICT: [ B. VALID WITH QUALIFICATIONS ]
      STATUS:  ACCEPTED AS EMPIRICAL EVIDENCE FOR AEC MARKET TIMING
================================================================================
```

The claimed primary result of EXP-AEC-003:
- **Mean Paired Margin Delta:** **+$57.36**
- **Directional Lower 95% Bound:** **+$23.17**
- **One-Sided Paired $t$-Test:** **$t = 2.8124, p = 0.003527$**
- **Win-Rate Delta:** **+56.00 percentage points** (Treatment: 75%, Control: 19%, Ties: 6%)
- **Ties-Excluded Win Rate:** **79.79%**
- **Commits:** **140 / 140 (100%)** `DEPENDENCY_AWARE_MARKET_TIMING`
- **Counterfactual Fidelity:** **100% VERIFIED**
- **Safety Regressions:** **0**
- **Quarantined Commits:** **0**
- **Holdout Touches:** **0** (Seeds 340050–340199 100% untouched)

is certified as **causally sound, statistically reproduced, and scientifically valid evidence** demonstrating that `DEPENDENCY_AWARE_MARKET_TIMING` improves performance over frozen V3 on the prospective evaluation cohort.

---

## 2. Definitive Audit Findings

1. **Execution Purity & Clean Start Certified**:
   - Initial launch (Attempt 1) crashed after 761ms on Match 1 due to an unhandled `AttributeError` in the runner's logging assertion logic (`CandidateTelemetry` vs `SafetyCertificate`).
   - Zero matches were completed and zero results were recorded during Attempt 1.
   - All 5 generated partial files were purged via `Remove-Item`, the manifest was restored from git HEAD, preflight re-passed, and Attempt 2 executed all 100 matches cleanly from scratch.
   - 100% of all 100 completed matches were executed by a single, immutable runner version: **Runner Version B** (`sha256: 9463d9bbc4c4357ed06793f911bea71d0697f68c6c15229db3e13cf758361cab`).

2. **Causal Attribution to Market Timing Isolated**:
   - All 140 commits across 45 active seeds are strictly intra-basket order reorderings (`DEPENDENCY_AWARE_MARKET_TIMING`).
   - Zero farmer or worker movements were altered. Zero orders were added or removed.
   - `FRONTLOAD_ORDERS` remained completely quarantined (0 commits).
   - In 140/140 commits, predicted `delta_money` matched realized `delta_money` with $0.00 error.

3. **Bit-for-Bit Statistical Reproduction**:
   - Every metric in `SUMMARY.json` was independently reconstructed directly from `RAW_RESULTS.json` with zero discrepancies.
   - Wilcoxon signed-rank test confirms median superiority at $p = 1.35 \times 10^{-5}$.
   - BCa 10,000-resample bootstrap interval [+$31.36, +$129.85] lies strictly above zero.

4. **Holdout & Integrity Invariants Preserved**:
   - The 150-seed holdout (`340050–340199`) was audited across all raw results, checkpoints, logs, and telemetry: **Total holdout execution count = 0**.
   - Zero seed numbers or hardcoded hacks exist in the AEC codebase.

---

## 3. Specific Qualifications to the Verdict

While the experimental result is accepted as valid empirical evidence, the following four qualifications are formally placed on record:

### Qualification 1: Runner Execution Restart Governance
The initial execution crash required editing line 374 of `run_experiment.py` outside of a prior git commit tag to resolve an object attribute lookup in telemetry assertions. Although forensic analysis proves that Attempt 1 completed 0 matches, that Attempt 2 was started from a 100% clean state, and that all 100 matches were executed under Runner Version B, future protocols must enforce that runner scripts are committed and tagged in git before any preflight or execution command is issued.

### Qualification 2: Passive Status of Defense Mechanisms
`TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` were enabled in the treatment configuration as defense-in-depth, but recorded **0 commits** across the entire 100 matches. Their passivity was caused by baseline V3 leaving zero unharvested crop or shed residual at terminal steps. Consequently, this experiment provides empirical validation **only** for `DEPENDENCY_AWARE_MARKET_TIMING`. The defense mechanisms remain unvalidated in prospective competition.

### Qualification 3: Telemetry Field Overloading during Quarantine Interception
In `aec/integration/executor.py`, on steps where quarantined mechanisms (specifically `LOCAL_WEED_DIG`, 1,265 occurrences) were detected and rejected, the telemetry field `committed_mechanism` was populated with the name of the rejected mechanism while setting `decision = "ABSTAIN"` and executing the unpatched baseline. While zero quarantined actions were executed, this field overloading created potential ambiguity in raw telemetry inspection.

### Qualification 4: Non-Generalization to External Competitors
This experiment certifies that `DEPENDENCY_AWARE_MARKET_TIMING` produces a $+57.36$ margin advantage against frozen baseline V3 on this seed distribution. It does **not** guarantee top-10 leaderboard rank, nor does it establish robust dominance against adversarial opponent behaviors (e.g. aggressive weeding, resource starvation, animal rushes) that were not present in the V3 self-play baseline.

---

## 4. Final Sign-Off

The audit is complete. EXP-AEC-003 is certified as **VALID WITH QUALIFICATIONS**.

In accordance with Section 25 (Stop Rule):
- No further experiments may be launched.
- No tuning of AEC may occur.
- Holdout seeds remain strictly locked.
- Next steps await explicit user review.
