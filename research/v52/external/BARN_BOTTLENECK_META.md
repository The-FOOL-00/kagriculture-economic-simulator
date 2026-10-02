# Barn Bottleneck Meta Research: Centralized Shed Contention & Micro-Pathing

## 1. Executive Summary
In the Kaggriculture environment, the player's farm features a centralized 4-tile farm-house / shed complex located at the center of the quadrant boundary (coordinates `(4,4)`, `(4,5)`, `(5,4)`, `(5,5)` on a 10x10 farm). All inventory storage, seed pickup, harvested crop drop-off, animal product collection, and fertilizer handling pass through these coordinates.

This audit compiles public and forensic evidence regarding spatial congestion around the barn:
1. **The Physical Geometry of Shed Access:** Only specific boundary tiles permit valid `DROP` and `PICKUP` interactions with the shed inventory.
2. **Multi-Worker Path Collisions:** In deterministic route tapes (such as the 2945 choreography with 6–10 active workers), workers frequently attempt to enter or pass through the shed perimeter simultaneously.
3. **The Loss Forensics Connection:** 2 of V49's 11 historical losses (specifically Seed 250416, -$716 delta across both seats) were directly attributed to path and occupancy contention near the shed.

---

## 2. Public Mechanism Audit Table

| Source | Author / Entity | Date | Mechanism Description | Reported Metric | Environment | Reproducible | License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Multi-Worker Logistics Layer** | Adaptive Economic Compiler (AEC / Phase 003) | 2026-08-25 | Implemented bipartite spatial matching between workers and crop beds to prevent multi-worker congestion around `(4,4)`–`(5,5)`. Prioritized worker movement based on cargo perishability. | Eliminated labor cannibalization; reduced idle waiting turns by 38% | Local Simulator | 100% Reproducible | Internal Audit / MIT |
| **Shed Capacity & Timing Guards** | `tetsutani` & `aurax7` | 2026-09-08 | Reactive state checks ensuring shed stock does not hit the 100-item maximum capacity at hour 23. Clamped orders to prevent wasted drop turns when the shed is full. | Prevented item loss at daily rollover; preserved cargo integrity | Kaggle Public Notebooks | 100% Reproducible | Apache-2.0 |
| **Forensic Loss Audit (Seed 250416)** | V51 Research Program | 2026-09-25 | Turn-by-turn trace revealed that at Step 520, worker movement carrying carrot deliveries was delayed by 4 turns due to occupancy contention at the shed door, causing delivery to slip past market absorption pricing. | Responsible for 2/11 historical losses (-$716 margin); localized to shared entrance bottleneck | Local Deterministic Simulator | 100% Reproducible | Internal Audit |

---

## 3. Spatial Mechanics of the Central Barn

1. **Shed Geometry & Interaction Rules:**
   - The central farm structure occupies tiles `(4,4)`, `(4,5)`, `(5,4)`, `(5,5)`.
   - Units cannot enter the solid interior walls; they interact from adjacent cardinal tiles (`(3,4)`, `(3,5)`, `(4,3)`, `(5,3)`, `(6,4)`, `(6,5)`, `(4,6)`, `(5,6)`).
   - Valid actions at shed adjacent tiles:
     - `DROP [ITEM] [QTY]`: Transfers item from worker inventory into shed.
     - `PICKUP [ITEM] [QTY]`: Transfers item from shed into worker inventory.
2. **Congestion Failure Modes:**
   - **Contention for Same Tile:** Hand 1 is walking North toward `(4,3)` while Farmer is moving South to `(4,3)`. In Kaggriculture, if two units attempt to enter the same tile on the same turn, one is prioritized by unit index and the other's movement fails (`BLOCKED`).
   - **Blocked Egress:** A worker performing a `DROP` at `(4,3)` occupies the tile, blocking a second worker behind them who intended to walk through `(4,3)` on that turn.
   - **Compounding Tape Desynchronization:** In open-loop action tapes, a single turn delay cascades: the delayed worker fails to plant on the next tick, leaving the dirt plot empty, delaying watering, and shifting crop harvest by 24–72 turns.

### Key Hypothesis for V52
Local entrance reservation or priority routing (e.g. drop before pickup, shortest distance priority, or single-turn detour) could clear the bottleneck on Seed 250416 without destabilizing the broader choreography.
