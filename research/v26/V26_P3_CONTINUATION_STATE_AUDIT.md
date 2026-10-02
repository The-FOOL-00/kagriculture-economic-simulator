# V26 — V25 P3 CONTINUATION STATE AUDIT

## 1. Executive Purpose
Inspect all stateful objects and memory structures in the `V25_P3_UNIFIED` macro planner to determine exactly what must be cloned, what must be recomputed, and why, to guarantee 100% state isolation and zero desynchronization during shadow counterfactual rollouts (§8).

---

## 2. Architectural Structure of V25 P3
The V25 P3 unified planner combines three functional components:
1. **Opening Capital Velocity Hook** (Turn 0: 30-unit wheat wash).
2. **Underlying Route Replay Chassis** (`_V3_AGENT` extracted from frozen `submission_Vj_kc_v3.tar.gz`).
3. **In-Place Zero-Inventory Labor Dispatch** (Per-turn check converting idle `PASS` units to `WATER` or `DIG`).

---

## 3. Stateful Objects & Lifecycle Audit Matrix

| State Component | Location | Must Clone? | Must Recompute? | Why & Failure Mechanism if Neglected |
| :--- | :--- | :---: | :---: | :--- |
| **`step == 0` Branch** | `v25_p3_unified.py` | No | Recomputed | Pure stateless conditional based on `observation['step']`. Returns 30-unit wash on step 0, calls underlying chassis on step > 0. |
| **Chassis `players` Dictionary** | `_PARENT_NS['_IMPL'].chassis.players` | **YES** | No | Stores `last_step`, `route`, `router_state`, `pending` unit action queues, and `sell_state` (`due_step`, `suppress`). If not restored, shadow simulation advances `last_step` and corrupts live turn execution. |
| **Chassis `routes` Tape** | `_PARENT_NS['_IMPL'].chassis.routes` | No | No | Read-only static table of precomputed action sequences. Never mutated at runtime. |
| **Chassis `diagnostics`** | `_PARENT_NS['_IMPL'].chassis.diagnostics` | **YES** | No | Tracks `layer_fallbacks` and `entry_fallbacks`. Isolated to prevent diagnostic telemetry leakage. |
| **Parent Namespace Dictionaries (`_STATES`, `_HORIZONS`, `_LAST`, etc.)** | `_PARENT_NS` | **YES** | No | Intermediate stateful tracking used by parent V43/V45 layers. Must be snapshotted and restored to ensure zero cross-turn contamination. |
| **Global `TELEMETRY` Dictionary** | `v3_module.__dict__['TELEMETRY']` | **YES** | No | Tracks opening turns and wrapper counts. Must be restored to maintain clean telemetry. |
| **Worker Positions & Farm Tiles** | Simulated `ShadowRolloutState` | **YES** | Recomputed per step | Tile wetness (`watered_today`), weeds, and unit positions are updated by the physical simulation engine. P3's in-place chore dispatcher reads these tiles dynamically. |
| **Cash Trajectory (`money`)** | `ShadowRolloutState.money` | **YES** | Recomputed per step | P3 conserves $200+ more cash on Day 0 than V3 due to 30-unit wash. Counterfactual simulator must evaluate cash deltas against P3's real cash, not V3 historical expectations. |
| **Market Orders Queue** | Action dict `market` | No | Recomputed per turn | Market orders are generated freshly each turn by the underlying chassis and then modified by AEC candidate interventions. |
| **In-Flight Coupled Trajectory** | `AECExecutor._in_flight_patch` | **YES** | Recomputed on abort | Multi-turn committed actions. Aborts on feed deficit or solvency risk. |

---

## 4. Root Cause of V25 AEC Failure Identified & Resolved
In the frozen V22R1 AEC:
- `snapshot_v3_state(agent_fn)` inspected `agent_fn.__globals__['_PARENT_NS']`.
- When passed `V25_P3_UNIFIED` (a wrapper function), `agent_fn.__globals__` pointed to `candidates/v25_p3_unified.py`'s namespace, where `_PARENT_NS` did not exist.
- As a consequence, `snapshot_v3_state` returned an empty dict `{'parent': {}}`.
- During shadow rollouts, the underlying V3 chassis was called on simulated future turns (e.g. step 10), advancing `chassis.players[0]['last_step']` to 10.
- When the live game resumed at step 2, the chassis observed `step <= last_step`, resetting state and destroying the route tape synchronization.
- **V26 Resolution**: The `V25P3BackboneAdapter` explicitly binds and snapshots the underlying `_v3_agent_callable` state. This prevents any cross-talk between shadow simulations and the live game.
