# V28 — TAIL AUDIT (rare events, farm/route fragility)

## 1. Outlier inventory (§23)

| Statistic | Value |
| :--- | ---: |
| Max Δ | +$12,087 (249534/seat 1, expansion tip) |
| Min Δ | −$3,154 (249544/seat 0, poor-farm grind) |
| 95th / 5th percentile | +$1,369 / +$1,286 |
| Top-1 seed contribution share | 9.5% ($10,559 / $111,199) |
| Top-3 seed share | 14.4% |
| Mean excluding largest match | +$1,254.6 (vs +$1,390.0) |
| Mean excluding smallest match | +$1,447.5 |
| Trimmed mean (5%) | +$1,289.5 |

No OUTCOME-D overlay: the largest single-seed total ($10,559) is far
below 50% of the grand total. Removing the tip match still leaves a
mean of +$1,254.6 with 77 wins. The result is NOT tail-dependent —
the tail diagnostic inverts the usual worry: the mass (74/80 at
exactly +$1,286) carries the result, and the tails are symmetric
noise around it (one +$12k tip, two farm-driven partial offsets).

## 2. The +$12,087 event vs V27's +$13k butterfly

Analogous in kind (cash-gated $10,438 sheep expansion, ≈20–400×
butterfly), different in role: V27's 249463 tip DOMINATED its cohort
mean; V28's 249534 tip contributes 9.5% of a mean that stands without
it. The gate itself replicated (same threshold $10,438, same bundle),
which upgrades it from an n=1 curiosity to a characterized reactive
branch — now observed tipping FOR the treatment on a virgin seed.

## 3. Farm/route audit (§24)

V3vV3 hermetic controls on all 40 virgin seeds
(`results/v28_farm_gaps.jsonl`): 38/40 exactly zero; nonzero only
249534 (−$6,267) and 249544 (−$10,965). Both of V28's losses sit on
these two seeds' poorer farms.

- 249544/seat 0 (−$3,154): gradual animal-product grind (one fewer
  pasture all game), NO route failure, NO missing BUILD event. V27's
  249450-style missing-pasture route pathology does NOT recur.
- 249534/seat 0 (−$1,528): same pattern on a milder farm gap.
- 249533 (seat-asymmetric WITHOUT a farm gap): late-market wobble
  only; structures identical. Farm symmetry does not imply
  seat-identical reactive play, but the seed-mean (+$1,286) is
  unaffected.

A7 exposes no latent route fragility: on farm-gap seeds the A7
mechanism (melon) still fires normally on BOTH farms
(+$1,255/+1,419 and +$1,394/+1,178 at obs[252]); what differs is the
farm trajectory underneath it. Land allocation, expansion, worker
routing, and placement are V3's own code on both sides (A7 has no
route/labor logic), so no A7-specific tail channel exists by
construction — and none is observed.

## 4. Catastrophic-loss check

Worst V28 loss −$3,154 (vs the −$10,000 preregistered floor and V27's
−$5,054 worst). No match approaches catastrophic territory. The loss
legs are bounded farm deficits with the +$1.3k mechanism still
firing — the floor held with 3× margin.
