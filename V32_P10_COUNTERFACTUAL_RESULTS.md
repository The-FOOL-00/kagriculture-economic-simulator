# V32 P10 — COUNTERFACTUAL RESULTS REPORT: RESIDUAL SCREENING & CAUSAL EVALUATION
**Experiment ID:** `EXP-V32-P10-03` / `EXP-V32-P10-04`  
**Phase:** V32 P10  
**Date:** 2026-09-23  
**Status:** COMPLETE — RIGOROUS REJECTION & QUARANTINE OF ALL RESIDUAL CANDIDATES  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. EXECUTIVE SUMMARY

The centerpiece of Phase 10 was the exact, simulator-grounded counterfactual evaluation of candidate local residuals layered on top of frozen `A7`. Every candidate was evaluated in paired head-to-head matches against the incumbent control across development seeds.

In total, 6 distinct candidate mechanisms were screened:
1. `R01`: `OPPONENT_SELL_PREEMPT` (Market Front-Running Preemption)
2. `R02`: `MARKET_QUANTITY_ADJUST` (Global Glut Sale Trimming)
3. `R02_B`: `OPPONENT_GLUT_TRIM` (Opponent-Specific Glut Deferral)
4. `R03`: `LIQUIDITY_PROTECTION` (Low-Cash Discretionary Capital Guard)
5. `R05`: `LOCAL_LABOR_PATCH` (Low-Cash Labor Throttle)
6. `R07`: `TERMINAL_LOCAL_PATCH` (Terminal Residual Shed Liquidation)

---

## 2. MASTER COUNTERFACTUAL SCREENING SCORECARD

| Candidate ID | Target Regime | Test Panel | Active Legs | Total Acts | Mean Paired Δ (All) | Mean Paired Δ (Active) | Median Paired Δ | Worst-Case Δ | Gate Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`R01`** | Opponent Sell Pressure | Dev (20 legs) | 20 / 20 | 193 | **-$348.35** | -$348.35 | -$298.00 | **-$1,056.00** | **REJECTED (FAIL G3, G4, G5)** |
| **`R02`** | Market Oversupply | Dev (20 legs) | 20 / 20 | 238 | **-$32.35** | -$32.35 | -$3.50 | **-$246.00** | **REJECTED (FAIL G3, G4)** |
| **`R02_B`** | Opponent Saturated Dump | Dev (20 legs) | 15 / 20 | 17 | +$9.30 | +$12.40 | +$0.00 | -$12.00 | *Screened to Phase 6* |
| **`R02_B`** | Fresh Seeds Validation | Fresh Dev (40 legs) | 24 / 40 | 36 | +$11.10 | +$18.50 | +$0.00 | **-$489.00** | **REJECTED (FAIL G4 Tail Risk)** |
| **`R03`** | Low Liquidity Stress | Dev (20 legs) | 20 / 20 | 40 | **+$0.00** | +$0.00 | +$0.00 | +$0.00 | **QUARANTINED (REDUNDANT)** |
| **`R05`** | Tight Runway Labor | Dev (20 legs) | 0 / 20 | 0 | **+$0.00** | +$0.00 | +$0.00 | +$0.00 | **QUARANTINED (REDUNDANT)** |
| **`R07`** | Terminal Window | Dev (20 legs) | 0 / 20 | 0 | **+$0.00** | +$0.00 | +$0.00 | +$0.00 | **QUARANTINED (REDUNDANT)** |

---

## 3. MECHANISM-BY-MECHANISM CAUSAL ATTRIBUTION

### 1. R01 (Opponent Sell Preempt): Severe Negative Regression
- **Result:** -$348.35 mean paired delta, with catastrophic -$1,056.00 worst case.
- **Causal Failure:** Injecting additional market sales whenever opponent activity was detected disrupted A7's carefully timed downstream liquidity schedule. Preemptive dumping lowered subsequent clearing prices for A7's own planned large melon and milk orders, costing far more in suppressed revenues than was saved in front-running.
- **Verdict:** **PERMANENTLY QUARANTINED**.

### 2. R02 & R02_B (Glut Sale Trimming): False-Positive Trap & Severe Tail Vulnerability
- **Initial Discovery:** In R02_B on historical dev seeds, restricting trimming to verified opponent dumps yielded a small apparent gain (+9.30 mean, -$12 worst).
- **Fresh Seed Exposure (249685–249694):** When exposed to 10 unseen development seeds across 40 legs, R02_B collapsed into severe downside:
  - Seed 249687 (Seat 0 & 1): **-$489.00 paired loss**.
- **Causal Failure:** Holding 50% of the sale quantity deferred critical working capital needed at that exact turn for purchasing seeds and fertilizer. The delayed compounding cost hundreds of dollars in lost crop cycles.
- **Verdict:** **PERMANENTLY QUARANTINED**.

### 3. R03, R05, R07: Absolute Redundancy with Frozen A7
- **R03 (Capital Guard):** A7 already avoids discretionary capital purchases when liquid cash is low; suppressing orders produced exactly $0.00 delta across all 20 legs.
- **R05 (Labor Guard):** A7 never schedules `HIRE` orders when cash $< \$100$ and workers $\ge 6$. Zero activations.
- **R07 (Terminal Liquidation):** A7's built-in Step 718 liquidation already dumps 100.0% of shed inventory into market orders. Zero residual shed goods remained at turn 718. Zero activations.
- **Verdict:** **CONFIRMED REDUNDANT**.

---

## 4. FORMAL ACCEPTANCE GATE VERDICTS (G1–G9)

```
========================================================================================
Gate   Requirement                  R01      R02     R02_B     R03      R05      R07
----------------------------------------------------------------------------------------
G1     Legality (0 illegal acts)    PASS     PASS     PASS     PASS     PASS     PASS
G2     Baseline Validity            PASS     PASS     PASS     PASS     PASS     PASS
G3     Economic Delta >= +$50       FAIL     FAIL     FAIL     FAIL     FAIL     FAIL
G4     Downside Loss <= $50         FAIL     FAIL     FAIL     PASS     PASS     PASS
G5     Robustness >= 60% pos        FAIL     FAIL     FAIL     FAIL     FAIL     FAIL
G6     Non-Duplication              PASS     PASS     PASS     FAIL     FAIL     FAIL
G7     Verifiable Causality         PASS     PASS     PASS     FAIL     FAIL     FAIL
G8     Runtime Budget               PASS     PASS     PASS     PASS     PASS     PASS
G9     Fallback Invariant           PASS     PASS     PASS     PASS     PASS     PASS
----------------------------------------------------------------------------------------
FINAL PROMOTION DECISION            REJECT   REJECT   REJECT   REJECT   REJECT   REJECT
========================================================================================
```

Not a single candidate residual passes all acceptance gates. Every proposed deviation either degrades A7's baseline performance, exposes the agent to intolerable tail risk, or is completely redundant with A7's native capabilities.
