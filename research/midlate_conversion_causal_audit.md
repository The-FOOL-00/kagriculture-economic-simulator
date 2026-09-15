# Championship Experiment — Mid/Late Wheat vs Livestock Conversion Causal Audit (Days 15–25)

**Audit Protocol**: Adversarial Causal Audit of Mid/Late Game Commodity Conversion  
**Date & Time**: 2026-09-10T07:15:00+05:30  
**Champion Status**: V54++ (`candidates/v54_plus_shop.py`) FROZEN AS IMMUTABLE CHAMPION  
**Benchmark Reference**: Untouched 500-Seed Symmetric Holdout (1,000 matches)  
**Final Verdict**: **NO-GO — wheat/livestock conversion controller not causally validated**  

---

## 1. Executive Verdict

### **VERDICT: NO-GO — wheat/livestock conversion controller not causally validated**

An exhaustive, adversarial causal audit of the mid-to-late game commodity conversion regime (Days 15–25, Steps 336–624) was conducted to evaluate the hypothesis that V54++ loses rare matches against Canonical V66 due to suboptimal wheat retention for livestock rather than direct market liquidation.

The investigation encompassed:
1. Turn-by-turn state telemetry extraction across 65 selected matches representing all holdout partition tiers (Groups A through G).
2. Per-seed economic identity modeling tracking direct wheat value versus realized livestock yield.
3. 940 paired counterfactual simulations across 10 distinct policy arms (**C0 through C9**) on a balanced stratified partition (Large Losses, Medium Losses, Close Games, and Large Wins).
4. Direct head-to-head discovery validation across 200 matches on 100 fresh seeds (Seeds 2000–2099).
5. Solo validation vs IDLE across 25 fresh seeds (Seeds 2500–2524).

### Key Empirical Findings:
1. **The Conversion Hypothesis Fails the Universal Distribution Test**:
   - Forcing additional wheat liquidation during elevated wheat price states (**Arm C1**) produces a catastrophic net drop of **-$6,565.5** across the full seed distribution (95% CI: $[-\$8,505.9, -\$4,762.2]$), destroying 73.3% of V54++ winning seeds and causing 70.2% of matches to suffer severe losses $> \$1,000$.
   - Forcing additional livestock retention by suppressing planned wheat sales (**Arm C2**) results in a devastating collapse of **-$32,683.7** (95% CI: $[-\$40,340.5, -\$25,265.6]$), causing inventory congestion and feed waste.
   - Price-only threshold rules (**Arm C3**) mirror Arm C1's failure (**-$6,535.8** net drop).
   - The best-performing discovery arm, **Arm C4** (Price + Inventory threshold: $P_{\text{wheat}} \ge 20.0$, $\text{shed\_wheat} \ge 25$), showed a nominal discovery gain of $+208.5$, but **completely collapsed in head-to-head validation against Frozen V54++**, suffering a statistically significant **-$266.13** deficit (95% CI: $[-\$367.38, -\$157.66]$).
   - In solo testing vs IDLE, Arm C4 regressed by **-$666.72** (95% CI: $[-\$1,051.37, -\$239.52]$).
2. **The Apparent Advantage of V66 is an Overfitted Asymmetric Tail**:
   - On the rare seeds where V66 wins by $\ge \$5,000$ (1.5% of matches), V66 achieves its margin not through superior closed-loop economic sensing, but because its hardcoded route prior happens to align with an extreme wheat commodity boom.
   - Any attempt to dynamically sell more wheat from V54++'s shed during mid-game deprives the farm of livestock feed reserves, creating severe downstream capacity destruction on the 98.5% majority of seeds.
3. **Action Rule Execution**:
   - Zero candidate mechanisms satisfied the 12-point success gate.
   - No candidate (`candidates/v54_plus_conversion.py`) is created.
   - **V54++ remains permanently frozen as the validated champion**.
   - **Zero Kaggle submissions**.

---

## 2. Frozen Champion

All research baselines are permanently frozen and hashed in [`research/midlate_frozen_manifest.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/midlate_frozen_manifest.md):

| Baseline Identifier | Relative Workspace Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| **V54+ Macro Candidate** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| **V54++ Champion** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |

---

## 3. V54++ vs V66 Loss Distribution

Partitioning of all 1,000 matches (500 symmetric seeds) from `research/shop216_holdout_results.json`:

| Group Identifier | Definition | Match Count | Percentage | Seed Count (Net) | Seed Percentage |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Group A** | V66 lead $\ge \$10,000$ | 4 | 0.4% | 2 | 0.4% |
| **Group B** | V66 lead $\ge \$5,000$ and $< \$10,000$ | 11 | 1.1% | 5 | 1.0% |
| **Group C** | V66 lead $\ge \$2,500$ and $< \$5,000$ | 95 | 9.5% | 45 | 9.0% |
| **Group D** | Close ($|\text{margin}| < \$2,500$) | 760 | 76.0% | 385 | 77.0% |
| **Group E** | V54++ lead $\ge \$2,500$ and $< \$5,000$ | 25 | 2.5% | 12 | 2.4% |
| **Group F** | V54++ lead $\ge \$5,000$ and $< \$10,000$ | 28 | 2.8% | 12 | 2.4% |
| **Group G** | V54++ lead $\ge \$10,000$ | 77 | 7.7% | 39 | 7.8% |
| **Total** | **All Evaluated Matches** | **1,000** | **100.0%** | **500** | **100.0%** |

> [!NOTE]
> Net large losses to V66 ($\ge \$5\text{k}$) occur in only **7 out of 500 seeds (1.4%)**, whereas net large wins by V54++ occur in **51 out of 500 seeds (10.2%)**.

---

## 4. Mid/Late Divergence Analysis

Turn-by-turn tracing of the large loss seeds produced [`research/wheat_livestock_first_divergence.csv`](file:///c:/Users/Sundareswaran/Kagriculture/research/wheat_livestock_first_divergence.csv):

| Seed | Divergence Step | Day / Hour | V54++ Action | V66 Action | Wheat Price | Wool Price | Milk Price | Downstream Consequence | Reward Delta |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **1773** | 301 | Day 12, H13 | RETAIN/FEED WHEAT | SELL WHEAT | \$40.0 | \$98.0 | \$57.0 | V66 sold 2,306 wheat; V54++ converted wheat to livestock | -\$18,804.0 |
| **1949** | 301 | Day 12, H13 | RETAIN/FEED WHEAT | SELL WHEAT | \$40.0 | \$198.0 | \$72.0 | V66 sold 2,305 wheat; V54++ converted wheat to livestock | -\$27,831.0 |
| **1542** | 301 | Day 12, H13 | SELL WHEAT | RETAIN WHEAT | \$42.0 | \$235.0 | \$124.0 | V54++ sold 2,296 wheat; V66 scaled wool conversion | -\$5,559.0 |
| **1609** | 301 | Day 12, H13 | SELL WHEAT | RETAIN WHEAT | \$42.0 | \$235.0 | \$95.0 | V54++ sold 2,314 wheat; V66 scaled wool conversion | -\$5,206.0 |
| **1691** | 301 | Day 12, H13 | RETAIN/FEED WHEAT | SELL WHEAT | \$40.0 | \$133.0 | \$110.0 | V66 sold 2,306 wheat; V54++ converted wheat to livestock | -\$8,202.0 |
| **1871** | 301 | Day 12, H13 | RETAIN/FEED WHEAT | SELL WHEAT | \$42.0 | \$72.0 | \$74.0 | V66 sold 2,119 wheat; V54++ converted wheat to livestock | -\$5,008.0 |
| **1948** | 301 | Day 12, H13 | SELL WHEAT | RETAIN WHEAT | \$41.0 | \$235.0 | \$133.0 | V54++ sold 2,296 wheat; V66 scaled wool conversion | -\$5,257.0 |
| **1969** | 301 | Day 12, H13 | RETAIN/FEED WHEAT | SELL WHEAT | \$43.0 | \$72.0 | \$74.0 | V66 sold 2,118 wheat; V54++ converted wheat to livestock | -\$5,503.0 |

### Forensic Insight:
The first consequential divergence occurs at **Step 301 (Day 12)** across all large loss seeds.  
On Seeds 1773, 1949, 1691, 1871, 1969, V54++ is on the Backbone route and hoards grain for cows/sheep, while V66 liquidates wheat into high prices ($>\$40$).  
However, on Seeds 1542, 1609, 1948, the **exact opposite occurred**: V54++ switched to the Yarn route and sold 2,300 wheat, while V66 converted wheat to wool and beat V54++.  
This proves that **neither pure grain liquidation nor pure livestock conversion is universally dominant**; the outcome is driven by seed-dependent shop availability and tile bonuses.

---

## 5. Wheat Economic Accounting

Telemetry across Days 14–26 (Steps 336 to 624) from [`research/midlate_accounting_telemetry.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/midlate_accounting_telemetry.json):

| Checkpoint Step | In-Game Day | Avg Wheat Price | V54++ Wheat Sold | V66 Wheat Sold | V54++ Wheat Revenue | V66 Wheat Revenue | Net Wheat Revenue Lead |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **336** | Day 14 | \$40.80 | 187.8 units | 162.3 units | \$7,662 | \$6,622 | -\$1,040 |
| **384** | Day 16 | \$40.46 | 316.2 units | 274.3 units | \$12,793 | \$11,098 | -\$1,695 |
| **432** | Day 18 | \$40.92 | 455.0 units | 370.4 units | \$18,619 | \$15,157 | -\$3,462 |
| **480** | Day 20 | \$41.28 | 537.8 units | 441.7 units | \$22,199 | \$18,233 | -\$3,966 |
| **528** | Day 22 | \$40.32 | 707.1 units | 555.9 units | \$28,511 | \$22,414 | -\$6,097 |
| **576** | Day 24 | \$41.09 | 795.0 units | 649.0 units | \$32,667 | \$26,667 | -\$6,000 |
| **624** | Day 26 | \$41.03 | 933.4 units | 746.4 units | \$38,297 | \$30,625 | -\$7,672 |

Across the broad seed distribution, V54++ actually sells **more physical wheat** on average than V66 (+187 units by Step 624). V66's grain lead is confined exclusively to the 1.4% tail seeds.

---

## 6. Livestock Conversion Accounting

Logged in [`research/wheat_livestock_economic_identity.csv`](file:///c:/Users/Sundareswaran/Kagriculture/research/wheat_livestock_economic_identity.csv):

| Partition Group | Avg Wool Price | Avg Milk Price | V54++ Wool Revenue | V66 Wool Revenue | V54++ Milk Revenue | V66 Milk Revenue | Net Livestock Conversion Value |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Large Loss Seeds** | \$142.6 | \$58.2 | \$2,140 | \$2,480 | \$890 | \$1,320 | **-\$770** |
| **Winning Seeds** | \$188.4 | \$84.6 | \$14,860 | \$4,120 | \$6,420 | \$2,100 | **+\$15,060** |
| **Close Seeds** | \$165.2 | \$48.1 | \$5,210 | \$4,980 | \$2,140 | \$2,080 | **+\$290** |

On winning seeds, converting wheat to wool and milk yields an overwhelming **+$15,060 net lead**. Sacrificing feed to sell raw wheat destroys this entire advantage.

---

## 7. First Causal Decision

Tracing source code execution reveals where wheat retention versus liquidation is governed:

| Component | File | Function | Code Lines | Operational Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Route Planner** | `mod_v62` | `_V56_BACKBONE_ROUTE` | Steps 240–650 | Planned market actions contain zero wheat sell orders during mid-game. |
| **Feed Reservation** | `v49.residual_controller` | `apply` / `_preempt` | Lines 639–647 | Calculates `required_wheat = ceil(animals * feed_days_reserve)`. |
| **Commodity Gating** | `v49.residual_controller` | `ResidualConfig` | Line 82 | `preempt_items` excludes `"WHEAT"`. Preemptor never liquidates wheat. |
| **Shop Switching** | `candidates/v54_plus_shop.py` | `_select_route` | Lines 85–106 | Switches between Backbone (livestock priority) and Yarn (wool/wheat export). |

The decision to retain or sell wheat is fundamentally determined by the **macro route selection** at Steps 72 and 144, not by a runtime micro-controller.

---

## 8. Public-State Sufficiency

Can the superior regime be inferred from public observation features before Step 301?
Evaluated features:
- $P_{\text{wheat}}$, $P_{\text{wool}}$, $P_{\text{milk}}$ at Steps 144–300
- 24-step price trends ($\Delta P$)
- Unlocked shops (`obs['town']['unlocked_shops']`)
- Farm cash and inventory

### Predictive Performance of Best Public State Classifier:
- **Accuracy**: $65.5\%$
- **Precision (Regime A)**: $87.5\%$
- **Recall (Regime A)**: $28.0\%$
- **False Negative Rate**: **$72.0\%$**

Public price features at Step 300 have very low recall ($28\%$) for detecting whether wheat price will remain elevated through Day 25. The market dynamics are endogenous and diverge after Day 15 based on town consumption.

---

## 9. Horizon Effect

Analysis of decision horizon at Steps 336 through 624:
- **Early Horizon (Days 14–18)**: Livestock conversion possesses higher potential NPV ($>\$60/\text{unit}$ equivalent) if animals survive multiple lactation/shearing cycles.
- **Late Horizon (Days 24–28)**: As $T \to 720$, the remaining cycles for newly produced milk/wool drop below the break-even feed cost. Raw wheat liquidation becomes strictly superior for any inventory that cannot complete a full production cycle.
- **V54++'s Existing Handling**: V54++ already incorporates this via `_TERMINAL_MARKET` at Step 718. Intervening earlier (Days 20–24) prematurely starves animals on normal seeds.

---

## 10. Liquidity Effect

Did V66 win due to intermediate cash flow timing?
- On Large Loss seeds: V66 achieved a mid-game cash lead of **+$1,657.32** at Step 480 by selling wheat.
- However, V54++ held cash balances above **$15,000** at all times after Day 10.
- Neither agent suffered worker starvation or was liquidity-constrained from hiring workers or purchasing fertilizer.
- **Verdict**: The difference is **pure commodity accounting**, not liquidity constriction.

---

## 11. Physical Capacity Effect

Did physical constraints (shed capacity, pasture slots) force the gap?
- Shed capacity is 100 units; V54++ is protected by `_v60_shed_guard` at Hour 23.
- Pasture slots were never saturated (average herd size: 2 cows, 3 sheep; capacity: 16 animals).
- Animal starvations were exactly **zero** across all matches.
- **Verdict**: Physical capacity bottlenecks did not cause the losses.

---

## 12. Market Endogeneity

- Each agent's wheat sales depress market wheat price by approximately **-$0.08 to -$0.12 per unit sold**.
- When Arm C1 dumped 8 units of wheat per turn, market wheat price plummeted from $\$42.0$ to $\$14.50$ within 3 days.
- By artificially forcing wheat liquidation, the controller **destroyed its own realized price**, turning a theoretical $\$40$ liquidation value into a realized $\$16$ yield.

---

## 13. Counterfactual Results

940 paired matches across arms **C0 through C9** from [`research/midlate_counterfactual_summary.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/midlate_counterfactual_summary.json):

| Arm | Policy Description | All Seeds Mean $\Delta$ | 95% Bootstrap CI | W / L / T | Large Losses Mean $\Delta$ | Large Wins Mean $\Delta$ | Tail Loss $P(\Delta < -\$1\text{k})$ |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | Frozen V54++ Baseline | $+0.0$ | $[+0.0, +0.0]$ | 0 / 0 / 94 | $+0.0$ | $+0.0$ | 0.0% |
| **C1** | Force Wheat Liquidation ($P \ge 22$) | **-$6,565.5** | $[-\$8,505.9, -\$4,762.2]$ | 22 / 72 / 0 | -\$741.6 | **-$5,372.1** | 70.2% |
| **C2** | Suppress Wheat Sells ($P_{\text{wool}} \ge 55$) | **-$32,683.7** | $[-\$40,340.5, -\$25,265.6]$ | 4 / 84 / 6 | -\$30,785.6 | **-$38,353.7** | 78.7% |
| **C3** | Price Threshold Rule ($P \ge 24$) | **-$6,535.8** | $[-\$8,381.6, -\$4,733.8]$ | 22 / 72 / 0 | -\$728.9 | **-$5,303.2** | 70.2% |
| **C4** | Price + Inventory ($P \ge 20, \text{shed} \ge 25$) | **+$208.5** | $[+\$105.4, +\$311.8]$ | 70 / 24 / 0 | +\$237.0 | +\$343.7 | 2.1% |
| **C5** | Price + Inventory + Horizon | **-$6,828.5** | $[-\$8,747.9, -\$5,017.3]$ | 22 / 72 / 0 | -\$535.0 | **-$5,760.3** | 70.2% |
| **C6** | Price Trend / Velocity Rule | **+$27.6** | $[-\$18.3, +\$68.9]$ | 64 / 18 / 12 | +\$112.6 | -\$31.6 | 0.0% |
| **C7** | Relative Value Selector | **-$6,616.5** | $[-\$8,662.8, -\$4,836.0]$ | 24 / 70 / 0 | -\$1,236.3 | **-$4,749.2** | 66.0% |
| **C8** | Random Decision Control (20%) | **-$423.2** | $[-\$921.4, +\$31.1]$ | 54 / 40 / 0 | -\$202.7 | +\$387.3 | 38.3% |
| **C9** | Deliberately Inverted Policy | **-$35,548.6** | $[-\$42,527.8, -\$28,197.9]$ | 0 / 94 / 0 | -\$32,732.1 | **-$42,481.2** | 100.0% |

---

## 14. Regime Classification

- **Regime A (Direct Wheat Superior)**: Present in only ~25% of matches.
- **Regime B (Livestock Conversion Superior)**: Present in ~55% of matches.
- **Regime C (Indifferent)**: Present in ~20% of matches.
Attempting to force Regime A policies globally destroys value in Regime B.

---

## 15. Discovery Validation (Arm C4)

Arm C4 emerged from the 940-match gauntlet as the only arm with a positive mean (+208.5).
It was advanced to a dedicated **Discovery Validation against Frozen V54++**:
- **Dataset**: 100 fresh seeds (Seeds 2000–2099) $\times 2$ seats = 200 matches.
- **Mean Margin (C4 - V54++)**: **-$266.13**
- **Median Margin**: +$2.00
- **95% Bootstrap CI**: **[-$367.38, -$157.66]** (Completely negative)
- **Win / Loss / Tie**: 100 Wins / 100 Losses / 0 Ties
- **$P(\text{margin} < -\$500)$**: 31.5%
- **$P(\text{margin} < -\$1,000)$**: 20.5%

### Verdict on Discovery Validation:
**FAIL**. The $+208$ discovery gain was an artifact of sample variance on the counterfactual partition. In head-to-head competition against V54++, Arm C4 is strictly inferior by **-$266.13** ($p < 10^{-4}$).

---

## 16. Untouched Holdout Validation

Because zero mechanisms passed Discovery Validation, **no candidate mechanism was promoted to the untouched holdout**.

---

## 17. Solo Validation

Solo benchmark vs IDLE on 25 fresh seeds (Seeds 2500–2524):
- **Frozen V54++ Solo**: **$154,574.52** (95% CI: $[+\$144,278.73, +\$164,648.34]$)
- **Arm C4 Solo**: **$153,907.80** (95% CI: $[+\$143,740.46, +\$163,278.48]$)
- **Paired Solo Delta (C4 - V54++)**: **-$666.72** (95% CI: **[-$1,051.37, -$239.52]**)

Arm C4 damages intrinsic farm productivity even in complete isolation without opponent interaction.

---

## 18. Tail-Risk Analysis

- Arm C1, C3, C5, C7 create catastrophic adverse tails: $70\%$ of matches lose $> \$1,000$.
- Arm C4 introduces a 20.5% probability of losing $> \$1,000$ in head-to-head matches against V54++.
- Zero mechanisms achieved non-negative tail bounds.

---

## 19. Final Controller Specification

**NO CONTROLLER ACCEPTED.**  
In accordance with Section 18 and 19:
> *"If any condition fails: NO-GO. If no mechanism passes: DO NOT invent a candidate. Keep V54++ frozen as champion."*

`candidates/v54_plus_conversion.py` was **NOT created**.

---

## 20. Hashes / Reproducibility

| File | SHA256 Checksum |
| :--- | :--- |
| `candidates/v54_plus_shop.py` (Champion) | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |
| `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |

---

## 21. Go / No-Go

### Final Verdict:
```
NO-GO — wheat/livestock conversion controller not causally validated
```

### Absolute Stop Protocol Enforced:
- **V54++ remains permanently frozen as the sole validated champion**.
- No candidate files created.
- No source modifications made.
- Zero Kaggle submissions.
- Mid/Late conversion research concluded and closed.
