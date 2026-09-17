# AEC-RESOURCE: Feed Security & Dynamic Inventory Conversion DAG
## Architectural Specification (Phase 002)

### Executive Summary

AEC-RESOURCE establishes dynamic, time-aware resource reasoning within the Kagriculture Adaptive Economic Compiler (AEC). Rather than relying on static inventory checks or disconnected heuristic rules, AEC-RESOURCE models resource transformations, obligations, and temporal flow through a formal **Time-Expanded Resource Directed Acyclic Graph (DAG)** coupled to a deterministic **Feed Security Engine**.

Candidate patches proposing inventory alterations (e.g. buying feed, selling commodities, processing raw materials, altering worker feeding routes) must pass through:
1. Structural dependency closure and conservation checks on the temporal DAG.
2. Exhaustive interval feed-security verification across all livestock obligations.
3. AEC-RECONNECT trajectory repair if worker movement is altered.
4. Exact counterfactual rollout simulation.
5. Invariant certification via the 9 extended resource checks in `SafetyCertificate`.

Any invariant breach, intermediate liquidity deficit, capacity overflow, starvation risk, or simulator mismatch results in an immediate, deterministic **ABSTAIN -> BACKBONE**.

---

### 1. Data Model & Temporal DAG

The core abstraction is defined in `aec/resource/dag.py`. Resources are discrete entities pinned to a specific turn $t$, location, provenance, and storage domain.

#### 1.1 Core Entities

- **`ResourceNode`**:
  Represents a discrete quantity $q \ge 0$ of a commodity at a discrete turn $t$.
  - `commodity`: Resource identifier (e.g. `HAY`, `MILK`, `WHEAT`, `CASH`).
  - `quantity`: Float / integer units.
  - `turn`: Time step $t \in [0, T]$.
  - `location`: Grid coordinates `(x, y)` or facility name (`"SHED"`, `"MARKET"`).
  - `capacity_domain`: Domain binding (`"SHED"`, `"CARGO"`, `"FIELD"`, `"FINANCIAL"`).
  - `provenance`: Origin of the resource (`"INITIAL"`, `"HARVEST"`, `"PURCHASE"`, `"ANIMAL_PRODUCT"`, `"CONVERSION"`).
  - `is_reserved`: Boolean indicating active reservation.

- **`ResourceEdge`**:
  Directed causal transformation link between source nodes $\{u_i\}$ at $t_{\text{start}}$ and destination nodes $\{v_j\}$ at $t_{\text{complete}}$.
  - `edge_id`: Unique identifier.
  - `source_nodes`: Input node IDs consumed or transferred.
  - `dest_nodes`: Output node IDs created.
  - `action`: Semantic operation (`"BUY"`, `"SELL"`, `"FEED"`, `"PROCESS"`, `"TRANSFER"`, `"HARVEST"`).
  - `start_turn`, `completion_turn`: Latency interval $[t_s, t_c]$ where $t_c \ge t_s$.
  - `cash_delta`: Direct cash flow associated with execution.
  - `capacity_delta`: Net shed/cargo space impact.
  - `worker_required`: Worker slot dependency.
  - `is_reversible`: Boolean (default `False`, all physical consumption is strictly irreversible).
  - `obligation_dependencies`: Tuple of obligation IDs unlocked or required.

- **`ResourceObligation`**:
  Mandatory future resource requirement that cannot be breached without severe penalty or game-over.
  - `obligation_id`: Unique identifier.
  - `commodity`: Required resource type.
  - `quantity`: Required units.
  - `due_turn`: Turn $t_{\text{due}}$ by which resource must be present.
  - `severity`: `"MANDATORY"` (e.g. livestock feed, seed for pre-scheduled planting) or `"STRATEGIC"`.
  - `consequence`: Consequence of breach (`"ESCAPE"`, `"PRODUCTION_HALT"`, `"PENALTY"`).

- **`ResourceReservation`**:
  Explicit lock binding a specific `ResourceNode` to a `ResourceObligation` or pipeline task, preventing double-allocation across competing consumers.

#### 1.2 Conservation Laws & Invariants

For every commodity $C$ and across all time steps $t$, the DAG enforces:
$$\text{Inventory}(C, t) = \text{Inventory}(C, t-1) + \sum \text{Produced}(C, t) + \sum \text{Purchased}(C, t) - \sum \text{Consumed}(C, t) - \sum \text{Sold}(C, t)$$

Conservation checks verify:
1. $\text{Inventory}(C, t) \ge 0 \quad \forall C, t$ (No negative inventory).
2. Total occupied shed volume $\le \text{ShedCapacity}$ at every turn $t$.
3. No resource node $u$ may have its quantity allocated to two conflicting reservations ($\sum \text{Reserved}(u) \le \text{Quantity}(u)$).
4. Temporal availability: An edge cannot consume node $u$ before $u.\text{turn}$.

---

### 2. Feed Security Engine

The Feed Security Engine (`aec/resource/feed_security.py`) implements deterministic care and starvation forecasting for livestock entities across the decision horizon.

#### 2.1 Livestock Semantics (Authoritative Simulator Ground Truth)

The Kagriculture simulator specifies the following exact mechanics for livestock:
- **Species**: `COW`, `SHEEP`, `GOOSE`.
- **Feed Item**: `HAY` (1 unit per animal per turn).
- **Daily Feeding Sequence**:
  - Each living animal requires 1 unit of `HAY` delivered or available in the shed per turn.
  - **Fed State**: Animal is satisfied; care bonus incremented; standard production cycle advances (Milk, Wool, Feather).
  - **Unfed State (Day 1)**: Animal starves for 1 turn. Production stops; care bonus reset to 0; animal enters `unfed_days = 1`.
  - **Unfed State (Day 2 - Consecutive)**: Animal reaches `unfed_days \ge 2`. **Animal escapes / dies**, permanently removing asset value, production pipeline potential, and inventory value from the farm.

#### 2.2 Feed Trajectory & Surplus Calculus

For every turn $\tau \in [t, t+H]$, the engine evaluates:
$$\text{FeedSurplus}(\tau) = \text{FeedAvailable}(\tau) + \text{ConfirmedIncoming}(\tau) - \text{MandatoryConsumption}(\tau) - \text{ReservedFeed}(\tau)$$

Where:
- $\text{FeedAvailable}(\tau)$: Current inventory carried forward.
- $\text{ConfirmedIncoming}(\tau)$: Confirmed arrivals from market purchases or deliveries.
- $\text{MandatoryConsumption}(\tau) = \sum_{a \in \text{Livestock}} \text{DailyRequirement}(a)$.
- $\text{ReservedFeed}(\tau)$: Feed locked by already committed downstream schedules.

**Safety Invariant**: If $\text{FeedSurplus}(\tau) < 0$ at any turn $\tau$, or if consecutive starvation causes animal escape ($\Delta \text{Escaped} > 0$), the candidate patch is rejected immediately with a feed security failure.

---

### 3. Dynamic Conversion Engine

Defined in `aec/resource/conversions.py`, the dynamic conversion engine discovers and evaluates potential resource transformation paths.

#### 3.1 Conversion Catalog

The engine maintains a catalog of valid, verified game recipes:
1. `FEED_TO_MILK`: 1 Cow + 1 Hay + 1 Turn $\to$ 1 Milk.
2. `FEED_TO_WOOL`: 1 Sheep + 1 Hay + 2 Turns $\to$ 1 Wool.
3. `FEED_TO_FEATHER`: 1 Goose + 1 Hay + 1 Turn $\to$ 1 Feather.
4. `WHEAT_TO_HAY`: 1 Wheat + 1 Turn $\to$ 1 Hay (Processing).
5. `WHEAT_TO_SEED`: 1 Wheat + 1 Turn $\to$ 2 Wheat Seeds (Recycling).
6. `BUY_HAY`: Cash ($P_{\text{hay}}$) $\to$ 1 Hay (Market timing).

#### 3.2 Feasibility & Hole Checks

Every conversion chain is evaluated for:
- **Cash Liquidity Hole**: Evaluates net cash trajectory at each intermediate step $t' \in [t, t+k]$. If intermediate cash dips below minimum liquid buffer (cash $< 0$), the conversion is marked infeasible.
- **Shed Capacity Overflow**: Checks whether intermediate or product inventory causes $\text{CurrentShedLoad} + \Delta \text{Volume} > \text{Capacity}$.
- **Terminal Horizon Pruning**: If remaining turns until episode termination $T - t < \text{Latency}$, the conversion cannot materialize or liquidate before end-of-game. The path is dropped.

---

### 4. Integration with AEC Compiler Passes

#### 4.1 Dependency Graph Integration

In `aec/ir/dependency_graph.py`, two new causal edge types were introduced:
- `RESOURCE_COUPLING`: Connects resource-producing actions (e.g. harvest, market buy, feed processing) to downstream resource consumers (e.g. sales, feed delivery).
- `FEED_SECURITY_COUPLING`: Enforces strict causal links between market hay orders, worker feed delivery routes, and animal production nodes.

When an inventory item's timing is shifted by $\Delta t$:
1. Upstream and downstream nodes in the `ActionBasketDependencyGraph` are identified via `RESOURCE_COUPLING`.
2. The full transitive closure is computed.
3. If closure spans beyond the local window, the compilation level automatically escalates (e.g. `LOCAL` $\to$ `DEPENDENCY_CLOSURE` $\to$ `EXTENDED_REPLAN`).

#### 4.2 Interaction with AEC-RECONNECT

When a resource conversion or feed purchase requires physical worker transport (e.g. diverting a worker to fetch hay from the shed or deliver feed to a pasture tile):
1. `ResourceOpportunityAnalyzer` synthesizes candidate actions and generates a `CoupledPatch`.
2. If the patch alters worker destination or timing, `AEC-RECONNECT` (`aec/reconnect/engine.py`) is invoked with a `ReconnectRequest`.
3. The Reconnect engine performs space-time reservation routing, validating waypoint feasibility against the worker reservation table.
4. If a valid, collision-free spliced trajectory is found, the spliced path is embedded into `CoupledPatch.reconnect_trajectory`.
5. If the route cannot be reconnected or breaches timing constraints, the patch is **abstained**.

#### 4.3 Counterfactual Simulator Integration

The candidate patch and its spliced continuation are passed to `CounterfactualSimulator` (`aec/counterfactual/simulator.py`).
- Exact simulator step logic advances inventory, cash, worker coordinates, and livestock state turn by turn.
- Daily livestock health and starvation counters are tracked in `ShadowRolloutState`.
- Any starvation escape or negative inventory encountered during rollout sets `feed_security_ok = False` or `resource_conservation_ok = False` on the resulting `SimulationOutcome`.

#### 4.4 Safety Certificate Extension

`SafetyCertificate` (`aec/safety/certificate.py`) and `SafetyChecker` (`aec/safety/checks.py`) enforce 9 formal invariants:
1. `resource_conservation_check`: Strict input/output balance across all resources.
2. `negative_inventory_check`: No commodity drops below 0 at any turn.
3. `conversion_precondition_check`: All recipe inputs and facilities exist prior to conversion start.
4. `feed_security_check`: Zero animal starvation escapes across the rollout horizon.
5. `capacity_consistency_check`: Shed inventory never exceeds max capacity.
6. `cash_liquidity_check`: Zero negative cash balances across intermediate steps.
7. `temporal_availability_check`: Resources are only consumed at or after their arrival turn.
8. `reservation_consistency_check`: Zero double-allocated resource units.
9. `terminal_resource_check`: No stranded, unharvestable, or unliquidatable conversions near terminal turn.

---

### 5. Adaptive Horizon Escalation

AEC-RESOURCE respects the hierarchical horizon architecture established in Checkpoint 001:
- **Level 1 (LOCAL)**: Evaluates turn $t$ immediate balance.
- **Level 2 (DEPENDENCY_CLOSURE)**: Traces all causal edges linked to affected resources.
- **Level 3 (MEDIUM_REPLAN)**: Evaluates medium-range interaction (3–8 turns) for livestock feed replenishment cycles.
- **Level 4 (EXTENDED_REPLAN)**: Evaluates multi-stage conversion chains (e.g. wheat $\to$ seed $\to$ crop $\to$ harvest).
- **Level 5 (FULL_REPLAN)**: Full episode terminal validation.

If a candidate appears profitable at `LOCAL` level but creates a deficit within `DEPENDENCY_CLOSURE`, the candidate is rejected. Conversely, if a candidate has downstream consequences beyond the local window, the planner escalates rather than making an uninformed local decision.

---

### 6. Computational Complexity & Tractability

- **DAG Construction**: Operates on $|V|$ nodes and $|E|$ edges bounded by active farm commodities ($< 20$) and rollout horizon $H \le 12$. Complexity: $\mathcal{O}(|V| + |E|) \approx \mathcal{O}(H)$.
- **Dependency Closure**: Breadth-first traversal over causal edges: $\mathcal{O}(|V| + |E|)$.
- **Feed Security Forecast**: Linear scan across livestock population $N \le 10$ over horizon $H \le 12$: $\mathcal{O}(N \times H)$.
- **Empirical Overhead**:
  - DAG Construction: $\approx 0.018$ ms.
  - Dependency Closure: $\approx 0.003$ ms.
  - Feed Security Engine: $\approx 0.051$ ms.
  - Conversion Discovery: $\approx 0.011$ ms.
  - **Total Overhead**: $< 0.1$ ms per evaluation, fully within real-time turn latency budgets ($< 100$ ms).
