# EXP-ARCH-002 H1 — CORRECTED RE-EXECUTION FREEZE RECORD

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`  
**Document**: `08_REEXECUTION_FREEZE_RECORD.md`  
**Date**: 2026-09-16  
**Auditor / Implementer**: Antigravity  
**Status**: **CORRECTED RE-EXECUTION ENVIRONMENT FROZEN — RE-EXECUTION AUTHORIZED**  

---

## 1. MANDATORY GOVERNANCE CERTIFICATION

> **EXPLICIT GOVERNANCE STATEMENTS**:
> 1. **"Scientific protocol unchanged"**: The experimental design, hypothesis (H1-ACT, H1-OVERALL), cohort, baseline, and H1 implementation are completely unchanged.
> 2. **"Correction limited to execution integrity"**: The modification is strictly and exclusively confined to eliminating the runner-level double-call defect that caused baseline state pollution in the original run.
> 3. **Original Execution Status**: The original execution of ARCH-002 completed on 2026-09-15 across seeds 320000–320499 remains permanently recorded as:
>    `ARCH-002 ORIGINAL EXECUTION = INVALID / EXECUTION-INTEGRITY FAILURE (RUNNER STATE POLLUTION)`
>    Its raw artifacts (`RAW_RESULTS.json`, `PAIRED_DELTAS.csv`, `TELEMETRY_EVENTS.csv`, `06_EXECUTION_AND_FORENSIC_REPORT.md`) are permanently preserved and unoverwritten.
> 4. **Quarantine Confirmation**:
>    - Final virgin holdout `214200–214249` remains strictly protected, virgin, and untouched.
>    - DEV-007 cohort `310000–310499` remains completely virgin, frozen, and untouched.
>    - DEV-007 remains frozen until ARCH-002 is fully resolved.
> 5. **Prospective Cohort State**: Zero prospective performance seeds (`320000–320499`) were executed under the corrected runner prior to this freeze record. Validation was conducted strictly on non-prospective fixtures and consumed DEV-006 seeds (248000–248049).

---

## 2. ARTIFACT IDENTITIES & FROZEN HASHES

| Component | Path | SHA-256 / Commit Identity |
|---|---|---|
| **Governing Preregistration Protocol** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/02_PREREGISTRATION.md` | `508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5` |
| **Isolation Audit** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/01_ISOLATION_AUDIT.md` | `0381a93eee7cc3d51833439ce868d51923dc9a2ff0cca68f9d692e5f81c03de4` |
| **Original Implementation Freeze Commit** | Git Commit | `862e35b75e375b49cd66e85c651fc4d463fd9b1e` |
| **Governance Seal Commit** | Git Commit | `2dfeedb015bf39db2bd57fc965e3b74f8316e0a7` |
| **Re-Execution Eligibility Audit** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/07_REEXECUTION_ELIGIBILITY_AUDIT.md` | `06870a49e75790026823dda7102c44f1b7fdbec6965600b3362bf31179f60ade` |
| **Corrected Runner (P-RE-RUN)** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_reexecution.py` | `e6f830c8847985f834dd3c498537e07f20fb006494e0596773e4f09d86b6a405` |
| **Re-Execution Validation Suite** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/tests/test_h1_reexecution_validation.py` | `c3b77aaa0c042a071f1b04cd625527260979ce55d699a7a122ddb810969be348` |
| **Frozen Baseline Policy** | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` |
| **Simulator Port Engine** | `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py` | Engine 1.32.7 (port v0.4.0.port1) |
| **Protected Artifact: Shop Scheduler** | `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` |
| **Protected Artifact: Horizon Guard** | `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` |
| **Protected Artifact: Pinned Unit Model** | `extracted_agents/dmitrii_lb2800/unit_model.py` | `c03e8c5cd10466c229ee0a44dece9a3943c10bff135d96a7822ffe75d6922724` |

---

## 3. EXACT CHANGES FROM ORIGINAL RUNNER

The changes between `run_arch002_h1_execution.py` and `run_arch002_h1_reexecution.py` are strictly confined to:

1. **Elimination of the Double-Call State Pollution**:
   - In `run_single_game()`, the original runner called `base_inst_h1.call(...)` during steps $t < \text{ENTRY\_STEP}$ and steps $712 \le t < 718$ to check P-PURE identity, despite `base_inst_h1` having already been stepped inside `agent_h1()`.
   - The corrected runner instantiates an independent baseline twin instance (`base_inst_twin = load_baseline()`) in H1's seat.
   - For P-PURE identity checking, `base_inst_twin.call(obs, cfg)` is evaluated once per turn.
   - Neither mutable policy instance (`base_inst_h1`, `base_inst_twin`, `base_inst_ctrl`) is ever called twice on the same step.
2. **Dedicated Output Artifact Names**:
   - Outputs are routed to `REEXECUTION_RAW_RESULTS.json`, `REEXECUTION_PAIRED_DELTAS.csv`, `REEXECUTION_TELEMETRY_EVENTS.csv`, `REEXECUTION_EXECUTION_MANIFEST.json`, and `REEXECUTION_LOG.txt` to strictly protect the original invalid execution records from being overwritten.
3. **Purity Verification**:
   - P-PURE pre-E action identity is verified against `base_inst_twin` actions, guaranteeing that H1 pre-E actions are 100% bit-identical to an untouched baseline policy without state mutation.

---

## 4. VALIDATION RESULTS (PHASE G GATE)

The corrected runner was subjected to the complete validation suite (`test_h1_reexecution_validation.py`) and passed all 12 test suites (100%):

1. `test_quarantine_hard_abort_holdout`: **PASS** (hard-aborts on 214200, 214225, 214249).
2. `test_quarantine_hard_abort_dev007`: **PASS** (hard-aborts on 310000, 310250, 310499).
3. `test_quarantine_hard_abort_fallbacks_and_consumed`: **PASS** (hard-aborts on protected blocks).
4. `test_quarantine_hard_abort_out_of_cohort`: **PASS** (hard-aborts on out-of-cohort seeds).
5. `test_quarantine_permits_consumed_validation_flag_only`: **PASS** (permits consumed seed 248000 only when flag set).
6. `test_g_hash_verification`: **PASS** (baseline and preregistration hashes verified).
7. `test_pure_baseline_vs_pure_baseline_identity`: **PASS** (independent baseline instances produce identical actions).
8. `test_no_accidental_double_call_and_p_pure_identity`: **PASS** (zero double calls, exactly 1 call per step, 100% pre-E bit-identity across seeds 248000, 248001, 248002).
9. `test_crn_and_purity_on_consumed_seeds`: **PASS** (full CRN on seeds 248001 and 248002: pure_pre_e_pass=True, pure_step_pass=True, pure_verbatim_pass=True, delta=0.00).
10. `test_terminal_window_micro_transitions`: **PASS** (steps 710–718 verified, valid action structures, clean entry, reason recording).
11. `test_checkpoint_and_resume`: **PASS** (atomic writes, non-destructive resume, CSV formatting).
12. `test_no_network_or_kaggle_contact`: **PASS** (zero network or Kaggle imports).

In addition, all 114 unit tests in the core H1 test suite (`test_h1_conformance.py`, `test_h1_determinism.py`, `test_h1_identity.py`, `test_h1_guards.py`, `test_h1_q1_shadow.py`, `test_h1_q2_parity.py`) passed (114/114 in 63.23s).

---

## 5. RE-EXECUTION SPECIFICATION

- **Authorized Cohort**: Seeds `320000–320499` inclusive (N = 500 seeds)
- **Experimental Design**: Common Random Numbers (CRN), 2 games per seed:
  - Game a: Seat 0 = H1 treatment, Seat 1 = Baseline
  - Game b: Seat 0 = Baseline, Seat 1 = H1 treatment
- **Total Scheduled Games**: Exactly 1,000 games
- **Parallel Workers**: 4
- **Command**:
  ```bash
  python experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_reexecution.py --workers 4
  ```

---

## 6. GOVERNANCE AUTHORIZATION

All pre-execution gates (G-HASH, G-QUAR, G-IMPL, G-RUN, G-PURE) are satisfied. The corrected re-execution environment is formally frozen.
Re-execution across seeds `320000–320499` is **AUTHORIZED**.
