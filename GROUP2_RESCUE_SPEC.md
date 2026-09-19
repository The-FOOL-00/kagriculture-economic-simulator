# AEC PHASE 012: GROUP 2 RESCUE SPECIFICATION
## Second-Generation Economic Redesign for Town/Cycle Intelligence, Emergency Recovery, Opponent Preemption, and Resource Conversion

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governing Architecture**: AEC Adaptive Economic Compiler (§0–§43)

---

## 1. Core Economic Rescue Principle: State-Transition Valuation

The central economic thesis for Group 2 mechanisms is:

> **Never value the immediate action alone. Value the complete economic state transition.**

A first-generation mechanism treated actions as static, isolated queries (e.g. "is price higher in 2 turns?", "is cash below wage threshold right now?"). In competitive farm management, any action in turn $t$ propagates downstream, shifting liquidity, worker trajectories, shed headroom, and market clearing depth across future turns.

Every second-generation Group 2 candidate is formulated as a complete state transition:
$$\text{Current State} \to \text{Transformation} \to \text{Released / Protected Resources} \to \text{Downstream Effects} \to \text{Terminal State}$$

The candidate is evaluated strictly by exact counterfactual forward simulation against the frozen empirical control:
$$\Delta V_{\text{net}} = V\big(\mathcal{T}_{\text{candidate\_continuation}}\big) - V\big(\mathcal{T}_{\text{baseline\_continuation}}\big)$$
where $V$ measures total realizable economic wealth:
$$\text{Wealth} = \text{Cash} + \sum_{p} \text{ShedUnits}(p) \cdot \text{MarketPrice}(p) + \sum_{w} \sum_{p} \text{CarriedUnits}(w, p) \cdot \text{MarketPrice}(p) + \text{AssetBookValue}$$

---

## 2. Mechanism A: Economic Cycle Timing (`TOWN_CYCLE`)

### 2.1 Economic Theory & Redesign
The purpose of cycle intelligence is **not** to blindly hold inventory whenever a town demand refresh is near. Its purpose is to **identify an inter-temporal timing transformation** where changing the sequence of town/market interactions improves the complete downstream trajectory without jeopardizing working capital.

### 2.2 Structural Liquidity Safety Model
Arbitrary safety buffers (e.g. "$50 buffer") are completely eliminated. Required liquidity is derived dynamically from actual upcoming structural obligations:
$$\text{RequiredLiquidity}(t, H) = \sum_{\tau=t}^{t+H} \Big(\text{MandatoryPurchases}(\tau) + \text{MandatoryFeed}(\tau) + \text{NightlyWages}(\tau) + \text{TerminalObligations}(\tau)\Big)$$

A `DELAY_SALE` candidate is permitted **only if**:
$$\text{Cash}(t) - \text{RequiredLiquidity}(t, \text{delay\_steps}) \ge 0$$
$$\text{ShedStock}(t) + \text{InFlightHarvests}(t, \text{delay\_steps}) \le 0.85 \times \text{SHED\_CAPACITY}$$

### 2.3 Supported Transformation Families
1. **`DELAY_SALE`**: Defer sale of an inventory parcel by $\Delta t \in [1..3]$ steps if town shop absorption is imminent, provided working capital and shed headroom invariants are satisfied.
2. **`ADVANCE_SALE`**: Liquidate high-elasticity inventory immediately when town shop demand has just refreshed, capturing peak clearing prices before rival or natural saturation occurs.
3. **`PARTIAL_SALE`**: Staged liquidation that sells only the minimal parcel required to satisfy immediate obligations ($t \equiv 0 \pmod{24}$ seed purchases / wages), holding the surplus parcel for peak cycle pricing.
4. **`SALE_AFTER_DEPENDENCY`**: Delay sale until a field worker has dropped harvested crops at the shed, bundling drop and sale into a single consolidated transaction.
5. **`BUY_BEFORE_PRICE_HIKE`**: Advance mandatory seed/feed purchases before anticipated town demand shifts inflate input prices.

### 2.4 Mathematical Decision Gate
$$\Delta V_{\text{cycle}} = \Delta \Pi_{\text{timing\_gain}} + \Delta V_{\text{opportunity\_unlocked}} - \text{OpportunityCost}_{\text{delayed\_cash}} - \text{ElasticityPenalty}(\text{parcel\_size})$$

---

## 3. Mechanism B: Emergency Recovery as Damage Avoidance (`EMERGENCY_RECOVERY`)

### 3.1 Economic Theory & Redesign
Emergency Recovery is **not** an alternative macro-planner, nor is it a panic-selling engine. It is a **selective damage-avoidance circuit breaker**:
> *"Is the baseline trajectory entering an irreversible or materially damaging failure state, and is there a minimal intervention that prevents it?"*

### 3.2 Four-Stage Irreversibility Classification
Before any candidate is synthesized, the current state and baseline trajectory are classified:
1. **Reversible Degradation**: The condition naturally resolves itself (e.g. temporary cash dip before an already-scheduled sale) $\to$ **ABSTAIN**.
2. **Recoverable Degradation**: A normal baseline scheduled action recovers the state within 2 turns $\to$ **ABSTAIN**.
3. **Emerging Irreversible Loss**: Baseline crosses a threshold after which recovery becomes impossible or materially more expensive (e.g. animal has 2 turns before death and no worker is carrying feed; wages are due tonight and baseline has zero sales scheduled) $\to$ **SURGICAL RESCUE ALLOWED**.
4. **Current Hard Failure**: Invariant violation imminent on current turn $\to$ **EMERGENCY INTERVENTION REQUIRED**.

### 3.3 Minimal Surgical Interventions
The mechanism strictly adheres to minimal interventions and returns control to the V3 backbone immediately:
- **Livestock Starvation Rescue**:
  1. If feed (wheat) is present in shed: Command the nearest available worker to take feed from shed and feed the starving livestock tile.
  2. If feed is absent from shed: Pair an immediate single-unit market purchase (`["BUY_PRODUCT", "WHEAT", 1]`) with worker dispatch.
  3. The patch spans only the exact turns required to feed the animal; continuation is immediately spliced back to the V3 baseline.
- **Critical Wage Deficit Rescue**:
  1. Calculate exact deficit: $\text{Deficit} = \text{WagesTonight} - \text{Cash}$.
  2. Liquidate the **minimal parcel** of lowest-margin shed commodities required to cover $\text{Deficit}$.
  3. Strictly forbid fire-sale dumping of high-margin crops (strawberry/melon) beyond $\text{Deficit}$.

### 3.4 Avoided Damage Valuation
$$\Delta V_{\text{recovery}} = \text{AvoidedAssetLoss}(\text{Animal/Worker}) - \text{CostOfIntervention}(\text{Feed/Labor}) - \text{BaselineSplicingCost}$$

---

## 4. Mechanism C: Robust Opponent Preemption (`OPPONENT_PREEMPT_SELL`)

### 4.1 Economic Theory & Redesign
Opponent Preemption must never rely on point prophecies ("rival will definitely sell"). It must operate under **bounded uncertainty**:
> Capture high-value market or spatial opportunities before competition can devalue them, provided our own net terminal economic outcome is superior under all plausible opponent responses.

### 4.2 Decision Rule: Self-Value Dominance
$$\min_{s \in \mathcal{S}} \Big[ V\big(\mathcal{T}_{\text{preempt}} \mid s\big) - V\big(\mathcal{T}_{\text{baseline}} \mid s\big) \Big] > 0.0$$
where $\mathcal{S} = \{\text{Rival Dumps}, \text{Rival Holds}\}$.
- Preemption is approved **only if** our own terminal wealth improves even if the opponent does *not* dump.
- Decreasing opponent score is **never** credited as positive economic value.

### 4.3 Preemption Transformation Families
1. **Defensive Inventory Preemption**: Sell a bounded parcel of goods into high market depth when opponent has high mature inventory and town shop consumption is nearing capacity.
2. **Purchase Preemption**: Acquire scarce high-yield seeds (melon/strawberry) before market stock depletes or price escalates.
3. **Capacity Preemption**: Liquidate shed stock to preserve drop-off capacity when opponent field harvests threaten shared town market depth.
4. **Route-Space Preemption**: Coordinate worker transit through choke points to prevent spatial stalls.

---

## 5. Mechanism D: Margin-First Resource Conversion (`RESOURCE_CONVERSION`)

### 5.1 Economic Theory & Redesign
Resource conversion exists **only when** it converts a resource with low marginal utility into a target resource that materially improves the overall economic trajectory, net of capital lockup and labor opportunity cost.

### 5.2 Comparative Margin-First Valuation
For every candidate conversion $S \to T$, the compiler evaluates four mutually exclusive choices:
$$\Delta V_{\text{convert}} = \Pi(T) - \Pi(S) - \text{Cost}_{\text{inputs}} - \text{LaborOppCost}(w, \Delta t) - \text{LiquidityRiskPenalty}$$
compared directly against:
1. $\text{KEEP SOURCE}$: Retain $S$ in shed or field for baseline use/sale.
2. $\text{BUY TARGET}$: Directly purchase $T$ from market if available and affordable.
3. $\text{PRODUCE TARGET}$: Standard biological production pathway.

If $\Delta V_{\text{convert}} \le 0$, the candidate is pruned before simulation.

### 5.3 Labor Opportunity Cost Integration
Labor is never treated as free. Using the validated `LaborOpportunityCostEngine`:
$$\text{LaborOppCost}(w, \Delta t) = \sum_{\tau=t}^{t+\Delta t} \lambda_{\text{shadow}}(w, \tau)$$
where $\lambda_{\text{shadow}}$ is the marginal revenue of the worker's counterfactual baseline actions (planting, watering, harvesting).

### 5.4 Conversion Families & Runway Gates
1. **Feed Conversion**: Convert grain into livestock feed only when it prevents starvation or unlocks animal yield with $\text{Runway} \ge \text{YieldCycleDays}$.
2. **Seed Conversion**: Purchase/convert seed only when planting runway satisfies $718 - t \ge \text{GrowthDays} + 4$.
3. **Product Conversion**: Intermediate processing only if target product has guaranteed market demand before step 715.
4. **Terminal Conversion**: Dominated by direct `TERMINAL_LIQUIDATION`. Any terminal conversion must prove:
   $$\text{NetPrice}(T) - \text{NetPrice}(S) > \text{LaborDisplacementCost}$$
   Otherwise, raw inventory is routed directly to shed liquidation.

---

## 6. Event Detector Remediation (§29)

To eliminate the `NO_EVENT_FAST_PATH` exposure starvation, `aec/events/event_types.py` and `aec/events/detectors.py` are extended with deterministic event triggers:
1. **`E9_LIVESTOCK_STARVATION_RISK`**: Fired when any animal on farm has $\text{turns\_to\_starve} \le 8$ and no worker is currently carrying feed to it.
2. **`E10_TOWN_CYCLE_PHASE`**: Fired during the town refresh anticipation window ($t \pmod{72} \in [64..71]$) and at consumption boundaries ($t \pmod 4 == 0$).
3. **`E11_OPPONENT_PRESSURE_SHIFT`**: Fired when continuous opponent sale or buy pressure shifts by $>0.30$.
4. **`E12_RESOURCE_BOTTLENECK`**: Fired when wheat inventory in shed is less than total herd feed requirements for the next 24 turns.

---

## 7. Adaptive Horizon Escalation

Group 2 transformations alter multi-turn state variables (cash, inventory, animal life). Horizons escalate adaptively:
- **Short ($H=6$)**: Immediate minimal emergency wage liquidations, local obstacle bypass.
- **Medium ($H=18$)**: Town cycle advance/partial sales, route-space preemption.
- **Extended ($H=36$)**: Delayed cycle sales, livestock feed delivery, resource conversion chains, terminal liquidations.

Every escalation records its formal justification in telemetry.
