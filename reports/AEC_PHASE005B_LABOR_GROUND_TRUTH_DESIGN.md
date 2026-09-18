# SPDX-License-Identifier: MIT
# AEC Phase 005B: Labor Opportunity Engine Ground-Truth & Harvest Discovery
## Methodological & Architectural Design Specification

**Phase**: AEC Phase 005B  
**Component**: `LaborOpportunityCostEngine` (`aec/resource/labor_engine.py`)  
**Evaluation Scope**: Development Seeds `50000–50024`  
**Date**: September 2026  
**Status**: DESIGN CERTIFIED  

---

### 1. Executive Problem Statement & Objectives

In Phase 005, the generic **Labor Opportunity-Cost Engine** (`LaborOpportunityCostEngine`) was introduced to evaluate the marginal cost of diverting farm workers. While the initial micro-validation battery passed, Phase 005 made critical aggregate claims and valuation assumptions that required forensic verification:

1. **Accounting Reconciliation**: Phase 005 reported 888 historical opportunities evaluated (448 rejected, 440 approved) and recommended `DYNAMIC_SHADOW_HARVEST` on the claim that 440 opportunities represented idle workers passing while cash crops waited unharvested.
2. **Economic Equivalence**: Phase 005 evaluated labor value using finite-horizon proxy asset values (cash, shed inventory, carried cargo, and growing field assets). It was unknown whether this rollout-derived quantity agrees with the exact simulator's actual terminal economic objective ($\text{money}$ at step 720).
3. **Double-Counting & Field Valuation**: Growing field assets were valued tile-by-tile. If mature unharvested crops are counted as liquid inventory, the act of harvesting produces zero net asset delta, distorting opportunity cost.

The primary objective of Phase 005B is to **forensically ground-truth the labor engine against exact simulator terminal rewards** and perform an **unbiased discovery of genuine harvest candidates**.

---

### 2. Forensic Reconciliation Framework

The audit framework reproduces all historical records from `results/PHASE005_LABOR_DIAGNOSTIC.csv` and `results/PHASE004B_PATCHES.csv` without trusting prose summaries:

$$\sum \text{Records} = N_{\text{RESOURCE\_CONVERSION}} + N_{\text{MARKET\_TIMING}} + N_{\text{EMERGENCY\_FEED}} = 576 + 304 + 8 = 888$$

Each record is partitioned into rigorous epistemological classifications:
- **NO_LABOR_OPPORTUNITY**: Mechanisms that operate on market queues without worker allocation (`assigned_workers: []`).
- **IDLE_WORKER**: Auxiliary worker whose baseline command is `PASS` or `WAIT` with zero assigned duties.
- **BUSY_WORKER**: Auxiliary worker engaged in active baseline tasks (`CARE`, `FEED_ANIMAL`, `WATER`, `HARVEST`).
- **PEER_ABSORPTION**: Multi-worker states where an idle peer absorbs the displaced worker's task.
- **LABOR_REQUIRED**: Tasks requiring physical presence and worker execution.

---

### 3. Exact Simulator Counterfactual Ground-Truth Architecture

To test whether the engine's `net_incremental_value` agrees with the terminal game objective, exact counterfactual game completions are executed in `kagsim`:

#### 3.1 Baseline Terminal Valuation ($V_{\text{baseline\_actual}}$)
For seed $S \in [50000, 50024]$, the baseline match is simulated from step 0 to step 719 under the frozen V3 chassis:
$$V_{\text{baseline\_actual}} = \text{Game}(S).\text{reward}(0) = \text{farm}[0].\text{money}_{t=719}$$

#### 3.2 Candidate Terminal Valuation ($V_{\text{candidate\_actual}}$)
At intervention step $t$, worker $W$ executes candidate action $a_{\text{cand}}(t)$ instead of baseline action $a_{\text{base}}(t)$. From step $t+1$ to 719, the match continues deterministically under the frozen V3 agent:
$$V_{\text{candidate\_actual}} = \text{Game}_{\text{intervened}}(S).\text{reward}(0)$$

#### 3.3 Exact Economic Delta ($\Delta_{\text{exact}}$)
$$\Delta_{\text{exact}} = V_{\text{candidate\_actual}} - V_{\text{baseline\_actual}}$$

#### 3.4 Engine Evaluation ($\Delta_{\text{engine}}$)
The engine evaluates $(O_0(t), a_{\text{base}}(t), a_{\text{cand}}(t))$ and outputs:
$$\Delta_{\text{engine}} = \text{LaborOpportunityAssessment}.\text{net\_incremental\_value}$$
$$\text{OpportunityCost}_{\text{engine}} = \text{LaborOpportunityAssessment}.\text{opportunity\_cost}$$

#### 3.5 Sign Agreement Criterion
A candidate state achieves **sign agreement** if:
$$\text{Sign}(\Delta_{\text{engine}}) \approx \text{Sign}(\Delta_{\text{exact}})$$
Formally:
- $(\Delta_{\text{exact}} > 0 \land \Delta_{\text{engine}} > 0)$
- $(\Delta_{\text{exact}} < 0 \land \Delta_{\text{engine}} < 0)$
- $(|\Delta_{\text{exact}}| < \epsilon \land |\Delta_{\text{engine}}| < \epsilon)$
- $(\Delta_{\text{exact}} \le 0 \land \Delta_{\text{engine}} \le 0 \land \text{rec} = \text{False})$

---

### 4. Mathematical Audit & Reformulation of the Valuation Engine

#### 4.1 Deconstructing the Opportunity Cost Formula
Let:
- $X$ be the gross incremental value created by candidate action.
- $Y$ be the value of baseline duties forgone by diverting the worker.
- $V_{\text{alt}} - V_{\text{base}}$ be the net trajectory delta across the rollout horizon.

In an exact counterfactual trajectory:
$$V_{\text{alt}} - V_{\text{base}} = X - Y$$

The economic opportunity cost is the lost baseline production $Y$:
$$\text{OpportunityCost} = Y = X - (V_{\text{alt}} - V_{\text{base}})$$
$$\text{NetIncrementalValue} = X - \text{OpportunityCost} = X - Y$$

#### 4.2 Failure Mode 1: Biological Asset Double-Counting
If unharvested mature crops on tiles are valued at 100% of market price ($P$):
- Before harvest: Tile has $P$, cargo has 0. Total = $P$.
- After harvest: Tile has 0, cargo has $P$. Total = $P$.
- Trajectory delta: $\Delta = P - P = 0$.
- Formula output: $\text{OpportunityCost} = \max(0, P - 0) = P$, $\text{NetValue} = P - P = 0$.

**Correction**: Unharvested mature crops on tiles are biological potential requiring labor, NOT liquid inventory. They must not be valued at 100% of product price in ground tile valuation.

#### 4.3 Failure Mode 2: Phantom Opportunity Cost on Ineffective Actions
If candidate task is unexecutable (e.g. `FEED` without wheat or without animal), actual gain is $X_{\text{actual}} = 0$. If the engine heuristically estimates $X_{\text{est}} = 135$, but $\Delta = 0$:
$$\text{OpportunityCost} = \max(0, 135 - 0) = 135$$
The engine hallucinates that baseline lost $135!

**Correction**: The engine must verify that candidate action actually produced inventory, shed, money, or crops in rollout before attributing heuristic gains. If $X_{\text{actual}} = 0$, $\text{OpportunityCost} = \max(0, -\Delta)$.

#### 4.4 Failure Mode 3: Transit Misclassification
Treating movement (`b_cmd in MOVES`) as idle ignores transit time and downstream task dependencies.

**Correction**: Only `b_cmd in ("PASS", "WAIT")` is classified as idle. Movement escalates to Level 3 forward simulation.

---

### 5. Genuine Harvest Candidate Discovery Architecture

A genuine harvest opportunity is defined by strict physical and temporal criteria:
1. **Biological Maturity**: Tile contains `kind == "PLANT"` with $\text{day} - \text{planted\_day} \ge \text{first\_yield\_day}$ and $\text{yield\_units} > 0$.
2. **Spatial Reachability**: Worker Manhattan distance $D \le 3$ (with $D=0$ being immediately harvestable).
3. **Non-Duplication**: Baseline action for this worker is not already `HARVEST`.
4. **Temporal Feasibility**: Game step $s < 718$ ($\text{day} < 30$), allowing harvest before episode termination.

Every discovered candidate is classified by:
- `worker_class`: `IDLE_WORKER` vs `BUSY_WORKER`
- `distance`: `dist == 0` (immediate) vs `dist in [1, 3]` (route compression)
- `terminal_effect`: `TERMINAL_SAFE` ($s < 650$) vs `NEAR_TERMINAL` ($s \ge 650$)
