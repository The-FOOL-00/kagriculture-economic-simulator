# PHASE020 — REPRESENTATION AUDIT (§31)

**Phase**: PHASE020  
**Title**: Prospective Headroom Reorientation & New Opportunity Family Discovery  
**Date**: 2026-09-20  
**Qualified Family**: `MULTIWORKER_SYNCHRONIZATION`  

---

## 1. Representation Audit by Architectural Layer (§31)

| Architectural Subsystem | Requirements for Multi-Worker Sync | Current Architecture Capability | Representation Status |
| :--- | :--- | :--- | :---: |
| **Economic IR** (`aec/ir/`) | Must track all worker positions, cargo, tile crops, and maturity | `EconomicState`, `FarmState.tiles`, `WorkerState` accurately model all worker coordinates and mature crops | **FULLY REPRESENTED** |
| **Opportunity Engine** (`aec/opportunities/`) | Opportunity detection when $\ge 2$ workers exist and mature plots are unattended | `Opportunity` class with category `"LABOR"` and family `"MULTIWORKER_SYNCHRONIZATION"` | **FULLY REPRESENTED** |
| **CoupledPatch** (`aec/patches/`) | Express joint action with farmer and hand mutations | `CoupledPatch.actions` and `worker_mutations` natively represent joint multi-worker actions | **FULLY REPRESENTED** |
| **Candidate Funnel** (`aec/funnel/`) | Candidate prioritization and reservation preservation | Candidate Funnel supports labor patches; Phase 018 reservation ensures no foundation displacement | **FULLY REPRESENTED** |
| **Trajectory Reconnection** (`aec/replanning/`) | Reconnecting worker to baseline suffix after single-step harvest | Single-turn harvest action maintains spatial continuity; worker remains on harvest tile | **FULLY REPRESENTED** |
| **Adaptive Horizon Evaluator** (`aec/counterfactual/`) | Macro boundary detection and exact long-horizon rollout | Phase 016 evaluator seamlessly simulates multi-worker action under dynamic V3 continuation | **FULLY REPRESENTED** |
| **Safety Certificate** (`aec/safety/`) | Collision detection, legal tile operations, solvency | `SafetyCertificate` checks multi-worker collisions and move legality | **FULLY REPRESENTED** |

---

## 2. Representation Verdict

**VERDICT**: **`CURRENTLY REPRESENTABLE`**

The AEC does **not** require any missing architectural primitives to express Multi-Worker Harvest Synchronization. The transformation uses the exact existing `CoupledPatch` and `EconomicIR` interfaces.
