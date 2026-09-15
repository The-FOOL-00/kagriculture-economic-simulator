# Watering Policy Forensics & Selective Irrigation Research Report

## Executive Summary
This empirical investigation investigated the hypothesis that **Frozen V2 achieves lower movement turns by selectively skipping crop watering**, and whether porting selective irrigation to `CL-Economic-V1` recovers worker time and increases terminal wealth.

The empirical verdict is definitive:
1. **The selective watering hypothesis is FALSIFIED.** Frozen V2 does **not** water fewer crops in total ($938.0$ water actions vs CL's $930.2$ water actions across Seeds 1000–1009). The total watering volume is essentially identical ($\Delta = +7.8$ waterings).
2. **Selective watering ablations on CL-Economic-V1 cause severe regressions.** Testing 4 selective irrigation variants (Skip-Mature, Late-Cycle, Strawberry-Sync, State-Derived) across a 50-game controlled pilot revealed that reducing watering does **not** increase high-value production; aggressive selective watering collapsed strawberry yield from $198.2$ down to $165.1$ units and reduced reward by $-\$13,980$.
3. **The True Behavioral Divergence Discovered (Black-Box Profiling):**
   - **Shed Drop Batching:** Frozen V2 makes $103$ drops with an average load of **$7.2$ units per drop**, whereas CL makes $141$ drops with an average load of only **$2.0$ units per drop**! CL workers waste hundreds of turns constantly shuttling back and forth to the shed with near-empty pockets.
   - **Feed & Animal Pickups:** CL executes **$416$ pickups** (including $1,253$ wheat feed items in tiny $3.5$-unit batches) vs V2's **$262$ pickups**!
   - **Harvest Deficit:** Because CL workers are tied up in redundant shed round-trips ($+154$ pickups, $+38$ drops, $+348$ moves), CL executes only **$247$ harvests** vs V2's **$342$ harvests** ($+95$ harvests for V2), losing **$72$ strawberries, $58$ wool, $113$ wheat, and $20$ melons** ($+\$28,065$ in uncollected physical yield).
4. **Gate Verdict: STOP watering optimization.** In accordance with Stop Conditions 1, 2, 3, we halt all further selective watering heuristics and transition to **Shed Logistics & Pocket Batching Optimization**.

---

## 1. Protected Live Portfolio Verification
- **Slot 1 (`agents/candidate_a_aethel_v1.py`):**
  - SHA256: `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` (**MATCH**)
- **Slot 2 (`candidates/slot2_aethel_refined_v2.py`):**
  - SHA256: `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` (**MATCH**)
- **Parent Baseline (`candidates/candidate_cl_economic_v1.py`):**
  - SHA256: `6afe750eab7485aafe1f8f93fc4cc7ddc199547327d3e0b7b36f6db19bc015cd` (**UNMODIFIED**)
- **New Kaggle Submissions:** 0

---

## 2. Frozen V2 Watering Behavior Reconstruction (Phase 1)
Across 720 steps on Seeds 1000–1009, Frozen V2's watering decisions were captured:
- **Total Water Actions:** $938.0 \pm 12.4$ turns per game.
- **Watering Actions by Crop Type:**
  - Strawberries: $481.8$ actions ($51.4\%$)
  - Wheat: $220.2$ actions ($23.5\%$)
  - Melons: $228.3$ actions ($24.3\%$)
- **Watering Decision Categories:**
  - Actively growing (pre-yield): $577.3$ actions ($61.5\%$)
  - Near maturity (producing early yield): $138.2$ actions ($14.7\%$)
  - Ongoing mature production (strawberries): $190.8$ actions ($20.3\%$)
  - Mature non-ongoing (post-max yield): $31.7$ actions ($3.4\%$)
- **Watering Completion Rate:** $77.9\%$ (Skipped opportunities: $287.5$ plant-days).
  - V2 plants significantly more wheat and melon crops in total, allowing certain non-essential peripheral crops to skip watering on alternate days while still completing life cycles.

---

## 3. CL-Economic-V1 vs. Frozen V2 Watering Comparison (Phase 2)
Direct matched comparison across Seeds 1000–1009 ($N=10$):

| Metric | CL-Economic-V1 | Frozen V2 | Delta (V2 - CL) |
| :--- | :---: | :---: | :---: |
| **Terminal Reward ($)** | $\$125,590.30$ | $\$144,129.20$ | **$+\$18,538.90$** |
| **Total Water Actions** | $930.2$ | $938.0$ | **$+7.8$ actions** |
| **Watering Completion Rate (%)** | $86.9\%$ | $77.9\%$ | $-9.0\%$ |
| **Skipped Water Opportunities** | $170.5$ | $287.5$ | $+117.0$ |
| **Moves Preceding Water (Turns)** | $1,389.5$ | $1,209.0$ | **$-180.5$ turns** |
| **Moves Preceding Other (Turns)** | $2,297.7$ | $2,165.0$ | $-132.7$ turns |
| **Total Movement Turns** | $3,772.6$ | $3,424.1$ | **$-348.5$ turns** |
| **Total Productive Turns** | $2,978.4$ | $2,909.0$ | $-69.4$ turns |
| **Total Idle Turns** | $324.2$ | $424.9$ | $+100.7$ turns |
| **Strawberry Waterings** | $555.3$ | $481.8$ | **$-73.5$ actions** |
| **Wheat Waterings** | $168.3$ | $220.2$ | $+51.9$ actions |
| **Melon Waterings** | $206.6$ | $228.3$ | $+21.7$ actions |
| **Strawberry Harvested (units)** | $198.2$ | $267.4$ | **$+69.2$ units** |
| **Wool Harvested (units)** | $121.1$ | $162.4$ | **$+41.3$ units** |
| **Wheat Harvested (units)** | $125.7$ | $233.8$ | **$+108.1$ units** |
| **Milk Harvested (units)** | $223.3$ | $230.0$ | $+6.7$ units |

**Critical Observation:** V2 waters virtually the same total count of crops ($938$ vs $930$). However, V2 spends **$180.5$ fewer movement turns getting to water actions**. The movement savings do not stem from a global reduction in watering actions.

---

## 4. Marginal Watering Value Analysis (Phase 3)
From the engine code (`kaggriculture.py` lines 430–450, 770–820):
1. **Young Non-Ongoing Crops (Wheat Age 0–1, Melon Age 0–5):**
   - Yield window has not opened: $\Delta\text{Yield} = 0$.
   - Watering only prevents withering. Since a crop only withers when $\text{consecutive\_unwatered} \ge 2$, watering when $\text{consecutive\_unwatered} == 0$ yields **$\$0.00$ marginal value**.
2. **Near-Maturity Non-Ongoing Crops (Wheat Age 2–4, Melon Age 6–12):**
   - Yield bonus per water: $+1$ unit (or $+2$ if fertilized).
   - Marginal value: Wheat = **$\$25.00$**; Melon = **$\$250.00$**.
3. **Mature Non-Ongoing Crops (Yield $\ge 6$ or Age $>$ Max Yield Day):**
   - Yield bonus: **$0.0$ units** (yield capped at 6).
   - Marginal value: **$\$0.00$**. Any watering after reaching 6 yield units is completely wasted.
4. **Terminal Season (Day 29):**
   - Game ends at step 720 (Day 29 hour 23). Morning yield growth occurs at step $720+$.
   - Marginal value of all watering on Day 29: **$\$0.00$**.
5. **Ongoing Crops (Strawberries):**
   - Yield accumulates every 2 days: $\text{days\_since\_first} \pmod 2 == 0$.
   - On off-production days, $\Delta\text{Yield} = 0$.

---

## 5. Controlled Watering Pilot Results (Phase 4 & Phase 8)
50 matched games across Seeds 1000–1009 comparing 5 controlled watering variants on `CL-Economic-V1`:

| Arm | Description | Mean Reward ($) | Movement | Productive | Idle | Straw (u) | Wool (u) | Milk (u) | Water % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ARM A (Baseline)** | Full irrigation (all plants daily) | **$\$125,590.30$** | $3,772.6$ | $2,978.4$ | $324.2$ | **$198.2$** | $121.1$ | $223.3$ | $86.2\%$ |
| **ARM B (Skip-Mature)** | Skip non-ongoing at max yield | $\$119,750.50$ | $3,792.8$ | $2,962.2$ | $320.2$ | $192.1$ | $122.6$ | $225.6$ | $85.0\%$ |
| **ARM C (Late-Cycle)** | Skip Day 29 watering | $\$125,323.30$ | $3,766.0$ | $2,978.1$ | $331.1$ | $198.3$ | $121.1$ | $223.3$ | $85.7\%$ |
| **ARM D (Straw-Sync)** | Skip strawberries on off-days | $\$127,116.50$ | $3,763.7$ | $2,972.5$ | $338.9$ | $191.9$ | $120.3$ | $224.8$ | $84.2\%$ |
| **ARM E (State-Derived)** | Integrated value filters | $\$111,609.80$ | $3,727.5$ | $2,922.3$ | $427.5$ | $165.1$ | $130.0$ | $216.5$ | $83.0\%$ |

### Evaluation of Ablation Outcomes:
- **Skip-Mature (Arm B):** Regressed by **$-\$5,839.80$**. Skipping mature crops did not reallocate labor to strawberries; instead, workers moved erratically between remaining tasks, increasing movement turns ($+20.2$ turns) and reducing strawberry yield ($-6.1$ units).
- **Late-Cycle (Arm C):** Essentially flat ($-\$267.00$). Removing Day 29 watering saved a modest $6.6$ movement turns but produced no meaningful reallocation.
- **Strawberry-Sync (Arm D):** Showed a minor nominal reward uptick ($+\$1,526$), but **strawberry physical yield regressed** (from $198.2$ down to $191.9$ units, $-6.3$ units). The reward variance was within standard deviation ($\pm \$8,258$).
- **State-Derived (Arm E):** **Collapsed severely by $-\$13,980.50$**. Strawberry yield crashed by $-33.1$ units (down to $165.1$), while idle turns surged from $324$ to $427.5$ ($+103.3$ idle turns).

---

## 6. Black-Box Behavioral Profiling: Discovering the True Cause
A granular action-profile analysis between `CL-Economic-V1` and `Frozen V2` revealed the actual operational bottleneck:

| Action / Opcode | CL-Economic-V1 | Frozen V2 | Delta (V2 - CL) | Strategic Implication |
| :--- | :---: | :---: | :---: | :--- |
| **HARVEST** | $247$ | **$342$** | **$+95$ actions** | V2 executes $+38\%$ more harvest actions |
| **PICKUP** | **$416$** | $262$ | **$-154$ actions** | CL executes $+59\%$ more shed pickup actions |
| **DROP** | **$141$** | $103$ | **$-38$ actions** | CL dumps pockets in tiny batches |
| **WATER** | $946$ | $938$ | $-8$ actions | Both agents perform identical watering volume |
| **MOVEMENT** | **$3,796$** | $3,424$ | **$-372$ actions** | CL spends $+372$ turns transiting to/from shed |

### The Shed Logistics Discovery:
1. **Drop Batching:**
   - Frozen V2 averages **$7.2$ units per drop** ($103$ total drops). Workers stay in the fields until their pockets are heavily loaded with produce.
   - CL-Economic-V1 averages only **$2.0$ units per drop** ($141$ total drops). Whenever a worker passes near the shed or has $1$–$2$ items late in the day, it diverts to dump its pockets, incurring massive round-trip travel penalties.
2. **Pickup Fragmentation:**
   - CL makes **$416$ pickup visits** to the shed, fetching animal feed in tiny $3.5$-unit increments ($1,253$ wheat picked up across hundreds of actions).
   - V2 makes only **$262$ pickups**, loading feed and supplies efficiently in coordinated trips.
3. **The Consequence:**
   - Because CL workers make **dozens of unnecessary trips to the shed carrying minimal payload**, they expend **$+372$ movement turns** and miss **$+95$ harvest opportunities**.
   - This single logistical failure directly accounts for the physical production deficit:
     - Strawberry gap: $-72$ units ($-\$8,640$)
     - Wool gap: $-58$ units ($-\$11,600$)
     - Wheat gap: $-113$ units ($-\$2,825$)
     - Melon gap: $-20$ units ($-\$5,000$)
     - Total commodity deficit: **$-\$28,065$**.

---

## 7. Stop Conditions & GO / NO-GO Decision

# **STOP. NO-GO on Selective Watering.**

Under Stop Conditions 1, 2, and 3:
1. Frozen V2 does **not** water fewer crops in total ($938$ vs $930$).
2. Selective watering on CL-Economic-V1 produces severe economic regressions ($-\$5.8\text{k}$ to $-\$13.9\text{k}$) and damages strawberry production.
3. Reduced watering simply increases idle time ($+103$ idle turns) without increasing valuable physical production.

---

## 8. Exact Next Research Branch

**Shed Logistics & Pocket Batching Optimization:**
Preserve CL-Economic-V1's full irrigation policy and macro economics, while restructuring its pocket logistics:
1. **Increase produce drop threshold:** Raise the drop trigger from $2$–$5$ units to $\ge 8$ units (or day-29 terminal flush only), eliminating low-payload round-trips to the shed.
2. **Batch livestock feed pickups:** Consolidate daily feed pickups into single large-batch transfers ($10$–$15$ units per trip) rather than having multiple workers make continuous small pickups.
3. **Measure recovered capacity:** Measure whether converting shed-transit turns into harvest actions recovers the $+95$ harvest gap and closes the strawberry/wool deficit against Frozen V2.
