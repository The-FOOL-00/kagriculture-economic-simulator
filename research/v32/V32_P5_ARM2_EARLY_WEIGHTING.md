# V32 P5 — ARM 2: BOUNDED EARLY-HORIZON LOSS EMPHASIS

## 1. SCIENTIFIC RATIONALE & OBJECTIVE

The rollout diagnostics (`V32_P5_ROLLOUT_DIAGNOSTIC.md`, `V32_P5_FIRST_DIVERGENCE.md`, `V32_P5_EARLY_HORIZON.md`) established:
1. **The Step-0 Unit Omission**: P4 Arm 1 applied critical weighting ($\lambda_{crit} = 50.0$) strictly to the market slots (`loss_m_op`, `loss_m_item`, `loss_m_qty`). The farmer unit head remained unweighted. Diluted by 138,000 downstream transitions where the farmer constantly moves, the model learned `WEST` (54.64% probability) instead of `PASS` (4.46% probability).
2. **The Step-1 Choreography Dilution**: Even when the farmer passes at Step 0, steps 1–10 (hiring 5 hands, buying 2 cows + 2 sheep, moving back to shed at Step 2 to pick up animals, building pasture, and planting) account for only **1.5%** of the dataset ($2,112$ transitions). Downstream wandering and harvesting dilute these initialization gradients 65-to-1.
3. **The Cascade**: Failing to execute the exact choreograph at Step 1 or Step 2 permanently locks the policy out of labor, livestock, and agronomy, collapsing terminal cash to ~$72.

**Arm 2 Goal**: Repair the early-horizon loss objective so that the critical initialization sequence is learned with high fidelity, preventing the policy from falling off the training manifold at steps 0–10.

---

## 2. MATHEMATICAL FORMULATION

The composite loss function for Arm 2 is:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{unit}} + \mathcal{L}_{\text{market}} + \lambda_{\text{crit}} \cdot \mathcal{L}_{\text{crit}}^{s=0} + \lambda_{\text{early}} \cdot \mathcal{L}_{\text{early}}^{s \in [1, 10]}$$

### 2.1 Critical Step-0 Loss ($\mathcal{L}_{\text{crit}}^{s=0}$)
Unlike P4, which only weighted the market slots, Arm 2 includes both the farmer unit operation and the market wash:
$$\mathcal{L}_{\text{crit}}^{s=0} = \mathcal{L}_{\text{CE}}(u_{\text{op}}^{s=0, \text{farmer}}, y_{\text{PASS}}) + \sum_{j=0}^{1} \left( \mathcal{L}_{\text{CE}}(m_{\text{op}, j}^{s=0}, y_{m_{\text{op}}, j}) + \mathcal{L}_{\text{CE}}(m_{\text{item}, j}^{s=0}, y_{m_{\text{item}}, j}) + \mathcal{L}_{\text{CE}}(m_{\text{qty}, j}^{s=0}, y_{m_{\text{qty}}, j}) \right)$$
with $\lambda_{\text{crit}} = 50.0$.

### 2.2 Bounded Early-Horizon Loss ($\mathcal{L}_{\text{early}}^{s \in [1, 10]}$)
For all transitions at steps $1 \le t \le 10$:
$$\mathcal{L}_{\text{early}} = \mathcal{L}_{\text{unit}}^{t \in [1, 10]} + \mathcal{L}_{\text{market}}^{t \in [1, 10]}$$
with $\lambda_{\text{early}} = 10.0$.

### 2.3 Bounded Gradient Mass Justification
- Steps 1–10 represent 1.39% of all training samples.
- With $\lambda_{\text{early}} = 10.0$, the effective gradient contribution of steps 1–10 is:
  $$\frac{1.39\% \times 10}{100\% + 1.39\% \times 9} \approx 12.3\%$$
- This ensures that early initialization receives 12.3% of the gradient mass—sufficient to guarantee adherence to the choreograph—while leaving **87.7% of the gradient mass** to optimize global gameplay, farming, and harvesting across steps 11–719.
- Total model parameters remain strictly frozen at **277,092** (`P3Policy`).

---

## 3. PREREGISTERED DECISION GATES FOR ARM 2

To proceed to full closed-loop screening (120 legs), Arm 2 must satisfy:
1. **Step-0 Wash Gate**: $\ge 240/240$ wash shape recovery.
2. **Step-0 Farmer Pass Gate**: $\ge 235/240$ `PASS` recovery on Step 0.
3. **Step-1 Hiring & Direction Gate**: Significant recovery of `NORTH` and $\ge 3$ hires on Step 1 probe.
4. **Global Validation Gate**: Full-action exact validation match does not collapse ($> 0.05$).
