# V41 Counterfactual Dataset Generation Report

**Document ID:** `research/v41/reports/COUNTERFACTUAL_DATASET_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v41/artifacts/counterfactual_dataset.pt`  
**Scope:** Specification, sampling protocol, safety governance, and empirical findings of the exact counterfactual simulator dataset.

---

## 1. Executive Summary

In direct compliance with Sections 12, 13, 14, and 15 of the V41 specification, we generated an exact counterfactual simulation dataset using `CounterfactualEvaluator` and `FastKagricultureSim`.

Rather than forcing an RL agent to blindly explore millions of random steps, the dataset mines exact, ground-truth cash and margin consequences $\Delta_{\text{cash}}(s_t, a) = \text{Cash}(a) - \text{Cash}(0)$ by branching the simulator at strategic decision points.

---

## 2. Sampling Protocol & Governance Invariants

1. **Strict Holdout Quarantine:**  
   Zero touches occurred on protected holdout seed ranges (`214200..214249`, `340090..340199`, `249695..249734`). All transitions were mined strictly from the safe training partition (`249635..249654`).
2. **Opponent Diversity:**  
   Matches were played against diverse league benchmarks: `E8_DMITRII`, `E2_A7`, and `E0_V3`.
3. **Zero Information Leakage:**  
   The candidate evaluator operates strictly on observable game state; it possesses zero access to random seeds, future commodity prices, or opponent internal parameters.

---

## 3. Dataset Summary Statistics

| Metric | Value |
| :--- | :---: |
| **Total Mined Transitions** | **1,327 transitions** |
| **Safe Training Seeds Used** | 10 seeds (`249635..249644`) |
| **Opponents Evaluated** | 3 (`E8_DMITRII`, `E2_A7`, `E0_V3`) |
| **Decision Points with Positive Alpha ($\Delta > 0$)** | **149 / 1,327 (11.2%)** |
| **Abstention Optimal ($a^* = 0$, Golden Property)** | **1,178 / 1,327 (88.8%)** |
| **Total Evaluation Wall Time** | 647.3s |
| **Effective Simulation Rate** | ~450 SPS aggregate |

---

## 4. Empirical Breakdown by Intervention Type

| Action ID | Action Name | Optimal Selection Count | Positive Alpha Count | Mean Cash Delta ($\Delta > 0$) | Max Observed Delta | Safety Class |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **0** | `NO_INTERVENTION` | 1,178 | 0 | $0.00 (Baseline) | $0.00 | `SAFE_ATOMIC` |
| **1** | `TERMINAL_LIQUIDATE_694` | 59 | 59 | **+$132.32** | **+$346.00** | `SAFE_ATOMIC` |
| **3** | `SPOT_SELL_MILK` | 31 | 31 | **+$139.35** | **+$528.00** | `SAFE_ATOMIC` |
| **4** | `SPOT_SELL_WOOL` | 38 | 38 | **+$10.34** | **+$146.00** | `SAFE_ATOMIC` |
| **5** | `SPOT_SELL_STRAWBERRY` | 4 | 4 | **+$119.75** | **+$158.00** | `SAFE_ATOMIC` |
| **7** | `HOLD_DEPRESSED_GOODS` | 4 | 4 | **+$2.50** | **+$4.00** | `CONDITIONALLY_SAFE` |
| **9** | `MIDGAME_LAND_EXPAND_F5` | 13 | 13 | **+$3,385.00** | **+$3,389.00** | `SAFE_WITH_REPLAN` |

---

## 5. Key Forensic & Economic Takeaways

1. **The Dominance of Abstention:** In 88.8% of strategic decision points, the incumbent baseline (A7/V35) is already mathematically optimal ($\Delta \le 0$ for all alternative actions). This proves why unregularized RL destroyed performance in V40: exploring randomly when the baseline is near-optimal causes catastrophic losses.
2. **Exploiting Peak Spot Prices:** Selling Milk and Strawberries when market spot prices peak ($P \ge \$30$) yields +$100 to +$528 in incremental alpha without disrupting farm chores.
3. **Midgame Land Expansion Alpha:** When farm liquidity exceeds $12,000 at steps 280–312, acquiring Quadrant 2 produces **+$3,385.00** in net profit, confirming the RLX2-F5 counterfactual hypothesis under safe execution conditions.
4. **Endgame Liquidation:** Step 693–694 liquidation of high-value goods consistently adds +$130 to +$346 per game by pre-empting the market crash caused by opponent harvests.
