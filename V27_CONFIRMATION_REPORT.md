# V27 — STAGE B CONFIRMATION REPORT (virgin 249510..249529)

Runner: `scripts/v27_prospective_tournament.py B` (same frozen bytes as
Stage A; runner asserts P3/V3/engine hashes at startup). Data:
`results/v27_confirmation_matches.jsonl` (40/40 complete). No code
changes after Stage A (freeze record in V27_DISCOVERY_REPORT.md §5
still current).

## 1. Result vs preregistered gates (§4)

| Gate | Required | Measured | Verdict |
| :--- | :--- | ---: | :--- |
| 1. Mean paired Δ > 0 | > 0 | **−469.85** | FAIL |
| 2. Median > 0 | > 0 | −100.0 | FAIL |
| 3. Positive rate > 50% | ≥21/40 | 18/40 (0.45) | FAIL |
| 4. Wins > losses | W>L | 18W/22L/0T | FAIL |
| 5. Tail floor > −$10k | min > −10,000 | −4,098 | PASS |
| 6. Seed-positive > 50% | ≥11/20 | 9/20 | FAIL |

Non-gating: seed-mean 95% CI **[−1,030.0, −10.4]** (entirely
negative); Wilcoxon p=0.15; seed sign p=0.82; margin-500 W/L/T
6/12/22; seat-identical 19/20 (sole exception 249516: +272/+192,
diff 80 < $300 → no farm check per §3); watchlist corr(g288,
terminal) = −0.04 (g288 all +425..+1,369, terminals mixed — pattern
refuted again); max +683 (no tip).

Per-seed (seat0/seat1): 249510 −118; 249511 +505; 249512 −1,409;
249513 −828; 249514 +121; 249515 −186; 249516 +272/+192; 249517 +505;
249518 −82; 249519 −358; 249520 −500; 249521 −2,855; 249522 +276;
249523 −4,098; 249524 −1,486; 249525 +287; 249526 +403; 249527 +683;
249528 +228; 249529 −717.

## 2. Pooled prospective (A+B, 80 matches / 40 virgin seeds)

Mean **−433.9**, median −164.0, SD 988.5, seed CI **[−747.0, −151.6]**,
W/L 30/50, seed-positive 15/40. The pooled virgin evidence excludes
zero on the negative side: P3 does not merely fail to beat V3 — it
loses to V3 by $150–$750 (95% seed CI) on unseen seeds.

## 3. Decision mapping (prereg §6)

"1+ gates fail with negative mean and seed CI excluding large positive
values → OUTCOME D." Five gates fail, the mean is negative, and the
seed CI excludes zero itself (let alone large positive values).
**OUTCOME D: V25 FAILED TO GENERALIZE.** V3 remains the stronger
validated backbone. No V25-native AEC is justified. (Consistent with
the ablation additive model: P3 = qty(+$1,500) − init(−$1,450) ≈ $0 +
seed-luck residual; prospective residual −$434.)

## 4. Integrity notes

- 40/40 matches COMPLETED, no crashes, no illegal actions.
- Determinism: 19/20 seat-identical (one benign 80-diff); runner
  checkpointed and resumable; digests recorded per match.
- Cohort isolation: 249510..529 used only here; 249530+ untouched;
  holdouts untouched (firewall test green).
