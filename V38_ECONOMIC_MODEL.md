# V38 Economic State Abstraction & Financial Valuation Model

**Document ID:** `V38_ECONOMIC_MODEL.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Physical vs Economic State Separation

To prevent the catastrophic policy drift observed in RL-X2, V38 mandates a strict separation between **Physical State** and **Economic State**:

```text
                     RAW ENVIRONMENT OBSERVATION
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 ▼                                 ▼
           PHYSICAL STATE                    ECONOMIC STATE
     (What can physically happen?)    (What is financially valuable?)
                 │                                 │
     • Tile contents (10x10)           • Liquid cash & cash velocity
     • Worker coordinates (x, y)       • Inventory liquidation value
     • Planted crop maturity stages    • Spot prices & price trends
     • Pasture & coop occupancies      • Committed wage liabilities
     • Weed locations & chores         • Liquidity safety buffer
     • Hand cargo states               • Opponent visible capital
                 │                                 │
                 ▼                                 ▼
       DETERMINISTIC PLANNER             LEARNED PPO RESIDUAL
      (Physical Choreography)          (Economic Macro Decisions)
```

The learned PPO network does **not** process raw $10 \times 10$ tile maps or output worker move commands. It operates exclusively on the **Economic State**, choosing high-level resource allocations, while the deterministic planner handles spatial routing and chore execution.

---

## 2. Feature Inventory & Normalization (64 Dimensions)

The observable vector $\mathbf{x} \in \mathbb{R}^{64}$ is partitioned into 9 semantically distinct groups:

| Group | Dimension | Features | Normalization / Clipping Range |
| :--- | :---: | :--- | :--- |
| **1. Temporal Progress** | 3 | Normalized game step, hour of day, town consumption flag | $[0, 1]$ |
| **2. Capital & Liquidity** | 6 | Cash float, cash velocity, shed liquidation value, liquidity buffer, wage runway days, daily wage obligation | Normalized to $[0, 10]$ |
| **3. Spot Market Prices** | 9 | Spot prices for WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER | Normalized by $100$ |
| **4. Price Deltas** | 9 | 1-step price deltas $\Delta P_i = P_t - P_{t-1}$ across all 9 commodities | Clipped to $[-3.0, 3.0]$ |
| **5. Shed Inventory** | 9 | Stored quantities for all 9 products | Normalized by $50$ |
| **6. Seed Inventory** | 5 | Stored seed quantities (5 crop types) | Normalized by $20$ |
| **7. Liabilities & Costs** | 4 | Next hire cost (Fibonacci), next quadrant unlock cost, feed runway days, unlocked shop count | Scaled to $[0, 2]$ |
| **8. Opponent Observables** | 6 | Opponent liquid cash, cash difference ($C_{\text{own}} - C_{\text{opp}}$), visible worker count, visible crops, visible livestock, unlocked quadrants | Scaled, zero leakage |
| **9. Physical State Summary** | 13 | Active workers, quadrant count, empty plots, weeds, unwatered crops, harvestable crops, cow/sheep/goose counts, unfed animals, empty pastures, busy/idle hands | Scaled to $[0, 5]$ |

---

## 3. Financial Valuation & Balance Sheet Accounting

At any step $t$, the total enterprise value $\hat{V}_{\text{enterprise}}(s)$ is defined as:
$$\hat{V}_{\text{enterprise}}(s) = C_t + V_{\text{shed}}(s) + V_{\text{bio}}(s) - L_{\text{wages}}(s)$$

1. **Shed Liquidation Value:**
   $$V_{\text{shed}}(s) = \sum_{p \in \text{PRODUCTS}} Q_{\text{shed}}(p) \cdot \min\left(P_{\text{spot}}(p), \, \bar{P}(p)\right)$$
   where $\bar{P}(p)$ is the rolling median price to avoid bubble valuations.
2. **Biological Asset Value:**
   $$V_{\text{bio}}(s) = 400 \cdot N_{\text{cow}} + 500 \cdot N_{\text{sheep}} + 300 \cdot N_{\text{goose}} + \sum_{\text{crop}} \text{DiscountedExpectedYield}(\text{crop})$$
3. **Committed Wage Liabilities:**
   $$L_{\text{wages}}(s) = N_{\text{hands}} \cdot \$10.00 \cdot \min(2, \text{DaysRemaining})$$
4. **Liquidity Safety Buffer:**
   $$B_{\text{liquid}}(s) = C_t - 2 \cdot (N_{\text{hands}} \cdot \$10.00)$$
   When $B_{\text{liquid}} < \$150.00$, the agent enters a restricted liquidity mode where capital-intensive macro interventions are rejected.

---

## 4. Strict Zero-Leakage Invariants

1. **No Opponent Identity:** The state does not contain `opp_id` or any categorical indicator of which benchmark bot is playing.
2. **No Opponent Private Storage:** Opponent shed inventory, seed stocks, and hand inventories are strictly omitted.
3. **No Seed Conditioning:** Feature extraction performs no lookups on random seed numbers or pre-generated event schedules.
4. **Strictly Causal:** All prices, velocities, and deltas are computed from current and historical observations only; no future market information is accessible.
