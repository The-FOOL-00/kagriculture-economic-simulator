# SEED 50018 FORENSIC TRACE: ANATOMY OF THE -$2,388 OUTLIER

**Experiment Identifier**: `EXP-DEV-001`  
**Target Seed**: `50018`  
**Paired Margin**: **-$2,388.00** (Match 0 Margin: -$1,194.00, Match 1 Margin: -$1,194.00)  
**Investigation Scripts**:
- [`scratch/diagnose_postmortem.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/diagnose_postmortem.py)
- [`scratch/verify_seed_50018_details.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/verify_seed_50018_details.py)
- [`scratch/trace_orders.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/trace_orders.py)  
**Auditor**: Antigravity Autonomous Pair Programmer  
**Date**: 2026-09-11  

---

## 1. Executive Summary & Forensic Discovery

The previous experiment report ([`EXP-DEV-001_RESULTS.md`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_RESULTS.md#L171-L177)) claimed:
> *"At Step 72 (Day 3): Shop 1 unlocked as `PET_CAFE`... The dynamic policy conditioned on `PET_CAFE` and scheduled secondary `CARROT` production, diverting resources away from standard wheat/feed buffering... At Step 144 (Day 6): Shop 2 unlocked as `YARN_STORE`... leading to severe worker starvation, desynchronization, and a -$2,388.00 paired loss."*

### Forensic Finding:
> **The narrative in the previous report is 100% FACTUALLY FALSE.**

1. On Seed 50018, **neither Shop 1 nor Shop 2 was Pet Cafe or Yarn Store**.
2. Shop 1 unlocked as **`PIZZA_SHOP`**; Shop 2 unlocked as **`PIZZA_SHOP`**.
3. Zero carrots were planted. Zero feed buffer was diverted.
4. Zero animal starvation occurred. Zero worker desynchronization occurred.
5. The true cause of the -$2,388.00 paired loss was **crop price risk on Day 11**: the candidate substituted 13 Strawberry plants with 13 Tomato plants because of the two early Pizza Shops. However, starting on Day 9, the town experienced an overwhelming **Strawberry boom** (5 Strawberry shops unlocked), rendering Strawberries far more profitable than Tomatoes.

---

## 2. Realized Shop Sequence on Seed 50018

The exact town shop unlocks on Seed 50018 across all 720 steps:

| Step | Day | Shop Unlocked | Accumulated Town Shops | Economic Significance |
| :---: | :---: | :--- | :--- | :--- |
| **72** | **3** | **`PIZZA_SHOP`** | `['PIZZA_SHOP']` | Tomato demand (+1/4 steps) |
| **144** | **6** | **`PIZZA_SHOP`** | `['PIZZA_SHOP', 'PIZZA_SHOP']` | Double Tomato demand (+2/4 steps) |
| **216** | **9** | **`FARMERS_MARKET`** | `[..., 'FARMERS_MARKET']` | **Strawberry Shop #1** |
| **288** | **12** | **`YARN_STORE`** | `[..., 'YARN_STORE']` | Wool demand |
| **360** | **15** | **`BRUNCH_SPOT`** | `[..., 'BRUNCH_SPOT']` | **Strawberry Shop #2** |
| **432** | **18** | **`ICE_CREAM_SHOP`** | `[..., 'ICE_CREAM_SHOP']` | **Strawberry Shop #3** |
| **504** | **21** | **`SMOOTHIE_SHOP`** | `[..., 'SMOOTHIE_SHOP']` | **Strawberry Shop #4** |
| **576** | **24** | **`FARMERS_MARKET`** | `[..., 'FARMERS_MARKET']` | **Strawberry Shop #5** |

Notice that from Day 9 through Day 24, **5 out of 6 revealed shops were STRAWBERRY SHOPS**!

---

## 3. Candidate Decision Trace & Mode Selection

1. **Step 72 (Day 3)**:
   - Observation: `unlocked_shops = ['PIZZA_SHOP']`.
   - Priority check in `_determine_crop_mode`: Priority 5 matches `PIZZA_SHOP` $\to$ `mode = 'TOMATO'`.
2. **Step 144 (Day 6)**:
   - Observation: `unlocked_shops = ['PIZZA_SHOP', 'PIZZA_SHOP']`.
   - Priority check: Still matches `PIZZA_SHOP` $\to$ `mode = 'TOMATO'`.
3. **Step 72 to Step 264**:
   - In `dev_001_dynamic_portfolio.py`, `TOMATO` mode logic is guarded by:
     ```python
     if 264 <= step <= 287:  # Day 11 secondary strawberry planting window
     ```
   - Therefore, between Step 72 and Step 264, the candidate executed **100% bit-exact actions identical to `ClosedLoopAgentV2`**!

---

## 4. The Exact Moment of Divergence: Step 265 (Day 11)

Across the entire 720-step episode, Candidate actions differed from `ClosedLoopAgentV2` on **exactly 23 steps**, all occurring during the Day 11 planting window (Steps 265–287):

### The First Divergence: Step 265
- **Observation State**:
  - Cash: \$2,100.00
  - Unlocked shops: `['PIZZA_SHOP', 'PIZZA_SHOP', 'FARMERS_MARKET']`
  - Hands: 5 workers active
- **Candidate Action**:
  - `farmer`: `['NORTH']`
  - `hands`: `[['WEST'], ['EAST'], ['SOUTH'], ['CARE'], ['COLLECT_FERTILIZER']]`
  - `market`: `[['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_LAND'], ['BUY_ANIMAL', 'GOOSE', 1], ['BUY_PRODUCT', 'FERTILIZER', 1], ['BUY_SEED', 'TOMATO', 2]]`
- **Control (`ClosedLoopAgentV2`) Action**:
  - `farmer`: `['NORTH']`
  - `hands`: `[['WEST'], ['EAST'], ['SOUTH'], ['CARE'], ['COLLECT_FERTILIZER']]`
  - `market`: `[['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['BUY_LAND'], ['BUY_ANIMAL', 'GOOSE', 1], ['BUY_PRODUCT', 'FERTILIZER', 1], ['BUY_SEED', 'STRAWBERRY', 2]]`

### Physical Difference:
- Both agents bought land, hired 5 workers, purchased 1 goose, collected fertilizer, and cared for animals identically.
- The **only** difference was that Candidate ordered `['BUY_SEED', 'TOMATO', 2]` while V2 ordered `['BUY_SEED', 'STRAWBERRY', 2]`.

### Total Seed Purchases across the Episode:
- **Candidate**:
  - Strawberry Seeds: **20**
  - Tomato Seeds: **13**
  - Total: 33 specialty crop seeds
- **`ClosedLoopAgentV2`**:
  - Strawberry Seeds: **33**
  - Tomato Seeds: **0**
  - Total: 33 specialty crop seeds

Candidate cleanly substituted 13 Strawberry seeds with 13 Tomato seeds.

---

## 5. Causal Decomposition of the -$2,388.00 Loss

### Why Did 13 Tomatoes Underperform 13 Strawberries by \$1,194 per Match?
1. **Town Shop Satiation**:
   - There were 2 Pizza Shops in town.
   - 2 Pizza Shops consume a maximum of $2 \times \frac{720 - 72}{4} = 324$ tomatoes over the whole game.
   - However, Candidate and Opponent already sell baseline produce into the market.
2. **The Late Strawberry Super-Regime**:
   - Between Step 216 and Step 576, **5 Strawberry Shops** opened in the town:
     - 2x Farmers Market (consumes Strawberry, Melon, Carrot)
     - 1x Brunch Spot (consumes Strawberry, Milk, Egg)
     - 1x Ice Cream Shop (consumes Strawberry, Milk)
     - 1x Smoothie Shop (consumes Strawberry, Melon)
   - Combined town demand for Strawberries was immense (up to 5 strawberries consumed every 4 steps).
   - This massive pull drove Strawberry market prices to the price ceiling.
3. **The Revenue Gap**:
   - `ClosedLoopAgentV2` possessed 33 mature Strawberry plants producing large harvest yields directly sold into this high-price Strawberry super-regime, earning **\$107,147.00**.
   - Candidate possessed only 20 Strawberry plants and 13 Tomato plants. The 13 Tomato plants were sold into a modest 2-Pizza-Shop market, earning **\$105,953.00**.
   - Loss in Match 0: $\$105,953.00 - \$107,147.00 = -\$1,194.00$.
   - Loss in Match 1: $\$105,953.00 - \$107,147.00 = -\$1,194.00$.
   - **Total Paired Loss**: $-\$1,194.00 + (-\$1,194.00) = -\$2,388.00$.

---

## 6. How the Original Causal Narrative Was Fabricated

The previous experiment report confused **Seed 50000** with **Seed 50018**:
- On **Seed 50000**: Shop 1 was `PET_CAFE` and Shop 2 was `YARN_STORE`. On Seed 50000, the candidate tied V2 with a delta of **$0.00** because it fell back to V2 via Yarn mode.
- On **Seed 50018**: Shop 1 was `PIZZA_SHOP` and Shop 2 was `PIZZA_SHOP`. The candidate diverged on Tomato and suffered the -$2,388.00 loss.

The author of the previous report combined the shop names from Seed 50000 with the outcome of Seed 50018, and hallucinated a story about animal starvation and feed exhaustion without checking the action logs.

### Forensic Conclusion:
- The -$2,388.00 loss is real.
- The stop criterion was legitimately triggered.
- But the cause was **unhedged crop price risk on Tomato substitution under late Strawberry shop arrivals**, NOT animal starvation or feed runway exhaustion.
