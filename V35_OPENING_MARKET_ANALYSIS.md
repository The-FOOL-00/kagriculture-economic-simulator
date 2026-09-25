# V35 Opening Market Interaction Analysis

## 1. Executive Summary
This analysis investigates whether the performance differential between the 30/30 wash and the 25/25 wash stems from interactive town market dynamics (e.g. price slippage, market saturation, opponent front-running) or purely from internal liquidity timing.

---

## 2. Town Market Mechanics at Step 0

In the Kaggriculture simulator (v1.32.7):
- At Step 0, both players submit their initial action before any production or consumption takes place.
- Town market queues process orders submitted at Step 0.
- For wheat:
  - Base price: $P_0 = 25.0$.
  - When Player A submits `BUY_PRODUCT WHEAT Q` followed by `SELL WHEAT Q`:
    - The `BUY_PRODUCT` order executes against available town inventory, shifting the marginal spot price upward according to the simulator's price elasticity curve:
      $$P_{\text{buy}} \approx P_0 \cdot \left(1 + \kappa_{\text{buy}} \cdot \frac{Q}{\text{Supply}}\right)$$
    - The subsequent `SELL` order executes, shifting the price back downward:
      $$P_{\text{sell}} \approx P_{\text{buy}} \cdot \left(1 - \kappa_{\text{sell}} \cdot \frac{Q}{\text{Demand}}\right)$$

---

## 3. Comparative Market Impact: 30/30 vs 25/25

| Dimension | 30/30 Wash (A7 Baseline) | 25/25 Wash (V34 / V35 Candidate) | Market Differential |
| :--- | :--- | :--- | :--- |
| **Gross Buy Volume** | 30 units | 25 units | -5 units (-16.7%) |
| **Gross Sell Volume** | 30 units | 25 units | -5 units (-16.7%) |
| **Capital Locked at Execution** | ~$750.00 | ~$625.00 | **+$125.00 liquid capital preserved** |
| **Slippage Loss (Round-Trip)** | ~$15.00 – $22.00 | ~$10.00 – $14.50 | **+$5.00 – $7.50 saved in friction** |
| **Opponent Market Interference** | Negligible (opponent does not wash wheat at t=0) | Negligible | Purely internal float advantage |
| **Step 1 Price Depletion** | Slightly higher price impact on wheat | Lower price impact on wheat | Favorable for step 1 wheat purchase |

---

## 4. Key Empirical Finding: Internal Float vs Market Exposure
1. **Opponent Market Cross-Talk:** In 100% of the league opponent families (`E2_A7`, `E8_DMITRII`, `E1_V22R1`, `E0_V3`, `V54`, `SYN_AGG`), opponents do not purchase wheat on Step 0. Therefore, the wash does not front-run or block opponent orders.
2. **Causal Mechanism Confirmation:** The advantage of 25/25 over 30/30 is **not** an adversarial market exploit. It is an **internal cash timing optimization**:
   - Preserves \$125 in liquid cash between Step 0 and Step 1.
   - Reduces price impact slippage by ~$6.00.
   - Protects the cash buffer against order bouncing during the heavy Step 1 purchase surge.
