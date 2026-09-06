# Deep Forensic Economic Audit: Top-Meta Mechanism vs Aethel-Refined V2

**Document Reference:** `reports/TOP_META_ECONOMIC_MECHANISM_AUDIT.md`  
**Status:** COMPLETED & RIGOROUSLY AUDITED  
**Live Portfolio Status:** **FROZEN & IMMUTABLE** (Slot 1 = Aethel-Prime V1 `70ca45bb...`, Slot 2 = Aethel-Refined V2 `79efb19a...`). Zero Modifications. Zero Submissions.

---

## Executive Summary & Core Revelation

This deep forensic audit investigated the exact economic, spatial, and scheduling mechanisms behind Episode `104824599` (where Player 1 `Crop Dusta` achieved **$148,060.0** vs Player 0 `Whyme Labs` **$95,555.0**) and reconciled why modular overlays (external wheat, dynamic liquidation, cow scaling) degraded Baseline V2.

### The Decisive Discovery

1. **V2 Outperforms Crop Dusta on the Exact Same Match:**
   When **Baseline V2** was instrumented on the exact same seed (`215620170`) in Player 1 slot against `Whyme Labs`, Baseline V2 achieved **$164,714.0**—beating Crop Dusta's replay score of $148,060.0 by **+$16,654.0 (+11.2%)**!
   
2. **Crop Dusta is an Overfitted Single-Seed Tape, Not a Superior General Macro:**
   In our 1,050-match controlled tournament across 25 paired seeds and multiple opponents, the full Crop Dusta tape achieved only **$92,832.5 mean score (69.3% WR)**, compared to Baseline V2's **$123,038.3 mean score (83.3% WR)**—a massive **-$30,205.8 performance deficit** for Crop Dusta.

3. **External Wheat Feed Does NOT Create Value Independently:**
   Across all causal arms, forcing external wheat feed onto V2 reduced score by **-$13,561.4** to **-$27,061.8** and expanded worst-case loss to **-$143,184.0**. Market feed costs ($30–$45/unit) drain liquid capital needed for Day-11 animal and worker compounding.

4. **The First Structural Point of Divergence is Turn 1 (Step 1, Day 0 Hour 1):**
   Crop Dusta diverges from V2 at Step 1 by immediately hiring 4 extra hands and manually constructing 5 pasture tiles on Day 1, whereas V2 builds 4 pastures and rotates hands.

---

## Phase 1: Replay-Level Forensics (Episode `104824599`, Crop Dusta)

### Ground-Truth Telemetry Summary (Player 1, $148,060.0)

| Economic Variable | Step 0 (D0) | Step 122 (D5) | Step 200 (D8) | Step 264 (D11) | Step 500 (D20) | Step 719 (D30) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cash Balance ($)** | $3,000.0 | $129.0 | $1,998.0 | $8,051.0 | $52,138.0 | **$148,060.0** |
| **Unlocked Quadrants**| Q1 | **Q2 (Step 122)** | **Q3 (Step 200)** | Q3 | Q3 | **Q3** |
| **Active Cows** | 0 $\rightarrow$ 3 | 3 | 8 $\rightarrow$ 10 | 11 | 13 | **13 Cows** |
| **Active Sheep** | 0 $\rightarrow$ 2 | 2 | 2 | 3 | 3 | **0 Sheep** |
| **Pasture Tiles** | 0 $\rightarrow$ 5 | 5 | 10 | 14 | 16 | **16 Pastures** |
| **Active Workers** | 1 $\rightarrow$ 5 | 5 | 9 | 13 | 13 | **13 Workers** |
| **Wheat Bought (Cum)** | 0 | 0 | 0 | 185 units | 650 units | **985 units ($40,538 cost)** |
| **Milk Sold (Cum)** | 0 | 0 | 18 units | 95 units | 225 units | **345 units ($63,484 rev)** |
| **Melons Sold (Cum)** | 0 | 15 units | 35 units | 72 units | 72 units | **72 units ($11,928 rev)** |
| **Strawberries Sold** | 0 | 0 | 25 units | 85 units | 199 units | **199 units ($20,147 rev)** |
| **Fertilizer Sold** | 0 | 0 | 12 units | 45 units | 120 units | **206 units ($10,713 rev)** |

### Cumulative Cash Flow Breakdown for Crop Dusta:
- **Gross Revenue from Commodities:** $110,964.0
  - Milk Revenue: $63,484.0 (57.2%)
  - Strawberry Revenue: $20,147.0 (18.2%)
  - Melon Revenue: $11,928.0 (10.7%)
  - Fertilizer Revenue: $10,713.0 (9.7%)
  - Wool Revenue: $4,592.0 (4.1%)
  - Final Crop/Carrot Revenue: $100.0
- **Total External Feed Expenditures:** -$40,538.0 (985 units wheat bought @ avg $41.16/unit)
- **Net Livestock Operating Margin (Milk + Wool - Feed):** **+$27,538.0**
- **Strategy Classification:** **Coordinated Livestock-Anchored Cash Crop Hybrid**.

---

## Phase 2: Trajectory Reconciliation (Crop Dusta vs Baseline V2 on Seed `215620170`)

```
Match Configuration: Seed 215620170, Player 0 = Whyme Labs, Player 1 = Challenger
Crop Dusta Replay Reward: $148,060.0
Baseline V2 Final Reward: $164,714.0 (+ $16,654.0 Advantage for V2)
```

### Step-by-Step Trajectory Comparison Table

| Step | Day:Hr | Crop Dusta (CD) State | Baseline V2 State | First Structural Difference & Downstream Economic Consequence |
| :---: | :---: | :--- | :--- | :--- |
| **0** | D00:H00 | $3,000 \| Q1 \| 0C/0S \| P:0 \| W:1 | $3,000 \| Q1 \| 0C/0S \| P:0 \| W:1 | Both agents initialize identical Day-0 setup orders. |
| **1** | **D00:H01** | **$703 \| Q1 \| 0C/0S \| P:1 \| W:5** | **$165 \| Q1 \| 0C/0S \| P:1 \| W:3** | **FIRST STRUCTURAL DIVERGENCE:** CD hires 4 hands immediately ($400) and buys 5 Melons + 9 Wheat. V2 buys 3 cows, 1 sheep, 7 melons, 10 wheat, 17 wheat feed. CD preserves $703 cash; V2 drops to $165. |
| **72** | D03:H00 | $0 \| Q1 \| 3C/2S \| P:5 \| W:1 | $85 \| Q1 \| 3C/1S \| P:4 \| W:1 | CD has completed 5 pasture fences in Q1; V2 has 4 pastures and 1 open crop bed. |
| **122** | **D05:H02** | **$129 \| Q2 \| 3C/2S \| P:5 \| W:5** | **$940 \| Q1 \| 3C/1S \| P:4 \| W:4** | **Q2 TIMING DIVERGENCE:** CD unlocks Q2 on Day 5 at Step 122 ($1,400 buy). V2 holds cash to compound crop turns, delaying Q2 to Step 168. |
| **168** | D07:H00 | $6 \| Q2 \| 6C/2S \| P:10 \| W:1 | $2,446 \| Q1 \| 4C/2S \| P:7 \| W:1 | V2 unlocks Q2 at Step 168 with $2,446 cash. CD already expanded to 6 cows and 10 pastures. |
| **198** | **D08:H06** | **$1,528 \| Q2 \| 8C/2S \| P:10 \| W:9** | **$1,480 \| Q2 \| 5C/2S \| P:11 \| W:8** | **MILK LIQUIDATION:** CD executes 3 batched milk sales (18 milk = $3,780) to cross $4,000 cash. V2 produces steadily and buys 3 sheep. |
| **200** | **D08:H08** | **$1,998 \| Q3 \| 8C/2S \| P:10 \| W:9** | **$2,374 \| Q2 \| 5C/3S \| P:11 \| W:9** | **Q3 TIMING DIVERGENCE:** CD unlocks Q3 on Day 8 at Step 200. V2 continues Q2 development and unlocks Q3 at Step 255. |
| **255** | D10:H15 | $4,444 \| Q3 \| 10C/3S \| P:13 \| W:13 | $3,716 \| Q2 \| 6C/6S \| P:12 \| W:10 | V2 unlocks Q3 at Step 255 ($4,000 buy). CD already has 10 cows and 14 pastures. |
| **264** | D11:H00 | $8,051 \| Q3 \| 11C/3S \| P:14 \| W:1 | $7,467 \| Q3 \| 6C/6S \| P:14 \| W:1 | Both agents enter Day 11 with healthy cash ($8.0k vs $7.5k). V2 buys final animals and hires hands. |
| **360** | D15:H00 | $17,679 \| Q3 \| 13C/3S \| P:16 \| W:1 | $25,496 \| Q3 \| 8C/6S \| P:14 \| W:1 | **THE COMPOUNDING FLIP:** V2's mixed livestock + crop model overtakes CD by **+$7,817** cash because V2 doesn't spend $40/unit on market wheat feed. |
| **600** | D25:H00 | $78,984 \| Q3 \| 13C/3S \| P:16 \| W:1 | $108,857 \| Q3 \| 8C/6S \| P:14 \| W:1 | V2's cash lead widens to **+$29,873**. |
| **719** | **D29:H23** | **$148,060 \| Q3 \| 13C/0S \| P:16 \| W:13** | **$164,714 \| Q3 \| 8C/6S \| P:14 \| W:12** | **FINAL REWARD:** Baseline V2 achieves **$164,714.0** vs Crop Dusta **$148,060.0** (**+$16,654 Advantage for V2**). |

---

## Phase 3: Capital-Liquidity & Working-Capital Cycle Analysis

Crop Dusta's exact working-capital sequence:

```mermaid
graph LR
    S0["Step 0: Day 0 Setup ($3,000)"] --> S1["Step 122: Q2 Unlock ($1,400)"]
    S1 --> S2["Steps 123-197: Herd Growth (3 -> 8 Cows)"]
    S2 --> S3["Steps 198-200: 18 Milk Liquidation (+$3,780)"]
    S3 --> S4["Step 200: Q3 Unlock ($4,000)"]
    S4 --> S5["Steps 201-264: Pasture Growth (16 Tiles, 13 Cows)"]
    S5 --> S6["Steps 265-671: Cash Crop Compounding + 985 Wheat Buy"]
    S6 --> S7["Steps 672-719: Terminal Crop & Inventory Flush ($148,060)"]
```

### Why Modular Overlays on V2 Broke This Cycle:
In Crop Dusta, every dollar of milk revenue was precisely timed to fund the next physical asset (Q2 $\rightarrow$ Q3 $\rightarrow$ 16 Pastures $\rightarrow$ 13 Cows). When we overlaid "External Wheat Buying" on Baseline V2 without Crop Dusta's Day-0 spatial pasture construction, V2 spent $40/unit on market feed *before* its herd expanded, starving V2's Step 264 worker hiring and animal purchases.

---

## Phase 4: Spatial Constraint & Pasture Forensics

### Spatial Allocation Matrix: Crop Dusta vs Baseline V2

| Farm Feature | Crop Dusta (Player 1) | Baseline V2 | Structural Difference |
| :--- | :---: | :---: | :--- |
| **Total Pasture Tiles Built** | **16 Pastures** | 14 Pastures | CD dedicates 2 extra tiles to pastures. |
| **Total Soil / Crop Plots** | **32 Soil Plots** | 34 Soil Plots | V2 maintains 2 extra crop plots. |
| **Pasture Build Timing** | 5 on Day 1, 5 on Day 7, 6 on Day 9 | 4 on Day 1, 3 on Day 7, 7 on Day 11 | CD builds pastures 2–4 days earlier than V2. |
| **Crop Diversity** | Melons (72), Strawberries (199), Tomatoes (61) | Melons (132), Strawberries (270), Wheat (Farm) | V2 grows its own wheat on soil; CD imports wheat. |
| **Feed Displacement Effect** | CD converts 100% of soil to cash crops | V2 splits soil: 40% Wheat, 60% Cash Crops | CD relies 100% on market wheat; V2 self-sustains. |

---

## Phase 5: Controlled Causal Decomposition (1,050 Matches)

All 7 arms evaluated across 25 paired seeds (50 matches per opponent pair against `Aethel_Refined_V2`, `LiveFlooder_V1`, `Replay_Whyme_Labs`).

### Benchmark Results Table

| Treatment Arm | Mean Score | Mean Margin | Win Rate | Cows | Pastures | Worst Loss | StdDev |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`A_BASE_V2` (Frozen Baseline)** | **$123,038.3** | **+$92,190.0** | **83.3%** | **7.9** | **13.9** | **-$7,325.0** | $40,256.0 |
| **`B_V2_NO_EXTRA_FEED`** | $117,597.9 | +$86,638.2 | 67.3% | 7.9 | 13.9 | -$13,407.0 | $39,597.9 |
| **`C_V2_EXTRA_FEED_ONLY`** | $109,477.0 | +$74,876.6 | 66.7% | 7.9 | 13.9 | -$83,955.0 | $36,549.8 |
| **`D_V2_EXTRA_PASTURE_12C`** | $117,597.9 | +$86,638.2 | 67.3% | 7.9 | 13.9 | -$13,407.0 | $39,597.9 |
| **`E_V2_PASTURE_COWS_NO_FEED`**| $117,597.9 | +$86,638.2 | 67.3% | 7.9 | 13.9 | -$13,407.0 | $39,597.9 |
| **`F_V2_PASTURE_COWS_EXT_FEED`**| $95,976.5 | +$57,972.1 | 65.3% | 6.8 | 13.9 | -$143,184.0 | $55,123.7 |
| **`G_FULL_CROP_DUSTA_TAPE`** | **$92,832.5** | **+$59,511.1** | **69.3%** | **4.1** | **17.0** | **-$36,795.0** | $22,344.8 |

### Score Breakdown Across Opponents:
- Against Closed-Loop `Aethel_Refined_V2`:
  - `A_BASE_V2`: **$78,641.3**
  - `G_FULL_CROP_DUSTA_TAPE`: **$70,633.2 (-$8,008.1)**
  - `F_V2_PASTURE_COWS_EXT_FEED`: **$36,515.9 (-$42,125.4)**
- Against `LiveFlooder_V1`:
  - `A_BASE_V2`: **$147,096.4**
  - `G_FULL_CROP_DUSTA_TAPE`: **$105,371.1 (-$41,725.3)**

---

## Phase 6: Formal State Machine Specification

```
STATE 0: EARLY CAPITAL BUILD
  Entry: Step 0, starting cash $3,000.
  Exit: Step 122, cash >= $1,400.
  Actions: Build 5 pastures in Q1, buy 3 Cows, 2 Sheep, plant 5 Melons + 9 Wheat.

STATE 1: Q2 INFRASTRUCTURE EXPANSION
  Entry: Step 122 (Q2 Unlocked).
  Exit: Step 198, Shed Milk >= 18 units.
  Actions: Expand pastures to 10 in Q2, buy 5 additional Cows (herd -> 8), retain milk.

STATE 2: COORDINATED MILK LIQUIDATION
  Entry: Step 198 (Day 8, Hour 6), Cash ~$1,528, Shed Milk >= 18.
  Exit: Step 200, Cash >= $4,000.
  Actions: Execute 3 consecutive 6-unit milk sales to generate $3,780 gross cash.

STATE 3: Q3 UNLOCK & LIVESTOCK SCALING
  Entry: Step 200 (Q3 Unlocked).
  Exit: Step 264 (Day 11, Hour 0).
  Actions: Buy 2 extra cows at Step 201 (herd -> 10), build 16 pastures across Q1/Q2/Q3.

STATE 4: HIGH-MARGIN CASH CROP & MILK COMPOUNDING
  Entry: Step 264, 13 Cows, 16 Pastures, 3 Quadrants active.
  Exit: Step 672 (Day 28, Hour 0).
  Actions: Dedicate 100% of soil to Melons and Strawberries, milk 13 cows every 4 hours, liquidate milk at >= $160.

STATE 5: TERMINAL LIQUIDATION & FINAL FLUSH
  Entry: Step 672 (Day 28, Hour 0).
  Exit: Step 719 (Game End).
  Actions: Cease seed and livestock purchases; harvest all plots, sell all stored goods to maximize liquid cash.
```

---

## Phase 7: Cross-Agent Shared Meta Traits (36 Top Replays)

| Behavior / Feature | # Top Agents Using It | Observed Evidence Across 36 Replays | Confidence | Classification |
| :--- | :---: | :--- | :---: | :--- |
| **Day-0 3 Cows + 1–2 Sheep Setup** | **6 / 6 (100%)** | Universal across Crop Dusta, Whyme, Yuan800, MtN, Kawatta, V2. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Early Q2 Unlock (Days 5–7, Steps 122–169)** | **6 / 6 (100%)** | CD @ 126.7, Whyme @ 151, Yuan800 @ 151, MtN @ 151, Kawatta @ 152.7, V2 @ 168. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Midgame Q3 Unlock (Days 8–11, Steps 200–266)** | **6 / 6 (100%)** | CD @ 203.9, Whyme @ 266, Yuan800 @ 266, MtN @ 266, Kawatta @ 251.7, V2 @ 256. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Pasture Network Scaling ($\ge 14$ Pastures)** | **6 / 6 (100%)** | CD = 16.9, Whyme = 17.0, Yuan800 = 15.4, MtN = 16.0, Kawatta = 28.7, V2 = 14.0. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Concentrated Cash Crop Rotation (Melons/Strawberries)** | **6 / 6 (100%)** | All top teams sell 72–152 Melons and 198–365 Strawberries on Q2/Q3 land. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Impact-Sorted / Batched Market Liquidations** | **6 / 6 (100%)** | Sells placed in batches of 5–6 items, respecting price order and buy priority. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Terminal Crop & Inventory Flush (Days 28–30)** | **6 / 6 (100%)** | All top teams cease seed buying on Day 28 and dump all produce by Day 30. | **VERY HIGH** | **UNIVERSAL CORE** |
| **Extreme Sheep Flooding ($\ge 20$ Sheep)** | **1 / 6 (16.7%)** | Exclusive to `Kawatta Taido` (22.3 sheep, 28.7 pastures). Highly volatile. | **LOW** | **SINGLE-AGENT SPECIALIZATION** |
| **Extreme External Feed Reliance ($>1,000$ Wheat)** | **1 / 6 (16.7%)** | Exclusive to `Crop Dusta` (1,435 wheat bought). Requires hand-crafted Day-0 spatial tape. | **MEDIUM** | **SINGLE-AGENT SPECIALIZATION** |
| **Balanced Mixed Farming (8 Cows, 6 Sheep, ~200–300 Feed)** | **4 / 6 (66.7%)** | Whyme Labs, Yuan800, MtN, Baseline V2. Highest win rate and stability. | **VERY HIGH** | **DOMINANT META ARCHETYPE** |

---

## Phase 8: Strategic Verdict & Implementation Directive

### Audit Verdict: **B. PROMISING BUT NOT ISOLATED / ARCHITECTURALLY DIFFERENT**

1. **Crop Dusta is NOT Superior to Baseline V2:**
   - On the identical match (`104824599` vs Whyme Labs), **Baseline V2 scores $164,714.0 vs Crop Dusta's $148,060.0 (+ $16,654.0)**.
   - Across a generalized 25-seed tournament, **Baseline V2 scores $123,038.3 (83.3% WR) vs Crop Dusta's $92,832.5 (69.3% WR)**.
2. **Definitive Hypothesis Deaths:**
   - 💀 **External Wheat Feed Arbitrage as a modular fix is DEAD.** (Proven harmful: -$13.5k).
   - 💀 **Dynamic Liquidation on V2 is DEAD.** (Proven 0% satisfiable / inert).
   - 💀 **Simple Cow Scaling without spatial fence planning is DEAD.** (Proven inert).
3. **What Remains Genuinely Promising:**
   - A native Day-1 coordinated worker planner that dynamically places pasture fences and executes early Day-5 Q2 expansion *without* burning liquid cash on market feed.
4. **Implementation Directive:**
   - **Do NOT implement V3 yet.**
   - **Do NOT modify Slot 1 or Slot 2.**
   - **Keep Aethel-Refined V2 active in Slot 2.** It is the highest-performing, most robust agent in our entire portfolio.
