# V32 P6 — EXACT STEP-2 LOGIT FORENSICS REPORT

## 1. PURPOSE & METHODOLOGY

In accordance with Section 7 of the **V32 P6 Protocol**, this document provides exact logit, probability, and margin telemetry for the farmer unit action head (`u_op[0]`) evaluated on the canonical teacher Step-2 state ($s_2^T$) using the frozen P5 Arm 2 checkpoint (`results/v32_p5_arm2_early_weighting.npz`).

---

## 2. FARMER OPCODE HEAD LOGIT BREAKDOWN

Evaluated on exact input features $x(s_2^T)$ and unit context $uc(s_2^T, \text{farmer})$:

| Rank | Opcode Name | Codec ID | Raw Logit | Softmax Probability | Cumulative Prob | Simulator Legality at [4, 3] |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **1** | **`PICKUP`** | 16 | **+8.204** | **81.60%** | 81.60% | **ILLEGAL (Not Shed Adjacent)** |
| **2** | **`NORTH`** | 1 | **+6.599** | **16.40%** | 98.00% | **LEGAL** (Moves to [4, 2]) |
| **3** | **`SOUTH` (Expert)** | 2 | **+4.487** | **1.98%** | 99.98% | **LEGAL** (Returns to Shed [4, 4]) |
| 4 | `BUILD_PASTURE` | 11 | -0.643 | 0.01% | 99.99% | LEGAL (Empty tile) |
| 5 | `PLANT` | 15 | -2.518 | 0.00% | 100.00% | ILLEGAL (No seeds in inv) |
| 6 | `WEST` | 4 | -3.072 | 0.00% | 100.00% | LEGAL (Moves to [3, 3]) |
| 7 | `PLACE` | 17 | -3.870 | 0.00% | 100.00% | ILLEGAL (Not on structure/shed) |
| 8 | `EAST` | 3 | -3.964 | 0.00% | 100.00% | LEGAL (Moves to [5, 3]) |
| 9 | `WATER` | 6 | -4.886 | 0.00% | 100.00% | ILLEGAL (No plant) |
| 10 | `PASS` | 0 | -5.586 | 0.00% | 100.00% | LEGAL |
| 11 | `CARE` | 14 | -5.744 | 0.00% | 100.00% | ILLEGAL (No animal) |
| 12 | `FERTILIZE` | 8 | -6.384 | 0.00% | 100.00% | ILLEGAL (No plant) |
| 13 | `HARVEST` | 7 | -6.428 | 0.00% | 100.00% | ILLEGAL (No plant/animal) |
| 14 | `FEED` | 12 | -6.599 | 0.00% | 100.00% | ILLEGAL (No animal) |
| 15 | `COLLECT_FERTILIZER` | 13 | -8.361 | 0.00% | 100.00% | ILLEGAL (No animal) |
| 16 | `DIG` | 9 | -8.653 | 0.00% | 100.00% | ILLEGAL (Tile is None) |
| 17 | `DROP` | 5 | -10.155 | 0.00% | 100.00% | ILLEGAL (Not Shed Adjacent) |
| 18 | `BUILD_COOP` | 10 | -11.743 | 0.00% | 100.00% | LEGAL (Empty tile) |

---

## 3. KEY METRICS & ANALYSIS

- **Logit Margin ($\text{Logit}_{\text{PICKUP}} - \text{Logit}_{\text{SOUTH}}$)**: **+3.717**
- **Probability Ratio ($P(\text{PICKUP}) / P(\text{SOUTH})$)**: **41.2 : 1**
- **Entropy ($H(u\_op)$)**: **0.542 nats**
- **Margin between Top Unmasked Legal Action (`NORTH`) and Expert (`SOUTH`)**:
  $$\text{Logit}_{\text{NORTH}} - \text{Logit}_{\text{SOUTH}} = +6.599 - 4.487 = \mathbf{+2.112}$$
  $$P(\text{NORTH} \mid \text{mask(PICKUP)}) = \frac{e^{6.599}}{e^{6.599} + e^{4.487} + \dots} \approx \mathbf{89.1\%}$$
  $$P(\text{SOUTH} \mid \text{mask(PICKUP)}) \approx \mathbf{10.8\%}$$

---

## 4. SCIENTIFIC IMPLICATIONS

1. **`PICKUP` Overwhelmingly Dominates**:
   The model does not "barely lose" the decision. `PICKUP` is favored with 81.6% probability due to the strong correlation between "animals recently bought into shed" and `PICKUP` operations in the training set.
2. **Mask-Only Intervention is Mathematically Insufficient**:
   Because `NORTH` is Rank 2 (16.4%) and is a completely legal movement operation, simply applying an exact semantic mask to remove `PICKUP` will promote `NORTH` to Top-1.
   Moving `NORTH` takes the farmer to `[4, 2]`, driving the farmer further away from the shed.
   Therefore, **an exact semantic mask alone will NOT repair `SOUTH`**. Targeted farmer-head rebalancing or hard-negative loss is mandatory.
