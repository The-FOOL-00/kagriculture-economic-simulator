# V32 P5 — CLOSED-LOOP EVALUATION & METRIC SYNTHESIS

## 1. EXECUTIVE SUMMARY

This report synthesizes all closed-loop metrics for **P5 Arm 2 (Bounded Early-Horizon Weighting)** across the 120-leg development screen (Seeds `249675–249684` $\times$ 6 opponents $\times$ 2 seats) in accordance with Section 24 of the V32 P5 Protocol.

---

## 2. COMPREHENSIVE CLOSED-LOOP METRICS

### 2.1 Opening Action & Early Choreography Metrics
- **Step-0 Wash Execution Rate**: **120 / 120 (100.0%)** (Shape `[BUY_PRODUCT WHEAT, SELL WHEAT]` executed).
- **Step-0 Farmer PASS Rate**: **120 / 120 (100.0%)** (Farmer stays at shed coordinate [4, 4]).
- **Step-1 Farmer NORTH Rate**: **120 / 120 (100.0%)** (Farmer moves North to [4, 3]).
- **Step-1 5-Hand Hiring Rate**: **120 / 120 (100.0%)** (Mean hires: 5.00 / 5.00).
- **Step-2 Present Hand Count**: **5.00 / 5.00 hands** on the field.

### 2.2 First Divergence Statistics
- **First Action Divergence ($t_{\text{act}}$)**:
  - Median: **Step 2** (commanding `PICKUP COW` at [4, 3] instead of `SOUTH` to shed [4, 4]).
  - 10th Percentile: Step 2
  - 90th Percentile: Step 2
- **First State Divergence ($t_{\text{state}}$)**:
  - Median: **Step 2**
- **First Economically Meaningful Divergence ($t_{\text{econ}}$)**:
  - Median: **Step 2** ($\Delta \text{Cash} > \$10$ due to rejected pickup followed by wander).

### 2.3 State Distribution & Trajectory Drift
- **State Divergence $\|s_t^P - s_t^T\|_2$**:
  - Step 0: **0.000**
  - Step 1: **0.000** (On-manifold, matched)
  - Step 2: **15.22** (Positional pickup mismatch)
  - Step 10: **19.08**
  - Step 72: **18.47**
  - Step 288: **23.49**
  - Step 718: **30.66**
- **Training-Manifold Distance ($\min_{x \in \mathcal{D}} \|s_t^P - x\|_2$)**:
  - Steps 0–1: 0.000 (Within training demonstration manifold)
  - Steps 2–10: 16.79 to 22.68 (Dislocated into unfamiliar observation space)

### 2.4 Terminal Economics (120 Legs)
- **Mean Terminal Cash**: **$2.94**
- **Median Terminal Cash**: **$0.00**
- **Standard Deviation**: **$31.09**
- **Minimum Cash**: **$0.00**
- **Maximum Cash**: **$342.00**
- **Wins**: **0 / 120 (0.0%)**
- **Losses**: **120 / 120 (100.0%)**
- **Ties**: **0 / 120 (0.0%)**

### 2.5 Tail Safety & Failure Mode Audit
- **Worst 1% Cash**: **$0.00**
- **Worst 5% Cash**: **$0.00**
- **Starvation / Wage Collapse**: 100% of episodes undergo full wage exhaustion by Step 24.
- **Resource Lock**: Farmer strands at coordinate [4, 0] at Step 6, repeatedly commanding `WATER` on unworked tiles.
- **Catastrophic Terminal Outcome**: Confirmed.
