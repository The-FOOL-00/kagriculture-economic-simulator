# PHASE 014: AEC ECONOMIC HEADROOM AUDIT SPECIFICATION

**Protocol Version**: 1.0.0  
**Phase**: 014 — AEC Economic Headroom Audit  
**Date**: September 19, 2026  
**Status**: ACTIVE / METHODOLOGICAL FOUNDATION  
**Governance Hash (V3 Chassis SHA-256)**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  

---

## 1. Primary Research Objective

Following the evaluation of Group 1 (Dynamic Harvest, Terminal Harvest, Route Compression, Cargo Ferry), Group 2 (Town/Cycle, Emergency Recovery, Opponent Preemption, Resource Conversion), and Group 3 (Shop Arbitrage, Production Arbitrage, Terminal Conversion, Emergency Feed Purchase), the canonical empirical live foundation remains:

$$\text{Live Foundation} = \text{V3} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$

The goal of Phase 014 is **not** to design another mechanism rescue campaign, nor to invent new heuristic patches. The goal is to rigorously investigate and answer:

> **Does meaningful economic headroom remain beyond the current live foundation, and if so, where is it?**

```text
V3 / Foundation
      ↓
Observed game states
      ↓
Potential alternative trajectories
      ↓
Best feasible alternative
      ↓
Potential economic headroom
      ↓
Can AEC represent it?
      ↓
Can candidate generation discover it?
      ↓
Can CoupledPatch express it?
      ↓
Can exact counterfactual realize it?
      ↓
If yes → why have current mechanisms missed it?
If no  → architecture / information boundary identified
```

---

## 2. Non-Negotiable Governance (§2, §38)

This phase is strictly diagnostic. Under no circumstances will this audit:
1. Inspect or tune against leaderboard performance.
2. Modify or access protected cohorts:
   - Primary Locked Holdout: `340050..340199`
   - Gate 0.3 Virgin Final Holdout: `214200..214249`
   - Prospective Tournament Cohort: `340300..340349`
3. Re-use previously consumed development cohorts:
   - Retired Cohorts: `50000..50024`, `249000..249049`, `249050..249110`
   - Phase 011 Group 1 Cohort: `249111..249170`
   - Phase 012 Group 2 Cohort: `249171..249230`
   - Phase 013 Group 3 Pilot Cohort: `249231..249240`
4. Modify `submission_Vj_kc_v3.tar.gz` (frozen chassis).
5. Modify the live empirical foundation configuration.
6. Promote any mechanism to production.
7. Loosen safety gates or tune heuristic thresholds to fabricate positive results.
8. Automatically implement a "Group 4" mechanism.

---

## 3. Baseline & Control Definitions

To eliminate ambiguity, two distinct definitions are maintained throughout all analyses:

### 3.1 Architectural Baseline
The complete algorithmic compilation pipeline of the Adaptive Economic Compiler:
$$\text{OBSERVE} \to \text{ECONOMIC IR} \to \text{V3 BACKBONE} \to \text{EVENT DETECTOR} \to \text{OPPORTUNITY DETECTOR} \to \text{CANDIDATE FUNNEL} \to \text{COUPLEDPATCH} \to \text{EXACT COUNTERFACTUAL} \to \text{SAFETY} \to \text{COMMIT / ABSTAIN}$$

### 3.2 Empirical Control
The frozen live agent configuration tested in Group 1, Group 2, and Group 3:
$$\text{V3 Chassis} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$
All Group 1, Group 2, and Group 3 experimental mechanisms are quarantined (`QUARANTINED_MECHANISMS`).

---

## 4. Competing Hypotheses

| Hypothesis | Description | Diagnostic Test |
| :--- | :--- | :--- |
| **H1: V3 Dominance** | V3 already operates near the optimal policy frontier across most sub-problems; headroom is negligible. | Oracle finds zero or marginal headroom across admissible local alternatives. |
| **H2: Detector Blindness** | Significant headroom exists, but current event/opportunity trigger predicates fail to recognize it. | Oracle finds large headroom in states where event/opportunity engines emit zero candidates. |
| **H3: Representation Gap** | Opportunity engine detects the scenario, but candidate generators cannot form the required transformation. | Opportunity is detected, but raw patch generation fails or produces malformed actions. |
| **H4: Compiler / Patch Gap** | The transformation is known, but CoupledPatch cannot coordinate multi-worker or reconnect constraints. | Candidate is generated but fails spatial validity, reconnect continuation, or pruning. |
| **H5: Horizon Insufficiency** | Value is realized only across deeper downstream horizons ($H > 18-36$ turns). | Candidate is negative/neutral at standard horizon $H=18$ but positive at $H=36$. |
| **H6: Mechanism Composition** | Value emerges only when multiple mechanism transformations are composed simultaneously. | Isolated transformations are $\le 0$, but coupled pairwise transformations yield net positive delta. |
| **H7: Opponent Contingency** | Advantage requires state-adaptive opponent reasoning (e.g. market preemption or collision avoidance). | Alternative trajectory outperforms baseline specifically under rival price/supply shifts. |
| **H8: Macro Policy Boundary** | Headroom is bottlenecked by the macro crop rotation / field assignment prior; local tactical patches cannot overcome it. | Headroom requires altering backbone macro policy rather than local tactical perturbations. |

---

## 5. State-Space Taxonomy & Profiling

Every baseline turn $t \in [0, 719]$ across fresh seeds is categorized across 6 orthogonal dimensions:

### 5.1 Worker State
- `productive`: Worker actively performing primary task (harvesting, planting, tending).
- `traveling`: Worker moving towards a destination tile with $>0$ travel steps remaining.
- `idle`: Worker executing `PASS` or waiting without active assignment.
- `carrying`: Worker carrying cargo near or at maximum capacity ($\ge 80\%$).
- `blocked`: Worker obstructed by map boundary, collision, or uncoordinated pathing.
- `reconnecting`: Worker executing trajectory continuation to rejoin baseline path.

### 5.2 Farm State
- `cash-rich`: Farm cash $> \$5,000$ with no near-term wage or seed obligations.
- `cash-constrained`: Farm cash $< \$500$ or insufficient for next day wage/seed cycle.
- `seed-constrained`: Zero inventory of required planting seeds for open mature fields.
- `feed-constrained`: Livestock feed inventory $< 2$ days of consumption.
- `shed-constrained`: Shed inventory $\ge 90$ units (capacity: 100).
- `terminal-constrained`: Turn $> 680$ with unliquidated field or shed assets.
- `resource-constrained`: Workable raw materials present but processing tools/hands missing.

### 5.3 Market State
- `normal`: Prices within $\pm 10\%$ of historical baseline.
- `favorable`: Sale prices $> +15\%$ above baseline; buying prices discounted.
- `unfavorable`: Depressed prices due to market supply saturation.
- `opportunity_window`: Transient price spike or impending town demand consumption tick.
- `saturation_risk`: High risk of price crash due to concurrent market dumps.
- `liquidity-sensitive`: Transactions critical to fund immediate subsequent turns.

### 5.4 Production State
- `normal`: Standard crop maturation cycle progressing.
- `bottlenecked`: Mature crops unharvested due to labor shortage or shed blockage.
- `idle`: Unplanted cultivated fields.
- `dependency-limited`: Secondary processing blocked awaiting primary inputs.
- `terminal-focused`: Production halted in preparation for endgame clearance.

### 5.5 Terminal State
- `far_from_terminal`: Turn $t < 600$.
- `terminal_runway_sufficient`: $600 \le t < 680$ with sufficient runway to clear assets.
- `terminal_runway_tight`: $680 \le t < 710$ with risk of unharvested/unsold crop waste.
- `liquidation_phase`: $710 \le t < 718$ active raw/processed liquidation.
- `shutdown_phase`: $t \ge 718$ final operations freeze and passive cash preservation.

### 5.6 Opponent State
- `low_pressure`: Rival distant, operating in disjoint market commodities.
- `moderate_pressure`: Rival active in shared commodities without immediate dump threat.
- `high_pressure`: Rival poised to dump or clear market liquidity.
- `ambiguous_pressure`: Incomplete rival visibility or conflicting movement signals.

---

## 6. Definition of Potential Headroom State

A state is flagged as an **Interesting / Potential Headroom State** if any of the following 16 diagnostic indicators are triggered:
1. `IDLE_WORKER_MATURE_CROP`: Worker executing `PASS` while a mature unharvested tile exists within Manhattan distance $\le 5$.
2. `WORKER_BOTTLENECK`: All workers traveling while mature crops are at risk of decay.
3. `LARGE_UNCOMMITTED_INVENTORY`: Shed inventory $> 50$ units while current market order queue is empty.
4. `CASH_TEMPORARILY_IDLE`: Cash $> \$3,000$ at day start with zero land purchases, hires, or seed investments scheduled.
5. `CASH_SHORTAGE_WAGE_RISK`: Cash $< \text{daily wage bill}$ within 6 turns of day boundary.
6. `MARKET_PRICE_SPIKE`: Current market price $> 25\%$ above baseline average for an asset in shed.
7. `MARKET_PRICE_COLLAPSE`: Impending saturation or negative price delta on held assets.
8. `MATURE_CROP_NEAR_TERMINAL`: Unharvested mature crop at turn $> 680$.
9. `UNUSED_SHED_CAPACITY`: Shed utilization $< 20\%$ during mid-game harvest phase.
10. `UNUSED_WORKER_CAPACITY`: Worker carrying 0 cargo while adjacent to harvested produce.
11. `PRODUCTION_INPUT_MISMATCH`: Raw inventory present in shed with available worker but no conversion orders.
12. `DEPENDENCY_BOTTLENECK`: Worker waiting for upstream harvest or market delivery.
13. `MARKET_COLLISION`: Shared sell order with opponent on identical asset slot.
14. `OPPONENT_PRESSURE`: Rival worker carrying large cargo approaching delivery tile.
15. `ROUTE_CONGESTION`: Two workers sharing or blocking adjacent movement corridors.
16. `TERMINAL_RUNWAY_ASYMMETRY`: Baseline plans multi-step production when raw liquidation yields higher net cash.

---

## 7. Bounded Oracle Headroom Probe

The Oracle Probe is an offline diagnostic evaluator using the exact simulator:
$$\Delta_{\text{oracle}} = \max_{a \in \mathcal{A}_{\text{bounded}}} V(a) - V(a_{\text{baseline}})$$

### Admissible Action Transformations $\mathcal{A}_{\text{bounded}}$:
1. **Worker Transformations**:
   - Alternate Task: Switch `PASS` / `MOVE` to `HARVEST`, `PLANT`, `WATER`, `TEND`.
   - Alternate Route: 1-step spatial detour avoiding bottleneck or taking direct path.
   - Alternate Harvest: Prioritize higher-value crop tile over baseline target.
   - Worker Reassignment: Swap tasks between Farmer and Hands.
2. **Market Transformations**:
   - Alternate Timing: Frontload sell by 1 turn or delay sell by 1 turn.
   - Alternate Sizing: Split bulk order into tranche or liquidate 100% of inventory.
   - Buy Timing: Accelerate seed purchase to avoid day-boundary cash squeeze.
3. **Resource Transformations**:
   - Produce vs Keep: Convert available raw materials vs hold for raw sale.
   - Convert vs Buy: Local production vs shop procurement.
4. **Terminal Transformations**:
   - Terminal Liquidation Sweep: Immediate dump of all shed assets at $t \ge 710$.
   - Terminal Route Truncation: Abort long return transit and execute terminal harvest.
5. **Multi-Worker Transformations**:
   - Coordinated Harvest: Helper worker collects produce dropped by lead harvester.
6. **Emergency Transformations**:
   - Emergency Feed Buy: Procure feed when livestock starvation projected within 2 days.
7. **Opponent-Contingent Transformations**:
   - Preemptive Sell: Clear market 1 turn prior to anticipated rival dump.

### Result Categories:
- **Category A (Zero Headroom)**: $\Delta_{\text{oracle}} \le 0$. Baseline is local upper envelope.
- **Category B (AEC Active & Captured)**: $\Delta_{\text{oracle}} > 0$, current AEC detects and commits candidate.
- **Category C (Detector Blindness)**: $\Delta_{\text{oracle}} > 0$, but current event/opportunity engines emit zero candidates.
- **Category D (Candidate Representation Defect)**: $\Delta_{\text{oracle}} > 0$, candidate generated but actions malformed or incomplete.
- **Category E (Compiler / Reconnect Failure)**: $\Delta_{\text{oracle}} > 0$, but CoupledPatch reconnect fails or desynchronizes.
- **Category F (Horizon Insufficiency)**: $\Delta_{\text{oracle}} > 0$ only at extended horizon ($H=36$).
- **Category G (Compositional Headroom)**: $\Delta_{\text{oracle}} > 0$ only when two transformations are applied simultaneously.
- **Category H (Opponent Contingency)**: $\Delta_{\text{oracle}} > 0$ dependent on rival action scenario.
- **Category I (Macro Policy Constraint)**: Headroom requires altering global macro rotation.

---

## 8. Causal Attribution Hierarchy

For every sampled state where $\Delta_{\text{oracle}} > 0$, exactly one primary failure layer is assigned:
$$\text{HEADROOM} \xrightarrow{(1)} \text{NOT\_DETECTED} \xrightarrow{(2)} \text{NOT\_REPRESENTED} \xrightarrow{(3)} \text{FILTERED} \xrightarrow{(4)} \text{NOT\_PATCHABLE} \xrightarrow{(5)} \text{RECONNECT\_FAILED} \xrightarrow{(6)} \text{HORIZON\_INSUFFICIENT} \xrightarrow{(7)} \text{COUNTERFACTUAL\_REJECTED} \xrightarrow{(8)} \text{SAFETY\_REJECTED}$$

---

## 9. Certified Fresh Cohort Allocation

- **Diagnostic Block 1**: Seeds `249241..249250` (N=10 seeds, 20 mirror matches, 14,400 turns).
- **Expanded Audit Block**: Seeds `249251..249275` (N=25 seeds, 50 mirror matches, 36,000 turns).
- Total Fresh Census: 35 unique seeds, 70 mirror matches, **50,400 total turns**.
- All protected holdout and tournament cohorts remain untouched.
