# PHASE 014: AEC ECONOMIC HEADROOM FORENSICS

**Phase**: 014 — AEC Economic Headroom Audit  
**Date**: September 19, 2026  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Empirical Foundation Control**: `V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`  
**Total Fresh Seeds Evaluated**: 35 unique seeds (`249241..249275`, 70 mirror matches, 50,330 total turns)  

---

## 1. Executive Summary & Central Findings

The Phase 014 forensic audit addresses the central question:
> **Does meaningful economic headroom remain beyond the current live foundation, and if so, where is it?**

Across 12,742 probed states across 35 pristine fresh development seeds:
1. **Headroom Abundance**: Measurable positive economic headroom exists in **80.72% of probed states** (10,285 states). The mean oracle headroom is **+$196.87 USD**, with a median of **+$27.00 USD**, a 90th percentile of **+$301.10 USD**, and a maximum of **+$17,730.00 USD**.
2. **The Causal Bottleneck is Detection & Representation**:
   - **78.23%** of positive headroom states suffer from **Detector Blindness** (`Category C`, `NOT_DETECTED`). The Event Detector and Opportunity Engine emit zero opportunities because trigger predicates are excessively rigid (e.g. requiring cash deviation $> \$200$ or shed stock $> 95$ units).
   - **21.56%** suffer from **Candidate Representation Defect** (`Category D`, `NOT_REPRESENTED`). Opportunities are flagged, but the candidate generator fails to construct the specific required transformation.
   - **< 0.3%** of failures are caused by Trajectory Compilation, Reconnection, Safety Gates, or Counterfactual Simulator divergence.
3. **Dominant Transformation Families**:
   - **Market Timing (85.91% of headroom)**: Uncommitted inventory sits idle in the shed rather than being liquidated in tranches during favorable price regimes or prior to market saturation.
   - **Terminal Liquidation (2.04% of states, highest mean delta = +$780.22)**: Suboptimal late-game transit where workers continue planting or tending rather than executing endgame liquidation sweeps.
   - **Opponent Preemption (3.63%, mean delta = +$156.71)**: Baseline ignores rival market movements, missing opportunities to capture clearing depth ahead of rival supply dumps.
   - **Multi-Worker Coordination (3.58%, mean delta = +$79.80)**: Uncoordinated paths where lead harvesters drop cargo without helper collection.

---

## 2. Turn-Level State Distribution & Foundation Allocation

Across 50,330 turns across the 35 fresh seeds:

### 2.1 Worker State Distribution
| Worker State | Turns | Frequency | Economic Implication |
| :--- | :---: | :---: | :--- |
| `productive` | 19,578 | 38.90% | Workers actively harvesting, planting, or tending. High V3 efficiency. |
| `idle` | 19,981 | 39.70% | Workers executing `PASS` or waiting at destination. Substantial labor slack. |
| `carrying` | 10,771 | 21.40% | Workers carrying cargo $\ge 8$ units; transit bottlenecks observed. |

### 2.2 Farm State Distribution
| Farm State | Turns | Frequency | Economic Implication |
| :--- | :---: | :---: | :--- |
| `cash-rich` | 29,760 | 59.13% | Cash $> \$5,000$. Ample capital available for unexploited reinvestment. |
| `normal` | 13,710 | 27.24% | Standard operational flow. |
| `cash-constrained` | 3,825 | 7.60% | Cash $< \$500$ or daily wage obligations tight near day boundaries. |
| `terminal-constrained` | 1,958 | 3.89% | Turn $\ge 680$ with unliquidated field or shed assets. |
| `shed-constrained` | 1,077 | 2.14% | Shed stock $\ge 90$ units (risk of harvest overflow discard). |

### 2.3 Market State Distribution
| Market State | Turns | Frequency | Economic Implication |
| :--- | :---: | :---: | :--- |
| `favorable` | 40,364 | 80.20% | Commodity prices $> +15\%$ above historical base; prime liquidation window. |
| `liquidity-sensitive` | 4,630 | 9.20% | Cash needed within 3 turns to service hiring fees or seed cycles. |
| `opportunity_window` | 4,132 | 8.21% | Transient town demand refresh window (step % 72 within 6 ticks). |
| `normal` | 1,057 | 2.10% | Baseline prices. |
| `unfavorable` | 147 | 0.29% | Depressed commodity prices from saturation. |

---

## 3. Potential Headroom State Indicators

The 16 diagnostic indicators triggered with the following frequencies:
1. `ROUTE_CONGESTION`: 169,944 events — Workers adjacent or crossing paths, indicating uncoordinated pathing.
2. `MARKET_PRICE_SPIKE`: 34,109 events — Held shed assets experiencing price spikes $> 25\%$ without market orders emitted.
3. `CASH_SHORTAGE_WAGE_RISK`: 3,822 events — Tight working capital near day boundaries.
4. `PRODUCTION_INPUT_MISMATCH`: 2,155 events — Raw produce stored in shed while workers sit idle.
5. `LARGE_UNCOMMITTED_INVENTORY`: 1,077 events — Shed inventory $> 50$ units with zero active market sell orders.
6. `TERMINAL_RUNWAY_ASYMMETRY`: 714 events — Late-game production actions executed when direct raw liquidation yields higher NPV.
7. `CASH_TEMPORARILY_IDLE`: 560 events — Cash $> \$3,000$ at day start with zero land purchases or seed orders.
8. `MARKET_PRICE_COLLAPSE`: 30 events — Inventory held through downward price corrections.

---

## 4. Bounded Oracle Headroom Distribution

Across the 10,285 positive headroom states:

```text
Percentile Distribution (USD):
  Min   : $   0.60
  p25   : $  12.00
  p50   : $  27.00
  p75   : $  90.40
  p90   : $ 301.10
  p95   : $ 654.20
  p99   : $1,840.00
  Max   : $17,730.00
  Mean  : $ 196.87
```

### Breakdown by Transformation Family:
| Family | Positive States | Share | Mean Delta | Max Delta | Primary Economic Mechanism |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `MARKET` | 8,836 | 85.91% | +$198.73 | +$17,730.00 | Immediate liquidation tranches during price spikes; frontloading before saturation. |
| `TERMINAL` | 210 | 2.04% | +$780.22 | +$2,084.00 | Complete shed liquidation dump at $t \ge 710$; aborting unharvestable plantings. |
| `OPPONENT` | 373 | 3.63% | +$156.71 | +$1,427.00 | Preemptive sell orders capturing clearing depth ahead of rival delivery. |
| `MULTI_WORKER` | 368 | 3.58% | +$79.80 | +$203.00 | Coordinated harvest: lead worker harvests, helper collects and drops. |
| `WORKER` | 498 | 4.84% | +$34.50 | +$268.00 | Immediate harvest execution when adjacent to mature crops instead of detour. |

---

## 5. Causal Layer Failure Attribution

Every positive oracle state was traced through the compiler layers to identify why the live foundation missed it:

```text
HEADROOM (10,285 states)
  │
  ├── NOT_DETECTED (8,066 states, 78.43%) ──► Event / Opportunity detectors blind
  │
  ├── NOT_REPRESENTED (2,185 states, 21.24%) ──► Candidate generator missing transformation
  │
  ├── SAFETY_REJECTED (16 states, 0.16%) ──► Intermediate solvency / overflow guard
  │
  ├── COUNTERFACTUAL_REJECTED (14 states, 0.14%) ──► Simulator evaluated delta <= 0
  │
  ├── FILTERED (2 states, 0.02%) ──► Static pruning dropped candidate
  │
  └── NONE_AEC_COMMITTED (2 states, 0.02%) ──► Captured by foundation
```

### Forensic Diagnosis of the Top 2 Bottlenecks:

#### 1. The Detector Bottleneck (78.43% of missed headroom)
- **Causal Mechanism**: Event detection in AEC currently triggers on coarse, lagging macroeconomic indicators:
  - `PRICE_SHOCK` requires $> 25\%$ relative deviation from the previous turn.
  - `SHED_ALARM` requires shed inventory $> 95$ units.
  - `CASH_DEVIATION` requires $> \$200$ shift from expectation.
- **Consequence**: When shed inventory accumulates 30–70 units of high-value crops (e.g. Strawberries or Melons) during favorable market prices, **zero events fire**. The opportunity engine remains dormant, and V3 emits empty market queues. The oracle demonstrates that liquidating 10-unit tranches during these stable high-price windows captures an average of **+$198.73 USD** per state.

#### 2. The Candidate Representation Bottleneck (21.24% of missed headroom)
- **Causal Mechanism**: In states where events do fire (e.g. `OPPONENT_PRESSURE` or `TOWN_CYCLE_APPROACH`), the candidate generator only evaluates predefined monolithic templates:
  - `DEPENDENCY_AWARE_MARKET_TIMING` only modifies existing baseline orders.
  - If the baseline emitted zero sell orders, `DEPENDENCY_AWARE_MARKET_TIMING` has nothing to reorder.
- **Consequence**: The compiler cannot generate an autonomous *new* sell tranche from scratch when the baseline is passive.

---

## 6. Testing the Central Hypotheses

- **H1 (V3 Dominance) — REJECTED**: Bounded local headroom exists on **80.7%** of turns, averaging +$196.87. V3 is not at the optimal economic frontier; it leaves substantial capital locked in shed inventory.
- **H2 (Detector Blindness) — CONFIRMED**: 78.4% of missed opportunities are never proposed by event/opportunity detectors.
- **H3 (Candidate Representation Gap) — CONFIRMED**: 21.2% of missed opportunities are detected but cannot be formulated by existing generators.
- **H4 (Compiler / CoupledPatch Limitation) — REJECTED**: Trajectory compilation and reconnection succeed with 99.9% reliability when candidates are provided.
- **H5 (Horizon Insufficiency) — REJECTED**: In §23 testing, peak headroom occurs at standard horizon $H=18$. Extending to $H=36$ reduces positive rate from 83.3% to 50.0%.
- **H6 (Mechanism Composition) — CONFIRMED**: Pairwise mechanism composition exhibits a **55.6% superadditive rate**, generating higher value than isolated components.
- **H7 (Opponent Contingency) — CONFIRMED**: Opponent preemption achieves a **100.0% win rate** under rival delivery pressure.
- **H8 (Macro Policy Boundary) — REJECTED for tactical play**: Headroom does not require changing the macro crop plan; it exists strictly in tactical inventory liquidation and worker coordination.
