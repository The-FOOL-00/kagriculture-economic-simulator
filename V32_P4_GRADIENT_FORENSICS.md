# V32 P4 GRADIENT FORENSICS REPORT

Date: 2026-09-23.
Tool: `scratch/v32_p4_forensics.py`.

## 1. Objective
Quantify gradient norms, relative magnitudes, and directional alignment (cosine similarity) between:
- Unit loss gradients: $L_{unit} = L_{u\_op} + L_{u\_arg} + L_{u\_qty}$
- Market loss gradients: $L_{mkt} = L_{m\_op} + L_{m\_item} + L_{m\_qty}$
backpropagated into the shared 3×256 Tanh trunk parameters $\theta_{trunk}$.

## 2. Quantitative Results

### 2.1 Representative General Batch ($B = 1024$, Uniform Random)
- Total Unit Loss: $L_{unit} = 8.2224$
- Total Market Loss: $L_{mkt} = 8.7493$
- Trunk Gradient Norm w.r.t Unit Loss:
  $$\| \nabla_{\theta_{trunk}} L_{unit} \| = 0.8696$$
- Trunk Gradient Norm w.r.t Market Loss:
  $$\| \nabla_{\theta_{trunk}} L_{mkt} \| = 0.8401$$
- Gradient Norm Ratio (Unit / Market):
  $$\frac{\| \nabla L_{unit} \|}{\| \nabla L_{mkt} \|} = 1.04$$
- **Cosine Similarity** ($\nabla_{\theta_{trunk}} L_{unit}$ vs $\nabla_{\theta_{trunk}} L_{mkt}$):
  $$\cos(\theta_{unit}, \theta_{mkt}) = \mathbf{-0.0536}$$

### 2.2 Step-0 Enriched Batch ($B = 1024$, Containing all 192 Step-0 Samples + 832 General Samples)
- Total Unit Loss: $L_{unit} = 8.2172$
- Total Market Loss: $L_{mkt} = 8.7697$
- Trunk Gradient Norm w.r.t Unit Loss:
  $$\| \nabla_{\theta_{trunk}} L_{unit} \| = 0.9251$$
- Trunk Gradient Norm w.r.t Market Loss:
  $$\| \nabla_{\theta_{trunk}} L_{mkt} \| = 1.6045$$
- Gradient Norm Ratio (Unit / Market):
  $$\frac{\| \nabla L_{unit} \|}{\| \nabla L_{mkt} \|} = 0.58$$
- **Cosine Similarity**:
  $$\cos(\theta_{unit}, \theta_{mkt}) = \mathbf{-0.0187}$$

### 2.3 Market Slot Embedding Gradient Norms ($\| \nabla_{W_{emb}[s]} L_{mkt} \|$)
| Slot | Description | Gradient Norm | Dominant Target Class |
| :--- | :--- | :--- | :--- |
| **Slot 0** | First market order | **0.0399** | SELL (51k samples) vs BUY_PRODUCT (6.5k samples) |
| **Slot 1** | Second market order | **0.0303** | NOOP (100k samples) vs SELL (17k samples) |
| **Slot 2** | Third market order | 0.0107 | NOOP (119k samples) |
| **Slot 3** | Fourth market order | 0.0104 | NOOP (125k samples) |
| **Slot 4** | Fifth market order | 0.0112 | NOOP (128k samples) |
| **Slot 5** | Sixth market order | 0.0115 | NOOP (130k samples) |
| **Slot 6** | Seventh market order| 0.0118 | NOOP (132k samples) |
| **Slot 7** | Eighth market order | 0.0116 | NOOP (133k samples) |
| **Slot 8** | Ninth market order  | 0.0112 | NOOP (134k samples) |
| **Slot 9** | Tenth market order  | 0.0113 | NOOP (134k samples) |

## 3. Forensic Interpretation
1. **Trunk Gradients are Near-Orthogonal**: The cosine similarity between unit and market trunk gradients is $-0.0536$, showing that unit loss and market loss do NOT actively cancel each other out in the trunk. They pull in roughly orthogonal directions.
2. **Loss Dilution is Primary**: The binding issue is not that unit gradients actively reverse market gradients; rather, within the market head itself, the 192 step-0 transitions (where Slot 0 = BUY and Slot 1 = SELL) are outnumbered **268 to 1** by non-step-0 transitions where Slot 0 = SELL.
3. **Slot Embedding Bias**: Slot 0 receives ~4× higher gradient magnitude towards SELL than late slots, entrenching a powerful inductive bias towards SELL on Slot 0 that a standard joint BC objective cannot overcome in 30 epochs.
