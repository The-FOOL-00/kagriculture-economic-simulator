# V27 — HISTORICAL STABILITY REPORT (Cohorts A / B / C)

Source data: `results/v27_historical_matches.jsonl` (120 records, built by
`scripts/v27_build_historical_dataset.py` from vendored checkpoints).
Statistics: `results/v27_historical_stats.json`
(`scripts/v27_historical_stability.py`, RNG seed 27, 10k bootstraps).

## 1. Forensic validation of published numbers

| Cohort | Published mean | Checkpoint mean | Published median | Checkpoint |
| :--- | ---: | ---: | ---: | ---: |
| A (249430..49) | +1,300.70 | +1,300.70 ✓ | +1,300 | +1,300 ✓ |
| B (249450..69) | +453.77 | +453.77 ✓ | +424.50 | +424.50 ✓ |
| C (249470..89) | −218.75 | −218.75 ✓ | −287.0 | −287.0 ✓ |

Means, medians, min/max all reproduce exactly. Standard deviations
reproduce once V25's population-σ convention (ddof=0) is accounted for
(A: 149.64 ✓, B: 3,173.40 ✓).

### 1.1 W/L/T rule reverse-engineered (material)

V25's published W/L/T counts do NOT use exact-zero ties. They are exactly
reproduced by a **tie rule |delta| ≤ $500**. Correction (same session):
the rule WAS preregistered in `V25_BACKBONE_PREREGISTRATION.md` §4
(Win Δ>+500 / Loss Δ<−500 / Tie |Δ|≤500) but omitted from
`V25_FINAL_REPORT.md`, which caused the cross-campaign confusion with
V26's exact-zero convention. V25 followed its own preregistration; V27
preregisters its rule explicitly (§20) and reports both conventions:

| Cohort | Published | Exact-zero recount | \|d\|≤500 recount |
| :--- | :--- | :--- | :--- |
| A | 39W/0L/1T | 40W/0L/0T | 39W/0L/1T ✓ |
| B | 14W/11L/15T | 27W/13L/0T | 14W/11L/15T ✓ |
| C (unpublished) | — | 18W/22L/0T | 10W/17L/13T |

There are **zero exact ties** in all 120 historical matches. V26 used
exact-zero ties (its 18 ties were bit-exact zero-commit matches). V27
reports exact-zero as primary with the margin-500 rule as sensitivity,
and preregisters the rule explicitly (§20) so no future ambiguity exists.

## 2. Objective A — terminal-cash delta (V25 − V3)

Seed-clustered 95% CIs (20 seeds/cohort; seats within a seed are
near-identical so match-level SEs are reported only for reference).

| Cohort | Mean | Median | SD | Seed CI (mean) | Min | Max | Wilcoxon p |
| :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: |
| A | +1,300.70 | +1,300.0 | 151.6 | [+1,247.5, +1,337.5] | +411 | +1,416 | 2.4e-08 |
| B | +453.77 | +424.5 | 3,213.8 | [−619.6, +1,991.6] | −5,054 | +13,053 | 0.59 |
| C | −218.75 | −287.0 | 932.8 | [−634.1, +179.1] | −1,970 | +1,185 | 0.24 |

- Only cohort A excludes zero. B and C are each individually
  indistinguishable from zero economic effect.
- B's distribution is grotesquely wide (SD 3,214; range spans $18k)
  relative to its mean (+454). One seed (249463, ≈+$13k both seats)
  contributes most of B's positive mean: without it B's mean falls to
  ≈ −$210 (exploratory, not a preregistered exclusion).
- Tail floors: A +411 (no loss anywhere), B −5,054, C −1,970.
  Lower-tail quantiles (q05/q10): A +1,250/+1,283, B −2,281/−2,063,
  C −1,815/−1,689. Full quantiles in the stats JSON.

## 3. Objective B — head-to-head outcome

| Cohort | Exact-zero W/L/T | Positive rate | Match sign p | Seed pos. rate | Seed sign p |
| :--- | :--- | ---: | ---: | ---: | ---: |
| A | 40W/0L/0T | 1.000 | 1.8e-12 | 20/20 | 1.9e-06 |
| B | 27W/13L/0T | 0.675 | 0.038 | 13/20 | 0.26 |
| C | 18W/22L/0T | 0.450 | 0.64 | 9/20 | 0.82 |

V25's "67.5% positive" confirmation claim (match-level p=0.038) does NOT
survive seed-clustered inference (13/20 seeds, p=0.26). Only cohort A
shows a real head-to-head edge. Reward and winning agree in A (both
dominant) and C (both null); in B the mean is positive but winning is
unproven — the two objectives must stay separate per §9.

## 4. Seat effect: seats are (near-)identical, not independent

| Cohort | Seat-identical seeds | Mean(seat0−seat1) | Max |seat diff| | Seat corr |
| :--- | ---: | ---: | ---: | ---: |
| A | 18/20 | +38.9 | 934 | ~0 (no variance to correlate) |
| B | 17/20 | +267.8 | 5,333 | 0.94 |
| C | 17/20 | −12.0 | 246 | 1.00 |

52/60 seeds produce identical deltas in both seats; 49/60 produce
bit-identical candidate action tapes (shared action digests, all
within-seed — no cross-seed digest sharing). No systematic seat advantage
exists (all seat-difference Wilcoxon p ≥ 0.5). The seat mirror is a
determinism check, not an independent observation: **effective N is 20
seeds per cohort, not 40 matches.**

Notable exceptions for trajectory follow-up:
- B/249450: seat0 +279 vs seat1 −5,054 (the only sign-flipping seat).
- A/249430: +1,345 vs +411. A/249435: +1,208 vs +1,364.
- Three seeds (A/249443, B/249452, C/249471) reach identical deltas via
  *different* action tapes — convergent economics, flagged for ledger.

## 5. Cohort heterogeneity (the central V27 question)

Seed-level pairwise mean differences (cluster bootstrap 95% CI,
10k permutation p on seed means):

| Contrast | Δ of means | 95% CI | Permutation p |
| :--- | ---: | :--- | ---: |
| A − B | +846.9 | [−770.4, +1,920.0] | 0.28 |
| A − C | +1,519.5 | [+1,118.0, +1,925.4] | < 1e-4 |
| B − C | +672.5 | [−498.8, +2,288.9] | 0.49 |

Kruskal-Wallis: p = 3.0e-08 (seed-level). Levene (variances differ):
p = 0.022.

**Compatibility answer:** +1,300.70 (A) and −218.75 (C) are NOT
compatible with one underlying V25 performance distribution
(non-overlapping seed CIs, permutation p < 1e-4). B (+453.77) is
compatible with both only because its confidence interval ([−620,
+1,992]) spans both — B is uninformative-wide, not a bridge. Cohort
sensitivity is real: at minimum, whatever generated cohort A does not
generate cohort C.

## 6. Data-quality findings

1. **Constant `early_idle_rate`.** All 80 V25 records carry the identical
   value 0.2793522267206478 to 16 decimals. Either P3's first-100-step
   idle pattern is perfectly seed-invariant (conceivable: V25 forensics
   report an identical 144-step opening across all 41 route tapes plus
   deterministic hires) or V25's telemetry was computed once and copied.
   V27 trajectory replays recompute this independently (Phase 3); the
   constant is NOT trusted until reproduced.
2. **Digest structure.** 71 unique action digests / 120 records; all 49
   collisions are within-seed seat mirrors. Cross-seed identical deltas
   (e.g. +1,286 on eight A-seeds) always have distinct tapes: delta
   quantization without tape identity.
3. **No exact ties, no missing matches.** 40 records/cohort, seats 20/20,
   ranges exact, all `COMPLETED`, all code hashes equal the frozen P3
   digest `13292582…`.

## 7. What this report does NOT establish

- WHY cohorts differ (no trajectories in checkpoint data: no capital,
  inventory, crop, livestock, market, or length time series). Phases 3–5
  reconstruct these by deterministic replay.
- Whether any single P3 mechanism causes the edge (ablations, Phase 7–8).
- Whether V25 generalizes (prospective virgin cohorts, Phases 10–12).
- Game length / terminal composition (absent from records; replayed next).

## 9. Replay-fidelity audit (post-analysis addendum — read before §8)

After this report's statistics were computed, V27 replayed all 200
historical matches deterministically (`scripts/v27_replay_trajectories.py`)
and discovered that **V25's file-loader tournament methodology is
worker-history-dependent**: a candidate's internal `import main` (the V3
payload) resolves through the process-global module cache, so a reused
pool worker replays a STALE V3 module whose residue depends on which
matches ran earlier in that worker. Evidence:

- Same-queue replay: DISC-P1 40/40, DISC-P2 40/40, DISC-P3 40/40
  bit-exact (rewards + full 720-step digests). V26A1 (hermetic adapter
  loader) 40/40 despite alien worker histories.
- Cross-queue replay: CONF-P3 0/40 (harness ran CONF after DISC tasks;
  V25 ran CONF in a fresh pool). Re-running CONF in a fresh pool with
  V25's queue order (F1) restores 40/40.
- P1 and P3 are behaviorally IDENTICAL programs (AST-equal modulo
  docstring/comments/tempdir prefix); their discovery contrast
  (−55.33 vs +1,300.70) is therefore a pure worker-history artifact:
  P1 tasks ran with fresh/early histories, P3 tasks with
  stale-after-P1/P2 histories.
- History flips individual matches by thousands of dollars (e.g. CONF
  249451/s0: fresh-pool history −1,050 vs post-DISC history +1,286).
- The constant `early_idle_rate` (0.27935… on all 80 V25 rows) DOES
  reproduce in all 200 replays: the first ~99 turns are
  history-independent; divergence emerges later. V25's telemetry is
  exonerated on this point.

**Quarantine decision.** The §2–§5 statistics above remain arithmetically
correct descriptions of the checkpoint files, but cohort A (+1,300.70)
MUST NOT be read as a property of the frozen P3 program — it is the
output of (P3 × stale-worker-history), unreproducible in a clean
context. Cohort B (+453.77) is reproducible only under V25's exact
worker-history regime (fresh pool, P3-only queue). The history-free
program behavior series A′/B′ (`results/v27_fresh_trajectories.jsonl`,
one match per OS process) and the hermetic cohort C are the evidence
base for the V27 ledger, regime decomposition, and all prospective
design. Full audit: `V27_BEHAVIORAL_DELTA_LEDGER.md` §1.

## 8. Consequences for V27 design (updated per §9)

1. All V27 inference is seed-clustered (n=20/cohort); match-level n=40
   figures are reported but never used for uncertainty.
2. (SUPERSEDED by §9 — kept for the record.) An earlier draft required a
   regime theory for "A tight-positive vs C dispersed-null". No such
   theory is needed: A is a harness artifact, not a program regime.
3. The seat mirror is retained as a determinism/integrity check and as a
   paired structure, never as independent N.
4. The |d|≤500 tie convention is documented here and fixed in
   `V27_PREREGISTRATION.md` before any prospective run.
5. All V27 execution uses hermetic loaders (V26 adapters, fresh
   namespace per match, proven history-independent) or one-match-per-
   process isolation. The V25 file-loader pool pattern is BANNED for
   V27 tournaments (committed test enforces adapter hermeticity).


1. All V27 inference is seed-clustered (n=20/cohort); match-level n=40
   figures are reported but never used for uncertainty.
2. Cohort A is a near-degenerate distribution (SD 152, min +411). Any
   regime theory must explain why A is tight and positive while C is
   dispersed and null — "same mechanism, more noise" is insufficient
   without a noise source that also flips the sign.
3. The seat mirror is retained as a determinism/integrity check and as a
   paired structure, never as independent N.
4. The |d|≤500 tie convention is documented here and fixed in
   `V27_PREREGISTRATION.md` before any prospective run.
