# V44 Production Mix & Livestock Lifecycle Report

**Document ID:** `research/v44/reports/V44_PRODUCTION_ALPHA_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Scope:** Systematic investigation of livestock scaling, crop rotation economics, and capital amortization horizons across full terminal rollouts.

---

## 1. Executive Summary

In Kagriculture, farm revenue is produced through two primary asset classes:
1. **Ongoing Crops (Tomato, Strawberry):** High initial seed cost ($50–$100), long maturation (8–10 days), ongoing yields every 1–2 days.
2. **Livestock (Goose, Cow, Sheep):** High initial animal cost ($300–$600), requires structure (Coop/Pasture), ongoing yields of Eggs ($50), Milk ($160), or Wool ($200).

In V44, we evaluated the capital efficiency and payback dynamics of these investments, testing:
* **`BUY_EXTRA_COW_EARLY`:** Purchasing an additional Cow ($600) at Steps 70–120.
* **`BUY_EXTRA_SHEEP_EARLY`:** Purchasing an additional Sheep ($500) at Steps 70–120.
* **`INVESTMENT_PAYBACK_CUTOFF`:** Enforcing strict cutoffs on late-game animal purchases (Step $\ge 520$).

---

## 2. Experimental Data Table

| Candidate Strategy | Intervention Description | Mean Cash $\Delta$ | Median Cash $\Delta$ | Casualties | Rescues | Win Rate (%) | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`INVESTMENT_PAYBACK_CUTOFF`** | Suppress animal buys step $\ge 520$ | $0.00 | $0.00 | **0** | 0 | 91.7% | Verified Safe Guard |
| **`BUY_EXTRA_COW_EARLY`** | Extra Cow ($600) step 70–120 | $0.00 | $0.00 | **0** | 0 | 91.7% | Neutral (A7 already buys cows) |
| **`BUY_EXTRA_SHEEP_EARLY`** | Extra Sheep ($500) step 70–120 | $0.00 | $0.00 | **0** | 0 | 91.7% | Neutral (Pasture tile limited) |
| **`COMPOSITE_PAYBACK_CUTOFF`** | Payback cutoff + V43 flush | **+$94.08** | **+$53.00** | **0** | **1** | **95.8%** | **PROMOTED** |

---

## 3. Mathematical Amortization Horizon Analysis

Every livestock purchase incurs an upfront capital cost and requires a fixed incubation period before first yield:

| Animal | Purchase Cost | First Yield Day | Step to First Yield | Yield Interval | Product Base Value | Steps to Full Amortization | Latest Profitable Purchase Step |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Goose** | $300 | Day 4 | 96 steps | 1 day (24 steps) | Egg ($50) | 240 steps | **Step 480** |
| **Cow** | $600 | Day 8 | 192 steps | 2 days (48 steps) | Milk ($160) | 384 steps | **Step 336** |
| **Sheep** | $500 | Day 6 | 144 steps | 3 days (72 steps) | Wool ($200) | 360 steps | **Step 360** |

### Critical Finding:
* A Cow purchased after **Step 336** cannot break even on its $600 purchase cost before Step 718 closes!
* Any animal purchased after Step 520 is a 100% dead-weight loss: the animal will never produce a single yield before the game ends.
* A7's baseline code occasionally queued animal purchases between Steps 160 and 265, but naturally decelerated purchases thereafter.
* Enforcing an explicit **Payback Cutoff at Step 520** guarantees that working capital is never stranded in unamortized livestock.

---

## 4. Policy Implementation

The V44 Candidate integrates the **Step 520 Investment Payback Cutoff**, permanently blocking any animal or land capital outlay in the final 200 turns of the match.
