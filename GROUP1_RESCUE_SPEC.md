# AEC PHASE 011: GROUP 1 RESCUE SPECIFICATION
## Second-Generation Economic Redesign for Dynamic Harvest, Terminal Harvest, Route Compression, and Cargo Ferry

**Author**: Antigravity AI Research Agent (Phase 011 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governing Architecture**: AEC Adaptive Economic Compiler (§0–§32)

---

## 1. Core Economic Rescue Principle

The fundamental hypothesis of the Phase 011 Group 1 Rescue is:

> *The true value of these mechanisms is not the immediate localized action. It is the economic value of the state transition they create.*

Under first-generation implementations, mechanisms were evaluated as isolated spatial actions (e.g. "is harvesting faster?", "is the route shorter?"). In competitive play against a strong V3 greedy baseline, such local optimizations are almost always redundant ($\Delta = \$0$) or counterproductive ($\Delta < \$0$) because they divert labor from established baseline tasks without pricing downstream effects.

In second-generation formulations, every mechanism is redesigned as a **Coupled Trajectory Transformation**:
$$\Delta V_{\text{net}} = V_{\text{candidate\_trajectory}} - V_{\text{baseline\_continuation}}$$
where $V$ is evaluated via **authoritative exact counterfactual forward simulation** under calibrated opponent pressure.

---

## 2. Dynamic Shadow Harvest ("Harvest + Released Productive Time")

### A. Economic Theory
Harvesting a mature crop does not merely generate cargo; it:
1. Prevents biological rot / decay.
2. Clears the farm tile for subsequent planting or soil management.
3. Fills worker cargo toward optimal hauling batch sizes.
4. **Releases worker time**: By completing harvest earlier or batching adjacent crops, subsequent turns in the worker's schedule are unlocked for productive tasks.

### B. Mathematical Formulation
A coupled harvest candidate produces a trajectory:
$$\mathcal{T}_{\text{harvest}} = \big[\text{Route}(w \to c) \to \text{HARVEST}(c) \to \text{Batch}(c_{\text{adj}}) \to \text{Route}(c \to \text{Shed}) \to \text{DROP} \to \text{SELL} \to \text{Reconnect} \to \text{Suffix}_{\text{productive}}\big]$$

The objective function evaluated by the compiler is:
$$\Delta V_{\text{trajectory}} = \Pi_{\text{direct\_crop}} + \Delta \Pi_{\text{timing}} + \sum_{t \in \text{released}} \lambda_{\text{labor}}(w, t) - \text{OppCost}_{\text{baseline\_tasks}} - \text{DisruptionCost}$$
where $\lambda_{\text{labor}}(w, t)$ is the marginal shadow productivity of worker $w$ at time $t$ derived from the baseline continuation.

### C. Architectural Enhancements
1. **Multi-Crop Cluster Batching**: If adjacent tiles $(x \pm 1, y \pm 1)$ contain mature crops and worker cargo capacity allows ($q < 3$), worker harvests adjacent crops in the same run before executing transit to shed.
2. **True Splicing Reconnect**: Reconnection is calculated against the ground-truth read-only future continuation from the V3 backbone (`future_trajectory`), preserving downstream baseline tasks.
3. **Adaptive Horizon**: Escalate rollout horizon ($H = 18 \dots 28$) whenever a harvest unblocks downstream tasks, ensuring value realization occurs inside the simulation window.

---

## 3. Terminal Harvest Sweep ("Terminal Economic Sweep")

### A. Economic Theory
Terminal harvest is not a blind late-game sweep. In the final phase ($t \ge 670$), turns are strictly finite. The value of a terminal candidate depends on:
1. Feasibility of realization: Can the crop be harvested, transported, and sold before turn 718?
2. Existing cargo monetization: Does a worker already carry valuable items that should be delivered immediately rather than harvesting more?
3. Opportunity cost against terminal liquidation and obligations.

### B. Mathematical Formulation & Feasibility Proof
For any proposed terminal sequence initiated at step $t_{\text{cur}}$, the arrival step at the market must satisfy:
$$t_{\text{sale}} = t_{\text{cur}} + d(w, \text{target}) + t_{\text{harvest\_actions}} + d(\text{target}, \text{shed}) + 1 \le 718$$
If $t_{\text{sale}} > 718$, the candidate is **strictly rejected as physically infeasible** before simulation.

### C. Flexible Terminal Action Shapes
Rather than enforcing a monolithic `route -> harvest -> shed -> drop -> sell` template, the compiler synthesizes the optimal shape:
- **Shape 1 (Full Salvage)**: `route -> harvest -> shed -> drop -> sell` (when $t_{\text{sale}} \le 718$).
- **Shape 2 (Direct Cargo Liquidation)**: If worker already carries cargo ($q \ge 1$), `route -> shed -> drop -> sell` without diverting to new crops.
- **Shape 3 (Local Salvage)**: `harvest` only, if adjacent to shed or if end-of-game rules credit on-field inventory.
- **Shape 4 (Maturing Crop Intercept)**: Schedules harvest for crops reaching maturity between steps 670 and 715 at their exact maturity turn.

---

## 4. Economic Route Compression

### A. Economic Theory
Shortest path routing is an engineering metric, not an economic one. In a multi-agent economic simulation:
- A route with fewer steps that delays a market order past a town tick is harmful.
- A route that reorders tasks to complete a high-value task 2 turns earlier is economically beneficial even if total distance traversed is identical.

### B. Mathematical Formulation
Given a baseline worker trajectory prefix $P_{\text{base}} = [a_1, a_2, \dots, a_k]$ and a candidate compressed prefix $P_{\text{comp}} = [a'_1, a'_2, \dots, a'_m]$ with $m < k$:
$$\Delta t_{\text{released}} = k - m$$
The candidate trajectory splices $P_{\text{comp}}$ followed by a reconnect bridge $B$, reconnecting to baseline at waypoint $W$. The released turns $\Delta t_{\text{released}}$ are backfilled by pulling forward baseline downstream tasks:
$$P_{\text{candidate}} = P_{\text{comp}} \mathbin{\Vert} B \mathbin{\Vert} \text{ShiftedSuffix}(P_{\text{base}}, \Delta t_{\text{released}})$$

### C. Constraints
1. **Spacetime Reservation Compliance**: All movements in $P_{\text{comp}}$ and bridge $B$ must pass multi-worker reservation checks against co-worker trajectories.
2. **Exact Suffix Preservation**: All downstream commitments (watering, feeding, scheduled market orders) must be preserved or accelerated.

---

## 5. Cargo Ferry ("Multi-Worker Marginal Value")

### A. Economic Theory
Assigning an auxiliary worker (Hand) to haul cargo is only economically justified if:
1. The **Primary Worker (Farmer)** is a binding bottleneck (e.g. carrying cargo away from high-priority field operations).
2. The **Helper (Hand)** has low marginal productivity elsewhere ($\text{OppCost}_{\text{helper}} < \text{Value}_{\text{transport}}$).
3. The **Coupled Trajectory** releases the Primary Worker to execute productive field labor immediately.

### B. Mathematical Formulation
A Cargo Ferry candidate is a **simultaneous two-worker coupled patch**:
$$\Delta V_{\text{ferry}} = V\big(\mathcal{T}_{\text{primary}}^{\text{field}}, \mathcal{T}_{\text{helper}}^{\text{haul}}\big) - V\big(\mathcal{T}_{\text{primary}}^{\text{haul}}, \mathcal{T}_{\text{helper}}^{\text{baseline}}\big)$$

Where:
- $\mathcal{T}_{\text{primary}}^{\text{field}}$: Primary Worker transfers cargo or leaves deposit duty, immediately performing field tasks (planting, watering, harvesting).
- $\mathcal{T}_{\text{helper}}^{\text{haul}}$: Helper collects cargo, travels to shed, deposits, sells, and reconnects to its baseline queue.

### C. Activation Preconditions
1. Primary worker has cargo $q \ge 2$ and distance to shed $d \ge 3$.
2. Primary worker has reachable unserviced field tasks.
3. Helper worker is within coordination distance ($\le 3$ steps) with available capacity.
4. Helper opportunity cost $\le 0.5 \times \text{Cargo Value}$.

---

## 6. Splicing Architecture & Pipeline Integration

To guarantee that candidate rollouts match baseline physics and avoid spatial desynchronization:
1. `AECExecutor.act()` fetches `future_trajectory` (and derives `co_worker_trajectories`) **before** invoking `PatchGenerator.generate_patches()`.
2. `PatchGenerator` injects ground-truth `future_trajectory` into all reconnect requests.
3. `CounterfactualSimulator` verifies that `spliced_continuation` maintains strict spatial continuity at the handoff point, eliminating false `commands = PASS` degradation.
4. `select_adaptive_horizon()` dynamically chooses:
   - $H = 12$: Local execution confirmation.
   - $H = 18$: Normal coupled harvest and route compression.
   - $H = 24$: Multi-worker cargo ferry and multi-crop batching.
   - $H = \min(24, 718 - \text{step})$: Terminal sweep.
