# V30 REPLAY FORENSICS

## 1. Live corpus (49 Eldritch games + tetsuya + misc, engine 1.32.7)

- Scale: live absolutes 24k-180k; V3 local range 54k-147k. Same scale.
- Highest live single-game score (Eldritch 180,191, ep 107511511) came
  against a collapsed 43,877 opponent: empty-market farming, not frontier
  capability. V3-vs-PASSIVE on that exact seed = 159,487 (same effect).
- Full same-seed deconfound (6 seeds): V3-vs-weak matches/exceeds live-best
  in 6/6 (159 vs 180, 165 vs 175, 152 vs 152, 193 vs 145, 178 vs 127,
  150 vs 126). Verdict: opponent-strength artifact, no absolute gap.
- tetsuya (top-1 ref): 98/114/138k. V3 self-play on those seeds:
  137/150/110k. V3 above in 2/3; the third is within the self-vs-weak
  opponent-effect band (self-play depresses shared-market absolutes).

## 2. Tape forensics (decoded P3090/P3000/NIGHT/P2900 tapes)

- Common skeleton: HIRE4-5 + COW/SHEEP + seeds at step 0; wheat/strawberry/
  melon; 2x land; fertilizer collect-heavy (296) but apply-light (72) and
  sell-heavy (235-300); SELL wheat late (t=120) or trickle.
- NIGHT variant: 4x wheat market cycling (BUY 980/SELL 828) — measured
  WEAKER (-47k vs V3, weakest self-play 62k). Wheat cycling is anti-edge.
- No tape plants CARROT/TOMATO or runs GOOSE/EGG; V3 does all four
  (CARROT 31 plants, EGG 25-42 sells in forensics matches).

## 3. V3 vs DMITRII divergence (nearest peer, +6.8k/+12.2k)

Same lineage (Ozer-reactive): hires/plants/animals/land/movement/daily-money
within ~5%. V3's edge decomposes to:
1. Fertilizer application 2x (118-126 vs 61 FERTILIZE).
2. Fertilizer input buying (26-31 vs 20 BUY_PRODUCT FERTILIZER).
3. Wheat sale volume (74-92 vs 63 SELL WHEAT).
4. Microstructure wrappers (frontload + 2-turn advance + horizon-24
   reservation) — inherited V3-vs-parent edge.
5. A7 opening wash path (+12.2k vs +6.8k): reactive peers are sensitive
   to the step-0 inventory cascade (V27 mechanism).

## 4. First-divergence analysis (V3 vs P3090, seed 249571)

- t=0-120: both invest (money 681 vs 548 at t=120). P3090 HIRE4+livestock;
  V3 wash + reactive buys.
- t=120-360: V3 pulls away (2,273 vs 2,157 at t=240; 26,507 vs 10,384 at
  t=360). Driver: crop diversity + earlier monetization (V3 SELL WHEAT
  from t=1 trickle; tape first SELL WHEAT t=120) + fertilizer buying.
- t=360-720: gap compounds (88,643 vs 63,068 final). No single turning
  point: systematic ~40% economy-size advantage, not a snipe.

## 5. Engine facts established (1.32.7 source)

- Hands reset EVERY dawn (`farm["hands"] = []`): labor is rented daily.
  HIRE spam in tapes = daily re-hire, ~10/day affordable mid-game.
- HIRE cost = fib(hires_today); LAND = 1000/2000/4000 NE/SW/SE.
- Market: per-unit lockstep, both players quoted pre-commit inventory.
- Live config == local config (townCenterSellInterval 24 = "rebalance").
  No regime confound.
