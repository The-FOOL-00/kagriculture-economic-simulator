# EXP-ARCH-002 H1 — EXECUTION RUNNER FREEZE RECORD

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`  
**Document**: `05_RUNNER_FREEZE_RECORD.md`  
**Date**: 2026-09-15  
**Auditor / Implementer**: Antigravity  
**Status**: **RUNNER FROZEN — EXECUTION AUTHORIZED**  

---

## 1. Governance Certification

> **MANDATORY GOVERNANCE STATEMENT**:  
> **ZERO PROSPECTIVE ARCH-002 PERFORMANCE GAMES WERE EXECUTED PRIOR TO RUNNER FREEZE.**  
> - Prospective ARCH-002 cohort `320000–320499` (N=500 seeds, 1000 games) remains completely virgin, uninspected, and unexecuted.  
> - Final holdout `214200–214249` (N=50 seeds) remains strictly protected, untouched, and unexecuted.  
> - DEV-007 cohort `310000–310499` (N=500 seeds) remains frozen, untouched, and unexecuted.  
> - Runner validation was performed exclusively against non-prospective fixtures and consumed DEV-006 seed `248000`. Zero prospective seeds were referenced, simulated, or touched during runner validation.

---

## 2. Runner Identity & Hashes

| Artifact | Path | SHA-256 |
|---|---|---|
| **Execution Runner (P-RUN)** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_execution.py` | `1599c4bb3153bb1f798a7e0e4f3cc0255f8eb304e913357fa83d850be1551fad` |
| **Runner Validation Suite** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/tests/test_h1_runner_validation.py` | `959bacf41906964f9b3cf9fbda57d60314d87e03bf3c14d97fb72338d60ebec7` |
| **Preregistration (P-RUN Authority)** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/02_PREREGISTRATION.md` | `508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5` |
| **Implementation Freeze Record** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/04_FREEZE_RECORD.md` | `d5598ba5cb0a789228804fa1c74291c944d1871a2fe5cebf50529d3cfbe29da5` |
| **Frozen Baseline** | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` |
| **Simulator Port (`sim.py`)** | `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py/sim.py` | `28bb1857ea24c311181816e87a224a1bfa82794eb8e34898fb87d353da634e35` |
| **Simulator API (`api.py`)** | `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py/api.py` | `4826b5280ee2d631dfb738cbe22b512c0a9693eb121b6dff567b5e4c0299f0dc` |

---

## 3. Environment & Execution Specifications

- **Platform / Interpreter**: Python 3.14.3 (`win32`), pytest 9.0.3, pluggy 1.6.0
- **Simulator Port**: `kagsim_py` v0.4.0.port1 (engine 1.32.7)
- **Authorized Cohort**: Seeds `320000–320499` inclusive (N = 500 seeds)
- **Design**: Paired Common Random Numbers (CRN), 2 games per seed:
  - Game a: Seat 0 = H1 treatment, Seat 1 = Baseline
  - Game b: Seat 0 = Baseline, Seat 1 = H1 treatment
- **Total Prospective Games**: Exactly 1,000 games
- **Execution Command**:
  ```bash
  python experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_execution.py --workers 4
  ```

---

## 4. Runner Validation Summary (Phase C)

- **Total Tests Executed**: 10
- **Passed**: 10 (100%)
- **Failed**: 0
- **Runtime**: 6.13s
- **Verified Capabilities**:
  - G-QUAR quarantine hard-abort on Final Holdout (`214200–214249`), DEV-007 (`310000–310499`), fallbacks, benchmarks, and out-of-cohort seeds.
  - G-HASH pre-execution bit-level verification.
  - Paired CRN structure (Game a + Game b, seat-swapping, delta arithmetic).
  - P-PURE validation (steps 0–711 action bit-identity, non-activated step identity, verbatim markets 712–717).
  - Atomic persistence (`RAW_RESULTS.json`, `PAIRED_DELTAS.csv`, `TELEMETRY_EVENTS.csv`) and deterministic resume idempotency.
  - Network and Kaggle isolation verified.
