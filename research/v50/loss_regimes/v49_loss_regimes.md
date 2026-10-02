# V49 Elite Loss Corpus & Causal Regime Analysis

## 1. Executive Summary & Benchmark Context
From the 1,536-leg elite benchmark across 128 seeds (250400–250527), 2 seats (0 and 1), and 6 elite opponent families (`V44`, `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`), V49 achieved:
- **1,525 Wins**
- **0 Ties**
- **11 Losses**
- **Win Rate: 99.28%**

Remarkably, **all 11 losses occurred exclusively against V44** (`candidates/v44_economic_portfolio/main.py`), and **all 11 losses occurred on Route 0** (`route=0` in the 2945 chassis). V49 scored 100% win rate (256/256) against all 5 other elite opponents.

Machine-readable loss records are cataloged in [`v49_loss_corpus.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/v50/loss_regimes/v49_loss_corpus.json).

---

## 2. Loss Census & Exact Physical Metrics

| Loss # | Seed | Seat | Route | V49 Cash | V44 Cash | Margin | V48 Cash | Raw 2945 Cash | Final Dead Stock |
|---|---|---|---|---|---|---|---|---|---|
| **01** | 250416 | 0 | 0 | $95,157 | $95,873 | **-$716** | $95,037 | $71,287 | 2 Wheat, 2 Carrot seeds; Dead Fert post-646 |
| **02** | 250416 | 1 | 0 | $95,157 | $95,873 | **-$716** | $95,037 | $71,287 | 2 Wheat, 2 Carrot seeds; Dead Fert post-646 |
| **03** | 250428 | 0 | 0 | $57,196 | $57,227 | **-$31** | $57,196 | $60,919 | Dead Fert post-646 ($200+ leaked) |
| **04** | 250428 | 1 | 0 | $57,133 | $57,293 | **-$160** | $57,133 | $60,368 | 1 Strawberry seed; Dead Fert post-646 |
| **05** | 250433 | 0 | 0 | $118,867 | $119,337 | **-$470** | $118,867 | $124,468 | Dead Fert post-646 ($200+ leaked) |
| **06** | 250433 | 1 | 0 | $118,867 | $119,337 | **-$470** | $118,867 | $124,468 | Dead Fert post-646 ($200+ leaked) |
| **07** | 250436 | 0 | 0 | $113,638 | $115,043 | **-$1,405** | $113,638 | $124,595 | Late order priority & dead fert |
| **08** | 250436 | 1 | 0 | $113,638 | $115,043 | **-$1,405** | $113,638 | $124,595 | Late order priority & dead fert |
| **09** | 250439 | 0 | 0 | $110,292 | $111,699 | **-$1,407** | $110,292 | $78,505 | Bakery/IceCream shop mismatch vs V44 |
| **10** | 250439 | 1 | 0 | $110,292 | $111,699 | **-$1,407** | $110,292 | $78,505 | Bakery/IceCream shop mismatch vs V44 |
| **11** | 250497 | 1 | 0 | $152,344 | $153,245 | **-$901** | $152,344 | $138,613 | Smoothies delivery & dead fert |

---

## 3. Causal Regime Classification

Rather than indexing by seed, the 11 losses partition into 3 distinct economic regimes based on physical state transitions and action consequences:

### Regime I: Sub-Marginal Capital Leakage (Losses #03, #04 — 18.2% of losses)
- **Deficit Range**: -$31 to -$160
- **Physical Signature**:
  - The game is decided by fewer than 2 units of unliquidated assets.
  - At step 649, Route 2 issues `['BUY_PRODUCT', 'FERTILIZER', 2]`, spending ~$160-$180.
  - At step 697, Route 2 issues another `['BUY_PRODUCT', 'FERTILIZER', 2]`, spending ~$160-$180.
  - Unit action tracing proves that across all routes, the **last unit `FERTILIZE` action occurs at step 631**.
  - These fertilizer purchases can never be applied. While terminal dumps at steps 712–717 attempt to liquidate inventory, the market spread and price degradation reduce recovered cash, yielding pure dead capital loss of $150–$300.
  - In Loss #03 (margin -$31) and Loss #04 (margin -$160), simply suppressing dead post-631 fertilizer purchases directly flips the outcome from loss to win.

### Regime II: Composite Seed & Fertilizer Over-Procurement (Losses #01, #02, #05, #06 — 36.4% of losses)
- **Deficit Range**: -$470 to -$716
- **Physical Signature**:
  - V49's E402 cap was coarse: it tracked `remaining` as a pooled sum of wheat and carrot plants rather than per-crop demand, and did not track other crops (e.g., Strawberry).
  - In Seed 250416 (Losses #01 & #02), V49 finishes step 718 with 2 unplanted Wheat seeds and 2 unplanted Carrot seeds, leaking ~$200 in unrecoverable seed cost.
  - Combined with ~$300 in dead fertilizer purchases at steps 649 & 697, total late-game dead capital leakage reaches ~$500–$550, accounting for nearly the entire deficit against V44.

### Regime III: Structural Delivery & Route Specialization Deficit (Losses #07, #08, #09, #10, #11 — 45.5% of losses)
- **Deficit Range**: -$901 to -$1,407
- **Physical Signature**:
  - In these worlds, V44's dynamic shop-unlock and economic portfolio allocation exploited higher-value product contracts (e.g., Smoothie Shop and Ice Cream Shop with high strawberry/milk demand).
  - Raw 2945 exhibited severe instability on these seeds (e.g. crashing to $78k in Seed 250439), whereas V48/V49 stabilized at $110k+.
  - However, Route 0's fixed delivery choreography suffered minor queue congestion in steps 600–648, causing V44 to out-earn V49 by ~$1k in shop fulfillment.
  - These deficits exceed late-game dead capital alone and stem from macro route selection rather than micro tactical leakage.
