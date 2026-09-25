# V38 Residual Intervention Forensics

**Document ID:** `V38_INTERVENTION_FORENSICS.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Artifact:** `scratch/v38/intervention_forensics.json`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Summary

Forensic accounting was performed on all evaluated macro candidate interventions across 128 decision states. Interventions were classified into:
* **SUCCESSFUL:** Discrete interventions yielding strictly positive terminal advantage ($\Delta \ge +\$50.0$).
* **NEUTRAL:** Interventions with zero or negligible delta ($|\Delta| < \$50.0$), where `TRUST_HEURISTIC` is optimal.
* **HARMFUL:** Interventions producing negative terminal delta ($\Delta < 0$).

Out of 128 states, **22 states (17.2%)** demonstrated positive causal alpha, while **106 states (82.8%)** were neutral or degraded by deviation.

---

## 2. Macro Option Empirical Performance Breakdown

| Macro Option | Evaluations | Positive Alpha Rate (%) | Mean Terminal Delta | Max Alpha Observed | Min Delta Observed | Causal Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`0: TRUST_HEURISTIC`** | 128 | **100.0%** | **+$0.00** | $0.00 | $0.00 | **Optimal default baseline** |
| **`1: EXPAND_LAND`** | 28 | **28.6%** | -$4,572.71 | **+$11,179.00** | -$25,950.00 | High-alpha, high-risk window |
| **`2: HIRE_WORKER`** | 30 | **0.0%** | -$469.33 | -$144.00 | -$987.00 | **Consistently harmful** (Wage burden) |
| **`3: ANIMAL_EXPANSION`** | 2 | **0.0%** | -$1,189.00 | -$1,189.00 | -$1,189.00 | **Harmful** (Capital lockup & feed drain) |
| **`4: CROP_EXPANSION`** | 24 | **0.0%** | -$826.67 | $0.00 | -$960.00 | **Harmful** (Labor bottlenecks) |
| **`5: SHOP_SUPPLY`** | 46 | **0.0%** | $0.00 | $0.00 | $0.00 | Neutral |
| **`6: SELL_INVENTORY`** | 68 | **11.8%** | -$254.44 | **+$123.00** | -$3,908.00 | Minor tactical value |
| **`8: MARKET_OPPORTUNITY`**| 44 | **0.0%** | $0.00 | $0.00 | $0.00 | Neutral |
| **`10: RECOVERY`** | 128 | **9.4%** | -$17,727.66 | **+$15,241.00** | -$55,600.00 | Extreme distress rescue only |

---

## 3. Forensic Anatomy of Why Most Macro Interventions Fail

1. **`HIRE_WORKER` is an Economic Trap:**
   Hiring an additional farm hand costs $1–$13 up front, but permanently commits $10/day in midnight wages. Unless the hand performs $\ge 2$ high-value watering or harvesting chores every single day, the cumulative wage drag ($10 \times \text{days\_left}$) strictly exceeds the crop value added.
2. **`ANIMAL_EXPANSION` Causes Feed Desynchronization:**
   Buying a cow or sheep without an pre-existing 15-unit wheat cushion drains the shed's wheat stock. When animals go unfed, their milk/wool production drops to zero, turning a $400 investment into a dead asset.
3. **`EXPAND_LAND` is Bimodal:**
   When triggered at Step 288 (Day 12) with liquid cash $> \$2,500$, unlocking Quadrant 1 yields **+$11,179.00** because melons have sufficient time to complete a full 10-day maturation cycle. When triggered at Step 480 (Day 20), there is insufficient time for crops to yield, destroying capital (-$25,950.00).
