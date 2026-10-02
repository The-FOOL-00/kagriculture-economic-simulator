# V58 Meta Drift

Numbers: [META_DRIFT.json](META_DRIFT.json) (from
[replay_database.jsonl](../data/replay_database.jsonl)); September endpoint =
V49 in-sim capture on engine 1.32.7.

## The carrot revolution (mid-August 2026)

| Week | seats | tiles | M/S/W | carrot seats | crew | elite seats |
|------|------:|------:|-------|-------------:|-----:|------------:|
| Jul-W5 | 5,514 | 111 | 24/3/33 | 4,028 | 9 | 0 |
| Aug-W1 | 19,864 | 135 | 24/42/67 | 3,523 | 13 | 181 |
| Aug-W2 | 52,430 | 187 | 21/37/127 | 3,524 | 14 | 336 |
| Aug-W3 | 35,178 | 192 | 19/37/134 | 16,408 | 12 | 1 |
| Aug-W4 | 29,862 | 187 | 12/37/128 | 21,165 | 12 | 0 |
| Aug-W5 | 6,550 | 206 | 12/39/134 | 3,066 | 12 | 0 |
| Sep (V49) | — | 239 | 12/33/163 | route-native | 13 | — (incumbent) |

Three facts:

1. **The elite window (Aug 05-15) sits BEFORE the carrot revolution.**
   All 518 elite seats are carrot-0; the population-wide carrot adoption
   (16k→21k seats) happens Aug-W3/W4, after the last elite seat in this crawl.
2. **The September meta is the child of the revolution, not of the August
   elite.** V49 (M12/C49/W163, crew 13, wash engine) continues the late-August
   direction (melon 24→12, wheat 67→134+, carrot adoption), not the August
   elite lines (M24/S42/W108 or M19/S37/W143, carrot 0).
3. **Elite ratings vanish from the crawl after Aug 15** (coverage artifact or
   ladder churn — unknown). The August families' fate after the revolution is
   unobservable in S1-S3; their executable fossils (P3090/P3000/night_harvest)
   lose to V49 by 25-100k on engine 1.32.7.

## Reading for §28/§30

- V49 does **not** represent an older elite meta. It represents the post-
  revolution meta that the August 3100+ population never played.
- The V58 premise inverts: the historical elite contains no higher structure
  above V49 — V49 is already on the far side of the last observed meta shift.
- A selector over August families would select *stale* routes. The only live
  boundary is inside the September cluster (V49 vs t2945 herd mix), tested by
  the plan tournament.
