# V31R2 LIVE SCORECARD — A7 vs V22R1 on the real ladder

Date: 2026-09-22 (updated with games through ~12:00 UTC). All 352
episodes retrieved with replays (99 A7 + 251 V22R1 public + 2
validation). Leaderboard snapshot 08:50 UTC (9,807 teams).
Machine-readable: `results/v31r2_live_scorecard.json`; per-episode:
`V31R2_LIVE_EPISODES.jsonl`; registry:
`V31R2_LIVE_SUBMISSION_REGISTRY.json`.

## Headline (NOT the whole story)

| Submission | Ref | Rating (08:50 → 12:00 UTC) | Games (public) | W/L/T | Win rate |
| ---------- | --- | -------------------------: | -------------: | ----- | -------: |
| A7 (`submission_a7_v30.tar.gz`) | 56450454 | 1859.6 → 1842.1 | 99 | 56/43/0 | 56.6% |
| V22R1 (`submission_aec_v22r1.tar.gz`) | 56401915 | 1880.3 → 1854.5 | 251 | 112/138/1 | 44.6% |

Both slots went 6-11 / 4-10 over the last ~3h (harder matchmaking as
ratings rose). The ~12-point gap persists.

A7's higher win rate with lower rating is a MATCHMAKING artifact (below),
not evidence A7 is stronger.

## Opponent strength (public LB score of each opponent team)

| | A7 | V22R1 |
| --- | ---: | ---: |
| Opponents mapped | 97/99 | 246/251 |
| Median / mean (full sample) | **1864**/1846 | **1929**/2008 |
| Opp median in our WINS | 1812 | 1857 |
| Opp median in our LOSSES | 1926 | 2081 |

V22R1 faces a much stronger field (median +69, p75 +325, max +165).
At 45.6% vs a 1926-median field it holds 1880; A7 at 61% vs an
1857-median field sits 1859.6. Both ratings are consistent with their
pools: each beats ~1800-rated teams and loses to ~2000+ teams.

## Absolute levels (terminal cash)

| | A7 | V22R1 |
| --- | ---: | ---: |
| Our median / mean | 100,768 / 100,100 | 100,180 / 100,777 |
| Delta median / mean | +414 / +4,263 | −46 / +1,846 |

Identical absolutes (~100k). Positive mean deltas come from blowout
wins vs weak teams; medians show the typical game is close.

## Shared opponents (same team faced by both)

11 teams (full table in decision report §6):
both-win 4, both-lose 2, A7-only-win 4 (BobtheBot369, Dresden 1-0-1,
moonzfxs, 孤寡少年 1-1 vs 0-2), V22R1-only-win 1 (MAOSEN: A7 −$45,
V22R1 +$3,941). Slight A7 edge on shared ground — the rating gap is
pool composition, not head-to-head inferiority.

## A7 loss anatomy (43 public losses; first 32 fully forensicked, 11 new wash-scanned — same families)

- 0 of 32 vs the V3 50-wash. A7's +$1,286 extraction fired in all 6
  live games vs 50-wash (6-0, incl. 4 exact +$1,286).
- 9+ vs trickle-sellers (<4k order units): mean −$5.8k. Largest $-drain.
- ~17 flood-vs-flood second-half collapses (ahead/tied at step 252,
  e.g. +$2,823 → −$6,319): wash-cascade + execution gaps.
- ~6 flat wash-ledger mirrors (−$34..−$2,055, decided by step 252).
- New batch (11): same wash families (7/2 ×4, 20/15 ×3, 10/10 ×2);
  worst: Chaoqi Luo −$11,170 (20/15), Rohit Kumar Sahoo −$6,352 (20/15+seed).
- The 1800–1900 band is a V3-clone mirror world: 12+ losses within
  $1,000; wins equally thin at the top of the pool.

## V22R1 loss anatomy (128 public losses)

Same families (7/2: 1–28; 20/15: 1–15; 10/10: 3–8; 50-mirrors: 1–6;
30-wash: 0–2). V22R1 opens 50/50 (101/101 kept) — V3-regime opening;
AEC market timing does not prevent trickle losses (JR −$13,785).

## Rating dynamics note

V22R1's publicScore moved 1875.0 → 1880.3 during observation:
simulation-ladder scores update as games complete. A7 (6h live, 82
games) is still early-sample; its rating under-samples the 2000+
bracket it must beat to climb.
