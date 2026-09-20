# PHASE 021: ACTION-SPACE COMPLETENESS AUDIT

**Date**: 2026-09-20  
**Phase**: PHASE021 — AEC Capability, Action-Space & Dependency Completeness Audit  
**Chassis Ground Truth**: `sim.hpp`, `kagsim.cpp`, `aec/patches/generator.py`, `aec/patches/coupled_patch.py`  

---

## 1. Executive Summary

This audit assesses the completeness of the AEC action-space representation across 7 core economic sequences. It evaluates whether AEC can (A) represent, (B) simulate exactly, (C) execute cleanly, (D) evaluate downstream consequences, and (E) safely recover if an intervention goes awry.

A candidate is **not** actionable merely because a local patch can trigger the first action. If the architecture cannot represent the subsequent closure operations (e.g. transit to shed and deposit), the action composition is incomplete and dangerous.

---

## 2. Action Sequence Completeness Matrix

| Economic Action Sequence | A. Represent | B. Simulate Exactly | C. Execute Exactly | D. Downstream Consequence Eval | E. Safe Recovery / Rollback | Actionability Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. Market Order Timing (`DEPENDENCY_AWARE_MARKET_TIMING`)** | **YES** | **YES** | **YES** | **YES** | **YES** | **100% COMPLETE (Live Foundation)** |
| **2. Terminal Liquidation (`TERMINAL_LIQUIDATION`)** | **YES** | **YES** | **YES** | **YES** | **YES** | **100% COMPLETE (Live Foundation)** |
| **3. Terminal Phase Shutdown (`PHASE_SHUTDOWN`)** | **YES** | **YES** | **YES** | **YES** | **YES** | **100% COMPLETE (Live Foundation)** |
| **4. Farmer Route Detour + Reconnect (`DYNAMIC_SHADOW_HARVEST`)** | **YES** | **YES** | Partial | Partial | Poor | **FRAGILE (Economically Dominated by V3)** |
| **5. Auxiliary Farmhand 1-Step Harvest (`MULTIWORKER_HARVEST`)** | **YES** | Partial | **YES** | **FAILED** | **NONE** | **INCOMPLETE / FATALLY TRAPPED** |
| **6. Auxiliary Farmhand Composed Harvest + Deposit** | **NO** | **YES** | **NO** | Partial | Poor | **MISSING REPRESENTATIONAL PRIMITIVE** |
| **7. Worker-to-Worker Inventory Hand-off** | **NO** | **NO** | **NO** | **NO** | **NO** | **ENVIRONMENT IMPOSSIBLE (Engine has no unit trade)** |

---

## 3. Detailed Sequence Analysis

### Sequence 1: Dependency-Aware Market Timing
- **Mechanics**: Reorders market basket at turn $t$ so that non-price-depressing orders or sell-before-buy dependencies resolve with optimal intra-basket pricing.
- **Completeness**: 
  - Representable in 1 turn via `CoupledPatch.market_mutations`.
  - Exactly simulatable via `ActionBasketDependencyGraph`.
  - Atomically executed; zero physical state disruption; zero spatial displacement.
  - Leaves physical board state 100% identical to baseline.
- **Verdict**: **The Gold Standard of AEC Action Completeness**.

### Sequence 5: Auxiliary Farmhand 1-Step Harvest (Phase 020 Failure)
- **Mechanics**: Intervenes on turn $t$ to set `hands[h] = ['HARVEST']`.
- **The Incompleteness Gap**:
  - AEC easily represented the first action (`['HARVEST']`).
  - However, AEC provided **zero representational closure** for the subsequent steps required by the environment's asset lifecycle:
    1. The farmhand had no instructions to walk to the shed.
    2. The farmhand had no instructions to execute `['DROP']`.
    3. The farmhand had no instructions on how to reconcile the harvested tile with its remaining daily watering duties.
- **Result**: The action sequence was severely truncated, leaving the system in an unrecoverable intermediate trapped state ($S3$).

### Sequence 6: Auxiliary Farmhand Composed Harvest + Deposit
- **Mechanics**: Multi-turn sequence: `[MOVE... -> HARVEST -> MOVE_TO_SHED... -> DROP -> RESUME]`.
- **Is it supported by the environment?**: **YES**. An auxiliary farmhand can legally walk to the shed and execute `['DROP']` before turn 23.
- **Can AEC represent it?**: **NO**.
  - AEC’s `CoupledPatch` and `HarvestCoupledPatchGenerator` only implement route-to-shed for the farmer (`worker_id = 0`), assuming farmhands are either stationary or follow immutable paths.
  - No generator in AEC currently constructs multi-worker coordinated route closures with dynamic shed docking for auxiliary farmhands.
- **Would it be economically positive even if implemented?**:
  - In a 10x10 board, routing a farmhand from a corner plot (e.g. $(4, 9)$) to the shed $(4, 4)$ takes 5 steps to reach the shed, 1 step to `DROP`, and 5 steps to return (11 steps total).
  - Given that a farmhand only lives for 24 turns, spending 11 turns (45.8% of its entire lifespan) to deposit 1-2 units of wheat ($35-$70) causes the farmhand to miss 11 scheduled watering steps, causing massive crop decay across the farm!
  - **The economic opportunity cost of the transit dominates any marginal harvest acceleration**.

### Sequence 7: Worker-to-Worker Inventory Hand-off
- **Mechanics**: Worker A harvests wheat and hands it to Farmer B on an adjacent tile so the Farmer can sell it or plant it.
- **Environment Legality**: **STRICTLY IMPOSSIBLE**.
  - In `sim.hpp`, there is no `OP_TRANSFER` or unit trade command.
  - Inventories are strictly isolated per unit (`f.inv[u]`).
  - The ONLY way items move between units is via the shed: Unit A must walk to shed $\to$ `DROP` $\to$ Unit B walks to shed $\to$ `PICKUP`.
- **Verdict**: Cannot be implemented because the physics of the environment do not support it.

---

## 4. Synthesis

The action-space audit demonstrates that:
1. Pure market transformations (`DEPENDENCY_AWARE_MARKET_TIMING`) are fully closed, complete, and safe.
2. Local physical worker interventions that fail to represent the complete multi-step closure (`HARVEST -> TRANSIT -> DROP`) are fatally incomplete.
3. Attempting to complete the physical closure for auxiliary workers imposes a catastrophic transit cost ($45\%$ of worker lifespan), destroying the economic rationale for the intervention in the first place.
