# V32 P4 H2 FREEZE VS UNFREEZE INTERFERENCE REPORT (Arms 2, 3, 4)

Date: 2026-09-23.
Scripts:
- `scripts/v32_p4_train.py --arm arm2_mkt_pretrain` -> `results/v32_p4_arm2_mkt_pretrain.npz`
- `scripts/v32_p4_train.py --arm arm3_mkt_frozen` -> `results/v32_p4_arm3_mkt_frozen.npz`
- `scripts/v32_p4_train.py --arm arm4_mkt_unfrozen` -> `results/v32_p4_arm4_mkt_unfrozen.npz`

## 1. Experimental Design (§18, §19, §20)

To rigorously test Hypothesis H2 (Joint-Optimization Interference), we executed a three-stage causal sequence:
1. **Arm 2 (Pretraining)**: Train the shared trunk and market heads on market loss only ($L_{mkt} + \lambda_{crit} L_{crit}$) to convergence.
2. **Arm 3 (Market Frozen)**: Initialize from Arm 2, freeze market heads (`m_op`, `m_item`, `m_qty`, `slot_emb`), and train unit heads (`u_op`, `u_arg`, `u_qty`) and the shared trunk on $L_{unit}$.
3. **Arm 4 (Jointly Unfrozen)**: Initialize from Arm 2, leave all parameters trainable, and train jointly under standard unweighted BC ($L_{unit} + L_{mkt}$).

## 2. Comparative Results Matrix

| Metric | Arm 2 (Market Pretrained) | Arm 3 (Market Frozen, Unit Train) | Arm 4 (Pretrained Init, Unfrozen Joint) |
| :--- | :--- | :--- | :--- |
| **Market Status** | Pretrained | **FROZEN** | **UNFROZEN** |
| **Step-0 Wash (Ep 0)** | 240/240 (100%) | 240/240 (100%) | **0/240 (0%)** |
| **Step-0 Wash (Ep 1)** | 240/240 (100%) | 240/240 (100%) | 0/240 (0%) |
| **Step-0 Wash (Ep 2)** | 240/240 (100%) | 0/240 (0%)* | 0/240 (0%) |
| **Final Step-0 Wash** | **240/240 (100%)** | 0/240 (0%)* | **0/240 (0%)** |
| **Final Slot 0 Argmax**| `BUY_PRODUCT WHEAT` | `BUY_PRODUCT FERTILIZER` | `SELL WHEAT` |
| **Final Slot 1 Argmax**| `SELL WHEAT` | `SELL WHEAT` | `BUY_PRODUCT WHEAT` |
| **Slot 0 P(BUY) Final**| **0.92** | 0.82 | **0.11** |
| **Slot 0 P(SELL) Final**| **0.08** | 0.18 | **0.89** |
| **Val `market_op_nonnoop`**| **0.825** | 0.486 | **0.900** |
| **Val `unit_op`** | 0.072 (untrained) | 0.509 | 0.493 |
| **Val `farmer`** | 0.056 (untrained) | 0.536 | 0.521 |
| **Val `full_exact`** | 0.004 | 0.009 | 0.061 |

*Note on Arm 3: In Ep 2, the action head emitted `BUY_PRODUCT FERTILIZER` instead of `WHEAT` because the trunk representation $h$ drifted to optimize unit actions.

## 3. Key Scientific Findings

### 3.1 Arm 4: Destructive Joint Optimization Conclusively Demonstrated
- Arm 4 was initialized with parameters that had **100% wash accuracy** (240/240) and $P(\text{BUY}) = 0.92$ on Slot 0.
- In **Epoch 0** of standard unweighted joint training, the 51,526 non-step-0 `SELL` examples immediately overwhelmed the 192 step-0 examples.
- $P(\text{SELL})$ on Slot 0 surged from $0.08 \to 0.68 \to 0.94$, and the wash completely flipped into the reversed failure mode `[SELL, BUY_PRODUCT]`.
- This definitively proves **gradient overpowering / catastrophic forgetting of the rare critical pattern under unweighted joint optimization**.

### 3.2 Arm 3: Latent Representation Drift in Shared Trunk
- Even when the linear classification weights of the market heads are frozen, their input is $[h, \text{slot\_emb}]$ where $h = \text{trunk}(s)$.
- As unit loss backpropagated through the trunk, the feature space $h$ drifted to serve unit predictions, causing market non-NOOP accuracy to plummet from 0.825 to 0.486 and item prediction to drift to FERTILIZER.
- This demonstrates that **market-side freezing alone cannot protect the policy without either freezing the shared trunk or maintaining a market gradient in the trunk**.

### 3.3 Synthesis with Arm 1
- Initializing from a good market checkpoint (Arm 4) fails because unweighted joint BC destroys it.
- Freezing market heads with a plastic trunk (Arm 3) fails because representation drift degrades the frozen head's input features.
- **Arm 1 (Critical-Pattern Balanced BC)** succeeds because it continuously maintains the gradient signal for the rare pattern in both the shared trunk and the market heads throughout joint optimization.
