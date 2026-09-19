# AEC PHASE 013: GROUP 3 RESCUE SPECIFICATION
## Second-Generation Economic Redesign for Shop Arbitrage, Production Arbitrage, Terminal Conversion, and Emergency Feed Purchase

**Author**: Antigravity AI Research Agent (Phase 013 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governing Architecture**: AEC Adaptive Economic Compiler (§0–§53)

---

## 1. Core Economic Principle: Local Spread $\ne$ Global Economic Value

The central mistake identified in the first-generation Group 3 mechanisms was evaluating local, instantaneous economic spreads in isolation:
- Buying an item because current purchase price is lower than a future projected price.
- Buying a seed because nominal harvest price exceeds seed cost.
- Selling or converting an item because the output has a higher nominal unit price.
- Purchasing feed reactively simply because inventory stock dropped below herd size.

In competitive farm simulation, **Local Economic Spread $\ne$ Global Economic Value**.
Every economic intervention alters working capital, occupies worker time, consumes shed storage capacity, shifts market depth, affects subsequent prices, and creates downstream dependencies.

Every second-generation Group 3 candidate must answer:
1. **What resource is being transformed?**
2. **What alternative use does that resource have?**
3. **What worker time does it consume?**
4. **What working capital does it consume?**
5. **What dependency does it create?**
6. **What downstream value does it unlock?**
7. **Can that value actually be realized before the horizon?**
8. **Does the transformation improve the exact terminal state?**

The authoritative gate remains the exact counterfactual comparison:
$$\Delta \text{TerminalState} = \mathcal{T}_{\text{treatment}}(\text{Step} \to 720) - \mathcal{T}_{\text{baseline}}(\text{Step} \to 720)$$

---

## 2. Mechanism A: Realizable Market Arbitrage (`SHOP_ARBITRAGE`)

### 2.1 Economic Thesis
A shop arbitrage candidate exists **only** when the transformation creates a real improvement in terminal wealth after accounting for source capital, acquisition timing, worker transit/timing, inventory capacity, conversion time, market timing, baseline sale alternatives, and terminal realization.

### 2.2 Explanatory Quantities
For every candidate, the mechanism calculates explanatory structural metrics:
$$\begin{aligned}
\text{GrossSpread} &= \text{RealizationValue} - \text{AcquisitionCost} \\
\text{NetRealizableSpread} &= \text{GrossSpread} - \text{WorkerOpportunityCost} - \text{LiquidityCost} \\
&\quad - \text{CapacityCost} - \text{TimingCost} - \text{DependencyRisk} - \text{TerminalRisk}
\end{aligned}$$
*Note: These terms explain candidate economics and filter out obvious losses. The final decision is determined exclusively by exact counterfactual simulation.*

### 2.3 Sequential Market Coupling & Non-Commutativity
Market operations are non-commutative:
$$\text{BUY} \to \text{SELL} \ne \text{SELL} \to \text{BUY}$$
- Executing a $\text{SELL}$ first injects liquidity, raising cash before a subsequent $\text{BUY}$ or wage payment.
- Executing a $\text{BUY}$ first consumes liquidity, potentially causing an immediate overdraft or failing if cash is insufficient.
- Market transactions shift clearing price and depth for subsequent actions in the same turn.
All candidates explicitly model and preserve exact sequential order in market order baskets ($\le 10$ orders).

### 2.4 Structural Working Capital & Hard Liquidity Constraint
Arbitrage that ties up cash is rejected if it impairs mandatory operations:
$$\text{Cash}(t) - \text{AcquisitionCost} \ge \text{RequiredLiquidity}(t, H_{\text{arbitrage}})$$
where:
$$\text{RequiredLiquidity}(t, H) = \text{UpcomingSeedPurchases} + \text{NightlyWages} + \text{FeedObligations}$$

### 2.5 Realizable Transformation Families
1. **`BUY_HOLD_SELL`**: Acquire discounted commodity from market, store in shed, liquidate upon town demand refresh when net spread covers capital lockup.
2. **`SELL_BUY_SELL`**: Liquidate current low-margin inventory to generate liquidity for a high-margin arbitrage purchase, liquidating the acquired good at peak market price.
3. **`DELAY_SALE_DEPTH`**: Hold inventory across 1–3 turns to exploit deterministic consumption-driven depth recovery.
4. **`TERMINAL_REALIZATION_GATE`**: If the acquired inventory cannot be physically or commercially liquidated before step 718, candidate is rejected ($H_{\text{completion}} > 718 - \text{Step}$).

---

## 3. Mechanism B: Marginal Production Opportunity (`PRODUCTION_ARBITRAGE`)

### 3.1 Economic Thesis
The mechanism must **not** re-implement the macro crop scheduler. The V3 backbone already dynamically chooses high-value crops.
Instead, the mechanism searches strictly for **Marginal Production Headroom**:
> *"Does changing one specific production decision create incremental economic value relative to the exact V3 continuation?"*

### 3.2 V3 Redundancy Test
For every proposed production transformation, evaluate:
$$\text{IsV3Redundant} = \begin{cases}
\text{TRUE} & \text{if V3 baseline continuation already executes this decision from its current state} \\
\text{FALSE} & \text{if candidate exploits new information, idle capacity, or external shocks}
\end{cases}$$
If $\text{IsV3Redundant} == \text{TRUE}$, the mechanism classifies the opportunity as `ALREADY_CAPTURED_BY_BACKBONE` and **ABSTAINS**.

### 3.3 Headroom Detection Sources
Headroom exists only when external changes create uncaptured potential:
1. **Newly Revealed Market Shock**: Sudden price spike in a short-cycle crop (e.g. carrot/tomato) after a town shop unlock event.
2. **Worker Availability Release**: An auxiliary worker finishes an assignment earlier than planned, leaving unallocated labor turns.
3. **Matured Input Surplus**: Excess harvested wheat or raw goods available in shed without allocated downstream purpose.
4. **Terminal Production Window**: Exact temporal alignment where a fast crop can complete growth and liquidation precisely before step 718, which macro planning missed due to conservative boundaries.

### 3.4 Coupled Production Trajectory
Every candidate specifies the complete lifecycle:
$$\text{Reassign Worker} \to \text{Acquire Input} \to \text{Plant/Till/Water} \to \text{Harvest} \to \text{Drop} \to \text{Liquidate}$$
Worker labor is valued using structural labor opportunity cost derived from displaced baseline tasks.

---

## 4. Mechanism C: Realizable Terminal Value Conversion (`TERMINAL_CONVERSION`)

### 4.1 Economic Thesis
Raw inventory at the end of the game has a guaranteed liquidation value under the foundation's `TERMINAL_LIQUIDATION`.
A conversion candidate is economically viable **only if** transforming the raw inventory into a secondary product yields net terminal wealth strictly exceeding direct raw liquidation:
$$\Delta V_{\text{terminal}} = V_{\text{terminal}}\big(\text{Conversion} \to \text{Liquidation}\big) - V_{\text{terminal}}\big(\text{Direct Raw Liquidation}\big) > 0$$

### 4.2 Mandatory Terminal Runway Proof
The conversion must be physically and temporally feasible before the hard cutoff ($T_{\text{cutoff}} = 718$):
$$\text{Step} + \text{TransitTurns} + \text{ConversionTurns} + \text{DropTurns} + \text{LiquidationWindow} \le 718$$
If remaining turns are insufficient:
$$\text{RunwayProof} = \text{FAILED} \implies \textbf{ABSTAIN}$$

### 4.3 Structural Invariants
1. **Direct Liquidation Superiority**: If raw inventory market sale yields equal or greater net revenue after accounting for worker diversion, the candidate is rejected.
2. **Shed Headroom Feasibility**: Output units must not cause shed overflow ($\text{ShedUnits} + \Delta \text{Units} \le \text{SHED\_CAPACITY}$).
3. **No Displacement of Terminal Harvests**: The allocated worker must not abandon higher-value standing field crops (e.g. mature melons) to perform late conversions.

---

## 5. Mechanism D: Irreversible Feed Failure Avoidance (`EMERGENCY_FEED_PURCHASE`)

### 5.1 Economic Thesis
The mechanism is **not** a generic feed buyer. In a well-managed baseline, routine feed purchases are handled naturally.
The mechanism activates **only as a catastrophic damage-avoidance circuit breaker**:
$$\text{Baseline Continuation} \to \text{Projected Feed Shortage} \to \text{Irreversible Loss (Animal Escape / Death)}$$
$$\textbf{and}$$
$$\text{Emergency Feed Purchase} \to \text{Prevents Irreversible Loss}$$

### 5.2 Multi-Alternative Structural Comparison
Before approving a market purchase of wheat/feed, evaluate all alternatives in order of economic cost:
1. **Existing Shed / Carried Inventory**: Check if wheat is already physically available on farm.
2. **Harvestable Field Wheat**: Check if mature wheat can be harvested within the escape window.
3. **Downstream Wheat-to-Hay Conversion**: Evaluate local conversion before market procurement.
4. **Emergency Market Purchase (`BUY_PRODUCT WHEAT`)**: Executed only if steps 1–3 are impossible or too slow.
5. **Do Nothing / Accept Loss**: If animal value is less than the emergency intervention cost, accept the loss.

### 5.3 Downstream Liquidity Conflict Screen
The purchase must not induce secondary systemic failure:
$$\text{Cash}(t) - \text{PurchaseCost} \ge \text{MandatorySeedCapital}(t_{\text{morning}})$$
If saving an animal depletes the working capital required to plant the primary crop rotation, the long-term crop loss exceeds animal salvage value. The candidate must verify holistic trajectory solvency.

---

## 6. Architecture & Gate Summary Matrix

| Mechanism | Trigger Window | Core Invariant Gate | Rejection Rule |
| :--- | :--- | :--- | :--- |
| **`SHOP_ARBITRAGE`** | $t \equiv 0 \pmod{4}$ or $t \equiv 0 \pmod{72} \pm 8$ | $\text{NetRealizableSpread} > 0$ under exact simulation | Working capital drag or terminal unrealizability $\to$ ABSTAIN |
| **`PRODUCTION_ARBITRAGE`** | $t \equiv 0 \pmod{24}$ or market shock | $\text{IncrementalValue} > 0$ and $\text{IsV3Redundant} == \text{FALSE}$ | Redundant with V3 or labor opportunity cost excessive $\to$ ABSTAIN |
| **`TERMINAL_CONVERSION`** | Steps 670–716 | $\text{RealizedConvertedValue} > \text{DirectLiquidationValue}$ | Runway insufficient or direct liquidation superior $\to$ ABSTAIN |
| **`EMERGENCY_FEED_PURCHASE`** | $\text{consecutive\_unfed} \ge 1$ or projected escape | $\text{AvoidedIrreversibleLoss} > \text{InterventionCost}$ | Baseline naturally safe or seed capital starved $\to$ ABSTAIN |
