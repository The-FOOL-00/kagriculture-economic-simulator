# EXP-ARCH-003_H1_TERMINAL_REPAIR — Isolation and Safety Audit

**Date:** 2026-09-16  
**Status:** PASSED AND VERIFIED  
**Experiment ID:** EXP-ARCH-003_H1_TERMINAL_REPAIR  
**Successor To:** EXP-ARCH-002_H1_DOMINANCE_TERMINAL (permanently frozen)  

---

## 1. Directory and Workspace Isolation

1. **Independent Experiment Directory:**
   - Location: `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/`
   - Complete self-contained implementation: `h1_const.py`, `h1_units.py`, `h1_baseline.py`, `h1_dominance.py`, `h1_shadow.py`, `h1_search.py`, `h1_telemetry.py`, `h1_agent.py`, `run_arch003_execution.py`, and test suite `tests/test_arch003_validation.py`.
   - No symlinks, shared mutable singletons, or dependencies on ARCH-002 runtime files.

2. **Pristine Immutability of Historical Artifacts:**
   - `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/`: Completely untouched and unmodified.
   - `experiments/EXP-DEV-007_H1_REAP_FERRY_OPTIMIZER/`: Completely untouched and unmodified.
   - Historical records, forensic audits, and test fixtures remain pristine.

3. **Cohort Isolation and Quarantine:**
   - Authorized cohort: `330000–330499` (500 seeds, 1000 CRN games).
   - Current execution status: **ZERO PROSPECTIVE SEEDS EXECUTED**.
   - Prospective directory `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/results/` is currently uncreated / empty.
   - Final holdout seeds (`214200–214249`) are completely untouched and strictly quarantined.
   - Micro-validation utilized strictly historical/consumed development seeds (`248012`, `248001`).

---

## 2. Baseline Immutability and State Isolation

1. **Baseline Identity and Verification:**
   - Reference Baseline: `V54++` (`candidates/compiled_v54_plus_residual.py`).
   - Baseline SHA-256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`.
   - Verified at every startup by `h1_baseline.py:load_baseline()`. If the file hash deviates, execution fails immediately.

2. **Controller Ledger and Telemetry Isolation:**
   - Live baseline policies maintain route state, telemetry call counts, and ledgers across steps 0–711.
   - At step 712, `fb.clone_ledgers(route, seat)` performs a deep copy of route state, pending orders, and route priors.
   - Shadow search and rollout roll over isolated cloned ledgers in `h1_shadow.py`.
   - `test_8_policy_isolation` verifies that 128 shadow simulations produce **zero** mutations in the live baseline controller's `telemetry["calls"]`, `states`, or `ledgers`.

3. **No Baseline Double-Call Defect in Runner:**
   - The runner `run_arch003_execution.py` executes each agent once per turn per seat:
     `action = agents[p](obs_p, configuration)`
   - The baseline baseline-vs-baseline and treatment-vs-baseline games invoke the baseline controller exactly once per step per baseline seat.
   - The treatment agent `H1Overlay` invokes the baseline controller internally once per step, clones ledgers before the call, and caches actions cleanly.

---

## 3. Fail-Closed Behavioral Guarantees

1. **Pre-E Exact Baseline Identity (Steps 0–711):**
   - For all steps $t < 712$, `H1Overlay.act` bypasses all candidate logic and calls `self.fb.call(obs, configuration)` directly.
   - Verified by `test_9_pre_e_purity`: actions on steps 0–711 are bit-identical to the unadorned baseline.

2. **Handshake Verification at Entry (Step 712):**
   - G0: Board size (10), turns per day (24), episode steps (720), shed capacity (100), max market orders (10).
   - G1: Shed non-negative integers, total shed $\le 100$.
   - G2: Inventory shapes match worker count, no unsupported product items.
   - G3: No weed-blocked operations, valid market orders on 712–717, empty pending ledger, no BUY FERTILIZER.
   - G4: G4-pre and post-rollout buy coverage gate verified (`money >= required(buy_units)`).
   - G5: Live baseline action at step 712 matches shadow baseline action at step 712 across `farmer`, `hands`, and `market`.
   - Any failure raises `H1Abstain` with specific error codes (`ABSTAIN_CONFIG`, `ABSTAIN_SHED`, `ABSTAIN_ITEMS`, `ABSTAIN_WINDOW_OPS`, `ABSTAIN_MARKET_OP`, `ABSTAIN_BUY_COVERAGE`, `ABSTAIN_HANDSHAKE`).
   - If aborted, `H1Overlay` emits the live baseline action verbatim.

3. **Stepwise Physical Re-verification (Steps 713–718):**
   - At every step $t \in [713, 718]$, `_verify_and_emit` compares the observed physical state (`farmer`, `hands`, `shed`, `inventories`, `prices`) against the candidate's forward-simulated state `expected_states[t - 712]`.
   - If any discrepancy is detected (e.g. unexpected tile collision, opponent theft, or market divergence), the plan is immediately aborted (`ABANDON_MISMATCH_T`), the plan is removed, and the live baseline action is emitted.
   - If a step is skipped or nonconsecutive, the plan is immediately aborted (`ABANDON_NONCONSECUTIVE`).
   - Verified by `test_6_handshake_fail_closed`.

---

## 4. Forbidden Mechanisms Static Audit

1. **Static AST & Content Inspection:**
   - Audited all files in `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/` for forbidden residual logic.
   - Forbidden:
     - `step == 500` / `H=500` checkpoint logic: **ABSENT**.
     - Checkpoint step $\le 288$ early interventions: **ABSENT**.
     - Expanded fertilizer application outside baseline routes: **ABSENT**.
     - Speculative market modifications on steps 712–717: **ABSENT**.
     - BUY orders at step 718: **ABSENT**.
     - Arbitrary search expansions beyond 128 simulations: **ABSENT**.
   - Verified by `test_12_forbidden_mechanisms_static_audit`.

---

## 5. Audit Sign-off

- **Workspace Status:** Pristine.
- **Isolation Check:** 100% Passed.
- **Network / External Dependencies:** Zero. Local deterministic execution only.
