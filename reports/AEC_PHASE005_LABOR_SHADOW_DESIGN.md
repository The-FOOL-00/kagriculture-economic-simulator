# SPDX-License-Identifier: MIT
# AEC Phase 005: Generic Labor Shadow Valuation & Opportunity-Cost Engine
## Technical Architecture & Mathematical Specification

**Phase**: AEC Phase 005  
**Component**: `LaborOpportunityCostEngine` (`aec/resource/labor_engine.py`, `aec/economic/`)  
**Status**: Implemented / Offline Micro-Validated / Tested  
**Chassis**: Frozen V3 (`submission_Vj_kc_v3.tar.gz`) — SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Target Population**: Offline Development Cohort `50000–50024` (Diagnostic Replay Only)  
**Scientific Isolation**: Prospective cohort `340300–340349` untouched; holdout cohorts `340050–340199` and `214200–214249` untouched. `RESOURCE_CONVERSION` quarantined.

---

### 1. Architectural Motivation & Problem Formulation

In AEC Phase 004B, all direct implementation defects of `RESOURCE_CONVERSION` were successfully resolved:
1. Classification hygiene: 100% of pure market seed purchases were excluded from conversion.
2. Farmer preservation: 0 Farmer displacements across 200 matches; 100% auxiliary absorption.
3. Liquidity verification: Forward turn-by-turn working capital solvency enforced with 0 overdrafts.

Despite these fixes, empirical replay revealed an ITT paired mean delta of -$1417.54 across development seeds. Causal trace forensics demonstrated that when auxiliary Hand 1 was diverted from strawberry, melon, or tomato cultivation to feed livestock, the gross commodity revenue (e.g. +$135 from cow milk) was orders of magnitude smaller than the lost harvest yield from the uncultivated cash crop field (>$5,000 loss).

The architecture was missing a generic, cross-cutting capability:
$$\text{OpportunityCost}(\text{Worker } W, \text{Task } T, [t_0, t_1])$$

Phase 005 establishes this capability as a reusable, general-purpose service rather than a special-case heuristic.

---

### 2. Core Economic Model

#### 2.1 Baseline Trajectory Valuation $V_{\text{baseline}}(W, [t_0, t_1])$
The baseline trajectory projects worker $W$ executing their strong backbone actions over interval $[t_0, t_1]$.
The total economic value attributable to the baseline trajectory over horizon $H$ is:
$$V_{\text{baseline}} = M_{\text{base}}(t_0 + H) + S_{\text{base}}(t_0 + H) + C_{\text{base}}(t_0 + H) + P_{\text{base}}$$
where:
- $M_{\text{base}}$: Liquid cash balance at end of evaluation horizon.
- $S_{\text{base}}$: Market liquidation value of inventory in shed: $\sum_{p \in \text{PRODUCTS}} q_p \cdot \text{Price}(p)$.
- $C_{\text{base}}$: Carried cargo value in worker inventories: $\sum_{w} \sum_{p} q_{w, p} \cdot \text{Price}(p)$.
- $P_{\text{base}}$: Growing crop asset valuation across field tiles: $\sum_{\text{tile}} \text{TileValue}(\text{crop}, \text{growth}, \text{yield})$.

#### 2.2 Alternative Trajectory Valuation $V_{\text{alternative}}(W, T, [t_0, t_1])$
When worker $W$ is diverted to execute candidate task $T$ at step $t_0$, the trajectory diverges:
1. At $t_0$: Worker $W$ performs candidate command $C$.
2. At $[t_0 + 1, t_0 + K]$: Worker $W$ transits back to reconnect with their baseline continuation tape via `ReconnectionEngine`.
3. At $[t_0 + K, t_0 + H]$: Worker $W$ resumes baseline duties with timing shift $\Delta t$.
The alternative trajectory realization is evaluated under identical market and opponent pressure:
$$V_{\text{alternative}} = M_{\text{alt}}(t_0 + H) + S_{\text{alt}}(t_0 + H) + C_{\text{alt}}(t_0 + H) + P_{\text{alt}} - L_{\text{preservation}}$$
where $L_{\text{preservation}}$ accounts for severe penalties (e.g. livestock escaping due to missed feeding obligations).

#### 2.3 Marginal Labor Opportunity Cost & Net Incremental Value
The marginal labor opportunity cost represents the baseline value lost due to worker displacement:
$$\text{OpportunityCost} = \max(0, \text{CandidateGrossValue} - (V_{\text{alternative}} - V_{\text{baseline}}))$$
$$\text{NetIncrementalValue} = \text{CandidateGrossValue} - \text{OpportunityCost}$$

#### 2.4 Hard Invariant: No Ordinal-to-Dollar Cheating (§7)
TaskPriority values (1000 HARD, 900 TERMINAL, 800 LIVESTOCK, 700 RESOURCE, 600 HARVEST, 500 PRODUCTION, 400 MARKET, 100 OPPORTUNISTIC) are strictly ordinal scheduling priorities.
They are **never** converted into dollar amounts. All valuations stem directly from physical simulation, crop prices, yields, and commodity curves.

---

### 3. Valuation Level Hierarchy (Levels 0–4)

To balance computational tractability with causal fidelity, the engine implements five hierarchical valuation levels:

| Level | Valuation Tier | Valuation Mechanism | Trigger / Escalation Condition |
| :---: | :--- | :--- | :--- |
| **0** | **Feasibility** | Capability, bounds, reachability, day-boundary expiry (`step % 24 == 23`). | Candidate evaluation entry gate. Fails closed if infeasible. |
| **1** | **Local Exact Dependency** | Local state valuation; zero baseline loss verification. | Worker baseline is `PASS`/idle, no active cargo, no crop duties, no multi-worker coupling. |
| **2** | **Broader Worker Trajectory** | Peer absorption check via `MultiWorkerLogisticsCoordinator`. | Worker has active agricultural duties (`PLANT`, `WATER`, `HARVEST`, `FEED`) that peer absorbs. |
| **3** | **Wider Economic Replay** | Exact forward simulation via `simulate_rollout` under opponent pressure. | Worker displacement cannot be absorbed; cash constraints; livestock security; market timing. |
| **4** | **Full-Horizon Fallback** | Extended simulation to terminal horizon (step 718–720). | Late-game decisions (remaining steps $\le 72$); multi-day strawberry crop cycles; terminal liquidation. |

---

### 4. Worker Displacement & Dependency Attribution

#### 4.1 Non-Separable Multi-Worker Attribution (§12, §13)
When multiple workers cooperate in a production chain (e.g. Hand 1 plants strawberry seed, Hand 2 waters, Farmer harvests):
- The terminal revenue is not assigned independently as full value to each worker ($3 \times \$360 = \$1,080$).
- The marginal value of diverting Hand 1 is evaluated counterfactually: what happens if Hand 1 does not plant? The chain collapses, so the entire net margin of the crop is lost.
- If peer worker Hand 2 is available to absorb the planting without disrupting their own work, the task is preserved by peer absorption (`ABSORBED_BY_PEER`), and opportunity cost drops to peer transit overhead.

#### 4.2 Time Value & Finite Terminal Horizon (§14, §15)
The engine respects physical game timing without inventing discount rates:
- **Maturity Deadlines**: Crops planted too late to mature before step 720 yield $0.
- **Shop Consumption Waves**: Output produced too late to catch daily town shop liquidity misses market realization.
- **Livestock Feeding Windows**: Failing to feed an animal for 2 consecutive days triggers animal escape ($1,500 asset loss).

---

### 5. Fail-Closed Governance & Abstention Rules (§17)

The engine abstains (`safe_to_use = False`, `commit_recommendation = False`) under explicit failure modes:
1. `PHYSICALLY_INFEASIBLE`: Target out of bounds or unreachable within horizon.
2. `DAY_BOUNDARY_EXPIRY`: Auxiliary hand contract expires before task completion (`step % 24 == 23`).
3. `INSUFFICIENT_TRAJECTORY`: Baseline continuation tape missing or truncated.
4. `COUNTERFACTUAL_INCOMPLETE`: Spatial desynchronization or simulator state corruption detected.
5. `WORKER_STATE_INCOMPLETE`: Missing or uninitialized worker entity.
6. `FARMER_FALLBACK_PROHIBITED`: Prohibited primary labor cannibalization.

Zero arbitrary dollar thresholds exist. Decisions are determined strictly by $\text{NetIncrementalValue} > 0$ under verified safety.
