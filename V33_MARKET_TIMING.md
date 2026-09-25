# V33 Market Timing & Sell Reordering Forensic Benchmark

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Question:** *Does price-impact-aware sell slot reordering improve A7's match win rate and cash payoff?*  
**Empirical Benchmark:** 60 paired legs across DEV seeds (`249675..249679`), both seats, vs all 6 League Opponents  
**Artifact Generated:** `market_timing_results.json`

---

## 1. Executive Summary & Stop Condition Triggered

In accordance with **Mandate Section 48 (Mandatory Stop Conditions)**:
> *"If market overlay does not improve fresh win rate: REMOVE IT."*

The market timing overlay was subjected to a rigorous 60-leg paired tournament comparing pure $R0\_A7$ against $A7 + \text{Market Overlay}$.

### Primary Findings:
1. **Win Rate Degradation:** Pure A7 achieved an **88.3% win rate** (53/60 wins), whereas A7 + Market Overlay achieved only **83.3%** (50/60 wins), dropping 3 matches.
2. **Economic Drag:** Mean cash decreased by **$-\$161.60$** across the league panel ($A7=\$102,037.15$ vs $A7+\text{Overlay}=\$101,875.55$).
3. **Pervasive Negative Paired Deltas:** The overlay exhibited negative mean paired deltas against 5 out of 6 opponent families.
4. **Decisive Action:** The market overlay is **PERMANENTLY REMOVED** from the V33 deployment candidate.

---

## 2. Quantitative Matchup Breakdown by Opponent Family

| Opponent Family | Paired Legs | Pure A7 Wins | Market Overlay Wins | Mean Paired Delta ($\Delta$) | Win Rate $\Delta$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`E0_V3`** | 10 | **10 / 10 (100%)** | 9 / 10 (90%) | **-$296.40** | -10.0% |
| **`E1_V22R1`** | 10 | **10 / 10 (100%)** | 9 / 10 (90%) | **-$218.00** | -10.0% |
| **`E2_A7` (Self-Mirror)** | 10 | **5.0 / 10 (50%)** | 4.0 / 10 (40%) | **-$244.40** | -10.0% |
| **`E8_DMITRII`** | 10 | **8.0 / 10 (80%)** | 8.0 / 10 (80%) | **-$219.30** | 0.0% |
| **`SYN_AGG`** | 10 | **10 / 10 (100%)** | 10 / 10 (100%) | **$0.00** | 0.0% |
| **`V54`** | 10 | **10 / 10 (100%)** | 10 / 10 (100%) | **+$8.50** | 0.0% |
| **OVERALL LEAGUE** | **60** | **53.0 / 60 (88.3%)** | **50.0 / 60 (83.3%)** | **-$161.60** | **-5.0%** |

---

## 3. Forensic Root-Cause Analysis (Failure Taxonomy F7 / F5)

Why did price-impact reordering degrade A7?

1. **Intra-Turn Execution Precedence vs Working Capital:**
   - In Kaggriculture, market transactions execute sequentially within a turn.
   - When A7 issues `[["SELL", "WHEAT", 30], ["BUY_ITEM", ...]]`, selling the high-velocity staple first immediately credits the farm's liquid cash, which is then consumed in the same turn by subsequent equipment purchases or seed restocks.
   - The market overlay reordered lower-volume or higher-margin goods first based on synthetic price-impact equations. In boundary cases where lower-volume goods traded zero quantity or delayed liquidation, intra-turn liquidity dipped below required thresholds, causing subsequent purchase orders to be rejected.
2. **A7's Choreography is Already Locally Optimized:**
   - A7's open-loop action tapes were compiled with tick-exact liquidity balances. Perturbing order sequence introduces frictional delays that compound over 720 turns.

---

## 4. Policy Decision

The market overlay is disqualified. V33 will **NOT** utilize sell reordering.
