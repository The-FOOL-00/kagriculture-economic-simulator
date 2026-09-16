# EXP-ARCH-003_H1_TERMINAL_REPAIR — Freeze Record

**Experiment ID:** EXP-ARCH-003_H1_TERMINAL_REPAIR  
**Date Frozen:** 2026-09-16  
**Status:** FROZEN AND VALIDATED — NO PROSPECTIVE EXECUTION  
**Authorized Cohort:** Seeds `330000` to `330499` inclusive (500 seeds, 1000 CRN games)  
**Cohort Status:** 100% UNTOUCHED (0 / 500 seeds executed)  

---

## 1. Frozen Code and Test Artifacts

All files comprising the implementation, execution runner, and validation test suite of EXP-ARCH-003 are cryptographically sealed with the following SHA-256 digests:

| File Path | SHA-256 Hash | Purpose |
| :--- | :--- | :--- |
| `01_ISOLATION_AUDIT.md` | `24a964f2324ce3d9cf0569022e251eeb5e17f630a40190d4e28afa488d9d3a9a` | Isolation & Anti-Pollution Audit |
| `02_PREREGISTRATION.md` | `7aefeec68c5982b73d317661f3fa8bc2b257f84837c44e052a2b7296ddfe6f8e` | Full Preregistration & Invariant Specification |
| `03_IMPLEMENTATION_VALIDATION_REPORT.md` | `10f9df0c32b3fa169a7961f12bbd72ac7316bf0212360ca07c2c12097b2ea113` | 12-Item Micro-Validation Verification Report |
| `05_RUNNER_FREEZE_RECORD.md` | `84a5effa46fdb60527ecf93e7b6530bbfc8a169c13c9f221ea1517cf50a44d60` | Runner Architecture & Quarantine Freeze |
| `h1_const.py` | `b68976f7a4f0a0efacf4b8d79e83122bea9763a4b9fcec8aaf129d2c630902cf` | Constants, Pins, Cohort Bounds, Search Budget |
| `h1_units.py` | `06b55c0d8a37058ec91acb9783e4f2a6678e6be29c54fa608e816f0adbc594c2` | Forward Unit Simulation Engine (1.32.7 exact extract) |
| `h1_baseline.py` | `abed6ee655fb28be7edb15587f8f3bae5745254ca5e4940b130a87e5da326990` | Frozen V54++ Baseline Loader & Ledger Cloner |
| `h1_dominance.py` | `243d76b816ea692ba9ea9397f0242325546c0776effc4e5a68ca6ab1829482f6` | D5 Safety/Dominance, Economic Acceptance, Liquidation |
| `h1_shadow.py` | `86cab5d87cf35c3321828e519c9574bf87049aeebe2b2ebe00ee718545378d8b` | Forward Shadow Rollout Simulator |
| `h1_search.py` | `6827710d2ba7c282158386f7189b6c114cfd522f1f1236e30193a02bc3c271a2` | Candidate Proposal Generator & 128-Sim Search |
| `h1_telemetry.py` | `155737b0908976d66ac04b6ac541b26e12c585e7e3f05a4e92c1a8025d6b907c` | Telemetry Schemas, Enums, and Record Types |
| `h1_agent.py` | `0bc325cb560d1ab5d1220de9eb615cd7bbd31c0a2199a5f19c027f72552df0b1` | Live Agent Overlay, State Verifier, and Handshake |
| `run_arch003_execution.py` | `ece9c80f01b2c1ba1c3091a7409c26783e98810861caf431e2d652e382ff3426` | 1000-Game CRN Evaluation Runner |
| `tests/test_arch003_validation.py` | `4659c37b1ddf49da2aa1209e57123a62925f199e9ffeddf1008e3281fb104b02` | 12-Item Micro-Validation Test Suite |

---

## 2. Frozen External Baseline

- **File Path:** `candidates/compiled_v54_plus_residual.py`
- **Baseline SHA-256:** `5ef81e4b8bb26c483a65191cf078a6aafe4d8721ad30303bfa82e850b924ea10`
- **Policy Role:** Exact read-only baseline loaded for pre-E execution (steps 0–711), live baseline actions (steps 712–718 when unguided), and benchmark opponent.

---

## 3. Core Architectural Mechanisms Frozen

1. **Change 1 — Step-718 Candidate Market Liquidation:**
   - Steps 712–717: Live baseline market orders emitted verbatim.
   - Step 718: Deterministic candidate liquidation market orders generated from simulated post-worker available shed stock. SELL only, PRODUCTS_9 only, positive integer quantities, $\le 10$ orders.

2. **Change 2 — Separation of D5 Dominance and Acceptance:**
   - **D5 (Safety / Dominance):**
     1. Zero overflow on all simulated steps.
     2. Intermediate market solvency on steps 712–717 ($\text{cand\_pre\_shed} \ge \min(\text{base\_scheduled}, \text{base\_pre\_shed})$ and BUY commitments satisfied).
     3. Terminal weak dominance at step 718 (pre-market shed $\ge$, total deposits across all actors $\ge$, cumulative sold $\ge$ baseline).
     4. No-steal invariant (`no_steal_pass`).
   - **Acceptance (Economic Adoption):**
     1. `worker_changed == True`.
     2. Terminal money delta: $\text{cand\_money} - \text{base\_money} > 0$.
     3. Sold deltas: $\forall p \in \text{PRODUCTS\_9}: \Delta_{\text{sold}}(p) \ge 0$.
     4. Sales improvement: $\exists p \in \text{PRODUCTS\_9}: \Delta_{\text{sold}}(p) > 0$.
     5. Zero candidate overflow.

3. **Change 3 — Search Preservation:**
   - Exactly 128 simulations, 1 pass, $\le 8$ proposals per actor, identical proposal generator and tie-breaking.

---

## 4. Micro-Validation Status

All 12 micro-validation tests passed (12/12):
- TEST 1 (Seed 248012 activation & real gain): **PASSED**
- TEST 2 (Seed 248001 delayed deposit intermediate solvency): **PASSED**
- TEST 3 (Step-718 liquidation parity): **PASSED**
- TEST 4 (Shadow/engine reward parity): **PASSED**
- TEST 5 (No-steal collision fixture): **PASSED**
- TEST 6 (Handshake & runtime fail-closed): **PASSED**
- TEST 7 (Pure passthrough on abstain): **PASSED**
- TEST 8 (Baseline state & telemetry isolation): **PASSED**
- TEST 9 (Pre-E purity on steps 0–711): **PASSED**
- TEST 10 (Market boundary enforcement): **PASSED**
- TEST 11 (BUY safety & G4 coverage gate): **PASSED**
- TEST 12 (Forbidden mechanisms static audit): **PASSED**

---

## 5. Non-Execution Declaration

- **Prospective Seeds Run:** 0 / 500.
- **Kaggle Execution:** None.
- **Holdout Execution:** None.
- **Next Authorized Step:** Final review and freeze sign-off.
