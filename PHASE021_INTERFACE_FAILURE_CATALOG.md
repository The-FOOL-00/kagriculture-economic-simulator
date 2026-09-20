# PHASE 021: INTERFACE FAILURE CATALOG & THREE-CLASS TAXONOMY

**Date**: 2026-09-20  
**Phase**: PHASE021 — AEC Capability, Action-Space & Dependency Completeness Audit  
**Data Sources**: `results/PHASE020_CENSUS_LEDGER.csv`, `results/PHASE020_PILOT_LEDGER.csv`  

---

## 1. Executive Summary

This catalog audits all non-tranche opportunity candidates identified during the Phase 020 census and classifies them into the three formal failure classes mandated by Section 9:
1. **`ECONOMICALLY FALSE`**: The apparent opportunity was an evaluation artifact that turns negative under closed-loop execution.
2. **`ECONOMICALLY REAL BUT ACTION-SPACE LIMITED`**: The opportunity is physically real, but the environment or architecture cannot safely express the necessary composed sequence.
3. **`ECONOMICALLY REAL AND ACTIONABLE`**: Already representable, executable, macro-safe, and captured by the live foundation.

---

## 2. Failure Class Taxonomy Matrix (§9)

| Candidate Opportunity Family | Census Signals | Probe Mean Delta | Closed-Loop Outcome | Failure Classification (§9) | Causal Root Defect |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Multi-Worker Harvest Synchronization** | 1,034 | +$118.75 | **-$552.00 (0W/10L/0T)** | **`ECONOMICALLY FALSE`** | Premature harvest destroys 75% of future biological crop yield; produce locked in farmhand backpack. |
| **Route / Spatial Compression Detours** | 1,536 | +$482.38 | **-$18.85 (Negative)** | **`ECONOMICALLY FALSE`** | Detouring off baseline path disrupts scheduled watering/feeding cycles; V3 already finds optimal shortest paths. |
| **Worker Allocation Reassignment** | 326 | +$81.97 | **-$35.96 (Negative)** | **`ECONOMICALLY FALSE / ACTION-SPACE LIMITED`** | Farmhands lack wheat for `FEED` or fertilizer for `FERTILIZE`; engine forbids direct unit-to-unit trade. |
| **Terminal Salvage Timing** | 140 | +$50.80 | **Neutral / Captured** | **`ECONOMICALLY REAL AND ACTIONABLE`** | Captured by live foundation (`TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`). |
| **Market Front-Loading / Tranche** | 3,158 | +$78.40 | **Catastrophic (-$757)** | **`ECONOMICALLY FALSE`** | Tranche front-loading depresses market price before shop consumption; permanently quarantined. |

---

## 3. Deep-Dive: Interface Failure Catalog

### Candidate 1: Multi-Worker Harvest Synchronization (`COORDINATE_WORKERS`)
- **Initial Census Signal**: 1,034 positive states, mean simulated delta +$118.75.
- **Action Sequence Required**:
  1. Farmhand executes `HARVEST` at turn $t$.
  2. Farmhand routes to shed ($K$ steps).
  3. Farmhand executes `DROP` at shed.
  4. Farmhand resumes watering tasks.
- **Currently Available Capabilities**: 1-step `HARVEST` patch on turn $t$.
- **Missing Capabilities**:
  - Multi-step route-to-shed planning for auxiliary farmhands.
  - Biological growth-stage gating (distinguishing `yield=1` vs `max_yield=4`).
- **Downstream Dependency**:
  - Biological dependency: Non-ongoing plants (WHEAT) are destroyed upon harvest.
  - Inventory dependency: Goods in farmhand backpack cannot be sold or fed until deposited into shed.
- **Reason Closed-Loop Execution Collapsed**:
  - The evaluator evaluated harvest as pure instantaneous cash.
  - In reality, harvesting at step 319 forfeited 3 subsequent yield units, and the single harvested wheat was locked in Hand 5's backpack for 16 turns until day-end reset, netting a -$552.00 loss across the pilot.
- **Class**: **`ECONOMICALLY FALSE`**.

---

### Candidate 2: Route Detour & Spatial Compression (`ALTER_ROUTE`)
- **Initial Census Signal**: 1,536 positive states, mean simulated delta +$482.38.
- **Action Sequence Required**:
  1. Worker diverts 1 step to step onto adjacent tile.
  2. Worker performs secondary task.
  3. Worker rejoins baseline trajectory.
- **Currently Available Capabilities**: 1-step directional mutation (`NORTH`/`SOUTH`/`EAST`/`WEST`).
- **Missing Capabilities**:
  - Global collision avoidance across all 10 units.
  - Knowledge of V3's future route schedule.
- **Downstream Dependency**:
  - Worker position dependency: Moving worker $u$ to $(x', y')$ alters its distance to all subsequent waypoints.
  - Tile exclusivity dependency: Moving onto an occupied tile fails with `OP_PASS`.
- **Reason Closed-Loop Execution Collapsed**:
  - V3's internal route planner already constructs optimal TSP routes for watering and feeding.
  - Diverting a worker causes it to arrive late at subsequent plots, causing crops to wither (`consecutive_dry >= 2` $\to$ weed transition).
- **Class**: **`ECONOMICALLY FALSE`**.

---

### Candidate 3: Worker Allocation Reassignment (`REASSIGN_WORKER`)
- **Initial Census Signal**: 326 positive states, mean simulated delta +$81.97.
- **Action Sequence Required**:
  1. Reassign `FEED` or `CARE` from farmer to adjacent farmhand.
  2. Farmer performs planting or marketing instead.
- **Currently Available Capabilities**: 1-step action reassignment.
- **Missing Capabilities**:
  - Inventory transfer: Transferring wheat from farmer backpack/shed to farmhand backpack.
- **Downstream Dependency**:
  - Engine requirement: `OP_FEED` requires `f.inv[u][WHEAT] >= 1`.
- **Reason Closed-Loop Execution Collapsed**:
  - Farmhands have empty backpacks (`f.inv[u] = {}`).
  - When ordered to `FEED`, the engine returns `false` (`f.inv_take` fails). The animal is NOT fed, risking escape if unfed for 2 days.
  - The Kagriculture environment **does not support direct unit-to-unit trade**.
- **Class**: **`ECONOMICALLY FALSE / ACTION-SPACE LIMITED`**.

---

## 4. Summary of Three-Class Audit

Across all 3,036 non-tranche census signals:
1. **Zero** candidates represent a viable, uncaptured `ECONOMICALLY REAL AND ACTIONABLE` opportunity outside the live foundation.
2. **Zero** candidates represent an `ECONOMICALLY REAL BUT ACTION-SPACE LIMITED` opportunity that could safely be unlocked within the rules of Kagriculture without catastrophic transit opportunity costs.
3. Over **95%** of surviving signals are **`ECONOMICALLY FALSE`**—they look positive in uncommitted single-turn rollouts because the evaluator is blind to future biological growth forfeiture and backpack cargo-trapping.
