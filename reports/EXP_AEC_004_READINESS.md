# EXP-AEC-004 Prelaunch Readiness & Protocol Freeze Certification

**Document Identifier:** `CERT-EXP-AEC-004-20260918-FINAL`  
**Mechanism Evaluated:** `EMERGENCY_FEED_PURCHASE` (Isolated)  
**Lead Validation Engineer & Architect:** Principal AEC Architect & Scientific Validation Engineer  
**Date Established:** 2026-09-18  
**Statutory Status:** **FROZEN PROTOCOL — READY FOR SEPARATE PROSPECTIVE EXECUTION**  
**Prospective Execution Directive:** **EXECUTION STRICTLY HALTED IN THIS TASK.**  

---

## 1. Executive Certification

The preregistration protocol and execution infrastructure for **EXP-AEC-004** have been fully drafted, audited, implemented, and verified against all statutory governance invariants.

### Statutory Verdict: **READY FOR SEPARATE PROSPECTIVE EXECUTION**

Every required audit, manifest, isolation guard, and preflight check has passed:
1. **Zero Prospective Matches Executed:** Exactly 0 matches have been simulated or executed on prospective seeds `340300–340349`.
2. **Zero Holdout Touches:** Primary Holdout `340050–340199` (150 seeds) and Secondary Holdout `214200–214249` (50 seeds) remain 100% untouched and unexecuted (0 touches).
3. **Exact Single-Mechanism Isolation:** Treatment differs from Control by **EXACTLY ONE** mechanism: `EMERGENCY_FEED_PURCHASE`.
4. **Strict Quarantine Invariant:** `RESOURCE_CONVERSION` is strictly quarantined in both Control and Treatment awaiting Phase 003 Multi-Worker Logistics Coordination.
5. **Frozen V3 Chassis Integrity:** `submission_Vj_kc_v3.tar.gz` verified bit-exact against SHA-256 `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
6. **No Live Config Alteration:** `aec/config.py` retains `EMERGENCY_FEED_PURCHASE` and `RESOURCE_CONVERSION` in `QUARANTINED_MECHANISMS`.
7. **Development Smoke Validation Passed:** Single-match smoke test on development seed `50015` executed with bit-exact determinism, 4 treatment feed rescues, 0 control feed commits, 0 safety violations, and verified counterfactual fidelity.

---

## 2. Experimental Architecture & Pre-Declared Parameters

| Parameter | Specification | Verification Evidence | Status |
| :--- | :--- | :--- | :---: |
| **Experiment ID** | `EXP-AEC-004` | `experiments/EXP-AEC-004/EXECUTION_MANIFEST.json` | **VERIFIED** |
| **Binding Protocol** | `PREREG-EXP-AEC-004-20260918-FINAL` | `reports/EXP_AEC_004_EMERGENCY_FEED_PREREGISTRATION.md` | **VERIFIED** |
| **Primary Question** | Non-inferior terminal margin delta ($\mu_\Delta \ge \$0.00$) under exact mechanism isolation | Section 1.2 of Preregistration Protocol | **VERIFIED** |
| **Cohort Seeds** | `340300–340349` ($N = 50$ contiguous seeds) | `reports/EXP_AEC_004_COHORT_AUDIT.md` | **VERIFIED VIRGIN** |
| **Cohort Selection Rule** | First $N=50$ contiguous block following consumed cohort `340250–340299` | Section 3.3 of Preregistration Protocol | **VERIFIED** |
| **CRN Structure** | Mirror seat pairing: Match A (Treat P0 vs Ctrl P1), Match B (Ctrl P0 vs Treat P1) | 100 total matches, 71,900 turns | **VERIFIED** |
| **Control Agent** | Validated AEC baseline (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`) | `experiments/EXP-AEC-004/CONFIG_CONTROL.json` | **VERIFIED** |
| **Treatment Agent** | Validated AEC baseline + `EMERGENCY_FEED_PURCHASE` enabled | `experiments/EXP-AEC-004/CONFIG_TREATMENT.json` | **VERIFIED** |
| **Mechanism Difference** | Exactly `EMERGENCY_FEED_PURCHASE` | `test_exp_004_mechanism_isolation` passed | **VERIFIED ISOLATED** |
| **Quarantined Pass** | `RESOURCE_CONVERSION` strictly quarantined | `test_exp_004_resource_conversion_quarantine` passed | **VERIFIED QUARANTINED** |
| **Primary Acceptance Gate**| One-sided lower 95% Student-$t$ bound for $\mu_\Delta \ge \$0.00$ | Section 2.4 & Section 6.1 of Protocol | **VERIFIED** |
| **Secondary Safeguard** | Win-rate delta $\Delta \text{WinRate} \ge -2.0\text{ percentage points}$ | Section 2.5 of Protocol | **VERIFIED** |
| **Hard Safety Gates** | 0 safety violations, 0 shed overflows ($>100$), 0 unquarantined commits | Section 6.1 of Protocol | **VERIFIED** |
| **Execution Harness** | Fail-closed sequential single-process runner | `experiments/EXP-AEC-004/run_experiment.py` | **VERIFIED** |

---

## 3. Cryptographic Artifact Hash Ledger

| Artifact Entity | Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :---: |
| **V3 Backbone Tarball** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | **EXACT MATCH** |
| **AEC Configuration** | `aec/config.py` | `8989283ca8f528d38b74203cf0e8239c242ae0bf6f0d9ee779e59b91141131f6` | **EXACT MATCH** |
| **Control Configuration** | `experiments/EXP-AEC-004/CONFIG_CONTROL.json` | `858b59ad0ab02ca6ae3d3e506fb1c517f29fe8c3088f4315c2e741e95231ed74` | **FROZEN** |
| **Treatment Configuration**| `experiments/EXP-AEC-004/CONFIG_TREATMENT.json` | `56256ef2d1befea4461e2d1f55ce72e0642958ade8313e1e344418856b801fe3` | **FROZEN** |
| **Execution Manifest** | `experiments/EXP-AEC-004/EXECUTION_MANIFEST.json` | `74d11d5f2f68399d6e8b59b6a82cdf76c2f6a29333fa04c798089a8b6bf64cd5` | **FROZEN** |
| **Runner Script** | `experiments/EXP-AEC-004/run_experiment.py` | `0b1c528a96c6fbe67df922d638a244e8f149887b3ade4ce05a08e0c63359696e` | **FROZEN** |
| **Preregistration Protocol**| `reports/EXP_AEC_004_EMERGENCY_FEED_PREREGISTRATION.md` | `5c738e4a2d339dae4fecae0f32997e06a3861845bb02e822a1ce09eb11c0f757` | **FROZEN** |
| **Cohort Audit** | `reports/EXP_AEC_004_COHORT_AUDIT.md` | `7d596c1dce034b2d8495b0aaee9ecf81ae33110210fa25dc642672562ef42c55` | **FROZEN** |
| **Prelaunch Audit** | `reports/EXP_AEC_004_PRELAUNCH_AUDIT.md` | `a58885660d6f7ad3f1b1cb32f320847f62634daf65f990ead1481a7cee73bc32` | **FROZEN** |

---

## 4. Verification Suite & Empirical Preflight Proof

1. **Unit & Isolation Verification Suite:**
   - [`tests/aec/test_exp_aec_004_isolation.py`](file:///C:/Users/Sundareswaran/Kagriculture/tests/aec/test_exp_aec_004_isolation.py): **7 / 7 passed** in 13.06s.
   - Entire AEC Test Suite: **297 / 297 passed** in 14.25s (`pytest tests/ -q`).
2. **Harness Preflight Check:**
   - Command: `python experiments/EXP-AEC-004/run_experiment.py --preflight-only`
   - Result: `PREFLIGHT_PASS: TRUE` (All cryptographic hashes and isolation bounds verified).
3. **Harness Halting Invariant Check:**
   - Command: `python experiments/EXP-AEC-004/run_experiment.py`
   - Result: `STATUS: FROZEN_NOT_LAUNCHED (EXECUTION HALTED)` (Clean zero exit).
4. **Development-Only Smoke Test Proof:**
   - Command: `python experiments/EXP-AEC-004/run_experiment.py --smoke-only --smoke-seed 50015`
   - Output:
     - Match A (Seat 0 Treatment vs Seat 1 Control): Margin `-$8.00`, 2 feed rescues, 0 control feed commits, mean latency 2.10ms, max latency 30.51ms.
     - Match B (Seat 1 Treatment vs Seat 0 Control): Margin `-$8.00`, 2 feed rescues, 0 control feed commits, mean latency 2.07ms, max latency 28.48ms.
     - Result: `SMOKE_TEST_PASS: TRUE`. Zero safety violations, zero shed overflows, exact mechanism isolation verified.

---

## 5. Execution Handoff & Launch Command

The prospective trial is fully prepared and frozen. It must only be executed under separate authorization by invoking:

```powershell
python experiments/EXP-AEC-004/run_experiment.py --authorized-execute-prospective-cohort
```

Until that separate task is invoked:
**NO PROSPECTIVE MATCHES MAY BE EXECUTED.**

---

READY FOR SEPARATE PROSPECTIVE EXECUTION
