# V45 Baseline Lock & Governance Integrity Verification Report

**Document ID:** `research/v45/reports/V45_BASELINE_LOCK.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 0 (Governance + Baseline Reproduction)  
**Formal Gate Verdict:** **PASS (100% Invariant Compliance)**  

---

## 1. Executive Summary

Phase 0 establishes the cryptographically locked foundation for the V45 research program. The objective is to verify that all protected baselines remain uncorrupted, the holdout seed quarantine is strictly enforced at runtime, and the incumbent V44 economic portfolio candidate reproduces without execution discrepancy.

A complete 128-leg paired tournament benchmark (16 seeds × 4 diverse opponents × 2 seat positions) was executed comparing V44 against the incumbent production baseline V35.

Key findings:
* **V44 Record:** 128 wins, 0 ties, 0 losses (**100.0% Win Rate**).
* **V35 Record:** 127 wins, 0 ties, 1 loss (**99.22% Win Rate**).
* **Mean Paired Cash Delta:** **+$71.16** over V35.
* **Median Paired Cash Delta:** **+$20.50** over V35.
* **Rescues:** **1 confirmed rescue** (Seed 249657 vs E2_A7 in Seat 0 rescued from loss to win).
* **Casualties:** **0 casualties** (0 losses caused by V44 where V35 had won).
* **Submissions Executed:** Exactly **0** (prohibition strictly maintained).

---

## 2. Cryptographic Governance Audit

All 6 protected baseline artifacts were hashed using SHA256 and verified bit-for-bit against their canonical definitions:

| Protected Artifact Path | Canonical SHA256 Hash | Verified Match |
| :--- | :--- | :---: |
| `candidates/v35_a7_opening/main.py` | `1959021BDB1AEFF720732AEC866F5C9F3C9FA0B259EE0AB25982BDA367593249` | **CONFIRMED** |
| `candidates/v30_a7_standalone/main.py` | `51C1D25245F68DD8DE66B355F2AD6CA1D79DE8AF02EFED521A5A82F7BE69CE3F` | **CONFIRMED** |
| `candidates/v42_alpha_residual/main.py` | `0B90784AFC8CFC66D3A947448E99CE796E5286C3E0D70F4A85B593141B24F296` | **CONFIRMED** |
| `candidates/v43_compositional_alpha/main.py` | `281ACD6961CC4172133483014FC2A47AA51341102B02FFBDCA9598CB44A92D02` | **CONFIRMED** |
| `candidates/v44_economic_portfolio/main.py` | `58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF` | **CONFIRMED** |
| `submission_aec_v22r1.tar.gz` | `6B879B3E499D2CF43B76884F6EF433479468B5C316F92CF4A8CC5119586FB3F5` | **CONFIRMED** |

Automated enforcement is permanently integrated into `research/v45/governance.py`. Any file tampering raises `BaselineIntegrityViolation` and terminates execution immediately.

---

## 3. Holdout Quarantine Enforcement

In accordance with Section 2 of the V45 specification, the following seed ranges are permanently quarantined:
* `214200–214249`
* `340090–340199`
* `249695–249734`

A hard runtime assertion guard (`assert_seed_safe(seed)`) is installed in `research/v45/governance.py` and called in every evaluation loop. Unit tests confirmed that attempting to evaluate seed `214220` immediately triggers `HoldoutQuarantineViolation` and aborts.

All 16 baseline evaluation seeds are clean DEV seeds outside the quarantine zones:
`249635, 249636, 249637, 249638, 249645, 249646, 249647, 249648, 249655, 249656, 249657, 249658, 249685, 249686, 249687, 249688`

---

## 4. V44 Baseline Reproduction Cohort (128 Paired Legs)

The 128-leg benchmark was executed across 4 opponent classes in both Seat 0 and Seat 1:
1. `E8_DMITRII`: High-rated competitive agent (32 legs)
2. `E2_A7`: Native incumbent opening and chore planner (32 legs)
3. `E0_V3`: Frozen reference agent (32 legs)
4. `SYN_AGG`: Hostile market dumping stressor (32 legs)

### Opponent Breakdown

| Opponent ID | Total Legs | V44 Wins | V35 Wins | Mean Cash Delta | Rescues | Casualties | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `E8_DMITRII` | 32 | 32 (100%) | 32 (100%) | +$64.12 | 0 | 0 | Verified |
| `E2_A7` | 32 | 32 (100%) | 31 (96.9%) | +$88.45 | 1 | 0 | Verified (Rescue) |
| `E0_V3` | 32 | 32 (100%) | 32 (100%) | +$59.38 | 0 | 0 | Verified |
| `SYN_AGG` | 32 | 32 (100%) | 32 (100%) | +$72.69 | 0 | 0 | Verified |
| **Total / Overall** | **128** | **128 (100%)** | **127 (99.2%)** | **+$71.16** | **1** | **0** | **PERFECT LOCK** |

Detailed JSON rollout records are archived at `research/v45/artifacts/baseline_v44_lock.json`.

---

## 5. Phase 0 Gate Compliance Matrix

| Requirement | Specification | Measured Value | Status |
| :--- | :--- | :--- | :---: |
| Protected Hashes | 100% unchanged | 6 / 6 verified exact match | **PASS** |
| Holdout Quarantine | 0 forbidden seed accesses | 0 accesses, runtime guard active | **PASS** |
| V44 Execution Discrepancy | No unexplained errors | 128 / 128 legs completed cleanly | **PASS** |
| Baseline Casualties | Exactly 0 | 0 casualties | **PASS** |
| Submission Commands | Exactly 0 | 0 submissions | **PASS** |

**Verdict:** Phase 0 is formally **LOCKED and PASSED**. V45 proceeds to Phase 1.
