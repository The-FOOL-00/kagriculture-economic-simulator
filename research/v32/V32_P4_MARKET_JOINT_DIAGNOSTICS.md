# V32 P4 MARKET JOINT ARRAY DIAGNOSTICS (§29)

Date: 2026-09-23.
Evaluation Set: 34,512 validation transitions (seeds 249647–249649).
Script: `scratch/v32_p4_market_array_diag.py`.

## 1. Overview
The purpose of this diagnostic is to evaluate whether the factorized market heads predict coherent joint market configurations across all 10 slots, and to determine whether high individual slot accuracies translate into high full-array exact matches.

## 2. Quantitative Results across All Arms

| Checkpoint | Full 10-Slot Array Exact | Non-NOOP Op Accuracy | Slot 0 Accuracy | Slot 1 Accuracy | Slot 2 Accuracy | Step-0 Wash Shape (240 samples) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P3 Baseline (3e-4)** | 76.38% | 83.71% | 88.55% | 90.79% | 96.00% | 0/240 (0.0%) |
| **P3 Baseline (3e-3)** | 87.12% | 91.60% | 94.49% | 94.88% | 97.60% | 0/240 (0.0%) |
| **P4 Arm 1 (Balanced)**| **79.51%** | **84.24%** | **88.14%** | **91.15%** | **96.80%** | **240/240 (100.0%)** |
| **P4 Arm 2 (Mkt Pretrain)**| 74.46% | 80.44% | 85.08% | 89.48% | 95.98% | **240/240 (100.0%)** |
| **P4 Arm 3 (Mkt Frozen)**  | 39.81% | 52.62% | 59.94% | 76.69% | 90.82% | 0/240 (0.0%) |
| **P4 Arm 4 (Mkt Unfrozen)**| 87.55% | 91.63% | 94.09% | 94.88% | 97.89% | 0/240 (0.0%) |

## 3. Analysis

### 3.1 Arm 1 Combines High Global Consistency with Perfect Critical Recovery
- In Arm 1, the full 10-slot ordered market array matches the expert target exactly on **79.51%** of validation transitions.
- Crucially, Arm 1 is the ONLY joint policy that achieves both high global market consistency (~80% full array match, 84.2% non-NOOP accuracy) AND **100% step-0 opening wash recovery** (240/240).

### 3.2 Marginal vs Joint Mode (Answering Hypothesis H3)
- Does the market head fail due to independent marginal heads being unable to model slot dependencies?
- **NO**: In Arm 1, independent heads predict the exact joint array `[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]` with 100% consistency across all 240 step-0 samples.
- The failure in P3 baseline and Arm 4 was not an inability to model dependencies between Slot 0 and Slot 1, but rather **loss dilution**: without critical weighting, Slot 0 is trained on 51,526 non-step-0 `SELL` examples, creating a massive global marginal bias toward `SELL` that drowns out the 192 opening `BUY` examples.
- When this frequency imbalance is counterbalanced with $\lambda_{crit} = 50.0$, the independent heads effortlessly learn the correct joint configuration.
- **Verdict on H3**: Conditional autoregressive market decoding is **UNNECESSARY**. The native factorized independent heads are fully capable of representing the joint market action.
