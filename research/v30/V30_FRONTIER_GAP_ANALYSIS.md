# V30 FRONTIER GAP ANALYSIS — THE INVERSION

## Question (§2)

What economically important capabilities do the strongest current
Kaggriculture agents possess that neither V3 nor A7 possess?

## Answer: NONE OBSERVED. The gap runs the other way.

### Evidence 1 — head-to-head: 176-0 (+80-0 wave 2 = 256-0 total legs... see ledger)

V3/A7 vs 11 runnable meta families, 8 seeds mirrored (16 legs each):

| Opp | V3 W/L | V3 mean | A7 W/L | A7 mean |
|---|---|---|---|---|
| P3090 | 16-0 | +27,717 | 16-0 | +27,717 |
| P3000 | 16-0 | +25,786 | 16-0 | +25,786 |
| P2900 | 16-0 | +25,786 | — | — |
| NIGHT | 16-0 | +47,138 | 16-0 | +47,138 |
| OKAMI | 16-0 | +91,125 | 16-0 | +91,125 |
| DMITRII | 16-0 | +6,833 | 16-0 | +12,175 |
| V66 | 16-0 | +17,650 | — | — |
| L2530 | 16-0 | +18,765 | 16-0 | +18,765 |
| ANDREY11 | 16-0 | +48,706 | — | — |
| MELON2736 | 16-0 | +55,945 | — | — |
| SOIL2843 | 16-0 | +25,819 | — | — |

Total: V3 176-0; A7 80-0. Zero losses, zero ties, both seats.

### Evidence 2 — absolute self-play levels (same 8 seeds)

| Agent | Mean | Median | Min | Max |
|---|---|---|---|---|
| V3 | 101,614 | 104,894 | 53,819 | 126,592 |
| A7 | 101,614 | 104,894 | 53,819 | 126,592 |
| DMITRII | 95,507 | 93,414 | 44,623 | 128,875 |
| MELON2736 | 87,912 | 83,088 | 59,312 | 129,600 |
| SOIL2843 | 87,913 | 95,325 | 51,821 | 107,729 |
| P3000/P2900 | 80,313 | 85,384 | 43,338 | 114,861 |
| V66 | 77,091 | 79,051 | 39,156 | 96,100 |
| L2530 | 76,266 | 82,024 | 38,343 | 100,675 |
| ANDREY11 | 75,835 | 77,360 | 30,803 | 127,263 |
| P3090 | 73,170 | 75,850 | 46,234 | 96,363 |
| NIGHT | 62,447 | 68,144 | 28,174 | 84,110 |
| OKAMI | 54,686 | 57,118 | 32,594 | 79,123 |

V3/A7 self-play EXCEEDS every meta self-play. CREATE gap = 0 or negative
for all observables.

### Evidence 3 — live-seed absolute control (6 live seeds)

V3-vs-weak matches/exceeds every live-best score on identical seeds.
Highest live score (180k) is an empty-market artifact. tetsuya top-1
matched/exceeded on 2/3 seeds, third within opponent-effect band.

### Required frontier ledger (V3 vs A7 vs strong meta, seed 249571)

| Capability | V3 | A7 | P3090 (strong meta tape) | DMITRII (near peer) |
|---|---|---|---|---|
| Opening wash | 50-wash | 30-wash | none (HIRE4+livestock) | reactive |
| Opening hires (day 0) | 5 | 5 | 4-5 | ~5 |
| Day-1 end money | ~20 | ~20 | ~10 | ~73 |
| Day-5 money | ~800 | ~800 | ~515 | ~330 |
| First expansion | day ~7 (t=168) | same | t=240 (quads 2) | same as V3 |
| Productive tiles (t=360) | 57 plant + 14 pasture | same | 62 + 12 | same as V3 |
| Workers | ~10/day | ~10/day | ~10/day | ~10/day |
| Livestock | COW+GOOSE+SHEEP | same | COW+SHEEP | COW+GOOSE+SHEEP |
| Fertilizer | BUY 26-31, APPLY 118-126 | same | BUY 0, APPLY 72, SELL 235+ | BUY 20, APPLY 61 |
| Crop mix | W+CARROT+STRAW+MELON | same | W+STRAW+MELON | same as V3 |
| Revenue by day 10 | ~17.6k | same | ~4.3k | ~same as V3 |
| Revenue by day 20 | ~54.5k | same | ~36.8k | ~same as V3 |
| Terminal cash | 88.6k (this seed) | same | 63.1k | ~same as V3 |

### Why V3 wins (causal chain, strongest-first)

1. **Crop/production diversity**: carrot + egg/goose income streams tapes lack.
2. **Fertilizer application intensity**: buys AND applies (2x DMITRII, 1.6x
   tapes); tapes sell fertilizer instead of applying it.
3. **Shop-reactive routing** (parent): adapts to per-seed shop draws; tapes
   cannot. Live ladder = many seeds; adaptivity compounds.
4. **Earlier monetization**: SELL WHEAT from t=1 vs tape t=120.
5. **Microstructure wrappers**: frontload + 2-turn advance + horizon 24.
6. **A7 opening path**: +1.3k vs V3-regime, +12k vs DMITRII (reactive peers
   sensitive to step-0 cascade).

### What the meta has that V3 lacks

- V66's **adaptive route SELECTION** (idea, not instance: loses by 17k).
- Tapes' **deterministic simplicity** (robustness, not economy).
- Nothing with positive absolute or head-to-head value was found.

### Implication for A8 (§12-14)

No observed capability gap exists to motivate A8. Per §3/§12, building A8
now would be unmotivated heuristic search. See V30_A8_SPEC.md (no-build
decision + trigger criteria) and V30_CAPABILITY_PRIORITY.md.
