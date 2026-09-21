# V27 — REGIME DECOMPOSITION & COHORT-SENSITIVITY RESOLUTION

## 1. Headline: there is no regime to decompose (artifact removed)

On the history-free series (A′/B/C), the three cohorts are mutually
compatible with ONE null-ish high-variance distribution:

| Cohort | Seed-mean | Seed 95% CI | Seed sign | Sign p |
| :--- | ---: | :--- | ---: | ---: |
| A′ | −55.3 | [−670.5, +479.6] | 12/20 | 0.50 |
| B | +453.8 | [−628.5, +2,050.5] | 13/20 | 0.26 |
| C | −218.8 | [−634.0, +185.9] | 9/20 | 0.82 |

Kruskal-Wallis (seed) p=0.57; Levene p=0.35; pairwise permutation
A−B p=0.65, A−C p=0.66, B−C p=0.49. The V27 brief's central question —
"how compatible are +1300/+454/−219 with one distribution?" — is
superseded: the +1300 was P2-residue artifact (see ledger §1). The
corrected triple (−55/+454/−219) shows no cohort heterogeneity at all.
Cohort sensitivity, as a property of the P3 PROGRAM, is not real. What
remains is high seed variance (SD ≈ $1–3k) around a ≈$0 mean.

## 2. Early-state features tested (all pre-outcome; all null)

| Feature | Finding |
| :--- | :--- |
| Money gap t=24 | CONSTANT +$28.0 all 120 matches (no variance → no signal) |
| Money gap t=144 | +$28.0 (117/120) or −$163 (3 farm-outlier legs) |
| Money gap t=252/288/432 | corr with terminal −0.30/−0.02/−0.69 (all); −0.24/−0.29/+0.40 (excl. monsters); sign agreement ≈ base rate 0.57 |
| Chore dose (5..17 waters) | corr +0.21 excl. 249463 / −0.14 incl. — sign-unstable, no claim |
| First-3 shop set | ~55 distinct sets over 60 seeds; max cell n=6 — no stratification |
| Seat | no systematic effect (Phase 2; farm gaps 0 on 54/60) |
| Farm gap (V3v3) | 0 on 54/60; the 6 nonzero are not predictable pre-game |

Early economy (t≤144) is seed-invariant scripted play; terminal
variance emerges mid-game (t≈252+) through reactive-market divergence
and rare threshold tips. No early observable predicts the terminal
sign above base rate. Classifying "regimes" post-hoc from terminal
outcomes (e.g. "tip seeds") would violate §22; the only
pre-outcome-visible structure (the +$108→+$28 deterministic lead) has
no variance to predict with.

## 3. The §13 mechanism checklist (measured, not assumed)

| Claimed mechanism | Measurement | Verdict |
| :--- | :--- | :--- |
| 30-unit wheat opening | +$54.00 vs −$54.00, all 120 | REAL, deterministic +$108; terminal leverage unidentified observationally (constant treatment) → ablation A1/A2 |
| Preserved liquid capital | +$28 through t=144 | REAL but tiny; dissipates into harvest economy |
| Lower early slippage | same as opening (lockstep) | REAL, +$108 |
| Zero-inventory in-place labor | +12 WATER / −13 PASS median; DIG 0 | REAL footprint; no dose-response → ablation A3 |
| Coherent macro coupling | no such code in P3 (125 lines: wash + dispatch) | NOT A MECHANISM (prose only) |
| Livestock/crop interaction | no such code; pasture/crop gaps 0 | NOT A MECHANISM |
| Early capital velocity | +$881 by t=288 on 249463 only | n=1; threshold tip, not a general velocity effect |

Frequency/conditional analyses (§13.1–4) are possible only for wash
(always differs, constant effect) and chores (always differs by 5–17,
no outcome gradient). Positive and negative outcomes do NOT differ in
mechanism frequency — both show the same +$108/+12-chore signature.

## 4. Cohort-by-cohort causal narrative (§14)

**A′ (−$55, 24W/16L, SD $1,336):** 20 seeds of micro-wobble. Opening
+$108, ~12 waters, identical structures, wheat-order shortfall −27,
late reactive-market churn. Largest |Δ| $4,023 (249434, both seats —
a within-program reactive swing, farm gap 0). Nothing tips. Mean −$55
is noise around zero (CI [−671, +480]).

**B (+$454, 27W/13L, SD $3,198):** 18 typical seeds (≈ −$210 mean
without monsters) + one +$13k reactive tip (249463: cash-gated sheep
branch at t=289, both seats, farm gap 0 — P3's early cash tips V3's own
branch) + one −$5k farm route (249450/seat1: missing t=33 pasture
BUILD in farm1's route; V3v3 gap +$6,893). The +$454 mean is
12×$1k-noise + 1 tip + 1 farm artifact. Fragile by construction.

**C (−$219, 18W/22L, SD $933):** 20 seeds of micro-wobble, hermetic
adapters. Same signature as A′ (opening, chores, wheat orders, zero
structural gaps). Mean −$219 is noise (CI [−634, +186]).

**Did V25 deploy capital differently by cohort?** No — opening,
hires, animals, plants identical across cohorts (all gaps 0 except
the two B events). **Did markets evolve differently?** Only through
seed-chaotic reactive churn, not cohort regimes. **Did P3 enter
different macro states?** Only on 249463 (tip) and 249450/seat1
(farm route). The "different regimes" hypothesis is rejected: the
same micro-signature appears in all 60 seeds; cohort means differ by
luck of rare events.

## 5. What WOULD constitute a regime (not observed)

A defensible V25-favorable regime would need: (a) a pre-outcome
feature, (b) varying across seeds, (c) interacting with a P3-specific
mechanism, (d) replicating prospectively. (a) fails for the wash
(constant); (b) fails for early gaps (constant); (c) fails for
livestock/sales/coupling (no such code); the 249463 threshold pattern
(a′) large pre-window lead → tip is n=1 and fires through V3-shared
reactive code (either player can tip it with cash). No (a)–(d) regime
exists in the historical data. The preregistration accordingly carries
NO confirmatory regime gate; the t=288-lead pattern is recorded as an
exploratory (non-gating) watchlist item with explicit n=1 provenance.

## 6. Implication for §27 decision states

The evidence as of Phase 5 points between OUTCOME C
(cohort-sensitive — now better read as "seed-noise-dominated, no
stable edge") and OUTCOME E (difference small relative to variance):
pooled program effect +$60 against seed-SD ≈ $2,100. The prospective
hermetic cohorts (Phases 10–12) exist to confirm the null rather than
to rescue an edge. If fresh data reproduces ≈$0 ± $300, V25 must NOT
replace V3, and no V25-native AEC is justified (OUTCOME E, possibly
hardening to D on replication of the null with tight CI).
