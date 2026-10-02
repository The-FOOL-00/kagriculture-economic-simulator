# V31R2 LOSS FORENSICS — every A7 public loss classified

Date: 2026-09-22. First 32 A7 public losses retrieved as full replays
and deeply analyzed (opening wash, money curves, yields, labor counts,
animal/seed mixes, sell volumes); 11 further losses (games 33–43,
through ~12:00 UTC) wash-scanned — same families, no new archetype.
One validation game (seed 0, canned) excluded.

## Method

For each loss: step-1 wash shape, diff trajectory (d17/d252/final),
harvested yields by product (tile-transition audit), unit-op counts
(WATER/FEED/FERTILIZE/HARVEST), animal/seed buys, SELL order volumes.
Primary cause = earliest causally meaningful divergence confirmed by
cross-game pattern or local experiment; single-case mechanisms are
marked HYPOTHESIS.

## Class T (trickle-order losses, 9 games, mean −$5.8k)

Opponents issuing <4k lifetime SELL-order units (vs A7's ~85–130k).
Local fill instrumentation shows BOTH sides fill only ~1.6k units
(A7's orders are 99% phantom), so "flood" is a misnomer — but the
correlation is perfect (9/9 losses) and subdivides causally:

| Game | Opp (LB) | Delta | d17/d252 | Sub-cause |
| ---- | -------- | ----: | -------- | --------- |
| ep111876058 | shawenher (2320) | −$10,395 | −31/+844 | PRODUCTION-TIMING: +99 yield units (wool+33, wheat+50) on identical animals/seeds; +35 FERTILIZE, +$2k hire savings |
| ep111886277 | Fedor (1834) | −$14,189 | −1/−1009 | ARCHETYPE (see Class S): strawberry/goose strategy, wash [BUY 5] only |
| ep111874934 | GOAT ZywOo (2558) | −$5,691 | +9/+881 | second-half collapse, counts ~equal; micro-unresolved |
| ep111875310 | Zhongyi Dai (1783) | −$4,186 | −21/−287 | divergent; micro-unresolved |
| ep111912405 | atl132 (2268) | −$3,673 | −54/+852 | LIVESTOCK-MIX: +3 SHEEP/−3 GOOSE (same as wen) |
| ep111919236 | xsong2020 (2077) | −$3,060 | −21/−210 | divergent; micro-unresolved |
| ep111864683 | Suyash Verma (2658) | −$2,480 | +9/−98 | divergent; micro-unresolved |
| ep111950010 | jiazepin (2475) | −$2,446 | −21/−196 | divergent; micro-unresolved |
| ep111921474 | Ezzzzzekki (2677) | −$5,733 | −1/+242 | LIVESTOCK-MIX: +3 SHEEP/−3 GOOSE |

## Class F (flood-vs-flood collapses, ~17 games)

Opponent sells ~85–118k order units like A7; A7 ahead/tied at step 252
then loses the second half. Diagnosed subsets:

- LIVESTOCK-MIX (wen-type, 3 games): wen chong yu −$8,984 (+3
  SHEEP/−3 GOOSE = +63 wool/−79 eggs ≈ +$8.6k, identical per-animal
  yields/timing); Guilherme Volpe −$6,039 (+3 COW/−3 GOOSE); Dzmitry
  Pihulski −$538 (+3 COW/−3 GOOSE). W72-vs-A7 on wen's own live seed:
  +$5 (NOT a wash cascade — intrinsic policy).
- SEED-CASCADE (carbonapi-type, 1+ games): carbonapi −$6,319
  (+2 TOMATO/+4 CARROT/+1 GOOSE seeds from 13/2-wash cash path;
  +$2,823 at step 252 → tomato window collapse).
- SELL-EXECUTION-MICRO (Marlubie-type): Marlubie −$4,307 with
  IDENTICAL yields (1410/1420), sells, sizes, labor, animals —
  mechanism below count resolution (deposit/sell phase or pool-timing).
  xder −$155 (+$729 at 252 → collapse) similar at small scale.
- Remaining flood losses (Raghav −$2,135, HIDEYO −$2,055, yuxian
  −$2,048, Fanch −$1,678, levshaazz −$1,401, PursueML −$1,367,
  孤寡少年 −$914, David Goldrajch −$671, Dương Đức Anh −$436,
  TY0912 −$303): second-half divergent, no single-count smoking gun;
  each consistent with small livestock/seed/timing edges.

## Class M (flat wash-ledger mirrors, ~6 games)

Decided by step ~30–252, parallel afterwards. 10/10 family: MAOSEN
−$45, maoxin123 −$126/−$139, 夏絵 −$140, HIDEYO-partial; 5/5:
kevin zhou −$34 (entire delta set by step 17); Masataka −$63.
Local E3b matrix replicates this scale exactly (W10-vs-A7 +$140 med).

## Loss-classification table (§8 categories)

| Class | N | Primary §8 code | Secondary |
| ----- | -: | --------------- | --------- |
| T-production-timing | 1–2 | CROP (yield) | FERTILIZER |
| T-livestock-mix | 3 | LIVESTOCK | — |
| T-unresolved-micro | 4–5 | UNKNOWN (timing-level) | MARKET |
| F-livestock-mix | 3 | LIVESTOCK | — |
| F-seed-cascade | 1+ | CROP (seed mix) | CAPITAL (open cash) |
| F-execution-micro | 2+ | MARKET (fill phase) | UNKNOWN |
| F-mixed-small | 10 | UNKNOWN (diverse) | — |
| M-mirrors | 6 | CAPITAL (wash ledger) | — |
| S-archetype (Fedor) | 1 | CROP (strategy) | MARKET |

## A7 case classification (§9)

CASE B (competitive but under-sampled) trending toward CASE D
(vulnerable to identifiable families: sheep-heavy livestock,
strawberry-archetype, high-fert micro). NOT Case C (no single common
reproducible failure; 61% WR vs pool) and NOT Case E (losses
concentrate in V3-clone micro/strategy adaptations, not diverse
independent collapses). NOT Case A either (82 games suffice to see
the pattern; sample is adequate, pool is just softer than V22R1's).
