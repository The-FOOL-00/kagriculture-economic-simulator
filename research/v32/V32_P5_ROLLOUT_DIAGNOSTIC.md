# V32 P5 — ROLLOUT DIAGNOSTIC: TEACHER-FORCED VS FREE-RUNNING

## 1. EXPERIMENT DESIGN & PROTOCOL

In accordance with Section 8 of the V32 P5 Protocol, we evaluated the canonical P4 Arm 1 checkpoint (`results/v32_p4_arm1_balanced.npz`, SHA16 `34587d45cd5ed4d9`) in two paired modes on identical development screen seeds (`249675–249679`) against opponent `E0_V3` (`submission_Vj_kc_v3.tar.gz`):

1. **Mode A — Teacher-Forced (Supervised Fidelity)**:
   - At each step $t \in [0, 719]$, the model observes the ground-truth teacher state $s_t^T$ and historical teacher trajectory.
   - The model predicts action $\hat{a}_t$.
   - $\hat{a}_t$ is recorded and compared to the expert action $a_t^T$.
   - $\hat{a}_t$ is discarded, and the rollout advances using $a_t^T \to s_{t+1}^T$.
   - This measures pure supervised action fidelity under the demonstration distribution.

2. **Mode B — Free-Running (Closed-Loop Rollout)**:
   - At each step $t \in [0, 719]$, the model observes its own resulting state $s_t^P$.
   - The model predicts action $\hat{a}_t^P$, which is executed in the simulator.
   - The simulator advances to $s_{t+1}^P$.
   - This measures actual deployment stability and error propagation.

---

## 2. EMPIRICAL RESULTS SUMMARY

| Seed | Teacher Cash | Mode A (Teacher-Forced) Full-Action Accuracy | Mode B (Free-Running) Terminal Cash | First Action Divergence | First State Divergence ($\|s^P - s^T\| > 0$) | First Economic Divergence ($\Delta > \$10$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **249675** | $59,603 | 6.12% (44/720) | $0.00 | Step 0 | Step 1 | Step 2 |
| **249676** | $80,884 | 5.84% (42/720) | $0.00 | Step 0 | Step 1 | Step 2 |
| **249677** | $142,499 | 5.84% (42/720) | $325.00 | Step 0 | Step 1 | Step 2 |
| **249678** | $66,200 | 6.12% (44/720) | $7.00 | Step 0 | Step 1 | Step 2 |
| **249679** | $71,274 | 4.73% (34/720) | $31.00 | Step 0 | Step 1 | Step 2 |
| **MEAN** | **$84,092** | **5.73%** | **$72.60** | **Step 0** | **Step 1** | **Step 2** |

---

## 3. KEY SCIENTIFIC FINDINGS

### 3.1 The Catastrophic Mode A vs Mode B Economic Gap
- While the teacher averages **$84,092**, the free-running policy collapses to **$72.60 mean cash** (with 2 of 5 seeds terminating at exactly $0.00 and zero wins).
- In Mode A, full exact-action match is only ~5.73%, indicating that even under teacher forcing, exact sequence matching across all 11 action heads simultaneously is rare.

### 3.2 The Step 0 Unit Head Omission
Forensic inspection of Step 0 reveals the exact mechanism:
- **Teacher Step 0 Action**:
  ```python
  {'farmer': ['PASS'], 'hands': [], 'market': [['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]}
  ```
- **P4 Arm 1 Step 0 Action**:
  ```python
  {'farmer': ['WEST'], 'hands': [], 'market': [['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]}
  ```
- In P4 Arm 1, critical weighting ($\lambda_{crit} = 50.0$) was applied **exclusively to market slots 0 and 1**. The market wash was learned with 100% fidelity.
- However, the farmer unit head was **unweighted**. Across 138,048 training transitions, `PASS` for the farmer is extremely rare (only 0.139% at step 0). The model assigned **54.64% probability to `WEST`** and only **4.46% to `PASS`**!
- As a direct result, the farmer moved West to (4, 5) at Step 0 instead of remaining at (5, 5).

### 3.3 The Instantaneous Covariate Shift at Step 1
- At Step 1, the model observes a novel state: farmer at (4, 5) with $3000 cash.
- Under this shifted observation, the normalized feature distance jumps immediately to **21.376**.
- The model fails to emit the critical 5-hire and livestock purchase (`['NORTH']` + 5 HIREs + 2 cows + 2 sheep), instead emitting `BUILD_PASTURE` and random product orders.
- No workers are hired. No animals are purchased. The economy is permanently broken on Step 1.
