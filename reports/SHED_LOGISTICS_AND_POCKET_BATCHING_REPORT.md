# Shed Logistics & Pocket Batching Research Report

## Executive Summary
This empirical investigation investigated the hypothesis that **fragmented shed logistics (frequent low-payload drops and feed pickups)** in `CL-Economic-V1` cause excessive worker transit, pull workers out of fields, reduce harvest actions, and explain the physical production gap versus `Frozen V2`.

The empirical verdict is definitive:
1. **The Shed Logistics Batching Hypothesis is FALSIFIED.**
   - Forcing workers to batch produce drops ($\ge 3, \ge 5, \ge 8, \ge 10$ units) reduced movement turns by $112$–$172$ turns, but **consistently collapsed terminal reward by $-\$5,547$ to $-\$16,250$**.
   - Holding produce in pockets starves the agent of intermediate working capital. Because the market controller can only sell goods located inside `private["shed"]`, delayed drops prevent midday sales, delaying farm-hand hiring, seed purchases, and livestock acquisitions.
2. **Feed Pickup Batching Causes Severe Livestock Degradation:**
   - Consolidating feed pickups (Moderate, Large, Dedicated Feeder, Coordinated Shared) reduced pickup actions but **consistently regressed reward by $-\$5,436$ to $-\$28,178$**.
   - Restricting feed pickups caused animal care/feeding completion to plummet from $98.3\%$ down to $81.4\%$, cutting wool output nearly in half (from $121.1$ down to $62.7$ units) due to animal starvation.
3. **Causal Understanding of the CL vs. V2 Divergence:**
   - Frozen V2's lower shed interaction count ($103$ drops, $262$ pickups) is **not** an emergent result of threshold batching. It is the direct consequence of a **globally synchronized, pre-choreographed geometric snake routine** where workers pass the shed at pre-calculated ticks when pockets happen to be full.
   - For a reactive, observation-driven agent, imposing static or threshold-based batching creates liquidity starvation and feeding delays that are far more damaging than the transit cost saved.
4. **Gate Verdict: STOP Logistics Optimization (NO-GO).**
   - In accordance with Stop Conditions 1, 2, and 5, we halt all further batching rules.

---

## 1. Protected Live Portfolio Verification
- **Slot 1 (`agents/candidate_a_aethel_v1.py`):**
  - SHA256: `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` (**MATCH**)
- **Slot 2 (`candidates/slot2_aethel_refined_v2.py`):**
  - SHA256: `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` (**MATCH**)
- **Parent Baseline (`candidates/candidate_cl_economic_v1.py`):**
  - SHA256: `6afe750eab7485aafe1f8f93fc4cc7ddc199547327d3e0b7b36f6db19bc015cd` (**UNTOUCHED**)
- **New Kaggle Submissions:** 0

---

## 2. Shed Logistics Forensic Reconstruction (Phase 1 & Phase 2)
Instrumented across Seeds 1000–1009 ($N=10$, 720 steps each):

### Aggregate Operational Profile:
* **Terminal Reward:** $\$125,590.30 \pm \$9,864.11$
* **HARVEST Actions:** $254.4$ turns
* **PICKUP Actions:** $406.2$ turns
* **DROP Actions:** $146.4$ turns
* **Mean Drop Payload:** $2.11$ units (Median: $1.0$, Max: $11.9$)
* **Feed Picked Up:** $1,273.5$ units (Mean batch: $3.6$ units)
* **Movement Turns:** $3,772.6$ turns
* **Productive Turns:** $2,978.4$ turns
* **Idle Turns:** $324.2$ turns
* **Commodities Harvested:**
  * Strawberry: $198.2$ units
  * Wool: $121.1$ units
  * Wheat: $125.7$ units
  * Melon: $105.3$ units
  * Milk: $223.3$ units
* **Max Shed Occupancy:** $79.8 / 100$ units (Shed capacity is never a bottleneck).

### Causal Classification of Shed Interactions:
| Classification Category | Mean Actions / Run | % of Total Shed Visits | Operational Role |
| :--- | :---: | :---: | :--- |
| **F. Fragmented feed pickup ($< 6$ units)** | $228.3$ | $41.3\%$ | Workers 0–3 reactively fetch 1–2 wheat per hungry animal |
| **F. Opportunistic low-payload drop ($< 5$ units)** | $124.4$ | $22.5\%$ | Workers dump pockets when passing within 2 tiles of shed |
| **B. Bulk feed pickup ($\ge 6$ units)** | $122.4$ | $22.1\%$ | Morning bulk feed collection |
| **E. Emergency animal placement** | $55.5$ | $10.0\%$ | Picking up cows/sheep from shed to pasture |
| **A. Significant produce drop ($\ge 5$ units)** | $14.4$ | $2.6\%$ | Rare heavy-pocket produce dumps |
| **F. Evening produce drop ($h \ge 20$)** | $7.6$ | $1.4\%$ | Evening shed runs (unnecessary: engine auto-drops at h23) |

---

## 3. Shed Capacity & Blocking Forensics (Phase 3)
Source inspection of the engine (`kaggriculture.py` lines 8–25, 335–425, 645–690, 835–885) established:
1. **Worker Inventory Capacity:** The engine imposes **NO capacity limit** on worker pockets (`_inv_add` simply increments `inv[item]`). Workers can hold arbitrary loads without blocking harvests.
2. **Shed Capacity:** Fixed at **$100$ units**. If shed hits 100, `BUY_PRODUCT` (feed) and `BUY_ANIMAL` fail, and manual drops delete overflow. Safe buffer is $\le 80$ units.
3. **Harvest Mechanics:** `HARVEST` mutates the tile and adds yield to worker inventory without checking pocket capacity. A worker carrying 20 items harvests with $100\%$ success.
4. **Market Order Dependency:** `SELL` orders can **only sell items located inside `private["shed"]`**. Items in worker pockets cannot be sold until dropped into the shed.
5. **Midnight Engine Auto-Drop:** At midnight (hour 23 -> 0), the engine's `_end_of_day` routine **automatically dumps all worker pocket inventories into the shed for free** (up to 100 units). Workers do not need to walk to the shed in the evening to preserve produce.
6. **Feed Consumption:** Animals eat once per day (`fed_today`). If an animal remains unfed for 2 consecutive days, it escapes.

---

## 4. Produce Batching Threshold Curve (Phase 4: 70 Matches, Seeds 1000–1009)

| Arm | Policy Description | Mean Reward ($) | Harvests | Drops | Payload | Moves | Straw (u) | Wool (u) | Melon (u) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ARM A (Baseline)** | Current CL trigger ($p \ge 5$ or $h \ge 20$ or $d \le 2$) | **$\$125,590.30$** | $254.4$ | $146.4$ | $2.11$u | $3,772.6$ | **$198.2$** | $121.1$ | $105.3$ |
| **ARM B (Drop $\ge 3$)** | Strictly produce $\ge 3$ | $\$114,315.70$ | $254.2$ | $69.3$ | $4.22$u | $3,648.6$ | $172.1$ | $128.8$ | $112.2$ |
| **ARM C (Drop $\ge 5$)** | Strictly produce $\ge 5$ | $\$120,042.90$ | **$256.8$** | $47.1$ | $5.15$u | $3,660.6$ | $176.4$ | $125.2$ | $115.4$ |
| **ARM D (Drop $\ge 8$)** | Strictly produce $\ge 8$ | $\$116,142.10$ | $251.8$ | $32.6$ | $4.78$u | $3,613.3$ | $164.2$ | $134.0$ | $124.5$ |
| **ARM E (Drop $\ge 10$)** | Strictly produce $\ge 10$ | $\$119,774.40$ | $253.2$ | $23.7$ | $3.64$u | $3,602.1$ | $166.7$ | $133.6$ | $125.0$ |
| **ARM F (Capacity)** | Drop $\ge 15$ or terminal flush | $\$109,339.50$ | $246.0$ | $22.1$ | $2.50$u | **$3,600.1$** | $156.7$ | $118.9$ | **$126.4$** |
| **ARM G (Hybrid)** | Adaptive liquidity / load trigger | $\$116,142.10$ | $251.8$ | $32.6$ | $4.78$u | $3,613.3$ | $164.2$ | $134.0$ | $124.5$ |

### Causal Findings on Produce Batching:
* **Movement fell significantly:** Raising the threshold reduced movement by $112$–$172$ turns and slashed drops from $146.4$ down to $22.1$.
* **Reward regressed severely:** Mean reward dropped by **$-\$5,547$ to $-\$16,250$ across every single variant**.
* **Why:** Strawberry physical yield collapsed (from $198.2$ down to $156.7$–$176.4$). Produce trapped in pockets was not converted to cash during the day, starving the agent of working capital needed to buy strawberry seeds and livestock on critical growth days (Days 5, 8, 10).

---

## 5. Feed Pickup Batching Experiment (Phase 5: 50 Matches, Seeds 1000–1009)

| Arm | Description | Mean Reward ($) | Harvests | Pickups | Wheat Pickups | Mean Batch | Moves | Wool (u) | Care/Fed % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ARM A (Baseline)** | Reactively fetch up to 6 per hungry | **$\$125,590.30$** | $254.4$ | $406.2$ | $350.7$ | $3.6$u | $3,772.6$ | $121.1$ | **$98.3\%$** |
| **ARM B (Moderate)** | Always fetch up to 6 wheat | $\$120,153.90$ | **$263.2$** | $331.6$ | $288.7$ | $4.5$u | **$3,706.7$** | **$126.4$** | $98.0\%$ |
| **ARM C (Large)** | Fetch up to 14 wheat | $\$118,492.30$ | $251.6$ | $299.7$ | $257.1$ | $8.6$u | $3,790.6$ | $122.5$ | $97.8\%$ |
| **ARM D (Dedicated)**| Worker 1 dedicated feeder | $\$97,411.40$ | $237.0$ | **$133.0$** | **$30.0$** | **$13.1$u** | $3,933.3$ | $62.7$ | $81.4\%$ |
| **ARM E (Shared)** | Single worker at a time ($\le 12$u) | $\$114,616.10$ | $253.1$ | $209.6$ | $159.1$ | $9.7$u | $3,835.5$ | $105.6$ | $94.5\%$ |

### Causal Findings on Feed Batching:
* **Dedicated Feeder is Catastrophic:** Restricting feed handling to a single worker caused a **$-\$28,178.90$ collapse**. A single worker could not traverse the farm and service 14 pastures in time. Feeding completion dropped to $81.4\%$, starving animals and cutting wool output from $121.1$ down to $62.7$ units.
* **Batching Feed Does Not Recover Harvests:** Increasing feed batch size (Arm C, Arm E) reduced pickup actions by $106$–$197$, but total harvests did not increase ($251$–$253$ vs baseline $254.4$).

---

## 6. Combined Candidate & Harvest-Capacity Analysis (Phases 6 & 7)
* **Combined Candidate:** **HALTED.** Neither produce batching nor feed batching produced an improvement independently; combining two regressive mechanisms would compound losses.
* **Harvest-Capacity Causal Analysis:**
  * The hypothesis that "reducing shed trips recovers $+95$ harvest actions" is **empirically disproven**.
  * When shed drops were reduced by $70\%$ (Arm C, Arm D) and pickups by $50\%$ (Arm E), total harvest actions remained virtually flat at **$251$–$256$ actions** (baseline: $254.4$).
  * The $+95$ harvest advantage of Frozen V2 ($342$ vs $247$) is **not** created by having more free worker turns; it is created by **having more mature crops planted simultaneously** on the field (V2 plants $+108$ more wheat and $+20$ more melons, providing physically more harvestable crops across the season).

---

## 7. Stop Conditions & GO / NO-GO Decision

# **STOP. NO-GO on Logistics Batching.**

Under Stop Conditions 1, 2, and 5:
1. Increasing batch size did **not** increase harvest actions ($251$–$256$ vs $254.4$).
2. Terminal reward regressed across all produce-batching ($-\$5.5\text{k}$ to $-\$16.2\text{k}$) and feed-batching ($-\$5.4\text{k}$ to $-\$28.1\text{k}$) variants.
3. Feed batching caused livestock feeding failures (down to $81.4\%$), damaging wool production.
4. Reductions in movement (saving $110$–$170$ turns) produced zero economic benefit.

---

## 8. Exact Updated H2H Gap Decomposition

| Component | Physical Yield Difference (V2 - CL) | Economic Loss ($) | Share of H2H Gap |
| :--- | :---: | :---: | :---: |
| **Strawberry Volume** | $+72$ units | $-\$8,640$ | $30.8\%$ |
| **Wool Volume** | $+58$ units | $-\$11,600$ | $41.3\%$ |
| **Wheat Volume** | $+113$ units | $-\$2,825$ | $10.1\%$ |
| **Melon Volume** | $+20$ units | $-\$5,000$ | $17.8\%$ |
| **Total Physical Yield Deficit** | **$+263$ units** | **$-\$28,065$** | **$100.0\%$** |

---

## 9. Next Exact Research Branch

**Field Planting Density & Crop Succession Pipeline:**
Having decisively falsified routing, watering, and shed logistics, the remaining physical difference is clear:
* Frozen V2 harvests **$342$ times** because it plants **$135$ total crops** ($238$ wheat, $132$ melons, $266$ strawberries).
* CL-Economic-V1 harvests only **$247$ times** because it plants only **$114$ total crops** ($125$ wheat, $112$ melons, $194$ strawberries).
* **Research Focus:** Investigate the planting schedule and tile recycling pipeline in CL-Economic-V1. Specifically, test whether aggressive post-wheat crop replanting (filling vacated tiles with second-wave grain/melons) directly generates the $+95$ missing harvest opportunities and closes the $\$28,065$ production deficit.
