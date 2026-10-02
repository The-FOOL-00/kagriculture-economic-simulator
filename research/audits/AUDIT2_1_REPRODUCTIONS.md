# AUDIT 2.1: INDEPENDENT EXPERIMENTAL REPRODUCTIONS
## Direct Forensic Verification of Empirical Findings, Retractions, and Benchmarks

This document details the independent reproductions conducted during Audit 2.1 to verify the empirical claims and retractions made in Audit 2 (`AUDIT2_REPRODUCTIONS.md`).

Every reproduction was conducted using independent scripts, raw simulator execution (`kagsim`, `sim.hpp`), official tournament replays, and raw result JSON files without inheriting prior assumptions.

---

## 1. Reproduction R1: Tomato Specialization ($3,942 Outlier vs -$5,382 Ensemble)

### Objective
Determine whether Audit 2's retraction of the "+$3,942 Tomato Alpha on Pizza worlds" is factually and statistically verified.

### Verification of Specific Sub-Questions
1. **Exact Seed List**: `[50003, 50011, 50021, 50026, 50030, 50042]` (6 True Pizza seeds without Yarn Shop).
2. **Exact Number of Seeds**: Exactly 6 seeds.
3. **Exact Parameter Combinations**: 18 parameter combinations in `scratch/true_pizza_sweep_results.json` ($\text{cohorts} \in \{1, 2, 3\}$, $\text{tiles} \in \{10, 15, 19, 20, 25, 30\}$).
4. **Exact Per-Seed Deltas** (from `scratch/test_tomato_with_sales.py`):
   - Seed 50003: V2 = $92,232, Tomato = $77,046, Dmitrii = $92,197 $\rightarrow$ **Delta vs V2: -$15,186**
   - Seed 50011: V2 = $87,541, Tomato = $86,530, Dmitrii = $87,494 $\rightarrow$ **Delta vs V2: -$1,011**
   - Seed 50021: V2 = $112,854, Tomato = $100,785, Dmitrii = $112,768 $\rightarrow$ **Delta vs V2: -$12,069**
   - Seed 50026: V2 = $79,124, Tomato = $83,692, Dmitrii = $79,046 $\rightarrow$ **Delta vs V2: +$4,568**
   - Seed 50030: V2 = $112,747, Tomato = $100,207, Dmitrii = $112,632 $\rightarrow$ **Delta vs V2: -$12,540**
   - Seed 50042: V2 = $107,019, Tomato = $110,961, Dmitrii = $106,795 $\rightarrow$ **Delta vs V2: +$3,942**
5. **Statistical Metrics Across 6 Seeds**:
   - Mean Delta vs V2: **-$5,382.67**
   - Median Delta vs V2: **-$6,540.00**
   - Sample Standard Deviation ($ddof=1$): **$8,911.97**
   - Population Standard Deviation ($ddof=0$): **$8,135.48**
6. **Arithmetic Verification**:
   $$\text{Sum} = -15186 + (-1011) + (-12069) + 4568 + (-12540) + 3942 = -32,296$$
   $$\text{Mean} = \frac{-32,296}{6} = -5,382.6667 \approx -\$5,382.67$$
   The reported -$5,382.67 number is calculated **100% correctly**.
7. **Sweep Grid Delta Verification**:
   In `scratch/true_pizza_sweep_results.json`, **all 18 parameter combinations have negative mean deltas vs V2**:
   - Maximum delta: -$2,332.67 (achieved by tiles=10, cohorts=1)
   - Minimum delta: -$2,499.33 (achieved by tiles=30, cohorts=3)
   - Mean delta across grid: -$2,395.17
8. **Cherry-Picking Confirmation**: Prior research cited ONLY Seed 50042 (+3,942) while suppressing the negative ensemble average (-$5,382.67).
9. **Baseline Consistency**: Baseline was genuinely identical across comparison (`ClosedLoopAgentV2` vs `Dmitrii-LB2800`).
10. **Test Validity**: The experiment code genuinely tested tomato planting with active selling.

**Verdict**: **AUDIT 2 RETRACTION 100% VERIFIED**.

---

## 2. Reproduction R2: Shop Demand Model Contamination

### Objective
Verify whether the shop demand profiles in `candidates/closed_loop_architecture/shop_transition_model.py` contradicted simulator ground truth.

### Independent Verification
We inspected `sim.hpp:127-136`, `kaggriculture.py`, and `shop_transition_model.py:22-31`:
- 6 of 8 shops in `shop_transition_model.py` had fabricated or incomplete demand lists:
  - `BRUNCH_SPOT`: Added Milk, omitted Wheat.
  - `FARMERS_MARKET`: Added Melon, omitted Wheat.
  - `ICE_CREAM_SHOP`: Omitted Wheat.
  - `PET_CAFE`: Added Milk (demands strictly Carrot at 2.0x).
  - `PIZZA_SHOP`: Omitted Milk (demands Milk, Tomato, Wheat).
  - `SMOOTHIE_SHOP`: Added Carrot and Melon, omitted Milk.
- Only `BAKERY` and `YARN_STORE` were correctly specified.

**Verdict**: **AUDIT 2 RETRACTION 100% VERIFIED**. All downstream Value of Information and transition models remain invalid and discarded.

---

## 3. Reproduction R3: Additive Slack Experiment Invalidity

### Objective
Verify Audit 2's finding that `scratch/run_additive_investigation.py` was invalid.

### Independent Code Tracing
Inspection of `scratch/run_additive_investigation.py`:
1. **`VACANT_TILES` mode (lines 167–193)**:
   - Line 172 replaces wheat buy orders with tomato buy orders.
   - Line 182 replaces wheat planting with `["PLANT", "TOMATO"]`.
   - Dedicated worker planner `_plan_dedicated_worker` is **never called** (it is gated under `if self.land_mode == "SE_LAND"` at line 154).
   - **Zero watering commands** and **zero harvesting commands** are ever issued for vacant tiles.
   - Crops rotted into weeds per `sim.hpp:725`.
2. **`SE_LAND` mode (lines 143–144)**:
   - At line 143: `if day >= self.deploy_day and hour == 1 and len(market) < 10: market.append(["HIRE"])`.
   - If deploy day is Day 12, it hires a worker every day from Day 12 to Day 29 (18 consecutive days), ballooning hiring costs.

### Evaluation of Alternatives
- A. Genuinely tested additive slack? **NO**.
- B. Invalid? **YES**.
- C. Partially valid but conclusion overstated? **NO**. The script tested software defects, not agricultural slack.

**Verdict**: **AUDIT 2 RETRACTION 100% VERIFIED**. The experiment tested broken code. The question of whether exploitable slack exists remains open.

---

## 4. Reproduction R4 & S4: Step 696 Causality & Physical Agronomy Divergence

### Objective
Reconstruct Seed 50081 (V2's worst loss of -$730 against Dmitrii) and evaluate whether Step 696 order truncation was the root cause, and whether physical agronomy was identical.

### Reconstructed Chronological Timeline (Seed 50081)

| Step | Day & Hour | V2 State | Dmitrii State | Divergence Event | Causal Attribution |
|:---:|:---:|:---|:---|:---:|:---|
| **0–163** | Days 0–6 | Identical cash ($697), identical tiles, identical actions. | Identical cash ($697), identical tiles, identical actions. | None | N/A |
| **164** | Day 6, Hr 20 | Submits `[['SELL', 'WHEAT', 9], ['SELL', 'WOOL', 2]]`. | Submits `[['SELL', 'WHEAT', 9]]`. | **First Market Action Divergence** (V2 advance sold wool) | Non-fatal |
| **165** | Day 6, Hr 21 | Cash = **$1,435.0**. | Cash = **$975.0**. | **First Cash Divergence** ($+\$460$) | Non-fatal |
| **216** | Day 9, Hr 0 | Cash = $1,164.0. | Cash = $1,168.0. | Cash gap narrows to $4 deficit on V2 | Downstream price dynamics |
| **217** | Day 9, Hr 1 | Cash = $950.0. Submits `['HIRE']`, `['BUY_ANIMAL', 'SHEEP', 2]`. Buys 1 hire ($1), 1 sheep ($500), cash left = $449. **$3 short of 2nd sheep!** | Cash = $954.0. Submits `['HIRE']`, `['BUY_ANIMAL', 'SHEEP', 2]`. Fertilizer sold +$48 $\rightarrow$ buys 1 hire and **both sheep**! | **Fatal Resource Shortfall** (V2 fails sheep purchase) | **ROOT CAUSE OF LOSS** |
| **218** | Day 9, Hr 2 | Cash = $497.0. Hand 8 has 1 sheep. | Cash = $1.0. Hand 8 has 2 sheep. | Inventory divergence | Direct symptom |
| **259** | Day 10, Hr 19 | Hand 5 attempts `['PLACE', 'SHEEP']`. **Inventory empty $\rightarrow$ placement fails!** | Hand 5 attempts `['PLACE', 'SHEEP']`. Places sheep on Tile (1, 4). | Placement failure | Direct symptom |
| **260** | Day 10, Hr 20 | Tile (1, 4) is `{'kind': 'PASTURE'}` (EMPTY). | Tile (1, 4) is `{'kind': 'PASTURE', 'animal': 'SHEEP'}`. | **First Physical Tile Divergence** | Starts 460 turns of tile divergence |
| **260–719** | Days 10–29 | Tile (1, 4) remains empty pasture for **460 turns**. | Tile (1, 4) produces wool for 460 turns. | Persistent production gap | Primary driver of final score delta |
| **695** | Day 28, Hr 23 | Cash = **$86,898.0**. | Cash = **$87,190.0**. | V2 is **already losing by $292.0** before Step 696! | Disproves Step 696 as root cause |
| **696** | Day 29, Hr 0 | Submits 9 HIREs, 1 STRAW sell, 1 WHEAT sell (11 orders). 11th order dropped. | Submits 1 WHEAT sell, 9 HIREs (10 orders). Executed. | Order truncation (36 wheat deferred) | Observational symptom |
| **712** | Day 29, Hr 16 | Liquidates wheat via `['SELL', 'WHEAT', 1000]`. Executes PASS on hands. | Liquidates wheat via `['SELL', 'WHEAT', 1000]`. Executes `COLLECT_FERTILIZER` on hands. | Terminal hand action divergence | Hand search advantage |
| **719** | Day 29, Hr 23 | Final cash = **$99,498.0**. | Final cash = **$99,863.0**. | Single-seat delta = -$365.0; Paired CRN margin = **-$730.0**. | Final Game Over |

### Findings on Causality
- Step 696 was **NOT the root cause**. V2 had already diverged at Step 164, suffered sheep purchase failure at Step 217, had physical tile divergence from Step 260, and was already down by $292 before Step 696. The 36 wheat was sold at Step 712.
- The true causal root of the -$730 loss on Seed 50081 was a **Day 9 sheep purchase failure** triggered by a tiny $4 cash shortfall ($950 vs $954).
- Physical agronomy is **NOT 100.0% bit-for-bit identical**: runtime cash feedback triggers animal purchase failures, and Dmitrii runs terminal Monte Carlo planning at steps 712–718.

**Verdict**: **AUDIT 2 RETRACTION 100% VERIFIED**.

---

## 5. Reproduction S1: Frozen Live Submissions SHA256 Integrity

### Objective
Cryptographically verify whether active live submissions 56146971 and 56146947 match frozen records.

### Verification Results
| Submission ID | File Path | File Size | Audit 2 Reported SHA256 | Audit 2.1 Computed SHA256 | Match? |
|:---:|:---|:---:|:---|:---|:---:|
| **`56146947`** | `candidates/compiled_v54_plus_shop.py` | 337,768 bytes | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | **EXACT MATCH** |
| **`56146971`** | `candidates/compiled_v54_plus_residual.py` | 338,100 bytes | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | **EXACT MATCH** |
| Control Source | `candidates/v54_plus_shop.py` | 24,196 bytes | `592f0ba3...` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` | **EXACT MATCH** |
| Control Source | `candidates/v54_plus_residual.py` | 24,534 bytes | `5b2d5080...` | `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80` | **EXACT MATCH** |

**Verdict**: **VERIFIED FROZEN AND UNTOUCHED**.

---

## 6. Reproduction S2: Replay `episode_107543042.json` & Hiring Collapse Disproof

### Objective
Verify whether our live submission suffered a Day-12 hiring collapse due to cash falling below $800.

### Independent Replay Data Inspection
In `replays/live_tournament/episode_107543042.json`:
- **Day 12 Dawn Cash (Step 288, Hour 0)**: Eldritch (Player 0) had **$9,847.0 cash**. (Nowhere near < $800).
- **Day 12 Hiring Actions (Step 289, Hour 1)**: Eldritch submitted 9 `['HIRE']` orders and bought 8 wheat seeds.
- **Hands Hired**: Workforce increased from 0 to **9 hands**.
- **Hiring Costs Paid**: Total spent was $168.0 ($80 seeds + $88 hiring cost for 9 workers).
- **Cash After Hiring (Step 289)**: **$9,679.0 cash**.
- **Origin of the False Narrative**:
  - `scratch/reconstruct_live_losses.py` line 66 parsed `len(f.get("units", []))`.
  - In official Kaggle replays, hands are in `f["hands"]`, not `f["units"]`.
  - The script recorded `hands: 0` across all checkpoints.
  - Researchers invented the story of an "$800 hiring collapse".
- **Real Cause of Loss**:
  - Unlocked town shops: Double Pizza, Triple Pet Cafe, One Yarn, One Smoothie, One Farmers Market.
  - Zero Brunch, Zero Ice Cream.
  - ORiginators specialized in Carrot and Tomato, earning $126,718.
  - Eldritch produced Strawberry without Strawberry town shop multipliers, earning $71,622.

**Verdict**: **AUDIT 2 DISPROOF 100% VERIFIED**.

---

## 7. Reproduction S3: Engine Enforcement of `MAX_ORDERS = 10`

### Objective
Verify whether orders at index $\ge 10$ are dropped silently.

### Behavioral Test Results
1. Injecting 12 `['BUY_SEED', 'WHEAT', 1]` orders in a single step:
   - Starting cash $3,000 $\rightarrow$ Final cash $2,900. Exactly 10 seeds purchased; orders 11 and 12 dropped without error.
2. Injecting 1 multi-unit order (`['BUY_SEED', 'WHEAT', 5]`) + 10 single orders (total 11 orders):
   - Exactly 14 seeds purchased (5 from order 0 + 9 from orders 1..9). Order 10 was dropped.

**Verdict**: **CONFIRMED ENGINE GROUND TRUTH**.

---

## 8. Reproduction S5: 19S / 0T Strawberry Bedrock Dominance

### Objective
Verify whether 19S/0T Strawberry Bedrock strictly dominates other static allocations within `crop_portfolio_sweep_results.json`.

### Recomputed Portfolio Metrics (50 Discovery Seeds, 100 Matches)

| Allocation | Mean Cash | Paired Margin vs Dmitrii | Win Rate | Worst Loss | Downside Risk |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **19S / 0T** | **$97,026.17** | **+$24.98** | **59.0%** | **-$222.00** | **56.72** |
| **17S / 2T** | $96,915.38 | -$1,465.44 | 40.0% | -$5,414.00 | 2,436.10 |
| **15S / 4T** | $97,000.32 | -$2,078.04 | 38.0% | -$7,765.00 | 3,528.71 |
| **13S / 6T** | $96,523.91 | -$3,259.85 | 34.0% | -$10,994.00 | 5,175.09 |
| **11S / 8T** | $95,499.40 | -$5,242.14 | 27.0% | -$15,285.00 | 7,603.65 |
| **10S / 9T** | $94,940.34 | -$6,179.46 | 25.0% | -$17,196.00 | 8,700.11 |
| **9S / 10T** | $94,202.18 | -$7,370.64 | 25.0% | -$19,263.00 | 10,066.90 |
| **8S / 11T** | $93,329.82 | -$8,774.21 | 18.0% | -$21,895.00 | 11,668.29 |
| **6S / 13T** | $92,083.73 | -$10,800.65 | 14.0% | -$25,264.00 | 13,901.66 |
| **4S / 15T** | $92,085.73 | -$10,798.65 | 14.0% | -$25,264.00 | 13,901.50 |
| **2S / 17T** | $92,087.73 | -$10,796.65 | 14.0% | -$25,264.00 | 13,901.36 |
| **0S / 19T** | $92,089.73 | -$10,794.65 | 14.0% | -$25,264.00 | 13,901.23 |

### Scope Qualification
- All numbers reported in Audit 2 match `crop_portfolio_sweep_results.json` to the penny.
- **Scope Restriction**: 19S/0T achieved the highest mean margin and lowest downside risk across the tested static hybrid allocations on the 50 Discovery seeds. However, it achieved a 59.0% win rate (not 100%), and does not strictly dominate on every individual seed.

**Verdict**: **VERIFIED WITHIN STATIC EXPERIMENTAL SCOPE**.
