# V45 Market Counterfactual Discovery & Strategy Evaluation Report

**Document ID:** `research/v45/reports/V45_MARKET_COUNTERFACTUAL_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 3 & 5 (Market Counterfactual Discovery & Strategy Search)  
**Artifact Path:** `research/v45/artifacts/market_counterfactuals.json`  
**Catalog Path:** `research/v45/artifacts/adversarial_alpha_catalog.json`  
**Full Rollouts Evaluated:** 640 Full-Terminal Matches (Step 0 to Step 719)  
**Gate Verdict:** **`V45_MARKET_ALPHA_NOT_ROBUST` (V44 Frontier Proves Near-Optimal)**  

---

## 1. Executive Summary

Phase 3 and Phase 5 evaluated whether observable opponent pressure and dynamic market indicators can be converted into robust incremental matchup alpha beyond the incumbent V44 portfolio.

Using our fast simulation engine, 10 systematic adversarial market strategies were evaluated across 64 tournament-scale match legs (8 clean DEV seeds × 4 league opponents × 2 seat positions) with **100% full-terminal Step 719 rollouts**.

The empirical evidence reveals a decisive negative result:
* **The V44 Bedrock Frontier:** V44 achieved a **100.0% Win Rate** (64/64 wins in this cohort, 128/128 in Phase 0) with zero casualties.
* **Premature Pre-emption Collapse:** Selling earlier (Steps 691–692) to front-run the opponent dump caused a **-$70.27 mean cash deficit** and **1 casualty**. At Step 691, late melon and strawberry crops have not completed their harvest-to-shed transit.
* **Dynamic Pressure Sensitivity:** Triggering early liquidation dynamically upon detecting initial price deterioration produced **-$100.70 mean cash deficit** and **1 casualty**.
* **Tranche Sizing Sensitivity:** Shifting the initial tranche from 50% to 60% (`TRANCHE_60_40`) achieved a nominal mean delta of **+$0.38**, but induced **1 casualty** on Seed 249657 vs `E2_A7` due to per-unit lockstep price slippage.
* **Depth Capping Penalty:** Capping order volume to 10 or 15 units stranded late inventory, resulting in a **-$4.59 deficit**.

---

## 2. Experimental Results Table (640 Full-Terminal Rollouts)

| Rank | Candidate Strategy Name | Core Mechanism Tested | Mean Cash $\Delta$ vs V44 | Median Cash $\Delta$ | Mean Margin $\Delta$ | Casualties | Rescues | Positive Hit Rate |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **-** | **`V44_BASELINE`** | **Payback Cutoff + 50/50 Staggered Flush** | **$0.00** | **$0.00** | **$0.00** | **0** | **0** | **100.0%** |
| 1 | `TRANCHE_70_30` | 70% at 693-694, 30% at 704 | -$1.38 | +$0.00 | -$2.12 | **0** | 0 | 15.6% |
| 2 | `TRANCHE_60_40` | 60% at 693-694, 40% at 704 | +$0.38 | +$0.00 | -$10.09 | **1** | 0 | 34.4% |
| 3 | `DEPTH_CAPPED_15` | Order cap 15 units on high-value | -$4.59 | -$6.50 | -$26.78 | **1** | 0 | 28.1% |
| 4 | `DEPTH_CAPPED_10` | Order cap 10 units on high-value | -$4.59 | -$6.50 | -$26.78 | **1** | 0 | 28.1% |
| 5 | `TRANCHE_40_60` | 40% at 693-694, 60% at 704 | -$18.22 | -$13.00 | -$54.72 | **1** | 0 | 18.8% |
| 6 | `PREEMPT_691_692` | Advance pre-emption to 691-692 | -$70.27 | -$71.00 | -$92.45 | **1** | 0 | 12.5% |
| 7 | `PREEMPT_692_693` | Advance pre-emption to 692-693 | -$70.27 | -$71.00 | -$92.45 | **1** | 0 | 12.5% |
| 8 | `DYNAMIC_PREEMPT` | Trigger early sell on price decay | -$100.70 | -$118.00 | -$136.11 | **1** | 0 | 10.9% |
| 9 | `ADVERSARIAL_PORTFOLIO` | Combined Dynamic + Depth + Ratio | -$123.86 | -$142.00 | -$153.20 | **1** | 0 | 3.1% |

---

## 3. Forensic Analysis: Why V44 is Near-Pareto Optimal

1. **Harvest Transit Latency:** In Kagriculture, mature crops harvested by farm hands take 1–3 steps to be physically hauled and deposited into the farm shed. Moving the pre-emption window earlier (Steps 691–692) truncates the harvest transit pipeline, causing fewer units to be liquidated at peak price.
2. **Order Book Depth & The 50% Threshold:** Sizing the initial tranche at 50% strikes the mathematical balance between extracting liquidity before the opponent tsunami dump (Steps 696–698) and avoiding self-induced price collapse. Sizing at 60% causes the trailing units of the order to suffer severe slippage ($-\$23.00/\text{unit}$ on Strawberry).
3. **The Saturated Baseline Win Rate:** Because V44 already wins 100.0% of evaluated baseline matches (including rescuing the near-tie loss on Seed 249657 vs `E2_A7`), there were 0 baseline losses in the DEV cohort available for rescue. Any degradation in cash directly risks a casualty.

---

## 4. Phase Advancement Verdict

In accordance with Section Phase 3 and Section 48:
* No candidate strategy achieved $> +$50 mean cash delta over V44 with 0 casualties.
* The formal verdict is **`V45_MARKET_ALPHA_NOT_ROBUST`**.
* The program moves to Phase 7 (Shadow Mode) to verify safety and governance before finalizing the research package.
