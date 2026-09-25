# V32 P12 Supervised Option Selector Report (P12-06 & P12-08)

## Executive Summary

Phase P12 hypothesizes that rather than relying on heavy online forward search simulation, a high-precision supervised neural network classifier can learn **WHEN** to trigger a search-validated sparse option directly from observable economic state features ($s_t \in \mathbb{R}^{71}$).

In Experiment **P12-06 (Supervised Option Selector)** and **P12-08 (Multi-Seed Selector Training)**:
1. We trained the `OptionClassifierNetwork` (a calibrated MLP mapping 71-dim S2 features to 7 discrete option classes) across 3 independent random seeds ($42, 137, 2026$) on the 60 search targets with positive advantage and negative A7 control points.
2. In closed-loop tournament play across 40 match legs (20 legs per policy, evaluating both Player Seat 0 and Player Seat 1 vs `E2_A7` and `E8_DMITRII`), the **Supervised Option Selector achieved 100% behavioral alignment with the Oracle Search Gated Controller**.
3. **Closed-Loop Performance:**
   - Mean Cash: **$102,177.60**
   - Paired Mean Delta vs A7: **+$7,227.20**
   - Minimum Delta (Worst Case): **+$0.00** (Zero negative legs!)
   - False Positive Rate: **0.0%**
   - Inference Latency: **< 0.15 ms** per tick (orders of magnitude faster than online lookahead).

---

## 1. Network Architecture & Training Protocol

- **Architecture:** 71-dim Input $\to$ Dense(128) + LayerNorm + ReLU + Dropout(0.1) $\to$ Dense(64) + LayerNorm + ReLU $\to$ Dense(7) Logits.
- **Output Classes:**
  - `0: FOLLOW_A7` (Mandatory Protected Default)
  - `1: O01 EXPAND_LAND`
  - `2: O02 CROP_EXPANSION_MELON`
  - `3: O03 LIQUIDATE_SURPLUS`
  - `4: O04 OPPORTUNISTIC_SELL`
  - `5: O05 PRESERVE_CASH`
  - `6: O06 SELECTIVE_PREEMPT_SELL`
- **Loss Function:** Weighted Cross-Entropy scaled by local advantage $\Delta$:
  $$w_i = 1.0 + \min(10.0, \Delta_i / 1000.0)$$
- **Inference Invariant:** Strict confidence threshold $\tau = 0.65$. If $\max_{c \ne 0} P(c) < \tau$, the selector fails closed to `0: FOLLOW_A7`.

---

## 2. Multi-Seed Training Convergence (P12-08)

| Seed | Final Loss | Accuracy (%) | Option Precision (%) | Option Recall (%) | False Positive Rate (%) | Checkpoint |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | 0.5742 | 71.7% | **100.0%** | 70.0% | **0.0%** | `supervised_selector_seed_42.pt` |
| **137** | 0.5356 | 70.0% | **100.0%** | 66.7% | **0.0%** | `supervised_selector_seed_137.pt` |
| **2026** | 0.5373 | 70.0% | **100.0%** | 63.3% | **0.0%** | `supervised_selector_seed_2026.pt` |

*Finding: Across all three seeds, Option Precision is exactly 100.0% and False Positive Rate is 0.00%. The model never triggers an option on a negative or inappropriate state.*

---

## 3. Closed-Loop Tournament Evaluation (P12-06)

Evaluated across 20 mirrored match legs per policy (Seeds 249635, 249636, 249637, 249675, 249676; Seats 0 and 1; Opponents `E2_A7` and `E8_DMITRII`):

| Policy | Mean Cash ($) | Median Cash ($) | Paired Mean $\Delta$ vs A7 ($) | Worst-Case $\Delta$ ($) | Win Rate vs Opponents (%) | Option Activations |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A7 Baseline** | $94,950.40 | $94,087.00 | +$0.00 | +$0.00 | 25.0% | 0 / 20 |
| **A7 + Search Gated** | **$102,177.60** | **$101,314.00** | **+$7,227.20** | **+$0.00** | **40.0%** | 10 / 20 |
| **A7 + Supervised Selector** | **$102,177.60** | **$101,314.00** | **+$7,227.20** | **+$0.00** | **40.0%** | 10 / 20 |

---

## 4. Key Takeaways & Learned Selector Feasibility

1. **Perfect Closed-Loop Alignment:**
   The supervised selector perfectly reproduced all 10 option activations of the oracle search-gated controller across both seats, delivering identical financial alpha (+7,227.20/leg) with zero regressions.
2. **Computational Superiority:**
   While online lookahead takes ~48ms per decision check, the PyTorch MLP inference executes in **0.12ms**, consuming less than 1% of the 1000ms Kaggle step budget.
3. **Fail-Closed Default Preserved:**
   Because all non-qualified states produce probabilities below $\tau = 0.65$, the policy executes A7's deterministic choreography uninterrupted in 100% of non-Bakery games.
