# V32 P7 — OPENING MACRO SURVIVAL

## 1. MILESTONES (DERIVED FROM THE RECORDED TEACHER PREFIX, §8 DATASET DOC)

Evaluated on the policy's steps 0–8 (`v32/p7/metrics.py::opening_macro_survival`,
milestone table in `scripts/v32_p7_eval_screen.py`):

```text
wash_complete@0 → farmer_pass@0 → north@1 → hires5@1 → south@2
→ shed_stocked@2 → pickup_sheep@3 → farmer_at_shed@3 → pickup_wheat@4
→ north@5 → west@6 → build_pasture@7 → place_sheep@8
```

## 2. RESULT: 0/120 MACRO SURVIVAL IN BOTH ARMS

| Milestone | Arm 0 reached | Arm 1 reached |
|:---|:---:|:---:|
| wash_complete@0 … shed_stocked@2 (6/6) | 120/120 | 120/120 |
| pickup_sheep@3 | **0/120** (SOUTH) | **0/120** (PICKUP COW) |
|@4–@8 (never evaluated: chain broken) | — | — |
| **Full macro passed** | **0/120** | **0/120** |

Both arms traverse the first 6 milestones identically; both fail at
`pickup_sheep@3` — Arm 0 with the wrong OP, Arm 1 with the wrong ARG.

## 3. POST-FAILURE BEHAVIOR (SEED 249675 TRACE)

- Arm 0: SOUTH@3 → NORTH@4 → wanders north to [4,1], PLANT/WATER without
  livestock; hands idle; capital exhausted (~step 41); terminal $0.
- Arm 1: PICKUP-COW@3 → NORTH@4 → BUILD_PASTURE@6 at [4,2] (teacher: [3,3]) →
  repeated PLACE-SHEEP no-ops (carries COW, places nothing until step 15) →
  CARE loop; terminal $29. The policy performs macro-SHAPED actions (pasture →
  place → care) at the wrong PLACE with the wrong ANIMAL — choreography without
  coordination.

## 4. PHASE VIEW

Teacher phase: OPENING×2 → LIVESTOCK×2 → PRODUCTION → ECONOMIC (step 5+).
Arm 0 policy: OPENING×2 → LIVESTOCK×4 → PRODUCTION (stuck; never stocks).
Arm 1 policy: OPENING×2 → LIVESTOCK×4 → PRODUCTION → ECONOMIC (step 16+, via
hand-built structures — too late, no capital left to exploit).

## 5. GATE READING

The opening livestock/pasture macro does NOT survive in either arm. Prefix-4
moved the failure from "wrong op" to "wrong arg" — one coordination degree
closer, but survival is binary and the chain still breaks at step 3.
