# V32 P3 DATASET AUDIT (P2 BC legs → P3 factorized labels)

Source: `results/v32_p2_bc_legs.jsonl` (120 legs, 172,560 steps, TEST-11-clean).
Audit runner: `scripts/v32_p3_audit.py` → `results/v32_p3_audit.json`.
No regeneration: P3 reuses the P2 dataset deterministically (same bytes, same
train/val split). No matches executed.

## 1. Manifest

| Item | Value |
| :--- | :--- |
| legs | 120 (seeds 249635–249649, P2-TRAIN) |
| steps (seat-rows) | 172,560 (719 × 240) |
| train steps | 138,048 (seeds 249635–249646, 249650+ excluded) |
| val steps | 34,512 (seeds 249647–249649, identical to P2 BC-val) |
| teachers | E0_V3 / E2_A7 / E6_W72 / E7_W2015 × 43,140 steps each |
| legs sha16 | `55c907db955b1210` |
| vocab sha16 | `f0df959940dfd216` (matches P2 BC report) |
| feature schema | `v32p2feat-v1`, 157 dims, normalizer `d2a41ab7…` (unchanged) |

## 2. P3 label conversion (deterministic, lossless)

Every recorded step converts via `v32/p3/codec.py::encode_action` with zero
normalizations: **N1=0, N2=0, N3=0, U:TRUNC=0, M:TRUNC=0** over all 172,560
steps. The round-trip is LITERAL identity on the full dataset (G1 test
re-verifies independently). Missing actions: 0 (no None farmer/hands/market).

## 3. Slot frequencies

### Unit slots (Σ(1+h) = 1,708,694 target triples)

| U_OP | count | | U_OP | count |
| :--- | ---: | :--- | :--- | ---: |
| WATER | 271,180 | | HARVEST | 117,856 |
| NORTH | 224,624 | | CARE | 101,720 |
| WEST | 217,258 | | COLLECT_FERTILIZER | 94,660 |
| EAST | 153,774 | | FEED | 83,066 |
| PASS | 134,895 | | PLANT | 57,629 |
| SOUTH | 127,110 | | PLACE | 27,068 |
| PICKUP | 47,692 | | FERTILIZE | 25,932 |
| DROP | 10,620 | | DIG | 8,786 |
| BUILD_PASTURE | 3,768 | | BUILD_COOP | 1,056 |

All 18 `U_OP` classes occur (min BUILD_COOP 1,056). PASS rate overall ≈ 7.7%.

Farmer slot: movement + WATER/HARVEST/CARE dominate; PLANT 4,300; PASS 15,900
(9.2%).

### Unit arg/qty (loss-masked heads; counts conditional on use)

- `U_ARG` (132,389 PLANT/PICKUP/PLACE slots): WHEAT 77,456, FERTILIZER 12,932,
  STRAWBERRY 11,739, CARROT 8,136, MELON 5,250, MILK 4,000, SHEEP 3,892,
  COW 3,548, WOOL 2,880, TOMATO 1,140, GOOSE 1,176, EGG 240. All 12 occur.
- `U_QTY` (74,760 PICKUP/PLACE slots): IMPLICIT 24,236 (32%), then 2/3/5/6/4
  (5k–13k each), 1000 × 1,892, all 17 classes occur.

### Market slots (1,725,600 = 172,560 × 10)

| M_OP | count | share |
| :--- | ---: | ---: |
| NOOP | 1,479,866 | 85.8% |
| SELL | 112,294 | 6.5% |
| HIRE | 67,788 | 3.9% |
| BUY_SEED | 44,236 | 2.6% |
| BUY_PRODUCT | 17,876 | 1.0% |
| BUY_ANIMAL | 2,956 | 0.2% |
| BUY_LAND | 584 | 0.03% |

- `M_ITEM` (177,362 qty-op slots): WHEAT 60,646, FERTILIZER 34,264,
  STRAWBERRY 20,310, MILK 17,380, WOOL 15,984, CARROT 11,770, EGG 7,180,
  MELON 4,884, TOMATO 1,988, SHEEP 1,312, COW 1,268, GOOSE 376. All 12 occur.
- `M_QTY`: 1 × 57,624, 2 × 26,176, 1000 × 20,300 (dump orders), 3 × 17,304,
  then 6/4/8/9/5/7/12/10 (2k–11k); long tail incl. 983–999 cluster; all 77
  classes occur.
- Positional semantics (NOOP rate by slot): M0 41% → M1 73% → M2 86% →
  M3–M9 91–97% (late slots mostly HIRE bursts). Slot identity carries signal.

## 4. No-op frequency per slot

- Unit: PASS 7.7% overall (farmer 9.2%). No implicit unit no-ops in data
  (every literal is a well-formed simulator op).
- Market: NOOP 85.8% overall; M0 41% (most active), M9 97.4%.
- Qty-0 orders (explicit no-op class): 370 occurrences in `M_QTY`.

## 5. Cardinality / distributions / maxima

- Hand count: 0 × 7,440; 3–14 occupied (11 × 45,130 most common); **max 14**
  (4,008 steps); counts 1–2 never occur (burst hiring); no sim cap (assert-cap
  16 retained).
- Market count: 0 × 70,772 (41%); 1 × 54,790; 2 × 23,204; 3–8 × 1.3k–7.5k;
  9 × 3,128; **10 × 4,532** — M=8 would truncate 7,660 steps (4.4%). M=10 confirmed.
- Max dims: market 10, hands 14, unit slots/step ≤ 15, market qty values 77,
  unit qty values 16 + IMPLICIT.

## 6. Invalid / edge examples

- Malformed literals: 0. Unknown opcodes (incl. WEED): 0. OOV items/qtys: 0.
  Trailing-arg literals: 0. Hands actions beyond live count: 0. Market >10: 0.
- Provably-noop PLANT (seeds 0, would be masked under P2 rule): 84 / 57,629
  (0.15%) — learned as no-op in P3 a1 (no masking).

## 7. Step-0 wash census (G3 population)

240/240 seat-legs wash at step 0 (100%), 60/60 per teacher. All share the shape
`M0=[BUY_PRODUCT,WHEAT,n>0], M1=[SELL,WHEAT,m>0]`, differing ONLY in qty:

| Teacher | M0 | M1 |
| :--- | :--- | :--- |
| E0_V3 | BUY_PRODUCT WHEAT 50 | SELL WHEAT 50 |
| E2_A7 | BUY_PRODUCT WHEAT 30 | SELL WHEAT 30 |
| E7_W2015 | BUY_PRODUCT WHEAT 20 | SELL WHEAT 15 |
| E6_W72 | BUY_PRODUCT WHEAT 7 | SELL WHEAT 2 |

Step-0 observable inputs are near-identical across legs (constant money/hands/
tiles/prices), so the 4 qty literals are mutually unidentifiable from state
under mixture supervision — G3 therefore reports (a) valid-wash shape rate
and (b) exact-literal match per teacher (see `V32_P3_STEP0_WASH_REPORT.md`).
A consistent single-pattern choice is the achievable mixture optimum.

## 8. Partition / seeds

Train: 249635–249646 + 249650+ excluded… precisely: all P2-TRAIN except
249647–249649 (138,048 steps). Val: 249647–249649 (34,512 steps). No P3
screen/CONFIRM seed appears in training. Conversion is deterministic
(pure functions; re-encode fixpoint verified in G1).
