# V32 P6 — ECONOMIC RECOVERY & FIRST-DIVERGENCE METRIC REPORT

## 1. EXECUTIVE SUMMARY & ECONOMIC COMPARISON

Phase V32 P6 evaluated whether repairing the Step-2 on-manifold action failure via semantic action masking and targeted farmer-head rebalancing would restore closed-loop economic compounding.

Across the 120-leg development screen (Seeds `249675–249684` $\times$ 6 opponents $\times$ 2 seats), the Step-2 action was repaired to **100.0% execution (`SOUTH`)**, pushing the median first action divergence from Step 2 to Step 3. However, terminal cash remained flat ($0.07 mean, $0.00 median, 0 wins).

| Metric | P4 Arm 1 (Baseline) | P5 Arm 2 (Early-Horizon BC) | P6 Arm 1 (Mask Only) | P6 Arm 2 (Rebalanced + Mask) | Delta (P6 Arm 2 vs P5) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Step-0 Wash Shape** | 100.0% | 100.0% | 100.0% | **100.0%** | 0.0% |
| **Step-0 Farmer PASS** | 0.0% | 100.0% | 100.0% | **100.0%** | 0.0% |
| **Step-1 Farmer NORTH** | 0.0% | 100.0% | 100.0% | **100.0%** | 0.0% |
| **Step-1 Hires (Mean)** | 0.00 | 5.00 | 5.00 | **5.00** | 0.00 |
| **Step-2 Farmer SOUTH** | 0.0% | 0.0% | 0.0% (100% NORTH) | **100.0% (120/120)** | **+100.0%** |
| **Median First Action Divergence** | Step 0 | Step 2 | Step 2 | **Step 3** | **+1 Step Later** |
| **Terminal Cash Mean** | $108.39 | $2.94 | $0.03 | **$0.07** | -$2.87 |
| **Terminal Cash Median** | $0.50 | $0.00 | $0.00 | **$0.00** | $0.00 |
| **Win Rate** | 0.0% | 0.0% | 0.0% | **0.0%** | 0.0% |

---

## 2. THE ANATOMY OF CONTINUED ECONOMIC FAILURE

### 2.1 The Sequential Horizon Shift
The experimental evidence across P4, P5, and P6 reveals a precise mathematical property of feed-forward Behavioral Cloning applied to complex macro-scripts:

$$\text{P4: Failure at Step 1} \xrightarrow{\lambda_{s1} \uparrow} \text{P5: Failure at Step 2} \xrightarrow{\lambda_{s2} \uparrow} \text{P6: Failure at Step 3}$$

1. In P4, the unweighted joint policy failed at Step 1 (predicting `SOUTH` instead of `NORTH` + 5 Hires).
2. In P5, early-horizon weighting ($\lambda_{early} = 10.0$) successfully stabilized Step 0 and Step 1. The model reached Step 2 on the exact teacher manifold, but failed at Step 2 by predicting `PICKUP` prematurely at `[4, 3]`.
3. In P6, targeted Step-2 farmer loss ($\lambda_{s2} = 50.0$) plus semantic masking successfully forced `SOUTH` at Step 2. The farmer arrived at `[4, 4]` (the shed tile) at Step 3, bit-identical to the teacher.
4. However, at Step 3, the unweighted policy predicts `SOUTH` to `[4, 5]` instead of `['PICKUP', 'SHEEP']`.
5. The model simply shifted its point of divergence from Step 2 to Step 3.

### 2.2 The Livestock Pipeline Starvation Mechanism
Why does missing the Step-3 `PICKUP` cause total economic collapse?
- **Capital Outlay at Step 1**: At Step 1, the model correctly hires 5 hands for $500 total, which incurs an ongoing wage liability of **$25 per step** ($5 \times \$5$). It also buys livestock contracts for ~$1,247. Remaining liquid capital: ~$1,005.
- **The Livestock Execution Dependency**: To make this investment pay off, the farmer must immediately retrieve the livestock from the shed at Steps 3 and 4 (`PICKUP SHEEP`, `PICKUP COW`), navigate to empty pasture tiles, build pastures, and place the animals so they begin generating wool, milk, and fertilizer.
- **The Divergence at Step 3**: Because the policy commands `SOUTH` at Step 3 instead of `PICKUP`, the farmer walks south away from the shed with zero livestock in inventory.
- **The Starvation Funnel**:
  - The farmer wanders unproductively across the board (eventually planting melon seeds at `[4, 1]` or `[3, 1]` without watering or harvesting).
  - The 5 hired hands have no livestock to tend and no coordinated crop cultivation schedule.
  - The wage drain continues unabated: $1,005 / $25 = 40.2$ steps.
  - By Step 41, the agent's cash balance hits exactly **$0.00**, and the entire economy starves out.

---

## 3. THEORETICAL IMPLICATIONS FOR THE V32 RESEARCH PROGRAM

1. **Pointwise Loss Weighting Does Not Scale**:
   Individually boosting step weights ($\lambda_{s0}=50$, $\lambda_{s1}=10$, $\lambda_{s2}=50$) successfully pushes the divergence horizon forward by one step at a time, but cannot provide sequence-level structural coherence across a 25-step opening macro.
2. **Feed-Forward Observation Insufficiency**:
   The feed-forward policy takes a 157-dim feature vector without memory of its position within the multi-step opening script. At coordinate `[4, 4]`, the policy has seen `PASS` (Step 0), `NORTH` (Step 1), and `SOUTH` (Step 2). At Step 3, standing at `[4, 4]` again, without an explicit step counter or recurrent hidden state, the static features alone do not sufficiently discriminate between continuing to move or executing an in-place pickup.
3. **The Role of Semantic Masking**:
   The semantic action mask proved essential for removing illegal simulator commands (`PICKUP` outside the shed), but cannot force the model to prefer the expert action among the remaining legal candidates (`NORTH` vs `SOUTH`).

---

## 4. GATE EVALUATION & RECOMMENDATION

- **Gate 1 (Simulator-Legality)**: **PASS** (Mask verified 100% compliant with simulator engine).
- **Gate 2 (First Divergence Delay)**: **PASS** (Divergence delayed past Step 2 to Step 3; Step 2 SOUTH = 100%).
- **Gate 3 (Economic Compounding)**: **FAIL** (Mean cash $0.07, median $0.00, 0 wins).
- **Gate 4 (Holdout Quarantine)**: **PASS** (Protected holdouts virgin).
- **Gate 5 (PPO Gate)**: **PASS / CLOSED** (`PPO 1M SLOPE GATE: CLOSED`).

**Final Conclusion**:
In accordance with preregistered decision rules, Phase P6 concludes as **P6 PARTIAL**.
