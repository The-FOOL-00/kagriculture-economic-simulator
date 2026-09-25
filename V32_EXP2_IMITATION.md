# V32 EXP-2 — IMITATION FEASIBILITY (executed 2026-09-22)

## 1. Data

`scripts/v32_capture.py` on TRAIN seeds 249641–249642, pair A7:V3 mirrored
(4 legs): **5,752 (obs, action) pairs in 62.6 s serial = 92 pairs/s**,
0 encode failures, encoder `v32enc-v1.1` (90 floats). No DEV/CONFIRM touch
for training data.

## 2. Probe: farmer-op classification (R0 rung)

17 farmer-op classes observed. Chronological split (first 80% train, last 20%
test — no shuffle leakage across the episode boundary).

| Model | Train acc | Test acc | Lift over majority |
| :--- | :--- | :--- | :--- |
| Majority (NORTH) | — | 0.107 | — |
| Softmax regression, 90 feats | 0.268 | **0.224** | **+0.114** |

Script: `scripts/v32_bc_probe.py` (numpy-only, deterministic seed).

## 3. Interpretation (honest)

- There IS learnable signal at the cheapest possible rung (2× majority on
  held-out tail). §52(1) ("cannot achieve useful learning") is NOT triggered.
- Absolute accuracy (22%) is far from expert fidelity. Causes: single-frame
  obs (no frame stack — movement ops are path-dependent), linear capacity,
  and farmer-head-only scoring (hands+market heads untested here).
- Full-action exact-match at any majority-style rung is ~0 by construction
  (joint match over farmer + up to 12 hands + up to 8 market orders). BC is
  not "solved" — it is "non-sterile, needs the ladder" (R1 0.1M MLP +
  frame stack next, per `V32_TRAINING_SPEC.md`).

## 4. Router toy (pipeline demonstration, NOT a result)

Planned: {V3, A7, W2015}-from-seat-0-vs-V3 labels on 10 TRAIN seeds with
leave-one-seed-out multinomial logistic. n=10 is a pipeline smoke test only;
any accuracy number at n=10 is noise. The real router experiment needs
≥40 TRAIN seeds × counterfactual labels and is gated on EXP-1's final matrix.

## 5. EXP-2 verdict

IMITATION IS VIABLE AS INITIALIZATION (Phase A), not as a solution. Proceed up
the model ladder; do not claim BC parity with any expert. Next rung: frame
stack + R1 MLP + hands/market heads, then DEV W/L/T of the BC policy itself
(a BC policy that can't beat PASS is a failed rung, no matter its loss).
