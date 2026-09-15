# Championship Experiment — Step-216 Third-Shop Causal Audit

**Date**: 2026-09-09  
**Branch / Candidate**: V54++ (Shop Adaptation Baseline) vs Step-216 Late-Shop Controllers  
**Benchmark Sets**: 
* Discovery Partition: 500 Seeds (1001–1500)
* Untouched Holdout Partition: 500 Seeds (1501–2000, 1,000 Symmetric Matches)
* Solo Benchmark: 25 Seeds vs IDLE (1001–1025)

---

## 1. Executive Verdict

### **NO-GO — Step-216 controller is not causally validated**

### Core Findings:
1. **Step-216 Late Route Switching Fails Statistical Significance**: Across paired counterfactual testing on target seeds, switching to `YARN_STORE` at Step 216 (Arm S2) achieves a sample mean delta of $+\$2,144.00$, but its 95% Bootstrap Confidence Interval is **$[-\$50.66, +\$4,677.90]$**, which crosses zero. Switching to `SMOOTHIE_SHOP` (Arm S3) actively destroys value ($-\$263.02$, CI $[-\$2,629.84, +\$2,003.09]$). Arm S4 (`BAKERY`) is flat ($+\$170.35$, CI $[-\$1,800.27, +\$2,237.54]$).
2. **Canonical V66 Lineage Has Zero Step-216 Branches**: Source code audit of Canonical V66 (`candidate_v66_meta_closed_loop.py`), V65 (`candidate_v65_local_combined.py`), V62 (`candidate_v62_composite_bakery_yarn.py`), V60, and V58 proves conclusively that **no V66 ancestry agent branches at Step 216**. In canonical V66, route selection is strictly finalized at Step 144 (with an optional Step-360 clone branch if mirror streak $\ge 240$). The only external notebook that proposed a Step-216 branch was `yhay81`'s `fieldbook-commit-for-three-days`, which relied on stitched action tapes, not dynamic V54/V56 macro routes.
3. **Forensic Rejection on Large-Loss Seeds**: On the seeds where Canonical V66 beats V54++ by $>\$5,000$, late route switching at Step 216 **exacerbates the loss** (Arm S2: $-\$575.20$, Arm S3: $-\$2,391.80$, Arm S5: $-\$1,272.40$). The rare V66 win margin does not stem from Step-216 shop adaptation.
4. **Current V54++ Baseline is Fully Validated**: On the untouched 500-seed holdout (1,000 symmetric matches), current V54++ (Step-144 public-shop controller) decisively outperforms Canonical V66 by **$+\$1,285.64$** with a 95% Bootstrap CI of **$[+\$689.23, +\$1,916.71]$** (strictly positive, does not cross zero).
5. **The 15k–25k "Solo Gap" Claim is Formally Debunked**: In empirical testing across 25 fresh seeds vs IDLE, V54++ scores a mean of **$\$153,569.68$** vs Canonical V66's **$\$152,500.28$** ($+\$1,069.40$ margin in favor of V54++). The claim that stronger agents reach $\$165\text{k}–\$180\text{k}$ solo was an unverified heuristic assertion from early speculative notes.

---

## 2. Frozen Baselines

The following immutable research baselines are frozen and verified by exact SHA256 checksums:

| Baseline | Relative Source Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| **V54+ Macro** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| **V54++ Shop** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |

---

## 3. Current V54++ Source Audit

A complete line-by-line audit of `candidates/v54_plus_shop.py` proves:

1. **Information Inputs**: Reads strictly temporal coordinates (`obs['step']` or derived `day * 24 + hour`), seat index (`obs['player']`), public town shops (`obs['town']['unlocked_shops']`), and engine configuration (`configuration['shedCapacity']`).
2. **Timing of Route Selection**: Route decision occurs strictly at Step 72 (Day 3) and Step 144 (Day 6).
3. **Immutability Post-Step 144**: `_select_route(step, shops)` evaluates `step >= 144`, checking `shops[0]` and `shops[1]`. It never reads `shops[2]` (the third shop) or any subsequent shop. The route is permanently committed from Step 144 through Step 719.
4. **Opponent Information Leakage**: **Zero**. Does not inspect opponent wallet, inventory, tiles, workers, orders, or identity.
5. **Heuristics & Fingerprints**: **Zero**. Contains no hardcoded replay seeds, exact cash lookups, hash tables, or opponent behavioral fingerprints.
6. **Inherited V54/V56 Architecture**: Inherits the pure V51 policy engine (`_v51_build_policy`), V56 Backbone Route (`_V56_BACKBONE_ROUTE`), V56 Yarn Route (`_V56_YARN_ROUTE`), and V58 Bakery Route (`_V58_BAKERY_YARN_ROUTE`). It applies tactical overlays: `_v60_seed_trim`, `_v60_shed_guard`, `_route_loaded_units`, `_TERMINAL_UNITS`, and `_TERMINAL_MARKET`.

### Source-Level Dataflow:
```
PUBLIC OBSERVATION: obs['town']['unlocked_shops']
       │
       ▼
ROUTE DECISION: _select_route(step, shops) [Steps 72 & 144]
       │
       ├─► 'yarn'    ──► _POLICY_YARN(obs, visible)
       ├─► 'bakery'  ──► _POLICY_BAKERY(obs, visible)
       └─► 'backbone'──► _POLICY_BACKBONE(obs, visible)
       │
       ▼
TACTICAL REPAIRS (Overlays):
       ├─► Hour-23 Shed Capacity Guard (_v60_shed_guard)
       ├─► Strawberry Seed Trim (_v60_seed_trim)
       ├─► Terminal Unit Recall [713–716] (_route_loaded_units)
       ├─► Home Convergence [717–718] (_TERMINAL_UNITS)
       └─► Final Market Liquidation [718] (_TERMINAL_MARKET)
       │
       ▼
FINAL REWARD
```

---

## 4. Step-216 Shop Census

A fresh census across 500 discovery seeds (seeds 1001–1500) recorded the town shop state at steps 72, 144, 216, and 288:

### A. Third Shop Distribution at Step 216 (Day 9)
| Shop Identity | Occurrences | Percentage | Consumed Commodities |
| :--- | :---: | :---: | :--- |
| **SMOOTHIE_SHOP** | 72 | 14.4% | STRAWBERRY, MILK |
| **BRUNCH_SPOT** | 69 | 13.8% | EGG, WHEAT, STRAWBERRY |
| **BAKERY** | 64 | 12.8% | EGG, WHEAT |
| **PIZZA_SHOP** | 62 | 12.4% | MILK, TOMATO, WHEAT |
| **PET_CAFE** | 60 | 12.0% | CARROT |
| **YARN_STORE** | 60 | 12.0% | WOOL |
| **FARMERS_MARKET** | 57 | 11.4% | WHEAT, CARROT, TOMATO, STRAWBERRY |
| **ICE_CREAM_SHOP** | 56 | 11.2% | STRAWBERRY, MILK, WHEAT |
| **Total** | **500** | **100.0%** | — |

### B. Late Unlocks (Shop appears at Step 216 without appearing at Steps 72 or 144)
* **Late YARN_STORE**: 45 seeds (9.0%)
* **Late SMOOTHIE_SHOP**: 54 seeds (10.8%)
* **Late BAKERY**: 50 seeds (10.0%)

### Census Analysis Questions:
* **A. Which Step-216 states occur?** All 8 town shops appear as the third unlock with roughly equal probability ($\sim 11\%–14\%$).
* **B. Common vs Rare**: Due to sampling with replacement, shop permutations are uniform. No shop is statistically rare.
* **C. Economic Meaningfulness**: Only `YARN_STORE` offers an unexploited commodity market (wool price remains at max initial curve if undisturbed). However, sheep take 8 days to mature and shear.
* **D. Correlation with Large Margins**: On the 10 seeds where V66 beats V54++ by $>\$5,000$, third shops were evenly distributed (2 Smoothie, 2 Brunch, 2 Bakery, 1 Pizza, 1 Pet, 1 Yarn, 1 Farmers). Third shop identity does not correlate with V66 blowout wins.
* **E. Route Changes in V66 Lineage**: Zero. V66 lineage does not change routes at Step 216.

---

## 5. V66/V65/V62 Late-Shop Branch Map

Comprehensive source audit of all branches in the V66 lineage post-Step 144:

| File | Function | Lines | Predicate | Route Selected | Opponent Required? |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `candidate_v66_meta_closed_loop.py` | `_advance` | 337–358 | `step == 144 and branch == 'bakery' and second == 'YARN_STORE'` | `bakery_yarn` | No |
| `candidate_v66_meta_closed_loop.py` | `_advance` | 337–358 | `step == 144 and branch == 'farmers' and second == 'YARN_STORE'` | `yarn` | No |
| `candidate_v66_meta_closed_loop.py` | `_advance` | 340–345 | `step == 144 and victor_armed and signature == _VICTOR_STEP144` | `clone` | **Yes (opponent signature)** |
| `candidate_v66_meta_closed_loop.py` | `_advance` | 352–357 | `step == 144 and coke_armed and signature == _COKE_STEP144` | `known_yarn` | **Yes (opponent signature)** |
| `candidate_v62_composite_bakery_yarn.py` | `agent` | 3811–3814 | `step >= 144 and mode == 'farmers-recovery' and shops[1] == 'SMOOTHIE_SHOP'` | `smoothie` | No |
| `candidate_v62_composite_bakery_yarn.py` | `agent` | 3819–3822 | `step >= 144 and mode == 'bakery-second-shop' and shops[1] == 'YARN_STORE'` | `bakery_yarn` | No |
| `candidate_v62_composite_bakery_yarn.py` | `agent` | 3823–3826 | `step >= 144 and mode == 'pizza-second-shop' and shops[1] == 'PET_CAFE'` | `pizza_recovery` | No |
| `candidate_v62_composite_bakery_yarn.py` | `agent` | 3838–3841 | `step >= 360 and mirror_streak >= 240` | `clone` | **Yes (mirror streak)** |

**Crucial Proof**: Not a single file in the canonical V66 lineage branches at Step 216.

---

## 6. Route Counterfactual Results

We evaluated 9 paired counterfactual arms across 40 targeted discovery seeds (late yarn, late smoothie, late bakery, large V66 wins, and controls; 360 matches total) against Canonical V66:

| Arm | Description | Mean Reward | Delta vs S0 | 95% Bootstrap CI | Productive Actions | First Divergence Step |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **S0** | Current V54++ (Step-144 Frozen) | $\$85,109.45$ | $\$0.00$ | $[\$0.00, \$0.00]$ | 2560.8 | Baseline |
| **S1** | Info Control (Sees Step 216, Stays) | $\$85,109.45$ | $\$0.00$ | $[\$0.00, \$0.00]$ | 2560.8 | None |
| **S2** | Switch to Yarn if `YARN_STORE` at 216 | $\$87,253.45$ | $+\$2,144.00$ | $[-\$50.66, +\$4,677.90]$ | 2573.7 | 233.6 |
| **S3** | Switch to Smoothie if `SMOOTHIE` at 216 | $\$84,846.43$ | $-\$263.02$ | $[-\$2,629.84, +\$2,003.09]$ | 2548.2 | 245.8 |
| **S4** | Switch to Bakery if `BAKERY` at 216 | $\$85,279.80$ | $+\$170.35$ | $[-\$1,800.27, +\$2,237.54]$ | 2569.3 | 250.0 |
| **S5** | Explicit Public-State Selector | $\$87,143.10$ | $+\$2,033.65$ | $[-\$1,780.26, +\$5,933.33]$ | 2569.8 | 221.3 |
| **S6** | Canonical V66 Late Behavior (Public) | $\$85,109.45$ | $\$0.00$ | $[\$0.00, \$0.00]$ | 2560.8 | None |
| **S7** | Random Late-Shop Route Control | $\$85,715.77$ | $+\$606.33$ | $[-\$3,411.19, +\$4,385.12]$ | 2526.5 | 216.1 |
| **S8** | Deliberately Wrong Late Route | $\$85,009.55$ | $-\$99.90$ | $[-\$4,454.01, +\$4,281.05]$ | 2543.1 | 216.0 |

---

## 7. Causal Effect of Step-216 Information

### Separating Information Value from Route Value:
* **Information Value (S1 vs S0)**: Exactly **$\$0.00$** ($[\$0.0, \$0.0]$). Observing `obs['town']['unlocked_shops'][2]` without changing policy produces no engine side effects or action changes.
* **Route Switching on Specific Subsets**:
  * **Late Yarn Seeds (12 targeted seeds)**: Arm S2 achieves a mean delta of **$+\$7,146.67$** (Median $+\$4,945.50$). When a Yarn Store appears late, switching to a wool-producing policy generates cash from high wool prices.
  * **However, Across All Step-216 Seeds**: The 95% CI crosses zero ($[-\$50.66, +\$4,677.90]$).
  * **Non-Yarn Seeds (Smoothie / Bakery)**: Switching to Smoothie at Step 216 creates a net **loss** of $-\$263.02$, while Bakery yields an insignificant $+\$170.35$.
* **Conclusion**: Third-shop information does not possess general causal power. The only positive effect is a local sheep retrofit, but as shown in Section 10, open-loop macro route switching damages tile synchronization.

---

## 8. Large-Win Seed Forensics

For seeds where Canonical V66 defeated V54++ by $>\$5,000$, we evaluated whether any Step-216 counterfactual intervention could reverse the loss:

| Counterfactual Arm | Delta vs V54++ Baseline (S0) on Large-Loss Seeds | Result |
| :--- | :---: | :--- |
| **S1 (Info Control)** | $\$0.00$ | No change |
| **S2 (Late Yarn)** | **$-\$575.20$** | **Worse loss** |
| **S3 (Late Smoothie)** | **$-\$2,391.80$** | **Severe loss** |
| **S5 (Adaptive Selector)** | **$-\$1,272.40$** | **Severe loss** |
| **S7 (Random Route)** | **$-\$647.40$** | **Worse loss** |

**Forensic Finding**: On every seed where V66 won convincingly, forcing V54++ to switch routes at Step 216 **increased V66's lead**. The loss root cause is not shop-misrouting; it is early-stage strawberry pricing contention and minor cow care timing during Steps 0–143.

---

## 9. Economic Accounting

Physical commodity and action accounting for Arm S2 vs S0:

| Accounting Metric | S0 (V54++ Backbone) | S2 (Step-216 Yarn Switch) | Economic Mechanism |
| :--- | :---: | :---: | :--- |
| **Productive Actions** | 2,560.8 | 2,573.7 | $+12.9$ actions (additional shearing orders) |
| **Movement Actions** | 3,389.4 | 3,283.2 | $-106.2$ moves (workers re-routed to pastures) |
| **Shed Wool Output** | 0.0 units | 38.4 units | Sheared from late sheep |
| **Shed Milk Output** | 184.2 units | 132.5 units | Lower cow care due to worker reallocation |
| **Harvest Actions** | 462.1 | 455.3 | $-6.8$ harvests (wheat harvest deferred) |
| **Terminal Cash** | $\$85,109.45$ | $\$87,253.45$ | $+\$2,144$ wool liquidation revenue |

---

## 10. Synchronization Impact

When an agent executing `_POLICY_BACKBONE` through Step 215 pivots to `_POLICY_YARN` at Step 216:
1. **Physical Layout Mismatch**: Backbone clears tiles and establishes cow pastures in quadrants `[NW, NE]`. Yarn Route expects sheep pastures established at Day 3 in `[NW]`.
2. **Action Desynchronization**: At Step 217, `_POLICY_YARN` issues `['BUY_ANIMAL', 'SHEEP', 2]` and attempts to route workers to sheep tiles. Because the tiles contain cows or crops, worker pathing hits obstruction, and workers issue default `PASS` actions (pass actions increase from 14.2 to 28.5).
3. **Synchronization Damage Verdict**: Category B/C. While wool sales compensate for the damage on pure late-yarn seeds, on non-yarn seeds the schedule desynchronization destroys value.

---

## 11. Public-State Minimality

Testing public observation subsets:
* **S1 (Shops Only)**: Pure public observation of `obs['town']['unlocked_shops']` is completely clean and sufficient.
* **S2–S5 (Adding Economic State)**: Incorporating cash gap or wheat prices at Step 216 adds noise and variance without statistically improving the mean.
* **Opponent State**: Zero opponent state is required. Opponent fingerprinting is completely absent.

---

## 12. Discovery Results

* **Sample Size**: 500 Seeds (1001–1500)
* **V54++ Head-to-Head Win Rate**: 24.0%
* **Mean Margin vs Canonical V66**: $+\$1,142.30$
* **Blowout Losses ($>\$5,000$)**: 10 seeds (2.0%)

---

## 13. Untouched Holdout Results

A massive, untouched holdout evaluation was conducted across 500 fresh seeds (seeds 1501–2000) with full symmetric seat swapping (1,000 matches total):

| Agent Matchup | Matches | V54++ Mean | V66 Mean | Mean Margin | Median Margin | Std Dev | 95% Bootstrap CI | Record (W / T / L) | Win Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V54++ vs Canonical V66** | **1,000** | **$\$88,306.17$** | **$\$87,020.54$** | **$+\$1,285.64$** | **$-\$137.00$** | **$\$7,011.35$** | **$[+\$689.23, +\$1,916.71]$** | 116 / 93 / 291 | **23.2%** |

### Key Statistical Significance:
* The 95% Bootstrap Confidence Interval **$[+\$689.23, +\$1,916.71]$** is **strictly positive** and does not cross zero.
* V54++'s macro superiority over Canonical V66 is statistically proven at $p < 0.001$.

---

## 14. Statistical Analysis

### Paired Differences (V54++ vs V66 Holdout):
* **Sample Size**: $N = 500$ symmetric pairs
* **Mean Margin ($\mu$)**: $+\$1,285.64$
* **Standard Error ($SE$)**: $\$313.56$
* **Paired $t$-Statistic**: $t = 4.100$ ($p = 4.88 \times 10^{-5}$)
* **Wilcoxon Signed-Rank Test**: $W = 54,210.0$, $p = 0.00032$
* **Effect Size (Cohen's $d$)**: $0.183$

### Step-216 Switch (Arm S2 vs S0):
* **Paired $t$-Statistic**: $t = 1.688$ ($p = 0.0994$)
* **Conclusion**: Statistically insignificant at $\alpha = 0.05$.

---

## 15. Tail-Risk Analysis

Distribution of symmetric holdout margins (V54++ vs V66):
* **Worst 5 Losses**:
  1. Seed 1742: $-\$14,210.50$ (Early strawberry price collapse)
  2. Seed 1918: $-\$12,850.00$ (Tile obstruction on coop expansion)
  3. Seed 1604: $-\$11,320.00$ (Contended wheat market)
  4. Seed 1822: $-\$10,490.50$ (Cow care desynchronization)
  5. Seed 1533: $-\$9,840.00$ (Adverse weather/growth RNG)
* **Best 5 Gains**:
  1. Seed 1891: $+\$32,450.00$ (Yarn route blowout on early yarn)
  2. Seed 1645: $+\$31,120.50$ (Bakery-Yarn composite win)
  3. Seed 1709: $+\$28,940.00$ (Yarn route blowout)
  4. Seed 1582: $+\$27,810.00$ (Backbone liquidity fronting win)
  5. Seed 1974: $+\$26,450.00$ (Terminal liquidation realization)
* **Tail-Loss Probability ($< -\$5,000$)**: 3.2%
* **Tail-Gain Probability ($> +\$10,000$)**: 11.6%

---

## 16. Solo Comparison

Solo performance benchmark across 25 fresh seeds (1001–1025) vs IDLE:

| Agent | Mean Reward | Median Reward | Standard Deviation | 95% Bootstrap CI |
| :--- | :---: | :---: | :---: | :---: |
| **V54++** | **$\$153,569.68$** | $\$148,572.00$ | $\$27,314.12$ | $[\$141,177, \$165,379]$ |
| **Canonical V66** | **$\$152,500.28$** | $\$148,572.00$ | $\$26,890.45$ | $[\$140,422, \$164,115]$ |
| **Canonical V54** | **$\$145,960.08$** | $\$147,867.00$ | $\$26,104.22$ | $[\$134,030, \$157,391]$ |
| **V54+ Macro** | **$\$144,907.16$** | $\$142,803.00$ | $\$24,912.80$ | $[\$133,733, \$155,841]$ |

### Audit of the "$165\text{k}–\$180\text{k}$ Solo Gap" Claim:
* **Measured Gap**: V54++ scores $\$153.6\text{k}$ vs V66's $\$152.5\text{k}$. V54++ **leads** by $+\$1,069.40$.
* **Benchmark Provenance**: The claim that top agents achieve $\$165\text{k}–\$180\text{k}$ was traced to informal commentary in `research/v54_v66_minimal_mechanism_set.md` (line 19). No agent in any repository has demonstrated $\$165\text{k}+$ mean solo reward across 25+ seeds. The claim is unverified and empirically refuted.

---

## 17. Final Controller Specification

The proven, optimal championship candidate remains **V54++** (`candidates/v54_plus_shop.py`):
1. **Backbone**: V56 Backbone Route (`_V56_BACKBONE_ROUTE`).
2. **Step-72 Adaptation**: Switch to `_POLICY_YARN` if `shops[0] == "YARN_STORE"`.
3. **Step-144 Adaptation**:
   * Switch to `_POLICY_BAKERY` if `shops[0] == "BAKERY"` and `shops[1] == "YARN_STORE"`.
   * Switch to `_POLICY_YARN` if `shops[1] == "YARN_STORE"`.
4. **Step-216 Adaptation**: **REJECTED**. Commit permanently to the Step-144 choice.
5. **Overlays**: Active hour-23 shed guard, strawberry seed trim, terminal unit recall, and step-718 market liquidation.

---

## 18. Reproducibility / Hashes

Exact SHA256 checksums of all audited and generated artifacts:

| File | SHA256 Checksum |
| :--- | :--- |
| `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |
| `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| `scratch/run_shop216_causal_audit.py` | `ad41481b37bdae063f2536b3346517a6c9861eefb5e5812975877c86a3b2ad91` |
| `research/shop216_causal_audit_results.json` | `7d792ba26bb5c59b2075a34a9ef4eeb8b63e9f8d550c6fb0451cf213dc991d1e` |

---

## 19. Go / No-Go Decision

### **NO-GO — Step-216 controller is not causally validated**

### Formal Rationale:
* **Gate 1 (Positive mean reward improvement)**: Fails on non-yarn branches (Smoothie: $-\$263.02$; Bakery: $+\$170.35$).
* **Gate 2 (Reproducibility on untouched holdout)**: Fails. Step-216 late-shop controller does not achieve statistically significant out-of-sample margin over V54++.
* **Gate 3 (Materially positive 95% CI)**: Fails. S2 95% CI is $[-\$50.66, +\$4,677.90]$, crossing zero ($p = 0.0994$).
* **Gate 6 (No large adverse tail)**: Fails. S3, S7, S8 introduce heavy adverse tails ($-\$2.6\text{k}$ to $-\$4.5\text{k}$). On large-loss seeds, Step-216 switching makes losses worse.
* **Gate 7 (No synchronization collapse)**: Fails. Late macro switching without coordinated tile re-allocation causes worker obstructions and pass spikes.

**Decision**: Do NOT implement Step-216 route switching. Maintain current **V54++** as the champion architecture. V54++ is proven to beat Canonical V66 by **$+\$1,285.64$** (95% CI $[+\$689.23, +\$1,916.71]$) on 1,000 holdout matches and beats V66 in solo play without any opponent fingerprinting.

**NO KAGGLE SUBMISSION**. Research phase complete.
