# EXP-ARCH-002 H1 — IMPLEMENTATION VALIDATION REPORT

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`  
**Document**: `03_IMPLEMENTATION_VALIDATION_REPORT.md`  
**Date**: 2026-09-15  
**Auditor / Implementer**: Muse Spark 1.3 Max  
**Authority**: `01_ISOLATION_AUDIT.md` (ISOLATION PASS) and `02_PREREGISTRATION.md` (FREEZE-READY)  
**Readiness Verdict**: **FREEZE-READY**  

---

## 1. Executive Summary

ARCH-002 H1 (Dominance-Gated Terminal Optimizer) has been implemented strictly under one-factor discipline and evaluated against a comprehensive 20-item validation battery comprising 163 automated unit, property, and adversarial tests.

- **Automated Tests Executed**: 163
- **Passed**: 163 (100%)
- **Failed**: 0
- **Execution Time**: 85.30s (Python 3.14.3 win32)
- **Protected File Integrity**: 100% bit-exact match across all frozen live artifacts, holdout partitions, and upstream protocols.
- **Prospective Performance Execution**: **ZERO prospective ARCH-002 performance games were executed.**
  - ARCH-002 prospective cohort `320000–320499` remains completely virgin and unexecuted.
  - DEV-007 cohort `310000–310499` remains frozen and unexecuted.
  - Final holdout `214200–214249` remains untouched.
  - Q2 validation used already-consumed DEV-006 seeds `248000–248049` solely for baseline/implementation parity validation; those validation replays were not used for performance estimation, tuning, seed selection, candidate selection, or protocol modification.
- **Verdict**: **FREEZE-READY**.

---

## 2. Files Created and Architecture

All implementation artifacts reside strictly within `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/`. No frozen live files were modified.

### Implementation Modules

| File | Description | Lines | SHA-256 |
|---|---|---|---|
| `h1_const.py` | Frozen constants, pins, whitelist, search budget, enums (D1–D8) | 76 | `080d0992ff1235dddbcf1be5bd0d5eb7a9c0eaf533ef0f725941f39ba226479c` |
| `h1_units.py` | Engine-exact unit/decay shim re-exporting `unit_model.py` (v1.32.7) | 65 | `9100029a1eac43d8cac527f79b33c865233435f52fd40f18e931278468fc8033` |
| `h1_baseline.py` | Frozen baseline loader, live config checks, unbound controller access | 289 | `20e7728f196228a022e762b7490b2081085f4ed639b48adecc810c1d2a0e4e58` |
| `h1_dominance.py` | Row-wise prefix dominance, strict gain, no-steal, BUY coverage gate | 208 | `37d36383f32f68d7a437331a709d07bcbe0ac2a88cf9265fa9ea36e26c623a23` |
| `h1_search.py` | Proposal generator, worker-by-worker search, frozen budget cap (128/1/8) | 292 | `1d476f7d7292f5f8af13ced0133b99f0dbb0e10499c64a5bd850ae394bbdaf9b` |
| `h1_shadow.py` | Shadow simulator, cloned ledgers, transition exactness, baseline replay | 488 | `8857a671e6d510ddb44957126b6839584d4264fc8d20f56ab94d7f9ea046055b` |
| `h1_telemetry.py` | Frozen 15-code reason enum, U-SEL structured sub-field schema, records | 133 | `dd7c9aa3a45fc0dea0b020d56b7c9368d071e9ae9f0e031e0026d228a4c6b31c` |
| `h1_agent.py` | H1 agent wrapper, G0–G7 entry guards, stepwise re-verification, fallback | 403 | `06aa31c72ea8c9740be2568810b7ade17edee1827e779b88cceddda70a40f4ae` |

### Test Suite (`tests/`)

| File | Focus Area | Test Count | SHA-256 |
|---|---|---|---|
| `conftest.py` | Shared fixtures, synthetic observations, tile helpers | - | `d12e5178c3afd095d7d8d7ff8792e88660e9807b92f0c4795fe3624c79deea09` |
| `test_h1_adversarial.py` | Adversarial Tests A through J | 28 | `8e7d5e7225f9a819cfd84c768bd2c48c9a81a6a363c1c9191fe0ec64b1fbbf0c` |
| `test_h1_conformance.py` | D1–D8 static conformance, G-IMPL forbidden checks, hash verification | 32 | `f7e55c5f74dca6d989b8a1dac58650ad52607ed4f1d2157d9d6b9e69b19928b5` |
| `test_h1_determinism.py` | Replay invariance, state determinism, proposal order stability | 5 | `e69c62ea1725b67aa5e15f3057fd26f9e07551e2fffee57741d5ac403cd37513` |
| `test_h1_fert_sparse_drop.py`| Fertilizer flag checks, sparse-market admission, DROP capacity overflow | 9 | `2d94f0d7b5b991705004afff71b400413b8c6afcdc7bc995a4eda17c07e8facc` |
| `test_h1_fronting_flow.py` | Fronting / flow ledgers, repay carry, near streak mirroring | 7 | `ba619a3a4bed0ffc8f22e0e66053318ff89b5813a9f77db8055d06eeb6f3653d` |
| `test_h1_guards.py` | Entry guards G0–G7, fail-safe abstention paths, reason code fidelity | 23 | `9e0abcc8302360ca997a81ac5881207ed935665fc870e6cbebf979d0e8af40ac` |
| `test_h1_identity.py` | Pre-entry identity (steps 0–711), post-window passthrough, reset on rewind | 21 | `d23f45aca808a9186e562f7ab88f7b7adf06f877e3ee351cf219d115ad24312f` |
| `test_h1_q1_shadow.py` | Micro-state transitions vs engine port (actions, decay, deposits, markets) | 28 | `8a3688217fd19bf43397e595195a5e4beba4d7196ca7be504698af888c1dbaac` |
| `test_h1_q2_parity.py` | Consumed cohort baseline parity (seeds 248000–248049), zero adoptions on split | 5 | `723a748442fb05cee99cce69b73c41bca6ee4cf8bca3f0697e882d4bcf97ec7b` |
| `test_h1_search_budget.py` | Simulation cap (≤128), per-worker cap (≤8), fixed proposal order | 5 | `17c47fe127f3856a55e3e72155e8118b16c87562c23f2d5ece1dec154ac3ade7` |
| **Total** | | **163** | |

---

## 3. Preregistered Decision Conformance (D1–D8)

| Decision | Preregistered Requirement | Implementation Mapping & Evidence | Status |
|---|---|---|---|
| **D1** | Whitelist: `{N,S,E,W,HARVEST,COLLECT_FERTILIZER,DROP,PASS}`, DROP-only (no PLACE), COLLECT under entry-flagged only, emission schema aligned | `h1_const.py:20–25`, `h1_search.py:39–53`, `h1_agent.py:177–187`. Tested in `test_h1_conformance.py` (`test_d1_*`). | **CONFORMANT** |
| **D2** | Entry step: `E = 712` (7-turn window 712–718) | `h1_const.py:12–15`, `h1_agent.py:113,123`. Tested in `test_h1_conformance.py:75–80`. | **CONFORMANT** |
| **D3** | Step-718 market rule: Verbatim baseline passthrough downstream of `terminal_market`. No live market recompute. | `h1_agent.py:351–358`, `h1_shadow.py:266–292`. Tested in `test_h1_adversarial.py` (Test G). | **CONFORMANT** |
| **D4** | Search: Mirror Dmitrii `_proposals`/`plan_terminal` (128 sims, 1 pass, ≤8 proposals/worker); offsets 0–6; carry-closure + top-6 singles + top-3×top-3 pairs; 2 direct reserves; frozen entry prices. | `h1_search.py:69–173,175–292`, `h1_const.py:26–34`. Tested in `test_h1_search_budget.py`. | **CONFORMANT** |
| **D5** | Dominance: Row-wise prefix dominance + strict value gain + two no-steal gates + acceptance conjunction + markets-verbatim cert; BUY_PRODUCT modeled with entry-money coverage gate ($125/unit worst case). | `h1_dominance.py:53–74,77–90,92–115,123–161,164–175,205–208`. Tested in `test_h1_adversarial.py` (Tests A–F). | **CONFORMANT** |
| **D6** | Determinism: Strict `>` everywhere; integer set inclusion; frozen sort keys; last strictly improving wins; fixed worker/offset order; float expression order fixed. | `h1_dominance.py:45–50,77–90`, `h1_search.py:141,165–172,222–226`. Tested in `test_h1_determinism.py`. | **CONFORMANT** |
| **D7** | Abstention: 8 entry guards (G0–G7) + stepwise re-verification + non-consecutive abandonment + abandon-to-baseline (no salvage mode) + frozen 15-code reason enum + U-SEL schema. | `h1_agent.py:180–326,329–378`, `h1_telemetry.py:12–29,58–79`. Tested in `test_h1_guards.py`. | **CONFORMANT** |
| **D8** | Baseline identity: `candidates/compiled_v54_plus_residual.py` SHA `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`. Hash verified at import and execution. | `h1_baseline.py:42–47,72–82`, `h1_const.py:59–62`. Tested in `test_h1_conformance.py:160–202`. | **CONFORMANT** |

---

## 4. Adversarial Test Battery Results (Handoff §27)

| Test ID | Adversarial Scenario | Expected Outcome | Observed Result | Status |
|---|---|---|---|---|
| **Test A** | Candidate has greater terminal value but violates row-wise prefix dominance | `REJECT` (`dominates() == False`, `ABSTAIN_DOMINANCE`) | Rejected immediately; prefix violation mid-window caught at row index 2; live baseline emitted. | **PASS** |
| **Test B** | Candidate physically dominates but provides equal or negative value (strict gain fails) | `REJECT` (`ABSTAIN_NO_GAIN`) | Ties fail strict `>`; `ABSTAIN_NO_GAIN` recorded; zero candidates adopted. | **PASS** |
| **Test C** | Candidate steals another worker's planned harvest or fertilizer acquisition | `REJECT` (`ABSTAIN_NOSTEAL`) | No-steal gate detects missing/short cell acquisition for other actors; candidate discarded. | **PASS** |
| **Test D** | Candidate requires BUY WHEAT without sufficient entry-money coverage ($125/unit) | `REJECT` (`ABSTAIN_BUY_COVERAGE`) | G4 gate evaluates required coverage ($125 × U); insufficient funds trigger fail-safe abstention. | **PASS** |
| **Test E** | Candidate triggers invalid fronting / flow state or divergent repay carry | `REJECT` / exact ledger match | Cloned ledgers simulate flow/near-streak/repay bit-identically to live controller; deviations abandon. | **PASS** |
| **Test F** | Candidate exceeds DROP capacity (overflow > 0) | `REJECT` (`dominates() == False`) | Overflow units counted; candidate with overflow=1 rejected even when stock value is superior. | **PASS** |
| **Test G** | Candidate attempts market mutation before Step 718 | `REJECT` (`markets_verbatim() == False`, `_emit` enforces live) | Element-wise market check fails; `_emit` constructs market strictly from live baseline. | **PASS** |
| **Test H** | Repeated identical simulations from identical states | Bit-identical output & telemetry | Plan SHA-256 and scrubbed telemetry match across runs; proposal sorting is fully deterministic. | **PASS** |
| **Test I** | Physical state or predicted baseline action disagrees with live execution | `ABANDON_MISMATCH_T` | Mismatch on step t abandons plan; emits live baseline action; forgets plan permanently. | **PASS** |
| **Test J** | Barren state where no candidate is valid | Exact baseline continuation | `ABSTAIN_NO_GAIN` emitted; plan rejected; actions equal baseline verbatim. | **PASS** |

---

## 5. Simulator-Equivalence & Fidelity Battery (Handoff §33)

1. **Source & Schema Validation**: Passed. All 8 modules conform to frozen constants and schemas.
2. **D1 Conformance**: Passed. Whitelist and emission schemas validated statically and dynamically.
3. **D2 Entry Validation**: Passed. E=712 verified; pre-entry turns pass through untouched.
4. **D3 Step-718 Validation**: Passed. Verbatim passthrough confirmed; no market recompute executed.
5. **D4 Search Validation**: Passed. Budget caps (128/1/8) enforced; proposal generation exact.
6. **D5 Dominance Validation**: Passed. Row-wise prefix dominance, no-steal, and acceptance conjunction validated.
7. **D6 Deterministic Selection**: Passed. Total ordering on proposals; strict `>` ties.
8. **D7 Fail-Safe Validation**: Passed. G0–G7 guards fail closed to baseline; no salvage mode exists.
9. **D8 Baseline Identity**: Passed. Hash `18402ec6…` confirmed bit-identical.
10. **Shadow / Live Equivalence (Q1 & Q2)**:
    - **Q1 (Micro-transitions)**: 28 hand-constructed state transitions compared against port step function; 100% agreement on moves, crops, animal yield, deposits, shed capacity, and decay.
    - **Q2 (Consumed Cohort Parity)**: Replayed pure baseline self-play on consumed DEV-006 seeds `248000–248049` (N=4 seeds, 8 seats). Handshake and prediction agreement checked; zero adoptions on disagreeing trajectories. These replays are classified strictly as validation-only replay on already-consumed cohorts, completely distinct from prospective performance execution.
11. **BUY WHEAT Tests**: Passed. Maximum price on curve proven to be $125; coverage gate verified.
12. **Fronting / Flow Tests**: Passed. Near streak, near latched, opponent supply, and repay carry mirrored exactly.
13. **No-Steal Tests**: Passed. Multi-worker ownership conflict detection validated.
14. **DROP Tests**: Passed. Shed capacity overflow destroys units in engine and causes dominance failure in H1.
15. **Sparse-Market Tests**: Passed. Admitted without reshaping to fixed 9-product vectors.
16. **Fertilizer Boundary Tests**: Passed. Unflagged tiles rejected; reaped fertilizer counted in telemetry.
17. **Pre-Terminal Identity Tests**: Passed. Steps 0–711 bit-identical between H1 and baseline.
18. **Deterministic Replay**: Passed. 10 identical runs produced 10 identical SHA-256 plan digests.
19. **Search-Budget Enforcement**: Passed. Hard stop at 128 simulations; per-worker proposal cap ≤ 8.
20. **Protected-Artifact Hash Check**: Passed. All 6 protected files match their canonical SHA-256 hashes.

---

## 6. Discrepancies, Fixes, and Adjudications

### Discrepancy 1: FERTILIZER BUY Coverage vs WHEAT Curve
- **Observation**: Preregistration §8.2/H2 derives `$125/unit` coverage from the WHEAT curve maximum. FERTILIZER quotes can theoretically reach $2,100/unit under zero inventory.
- **Resolution**: `h1_agent.py` G3 implements a conservative fail-closed check: any baseline schedule containing `BUY_PRODUCT FERTILIZER` raises `ABSTAIN_MARKET_OP`.
- **Impact**: Zero in live V54++ (all window BUYs in live routes are WHEAT). Safe conservative extension.

### Minor Test Fix: Windows Subprocess Handle Inheritance
- **Observation**: `test_h1_determinism.py` `_probe_digest` invoked `subprocess.run` without explicit `stdin`. In non-interactive Windows background tasks without console standard handles, `_winapi.DuplicateHandle` raised `OSError: [WinError 6] The handle is invalid`.
- **Fix**: Added `stdin=subprocess.DEVNULL` to `subprocess.run` call in `test_h1_determinism.py:53`. All 5 tests now pass cleanly in 6.46s.

---

## 7. Protected File and Repository Integrity

All protected artifact hashes were recomputed and verified bit-identical:

```
candidates/compiled_v54_plus_residual.py:
  18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb [MATCH]
candidates/compiled_v54_plus_shop.py:
  f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8 [MATCH]
candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py:
  f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78 [MATCH]
candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py:
  06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb [MATCH]
experiments/EXP-DEV-007_MECHANISM_EXPOSURE/PROTOCOL.md:
  d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff [MATCH]
extracted_agents/dmitrii_lb2800/unit_model.py:
  c03e8c5cd10466c229ee0a44dece9a3943c10bff135d96a7822ffe75d6922724 [MATCH]
```

### Governing Document Hashes
```
experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/01_ISOLATION_AUDIT.md:
  0381a93eee7cc3d51833439ce868d51923dc9a2ff0cca68f9d692e5f81c03de4 [MATCH]
experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/02_PREREGISTRATION.md:
  508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5 [MATCH]
```

---

## 8. Remaining Unknowns (Pre-Execution Status)

1. **U10 (Natural Activation Rate)**: Empirically unknown on prospective cohort `320000–320499`. By preregistered design, this is measured by main-run telemetry, not estimated by pre-execution scouting.
2. **U11 (Live Environment Parity)**: Standing program caveat regarding subtle engine edge cases; closed by fail-safe abandon-to-baseline re-verification.
3. **P-PERF (Runtime Overhead)**: Observed average planning time is ~15–35 ms per seat at Step 712 on consumed seeds, well within Kaggle's per-step limits.

---

## 9. Final Readiness Verdict

**VERDICT: FREEZE-READY**

The H1 implementation satisfies all 24 preregistered requirements, complies with all G-IMPL and G-SIM constraints, passes all 163 unit and adversarial validation tests, preserves all frozen hashes, and executes zero performance seeds. The implementation is ready for formal freeze.

---

## 10. Execution Classification & Governance

This document explicitly certifies the critical distinction between prospective performance execution and historical validation replay:

1. **Zero Prospective Performance Execution**:
   - Prospective ARCH-002 cohort `320000–320499` (N=500 seeds) is completely virgin, unexecuted, and uninspected.
   - DEV-007 cohort `310000–310499` (N=500 seeds) remains frozen, untouched, and unexecuted.
   - Final holdout `214200–214249` (N=50 seeds) remains strictly protected and untouched.

2. **Classification of Q2 Parity Replays**:
   - Q2 evaluated 4 seeds (8 seats) drawn strictly from the already-consumed DEV-006 cohort `248000–248049`.
   - These replays were executed offline solely to verify shadow baseline prediction parity against live baseline execution.
   - Zero Q2 validation results were used for performance estimation, threshold setting, parameter tuning, seed scouting, candidate selection, or protocol modification.
   - Q2 replays are classified as **VALIDATION-ONLY / CONSUMED-COHORT REPLAY** and do not constitute prospective performance evidence.
