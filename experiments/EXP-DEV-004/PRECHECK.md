# EXP-DEV-004 PRECHECK & PREFLIGHT VERIFICATION
## Pre-Simulation Formal Gate Audit for Joint Macro Production Scheduler
**Experiment Identifier**: EXP-DEV-004  
**Date**: 2026-09-14  
**Governing Protocol**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_3.md`  
**Candidate Identifier**: `dev_004_joint_macro_scheduler`  
**Certified Discovery Partition**: Seeds `246000` to `246049` ($N=50$ contiguous seeds)  
**Status**: **ALL PREFLIGHT GATES VERIFIED — PENDING USER EXECUTION AUTHORIZATION**

---

## 1. Preflight Invariant Verification Matrix

| Check ID | Verification Gate | Expected Value / Criterion | Actual Observed Value | Status | Forensic Detail |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **Check A** | Protocol Freeze & Hash | SHA-256 of `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_3.md` | `436fb79fb94ad2a05e0d01d3f16f487e51970478830d609a76f91b802e109751` | **PASS** | Bit-for-bit frozen protocol recorded on disk and hashed. |
| **Check B** | Candidate Treatment Hash | SHA-256 of `candidates/closed_loop_architecture/dev_004_joint_macro_scheduler.py` | `321fc4bd3aa3c8629a125f04edbbe0422fb0a01f8c29a530dc3c19f8f1207e25` | **PASS** | Source code frozen prior to simulation. |
| **Check C** | Authoritative Baseline Hash | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | **PASS** | Verified match for `candidates/compiled_v54_plus_residual.py` (Submission `56146971`). |
| **Check D** | AST Zero-Leakage Audit | 0 AST violations of forbidden future keys | **0 violations** | **PASS** | Verified via `audit_agent_ast()` on candidate source. |
| **Check E** | Certified Virgin Partition | Exhaustive repository scan across 2,749 files, Git history, results | **0 hits in 246000–246049** | **PASS** | Full certification recorded in `SEED_PROVENANCE.md`. |
| **Check F** | Holdout Quarantine Buffer | Distance to Final Holdout (`214200–214249`) > 30,000 seeds | **31,751 seeds** separation | **PASS** | Certified buffer maintained. |
| **Check G** | Qualification Quarantine | Protection of Qualification Partition (`50050–50099`) | Enforced via runtime assertions | **PASS** | Hard exceptions prevent execution during Discovery. |
| **Check H** | DEV-003 Isolation | Re-use of DEV-003 seeds (`245000–245049`) strictly forbidden | Excluded from seed list | **PASS** | Zero seed overlap with DEV-003. |
| **Check I** | Simulator Engine Integrity | Native C++ simulator `kagsim` loaded | C++ `kagsim` 1.32.7 operational | **PASS** | `kagsim.Game` class instantiated cleanly. |
| **Check J** | Preemption Invariant | Exact preservation of residual parameters | `deficit = 2000.0, delta = 4.0, batch = 12` | **PASS** | Preserved inside compiled baseline and candidate. |

---

## 2. Quarantine Assertions in Execution Harness

The execution runner [`run_exp_dev_004.py`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-004/run_exp_dev_004.py) includes active runtime boundary assertions:
```python
def assert_not_quarantined(seed: int):
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Virgin Holdout seed {seed} requested!")
    if 50050 <= seed <= 50099:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Qualification seed {seed} requested during Discovery!")
    if 50100 <= seed <= 50149:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Contaminated seed {seed} requested!")
    if 245000 <= seed <= 245049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-003 consumed seed {seed} requested!")
```

---

## 3. Precheck Verdict

All 10 security, provenance, and governance gates have **PASSED**.  
Simulation execution is **strictly halted** pending user review and authorization.
