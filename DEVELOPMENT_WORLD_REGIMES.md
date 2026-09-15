# DEVELOPMENT WORLD REGIMES: ENVIRONMENT PARTITIONING & TAXONOMY (POST-AUDIT 2.2)
## Source-Grounded Environment Taxonomy, Shop Mechanics, and Observable Economic Regimes

**Governing Standard**: Audit 2.2 Final Evidence Base ([`AUDIT2_2_FINAL_EVIDENCE_BASE.md`](file:///c:/Users/Sundareswaran/Kagriculture/AUDIT2_2_FINAL_EVIDENCE_BASE.md))  
**Simulator Grounding**: C++ Source `external_repos/kaggriculture-cppsim/sim/sim.hpp:127-137`, Python `kaggriculture.py`  
**Development Protocol**: Section 12 Problem Partitioning by World Type  
**Date**: 2026-09-11  
**Status**: **AUTHORITATIVE IMMUTABLE TAXONOMY**

---

## 1. Ground Truth Simulator Mechanics (Town Shops)

Town shops represent the primary external demand sink that can purchase player commodities at favorable, non-crashing prices. All world regime modeling must begin strictly from simulator code.

### 1.1 Town Shop Table & Demanded Goods

The simulator defines exactly 8 shop types (`sim.hpp:127-137`):

| Shop Enum Index | Shop Name | Demanded Commodities | Multiplier | Strategic Nature | Draw Probability (per slot) |
| :---: | :--- | :--- | :---: | :--- | :---: |
| **0** | **`BAKERY`** | `EGG`, `WHEAT` | 1.0x | Diversified basic food sink | 12.5% (1/8) |
| **1** | **`BRUNCH_SPOT`** | `EGG`, `WHEAT`, `STRAWBERRY` | 1.0x | Strawberry + Wheat + Poultry synergy | 12.5% (1/8) |
| **2** | **`FARMERS_MARKET`** | `WHEAT`, `CARROT`, `TOMATO`, `STRAWBERRY` | 1.0x | Broad multi-crop produce sink | 12.5% (1/8) |
| **3** | **`ICE_CREAM_SHOP`** | `STRAWBERRY`, `MILK`, `WHEAT` | 1.0x | Strawberry + Dairy joint synergy | 12.5% (1/8) |
| **4** | **`PET_CAFE`** | `CARROT` (Strictly) | **2.0x** | High-multiplier single-commodity sink | 12.5% (1/8) |
| **5** | **`PIZZA_SHOP`** | `MILK`, `TOMATO`, `WHEAT` (All 3 required) | 1.0x | Complex 3-commodity joint production sink | 12.5% (1/8) |
| **6** | **`SMOOTHIE_SHOP`** | `STRAWBERRY`, `MILK` | 1.0x | Strawberry + Dairy joint synergy | 12.5% (1/8) |
| **7** | **`YARN_STORE`** | `WOOL` (Strictly) | **2.0x** | High-multiplier single-commodity livestock sink | 12.5% (1/8) |

### 1.2 Marginal Commodity Draw Probabilities vs. Full Episode Realization

Each of the 8 shop slots is sampled **uniform at random with replacement** (`rng.choice_index(8)`). 

It is vital to distinguish between:
1. **Marginal Per-Slot Draw Probability ($p_c$)**: The probability that a single drawn shop slot demands commodity $c$.
2. **Full Episode Occurrence Probability ($1 - (1 - p_c)^8$)**: The probability that commodity $c$ appears at least once across all 8 shop unlock events in a match.

| Commodity | Demanding Shops (Count / 8) | Single Slot Marginal Draw Probability ($p_c$) | Probability in First 3 Reveals (by Day 9) | Probability Across Full 8-Shop Episode | Expected Shop Count in 8 Draws ($\mu = 8 p_c$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Wheat** | Bakery, Brunch, Farmers Market, Ice Cream, Pizza (5) | **62.50% (5/8)** | **94.73%** | **99.96%** | 5.00 shops |
| **Strawberry** | Brunch, Farmers Market, Ice Cream, Smoothie (4) | **50.00% (4/8)** | **87.50%** | **99.61%** | 4.00 shops |
| **Milk** | Ice Cream, Pizza, Smoothie (3) | **37.50% (3/8)** | **75.59%** | **97.67%** | 3.00 shops |
| **Tomato** | Farmers Market, Pizza (2) | **25.00% (2/8)** | **57.81%** | **89.99%** | 2.00 shops |
| **Carrot** | Farmers Market, Pet Cafe (2) | **25.00% (2/8)** | **57.81%** | **89.99%** | 2.00 shops |
| **Egg** | Bakery, Brunch (2) | **25.00% (2/8)** | **57.81%** | **89.99%** | 2.00 shops |
| **Wool** | Yarn Store (1) | **12.50% (1/8)** | **33.01%** | **65.64%** | 1.00 shops |

> [!NOTE]
> **Key Epistemic Distinction**: Commodities with a 25.0% per-slot draw probability (Tomato, Carrot, Egg) are NOT rare in full games. They appear in **89.99% of all 8-shop episodes**! The strategic variable is not mere presence, but the **arrival step** (Day 3 vs Day 24) and **cumulative capacity**.

### 1.3 Shop Unlock Schedule & Information Horizon

Shops unlock at dawn of every 3rd day starting at Day 3 (`step % 72 == 0` for steps $> 0$):

| Unlock Instance | Game Day | Game Step | Cumulative Shops Revealed | Fraction of Total Game Elapsed |
| :---: | :---: | :---: | :---: | :---: |
| **Shop 1** | **Day 3** | **Step 72** | 1 / 8 (12.5%) | 10.0% |
| **Shop 2** | **Day 6** | **Step 144** | 2 / 8 (25.0%) | 20.0% |
| **Shop 3** | **Day 9** | **Step 216** | 3 / 8 (37.5%) | 30.0% |
| **Shop 4** | **Day 12** | **Step 288** | 4 / 8 (50.0%) | 40.0% |
| **Shop 5** | **Day 15** | **Step 360** | 5 / 8 (62.5%) | 50.0% |
| **Shop 6** | **Day 18** | **Step 432** | 6 / 8 (75.0%) | 60.0% |
| **Shop 7** | **Day 21** | **Step 504** | 7 / 8 (87.5%) | 70.0% |
| **Shop 8** | **Day 24** | **Step 576** | 8 / 8 (100.0%) | 80.0% |

> [!IMPORTANT]
> **Decision Horizon Constraint**: Major crop planting decisions occur on **Day 0 (Step 0)** and **Day 11 (Step 264)**. At Day 0, **zero shops are known** (prior distribution only). At Day 11, **exactly 3 shops are known** (Shops 1, 2, 3), while Shops 4–8 (62.5% of town demand) remain completely unrevealed. Any strategy claiming to optimize Day-11 planting against total shop composition is guilty of future information leakage unless it conditions strictly on Shops 1–3.

---

## 2. Analyst-Created World Regime Taxonomy (Heuristic Abstractions)

> [!WARNING]
> **Epistemic Classification Notice**: The regimes defined below are **analyst-created heuristic abstractions**, NOT simulator game states. The simulator (`sim.hpp`) maintains zero internal state corresponding to these regimes. Furthermore, these regimes are **overlapping and partially observed**: at Day 0, zero shops are observable; at Day 6, only 2 shops are revealed. They serve strictly as conceptual modeling tools for decision conditioning, not deterministic physical environments.

```
                              [Game Initialization: Day 0]
                                  (Prior Distribution)
                                           │
                       ┌───────────────────┴───────────────────┐
                       ▼                                       ▼
            [Strawberry-Friendly Shop]              [Adverse / Niche Shop]
             (Brunch, Smoothie, Ice, FM)             (Pizza, Pet, Yarn, Bakery)
             Pr = 50.0% at Day 3                     Pr = 50.0% at Day 3
                       │                                       │
         ┌─────────────┴─────────────┐           ┌─────────────┴─────────────┐
         ▼                           ▼           ▼                           ▼
  [Regime A: Straw-Rich]     [Regime B: Mixed]   [Regime C: Niche/Pet]   [Regime D: Hostile]
  (>=2 Straw by Day 6)      (1 Straw, 1 Other)  (Pet Cafe / Yarn)       (0 Straw by Day 6)
```

### 2.1 Regime A: Strawberry-Rich Worlds (Heuristic Category)
- **Observable Signature**: $\ge 2$ Strawberry-demanding shops (`BRUNCH_SPOT`, `SMOOTHIE_SHOP`, `ICE_CREAM_SHOP`, `FARMERS_MARKET`) revealed in the first 3 reveals (Days 3, 6, 9).
- **Theoretical Probability**:
  $$\mathbb{P}(\ge 2 \text{ Straw in 3 draws}) = \binom{3}{2}(0.5)^2(0.5) + \binom{3}{3}(0.5)^3 = 3(0.125) + 0.125 = 50.0\%$$
- **Economic Characteristics**: 
  - Town center continuously absorbs strawberry volume without triggering price collapse.
  - Static 19S / 0T Strawberry Bedrock achieves strong empirical cash generation ($>\$96,000$) within the evaluated static grid on Discovery seeds.
  - Minimum risk of stranded production inventory.
- **Optimal Strategic Stance**: Maintain pure Strawberry Bedrock; maximize watering and harvest speed; execute standard sheep livestock schedule.

---

### 2.2 Regime B: Tomato / Pizza Synergy Worlds (Heuristic Category)
- **Observable Signature**: `PIZZA_SHOP` revealed at Day 3 (Step 72) or Day 6 (Step 144), accompanied by `FARMERS_MARKET` or dairy shop.
- **Theoretical Probability**:
  $$\mathbb{P}(\text{Pizza in first 2 draws}) = 1 - (7/8)^2 = 1 - 49/64 = 23.44\%$$
- **Economic Characteristics**:
  - `PIZZA_SHOP` requires **all three** inputs: Milk, Tomato, Wheat.
  - Selling Tomato without Milk or Wheat generates zero Pizza Shop sales.
  - Requires simultaneous dairy infrastructure (Cow costs $600, pasture tile, 8-day maturity) and tomato agronomy (seed $50, 8-day maturity).
- **Empirical Trap Warning**: As proven in Audit 2.2 (Retraction EVD-20), uncoordinated tomato planting on Pizza worlds collapsed ensemble returns by -$5,382.67 because cows were missing and tomato volume flooded the open market.
- **Optimal Strategic Stance**: Never pivot to tomato unless cow ownership and wheat inventory are already secured or guaranteed.

---

### 2.3 Regime C: High-Multiplier Niche Worlds (Pet Cafe & Yarn Store) (Heuristic Category)
- **Observable Signature**: `PET_CAFE` (2.0x Carrot) or `YARN_STORE` (2.0x Wool) revealed by Day 6 (Step 144).
- **Theoretical Probability**:
  $$\mathbb{P}(\text{Pet Cafe or Yarn Store in first 2 draws}) = 1 - (6/8)^2 = 1 - 36/64 = 43.75\%$$
- **Economic Characteristics**:
  - `PET_CAFE` pays 2.0x multiplier on Carrot ($70/unit baseline). Carrot matures in 2–3 days (fastest cash crop).
  - `YARN_STORE` pays 2.0x multiplier on Wool ($400/unit baseline). Sheep shearing cycle is 3 days.
  - In Episode 107543042, opponent exploited Triple Pet Cafe with Carrot/Tomato to reach $126,000 while our static strawberry agent managed only $71,000.
- **Optimal Strategic Stance**: Investigate fast 3-day carrot opportunistic planting cycles on Day 11 vacant tiles when Pet Cafe is confirmed active.

---

### 2.4 Regime D: Low-Strawberry Adverse Worlds (Glut / Drought) (Heuristic Category)
- **Observable Signature**: 0 Strawberry-demanding shops revealed across the first 3 reveals (Days 3, 6, 9).
- **Theoretical Probability**:
  $$\mathbb{P}(0 \text{ Straw in 3 draws}) = (0.5)^3 = 12.5\%$$
- **Economic Characteristics**:
  - All strawberry volume must be dumped onto the general market.
  - General market price curve drops sharply as cumulative sales exceed parameter $T = 100$ (`compute_market_price` enters depressed regime).
  - Severe revenue compression for pure strawberry agents.
- **Empirical Baseline Evidence**: On the 50 pure `Straw` seeds in our baseline scan, V2's mean margin vs Dmitrii dropped to -$20.48 (win rate 48.0%) as price depression penalized late strawberry liquidation.
- **Optimal Strategic Stance**: Conservative cash generation; accelerated market dumping before opponent floods the market; strict liquidity preservation.

---

## 3. Empirical World Distribution Across Evaluated 150 Seeds

Analyzing the realized shop sequences in `scratch/v2_dmitrii_margin_scan.json` reveals the empirical frequency of these regimes across the 150-seed benchmark:

| Realized Shop Family | Seeds Observed | Observed % | V2 Mean Cash | Dmitrii Mean Cash | Paired Margin | V2 Win Rate | Characterization |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`Pizza` (Pure)** | 1 | 0.67% | $97,075.00 | $97,086.00 | -$22.00 | 0.0% | Seed 50042: Singular outlier |
| **`Pizza+Straw`** | 99 | 66.00% | $95,209.46 | $95,185.53 | **+$47.86** | **58.6%** | Favorable joint demand; V2 dominates |
| **`Straw` (Pure)** | 50 | 33.33% | $96,593.72 | $96,603.96 | **-$20.48** | **48.0%** | Pure strawberry; Dmitrii terminal planner wins |
| **Total Benchmark** | **150** | **100.0%** | **$95,683.47** | **$95,658.85** | **+$24.61** | **54.67%** | Central evaluated distribution |

> [!NOTE]
> **Data Provenance & Historical Code Note**: The three-way partition above was generated by `scratch/run_margin_scan.py:50-71`. It evaluated `obs_final` at Step 719 (post-match hindsight). In addition, line 57 of `run_margin_scan.py` checked `"YARN_SHOP" in shops` instead of `"YARN_STORE"`, which caused Yarn Store occurrences to be subsumed into `Straw` or `Pizza+Straw`. This table is an empirical report of historical scan logging, not an authoritative physical ontology of the simulator.

---

## 4. Production Synergies, Capital Requirements & Conflict Matrix

Economic specializations cannot be mixed freely; they compete directly for **tiles, worker hands, cash liquidity, and shed capacity**:

| Production Line | Capital Cost | Maturity Time | Harvest Interval | Land Footprint | Labor Demand (Hands/Turn) | Shed Footprint | Primary Town Synergies | Major Operational Conflict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **Strawberry** | $100 / seed | 10 days | 2 days (4 crops) | 19 tiles (NW/NE/SW) | 4–6 watering / harvest | 16–24 units / wave | Brunch, Smoothie, Ice Cream, FM | Requires high sustained liquidity; blocks land for 18 days. |
| **Tomato** | $50 / seed | 8 days | 1 day (4 crops) | 4–8 tiles | 4–8 watering / harvest | 16–32 units / wave | Pizza Shop, Farmers Market | Daily harvesting consumes heavy worker actions; rots quickly. |
| **Carrot** | $20 / seed | 2–3 days | Single harvest | 2–4 tiles | 1–2 actions | 8–16 units | Pet Cafe (2.0x), Farmers Market | Fast cash turnaround; low capital risk. |
| **Wheat** | $10 / seed | 2–4 days | Single harvest | 2–4 tiles | 1–2 actions | 8–16 units | Bakery, Brunch, Pizza, Ice Cream | Essential ingredient for Pizza; low margin on open market. |
| **Sheep (Wool)** | $500 / head | 6 days | 3 days | 1 pasture tile | 1 feed/care/shear | 1–2 wool / cycle | Yarn Store (2.0x) | Requires feed buffer; early cash drain on Day 6. |
| **Cow (Milk)** | $600 / head | 8 days | 2 days | 1 pasture tile | 1 feed/care/milk | 1–2 milk / cycle | Pizza, Ice Cream, Smoothie | Expensive; slow return; requires pasture space. |

---

## 5. Opponent Specialization & Market Coupling

In addition to town shops, the realized environment is shaped by **opponent actions in the shared market**:

1. **Simultaneous Market Execution**:
   - Both players submit market orders independently each turn.
   - Orders execute in alternating or array index sequence without revealing current-turn orders.
   - If both players sell strawberry in the same turn, the second player suffers immediate price depression from the first player's sales volume.
2. **Opponent Farm Telemetry (Observable)**:
   - Opponent tile layouts, crops, animals, and worker counts are **legally observable in `obs`** each turn.
   - If opponent's NW quadrant is 100% strawberry on Day 1, an opponent strawberry glut is guaranteed on Days 10, 12, 14, 16.
   - If opponent builds pastures on Day 6, wool market prices will face supply pressure by Day 12.
3. **Strategic Rule for Development**:
   - Never condition agent strategy on future opponent moves.
   - Condition strictly on observable past opponent tile allocations and historical market price movements.
