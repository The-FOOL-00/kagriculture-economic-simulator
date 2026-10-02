# V29 — FINAL REPORT: A7 PROTECTED-HOLDOUT PROMOTION GATE + ABSOLUTE-LEVEL DECOMPOSITION

## 1. Executive conclusion

**OUTCOME B: A7 won all 80 holdout legs against V3 (+$1,289 mean, 6/6 gates pass, 80/80 canonical mechanism) but creates ZERO absolute economic value (A7vA7 ≡ V3vV3 to the dollar on all 40 seeds) — a confirmed competitive response, NOT promoted.**

## 2. V28 evidence entering V29

V28 (OUTCOME A): frozen A7 vs frozen V3 on virgin seeds 249530..249569
(80 matches): mean +$1,389.99, median +$1,286, 78W/2L/0T, seed-positive
40/40, seed CI [+$1,188, +$1,592], all six gates passed; typical win via
the one-melon chain (74/80); top-1 share 9.5% (not tail-dependent).
V27 exploratory: ≈+$1,451. Both served V29 as replication references
only — no tuning input.

## 3. Frozen artifacts

| Artifact | Hash / commit |
| :--- | :--- |
| V29 prereg commit | `d818fb1c7cf6bc4903cade75bad7e78d191b7ac8` (before first holdout match) |
| V29 prereg SHA256 | `ab6673d0…cc948` |
| A7 source | `18d2c8ea…e7ae9` (unchanged since V27 Stage A) |
| V3 payload | `845e0d10…bf18943` |
| V28 raw (re-verified) | `2efb4446…f21082` |
| V29 raw (160 rows) | `565f1198…faa23bc` |
| Engine / Python | `kaggle_environments==1.32.7` / 3.14.4 |
| V22R1 (fallback) | commit `33763a8…`, archive `6b879b3e…` — re-verified, untouched |

A7/V3 bytes, all six adapter dependency hashes, harness protocol, and
statistics frozen; every V29 record carries A7/V3/sim/harness digests.

## 4. Holdout governance

Authorized slice `340050..340089` (40 seeds) consumed; remainder
`340090..340199` verified untouched before, during (runner hard-refusal
+ analyzer/test assertions), and after the campaign. Pre-campaign scan:
0 seed-field hits in all results JSONL/CSV, 0 interior literals except
resolved false positives (range boundaries, replay timestamp/hash
noise, V28's authorization pointer); neighbor AEC cohorts verified
disjoint. Manifest: `V29_COHORT_MANIFEST.json`.

## 5. Preregistration

`V29_PREREGISTRATION.md` (committed `d818fb1`): primary endpoint paired
Δ = A7−V3 on Arms 1+2; six gates copied EXACTLY from V28 (no threshold
eased); 160 matches (40×A1 + 40×A2 + 40×A3 + 40×A4); seed-clustered
t-CI inference; decomposition math frozen by reference to
`V29_ABSOLUTE_LEVEL_SPEC.md` (`m = CREATE + EXTRACT` identity);
tail/overlay rules; failure mapping (A/B/C/D); no-retuning rule; stop
conditions; preregistered 14-instance rerun subset. Never edited after
holdout results appeared.

## 6. Integrity validation

- Isolation regression: 7/7 contexts × 4 arms invariant (44 runs, 2
  consumed seeds; P3-primer pattern dead; `sys.modules` clean).
- Serial/pool parity: 8/8 bit-exact (+ subprocess parity in tests).
- Tournament: 160/160 distinct pids+nonces (fresh process per match).
- Independent rerun: 14/14 exact (preregistered subset, fresh
  interpreters, no cache).
- Rewrite deployed: 80/80 A7vV3 legs + 80/80 A7 self-play instances;
  0 unexpected shapes.
- Tests: 81/81 green (29 V29 + 16 V28 + 26 V27 + 10 V26-backbone).
  One stale-test maintenance was required (see §15).

## 7. Primary A7 vs V3 holdout result

Mean **+$1,289.18**, median +$1,286, SD $156 (match) / $15 (seed),
W/L/T **80/0/0** (exact and |Δ|≤$500), posrate 1.000, seed-positive
40/40, min +$583, max +$1,989, q05/q95 +$1,166/+$1,407, trimmed mean
+$1,289.5, bootstrap CI [+$1,286, +$1,295], Wilcoxon p = 7.6e−17.
Third quantitative replication (V27 ≈+$1,451 → V28 +$1,390 → V29
+$1,289; median +$1,286 all three; V29 seed-SD 10× tighter at $15).

## 8. Six-gate decision

| Gate | Result |
| :--- | :--- |
| 1. Mean > 0 (+$1,289.18) | PASS |
| 2. Median > 0 (+$1,286) | PASS |
| 3. Posrate > 50% (80/80) | PASS |
| 4. W > L (80/0/0) | PASS |
| 5. Seed CI > 0 ([+$1,284, +$1,294]) | PASS |
| 6. Floor > −$10k (+$583) | PASS |

**6/6 → primary PASSES.** No tail-dependence overlay (top-1 share 2.7%).

## 9. A7 self-play

Mean terminal cash $94,574.78; both seats identical on 34/40 seeds
(6 tiny farm gaps, |G|≤$219, policy-independent); full 720-step money
and structural trajectories recorded per seed.

## 10. V3 self-play

Mean terminal cash $94,574.78 — identical to A7vA7 to the cent.
Farm gaps identical to A7vA7's on all 6 nonzero seeds (`G_A == G_V`).

## 11. Create/extract decomposition

`CREATE = $0.00` exactly (SD $0.00, CI [$0,$0], 0/40 seeds positive,
per-seat `C_0 = C_1 = $0`); `EXTRACT = +$1,289.18` (100% share).
A7vA7 and V3vV3 trajectories are identical at ALL 720 steps on 40/40
seeds; actions differ ONLY at step 0 (the wash). Wash ledger at obs[1]:
30-vs-50 → +$54/−$54 (zero-sum between washers); 30-vs-30 and 50-vs-50
→ $0/$0. The symmetric wash size is a complete downstream no-op; wash
size matters ONLY relatively. Head-to-head games reach ±tens of
thousands different absolute wealth than self-play on the same seed
(common-mode regime effect, either direction) with the differential
pinned at ≈+$1,286. All six brief-§22 questions answered cleanly
(pure extraction, zero creation, every seed, both seats).

## 12. Mechanism replication

80/80 legs CANONICAL_MELON (100%): cash17 +$108, melon-seed +1,
melon-plant +1, first unit div step 18, first market div step 17,
harvest +$1,258 at obs[252] (78 legs; +$1,341 on 340068 both seats).
16 legs carry late micro-wobble (2–3 unit divs), mean-preserving at
seed level. V28's 74/80 "typical win" upgraded to universal on this
slice. Contribution: CANONICAL_MELON 100% of +$103,134; all other
classes 0 legs.

## 13. Tail behavior

No negative tail (min +$583, a win); no +$12k tip (max +$1,989, 1.5×
median); both extremes on one wobble seed (340080, seed mean +$1,286).
Top-1/3/5 shares 2.7%/7.7%/12.7%; means excluding extremes within $9
of the primary. No sheep gate (0/80), no route pathology, no farm
loss (worst farm gap −$219).

## 14. Failure analysis

There are no failures to attribute: 80W/0L/0T. The smallest win (+$583)
is a wobble leg with the mechanism fully intact on a −$129 farm gap.
Farm-quality disadvantage (V28's loss mode) is absent as a loss cause
on this slice; farm gaps ≤ |$219| merely modulate wobble seeds.

## 15. Promotion conclusion

**OUTCOME B — A7 NOT PROMOTED.** All six gates and all integrity checks
pass, but the preregistered OUTCOME-B pattern triggered on BOTH clauses
(`Cbar = $0 ≤ 0`; `Ebar/M = 100% ≥ 50%`): A7 beats V3 80/80 on the
holdout while creating zero absolute value. A7 is CONFIRMED AS A
COMPETITIVE RESPONSE (a solved positional edge in the opening-wash
game), not a general economic-dominance candidate. The catastrophic
veto did not trigger (C is exactly 0, not significantly negative);
this is weakness-by-absence-of-creation, not predation.

Stale-test note (transparency): `tests/test_v28_freeze.py::test_cohort_
quarantine` (unbounded `seed ≥ 249530` scan, predating V29) false-
positived on V29's authorized 340050+ outputs — offender list contained
ONLY post-V28 V29 rows. Minimal maintenance applied: V29 own-files join
the test's existing name-allowlist convention (its docstring scopes it
to "pre-V28 artifacts"). Verified: suite green (81/81), and a planted-
violation mutation probe still FAILS as required. V28's protection over
pre-V29 files is byte-identical. No V28 evidence, result, spec, or
candidate byte was altered.

## 16. Explicit non-conclusions

- This does NOT show A7 is useless: an 80/80 +$1.3k head-to-head edge
  is real, replicated 3×, and exactly characterized.
- This does NOT show A7 would fail on Kaggle: leaderboard opponents
  play V3-like openers, not A7 mirrors — positional edges score when
  opponents don't mirror them. It DOES show the edge evaporates under
  mirroring (AEC/self-play deployment caveat).
- This does NOT prove all wash sizes are equivalent: only 30-vs-50
  (asymmetric, tested) and symmetric 30/50 (identical, tested) are
  characterized; other sizes/thresholds untested (§28 forbade tuning).
- This does NOT explain WHY symmetric 30/50 paths coincide to the
  dollar (exact cancellation mechanism unprobed) or why asymmetric
  openings trigger ±$80k common-mode regime shifts — both are now
  sharp open questions with frozen data to attack them.
- A7 is not globally optimal, not guaranteed leaderboard-top-10, not
  universally better than every agent; AEC necessity is unaddressed.

## 17. Next step

**V30: pre-registered symmetric-wash-equivalence probe + common-mode
regime characterization on a fresh protected slice** — one experiment
testing (a) whether the A3≡A4 to-the-dollar identity and wash zero-sum
ledger replicate off-slice, and (b) what tips asymmetric-opening games
into ±wealth regimes (early money-path divergence mapping), before any
packaging or AEC-substrate decision on A7.
