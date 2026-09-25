# V32 R1 EVALUATION — TEST (32 seeds x 6 opponents = 192 b1 rows)

Eval: `scripts/v32_router_evaluate.py --split test`, machine-readable
`results/v32_r1_eval_test.json` (metrics + paired CIs + per-row tables).
CIs are 95% seed-bootstrap (2000 resamples); seeds are the sample unit.

## 1. Headline table (b1 TEST)

| predictor | mean_cash | median | mean_regret | median_regret | W-L-T | cat | lift_vs_A7 [95% CI] |
| :--- | ---: | ---: | ---: | ---: | :--- | ---: | :--- |
| always_A7 | 97,638 | 95,529 | 8,659 | 17 | 94-69-29 | 0 | — |
| always_W72 | 98,986 | 96,154 | 7,311 | 11 | 152-11-29 | 6 | +1,348 [−1,043, +3,752] |
| always_best_fixed (TRAIN=V3) | 97,548 | 95,470 | 8,749 | 430 | 48-115-29 | 25 | −90 [−2,207, +2,078] |
| random | 97,529 | 95,539 | 8,768 | 231 | 86-72-34 | 10 | −108 |
| per_opp_lookup_M1 | 96,846 | 95,109 | 9,451 | 357 | 79-84-29 | 21 | −792 [−3,409, +1,999] |
| M2_logistic_aid | 97,542 | 95,589 | 8,755 | 234 | 79-84-29 | 25 | −96 [−3,140, +3,091] |
| M3_small_b1 (all 4 variants identical) | 97,538 | 95,589 | 8,759 | 257 | 79-113-0 | 25 | −100 [−3,143, +3,091] |
| M3_shuffled_b1 | 97,548 | 95,470 | 8,749 | 430 | 48-115-29 | 25 | −90 |
| oracle_cash | 106,297 | 102,465 | 0 | 0 | 127-37-28 | 0 | +8,659 [+6,525, +11,102] |
| oracle_WL | 103,343 | 97,790 | 2,954 | 0 | 156-7-29 | 0 | +5,706 [+4,102, +7,412] |

b2 TEST: all predictors within $2 (vacuous; oracle gap $2). Not a task.

## 2. OBSERVED FACTS

E1. Oracle gap is large and robust: +$8,659 mean [+$6,525, +$11,102],
drop-one-seed min +$8,081, positive on all 32 seeds. Median A7 regret is
$17 — the gap is a heavy tail (a few $30–77k suppression-avoidance rows),
not a level shift.
E2. Fixed experts are statistically tied: best nominal (W72 +$1,348)
CI includes 0; seed-positive fraction 0.59 (below G3's 0.60).
E3. All routers null-or-negative: M1 −$792, M2 −$96, M3 −$100 (CIs all
include 0), each introducing 21–25 catastrophes vs A7's 0. Shuffled
(−$90) is indistinguishable from "real" models: nothing was learned (G4
passes trivially).
E4. All four M3 variants (stacks x seeds) pick IDENTICALLY (79-113-0):
regularized training collapsed to one marginal function. Frame stack has
zero economic effect (P4 refuted).
E5. Per-opponent best-class FLIPS between TRAIN and TEST on 5/6 opponents
(e.g. vs W2015: TRAIN→V3 by +$11k mean; TEST→W72). TRAIN-fit static rules
anti-generalize. Post-hoc TEST per-opp ceiling is only +$1.4k over A7
(vs +$4.9k TRAIN): opponent-driven signal ≈ 0 on fresh seeds (P1-F7 47%
refuted; P1 best-baseline prediction refuted).
E6. Best-class concentrates 1–2 per SEED across opponents (seed lottery);
median per-row spread $11.7k (b1). W72 is oracle-best on 75/192 TEST rows
vs 6/48 EXP-1 rows — the lottery, not the opponent, picks the winner.
E7. Prefix carries no lottery signal: wheat@t24 constant (28.0) across
all rows/outcomes; cash@t24 pure noise; class money curves separate
>$2k only at median step 258 of ~720 (measured on 41 fresh seeds).
The lottery resolves mid-game, unknowable at t≤24.
E8. CROSS-WITHIN confirmation FAILED: 17/41 fresh seeds (P8 needed ≥21).
The post-hoc G1/G2 grouping does not generalize (pair swings are real
but seed-lottery-specific, not family-structured).
E9. Opp-holdout secondary: M3_oh −$100, M2_oh −$42 on TEST; wash-micro
columns ≈ 0. No generalization to unseen families because there is no
within-family signal to generalize (P6 refuted).
E10. M1/M2/M3 W/L (79-84/79-113) underperforms A7 (94-69): routers lose
both cash and games.

## 3. Preregistration scorecard

P1 best baseline M1 +$4–6k: REFUTED (−$792). P2 oracle +$8–12k mean:
CONFIRMED (+$8,659); median +$1–3k: REFUTED ($17 — heavier tail than
predicted). P3 M4/B2 +$2–6k: SUPERSEDED by A1 (B2 vacuous), B1 analogue
M3 −$100: REFUTED. P4 stack longer>short>none: REFUTED (identical). P5
B1≥B2: VACUOUS (B2 not a task). P6 holdout above A7: REFUTED (null). P7
W72 rare selections: REFUTED (oracle picks W72 most, 75/192). P8
CROSS-WITHIN ≥21/41: REFUTED (17/41).

## 4. INTERPRETATION

The phase's primary question is answered NEGATIVELY with mechanism proofs
at every step: (i) the router decision ≡ the step-0 wash decision
(wash-identity proof); (ii) step-0 state is constant (P1-F10), so no
pre-episode information exists; (iii) the best wash is a seed lottery
resolving at t≈260+, invisible in any t≤24 prefix (E7); (iv) the
opponent-driven structure seen at n=6–10 was small-n mirage (E5, E8).
No pre-episode or early-episode router over this population can beat the
best fixed expert. The $8.6k oracle gap is real but reachable only by
within-episode ADAPTIVE policies (observe the resolving lottery mid-game
and adjust the economy — BC/PPO territory) or new expert designs
(e.g. delayed-wash scouting), never by expert selection. See
`V32_R1_DECISION_REPORT.md` (Branch C, refined).
