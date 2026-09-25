# V32 P6 — CLOSED-LOOP EVALUATION & METRIC SYNTHESIS

## 1. EXECUTIVE SUMMARY

This report synthesizes all closed-loop metrics for **Phase V32 P6 Arm 2 (Targeted Farmer-Head Rebalancing + Semantic Action Mask)** evaluated across the full 120-leg development screen (Seeds `249675–249684` $\times$ 6 opponents $\times$ 2 seats) in strict accordance with the preregistered V32 P6 protocol.

---

## 2. COMPREHENSIVE CLOSED-LOOP METRICS (120 LEGS)

### 2.1 Opening Action & Early Choreography Metrics
- **Step-0 Wash Execution Rate**: **120 / 120 (100.0%)** (Shape `[BUY_PRODUCT WHEAT, SELL WHEAT]` executed).
- **Step-0 Farmer PASS Rate**: **120 / 120 (100.0%)** (Farmer stays at shed coordinate `[4, 4]`).
- **Step-1 Farmer NORTH Rate**: **120 / 120 (100.0%)** (Farmer moves North to `[4, 3]`).
- **Step-1 5-Hand Hiring Rate**: **120 / 120 (100.0%)** (Mean hires: **5.00 / 5.00**).
- **Step-2 Farmer SOUTH Rate**: **120 / 120 (100.0%)** (Farmer moves South back to shed tile `[4, 4]`).
- **Step-2 Illegal PICKUP Rate**: **0 / 120 (0.0%)** (Completely eliminated).

### 2.2 First Divergence Statistics
- **First Action Divergence ($t_{\text{act}}$)**:
  - Median: **Step 3** (Predicts `['SOUTH']` from `[4, 4]` instead of teacher's `['PICKUP', 'SHEEP']`).
  - 10th Percentile: Step 3
  - 90th Percentile: Step 3
  - Prior Phase Comparison: **Delayed by +1 step** (Step 2 in P5 $\to$ Step 3 in P6).
- **First State Divergence ($t_{\text{state}}$)**:
  - Median: **Step 3**
  - Prior Phase Comparison: **Delayed by +1 step** (Step 2 in P5 $\to$ Step 3 in P6).
- **First Economically Meaningful Divergence ($t_{\text{econ}}$)**:
  - Median: **Step 3** (Failure to load livestock into inventory prevents subsequent pasture stocking).

### 2.3 Terminal Economics (120 Legs)
- **Mean Terminal Cash**: **$0.07**
- **Median Terminal Cash**: **$0.00**
- **Standard Deviation**: **$0.82**
- **Minimum Cash**: **$0.00**
- **Maximum Cash**: **$9.00**
- **Wins**: **0 / 120 (0.0%)**
- **Losses**: **120 / 120 (100.0%)**
- **Ties**: **0 / 120 (0.0%)**

### 2.4 Tail Safety & Starvation Audit
- **Worst 1% Cash**: **$0.00**
- **Worst 5% Cash**: **$0.00**
- **Wage-Drain Starvation Rate**: **100.0%** (Episodes suffer wage exhaustion by Step 24–41).
- **Choreography Drift**: When livestock pickup is skipped at Step 3, the policy wanders away from the shed; the 5 hired workers drain wages without active agricultural revenue.

---

## 3. MULTI-ARM COMPARATIVE MATRIX (120 LEGS EACH)

| Metric | P4 Arm 1 (Baseline) | P5 Arm 2 (Early Weighting) | P6 Arm 1 (Mask Only) | P6 Arm 2 (Rebalanced + Mask) | Status / Trend |
|:---|:---:|:---:|:---:|:---:|:---|
| **Step-0 Wash** | 100.0% | 100.0% | 100.0% | **100.0%** | Preserved |
| **Step-0 PASS** | 0.0% | 100.0% | 100.0% | **100.0%** | Preserved |
| **Step-1 NORTH** | 0.0% | 100.0% | 100.0% | **100.0%** | Preserved |
| **Step-1 Hires** | 0.00 | 5.00 | 5.00 | **5.00** | Preserved |
| **Step-2 SOUTH** | 0.0% | 0.0% | 0.0% (100% NORTH) | **100.0% (120/120)** | **Completely Repaired** |
| **Step-2 PICKUP** | 0.0% | 100.0% | 0.0% | **0.0% (0/120)** | **Eliminated** |
| **Median $t_{\text{act}}$** | Step 0 | Step 2 | Step 2 | **Step 3** | **Delayed to Step 3** |
| **Mean Cash** | $108.39 | $2.94 | $0.03 | **$0.07** | Flat zero regime |
| **Median Cash** | $0.50 | $0.00 | $0.00 | **$0.00** | Flat zero regime |
| **Win Rate** | 0.0% | 0.0% | 0.0% | **0.0%** | 0 wins |

---

## 4. SCIENTIFIC INTERPRETATION

1. **Step-2 Repair Confirmed**: The combination of simulator-grounded semantic masking and targeted class-weighting ($\lambda_{s2} = 50.0$) achieves 100.0% fidelity on the Step-2 decision across all 120 evaluation legs.
2. **Sequential Horizon Shift Verified**: Repairing Step 2 does not unlock economic compounding because the divergence immediately shifts to Step 3 ($t_{\text{act}} = 3$), where the policy fails to execute livestock pickup.
3. **P6 Decision Verdict**: Meets Gate 2 (First Divergence Delay past Step 2), but fails Gate 3 (Economic Compounding Gate). Concludes as **P6 PARTIAL**.
