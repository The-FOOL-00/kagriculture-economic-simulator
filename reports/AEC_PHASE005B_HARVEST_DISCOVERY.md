# SPDX-License-Identifier: MIT
# AEC Phase 005B: Labor Opportunity Engine Ground-Truth & Harvest Discovery
## Harvest Opportunity Family Discovery & Feasibility Assessment

**Phase**: AEC Phase 005B  
**Component**: Harvest Discovery Service & `results/PHASE005_HARVEST_CANDIDATES.csv`  
**Evaluation Scope**: Development Seeds `50000–50024` (89,590 candidate records)  
**Date**: September 2026  
**Status**: DISCOVERY COMPLETE / STRUCTURALLY VALID  

---

### 1. Forensic Audit of the Phase 005 Recommendation

The Phase 005 readiness report recommended `DYNAMIC_SHADOW_HARVEST` or `TERMINAL_HARVEST_SWEEP` on the premise that:
> *"The offline replay revealed that in 440 instances, auxiliary workers were completely idle (PASS) while mature crops or high-margin opportunities existed nearby."*

Our forensic audit proved that this premise was **factually conflated**:
1. In `results/PHASE005_LABOR_DIAGNOSTIC.csv`, exactly 440 records were approved.
2. Every single one of those 440 approved records was a **`RESOURCE_CONVERSION` patch** (`candidate_task: FEED`), where an auxiliary hand fed an animal from an idle baseline state.
3. The remaining 312 records (304 market timing + 8 emergency feed) were all rejected.
4. **Zero harvest patches were approved in Phase 005.** The 440 approved conversions were erroneously cited in prose as harvest opportunities.

---

### 2. Systematic Discovery of Genuine Harvest Candidates

To establish whether harvest is truly an economically justified mechanism family, an independent, comprehensive scan was executed across all 25 development seeds (`50000–50024`).

#### 2.1 Criteria for Genuine Harvest Opportunities
A candidate state was recognized as a genuine harvest opportunity if and only if:
1. **Biological Maturity**: A tile on the player's farm contains a mature crop (`kind == "PLANT"`, $\text{day} - \text{planted\_day} \ge \text{first\_yield\_day}$, and $\text{yield\_units} > 0$).
2. **Legal & Spatial Reachability**: An active worker is within reach ($D \le 3$ Manhattan distance, or standing directly on the tile $D = 0$).
3. **Non-Duplication**: The worker's current baseline action is not already `HARVEST`.
4. **Temporal Horizon**: Current step $s < 718$ ($\text{day} < 30$), ensuring harvest is feasible before episode termination.

#### 2.2 Aggregate Discovery Metrics (Seeds 50000–50024)

| Metric | Measured Value | Percentage |
| :--- | :---: | :---: |
| **Total Genuine Harvest Candidates Discovered** | **89,590** | 100.0% |
| **Idle-Worker Harvest Opportunities (`PASS`)** | **3,734** | 4.17% |
| **Busy-Worker Harvest Opportunities (`Active`)** | **85,856** | 95.83% |
| **Immediately Harvestable ($D = 0$ on tile)** | **18,376** | 20.51% |
| **Route Compression / Deviation ($D \in [1, 3]$)** | **71,214** | 79.49% |
| **Terminal Harvest Opportunities ($s \ge 650$)** | **3,557** | 3.97% |

---

### 3. Economic Viability & Trajectory Analysis

#### 3.1 Immediate Direct Value vs Full Match Compounding
In controlled fixtures (e.g. `GT-01`), assigning an idle worker to harvest a mature crop yields:
- Immediate Cargo Value: **+$60.00** (CARROT) to **+$150.00** (STRAWBERRY)
- Marginal Labor Opportunity Cost: **$0.00**
- Net Incremental Value: **+$60.00** to **+$150.00**

In full 720-step matches, when Hand 3 at step 67 was assigned to harvest wheat at `(2, 0)`, the terminal game score increased by **+$12,879.00** because clearing the tile allowed rapid replanting of cash crops.

#### 3.2 Why Naive 1-Turn Harvest Patches Cause Losses
In the 100-state ground-truth counterfactual experiment, 19 of 25 single-turn harvest interventions produced negative full-game deltas. The causal root cause is **state desynchronization**:
1. When a 1-turn patch forces a worker to execute `HARVEST`, the worker gains 2–4 crop units in their cargo backpack.
2. The frozen V3 agent at step $t+1$ has no awareness that the patch occurred. The agent attempts to execute its precomputed plan assuming an empty backpack.
3. The worker cannot pick up subsequent tools or enters illegal shed access states, stalling the worker for multiple turns and destroying compound revenue.

#### 3.3 Core Architectural Conclusion: Trajectory Splicing is Mandatory
A viable harvest mechanism **cannot be an isolated 1-turn action injection**.
A genuine `DYNAMIC_SHADOW_HARVEST` mechanism must be implemented as a **complete coupled patch (`CoupledPatch`)**:
$$\text{HarvestPatch} = [\text{Navigate to Crop}] \to [\text{HARVEST}] \to [\text{Deliver to Shed / Market}] \to [\text{Reconnect to Baseline}]$$
The `ReconnectionEngine` (`aec/replanning/reconnect.py`) and `SpacetimeReservationTable` must splice the worker back onto their baseline trajectory after shedding the harvested cargo.

---

### 4. Recommendation & Prerequisites for Prospective Preregistration

1. **Mechanism Viability**: `DYNAMIC_SHADOW_HARVEST` is **STRUCTURALLY VALID**. There is an abundance of genuine opportunities (89,590 candidates across 25 seeds).
2. **Prioritization**:
   - Priority 1: **Immediately Harvestable Idle Hands ($D = 0$, 3,734 candidates)**. Lowest risk, immediate execution.
   - Priority 2: **Terminal Harvest Sweep ($s \ge 650$, 3,557 candidates)**. Clears remaining field inventory directly into score before episode end.
   - Priority 3: **Route Compression ($D \in [1, 3]$, 71,214 candidates)**. Requires multi-step spatial detour planning.
3. **Precondition Before Live Trial**:
   - Trajectory splicing and shed delivery must be closed-loop validated offline before any prospective tournament match is run.
