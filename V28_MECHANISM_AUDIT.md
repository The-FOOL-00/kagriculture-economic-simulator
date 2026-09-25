# V28 — MECHANISM AUDIT (measured on virgin records)

Probes: `scripts/v28_mechanism.py` → `results/v28_mechanism.json`;
`scripts/v28_mechanism_detail.py` → `results/v28_mechanism_detail.json`.
Step convention: game-steps for actions (env.run indexing); obs[t] is
the pre-action state at game-step t. (An earlier draft of the probe
scripts labeled env.steps indices; all numbers below are corrected to
game-steps and verified against the counterfactual replay.)

## 1. The typical match (74/80): OPENING → CAPITAL → CROP

Causal timeline (seed 249530/seat 0; identical on all 74):

1. **Initial state:** symmetric farms, both players $3,000.
2. **First divergence (game-step 0):** the treatment itself —
   A7 washes 30/30 (nets +$54), V3 washes 50/50 (nets −$54).
   Money gap +$108 at obs[1], decaying to +$28 by obs[24] (hires).
3. **Immediate consequence (game-step 17):** A7 holds $266 vs V3's
   $158. A7's reactive buyer takes MELON×2 seeds; V3 takes ×1
   (counterfactual CF-V28-2 bisects the ×2 gate at $164.50: V3
   misses it by $6.53, A7 clears it by $101.50).
4. **Medium-term (game-step 18):** identical unit positions; A7's
   6th unit PLANTs the extra MELON where V3 PASSes. This is the
   ONLY unit-action divergence in the entire 720-step game
   (1/719 turns); market actions diverge exactly twice (steps 0, 17).
5. **Terminal consequence (obs[252]):** the extra melon harvests —
   A7 +$2,050 vs V3 +$792 that step. The gap jumps +$28 → +$1,286
   in ONE step and never moves again (identical play, identical
   end structures: 17/17 pastures, 11/11 hands, 3/3 quads).

Classification: **OPENING/CAPITAL** (wash savings buy a discrete
production asset; harvest realization). The V27 exploratory account
is confirmed in its essentials but sharpened: the "wash-path fill
cascade" resolves to a single quantifiable asset (one melon plant,
+$1,258 harvest), and the "late reactive market" channel carries
$0 on typical seeds — the game is decided by obs[252].

## 2. The +1,369 variant (4/80): same mechanism, richer harvest

Seeds 249542, 249564 (both seats): identical divergence anatomy
(steps 0/17/18, 2 unit divs, 2 market divs, identical structures).
The t=252 jump pays +$1,341 instead of +$1,258 (harvest price/yield
noise on the same extra melon). Classification: OPENING/CAPITAL.

## 3. Seed 249533 (+442/+2,130): MARKET micro-butterfly

Farm gap 0; structures identical (17/17, 11/11, 3/3). The melon
mechanism fires normally (+$1,286 at obs[288] both seats); then
SIX late market micro-divergences (game-steps 479/493/577/598:
strawberry sale sizing 4-vs-6 etc.) walk the seats to +442/+2,130.
Seed-mean exactly +$1,286. Classification: **MARKET** (late
reactive-seller wobble; no structural divergence at any point).

## 4. Seed 249534 (−1,528/+12,087): EXPANSION tip + FARM deficit

Farm gap −$6,267 (V3vV3: farm1 richer, program-independent).

- **Seat 1 (+$12,087):** at game-step 289 A7's cash ($11,948)
  clears the reactive expansion gate (bisected at $10,438.35 —
  the SAME $10,438 gate V27 found on 249463) and fires BUY_LAND +
  SHEEP×6 + HIRE×2; V3 ($9,916) misses by $522. A7 invests
  (money dips below V3 mid-game), builds 23 vs 16 pastures and a
  4th quadrant, overtakes at t≈456, ends +$12,087. Counterfactual
  CF-V28-1 proves the branch is purely state-driven (brain swaps).
  Classification: **EXPANSION** (cash-gated sheep branch).
- **Seat 0 (−$1,528):** A7 plays the poorer farm0. The melon fires
  (+$1,255 at obs[252]) but the farm deficit grinds it down.
  Farm-purged program effects: +$4,739/+5,820 (mean +$5,279.5 =
  the seed mean; per-farm splits are market-regime-confounded, so
  the seed mean is the honest farm-robust read).
  Classification: **FARM** (poorer-farm grind; mechanism intact).

## 5. Seed 249544 (−3,154/+5,726): FARM deficit, no gate

Farm gap −$10,965, the deepest in the cohort. No expansion gate
fires on either seat (market windows show sells/hires only).
A7's farm0 (seat 0) trails V3's farm1 by one pasture all game
(17→16 vs 18→17) and loses slowly on animal-product flows
(MILK 3-vs-6, 6-vs-12; WOOL 6-vs-10). The melon mechanism still
fires on BOTH seats (+$1,394/+1,178 at obs[252]); seed-mean
exactly +$1,286. Classification: **FARM** (no route failure, no
missing BUILD — just a structurally poorer farm; cf. V27's 249450
route event, which does NOT recur here).

## 6. Loss audit (the 2 V28 losses)

Both losses are seat-0 legs on farm-gap seeds (249534, 249544):
A7 on the poorer farm, losing to V3 on the richer farm. In both,
(a) the melon mechanism fired normally, (b) farm-purged and
seed-mean program effects are strongly positive (+$5,279.5 and
+$1,286), (c) no A7-specific defect (no missed gate, no bad route,
no dispatch error — A7 has no dispatch code) is visible. The
losses are farm luck, not mechanism failure.

## 7. What V27 got right and wrong

- RIGHT: the additive story (qty + init kept by A7), the
  irrelevance of dispatch (A7 has none), the existence of $10,438
  expansion gates, the t≈252 medium-horizon emergence window.
- SHARPENED: the typical +$1,286 is not a "fill cascade" in any
  diffuse sense — it is ONE melon plant (game-step 17/18 asset
  acquisition, obs[252] harvest). Late reactive markets carry $0
  typically (V27's A3-vs-A7 t=433 market divergence describes the
  P3-bypass pathology, not A7's typical win).
- The V28 tip (249534/s1) is the second independent observation of
  the $10,438 sheep gate (after V27's 249463), now with a
  treatment-driven clearance.
