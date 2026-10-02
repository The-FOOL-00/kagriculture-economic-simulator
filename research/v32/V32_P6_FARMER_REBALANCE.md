# V32 P6 — ARM 2 TRAINING SPECIFICATION: TARGETED FARMER-HEAD REBALANCING

## 1. PURPOSE & SCIENTIFIC RATIONALE

In accordance with Section 17 and Section 18 of the **V32 P6 Protocol**, **P6 Arm 2** implements targeted early farmer-head rebalancing to eliminate the Step-2 action error.

Our preceding diagnostic findings established:
1. **On-Manifold Error**: The policy arrives at Step 2 in a state geometrically identical to the expert trajectory (`V32_P6_STEP2_RECONSTRUCTION.md`).
2. **Logit Ranking on Teacher State**:
   - Rank 1: `PICKUP` (+8.204 logit, 81.60%) — Simulator Invalid
   - Rank 2: `NORTH` (+6.599 logit, 16.40%) — Legal Move
   - Rank 3: `SOUTH` (+4.487 logit, 1.98%) — Expert Action
3. **Failure of Mask-Only Intervention (Arm 1)**:
   Applying the semantic mask alone suppressed `PICKUP`, but immediately promoted `NORTH` (100% of legs), stranding the farmer at [4, 0] and collapsing terminal cash to $0.03 (`V32_P6_MASK_EVAL.md`).
4. **Data Choreography Ground Truth**:
   Across all 192 training demonstrations, Step 2 is **100.0% `SOUTH`** (192 / 192).

Therefore, the farmer opcode head must be explicitly rebalanced to elevate `SOUTH` above `NORTH` and `PICKUP` at Step 2.

---

## 2. MATHEMATICAL FORMULATION

The objective function adds a dedicated critical weighting term for the Step-2 farmer opcode while preserving the validated P4/P5 losses:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{unit}} + \mathcal{L}_{\text{mkt}} + \lambda_{\text{crit}} \cdot \mathcal{L}_{\text{crit}}^{s=0} + \lambda_{\text{early}} \cdot \mathcal{L}_{\text{early}}^{s \in [1, 10]} + \lambda_{s2} \cdot \mathcal{L}_{\text{farmer}}^{s=2}$$

Where:
- $\mathcal{L}_{\text{unit}} = \mathcal{L}_{u\_op} + \mathcal{L}_{u\_arg} + \mathcal{L}_{u\_qty}$ (Standard global BC loss over all units).
- $\mathcal{L}_{\text{mkt}} = \mathcal{L}_{m\_op} + \mathcal{L}_{m\_item} + \mathcal{L}_{m\_qty}$ (Standard global BC loss over all market slots).
- $\mathcal{L}_{\text{crit}}^{s=0} = \mathcal{L}_{\text{farmer}}^{s=0} + \mathcal{L}_{\text{wash}}^{s=0}$ with $\lambda_{\text{crit}} = \mathbf{50.0}$ (Guarantees Step-0 market wash and farmer `PASS`).
- $\mathcal{L}_{\text{early}}^{s \in [1, 10]}$ with $\lambda_{\text{early}} = \mathbf{10.0}$ (Guarantees Step-1 farmer `NORTH`, 5-hand hiring, livestock purchase, and steps 3–10 operations).
- $\mathcal{L}_{\text{farmer}}^{s=2} = \text{CrossEntropy}(u\_op[0], \text{SOUTH})$ with $\lambda_{s2} = \mathbf{50.0}$ (Forces farmer opcode head at Step 2 to prioritize `SOUTH`).

---

## 3. OPTIMIZATION HYPERPARAMETERS

| Parameter | Value | Rationale |
|:---|:---:|:---|
| **Base Model** | P3/P4/P5 MLP Trunk (157 dims $\to$ 256 $\to$ 256) | Strict architecture freeze |
| **Initialization** | `results/v32_p5_arm2_early_weighting.npz` | Warm-start from verified Step 0/1 baseline |
| **Optimizer** | Adam ($\beta_1 = 0.9, \beta_2 = 0.999$) | Standard |
| **Learning Rate** | $3 \times 10^{-4}$ | Smooth fine-tuning |
| **Batch Size** | 128 | Standard |
| **Epochs** | 10 | Bounded convergence |
| **Grad Clip** | 1.0 | Stability |
| **Probe Targets** | Step-0 Wash = 240/240, Step-0 Pass = 240/240, Step-1 North = 240/240, Step-2 South = 240/240 | Strict opening fidelity |

---

## 4. CHECKPOINT ARTIFACT

Output artifact path: `results/v32_p6_arm2_rebalanced.npz`.
