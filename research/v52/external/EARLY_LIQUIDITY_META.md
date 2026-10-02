# Early Liquidity Meta Research: Opening Float, Step-36 Dynamics & Working Capital

## 1. Executive Summary
Early liquidity in Kaggriculture is the catalyst for capital compounding. In a 720-step match, an extra \$100–\$1,400 available between Step 0 and Step 48 can fundamentally shift the speed at which farm hands are recruited, crops are planted, and animals are amortized.

This audit compiles the public mechanisms and historical evidence surrounding early working capital management:
1. **The Step 0 Wheat Wash Lineage** (from 50/50 down to 25/25 and 20/15).
2. **Rayk Kretzschmar's Funded Atomic Opening** (Step 1 capital aggregation).
3. **The V44 Step-36 Liquidity Float / Goose Arbitrage** (which accounts for 7 of V49's 11 historical losses).

---

## 2. Public Mechanism Audit Table

| Source | Author / Entity | Date | Mechanism Description | Reported Metric | Environment | Reproducible | License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Opening Wheat Wash Analysis** | Ahmed Berat Ozer / Kaggriculture Community | 2026-09-08 | Simulates BUY and SELL of Wheat at Step 0 to exploit initial spread pricing. Early public bots executed 50 BUY / 50 SELL. Evolved to 30/30 (A7) and 25/25 (V34/V44), capturing spread while preserving immediate cash float. | 25/25 wash captures 83.3% of spread while preserving +$125 cash float over 30/30; eliminates Step 1 order bouncing | Local Sim & Public LB | 100% Reproducible | Apache-2.0 / MIT |
| **Funded Atomic Opening** | Rayk Kretzschmar (`Rank Your Agent`) | 2026-09-05 | Aggregates Step 1 outlays into an atomic transaction: 5 farm hands ($10 each wage commitment) + 2 Cows ($800) + 2 Sheep ($1,000) + basic tools. Enforces liquidity safety buffers to ensure hand wages ($10/turn) do not bounce subsequent seed orders. | Prevents early game order bouncing and worker idling | Public Kernels & Competition | 100% Reproducible | MIT |
| **COWSWAP Layer & Goose Arbitrage** | Claude / Competition Analysis (`tools/claude_build_cowswap.py`) | 2026-09-13 | Evaluates Step 144–192 first cow purchase against town shop state. If milk shops are absent and egg shops are open, swaps Cow to Goose to capture immediate low-cost egg revenue. In V49, this mechanism is active, but against V44 it creates a $1,400 loss deficit on seeds where cow compounding dominates. | +$1,203 mean on specific no-milk seeds in discovery, but responsible for 7/11 historical losses against V44 | Local Simulation | 100% Reproducible | Apache-2.0 |

---

## 3. The Causal Anatomy of the "Liquidity Float"

In Kaggriculture:
1. **Step 0 Market Transaction:**
   - Both players begin with \$3,000 cash.
   - At Step 0, players can issue market orders before workers take physical steps.
   - A wheat wash (e.g. `BUY_PRODUCT WHEAT 25`, `SELL WHEAT 25`) takes advantage of town inventory pricing.
   - However, purchasing wheat temporarily ties up cash. If an agent executes an asymmetric buy/sell or holds inventory into Step 1, its cash float going into Step 1 is reduced.
2. **Step 1 Worker & Animal Commitments:**
   - Hires cost exponential/Fibonacci fees ($N_{\text{hands}}$ cost increases with each hire).
   - 5 farm hands + 2 Cows (\$800) + 2 Sheep (\$1,000) = \$1,946+ outlay.
   - If starting cash is \$2,873 (V49) vs \$2,997 (V44), V44 holds an immediate +\$124 liquid surplus.
3. **The Step 36–150 Compounding Cascade:**
   - If an agent can afford to purchase melon seeds or hire an additional hand 1–2 cycles earlier, that worker begins tilling plots and harvesting crops earlier.
   - By Step 144 (Day 6), when the first land expansion quadrant unlocks (\$1,000 for NE), the agent with superior cash float buys the land immediately, planting high-value melons and harvesting them by Day 12.
   - Conversely, an agent delayed by even \$50 at Step 144 must postpone land acquisition to Day 7 or Day 8, missing an entire 72-turn crop growth cycle.
