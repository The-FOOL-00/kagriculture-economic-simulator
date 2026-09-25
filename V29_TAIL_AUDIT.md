# V29 — TAIL AUDIT (rare events, farm/route fragility)

## 1. Outlier inventory (brief §25)

| Statistic | Value |
| :--- | ---: |
| Max Δ | +$1,989 (340080/seat 1, late wobble) |
| Min Δ | +$583 (340080/seat 0, late wobble) |
| 95th / 5th percentile | +$1,406.5 / +$1,165.5 |
| Top-1 seed contribution share | 2.7% |
| Top-3 seed share | 7.7% |
| Top-5 seed share | 12.7% |
| Mean excluding largest match | +$1,280.3 (vs +$1,289.2) |
| Mean excluding smallest match | +$1,298.1 |
| Trimmed mean (5%) | +$1,289.5 |

No OUTCOME-D overlay: the largest single-seed total is 2.7% of the
grand total. There is NO negative tail at all (min +$583, 80/80 wins)
and no positive tip remotely like V28's +$12,087: the max (+$1,989) is
1.5× the median, not 9×. The result is carried entirely by the mass
(median = q25 = q75 = +$1,286).

## 2. The extremes vs V28's events

- No +$12k-style expansion tip: no leg shows BUY_LAND/sheep-gate
  anatomy (max pasture gap +1; `SHEEP_GATE` class count 0/80).
- No farm-driven loss: min is +$583 (a win). Both extremes sit on ONE
  seed (340080, farm gap −$129): the melon mechanism fired normally on
  both legs (+$1,258 at obs[252]); late reactive-market divergence
  (2 unit / 2 market divs) walked the legs to +583/+1,989. The seed
  mean is exactly +$1,286 — the wobble is mean-preserving.
- No route pathology: V27's 249450-style missing-pasture event does
  not recur; A7 (no route/labor code) exposes no new tail channel.

## 3. Farm/route audit (brief §26)

V3vV3 hermetic controls on all 40 holdout seeds (Arm 4): 34/40 exactly
zero farm gap; nonzero only on 6 seeds with |G| ≤ $219
(+111, +78, −32, −115, −129, −219). G_A == G_V on all 6 (farm
asymmetry is policy-independent, as required).

Loss analysis: there are no losses (80W/0L/0T), so no mechanism-failure
vs farm-disadvantage attribution is needed. The smallest win (+$583,
340080/seat 0) is a wobble leg on a −$129 farm gap with the mechanism
fully intact — farm luck narrows but never threatens the edge on this
slice.

## 4. Catastrophic-loss check

Worst V29 leg +$583 (a win) vs the −$10,000 preregistered floor — the
floor held with infinite margin on the loss side. No match approaches
catastrophic territory from either direction.
