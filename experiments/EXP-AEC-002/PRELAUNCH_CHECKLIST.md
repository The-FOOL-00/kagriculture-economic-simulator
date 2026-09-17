# EXP-AEC-002 Prelaunch Governance Checklist

**Experiment ID:** `EXP-AEC-002`  
**Protocol Document:** `reports/EXP_AEC_002_PREREGISTRATION_FINAL.md`  
**Execution Manifest:** `experiments/EXP-AEC-002/EXECUTION_MANIFEST.json`  
**Verification Date:** 2026-09-17  
**Governance Authority:** Scientific Governance & Implementation Agent  

All checklist items below have been audited against physical files, test execution outputs, and git commit history. All items must evaluate to **TRUE** before explicit user execution authorization may be granted.

---

## 1. Governance & Cohort Verification Checklist

- [x] **EXP-AEC-001 cohort excluded**  
  *Evidence:* Seeds `340000–340049` are officially registered as `HISTORICAL / CONSUMED` in `reports/EXP_AEC_002_COHORT_AUDIT.md` and excluded from the prospective protocol.
  
- [x] **New 50-seed cohort verified untouched**  
  *Evidence:* Exhaustive regex scan of the workspace and git log pickaxe search confirmed **0 prior occurrences** of seeds `340200–340249`.

- [x] **New cohort not holdout**  
  *Evidence:* AEC locked holdout partition is `340050–340199`. Seed range `340200–340249` is contiguous and strictly disjoint ($\min(\text{Cohort}) = 340200 > 340199 = \max(\text{Holdout})$).

- [x] **New cohort not development-used**  
  *Evidence:* 0 occurrences of seeds `340200–340249` across all development scripts, unit tests, mock fixtures, and parameter sweeps.

- [x] **Holdout untouched**  
  *Evidence:* Seeds `340050–340199` have 0 execution records in any result file or runner log.

- [x] **V3 hash exact**  
  *Evidence:* Cryptographic SHA-256 of `submission_Vj_kc_v3.tar.gz` verified as `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.

- [x] **`LOCAL_WEED_DIG` quarantined**  
  *Evidence:* Registered as `ScientificStatus.QUARANTINED` in `aec/config.py`. Emits `decision="ABSTAIN"` with `abstain_reason="SCIENTIFIC_QUARANTINE"` and returns the exact baseline action.

- [x] **All other quarantined families blocked**  
  *Evidence:* `QUARANTINED_MECHANISMS` in `aec/config.py` explicitly enumerates all 7 quarantined families: `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`, `EMERGENCY_FEED_PURCHASE`, `TERMINAL_HARVEST_SWEEP`, `TOWN_CYCLE`.

- [x] **`FRONTLOAD_ORDERS` exact two-phase parity verified**  
  *Evidence:* Ground-truth lockstep fixture verified in `tests/aec/test_v1_1_development_fixes.py`: $\Delta M_{\text{our}} = +\$31$, $\Delta M_{\text{opp}} = -\$30$, $\Delta \text{Margin} = +\$61$.

- [x] **110+ tests passing after final modifications**  
  *Evidence:* Pytest run executed: 110 passed in 0.79s across the entire AEC test suite.

- [x] **Treatment configuration hash frozen**  
  *Evidence:* Canonical JSON SHA-256 hash of `AECConfig` is `db59108d29241534cde9d9a12bdc93c588800be7ad7ec2838cee09efdea5721c`, recorded in manifest.

- [x] **Preregistration document frozen**  
  *Evidence:* Final protocol completed and frozen at `reports/EXP_AEC_002_PREREGISTRATION_FINAL.md`.

- [x] **Execution manifest says `FROZEN_NOT_LAUNCHED`**  
  *Evidence:* `experiments/EXP-AEC-002/EXECUTION_MANIFEST.json` contains `"execution_status": "FROZEN_NOT_LAUNCHED"`.

- [x] **No seeds executed**  
  *Evidence:* 0 matches executed, 0 prospective seeds simulated, zero output CSVs/JSONs generated for `EXP-AEC-002`.

- [x] **No outcome-driven tuning performed**  
  *Evidence:* All thresholds, horizons, opportunity limits, and candidate search limits are fixed in advance prior to execution.

---

## 2. Authorization Status

```
===============================================================================
PRELAUNCH AUDIT VERDICT: ALL 15 CRITICAL GOVERNANCE GATES PASSED
CURRENT STATE: PROTOCOL SEALED — FROZEN_NOT_LAUNCHED
AWAITING EXPLICIT USER AUTHORIZATION BEFORE ANY EXECUTION
===============================================================================
```
