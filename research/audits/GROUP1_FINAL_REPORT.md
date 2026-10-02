# AEC PHASE 011: GROUP 1 MECHANISM RESCUE FINAL SCIENTIFIC REPORT

**Author**: Antigravity AI Research Agent (Phase 011 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (Verified Bit-Identical)  
**Development Cohort**: Certified Fresh Block `249111..249120` (N=10 seeds, 20 mirror matches per mechanism)  
**Protected Cohort Protection**: Verified 100% untouched (`340050–340199`, `214200–214249`, `340300–340349`).  
**Scientific Method**: Common Random Numbers (CRN) paired mirror-seat matching against frozen live foundation.

---

## 1. Executive Summary & Qualification Matrix

Phase 011 was initiated to address the dormancy of Group 1 mechanisms (`DYNAMIC_SHADOW_HARVEST`, `TERMINAL_HARVEST_SWEEP`, `ROUTE_COMPRESSION`, `CARGO_FERRY`), all of which had recorded **zero commits** during Phase 010.

Rather than dismissing these ideas or applying ad-hoc heuristic thresholds, Phase 011 executed a **second-generation economic rescue**, redesigning the mechanisms around state transitions, trajectory preservation, spliced continuation, multi-worker coordination, comprehensive wealth accounting, and in-flight trajectory execution.

Every mechanism was rescued, implemented, tested against adversarial synthetic matrices (45/45 tests passing, 537/537 suite passing), and subjected to rigorous empirical qualification on certified fresh seeds.

| Mechanism Family | Original Problem | Rescued Formulation | Candidates | Commits | Mean Paired Delta | 95% Conf. Interval | Safety Breaches | Scientific Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **DYNAMIC_SHADOW_HARVEST** | 0 commits; evaluated single-turn harvest without trajectory | Harvest + shed deposit + sell + spliced reconnect + in-flight execution | 51,245 | 238 | -1,030.65 pts | [-2059.33, -1.97] | 0 | **FUNCTIONALLY COMPLETE / QUARANTINED** |
| **TERMINAL_HARVEST_SWEEP** | 0 commits; evaluated as harvest-only without runway feasibility | Runway-certified terminal sweep + stranded cargo salvage + liquidation | 3,662 | 160 | -906.60 pts | [-1814.90, +1.70] | 0 | **FUNCTIONALLY COMPLETE / QUARANTINED** |
| **ROUTE_COMPRESSION** | 0 commits; geometric shortest path without economic state | Economic state transition value + detour compaction + spacetime reservations | 26,932 | 4,445 | -162,361.65 pts | [-173227.65, -151495.65] | 0 | **FAILED / QUARANTINED** |
| **CARGO_FERRY** | 0 commits; treated helper as free labor without opportunity cost | Full coupled multi-worker unburdening + exact helper opportunity cost | 34,645 | 510 | -850.65 pts | [-1373.79, -327.51] | 0 | **FUNCTIONALLY COMPLETE / QUARANTINED** |

---

## 2. Forensic Diagnosis: Why First-Generation Formulations Failed

In Phase 010, Group 1 mechanisms failed to commit due to distinct architectural shortcomings in their initial formulation:

1. **DYNAMIC_SHADOW_HARVEST**: Treated harvesting as a 1-turn instantaneous action query. A worker adjacent to or near a mature crop had no multi-turn representation connecting harvest $\to$ shed transit $\to$ deposit $\to$ reconnection to future baseline waypoints.
2. **TERMINAL_HARVEST_SWEEP**: Proposed harvesting at late game steps without proving runway feasibility ($T_{\text{feas}} \le 718 - \text{step}$). Candidates that could not deposit or sell before turn 720 were pruned or rejected as stranded inventory.
3. **ROUTE_COMPRESSION**: Optimized pure geometric Manhattan distance. In a turn-based farming game, a route that is one step shorter but reaches a field at an unscheduled time disrupts downstream planting/watering dependencies.
4. **CARGO_FERRY**: Evaluated helper workers without accounting for their alternative baseline productivity, causing negative economic evaluations whenever a helper was assigned to transport tasks.
5. **The Critical Executor Gap (Discovered in Phase 011)**: Prior to Phase 011, `AECExecutor` was open-loop and stateless across turns. When a multi-turn patch committed at step $t$, the executor emitted step 0 and immediately discarded steps $1..N-1$, leaving workers stranded mid-field.

---

## 3. Second-Generation Mechanism Rescue Architecture

### 3.1 DYNAMIC_SHADOW_HARVEST ("Harvest + Released Productive Time")
- **Architecture**: Assembles full multi-turn coupled trajectories: `worker route to crop -> multi-crop harvest up to shed capacity -> route to shed -> deposit -> market sell -> bridge moves -> rendezvous reconnection at turn k`.
- **Spliced Continuation**: Directly stitches the patch actions to the baseline suffix from the reconnection waypoint onward.
- **Comprehensive Wealth Accounting**: Replaced cash-only delta with complete economic wealth:
  $$\text{Wealth} = \text{Cash} + \text{Shed Inventory Value} + \text{Carried Cargo Value}$$
- **In-Flight Trajectory Execution**: `AECExecutor` maintains active patch state across turns until reconnection is achieved, with emergency abort capabilities on feed or solvency risks.

### 3.2 TERMINAL_HARVEST_SWEEP ("Terminal Economic Sweep")
- **Architecture**: Enforces hard feasibility proofs:
  $$T_{\text{transit\_to\_crop}} + T_{\text{harvest}} + T_{\text{transit\_to\_shed}} + T_{\text{deposit}} \le 718 - \text{current\_step}$$
- **Stranded Cargo Salvage**: Detects workers already carrying mature cargo in the endgame and routes them directly to shed tiles for liquidation.
- **Immediate Market Liquidation**: Pairs the terminal deposit with a top-priority `SELL` market order.

### 3.3 ROUTE_COMPRESSION ("Economic Route Compression")
- **Architecture**: Replaces geometric distance minimization with economic state-transition valuation.
- **Spacetime Collision Reservation**: Uses `SpaceTimeReservationTable` to verify that alternative routes do not collide with co-workers.
- **Suffix Preservation**: Reconnects compressed routes back to original baseline targets via deterministic path bridges.

### 3.4 CARGO_FERRY ("Multi-Worker Cargo Hand-off")
- **Architecture**: Evaluates multi-worker marginal value by pairing a burdened primary worker with an underutilized helper.
- **Helper Opportunity Cost**: Evaluates the helper's counterfactual baseline value and requires:
  $$\Delta_{\text{Primary Time Saved}} \times \text{Shadow Rate} + \Delta_{\text{Realized Value}} > \text{Helper Opportunity Cost} + \text{Coordination Cost}$$

---

## 4. Empirical Qualification Evidence & Findings

### 4.1 DYNAMIC_SHADOW_HARVEST
- **Functional Evidence**: 100% verified. 45/45 matrix tests passing. Deterministic replay verified across all seeds. 0 safety breaches. 0 desynchronizations.
- **Activation / Exposure**: 51,245 candidates generated across 10/10 seeds; 238 commits executed across 9/10 seeds.
- **Economic Evidence**: Mean paired delta of **-1,030.65 pts** (SE = 454.77, 95% CI [-2059.33, -1.97], $t = -2.27, p = 0.049$). 0 wins / 10 losses.
- **Scientific Attribution**: The frozen V3 backbone operates a highly tuned, tightly synchronized grid farming schedule. Even when a harvest candidate cleanly deposits and reconnects, diverting a worker away from baseline planting/watering routines causes downstream compound losses that exceed the value of the harvested crop.
- **Status**: **FUNCTIONALLY COMPLETE / QUARANTINED**.

### 4.2 TERMINAL_HARVEST_SWEEP
- **Functional Evidence**: 100% verified. 0 safety violations.
- **Activation / Exposure**: 3,662 candidates generated across 10/10 seeds; 160 commits executed across 10/10 seeds.
- **Economic Evidence**: Mean paired delta of **-906.60 pts** (SE = 401.55, 95% CI [-1814.90, +1.70], $t = -2.26, p = 0.050$). Demonstrated localized value with 2 winning seeds (Seed 249114: +8.0 pts, Seed 249115: +93.0 pts) and 1 tie (Seed 249112: +0.0 pts), but 7 losses.
- **Scientific Attribution**: In late endgame (turns 650–718), V3's native terminal liquidation schedule is already highly optimized. Splicing terminal sweeps occasionally captures marginal crop value, but frequently consumes the turns required for optimal batch liquidation.
- **Status**: **FUNCTIONALLY COMPLETE / QUARANTINED**.

### 4.3 ROUTE_COMPRESSION
- **Functional Evidence**: 100% verified. 0 runtime crashes. Spacetime reservations prevented collisions.
- **Activation / Exposure**: 26,932 candidates generated; 4,445 commits executed across 10/10 seeds (445 commits/seed).
- **Economic Evidence**: Mean paired delta of **-162,361.65 pts** (SE = 4,803.71, 95% CI [-173227.65, -151495.65], $t = -33.80, p < 10^{-8}$). 0 wins / 10 losses.
- **Scientific Attribution**: Replacing planned trajectory prefixes with direct shed paths diverted workers away from their farming tasks almost every turn. Workers endlessly shuttled to the shed without planting or watering, collapsing the farm economy.
- **Status**: **FAILED / QUARANTINED**.

### 4.4 CARGO_FERRY
- **Functional Evidence**: 100% verified. Multi-worker action coordination executed cleanly.
- **Activation / Exposure**: 34,645 candidates generated across 10/10 seeds; 510 commits executed across 10/10 seeds.
- **Economic Evidence**: Mean paired delta of **-850.65 pts** (SE = 231.27, 95% CI [-1373.79, -327.51], $t = -3.68, p = 0.005$). 0 wins / 10 losses.
- **Scientific Attribution**: In V3's farm architecture, workers have dedicated operational sectors. Moving a helper worker across sectors to ferry cargo imposes heavy travel overhead and completely shuts down the helper's local production, resulting in net negative system welfare.
- **Status**: **FUNCTIONALLY COMPLETE / QUARANTINED**.

---

## 5. Summary of Scientific Statuses & Governance Directives

In accordance with Phase 011 Governance (§0, §15, §17):

1. **DYNAMIC_SHADOW_HARVEST**: **FUNCTIONALLY COMPLETE / QUARANTINED**. (Implementation is complete, correct, and actively committing, but exact counterfactual economics show a statistically significant net loss. Quarantined cleanly.)
2. **TERMINAL_HARVEST_SWEEP**: **FUNCTIONALLY COMPLETE / QUARANTINED**. (Demonstrated localized positive margin on 2 seeds, but aggregate paired margin delta is negative. Quarantined cleanly.)
3. **ROUTE_COMPRESSION**: **FAILED / QUARANTINED**. (Repeated empirical evidence of catastrophic economic destruction caused by route detour diversion. Quarantined cleanly.)
4. **CARGO_FERRY**: **FUNCTIONALLY COMPLETE / QUARANTINED**. (Implementation works, but helper opportunity costs consistently outweigh primary relief. Quarantined cleanly.)

### Final Live Configuration:
The production live configuration remains protected and fail-closed:
- **Active Foundation**: `DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`
- **Quarantined Mechanisms**: `DYNAMIC_SHADOW_HARVEST`, `TERMINAL_HARVEST_SWEEP`, `ROUTE_COMPRESSION`, `CARGO_FERRY`, `LOCAL_WEED_DIG`, `SHOP_ARBITRAGE`, `PRODUCTION_ARBITRAGE`, `TERMINAL_CONVERSION`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`, `TOWN_CYCLE`, `RESOURCE_CONVERSION`
- **Frozen Chassis**: Bit-identical `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
- **Protected Cohorts**: 100% clean and untouched.
