# V32 P10 — RESIDUAL CANDIDATES SPECIFICATION: LOCAL OVERRIDES ON FROZEN A7
**Phase:** V32 P10  
**Date:** 2026-09-23  
**Status:** PREREGISTERED FOR SCREENING  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. RESIDUAL PHILOSOPHY & NON-NEGOTIABLE CONTRACT

In accordance with P10 design principles:
- The default agent behavior is **100% frozen A7**.
- A residual is **NOT** a second macro-planner and **NOT** a new strategy.
- It is a **narrow, single-turn, state-grounded patch** that intercepts A7's proposed action at step $t$, applies a local modification, and immediately returns control to A7.
- Every override must produce a typed `ResidualDecision` record with full traceability.

---

## 2. CANDIDATE RESIDUAL REGISTRY

| ID | Permanent Name | Target Mechanism | Activation Condition | Proposed Action Mutation | Causal Horizon |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **`R01`** | `OPPONENT_SELL_PREEMPT` | Prevent negative market price slippage on high-value perishables. | Opponent sell pressure detected OR town consumption due in 1 step; player holds $\ge 4$ un-sold Milk/Wool/Melon in shed at spot price $\ge \$30$. | Add targeted `['SELL', item, min(qty, 12)]` to market queue before price collapses. | 8 steps |
| **`R02`** | `MARKET_QUANTITY_ADJUST` | Prevent dumping into severely depressed, oversupplied markets. | Mid-game step ($10 < t < 710$); market inventory $\ge 40$; spot price $< \$15$; A7 proposing large sell order ($> 8$ units) while player cash is healthy ($> \$500$). | Trim sell quantity to $50\%$ to preserve stock for post-consumption price recovery. | 8 steps |
| **`R03`** | `LIQUIDITY_PROTECTION` | Prevent cash exhaustion and delayed production compounding. | Liquid cash critically low ($< \$120$); A7 order contains non-essential capital expense (`BUY_ANIMAL` or `BUY_LAND`). | Suppress the non-essential capital expenditure to maintain the wage/seed buffer. | 12 steps |
| **`R05`** | `LOCAL_LABOR_PATCH` | Eliminate unnecessary wage burden during low-activity windows. | Step $10 < t < 650$; cash $< \$100$; active workers $\ge 6$; A7 proposing `HIRE` order. | Suppress single `HIRE` order to avoid pushing cash into negative runway. | 24 steps |
| **`R07`** | `TERMINAL_LOCAL_PATCH` | Extract residual un-liquidated goods in terminal window. | Final steps ($t \ge 716$); player shed holds positive stock of any commodity not already included in A7's sell orders. | Add `['SELL', prod, qty]` for all reachable residual items to maximize terminal cash. | 4 steps |

---

## 3. CAUSAL LOGIC PER CANDIDATE

### R01: Opponent Sell Preemption
- **Hypothesis:** When an opponent dumps commodity lots into the market (e.g., Dmitrii selling 24 melons or 12 milk), market inventory rises and the simulator's price function depresses the bid price. If A7 has mature goods in the shed and waits for its scheduled tape turn, it sells into the trough. Preempting the sale by 1–2 steps captures the pre-dump spot price.
- **Downside Risk:** Prematurely selling goods that may be needed for downstream quest/shop fulfillment or triggering town consumption clearing prematurely. Gated by minimum price floor ($\ge \$30$) and lot cap ($\le 12$).

### R02: Market Quantity Adjustment
- **Hypothesis:** When town market inventory exceeds 40 units, prices drop by up to $80\%$. Because the town consumes supply every 4 steps, dumping large quantities into a saturated market yields minimal return. Trimming sales until after consumption restores price realization.
- **Downside Risk:** Trapping inventory in the shed and hitting the 100-item capacity limit. Gated by cash safety floor ($> \$500$).

### R03: Liquidity Protection
- **Hypothesis:** Early/mid-game cash crunches below $120 cause farm operations to stall if wages or seed purchases bounce. Deferring a non-urgent land or animal expansion protects continuous crop cycles.
- **Downside Risk:** Delaying compounding returns from animal/land investments. Gated strictly to extreme cash emergencies ($< \$120$).

### R05: Local Labor Patch
- **Hypothesis:** Daily hand hiring follows a Fibonacci wage curve ($1, 1, 2, 3, 5, 8, 13, 21\dots$). Hiring when the farm already has 6+ workers and cash is tight drains working capital without adding productive harvest output.
- **Downside Risk:** P9 proved that general labor throttling strands crops. Therefore, R05 is restricted strictly to non-endgame ($t < 650$), non-opening ($t > 10$) steps when cash is $< \$100$.

### R07: Terminal Local Patch
- **Hypothesis:** At steps 716–718, any unsold item in the shed has exactly zero terminal economic value. Forcing liquidation of all unlisted shed goods captures incremental residual coin.
- **Downside Risk:** Exceeding the 10-order market limit. Gated by `len(market) < 10`.

---

## 4. EVALUATION CRITERIA

Each candidate must be evaluated in isolation against pure A7 on the 10 development seeds:
1. **Activation Count:** Must activate $\ge 3$ times across the dev panel.
2. **Paired Delta:** Mean delta on activated legs must be positive ($\Delta \ge +\$50.00$).
3. **Worst-Case Loss:** Must not suffer a single catastrophic loss ($Worst \ge -\$50.00$).
4. **Legality & Invariant Safety:** 0 illegal actions, 0 crashes, 100% fallback to A7 on any anomaly.
