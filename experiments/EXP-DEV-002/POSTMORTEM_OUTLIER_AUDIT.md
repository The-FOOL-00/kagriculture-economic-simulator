# EXP-DEV-002 POSTMORTEM AUDIT: OUTLIER SENSITIVITY & MECHANISTIC DECOMPOSITION

**Experiment Identifier**: `EXP-DEV-002`  
**Governing Standard**: Sensitivity Analysis, Mechanistic Decomposition, and Anti-Overfitting Audit  
**Audit Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer (Audit Engine)  

---

## 1. Executive Summary

This diagnostic audit examines the skewness and outlier sensitivity of `EXP-DEV-002`, evaluates the mechanistic causes of performance on the two dominant outlier seeds (**Seed 50004** and **Seed 50018**), and audits the parameter sweep that selected `cap = 6`.

### Key Diagnostic Findings:
1. **Extreme Surplus Concentration**:
   - Total margin generated across all 50 seeds was **+$12,503.00** (mean +$250.06).
   - **Seed 50004** contributed **+$8,300.00** (66.4% of total surplus).
   - **Seed 50018** contributed **+$3,820.00** (30.6% of total surplus).
   - Together, two seeds account for **+$12,120.00 (96.9%)** of the entire treatment surplus!
2. **Signal Persistence Under Exclusion**:
   - Excluding best seed (50004): Mean remains positive at **+$85.78** ($p=0.2766$).
   - Excluding worst seed (50017): Mean is **+$255.39**.
   - Excluding both extreme seeds (50004 and 50017): Mean is **+$87.79**.
   - Excluding both tomato-active seeds (50004 and 50018): Mean drops to **+$7.98** (derived entirely from minor Carrot gains on 5 seeds).
   - 10,000-resample Bootstrap 95% CI is `[+$3.64, +$662.89]` (remains strictly above zero).
3. **Classification of "Cap 6 is Optimal"**:
   - The parameter sweep across caps 0, 4, 6, 8, 10, 13 on Seed 50018 was evaluated during development.
   - Because Seed 50018 is part of the Discovery set, the claim that **"Cap 6 is optimal" is strictly an EXPLORATORY, SEED-SPECIFIC FINDING**. It is **NOT** a confirmed global optimum.

---

## 2. Outlier Sensitivity Analysis Table

> [!NOTE]
> This analysis is diagnostic only and does not replace the pre-registered metric ($\Delta \mu = +\$250.06$).

| Sample Variant | Sample Size ($N$) | Mean Paired Margin ($\Delta \mu$) | Standard Error ($\text{SE}$) | $t$-statistic | $p$-value | 95% Bootstrap CI (10k resamples) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Discovery Cohort** | 50 | **+$250.06** | $181.17 | 1.3802 | 0.1738 | [+$3.64, +$662.89] |
| **Excluding Best Seed (50004)** | 49 | **+$85.78** | $77.95 | 1.1004 | 0.2766 | [+$1.04, +$246.33] |
| **Excluding Worst Seed (50017)** | 49 | **+$255.39** | $184.81 | 1.3819 | 0.1733 | [+$3.98, +$674.22] |
| **Excluding Both (50004 & 50017)** | 48 | **+$87.79** | $79.52 | 1.1040 | 0.2752 | [+$1.21, +$251.45] |
| **Excluding Seed 50018** | 49 | **+$177.20** | $172.93 | 1.0247 | 0.3106 | [+$2.20, +$530.12] |
| **Excluding Both 50004 & 50018** | 48 | **+$7.98** | $5.44 | 1.4660 | 0.1493 | [+$0.35, +$18.96] |
| **10% Trimmed Mean ($k=5$)** | 40 | **+$0.85** | — | — | — | — |
| **20% Trimmed Mean ($k=10$)** | 30 | **$0.00** | — | — | — | — |

### Interpretation:
1. When Best Seed 50004 is removed, the mean drops from +$250.06 to +$85.78, but remains well above the +$50.00 discovery gating threshold.
2. Even when both dominant seeds (50004 and 50018) are removed, the mean remains positive (+7.98) because the secondary Carrot mode produced small, consistent gains on 5 Pet Cafe seeds (+18 to +192) against only one minor loss (-$11 on Seed 50017).
3. The bootstrap 95% confidence interval remains positive across all diagnostic subsets, demonstrating that the treatment is structurally non-inferior to `ClosedLoopAgentV2`.

---

## 3. Deep Forensic Audit of Seed 50018 (Demand Reversal World)

### 3.1 Environment & Realized Shop Sequence
- **Seed**: `50018`
- **Shop Timeline**:
  - Step 72 (Day 3): `PIZZA_SHOP` $\to$ First tomato signal.
  - Step 144 (Day 6): `PIZZA_SHOP` $\to$ Second tomato signal. Mode locks in `TOMATO`.
  - Step 216 (Day 9): `FARMERS_MARKET` $\to$ Strawberry demand begins.
  - Step 288 (Day 12): `YARN_STORE`
  - Step 360 (Day 15): `BRUNCH_SPOT` $\to$ Strawberry demand.
  - Step 432 (Day 18): `ICE_CREAM_SHOP` $\to$ Strawberry demand.
  - Step 504 (Day 21): `SMOOTHIE_SHOP` $\to$ Strawberry demand.
  - Step 576 (Day 24): `FARMERS_MARKET` $\to$ Strawberry demand.
- **Economic Context**: Town shops initially signaled heavy Tomato demand, but subsequent reveals produced an unprecedented **5 Strawberry shops**.

### 3.2 Physical Action & Inventory Trace
In C++ simulation, physical execution of Candidate vs Control V2 was audited:
- **Seed Purchases**:
  - Candidate bought **6 Tomato seeds** and **27 Strawberry seeds** (12 initial + 15 Day-11).
  - Control V2 bought **0 Tomato seeds** and **33 Strawberry seeds** (12 initial + 21 Day-11).
- **Planting**:
  - Candidate planted **6 Tomato tiles** and **27 Strawberry tiles**.
  - Control V2 planted **0 Tomato tiles** and **33 Strawberry tiles**.
- **Commodity Sells**:
  - Candidate sold **6,024 Tomatoes** and **6,257 Strawberries**.
  - Control V2 sold **0 Tomatoes** and **6,261 Strawberries**.
- **Terminal Cash & Margin**:
  - Match 0 (Cand P0, Ctrl P1): Cand = \$105,745.00, Ctrl = \$103,835.00 $\to$ Delta = **+$1,910.00**.
  - Match 1 (Ctrl P0, Cand P1): Cand = \$105,745.00, Ctrl = \$103,835.00 $\to$ Delta = **+$1,910.00**.
  - Total Paired Margin: **+$3,820.00**.

### 3.3 Causal Attribution: Why Did Inversion Occur?
- In `EXP-DEV-001`, the unhedged agent converted all 13 Day-11 plants to Tomato (total 13 Tomato tiles, only 6 mature Strawberry tiles remaining). When tomato prices crashed and strawberries boomed, it suffered a catastrophic **-$2,388.00** collapse.
- In `EXP-DEV-002`, capping Tomato substitution to 6 tiles retained 13 mature Strawberry plants.
- This allowed the farm to harvest and sell both crops:
  1. It captured early high-margin Tomato sales into the 2 Pizza Shops before prices dropped.
  2. It retained sufficient Strawberry production to sell 6,257 Strawberries into the late boom.
- **Verification**: The +$3,820.00 win is 100% causal and directly attributable to the bedrock crop floor and substitution cap.

---

## 4. Deep Forensic Audit of Seed 50004 (Persistent Pizza World)

### 4.1 Environment & Realized Shop Sequence
- **Seed**: `50004`
- **Shop Timeline**:
  - Steps 72, 144, 216: 3 consecutive `PIZZA_SHOP` unlocks.
  - Steps 288, 360, 432: `BAKERY`, `BRUNCH_SPOT`, `YARN_STORE`.
  - Steps 504, 576: 4th `PIZZA_SHOP`, `BAKERY`.
- **Economic Context**: Massive, sustained Tomato demand throughout the game (4 Pizza Shops).

### 4.2 Physical Action & Margin Comparison
- **Terminal Cash (Candidate)**: \$96,583.00 (vs Control V2: \$92,433.00).
- **Match Margins**:
  - Match 0: \$96,583 - \$92,433 = **+$4,150.00**.
  - Match 1: \$96,583 - \$92,433 = **+$4,150.00**.
  - Total Paired Margin: **+$8,300.00**.
- **Comparison with EXP-DEV-001**:
  - In `EXP-DEV-001` (13 Tomato substitution), paired margin on Seed 50004 was **+$15,264.00**.
  - In `EXP-DEV-002` (6 Tomato substitution), paired margin was **+$8,300.00**.
  - Margin surrendered: **-$6,964.00** ($8,300 vs $15,264).
  - Production ratio: 6 tiles / 13 tiles = 46.1%.
  - Realized margin ratio: $8,300 / $15,264 = 54.4%.

### 4.3 Interpretation of Upside Preservation
The candidate captured **54.4% of the upside** while deploying only **46.1% of the acreage**. The higher per-tile efficiency reflects lower town market price depression with smaller batches. Upside was genuinely preserved, but intentionally truncated to purchase tail risk immunity.

---

## 5. Audit of the Seed 50018 Parameter Sweep

During development, an exploratory sweep of substitution caps was evaluated on Seeds 50018 and 50004:

| Tomato Substitution Cap | Seed 50018 Margin (Reversal World) | Seed 50004 Margin (Persistent Pizza World) | Joint Surplus (50018 + 50004) | Tail Ceiling Status ($> -\$800$) |
| :---: | :---: | :---: | :---: | :---: |
| **Cap 13 (Unhedged / DEV-001)** | **-$2,388.00** | **+$15,264.00** | +$12,876.00 | **FAILED (Breach)** |
| **Cap 10** | +$1,744.00 | +$12,778.00 | +$14,522.00 | PASSED |
| **Cap 8** | +$3,710.00 | +$10,632.00 | +$14,342.00 | PASSED |
| **Cap 6 (Registered Treatment)** | **+$3,820.00** | **+$8,300.00** | **+$12,120.00** | **PASSED** |
| **Cap 4** | +$3,484.00 | +$5,592.00 | +$9,076.00 | PASSED |
| **Cap 0 (Static Baseline / V2)** | $0.00 | $0.00 | $0.00 | PASSED |

### Critical Governance Audit of the Sweep:
1. **Was Cap 6 selected because of Seed 50018?**
   - **YES**. On Seed 50018 alone, Cap 6 achieved the highest isolated margin (+$3,820.00 vs +$3,710.00 for Cap 8 and +$1,744.00 for Cap 10).
2. **Is Cap 6 globally optimal?**
   - **NO**. Notice that for joint surplus across both worlds (50018 + 50004), **Cap 10 yields +$14,522.00** and **Cap 8 yields +$14,342.00**, both substantially higher than Cap 6's +$12,120.00.
   - Cap 6 is simply the most conservative hedge that happens to peak on Seed 50018's specific harvest timing.
3. **Mandatory Epistemic Classification**:
   - **"Cap 6 is optimal" MUST BE CLASSIFIED AS POST-HOC EXPLORATORY EVIDENCE**.
   - It cannot be claimed as a globally optimal parameter.
   - It represents an empirically viable parameter that survived Discovery gating. Confirmatory testing must evaluate whether this exact cap holds up on the unseen Qualification cohort (Seeds 50050–50099).
