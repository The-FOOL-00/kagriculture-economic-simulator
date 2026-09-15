# Compiled Semantic Equivalence Audit Report

**Document ID**: `research/compiled_semantic_equivalence.md`  
**Date**: 2026-09-10  
**Audit Target**: Original Modular Harnesses vs Compiled Standalone Deployment Artifacts  
- Original Control: `candidates/v54_plus_shop.py` (SHA256: `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8`)
- Compiled Control: `candidates/compiled_v54_plus_shop.py` (SHA256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`)
- Original Residual: `candidates/v54_plus_residual.py` (SHA256: `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80`)
- Compiled Residual: `candidates/compiled_v54_plus_residual.py` (SHA256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`)

---

## 1. Constants & Route Table Equivalence

| Component | Invariance Condition | Test Method | Audit Result |
| :--- | :--- | :--- | :---: |
| **`_V56_BACKBONE_ROUTE`** | Exact 719-turn action sequence equality | List item-by-item comparison | **PASS (100% Match)** |
| **`_V56_YARN_ROUTE`** | Exact 719-turn action sequence equality | List item-by-item comparison | **PASS (100% Match)** |
| **`_V58_BAKERY_YARN_ROUTE`** | Exact 719-turn action sequence equality | List item-by-item comparison | **PASS (100% Match)** |

---

## 2. Configuration & Parameter Invariance

| Configuration Parameter | Original V54++ Control | Compiled Control | Original Residual | Compiled Residual | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `front_money_deficit` | 4500.0 | 4500.0 | 4500.0 | 4500.0 | **INVARIANT** |
| `front_on_near` | True | True | True | True | **INVARIANT** |
| `preempt_enabled` | True | True | True | True | **INVARIANT** |
| `preempt_money_deficit` | **4000.0** | **4000.0** | **2000.0** | **2000.0** | **PRESERVED** |
| `preempt_minimum_delta` | **8.0** | **8.0** | **4.0** | **4.0** | **PRESERVED** |
| `preempt_maximum_batch` | **8** | **8** | **12** | **12** | **PRESERVED** |
| `preempt_horizon` | 2 | 2 | 2 | 2 | **INVARIANT** |
| Full `__dict__` Attribute Match | Match | Match | Match | Match | **100% EQUIVALENT** |

---

## 3. Route Selector & Branch Predicates

The S2 Minimal Shop Controller (`_select_route`) was tested across all possible game horizons and public shop configurations:
1. Step 0–71 with any shop combinations -> `backbone` (Match: True)
2. Step 72 with first shop `YARN_STORE` -> `yarn` (Match: True)
3. Step 72 with first shop `BAKERY` -> `backbone` (Match: True)
4. Step 144 with second shop `YARN_STORE` -> `yarn` (Match: True)
5. Step 144 with first shop `BAKERY` and second `YARN_STORE` -> `bakery` (Match: True)
6. Step 144+ with other combinations -> `backbone` (Match: True)

**Branch Predicate Verdict**: **100% IDENTICAL BEHAVIOR ACROSS ALL HORIZONS**.

---

## 4. Tactical & Terminal Realization Overlays

- **Strawberry Seed Trim (`_v60_seed_trim`)**: Unaltered implementation inlined.
- **Shed Guard (`_v60_shed_guard`)**: Unaltered implementation inlined.
- **Terminal Unit Recall (`_route_loaded_units`)**: Exact Step 713–716 access-distance routing preserved.
- **Home Convergence (`_TERMINAL_UNITS`)**: Exact Step 717–718 home pathing preserved.
- **Terminal Liquidation (`_TERMINAL_MARKET`)**: Exact Step 718 collision market dump preserved.

**Semantic Equivalence Verdict**: **PASS (ZERO DIVERGENCE)**.
