# V25 Capital Planner Specification

## 1. Objective
Replace static, arbitrary cash reserve thresholds with a dynamic, solvency-guaranteed capital budgeting model. Enable aggressive early capital velocity without risking bankruptcy or worker wage starvation.

## 2. Core Economic Accounting

At any turn $t \in [0, T]$ with remaining horizon $H = T - t$:

$$Cash_{available}(t) = Cash(t) - Cash_{reserve}(t) - Cash_{obligations}(t, \Delta t)$$

Where:
* $Cash(t)$: Current liquid cash balance.
* $Cash_{obligations}(t, \Delta t)$: Committed operational expenses over the planning window $\Delta t = \min(10, H)$:
  $$Cash_{obligations}(t, \Delta t) = \sum_{\tau=t}^{t+\Delta t} \left[ N_{workers}(\tau) \times Wage_{daily} + N_{livestock}(\tau) \times FeedCost_{daily} \right]$$
* $Cash_{reserve}(t)$: Safety cushion against price volatility and emergency feed procurement:
  $$Cash_{reserve}(t) = \begin{cases}
  500 & \text{if } t < 100 \\
  1000 & \text{if } 100 \le t < 500 \\
  200 & \text{if } t \ge 500 \text{ (terminal wind-down)}
  \end{cases}$$

## 3. Capital Allocation Hierarchy

When $Cash_{available}(t) > 0$, capital is deployed strictly according to expected marginal return per turn:

1. **Working Capital Priority 1: High-Velocity Seeds**
   * Planting available cleared tiles with target crops (Carrot / Tomato) has the highest immediate turnover ($ROI / turn \approx 8 - 15\%$).
   * Allocated up to current tilled soil capacity.

2. **Capital Priority 2: Worker Expansion**
   * Hiring a worker costs 500 capital + 100/turn operating wage.
   * Feasible only when $Cash_{available}(t) \ge 1500$ and marginal productive labor exists (unattended crops or livestock).

3. **Capital Priority 3: Livestock Scaling**
   * Purchasing cows/sheep requires capital lockup (1,000 / cow).
   * Feasible only when $Cash_{available}(t) \ge 2000$ and $H \ge 200$ turns remaining (amortization horizon).

4. **Capital Priority 4: Market Inventory Buffer**
   * Bulk seed purchase when prices are below moving average.

## 4. Solvency Invariant
No capital expenditure (seed purchase, livestock buy, tool unlock, worker hire) may be scheduled if it drives projected $Cash_{available}(t + \tau) < 0$ for any $\tau \in [1, \Delta t]$.
