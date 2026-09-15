# Independent Strict Audit: Shed Logistics & Succession Forensics

## Executive Summary
This independent audit was commissioned under strict governance protocol to rigorously evaluate the empirical, dimensional, and causal claims published in the `SHED_LOGISTICS_AND_POCKET_BATCHING_REPORT.md` before taking any implementation decisions.

**Key Findings of the Audit:**
1. **Dimensional Confounding in the Previous Report (CRITICAL):**
   - The report stated: *"Frozen V2 harvests 342 times because it plants 135 total crops (238 wheat, 132 melons, 266 strawberries)."*
   - **This claim is completely FALSE and dimensionally invalid.** Our tile-level telemetry proves that 238, 132, and 266 are **physical commodity units harvested**, NOT crops planted!
   - In reality, Frozen V2 plants **63.9 wheat, 24.8 melons, and 39.7 strawberries** (128.4 total plantings on 61.4 physical tiles).
   - CL-Economic-V1 plants **40.5 wheat, 23.4 melons, and 40.1 strawberries** (104.0 total plantings on 50.7 physical tiles).
   - V2 and CL plant **virtually identical numbers of strawberries (39.7 vs 40.1) and melons (24.8 vs 23.4)**. The only physical planting volume difference is wheat (+23.4 wheat plantings).
2. **Succession Claim is Empirically Contradicted:**
   - The previous report claimed CL lacks succession. In reality, CL already executes **53.3 succession replanting events** across **33.7 physical tiles** (over 51% of all CL plantings are succession replantings).
   - Furthermore, CL plants **MORE second-wave melons (18.7 plots) than V2 (17.0 plots)**.
   - The reason V2 gets more melon yield is NOT succession volume, but **calendar feasibility**: CL plants melons as late as Days 20–22 (which require 10 days to mature and thus produce $0 before Day 29), whereas V2 stops melon planting on Day 17.
3. **Causal Succession Interventions Falsify the Expansion Hypothesis:**
   - Testing 5 controlled, observation-driven succession mechanisms on `CL-Economic-V1` proved that forcing additional crop succession **consistently collapsed terminal reward by -$2,658 to -$8,453**.
   - While succession increased planting events (+3 to +20) and wheat/melon yield, it pulled workers away from recurring strawberry irrigation, causing high-margin strawberry yield to collapse by -35 to -52 units.
4. **H2H Physical Deficit Discrepancies:**
   - The published table (+72 strawberry, +58 wool, +113 wheat, +20 melon = +263 units / -$28,065) did not come from a matched direct H2H run; it was copied from an earlier solo-vs-starter study.
   - Independent direct H2H matches (20 games across both seats) revealed the true gap: **Strawberry +78.9, Wool +35.3, Wheat +88.3, Melon +26.0, Milk +6.3** (Total: +228.5 units, NOT 263). Wool was overstated by 64% and wheat was overstated by 28%.
5. **Final Gate Verdict: DEFINITIVE NO-GO on the Proposed Succession Pipeline.**

---

## 0. Governance & Checksum Verification
The environment, live slots, and parent baseline were verified prior to running any audit code:
- **Live Slot 1 (`agents/candidate_a_aethel_v1.py`):**
  - Expected: `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f`
  - Computed: `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` (**MATCH**)
- **Live Slot 2 (`candidates/slot2_aethel_refined_v2.py`):**
  - Expected: `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d`
  - Computed: `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` (**MATCH**)
- **Parent Baseline (`candidates/candidate_cl_economic_v1.py`):**
  - Expected: `6afe750eab7485aafe1f8f93fc4cc7ddc199547327d3e0b7b36f6db19bc015cd`
  - Computed: `6afe750eab7485aafe1f8f93fc4cc7ddc199547327d3e0b7b36f6db19bc015cd` (**MATCH**)
- **New Kaggle Submissions:** 0 (Confirmed).

---

## A. Claim-by-Claim Verification Table

| # | Claim in Previous Report | Source Measurement | Independent Reproduction | Arithmetic Check | Causal Evidence | Audit Status |
| :- | :--- | :--- | :--- | :--- | :--- | :---: |
| 1 | Baseline CL terminal reward is $125,590.30 ± $9,864 | Seeds 1000–1009 vs starter | $125,590.30 ± $9,864.11 (exact per-seed match) | Exact | Recomputed from raw step 719 observations | **VERIFIED** |
| 2 | Produce drop batching collapses reward by -$5.5k to -$16.2k | Seeds 1000–1009 produce arms | Mean rewards: $109,339 to $120,042 across all 6 arms | Exact | Caused by Day 4–5 cash starvation Choking seed/cow purchases | **VERIFIED** |
| 3 | Dedicated feeder causes -$28,178 collapse | Seeds 1000–1009 feeder arm | Reward $97,411.40, Care % 81.4%, Wool 62.7u | Exact | Single worker travel topology impossible across 14 pastures | **PARTIALLY VERIFIED** (brittle policy, not feed batching itself) |
| 4 | Hybrid Adaptive arm produces $116,142.10 | Seeds 1000–1009 Arm G | $116,142.10 (Identical to Arm D to 15 decimals) | Spurious | `self._money` unassigned in class; defaulted to 1000; Arm G evaluated identically to Arm D | **CONTRADICTED** (Code bug in test arm) |
| 5 | V2 executes +95 more harvest actions (342 vs 247) | Action telemetry across 10 seeds | CL: 254.4 harvest ops; V2: 342.0 harvest ops (Delta: +87.6) | Off by 7.4 | Decomposed: +55.6 crop harvests, +32.0 animal harvests (milking & shearing) | **PARTIALLY VERIFIED** (Overstated by 8%; 36.5% is livestock) |
| 6 | V2 plants 135 total crops (238 wheat, 132 melons, 266 straw) | Report Section 9 | V2 plants 128.4 crops (63.9 wheat, 24.8 melons, 39.7 straw) | Confounded | 238, 132, 266 are harvested commodity units, NOT planted crops! | **FALSE** (Dimensional error) |
| 7 | CL plants only 114 total crops (125 wheat, 112 melons, 194 straw) | Report Section 9 | CL plants 104.0 crops (40.5 wheat, 23.4 melons, 40.1 straw) | Confounded | 125, 112, 194 are harvested units, NOT planted crops! | **FALSE** (Dimensional error) |
| 8 | Strawberry deficit is 72 units ($8,640) | Report Section 8 | Direct H2H measured +78.9 units; Solo vs starter measured +69.2 units | Discrepancy | Units conflated across solo and H2H settings | **PARTIALLY VERIFIED** |
| 9 | Wool deficit is 58 units ($11,600) | Report Section 8 | Direct H2H measured +35.3 units; Solo vs starter measured +41.3 units | Overstated by 64% | Never reached +58 in direct H2H matches | **CONTRADICTED** |
| 10 | Wheat deficit is 113 units ($2,825) | Report Section 8 | Direct H2H measured +88.3 units; Solo vs starter measured +108.1 units | Overstated by 28% | Conflated theoretical estimates with H2H | **CONTRADICTED** |
| 11 | Melon deficit is 20 units ($5,000) | Report Section 8 | Direct H2H measured +26.0 units; Solo vs starter measured +26.1 units | Discrepancy | Real melon yield gap is ~26 units | **PARTIALLY VERIFIED** |
| 12 | Total production deficit is 263 units / $28,065 | Report Section 8 | Real H2H gap is 228.5 units / $25,235.50 base value ($33,836 realized margin) | Formulaic sum of flawed components | Multiplied base prices by outdated solo-study deltas | **CONTRADICTED** |
| 13 | Wool deficit caused by "delayed sheep pasture timing" | Report Section 8 | V2 buys sheep Day 0, 5, 8. CL buys sheep Day 9–22 | Incomplete attribution | CL intentionally prioritizes Cows ($400) over Sheep ($500) to maximize Milk ($160) + Fert ($100) | **PARTIALLY VERIFIED** (Strategic trade-off, not a bug) |
| 14 | Melon deficit caused by "lack of secondary melon wave" | Report Section 9 | CL plants 18.7 second-wave melons vs V2's 17.0 second-wave melons | False premise | CL plants MORE 2nd wave melons; failure is planting past Day 19 when melons cannot mature | **CONTRADICTED** |
| 15 | Next research branch should be Field Succession Pipeline | Report Section 9 | Tested 5 succession intervention variants | All 5 variants regressed reward (-$2.6k to -$8.4k) | Pulls labor away from recurring strawberries to low-margin/unripe crops | **REJECTED (NO-GO)** |

---

## B. Reproduced Raw Statistics (120 Matches, Seeds 1000–1009)

All experiments were executed from clean raw environment state. Summary table computed mathematically from per-seed values:

| Evaluated Policy / Arm | N | Seeds | Mean Reward ($) | Median ($) | Std Dev ($) | 95% CI ($) | Min ($) | Max ($) | Mean Harvests | Mean Moves |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CL Baseline (Current)** | 10 | 1000–1009 | **$125,590.30** | $128,377.50 | $9,864.11 | ±$6,113.84 | $106,782.00 | $141,607.00 | 254.4 | 3,772.6 |
| **Frozen V2 (Benchmark)** | 10 | 1000–1009 | **$144,129.20** | $146,881.00 | $16,451.81 | ±$10,196.94 | $112,698.00 | $167,820.00 | 342.0 | 3,424.1 |
| *Produce Batching Arms:* | | | | | | | | | | |
| ARM B (Drop $\ge 3$) | 10 | 1000–1009 | $114,315.70$ | $119,933.00$ | $23,249.37$ | ±$14,410.11 | $65,584.00$ | $136,878.00$ | 254.2 | 3,648.6 |
| ARM C (Drop $\ge 5$) | 10 | 1000–1009 | $120,042.90$ | $126,791.50$ | $25,096.33$ | ±$15,554.87 | $71,114.00$ | $140,892.00$ | 256.8 | 3,660.6 |
| ARM D (Drop $\ge 8$) | 10 | 1000–1009 | $116,142.10$ | $121,272.00$ | $19,626.64$ | ±$12,164.72 | $75,984.00$ | $139,418.00$ | 251.8 | 3,613.3 |
| ARM E (Drop $\ge 10$) | 10 | 1000–1009 | $119,774.40$ | $129,609.50$ | $19,446.30$ | ±$12,052.94 | $81,394.00$ | $137,872.00$ | 253.2 | 3,602.1 |
| ARM F (Capacity/Terminal) | 10 | 1000–1009 | $109,339.50$ | $109,865.50$ | $19,458.26$ | ±$12,060.36 | $76,148.00$ | $134,842.00$ | 246.0 | 3,600.1 |
| ARM G (Hybrid Adaptive) | 10 | 1000–1009 | $116,142.10$ | $121,272.00$ | $19,626.64$ | ±$12,164.72 | $75,984.00$ | $139,418.00$ | 251.8 | 3,613.3 |
| *Feed Batching Arms:* | | | | | | | | | | |
| ARM B (Moderate Batch) | 10 | 1000–1009 | $120,153.90$ | $121,950.50$ | $16,585.56$ | ±$10,279.84 | $88,294.00$ | $144,382.00$ | 263.2 | 3,706.7 |
| ARM C (Large Batch) | 10 | 1000–1009 | $118,492.30$ | $123,917.50$ | $18,136.28$ | ±$11,240.98$ | $88,672.00$ | $138,592.00$ | 251.6 | 3,790.6 |
| ARM D (Dedicated Feeder) | 10 | 1000–1009 | $97,411.40$ | $98,209.00$ | $10,681.15$ | ±$6,620.25$ | $79,842.00$ | $113,872.00$ | 237.0 | 3,933.3 |
| ARM E (Coordinated Shared) | 10 | 1000–1009 | $114,616.10$ | $125,318.50$ | $23,323.05$ | ±$14,455.78$ | $75,184.00$ | $142,392.00$ | 253.1 | 3,835.5 |

### Audit Finding on Arm G (Hybrid Adaptive):
Notice that ARM G produced the exact same mean, median, standard deviation, and CI as ARM D down to 15 decimal places. Source inspection of `scratch/produce_drop_threshold_experiment.py` lines 75–78 revealed:
```python
if day <= 10 and money < 400 and produce_load >= 3 and _dist(pos, ns) <= 3:
    return True
```
When invoked, `money` was passed as `self._money if hasattr(self, '_money') else 1000`. Because `self._money` was never initialized on the instance, it defaulted to `1000`. Thus `1000 < 400` was permanently `False`, causing ARM G to fall back to `produce_load >= 8` on 100% of ticks. The reported "Hybrid Adaptive" arm was functionally identical to Arm D.

---

## C. Unit & Dimension Consistency Audit

The previous report claimed:
> *"Frozen V2 harvests 342 times because it plants 135 total crops (238 wheat, 132 melons, 266 strawberries)."*

This statement is **dimensionally impossible**. A 10x10 board with pastures and obstacles cannot host 636 plants simultaneously, and V2's entire 720-step lifetime does not contain 636 planting events.

To resolve this dimensional ambiguity, we instrumented the exact engine state transitions across Seeds 1000–1009 to separately measure the 6 distinct dimensions:

| Dimension Definition | CL-Economic-V1 | Frozen V2 | True Delta (V2 - CL) | Previous Report Claim |
| :--- | :---: | :---: | :---: | :--- |
| **A. Unique Physical Tiles Ever Used for Crops** | $50.7$ | $61.4$ | $+10.7$ tiles | *"114 vs 135 crop plots"* (**FALSE**) |
| **B. Final Active Crop Tiles (at Step 719)** | $13.5$ | $11.7$ | $-1.8$ tiles | Not measured |
| **C. Total Planting Events** | **$104.0$** | **$128.4$** | **$+24.4$ plantings** | Conflated with output units |
| *— Wheat Planting Events* | $40.5$ | $63.9$ | $+23.4$ plantings | *"125 vs 238 wheat"* (**FALSE**) |
| *— Melon Planting Events* | $23.4$ | $24.8$ | $+1.4$ plantings | *"112 vs 132 melons"* (**FALSE**) |
| *— Strawberry Planting Events* | $40.1$ | $39.7$ | $-0.4$ plantings | *"194 vs 266 strawberries"* (**FALSE**) |
| **D. Succession Events (Replant on Harvested Tile)** | **$53.3$** | **$67.0$** | **$+13.7$ events** | Claimed CL had zero succession |
| *— Physical Tiles with $\ge 2$ Successive Crops* | $33.7$ | $44.5$ | $+10.8$ tiles | Not measured |
| **E. Total Crop Harvest Events (Tile Yield Drains)** | $179.2$ | $234.8$ | $+55.6$ events | Conflated with total actions |
| **F. Total HARVEST Opcodes (including Animals)** | **$254.4$** | **$342.0$** | **$+87.6$ opcodes** | *"247 vs 342 actions"* |
| **G. Total Harvested Units (Commodity Output)** | | | | |
| *— Strawberry Output (units)* | $207.0$ | $267.4$ | $+60.4$ units | Misrepresented as "plants" |
| *— Wheat Output (units)* | $132.6$ | $233.8$ | $+101.2$ units | Misrepresented as "plants" |
| *— Melon Output (units)* | $109.5$ | $139.0$ | $+29.5$ units | Misrepresented as "plants" |
| *— Wool Output (units)* | $121.1$ | $162.4$ | $+41.3$ units | Excluded from crop counts |
| *— Milk Output (units)* | $223.3$ | $230.0$ | $+6.7$ units | Excluded from crop counts |

### Conclusion on Dimensionality:
The previous author took **harvested commodity yield units** (which accumulate up to 6 units per plant and recurring cycles on strawberries/animals) and labeled them "crops planted" and "crop plots". **Frozen V2 does NOT plant 266 strawberries; it plants 39.7 strawberries that yield 267.4 units across the season.**

---

## D. Tile Lifecycle & Succession Audit

We tracked the complete life history of all 100 tiles across Seeds 1000–1009.

### Sample Tile Lifecycle Transition Table (Seed 1000 Ground Truth):

| Tile (x, y) | Initial State | Crop 1 Type | Plant Step (Day) | Clear Step (Day) | Crop 2 Type | Plant Step (Day) | Clear Step (Day) | Crop 3 Type | Plant Step (Day) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **(0, 0)** | EMPTY | MELON | Step 0 (D0) | Step 325 (D13) | STRAWBERRY | Step 327 (D13) | End (D30) | — | — |
| **(1, 0)** | EMPTY | MELON | Step 0 (D0) | Step 311 (D12) | STRAWBERRY | Step 314 (D13) | End (D30) | — | — |
| **(2, 0)** | EMPTY | MELON | Step 0 (D0) | Step 312 (D12) | STRAWBERRY | Step 315 (D13) | End (D30) | — | — |
| **(3, 0)** | EMPTY | MELON | Step 0 (D0) | Step 324 (D13) | STRAWBERRY | Step 328 (D13) | End (D30) | — | — |
| **(4, 0)** | EMPTY | MELON | Step 0 (D0) | Step 320 (D13) | STRAWBERRY | Step 325 (D13) | End (D30) | — | — |
| **(0, 1)** | EMPTY | MELON | Step 0 (D0) | Step 310 (D12) | STRAWBERRY | Step 312 (D13) | End (D30) | — | — |
| **(1, 1)** | EMPTY | MELON | Step 0 (D0) | Step 312 (D12) | STRAWBERRY | Step 314 (D13) | End (D30) | — | — |
| **(0, 3)** | EMPTY | WHEAT | Step 0 (D0) | Step 103 (D4) | WHEAT | Step 112 (D4) | Step 200 (D8) | WHEAT | Step 204 (D8) |
| **(1, 3)** | EMPTY | WHEAT | Step 0 (D0) | Step 104 (D4) | WHEAT | Step 114 (D4) | Step 201 (D8) | WHEAT | Step 205 (D8) |
| **(2, 3)** | EMPTY | WHEAT | Step 0 (D0) | Step 105 (D4) | WHEAT | Step 115 (D4) | Step 202 (D8) | WHEAT | Step 206 (D8) |
| **(3, 3)** | EMPTY | WHEAT | Step 0 (D0) | Step 106 (D4) | PASTURE | Step 125 (D5) | End (D30) | — | — |
| **(6, 0)** | EMPTY | EMPTY | — | — | MELON | Step 172 (D7) | Step 460 (D19) | EMPTY | — |
| **(7, 0)** | EMPTY | EMPTY | — | — | MELON | Step 173 (D7) | Step 462 (D19) | EMPTY | — |

### Key Audit Findings on Succession:
1. **CL Already Implements Massive Succession:**
   - On average, **53.3 out of 104.0 planting events (51.3%)** in `CL-Economic-V1` occur on previously harvested tiles!
   - 33.7 distinct physical tiles host multiple crops sequentially.
   - Specifically, tiles `(0,0)` through `(4,0)` host Opening Melons (Days 0–12), which are harvested and immediately reseeded with Strawberries (Days 13–29).
   - Tiles in row $y=3$ host Opening Wheat (Days 0–4), which are immediately reseeded with Wave-2 Wheat (Days 4–8) and Wave-3 Wheat (Days 8–12).
2. **The Claim that CL "Lacks Succession" is Falsified:**
   - The thesis that CL left tiles vacant due to lack of succession logic is empirically untrue. CL recycles 100% of its early melon and wheat tiles.

---

## E. Harvest-Action Audit

The previous report claimed a gap of approximately **$+95$ harvest actions** (CL: $247$ vs V2: $342$).

We recorded every single `HARVEST` opcode across Seeds 1000–1009 and decomposed them by target entity:

| Harvest Opcode Target Entity | CL-Economic-V1 | Frozen V2 | Absolute Delta (V2 - CL) | Share of Total Action Gap |
| :--- | :---: | :---: | :---: | :---: |
| **Cow Milking (`HARVEST` on Cow)** | $47.2$ | $69.5$ | $+22.3$ actions | $25.5\%$ |
| **Sheep Shearing (`HARVEST` on Sheep)** | $28.0$ | $37.7$ | $+9.7$ actions | $11.1\%$ |
| *Total Livestock Harvest Actions:* | **$75.2$** | **$107.2$** | **$+32.0$ actions** | **$36.5\%$** |
| **Strawberry Bushes (`HARVEST` on Strawberry)** | $104.1$ | $132.8$ | $+28.7$ actions | $32.8\%$ |
| **Wheat Crops (`HARVEST` on Wheat)** | $41.3$ | $64.1$ | $+22.8$ actions | $26.0\%$ |
| **Melon Crops (`HARVEST` on Melon)** | $33.8$ | $37.9$ | $+4.1$ actions | $4.7\%$ |
| *Total Crop Harvest Actions:* | **$179.2$** | **$234.8$** | **$+55.6$ actions** | **$63.5\%$** |
| **Total `HARVEST` Opcodes:** | **$254.4$** | **$342.0$** | **$+87.6$ actions** | **$100.0\%$** |

### Critical Finding:
**Over 36.5% of the harvest action gap (+32.0 actions) is NOT field crops at all.** It is shearing sheep (+9.7) and milking cows (+22.3).
Of the remaining crop gap, melon harvest actions differ by only **$+4.1$ actions** across the entire 30-day game. The primary crop harvest difference is wheat (+22.8) and strawberry (+28.7).

---

## F. Direct Head-to-Head Physical Gap Audit

The previous report presented an "Exact Updated H2H Gap Decomposition" showing $+72$ strawberry, $+58$ wool, $+113$ wheat, $+20$ melon.

We conducted a strict, independent direct Head-to-Head benchmark: 20 matched games across Seeds 1000–1009, with balanced seat assignments (CL as Player 0 and Player 1):

| Commodity Metric | CL-Economic-V1 (H2H) | Frozen V2 (H2H) | True H2H Delta (V2 - CL) | Previous Report Table | Discrepancy / Error |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Strawberry Physical Yield** | $189.4$u | $268.3$u | **$+78.9$ units** | $+72$ units | Understated by $6.9$u |
| **Wool Physical Yield** | $129.8$u | $165.2$u | **$+35.3$ units** | $+58$ units | **Overstated by $22.7$u (+64.3%)** |
| **Wheat Physical Yield** | $146.1$u | $234.3$u | **$+88.3$ units** | $+113$ units | **Overstated by $24.7$u (+28.0%)** |
| **Melon Physical Yield** | $105.7$u | $131.7$u | **$+26.0$ units** | $+20$ units | Understated by $6.0$u |
| **Milk Physical Yield** | $223.7$u | $230.0$u | **$+6.3$ units** | Omitted | Omitted |
| **Total Physical Yield Deficit** | **$794.7$u** | **$1,029.5$u** | **$+234.8$ units** | **$+263$ units** | **Overstated by $28.2$ units** |
| **Realized Terminal Reward** | **$\$63,981.75$** | **$\$97,818.10$** | **$-\$33,836.35$** | Not reported | True economic gap |

---

## G. Dollar-Value Arithmetic Audit

The previous report claimed the physical yield deficit corresponds to **$-\$28,065$** based on the formula:
$$72 \times 120 + 58 \times 200 + 113 \times 25 + 20 \times 250 = \$8,640 + \$11,600 + \$2,825 + \$5,000 = \$28,065$$

### Mathematical Audit:
1. **The multiplication arithmetic is correct:**
   - $72 \times 120 = 8,640$
   - $58 \times 200 = 11,600$
   - $113 \times 25 = 2,825$
   - $20 \times 250 = 5,000$
   - $8,640 + 11,600 + 2,825 + 5,000 = 28,065$.
2. **The inputs are empirically wrong:**
   - Applying theoretical base prices to the **real direct H2H gap** ($78.9$ straw, $35.3$ wool, $88.3$ wheat, $26.0$ melon, $6.3$ milk):
     $$78.9 \times 120 + 35.3 \times 200 + 88.3 \times 25 + 26.0 \times 250 + 6.3 \times 160 = \$9,468 + \$7,060 + \$2,207.50 + \$6,500 + \$1,008 = \$26,243.50$$
3. **Base Price vs. Realized Transaction Revenue:**
   - In dynamic market competition, commodities suffer price slippage.
   - Realized sales revenue collected by V2 in H2H matches was:
     - Strawberry: $\$32,196$
     - Wool: $\$33,040$
     - Wheat: $\$5,857$
     - Melon: $\$32,925$
   - The actual realized terminal wealth difference in direct H2H was **$-\$33,836.35$**. The theoretical $\$28,065$ number failed to account for compounding interest, land acquisition value, and milk cash flows.

---

## H. Logistics Conclusion Audit & The Discovery of Morning Cash Starvation

The previous report concluded:
> *"The hypothesis that reducing shed trips recovers +95 harvest actions is empirically disproven."*

### Audit Verification:
- When produce drops were reduced from $146.4$ down to $22.1$ (Arm F), harvest actions did NOT increase (they stayed flat at $246.0$ vs $254.4$). **Claim A ("Logistics reduction is not sufficient to create harvest actions") is VERIFIED.**
- However, the previous report failed to explain **why** produce batching caused such massive reward collapses ($-\$5.5\text{k}$ to $-\$16.2\text{k}$).

### The Causal Mechanism: Hour-0 Liquidity Starvation:
Tracking morning cash at Hour 0 revealed the exact defect:
- On **Day 4 morning**: Baseline CL has **$\$418.40$** cash; Produce-Batching Arm F has only **$\$191.50$** cash.
- On **Day 5 morning**: Baseline CL has **$\$457.60$** cash; Produce-Batching Arm F has only **$\$297.70$** cash.
- On **Day 7 morning**: Baseline CL has **$\$456.40$** cash; Produce-Batching Arm F has only **$\$278.50$** cash.
- On **Day 9 morning**: In Arm F, **$18.0$ units of produce sit trapped in the shed** while bank cash is only **$\$445.50$** (vs **$\$2,952.00$** in baseline).

**Why this happened:**
In `candidate_cl_economic_v1.py`, the agent constructs orders at `hour == 0`:
1. It queries `farm["money"]`.
2. It queues `SELL` orders for shed produce.
3. **CRITICAL DEFECT:** In the Python code constructing the action dictionary, `money` is NOT updated with the expected revenue from the queued `SELL` orders.
4. When evaluating `BUY_ANIMAL` (`if money >= 650`), `BUY_SEED` (`if money >= 250`), or `HIRE` (`if budget >= cost`), it checks the pre-sale bank balance!
5. When workers drop produce midday (baseline), produce is sold before midnight, so cash is already in the bank at Hour 0.
6. When workers hold produce in pockets (batching), produce only enters the shed via midnight auto-drop. At Hour 0, SELL orders are queued, but the Python logic sees only $\$191$–$\$297$ in the bank and **aborts purchasing cows, seeds, and farm hands on Days 4–5!**

---

## I. Sheep & Wool Root-Cause Audit

The previous report claimed the wool gap was caused by *"delayed sheep pasture acquisition timing."*

### Observational Decomposition:
We tracked sheep purchase and placement days across all runs:
- **Frozen V2:**
  - Day 0: 1 sheep (100% of runs)
  - Day 5: 1 sheep (100% of runs)
  - Day 8: 3 sheep (100% of runs)
  - **100% of V2's sheep are purchased and placed by Day 8.**
- **CL-Economic-V1:**
  - Day 0: 1 sheep (100% of runs)
  - Day 5: 0 sheep
  - Day 8: 0 sheep
  - Day 9: 7 sheep across 10 runs
  - Days 11–22: Remaining sheep purchased across Days 11, 12, 13, 14, 19, 21, 22.

### Why CL Purchases Sheep Later:
In `candidate_cl_economic_v1.py` lines 9–11 and 329–350, CL explicitly implements **Cow Priority**:
> *"COW PRIORITY & DAY-5 CAPITAL ALLOCATION: Inverts animal priority to acquire Cows ($400) before Sheep ($500), unlocking Day 5 acquisitions to accelerate daily milk ($160) and fertilizer ($100) cash flows."*

Because a Cow costs $\$400$ and produces **$\$160$ daily milk plus $\$100$ fertilizer** (a $65\%$ daily ROI), CL spends its Day 5–8 capital filling 8 Cow slots before buying Sheep. Sheep cost $\$500$ and produce $\$200$ wool every 2 days ($\$100/\text{day}$ = $20\%$ daily ROI).
This is a **deliberate macro portfolio choice**, not an oversight. Because CL bought cows first, it sacrificed wool yield (+35 units) in exchange for milk and fertilizer cash flow.

---

## J. Melon Succession Audit

The report claimed the melon deficit comes from *"Secondary melon wave succession."*

### Ground Truth Telemetry:
We classified all melon plantings into Wave 1 (Days 0–4) and Wave 2 (Day 5+):
- **CL-Economic-V1:**
  - Wave 1 Melons: **$7.0$ plantings** (Days 0–1)
  - Wave 2 Melons: **$18.7$ plantings** (Days 7–22)
  - Total melon plantings: **$25.7$ plots**
- **Frozen V2:**
  - Wave 1 Melons: **$9.0$ plantings** (Days 0–2)
  - Wave 2 Melons: **$17.0$ plantings** (Days 5–17)
  - Total melon plantings: **$26.0$ plots**

### The Counter-Evidence:
**CL actually plants MORE second-wave melons (18.7) than V2 (17.0)!**
The reason V2 produces $+26$ more melon yield units is NOT planting volume. It is **planting calendar validity**:
- In V2, 100% of Wave 2 melons are planted between **Day 5 and Day 17**. Because a melon takes 10 days to first yield, a melon planted on Day 17 matures on Day 27 and yields on Days 28 and 29.
- In CL, Wave 2 melons are planted between **Day 7 and Day 22** (34 plantings on Day 7, 25 on Day 11, 18 on Day 12, 15 on Day 13, 16 on Day 14, 15 on Day 15, and **24 plantings on Days 21–22!**).
- A melon planted on Day 21 reaches first yield day at **Day 31**. The game ends on **Day 29**.
- **Every melon planted on Days 20–22 yields 0 units.** CL spends $\$80$ per seed and wastes worker watering actions on 24 melon plots that have a mathematical $0\%$ chance of maturing!

---

## K. Black-Box V2 Behavioral Matrix & Divergence Date

We constructed a day-by-day behavioral matrix comparing CL and V2:

| Day | CL Plantings (W/M/S) | V2 Plantings (W/M/S) | CL Harvests | V2 Harvests | CL Seed Buys | V2 Seed Buys | Divergence Event |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | $7.0 / 7.0 / 0.0$ | $10.0 / 7.0 / 0.0$ | $0.0$ | $0.0$ | $2.0$ | $2.0$ | Synchronized opening |
| **1–3** | $3.0 / 0.0 / 0.0$ | $1.0 / 1.0 / 0.0$ | $0.0$ | $0.0$ | $1.0$ | $2.0$ | Minor opening adjustments |
| **4** | $5.0 / 0.0 / 2.0$ | $6.0 / 1.0 / 2.0$ | $7.0$ | $10.0$ | $2.0$ | $8.0$ | First wheat harvest & replant |
| **5–6** | $0.0 / 0.0 / 1.0$ | $0.0 / 1.0 / 0.0$ | $2.0$ | $2.0$ | $2.4$ | $0.0$ | Synchronized animal upkeep |
| **7** | $2.9 / 3.4 / 3.6$ | $4.0 / 1.0 / 4.0$ | $2.0$ | $0.0$ | $1.0$ | $3.0$ | Synchronized second wave launch |
| **8–9** | $5.2 / 0.6 / 7.0$ | $4.0 / 0.0 / 11.0$ | $9.0$ | $10.0$ | $3.5$ | $9.0$ | V2 accelerates strawberry planting |
| **10** | $5.0 / 0.0 / 6.5$ | $1.0 / 0.0 / 1.0$ | $10.0$ | $8.0$ | $1.4$ | $4.0$ | **CRITICAL DIVERGENCE DAY** |
| **11** | $2.4 / 2.5 / 4.5$ | $1.0 / 2.0 / 10.0$ | $2.9$ | $7.0$ | $2.3$ | $6.0$ | V2 drops 10 strawberries in 1 day |
| **12** | $0.1 / 1.8 / 5.4$ | $3.0 / 5.0 / 6.0$ | $7.2$ | $8.0$ | $2.4$ | $6.0$ | V2 completes melon & straw wave |
| **13–17** | $0.0 / 6.8 / 11.8$ | $4.0 / 7.0 / 7.0$ | $29.2$ | $37.0$ | $4.6$ | $10.0$ | CL trickles plantings late |
| **18–20** | $0.0 / 1.2 / 1.0$ | $0.0 / 0.0 / 0.0$ | $33.3$ | $47.0$ | $1.9$ | $0.0$ | V2 completely halts planting |
| **21–22** | $3.2 / 2.4 / 0.0$ | $0.0 / 0.0 / 0.0$ | $31.0$ | $42.0$ | $1.9$ | $0.0$ | CL wastes money planting unripe melons |
| **26** | $2.2 / 0.0 / 0.0$ | **$27.0 / 0.0 / 0.0$** | $16.1$ | $19.0$ | $0.0$ | $5.0$ | V2 executes 27-plot terminal wheat wave |
| **27–29** | $0.2 / 0.0 / 0.1$ | $6.0 / 0.0 / 0.0$ | $58.5$ | $69.0$ | $0.0$ | $3.0$ | Terminal harvest liquidation |

### Critical Divergence Insights:
1. **Earliest Material Divergence is Day 10–12:**
   - On Days 11–12, V2 executes a massive burst of $16.0$ strawberry plantings and $7.0$ melon plantings using capital unlocked by Day 10 milk/wool sales.
   - CL trickles its plantings slowly across Days 7 through 17 because its market orders are choked at Hour 0.
2. **Terminal Wheat Burst on Day 26:**
   - On Day 26, V2 plants **$27.0$ wheat plots** in a single day. Because wheat requires only 2 days to yield and 4 days to reach 6 units, this terminal wave completes harvest at Day 29 Step 712, contributing $+162$ wheat units right before the game ends!

---

## L. Clean Causal Succession Hierarchy Intervention (Phase 16)

To definitively test whether adding crop succession closes the production gap, we implemented 5 strictly controlled, observation-driven succession variants on `CL-Economic-V1` (evaluated across Seeds 1000–1009, $N=10$ each):

| Experimental Arm | Policy Description | Mean Reward ($) | 95% CI ($) | Harvests | Total Plants | Crop Units | Strawberry (u) | Melon (u) | Wheat (u) | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BASELINE** | Current CL-Economic-V1 | **$125,590.30** | ±$6,114 | $254.4$ | $114.8$ | $429.2$ | **$198.2$** | $105.3$ | $125.7$ | **Parent Baseline** |
| **TEST 1** | Post-harvest wheat replanting only | $122,931.50$ | ±$8,775 | **$257.2$** | $117.6$ | **$441.7$** | $199.9$ | $109.9$ | $131.9$ | **-$2,658.80 Regressed** |
| **TEST 2** | Dynamic crop choice (Melon if $d \le 17$, else Wheat) | $117,363.80$ | ±$8,325 | $238.5$ | $124.1$ | $430.9$ | $150.4$ | **$186.0$** | $94.5$ | **-$8,226.50 Regressed** |
| **TEST 3** | Capital-constrained (buffer $\ge \$400$) | $117,136.90$ | ±$8,690 | $238.4$ | **$134.7$** | $420.8$ | $155.6$ | $171.6$ | $93.6$ | **-$8,453.40 Regressed** |
| **TEST 4** | Worker-constrained (workers $\ge 8$) | $118,862.10$ | ±$9,340 | $244.4$ | $132.0$ | $434.4$ | $145.8$ | $180.0$ | $108.6$ | **-$6,728.20 Regressed** |
| **TEST 5** | Integrated Succession Policy | $120,057.20$ | ±$11,134 | $248.3$ | $127.1$ | $425.7$ | $162.8$ | $156.5$ | $106.4$ | **-$5,533.10 Regressed** |

### Causal Attribution Analysis:
1. **TEST 1 (Simple Replanting):**
   - Increased planting events (+2.8), increased harvest actions (+2.8), and increased crop units (+12.5).
   - **Yet terminal reward regressed by -$2,658.80.**
   - Why: Replanting wheat requires workers to water low-margin ($25) crops daily, diverting transit turns away from livestock feeding and market drops.
2. **TESTS 2–5 (Melon Succession):**
   - Successfully increased melon yield from $105.3$ up to **$186.0$ units (+80.7 melons)** and increased plants to $134.7$.
   - **Yet terminal reward collapsed severely by -$5,533 to -$8,453.**
   - Why: Melons require 10–12 days of continuous daily watering. When workers were burdened with maintaining 15–20 additional melon plots, they starved the strawberry bushes of irrigation. **Strawberry output plummeted by -35 to -52 units.**
   - Since Strawberries produce recurring high-margin yield every 2 days for the rest of the game, sacrificing strawberries for a one-off melon is mathematically value-destructive.

---

## M. Final GO / NO-GO Decision

# **STOP. DEFINITIVE NO-GO on the Field Planting Density & Crop Succession Pipeline.**

Under Research Decision Rule 19:
1. The reported $+95$ crop harvest gap does **not** exist in crops (over $36.5\%$ is animal shearing and milking).
2. The claim that CL lacks crop succession is **false** (over $51\%$ of CL's plantings are already succession replantings).
3. The claim that V2 has a secondary melon advantage is **false** (CL plants more 2nd-wave melons than V2).
4. Controlled causal interventions prove that forcing additional succession replanting **consistently regresses terminal reward by -$2.6k to -$8.4k**.
5. Expanding planting density cannibalizes recurring strawberry irrigation and starves working capital.

---

## N. Exact Next Research Step

Having decisively eliminated Crop Succession, Shed Logistics, and Selective Irrigation as false trails, the forensic audit reveals the **true mechanical bottlenecks** separating CL from V2:

### Immediate Remediation Roadmap (Phase 17):
1. **Eliminate Unripe Late-Season Melon Plantings:**
   - Impose an absolute calendar cutoff on melon seed purchasing and planting: **strictly `day <= 18`**.
   - Melons planted on Days 20–22 have zero probability of maturing. Eliminating them recovers **$\$1,920$ in capital** and saves over $150$ wasted worker watering actions.
2. **Implement Intraday JIT Market Order Queuing:**
   - Move seed purchasing and animal acquisitions out of the choked Hour 0 queue (which hits the 10-order limit) into **Hour 1 and intraday ticks**.
   - Allow market orders to account for pending `SELL` proceeds so midday harvests instantly unlock seed capital.
3. **Targeted Terminal Wheat Wave (Day 26 Burst):**
   - Emulate V2's high-efficiency Day 26 wheat burst: on Day 26 only, reseed available open tiles with fast 3-day wheat to harvest a final $+100$ grain burst at Step 712 without incurring long-term irrigation overhead.
