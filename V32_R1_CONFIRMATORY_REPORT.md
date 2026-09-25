# V32 R1 CONFIRMATORY REPORT (2026-09-22)

Preregistration: `V32_R1_PREREGISTRATION.md` (+ Addendum A1), sealed
`results/v32_prereg_seal.json` (sha `6c28baf3…`, 2026-09-22T14:36:55Z —
before any new match completed). LOCKED legs (8 seeds x 30 pairs = 240)
run once, opened once, only here. Machine-readable:
`results/v32_r1_eval_testlocked.json`, `results/v32_r1_eval_locked.json`.

## 1. Gate set: TEST+LOCKED (40 seeds x 6 opponents = 240 b1 rows)

| predictor | mean_cash | lift_vs_A7 [95% CI] | drop1min | seed_pos | cat |
| :--- | ---: | :--- | ---: | ---: | ---: |
| always_A7 | 98,159 | — | — | — | 0 |
| always_W72 | 98,955 | +796 [−1,195, +2,821] | +363 | 0.57 | 8 |
| M1 lookup | 97,558 | −601 [−2,997, +1,903] | −1,232 | 0.40 | 23 |
| M2 logistic | 97,884 | −275 [−3,085, +2,549] | −897 | 0.47 | 28 |
| M3 small/longer | 97,880 | −279 [−3,088, +2,549] | −901 | 0.47 | 28 |
| M3 shuffled | 97,877 | −282 | −707 | — | 28 |
| oracle_cash | 106,056 | +7,897 [+5,984, +10,064] | +7,418 | 1.00 | 0 |

## 2. LOCKED-only (8 seeds, 48 rows)

A7 100,244; W72 98,830 (−$1,414 — sign flip vs TEST +$1,348, confirming
lottery noise); M1 100,407 (+$163, null); oracle 105,094 (+$4,850
[+$1,967, +$8,731] — gap persists on locked).

## 3. Gate verdict (prereg G1–G6, amended primaries M1/M2/M3 on b1)

G1 (CI excludes 0, positive): FAIL — all router lifts negative with CIs
including 0. G2 (no catastrophe): FAIL as improvement (23–28 rows
< A7 −$25k... note: G2's threshold counts rows worse than A7 by $25k;
routers introduce 23–28 such rows vs A7's 0 — the routers ADD tail).
G3 (seed-positive ≥ 60%): FAIL (0.40–0.47). G4 (shuffled ≤ baseline):
PASS trivially (shuffled −$282 ≈ M3 −$279 — nothing learned anywhere,
no leakage signal). G5 (determinism): PASS (rerun-identical selections;
no expert code touched). G6 (drop-one-seed stays positive): FAIL
(all negative).
GATE: FAIL → Branch B/C/D mapping (§4 of prereg): oracle gap large and
robust (+$7.9k gate / +$4.9k locked) while learned routers ≈ A7 →
**BRANCH C** (oracle exists, router cannot find it). See decision report
for the required refinement (late-resolving lottery + vacuous switching).

## 4. V22R1 strong-opponent probe (TEST seeds 249650–249655, 24 legs)

W2015 vs V22R1: 12-0, +$231. A7 vs V22R1: 12-0, +$1,257 (replicates
EXP-1 +$1,250). Static picture holds vs the strong opponent. NOTE: one
W2015-mirror pair on seed 249653 is seat-asymmetric (+$108 vs +$683 —
second V22R1-asymmetry seed after EXP-1's 249640; winners agree).
V22R1 stays evaluation-only and out of single-seat grids.
