# V32 ROUTER BASELINES (R1)

Brief §5 baselines on (a) EXP-1 (complete, below) and (b) fresh TEST+LOCKED
grids (pending grid completion; same table schema, written by
`scripts/v32_router_evaluate.py`).

## A. EXP-1 reference (48 rows = 6 seeds x 8 opponents, 5-class b1)

Caveat: EXP-1 lacks self-play, so fixed experts cover 42 rows each (all
opponents except self) while A7 covers 48 (opponent is never A7). Means
are mildly non-comparable across experts; the fresh grid completes all
5x6 cells. M1 is post-hoc fit on the same 48 rows (optimistic).

| predictor | n | mean_cash | median_cash | mean_regret | median_regret |
| :--- | ---: | ---: | ---: | ---: | ---: |
| always_A7 (BASELINE 1) | 48 | 103,114 | 104,255 | 10,546 | 1,638 |
| always_W2015 (~BASELINE 2) | 42 | 103,848 | 103,195 | 9,828 | 0 |
| always_V25P3 | 42 | 103,638 | 103,903 | 10,839 | 1,640 |
| always_V3 | 42 | 100,246 | 102,528 | 12,813 | 7,673 |
| always_W72 (BASELINE 3) | 42 | 93,407 | 102,536 | 23,296 | 20,264 |
| random (BASELINE 4, expected) | — | ~100,195 | — | ~13,464 | — |
| per-opp M1 (post-hoc) | 48 | 108,061 | — | 5,598 | — |
| oracle_cash (BASELINE 5a) | 48 | 113,659 | 119,119 | 0 | 0 |
| oracle_WL (BASELINE 5b) | 48 | 110,059 | — | 3,600 | — |

W/L reference: A7 win-score 0.750, oracle-WL 0.875 (+0.125). The WL-oracle
gains +$6,945 cash over A7 — less than the cash-oracle (+$10,545): the
W/L-vs-cash tension costs ~$3.6k (P1-F5).

Reading: the oracle advantage over A7 is LARGE (mean +$10.5k, 42/48 rows
positive), so routing is strongly justified IF predictable (P1-F7: ~47%
opponent-driven). Fixed-A7's risk is tail, not level (median regret only
$1,638). W2015, not A7, is the best fixed class by cash.

## B. Fresh TEST grids (b1, 192 rows; LOCKED confirmatory in §C)

| predictor | mean_cash | mean_regret | median_regret | lift_vs_A7 [95% CI] |
| :--- | ---: | ---: | ---: | :--- |
| always_A7 (BASELINE 1) | 97,638 | 8,659 | 17 | — |
| always_W72 (best nominal) | 98,986 | 7,311 | 11 | +1,348 [−1,043, +3,752] |
| always_V3 (TRAIN best-fixed) | 97,548 | 8,749 | 430 | −90 [−2,207, +2,078] |
| always_W72 as BASELINE 3 | (same row as above) | | | |
| random (BASELINE 4) | 97,529 | 8,768 | 231 | −108 |
| per_opp M1 | 96,846 | 9,451 | 357 | −792 [−3,409, +1,999] |
| oracle_cash (BASELINE 5a) | 106,297 | 0 | 0 | +8,659 [+6,525, +11,102] |
| oracle_WL (BASELINE 5b) | 103,343 | 2,954 | 0 | +5,706 [+4,102, +7,412] |

b2: all baselines within $2 (vacuous — not a task). Fixed experts tied
(all CIs include 0). Oracle gap robust (drop-one-seed min +$8,081).

## C. TEST+LOCKED gate set (40 seeds, 240 b1 rows — confirmatory)

| predictor | mean_cash | lift_vs_A7 [95% CI] |
| :--- | ---: | :--- |
| always_A7 (BASELINE 1) | 98,159 | — |
| always_W72 | 98,955 | +796 [−1,195, +2,821] |
| always_V3 (TRAIN best-fixed) | 97,877 | −282 [−2,262, +1,714] |
| random (BASELINE 4) | 97,950 | −209 |
| per_opp M1 | 97,558 | −601 [−2,997, +1,903] |
| oracle_cash (BASELINE 5a) | 106,056 | +7,897 [+5,984, +10,064] |
| oracle_WL (BASELINE 5b) | 103,202 | +5,043 [+3,712, +6,560] |

Source: `results/v32_r1_eval_testlocked.json` (single LOCKED opening).
