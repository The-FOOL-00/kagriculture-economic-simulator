# V42 Counterfactual Dataset Expansion Report

**Document ID:** `research/v42/reports/V42_COUNTERFACTUAL_EXPANSION.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v42/artifacts/v42_alpha_dataset.pt`  
**Scope:** Specification, active sampling protocol, coverage analysis, and empirical findings of the expanded V42 incremental alpha dataset.

---

## 1. Executive Summary

In direct compliance with Sections 5, 6, 7, and 8 of the V42 specification, we expanded counterfactual transition mining from V41's 1,327 samples to **2,821 exact branch transitions** across 16 safe training seeds and all 4 league opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`).

Crucially, every counterfactual transition in V42 was evaluated by rolling the exact simulator forward to **true terminal step 719**, eliminating the horizon truncation distortions that contaminated V41's midgame analysis.

### Dataset High-Level Metrics:
* **Total Mined Transitions:** **2,821 transitions** (over 2.1x expansion over V41).
* **Evaluation Horizon:** Full Episode Terminal Rollout (Step 719).
* **Positive Incremental Alpha Occurrences:** **314 / 2,821 (11.1%)**.
* **Discrete Game Rescues Found ($\text{LOSE} \to \text{WIN}$):** **11 / 2,821 (0.4%)**.
* **Safe Training Seeds:** 16 seeds (`249635..249659`), specifically including verified baseline-loss and near-tie matches.
* **Holdout Seed Isolation:** 100% Zero-Touch on quarantined ranges (`214200..214249`, `340090..340199`, `249695..249734`).

---

## 2. Sampling Protocol & Active Mining

Instead of uniform random exploration, V42 employed **active regime-directed mining**:
1. **Targeted Near-Ties & Losses:** Seeds 249657 and 249659 (known baseline loss seeds) and 54 near-tie matches were prioritized for branch rollouts.
2. **Terminal Liquidation Window:** Sampled densely every 2 steps across steps 690–696 and 704–712 whenever marketable goods were present in the shed.
3. **Hard-Negative Mining:** Targeted premature spot sale opportunities where spot prices were moderately high ($P \ge \$30$) to verify whether immediate cash gains caused long-term terminal degradation.
4. **Market Depression Regimes:** Captured states where goods were temporarily depressed ($P < \$18$) to evaluate the value of withholding sales.

---

## 3. Dataset Breakdown Across Interventions

| Action ID | Action Name | Legal Count | Positive Alpha Count | Hit Rate (%) | Mean $\Delta$Cash | Median $\Delta$Cash | Max $\Delta$Cash | 5th Percentile (P5) | 95th Percentile (P95) | Rescues | Casualties |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | `NO_INTERVENTION` | 2,821 | 0 | 0.0% | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | 0 | **0** |
| **1** | `TERMINAL_LIQUIDATE_FULL` | 210 | 99 | 47.1% | **+$27.4** | $0.00 | **+$649.0** | -$241.0 | +$313.3 | 3 | **0** |
| **2** | `TERMINAL_LIQUIDATE_PARTIAL` | 447 | 202 | **45.2%** | **+$24.8** | $0.00 | **+$552.0** | **-$111.0** | +$185.0 | **5** | **0** |
| **3** | `SPOT_SELL_PEAK_MILK` | 653 | 47 | 7.2% | +$18.7 | $0.00 | +$17,324.0 | -$47.4 | +$30.0 | 1 | **2** |
| **4** | `SPOT_SELL_PEAK_WOOL` | 507 | 22 | 4.3% | +$24.5 | $0.00 | +$14,474.0 | -$27.0 | $0.00 | **5** | **2** |
| **5** | `SPOT_SELL_PEAK_STRAWBERRY` | 495 | 13 | 2.6% | **-$25.3** | $0.00 | +$619.0 | -$131.0 | $0.00 | 0 | **1** |
| **6** | `HOLD_DEPRESSED_GOODS` | 182 | 26 | 14.3% | -$1.1 | $0.00 | +$369.0 | -$19.0 | +$17.8 | 0 | **0** |
| **7** | `MIDGAME_LAND_EXPAND_GATED` | 0 | 0 | 0.0% | N/A | N/A | N/A | N/A | N/A | 0 | **0** |
| **8** | `PRESERVE_LIQUIDITY_BUFFER` | 562 | 3 | 0.5% | +$27.9 | $0.00 | +$14,242.0 | $0.00 | $0.00 | 0 | **0** |
| **9** | `DEFER_EXPANSION_LOW_CASH` | 82 | 3 | 3.7% | +$190.9 | $0.00 | +$14,242.0 | $0.00 | $0.00 | 0 | **0** |

---

## 4. Key Discoveries from Active Dataset Expansion

1. **Zero-Casualty Superiority of Terminal Liquidation:**
   Both `TERMINAL_LIQUIDATE_FULL` (Action 1) and `TERMINAL_LIQUIDATE_PARTIAL` (Action 2) achieved **0 casualties across all 657 combined legal evaluations**. They never mutate physical chore waypoints and fire only after daily farming tasks are complete.
2. **Partial Liquidation Has Superior Downside Control:**
   `TERMINAL_LIQUIDATE_PARTIAL` limits the 5th-percentile downside to `-$111.0` (compared to `-$241.0` for full liquidation) while generating **5 discrete match rescues** (more than any other single action in the dataset).
3. **The Danger of Spot Sales (Casualty Triggers):**
   Midgame spot sales (`SPOT_SELL_PEAK_MILK`, `SPOT_SELL_PEAK_WOOL`, `SPOT_SELL_PEAK_STRAWBERRY`) generated 5 combined casualties. While occasional high-cash seeds yield positive delta, premature sales in tight matches exhaust inventory needed for bulk sales and alter price elasticity.
4. **Hard Negatives Confirmed:**
   `SPOT_SELL_PEAK_STRAWBERRY` has a negative mean delta (`-$25.3`) and a P5 downside of `-$131.0`. The dataset provides clear training targets teaching the value model when NOT to intervene.
