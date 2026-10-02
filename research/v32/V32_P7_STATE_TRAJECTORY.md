# V32 P7 — STATE TRAJECTORY ANALYSIS (MODE B ROLLOUT CONSISTENCY)

## 1. METHOD

Free-running policy (masked) vs live E2_A7 replay, same seed/opp/seat, steps
0–8, all 120 screen legs per arm. Distance = `v32/p7/state.py::state_distance`
(normalized components; weights: position 2, hands 1, cash 1, inventory 1,
livestock 2, crops 1, market 0.5). No teacher-state overwrite, no splicing —
pure simulator execution (`tests/test_v32_p7.py::test_05`).

## 2. MEAN STATE DISTANCE BY STEP (120 LEGS)

| Step | Arm 0 | Arm 1 | Δ |
|:---:|:---:|:---:|:---:|
| 0 | 0.0000 | 0.0000 | 0 |
| 1 | 0.0370 | 0.0030 | −92% (wash bleed −$1,014 → −$118) |
| 2 | 0.0222 | 0.0010 | −95% |
| 3 | 0.0445 | 0.0206 | −54% |
| 4 | 0.0794 | 0.0340 | −57% (positions still synced: PICKUP is stationary) |
| 5 | 0.1288 | 0.1154 | −10% (t_pos: physical split) |
| 6 | 0.1791 | 0.1710 | −5% |
| 7 | 0.1865 | 0.1733 | −7% |
| 8 | 0.2424 | 0.2114 | −13% |

## 3. INTERPRETATION

1. **Prefix supervision DID improve rollout consistency**: the Arm 1 state
   trajectory is uniformly closer to the teacher's at every step 1–8. H1's
   literal prediction (reduced sequence drift) is confirmed.
2. **The improvement DECAYS with horizon**: −95% at step 2 → −13% at step 8.
   Early cash/position fidelity does not compound into macro fidelity because
   the step-3 arg error re-seeds divergence (wrong animal → wrong step 4 →
   wrong pasture tile → no-op PLACEs).
3. **Component attribution** (seed 249675 trace): steps 1–2 gains are ~entirely
   the cash component (wash qty); steps 3–4 gains are position + livestock
   (stationary PICKUP keeps farmer at shed, COW secured vs nothing); steps 5–8
   the livestock/inventory components re-diverge (COW≠SHEEP propagates).
4. Mode-B selection during training (train seeds, d ≈ 0.08–0.10) correctly
   predicted the DIRECTION (improvement) but the screen shows its LIMIT
   (no macro stabilization). Mode B as a metric works; Mode A as supervision
   saturates below the goal.

## 4. GATE READING

State divergence decreased materially (Gate 1, partial pass) but the trajectory
still leaves the teacher manifold irreversibly at step 3–5 on all 120 legs.
State-trajectory fidelity improved; state-trajectory STABILITY was not achieved.
