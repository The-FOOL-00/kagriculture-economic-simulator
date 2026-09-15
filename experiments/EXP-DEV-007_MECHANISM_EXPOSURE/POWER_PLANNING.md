# POWER / PRECISION PLANNING: EXP-DEV-007_MECHANISM_EXPOSURE

**Experiment**: `EXP-DEV-007_MECHANISM_EXPOSURE`
**Date**: 2026-09-15
**Status**: PRE-REGISTRATION (planning exercise only — no seeds executed, no outcomes observed)
**Planning trigger-rate basis**: fresh-cohort observed 2/100 (Discovery 248xxx 2/50,
Qualification 50050–50099 0/50); retrospective 247xxx 2/50 shown for context only.

This document records the sample-size reasoning that fixes N **before** the seed
block is selected and before any execution. N must not be changed on the basis of
any observed result.

---

## 1. Candidate cohort sizes

| N | Games (4/seed) | Est. runtime @2.2 s/game |
|---|---|---|
| 250 | 1,000 | ~37 min |
| **500 (SELECTED)** | **2,000** | **~73 min** |
| 750 | 3,000 | ~110 min |
| 1000 | 4,000 | ~147 min |

Runtime basis (recorded, not re-measured): Discovery manifest 200 games in 425 s
(2.13 s/game); Qualification manifest 200 games in 438 s (2.19 s/game).
Plus ~10 min parity re-validation and ~1–2 min per 10 forensically traced seeds.
All candidates fit a single session; runtime is not the binding constraint.

## 2. Exposure planning (binomial, exact)

X ~ Binomial(N, p). Trigger = qualifying late-entry event on a seed (see
PROTOCOL.md §4). Planning rates 1% / 2% / 3% bracket the fresh-cohort
observation (2%) with a pessimistic and an optimistic scenario.

| N | p | E[X] | P(X=0) | P(X>=5) | P(X>=10) |
|---|---|---|---|---|---|
| 250 | 1% | 2.5 | 0.081059 | 0.107812 | 0.000250 |
| 250 | 2% | 5.0 | 0.006405 | 0.561281 | 0.030375 |
| 250 | 3% | 7.5 | 0.000493 | 0.871798 | 0.220952 |
| 500 | 1% | 5.0 | 0.006570 | 0.560389 | 0.031102 |
| 500 | 2% | 10.0 | 0.000041 | 0.971877 | 0.543336 |
| 500 | 3% | 15.0 | 0.000000 | 0.999246 | 0.933071 |
| 750 | 1% | 7.5 | 0.000533 | 0.869218 | 0.222727 |
| 750 | 2% | 15.0 | 0.000000 | 0.999212 | 0.932095 |
| 750 | 3% | 22.5 | 0.000000 | 0.999998 | 0.999031 |
| 1000 | 1% | 10.0 | 0.000043 | 0.971314 | 0.542699 |
| 1000 | 2% | 20.0 | 0.000000 | 0.999985 | 0.995319 |
| 1000 | 3% | 30.0 | 0.000000 | 1.000000 | 0.999994 |

Computed 2026-09-15 with exact integer binomial arithmetic
(`math.comb`; no simulation, no seeds executed).

## 3. Decision: N = 500

**Selected N: 500.**

Reasons:

1. At the empirical planning rate (2%), N=500 gives E[X]=10 exposures with
   P(X>=5)=97% and P(X=0)≈0 — a reasonable chance of *multiple* exposure
   events, which is the experiment's stated purpose.
2. At the pessimistic rate (1%), N=500 still gives E[X]=5, P(X>=5)=56%,
   P(X=0)<1% — the mechanism remains testable in the bad case.
3. N=250 fails the purpose test: at 1–2% it offers only an 11–56% chance of
   >=5 exposures and up to 8% zero-exposure risk. REJECTED.
4. N=750/1000 buy insurance concentrated in the pessimistic world (at 1%,
   P(X>=10) rises to 22%/54%) and tighter incidence intervals, at 1.5–2x
   operational cost. The mechanism question does not require >=10 exposures:
   >=5 well-traced exposures with consistent prevention, added to the existing
   4/4 cross-cohort evidence, already answers "does the guard prevent the
   damage when exposed". The marginal information does not justify the extra
   operational surface (longer single run, larger forensic load, larger
   re-run cost if the harness faults). REJECTED.

## 4. Incidence precision (Clopper-Pearson exact 95% CI, N=500)

| Observed k | 95% CI for P(trigger) |
|---|---|
| 0 | [0.000%, 0.735%] |
| 2 | [0.048%, 1.437%] |
| 5 | [0.325%, 2.318%] |
| 10 | [0.963%, 3.647%] |
| 15 | [1.689%, 4.900%] |
| 20 | [2.460%, 6.110%] |

Even k=0 is informative: it would bound the trigger rate below 0.74% and the
report would read "mechanism not exposed in this cohort" per the frozen stop
rule — an acceptable scientific outcome, not a failure.

## 5. Unconditional-performance precision (Estimand 1)

Observed cross-seed SD in prior cohorts: ~1,470–3,170.

| SD | N=500 SE | 95% half-width | N=1000 SE | 95% half-width |
|---|---|---|---|---|
| 1,500 | 67 | ~131 | 47 | ~93 |
| 2,000 | 89 | ~175 | 63 | ~124 |
| 3,200 | 143 | ~280 | 101 | ~198 |

No significance is promised. With the established trimmed-mean-$0 structure,
a significant unconditional mean requires a large concentrated mean; the
experiment is powered for *exposure and incidence*, and the unconditional
estimand is reported honestly whatever it shows.

## 6. Conditional-effect precision (Estimand 3)

Precision here is governed by realized k, which is random. Scenarios at N=500,
assuming per-exposure prevention of roughly $5k–$8k (prior magnitude) with
within-exposure SD ~$3k: k=5 gives SE ~$1,340; k=10 gives SE ~$950. These are
illustrative only — no power claim is made, and the conditional analysis uses
explicitly non-causal language (see PROTOCOL.md §5).

## 7. Planning integrity statement

- No experimental seed was executed to produce this document.
- No candidate-cohort outcome exists; none was inspected.
- N=500 is fixed by this freeze. Cohort resizing after observing results is
  forbidden by PROTOCOL.md §8.
