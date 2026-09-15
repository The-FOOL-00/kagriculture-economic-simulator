# SEED 50004 FORENSIC TRACE: ANATOMY OF THE +$15,264 OUTLIER

**Experiment Identifier**: `EXP-DEV-001`  
**Target Seed**: `50004`  
**Paired Margin**: **+$15,264.00** (Match 0 Margin: +$7,632.00, Match 1 Margin: +$7,632.00)  
**Investigation Scripts**:
- [`scratch/diagnose_postmortem.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/diagnose_postmortem.py)
- [`scratch/trace_orders.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/trace_orders.py)  
**Auditor**: Antigravity Autonomous Pair Programmer  
**Date**: 2026-09-11  

---

## 1. Executive Summary

Seed 50004 produced the single largest margin in EXP-DEV-001: **+$15,264.00**. This single seed accounts for **115.1% of the total cumulative profit** of the candidate across all 50 seeds (cumulative margin with Seed 50004 = +$13,259.00; without Seed 50004 = -$2,005.00).

Understanding the mechanics of Seed 50004 is essential to determining whether dynamic portfolio adaptation has general merit or represents an extreme, highly volatile lottery ticket.

---

## 2. Realized Shop Sequence on Seed 50004

The exact town shop unlocks on Seed 50004 across all 720 steps:

| Step | Day | Shop Unlocked | Accumulated Town Shops | Economic Significance |
| :---: | :---: | :--- | :--- | :--- |
| **72** | **3** | **`PIZZA_SHOP`** | `['PIZZA_SHOP']` | Tomato demand (+1/4 steps) |
| **144** | **6** | **`PIZZA_SHOP`** | `['PIZZA_SHOP', 'PIZZA_SHOP']` | Double Tomato demand (+2/4 steps) |
| **216** | **9** | **`PIZZA_SHOP`** | `['PIZZA_SHOP', 'PIZZA_SHOP', 'PIZZA_SHOP']` | **Triple Tomato demand (+3/4 steps)** |
| **288** | **12** | **`BAKERY`** | `[..., 'BAKERY']` | Wheat demand |
| **360** | **15** | **`BRUNCH_SPOT`** | `[..., 'BRUNCH_SPOT']` | Strawberry Shop #1 |
| **432** | **18** | **`YARN_STORE`** | `[..., 'YARN_STORE']` | Wool demand |
| **504** | **21** | **`PIZZA_SHOP`** | `[..., 'PIZZA_SHOP']` | **Quadruple Pizza Shop (+4/4 steps)** |
| **576** | **24** | **`BAKERY`** | `[..., 'BAKERY']` | Wheat demand |

### Crucial Feature:
Seed 50004 realized **FOUR PIZZA SHOPS** (at Steps 72, 144, 216, and 504), and **zero Strawberry shops until Day 15 (Step 360)**!

---

## 3. Candidate Decision Trace & Divergence

Just as in Seed 50018:
1. **Mode Selection**: Candidate observed `PIZZA_SHOP` at Step 72 and Step 144, selecting `mode = 'TOMATO'`.
2. **Divergence Window**: Between Steps 265 and 287 (Day 11), Candidate substituted 13 Strawberry seeds with 13 Tomato seeds.
3. **Execution**: Exactly 23 divergent steps out of 720.

---

## 4. Why Did Candidate Gain +$15,264.00 Over V2?

1. **The Tomato Monopolistic Satiation**:
   - In town, 3 Pizza Shops opened early (by Day 9). They consumed 3 Tomatoes every 4 steps.
   - Candidate’s 13 Tomato plants produced hundreds of high-value harvest units that were continuously pulled by 3–4 Pizza Shops at peak market prices.
2. **The Strawberry Starvation on V2**:
   - `ClosedLoopAgentV2` planted 33 Strawberries.
   - But on Seed 50004, there was **only ONE Strawberry shop in town** (`BRUNCH_SPOT` at Step 360), which consumes only 1 Strawberry every 4 steps!
   - V2 suffered catastrophic market gluts on Strawberries: excess Strawberry supply collapsed the strawberry price toward minimum baseline or left inventory stranded in the order book.
3. **The Score Delta**:
   - In Match 0: Candidate earned **\$100,541.00**; V2 earned **\$92,909.00** (Delta = **+$7,632.00**).
   - In Match 1: Candidate earned **\$100,541.00**; V2 earned **\$92,909.00** (Delta = **+$7,632.00**).
   - **Total Paired Margin**: $\$7,632.00 + \$7,632.00 = +\$15,264.00$.

---

## 5. Mechanistic Comparison: Seed 50004 vs. Seed 50018

Seeds 50004 and 50018 are identical mirror images of the same underlying bet:

| Feature | Seed 50004 (+15k Win) | Seed 50018 (-2.3k Loss) |
| :--- | :--- | :--- |
| **Day 3 Shop** | `PIZZA_SHOP` | `PIZZA_SHOP` |
| **Day 6 Shop** | `PIZZA_SHOP` | `PIZZA_SHOP` |
| **Candidate Mode** | `TOMATO` | `TOMATO` |
| **Action Taken** | Substituted 13 Strawberries with 13 Tomatoes | Substituted 13 Strawberries with 13 Tomatoes |
| **Later Shops (Days 9–24)** | 2x Pizza, 2x Bakery, 1x Brunch, 1x Yarn | 5x Strawberry shops, 1x Yarn |
| **Town Demand Realized** | Enormous Tomato demand; 1 Strawberry shop | Enormous Strawberry demand; 0 new Pizza shops |
| **Outcome** | Tomatoes massively outperform Strawberries | Strawberries massively outperform Tomatoes |
| **Result** | **+$15,264.00 margin** | **-$2,388.00 margin** |

---

## 6. Analytical Conclusion

1. **The gain is mechanistically reproducible**: If a world realizes 4 Pizza Shops and only 1 Strawberry shop, planting Tomatoes on Day 11 is dramatically superior to planting pure Strawberries.
2. **However, it is a speculative directional bet**: At Day 11 (Step 265), only 3 shops have been revealed. The agent cannot know whether the remaining 5 shops will be Pizza Shops or Strawberry Shops.
3. **Extreme Bimodal Risk**:
   - If future shops confirm the early signal $\to$ massive win (+15k).
   - If future shops pivot to Strawberry $\to$ catastrophic tail loss (-2.3k).
4. **Generalization Warning**: Seed 50004 cannot be used to justify dynamic portfolio adaptation. It is an outlier from a high-variance, unhedged directional bet.
