# PHASE 021: STATE OBSERVABILITY AUDIT

**Date**: 2026-09-20  
**Phase**: PHASE021 — AEC Capability, Action-Space & Dependency Completeness Audit  
**Chassis Ground Truth**: `kagsim.cpp`, `sim.hpp`, `aec/ir/economic_state.py`  

---

## 1. Executive Summary

This audit evaluates the visibility, derivability, and accessibility of all state variables necessary for evaluating economic opportunities in Kagriculture. While physical state variables (cash, tile contents, backpack inventories) are fully observed via the environment observation dictionary, **worker intentionality, internal backbone task queues, and discard events are strictly hidden**, creating severe blindness when intervening on worker actions.

---

## 2. State Variable Observability Matrix

| State Variable | Environment Source | AEC IR Mapping | Observability Class | Evaluator Availability | Architectural Impact & Vulnerabilities |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Worker Backpack Contents** | `obs["private"]["inventories"]` | `WorkerEntity.cargo` | **Directly Observed** | Full | AEC correctly parses the inventory of each unit (farmer and hands). No sensory deficit. |
| **Shed Stock per Commodity** | `obs["private"]["shed"]` | `ShedInventory.stock` | **Directly Observed** | Full | Accurately observed. |
| **Shed Total Occupancy** | Derived via `sum(shed.values())` | `ShedInventory.total_units` | **Derivable** | Full | Readily available to prevent overflow. |
| **Worker Positions** | `obs["farms"][p]["farmer"]`, `hands` | `WorkerEntity.position` | **Directly Observed** | Full | Spatial coordinates for all units are known every turn. |
| **Tile Crop Kind & Growth** | `obs["farms"][p]["tiles"][y][x]` | `FarmTileState` | **Directly Observed** | Full | `kind`, `crop`, `planted_day`, `watered_today`, `yield_units` observed. |
| **Tile Animal State** | `obs["farms"][p]["tiles"][y][x]` | `FarmTileState` | **Directly Observed** | Full | `animal`, `fed_today`, `cared_today`, `fertilizer_available` observed. |
| **Liquid Capital (Money)** | `obs["farms"][p]["money"]` | `EconomicState.money` | **Directly Observed** | Full | Accurate to floating-point precision. |
| **Seed Stock** | `obs["private"]["seeds"]` | `EconomicState.seeds` | **Directly Observed** | Full | Accurate per-crop seed counts observed. |
| **Market Shared Inventory** | `obs["market"]["inventory"]` | `MarketState.inventory` | **Directly Observed** | Full | Shared inventory observed for all 9 commodities. |
| **Market Current Prices** | `obs["market"]["prices"]` | `MarketState.current_prices` | **Directly Observed** | Full | Readily available. |
| **Unlocked Town Shops** | `obs["town"]["unlocked_shops"]` | `TownState.unlocked_shops` | **Directly Observed** | Full | Accurate shop instances observed. |
| **Backbone Route & Task Queue** | Internal V3 memory (`_PLANNER_NS`) | None (Unobserved) | **HIDDEN** | **UNAVAILABLE** | **CRITICAL ARCHITECTURAL LIMITATION**: V3 does not expose what a worker is scheduled to do on turns $t+1 \dots t+K$. Interventions overwrite step $t$ blind to future route commitments. |
| **Worker-to-Task Coupling** | Internal V3 memory | Heuristic estimate | **Partially Observed** | Incomplete | AEC can see current action $A_t$ but cannot see whether a unit is mid-route on a 6-step journey to water an endangered crop. |
| **Simultaneous Opponent Action** | Simultaneous engine execution | Opponent model proxy | **HIDDEN** | Unavailable | Game rule invariant: opponent's current-turn action resolves simultaneously. |
| **Shed Discard Losses** | C++ `Farm.discarded` | Sim telemetry only | **HIDDEN IN OBS** | Partial | Official Kaggle observation does not report discarded units. Only detectable via engine-level telemetry. |

---

## 3. Deep-Dive: The Hidden Task-Queue Problem

The primary observability failure is **not** environmental; it is **backbone-coupling blindness**:
1. **The V3 Planner State is Opaque**:
   The frozen V3 chassis plans multi-step routes for all units using `_proposals` and `_return` functions. Once a route is assigned (e.g. an 8-turn watering circuit for Hand 5), V3 only outputs the single slice `hands[4] = ['WATER']` at turn $t$.
2. **AEC's Sensory Deficit**:
   AEC sees that Hand 5 is at $(4, 9)$ and that the baseline action is `['WATER']`. AEC **cannot see** that Hand 5 has 5 more tiles to water on its daily route before it despawns at step 335.
3. **The Disruption Blindspot**:
   When AEC replaces `['WATER']` with `['HARVEST']`, it is blind to the fact that it just severed an ongoing route obligation. Because V3's internal planner receives an observation where the crop at $(4, 9)$ is gone and Hand 5 has cargo, V3 does not know how to handle the trapped cargo on an auxiliary worker and continues executing subsequent movement commands without routing to the shed.

---

## 4. Conclusion

The AEC perception layer is complete with respect to the Kaggle environment observation specification. There are no missing environmental sensors. 

However, **there is a severe intra-agent observability gap**: the AEC is blind to the internal trajectory commitments of the frozen V3 backbone. Any single-turn action mutation applied to an auxiliary worker operates without knowledge of that worker's multi-step task obligations, leading to cascading coordination failures.
