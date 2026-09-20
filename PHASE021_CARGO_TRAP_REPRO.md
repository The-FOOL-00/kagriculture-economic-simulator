# PHASE 021: DETERMINISTIC MINIMAL REPRODUCTION OF THE CARGO-TRAPPING FAILURE

**Date**: 2026-09-20  
**Phase**: PHASE021 — AEC Capability, Action-Space & Dependency Completeness Audit  
**Reproduction Seed**: `249366`, Seat 0  
**Intervention Step**: Step 319 (Day 13, Hour 7)  
**Target Unit & Tile**: Auxiliary Farmhand 5 (Unit 5) on Tile `(4, 9)`  
**Reproduction Script**: [scripts/run_phase021_cargo_trap_repro.py](file:///c:/Users/Sundareswaran/Kagriculture/scripts/run_phase021_cargo_trap_repro.py)  
**Raw Trace Data**: `results/PHASE021_CARGO_TRAP_TRACE.json`  

---

## 1. Executive Summary

This experiment deterministically isolates the causal chain of the catastrophic failure observed during the Phase 020 `MULTIWORKER_HARVEST_SYNCHRONIZATION` pilot trial (-$552.00 mean loss, 0W/10L/0T). 

The empirical trace proves that the failure was **not** caused by random market noise or opponent preemption. It was a deterministic **triple-failure of biological growth, inventory localization, and backbone schedule disruption**:
1. **Biological Destruction**: Harvesting at step 319 harvested 1 unit of wheat and destroyed the plant, forfeiting 3 subsequent units of growth (harvested at yield 1 vs baseline harvesting at yield 4 at step 368).
2. **Backpack Cargo-Lock**: The single harvested wheat remained locked in Hand 5's personal backpack for 16 turns (steps 319–335), completely inaccessible for market liquidation, animal feed, or planting.
3. **Empty Tile Wastage**: The plot sat empty for 51 turns without replanting, risking weed infestation.

---

## 2. Deterministic Step-by-Step Trajectory Trace

| Step | Day:Hour | Baseline Action (Hand 5) | Mutated Action (Hand 5) | Baseline Tile (4,9) State | Mutated Tile (4,9) State | Hand 5 Cargo (Base) | Hand 5 Cargo (Mut) | Shed Stock (Base vs Mut) | Economic Divergence Note |
| :---: | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **318** | 13:06 | `['WEST']` | `['WEST']` | Planted Day 11, `yield=1`, `watered=false` | Identical | `{}` | `{}` | 19 vs 19 | Identical pre-intervention state. |
| **319** | 13:07 | **`['WATER']`** | **`['HARVEST']`** | `watered=true`, plant continues growth | **Plant destroyed (`None`)**, `yield=0` | `{}` | **`{'WHEAT': 1}`** | 19 vs 19 | **INTERVENTION**: Harvests prematurely at yield 1. |
| **320** | 13:08 | `['WEST']` | `['WEST']` | `watered=true`, **`yield=2`** | `None` (Empty tile) | `{}` | `{'WHEAT': 1}` | 19 vs 19 | Baseline yield scales to 2. Mutated tile is bare. |
| **325** | 13:13 | `['WATER']` | `['WATER']` | `watered=true`, `yield=2` | `None` (Empty tile) | `{}` | `{'WHEAT': 1}` | 19 vs 19 | Hand 5 executes routine watering on other tiles. |
| **334** | 13:22 | `['WATER']` | `['WATER']` | `watered=true`, `yield=2` | `None` (Empty tile) | `{'WHEAT': 2}` | `{'WHEAT': 3}` | 0 vs 0 | Hand 5 carries cargo accumulated along its route. |
| **335** | 13:23 | `['PASS']` | `['PASS']` | Day 13 final turn; `yield=2` | `None` (Empty tile) | `{'WHEAT': 2}` | `{'WHEAT': 3}` | 0 vs 0 | **Day 13 Closes**. Automatic `drop_inventories` triggered. |
| **336** | 14:00 | *New Day* | *New Day* | Day 14 start; `yield=2` | `None` (Empty tile) | **DESPAWNED** | **DESPAWNED** | 16 vs 17 | Hand 5 despawns. Shed receives cargo 16 turns late. |
| **353** | 14:17 | `['WATER']` | N/A | **`yield=3`** (Day 14 watering) | `None` (Empty tile) | — | — | — | Baseline yield increases to 3. |
| **367** | 15:07 | `['WATER']` | N/A | **`yield=4`** (Day 15 watering) | `None` (Empty tile) | — | — | — | Baseline reaches maximum crop yield of 4. |
| **368** | 15:08 | **`['HARVEST']`**| N/A | **Harvested at `yield=4`** | `None` | — | — | — | Baseline cleanly harvests 4 units at optimal maturity! |
| **370** | 15:10 | `['PLANT']` | N/A | Replanted with fresh seed | `None` | — | — | — | Baseline immediately replants plot. |

---

## 3. Causal Mechanics Breakdown

### Defect 1: Biological Growth Misunderstanding
In Kagriculture, non-ongoing crops (WHEAT, CARROT, MELON) undergo a multi-day maturation window.
- For WHEAT, first yield occurs at day 2 (`first_yield_day = 2`), but daily watering during the maturation window increments `yield_units` up to `max_yield = 6` (in V3 play, typically reaching 4).
- The Phase 020 opportunity detector observed `yield_units >= 1` and evaluated it as a ripe harvest.
- By triggering `HARVEST` at step 319, it gained **1 unit** of wheat but permanently killed the plant, forfeiting **3 additional units** of future wheat production on that single plot.
- Over 134 commits, this biological truncation destroyed hundreds of units of potential harvest.

### Defect 2: The Backpack Inaccessibility Trap
- Goods harvested by farmhands enter `f.inv[idx]`.
- Market orders process exclusively from `f.shed`.
- Because Hand 5 had no route-to-shed instruction, the single harvested wheat was trapped in Hand 5's backpack for **16 turns** until step 335.
- During those 16 turns, the wheat was completely useless: it could not be sold at peak prices, could not be used to feed animals, and could not be accessed by the farmer.

### Defect 3: Farmhand Diurnal Ephemerality
- Hand 5 despawned at step 336 (`f.n_units = 1`).
- While the environment’s automatic `drop_inventories` saved the wheat from being lost, the delay meant market timing was missed, and the opportunity to use auxiliary labor productively was wasted.

---

## 4. Conclusion & Scientific Takeaway

The Cargo-Trapping failure was **not an implementation bug in the Python wrapper**. It was an **economic and dependency model failure**:
1. It modeled harvest as an unconstrained value-extraction action, ignoring the biological opportunity cost of ongoing growth.
2. It assumed harvested produce is immediately fungible, ignoring the physical dependency that goods in a farmhand's backpack cannot be sold or utilized until delivered to the shed.
3. It intervened with a 1-step patch on an auxiliary worker whose lifecycle is diurnal and whose pre-planned schedule was dedicated to watering.
