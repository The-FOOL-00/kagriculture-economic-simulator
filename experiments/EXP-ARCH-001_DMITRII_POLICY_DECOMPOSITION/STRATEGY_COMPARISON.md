# STRATEGY COMPARISON — matrix and economic-vs-positional verdict

Machine-readable companion: `STRATEGY_SUMMARY.csv`.
Evidence: `analysis/01,03,04,06,07,08,09,10,11,12`.

## 1. Matrix (rows = 13 strategies)

Legend: D=drip small-lot sales; A=aggressive wool x100 + x1000 bursts;
S=sparse sales; J=JIT seed trickle; B=bulk seed buying.

- t0: shops=49 non-YARN pairs; invest=M12/W163/S33/C31; herd=8C6S3G(17);
  first$=FERT@30; revenue=FERT/MILK/WHEAT/STRAW/WOOL/MELON/EGG/CARROT;
  sales=D; workers=260/11; liquidity=day0 $2842; route=base; terminal=plan2.
- t1: shops=(Y,FM); invest=M12/W163/S33/C31; herd=6C10S(16);
  first$=FERT@30; revenue=+WOOL emphasis, EGG dead; sales=A; workers=277/12;
  liquidity=same; route=core cluster; terminal=plan2.
- t2: shops=(forced @648); invest=same as t0; herd=8C6S3G(17);
  first$=FERT@30; revenue=same as t0; sales=D; workers=260/11;
  liquidity=same; route=base+late variant; terminal=plan2 (defines it).
- t3: shops=(BAK,Y); invest=M12/W163/S33/C31; herd=6C11S(17);
  sales=A; workers=276/12; route=core cluster; rest as t1.
- t4: shops=(BRU,Y); invest=M12/W163/S33/C31; herd=6C10S(16);
  sales=A; workers=276/12; route=core (≈t1, day-9 block differs).
- t5: shops=(FM,Y),(PET,Y); invest=M12/W163/S33/C31; herd=6C10S(16);
  sales=A; workers=276/12; route=core (17 scattered diffs from t1).
- t6: shops=(ICE,Y),(Y,PIZ); invest=M12/W163/S33/C31; herd=6C11S(17);
  sales=A; workers=276/12; route=core.
- t7: shops=(PIZ,Y); invest=M12/W163/S33/C31; herd=6C11S(17);
  sales=A; workers=275/12; route=core (16 diffs from t8).
- t8: shops=(SMO,Y); invest=M12/W163/S33/C31; herd=6C11S(17);
  sales=A; workers=275/12; route=core.
- t9: shops=(Y,BAK),(Y,BRU),(Y,ICE); invest=M12/W165/S33/C28;
  herd=6C11S(17); first$=FERT@30; revenue=thin STRAW (33 turns);
  sales=S (daily wheat, sparse); workers=276/12; route=full permutation.
- t10: shops=(Y,PET); invest=M12/W161/S34/C31; herd=6C11S(17);
  sales=A; workers=277/12; route=adjacent (days 8–9 block differs).
- t11: shops=(Y,SMO); invest=M12/W167/S33/C31; herd=6C11S(17);
  sales=A; workers=276/12; route=core (day-8 block differs).
- t12: shops=(Y,Y); invest=M13/W169/S44/C24; herd=4C14S bought/17 housed;
  first$=FERT@30; revenue=+WOOL/STRAW; sales=A; seed-buy=B;
  workers=277/12; route=full permutation.

Invariant across ALL rows: PLANT day×crop table; LAND @150/@265;
workforce scale 3–5→7–12; day-0 $2,842; first-revenue turns ±3 steps;
no worker roles; shared 0..143 opening and 648..718 terminal.

## 2. Which differences are genuinely economic?

1. Herd composition: sheep 6 (t0/t2) → 10–11 (cluster) → 14 (t12);
   cows 8 → 6 → 4; geese 3 → 0. Direction: YARN plans carry more
   sheep, no geese. Magnitude: ±4 head, same 16–17 scale. VERDICT:
   real but small.
2. Wool liquidation: 42 small lots (t0) vs 76–84 lots with x100
   clearing (cluster). Same wool, very different sale cadence.
   VERDICT: real (SALES policy, not production).
3. Clearing bursts: x1000 all-product bursts at 402–407/430–431/
   669–671 in cluster + t12, absent in t0/t2/t9. VERDICT: real but
   mostly dead-quantity (they clear whatever exists, often ~0 for
   EGG/CARROT/TOMATO); live effect concentrated in WOOL/MILK/FERT.
4. Seed-purchase batching: JIT trickle (all) vs bulk (t12 only:
   264:WHEAT x11 + STRAW x23, daily WHEAT x8–11). Same planted
   totals. VERDICT: real (liquidity TIMING), small.
5. Sales sparsity (t9): daily wheat lots + 33 straw turns vs 51.
   VERDICT: real (SALES policy), direction unclear (thinner = worse
   price averaging? or lower price impact? unknowable statically).
6. Strawberry seeds 33 → 34 (t10) → 44 (t12). VERDICT: real, tiny
   (t12: +11 plants ≈ +1 tile-row equivalent... actually +11 seeds).

## 3. Which differences are only positional/path?

1. All 144..647 action-sequence divergence not explained by §2:
   cluster pairs differ by single-day blocks (t1/t4: day 9; t3/t6:
   day 10; t10/t1: days 8–9) or scattered steps (t1/t5: 17 steps)
   with identical daily op totals — pure re-timing/re-routing.
2. Outlier pairs (t9, t12 vs rest: 481–504/504 steps differ) with
   daily op-mix L1 only 2–18%: same schedule, different paths.
   Sampled days: day10 t0–t9 L1 = 2.4% (13/551 ops); day6 ≈ 11%.
3. HIRE/hands ±1 per day across tapes: same workforce scale, slightly
   different hire timing (arrival positions shift downstream routes).
4. Dead-order placement (TOMATO/EGG/CARROT x1000, `[]`, `x0`): differs
   across tapes, zero economic content.

## 4. Cluster structure (144..647 action diffs)

- Base pair: t0–t2 (110 diffs, late-mid days 13+).
- Core cluster: t1,t3,t4,t5,t6,t7,t8,t10,t11 (17–89 diffs within).
- Outlier routes: t9, t12 (412–504 diffs to everything, incl. 412 to
  each other) — yet §2 shows their economics differ only slightly.

## 5. Bottom line for Phase 4

The 13 tapes encode ONE agronomic economy with TWELVE route/sales
variants of the 144..647 continuation. Genuinely economic deltas:
sheep-heavy + goose-free herds in YARN plans, aggressive vs drip vs
sparse wool/sales cadence, and t12's bulk seed buying. Everything
else — including 100%-step-diff tape pairs — is route permutation.
Any "strategy selection" effect in live play comes overwhelmingly
from (a) which SALES cadence runs and (b) which route's timing best
fits the realized weed/price randomness, not from crop mix (identical)
or scale (identical).
