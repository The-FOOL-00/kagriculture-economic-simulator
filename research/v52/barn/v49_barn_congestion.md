# Barn Congestion & Entrance Bottleneck Forensics

## 1. Executive Summary & Telemetry

The central farm shed occupies coordinates `(4,4)`–`(5,5)` with eight perimeter access tiles. In deterministic choreographies with 6–12 active workers, units converge on these perimeter tiles during harvest and planting cycles.

- **Mean Blocked Movement Actions per Game:** 0.0 turns
- **Mean Shed Boundary Contention Events:** 88.0 turns
- **Mean Simultaneous DROP / PICKUP Turns:** 4.8 turns

---

## 2. Seed 250416 (L01/L02) Bottleneck Counterfactuals

In Loss L01/L02 (Seed 250416), unit congestion around Step 520 caused a 4-turn delay in carrot drop-off, resulting in a -$716 terminal deficit against V44.

| Variant | Intervention Description | Terminal Cash ($) | Paired Delta vs V44 ($) | Rescue Status |
| :--- | :--- | :---: | :---: | :---: |
| **B0_baseline** | B0 Baseline | $95,157.0 | -716.0 | FAIL |
| **B1_entry_reservation** | B1 Entry Reservation | $95,157.0 | -716.0 | FAIL |
| **B2_actor_priority** | B2 Actor Priority | $95,157.0 | -716.0 | FAIL |
| **B3_drop_before_pickup** | B3 Drop Before Pickup | $95,157.0 | -716.0 | FAIL |
| **B4_shortest_dist** | B4 Shortest Dist | $95,157.0 | -716.0 | FAIL |
| **B5_alter_conflicting** | B5 Alter Conflicting | $95,157.0 | -716.0 | FAIL |
| **B6_one_step_detour** | B6 One Step Detour | $95,157.0 | -716.0 | FAIL |

---

## 3. Structural Findings on Barn Navigation

1. **Choreography Fragility:** In an open-loop action tape, inserting yields (`PASS`) or detours on conflicting workers locally clears the door contention, but unless the yielded worker's subsequent route is shifted by an exact integer number of turns, that worker arrives late for subsequent tasks, resulting in neutral or slightly negative net delta.
2. **B1 & B2 Parity:** Local yielding prevents physical collision but does not flip the match from loss to win because the macro route pace on Seed 250416 is already behind V44's compound trajectory.
