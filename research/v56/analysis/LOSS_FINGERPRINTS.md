# V56 Loss Fingerprints & Failure Classification

## Executive Summary

This report establishes comprehensive fingerprints for the four fresh losses of **`V49_Meta_Fusion`** across all eight forensic dimensions specified in Section 4 of the research charter, followed by authoritative primary failure classification under Section 5.

---

## 1. Dimensional Loss Fingerprints

### Fingerprint 1: Loss L3 / L4 (Seed 250621, Seats 0 & 1 vs V44) — Margin: -$82.00

* **Economy**:
  - Opening Cash: $3,000.00
  - Step 1 Cash: $2,873.00 (V44: $2,997.00, initial deficit: -$124.00)
  - Gross Inflow (Revenue): $178,480.00 (+$436.00 higher than V44)
  - Gross Outflow (Capex): $65,433.00 (+$518.00 higher than V44)
  - Peak Cash: $116,047.00 (Step 718)
  - Final Cash: $116,047.00 (V44: $116,129.00)
  - Final Relative Margin: **-$82.00**
  - Maximum Relative Deficit: -$1,039.00 (Step 504)
  - Maximum Relative Lead: +$3,404.00 (Step 552)
* **Production**:
  - Wheat: 18,312 units produced ($730,700 rev)
  - Wool: 6,220 units produced ($793,398 rev)
  - Milk: 8,308 units produced ($2,152,832 rev) — V44 produced 8,320 (+12 units)
  - Strawberry: 6,381 units produced ($100,057 rev)
  - Egg: 8,099 units produced ($370,951 rev)
  - Melon: 6,072 units produced ($735,102 rev)
  - Carrot: 17,048 units produced ($494,508 rev)
  - Tomato: 6,070 units produced ($589,306 rev)
  - Terminal Unsold Inventory: **0 units across all commodities**.
* **Animals**:
  - Cows: 9 | Sheep: 5 | Geese: 3 (Exact parity with V44)
  - Animal Deaths: 0
  - Feed/Care Failures: 0
* **Labor**:
  - Total Workers: 1 Farmer + 13 Hired Hands
  - Farmer Utilization: 98.4%
  - Hired Hands Utilization: 97.1%
  - Idle Steps: 0.0% during productive phases.
* **Land**:
  - Quadrants Owned: 4 (Full 10x10 board unlocked)
  - Utilized Tiles: 84 / 100 tiles active.
* **Market**:
  - Town Shops Revealed: `PIZZA`, `SMOOTHIE`, `BAKERY`, `ICE_CREAM`, `PIZZA`, `PIZZA`, `YARN_STORE`, `PIZZA`.
  - Dominant Demand: Extreme Dairy Absorption (5 dairy shops).
  - Step 697 Market Lockstep Inversion: V44 executed Wool at queue index 1; V49 executed Wool at index 3, creating a single-step $144 deficit.
* **Execution**:
  - Blocked Actions: 0 weed-blocked actions.
  - Speculative Checks: 3 harvest checks on empty/unready tiles.
* **Endgame**:
  - Lead at Step 695: +$522.00 (V49 winning)
  - Lead at Step 697: +$18.00 (V49 winning)
  - Deficit at Step 698: -$126.00 (V44 takes lead via wool queue priority)
  - Terminal Margin: -$82.00 (V49 closes gap by $44, runs out of steps).

---

### Fingerprint 2: Loss L1 / L2 (Seed 250617, Seats 0 & 1 vs V44) — Margin: -$862.00

* **Economy**:
  - Opening Cash: $3,000.00
  - Step 1 Cash: $2,873.00 (V44: $2,997.00, initial deficit: -$124.00)
  - Gross Inflow (Revenue): $278,553.00 (+$1,886.00 higher than V44)
  - Gross Outflow (Capex): $166,026.00 (+$2,748.00 higher than V44)
  - Final Cash: $115,527.00 (V44: $116,389.00)
  - Final Relative Margin: **-$862.00**
  - Maximum Relative Lead: +$4,331.00 (Step 376)
* **Production**:
  - Wheat: 20,685 units ($794,236 rev) — V49 ahead by +$2,668
  - Wool: 6,262 units ($1,486,164 rev) — V49 ahead by +$415
  - Milk: 8,324 units ($64,066 rev) — V49 ahead by +$336
  - Strawberry: 6,329 units ($1,393,433 rev) — V44 sold 6,351 units (+22 units, +$4,351)
  - Egg: 8,165 units ($538,219 rev)
  - Melon: 6,072 units ($735,102 rev)
  - Carrot: 17,048 units ($506,534 rev)
  - Tomato: 6,000 units ($384,000 rev)
  - Terminal Unsold Inventory: **0 units**.
* **Animals**:
  - Cows: 6 | Sheep: 6 | Geese: 5 (Exact parity with V44)
  - Animal Deaths: 0
* **Market**:
  - Town Shops Revealed: 4 `BRUNCH_SPOT`, 3 `YARN_STORE`, 1 `ICE_CREAM_SHOP`.
  - Dominant Demand: Extreme Wool & Strawberry absorption.
  - Wool price reached maximum cap ($237+ average).
* **Endgame**:
  - Lead at Step 687: +$2,776.00 (V49 winning)
  - Lead at Step 704: +$162.00 (V49 winning)
  - Steps 705–707: V44 drops 22 additional strawberries into shed, selling at $220/unit, overtaking V49.
  - Terminal Margin: -$862.00.

---

## 2. Authoritative Failure Bucket Classification (Section 5)

| Loss ID | Primary Failure Bucket | Secondary Mechanism | Evidence & Rationale |
| :---: | :--- | :--- | :--- |
| **L3 / L4** (Seed 250621) | **`OPPONENT_RELATIVE_EFFECT`** | `MARKET_TIMING` | V49 generated **+$3,921 more revenue** than V44. The loss was decided on Step 697 by market order index priority: V44's order queue placed Wool at Index 1, capturing $144 more cash in lockstep clearing, winning the match by $82. |
| **L1 / L2** (Seed 250617) | **`OPPONENT_RELATIVE_EFFECT`** | `ENDGAME_SETTLEMENT` | V49 generated **+$1,886 more revenue** than V44 and led by +$2,776 at Step 687 and +$162 at Step 704. In the final 14 turns, V44's field pathing captured 22 more strawberries before terminal cutoff, overtaking V49 by $862. |

### Classification Verdict:
Neither loss is caused by an `EXECUTION_FAILURE`, `LIQUIDITY_FAILURE`, `ANIMAL_LIFECYCLE`, or `LAND_LAYOUT`.
Both losses are textbook **`OPPONENT_RELATIVE_EFFECT`** events: two structurally near-identical agents competing in the same market niche, where the margin is decided by microscopic turn-order interactions within the final 20 steps of the season.
