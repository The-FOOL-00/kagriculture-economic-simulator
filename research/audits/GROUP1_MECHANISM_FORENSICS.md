# AEC PHASE 011: GROUP 1 MECHANISM FORENSIC AUDIT & ATTRIBUTION REPORT

**Author**: Antigravity AI Research Agent (Phase 011 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Scope**: Complete 12-Stage Forensic Reconstruction of Group 1 Mechanisms across Phase 010 Pilot Cohorts (`249050–249061`)

---

## 1. Executive Forensic Summary Table

| Mechanism | Candidates | Exact Sims | Commits | Rejections | Main Rejection Cause | Missing Economic Variable |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **DYNAMIC_SHADOW_HARVEST** | 1,876 | 932 | 0 | 932 | V3 baseline already harvests mature crops within 1–2 turns; continuation desynchronization against static repeated action; diverted worker delayed maintenance without downstream credit. | Released productive worker time, multi-crop cluster sweep, downstream task unlocking, joint trajectory with real V3 continuation. |
| **TERMINAL_HARVEST_SWEEP** | 826 | 412 | 0 | 412 | Rigid fixed shape exceeds remaining episode runway ($d_1 + d_2 + 2 > 718 - \text{step}$); crops that fit are already harvested/sold by baseline; no cargo feasibility proof. | Incremental realizable terminal value, runway feasibility proof, flexible terminal sequence (harvest vs deliver vs sell), existing cargo monetization. |
| **ROUTE_COMPRESSION** | 266 | 134 | 0 | 134 | V3 BFS transit pathfinder is already Manhattan-optimal; geometric detour to harvest crops delayed deposit and risked peer collision; continuation desynchronization. | Economic state transition value of released turns, multi-worker reservation awareness, task reordering with baseline suffix preservation. |
| **CARGO_FERRY** | 744 | 372 | 0 | 372 | Primary worker trajectory was uncoupled (did not capture saved time); helper opportunity cost outweighed hauling benefit; 100% of pilot margin came from market timing. | Primary worker bottleneck condition, coupled two-worker joint trajectory mutating primary into productive field labor, helper alternative opportunity cost. |

---

## 2. Global Pipeline Defect: Splicing Desynchronization

Across all four mechanisms, our forensic inspection discovered an architectural desynchronization bug between `AECExecutor` and `PatchGenerator`:

```
[OBSERVE] -> [IR] -> [EVENTS] -> [OPPORTUNITY ENGINE]
                                        |
  [PATCH GENERATOR] <-------------------+  (CALLED WITH baseline_continuation=None!)
        |
        +--> Defaulted to [baseline_action] * H (Static repeated action!)
        +--> Reconnect engine searched waypoints on STATIC action!
        +--> Spliced continuation attached STATIC action suffix!
                                        |
  [BACKBONE FUTURE TRAJECTORY] <--------+  (Queried AFTER patch generation!)
        |
  [COUNTERFACTUAL SIMULATOR]
        |
        +--> Candidate ran with SPLICED STATIC SUFFIX!
        +--> Baseline ran with REAL V3 BACKBONE TRAJECTORY!
        +--> Spatial Check in simulate_rollout detected position mismatch:
             "Worker diverged: expected [x,y], actual [x',y'] -> commands = PASS"
        +--> Candidate collapsed to PASS commands -> Delta Margin <= 0.0 -> REJECTED
```

This discovery proves that **candidates were systematically crippled during counterfactual evaluation**, artificially suppressing commits even when the underlying tactical intuition was valid.

---

## 3. Detailed 12-Stage Reconstruction by Mechanism

### A. Dynamic Shadow Harvest (`DYNAMIC_SHADOW_HARVEST`)

1. **Detector Trigger**:
   - `LaborOpportunityAnalyzer.analyze()` in `aec/opportunities/labor.py`.
   - Scanned farm tiles for `kind == "PLANT"` with `yield_units > 0`.
   - Triggered when worker was within Manhattan distance $\le 4$ of a mature crop.
2. **Opportunity Candidate**:
   - Emitted `Opportunity(candidate_transformation_family="DYNAMIC_SHADOW_HARVEST")`.
   - Proposed 1,876 candidates across seeds `249050–249052`.
3. **Candidate Metadata**:
   - `dependency_info` contained `worker_id`, `target_xy`, `crop`, `dist`, `gross_value`, `opportunity_cost`, `net_incremental_value`.
4. **Labor Valuation**:
   - Screened by `LaborOpportunityCostEngine.assess_opportunity()`.
   - Passed Stage S5 labor screening if `net_incremental_value > 0`.
5. **Dependency Graph**:
   - Dependent on `CROP_MATURE_{crop}_{x}_{y}`.
6. **Patch Generation**:
   - `HarvestCoupledPatchGenerator.generate_harvest_patch()`.
   - Constructed fixed sequence: `route_to_target -> HARVEST -> route_to_shed -> DROP -> SELL`.
7. **Route / Trajectory Mutation**:
   - Worker diverted to target tile, harvested, then walked to shed tile $(0, 0)$.
8. **Reconnect**:
   - Attempted reconnection from shed tile $(0, 0)$ back to baseline waypoint.
   - Waypoints were derived from static repeated baseline actions, creating invalid bridge moves.
9. **Exact Simulation**:
   - 932 candidates reached `CounterfactualSimulator.evaluate()`.
   - Spliced trajectory executed static/pass actions while baseline continued intelligent farming.
10. **Economic Comparison**:
    - Evaluated in `WinModel.evaluate()`.
    - Baseline achieved equal or better cash because baseline agent harvested within 1–2 steps anyway.
    - Candidate yielded $\Delta_{\text{margin}} \le \$0.00$.
11. **Safety Decision**:
    - `SafetyChecker.verify()` reported 0 safety violations (100% safe).
12. **Final Commit Gate**:
    - 0 commits. All 932 candidates classified as `NO_CANDIDATE_CERTIFIED_SUPERIOR`.
    - **Missing Variables**: Did not measure released worker time, downstream tasks unlocked by the harvest, multi-crop cluster harvesting, or true baseline continuation.

---

### B. Terminal Harvest Sweep (`TERMINAL_HARVEST_SWEEP`)

1. **Detector Trigger**:
   - `TerminalOpportunityAnalyzer.analyze()` in `aec/opportunities/terminal.py`.
   - Triggered exclusively when `step >= 696`.
2. **Opportunity Candidate**:
   - Emitted candidates for every mature tile on the board, selecting `best_w = min(workers, key=dist)`.
   - 826 candidates proposed across seeds `249053–249055`.
3. **Candidate Metadata**:
   - `crop`, `target_xy`, `dist`, `yield_units`, `worker_id`.
4. **Labor Valuation**:
   - Bypassed labor shadow screen due to terminal urgency.
5. **Dependency Graph**:
   - Dependent on crop maturity and terminal step boundary.
6. **Patch Generation**:
   - Routed to `HarvestCoupledPatchGenerator` with `is_terminal_sweep=True`.
   - Forced fixed cycle: `route_to_target -> HARVEST -> route_to_shed -> DROP -> SELL`.
7. **Route / Trajectory Mutation**:
   - Worker routed to crop, then to shed.
8. **Reconnect**:
   - Suffix was empty if deposit occurred at $\ge 716$, but for earlier terminal steps, attempted reconnect.
9. **Exact Simulation**:
   - 412 candidates reached simulation.
   - For distant crops, deposit step $d_1 + d_2 + 2 + \text{step} > 718$, causing simulation failure or `TERMINAL_RISK`.
   - For nearby crops, V3 baseline already harvested and sold them.
10. **Economic Comparison**:
    - $\Delta_{\text{margin}} \le \$0.00$ in 100% of simulations.
11. **Safety Decision**:
    - 0 safety violations.
12. **Final Commit Gate**:
    - 0 commits. All 412 candidates abstained.
    - **Missing Variables**: Feasibility proof of remaining runway; flexible terminal transformations (e.g. `DELIVER -> SELL` for existing cargo, local `HARVEST` only); reasoning over crops maturing between 696 and 715.

---

### C. Route Compression (`ROUTE_COMPRESSION`)

1. **Detector Trigger**:
   - `RouteCompressionDetector.detect()` in `aec/opportunities/route_compression.py`.
   - Triggered when worker had a mature crop within radius 1–3 steps or `deposit_path_len > direct_dist + 1`.
2. **Opportunity Candidate**:
   - 266 candidates proposed across seeds `249056–249058`.
3. **Candidate Metadata**:
   - `target_pos`, `crop`, `saved_steps`, `target_tasks: ["HARVEST", "DROP"]`.
4. **Labor Valuation**:
   - Assumed heuristic saving: `saved = orig_steps - comp_steps`.
5. **Dependency Graph**:
   - Spacetime reservations between worker and target tile.
6. **Patch Generation**:
   - `deterministic_find_path()` to target tile + `target_tasks` + reconnect.
7. **Route / Trajectory Mutation**:
   - Substituted detour path into worker queue.
8. **Reconnect**:
   - Reconnected to static repeated baseline continuation.
9. **Exact Simulation**:
   - 134 candidates reached exact simulation.
   - In baseline V3, worker was already taking the shortest BFS path to shed. Adding a detour to harvest delayed the deposit, missing town market consumption windows.
10. **Economic Comparison**:
    - Detour delayed market realization; $\Delta_{\text{margin}} \le \$0.00$.
11. **Safety Decision**:
    - 0 safety violations.
12. **Final Commit Gate**:
    - 0 commits.
    - **Missing Variables**: Economic state transition value (measuring released turns applied to downstream tasks rather than Manhattan distance); baseline suffix preservation; task reordering in queue.

---

### D. Cargo Ferry (`CARGO_FERRY`)

1. **Detector Trigger**:
   - `CargoFerryDetector.detect()` in `aec/opportunities/cargo_ferry.py`.
   - Triggered when an auxiliary hand was idle and within 3 steps of a ripe crop.
2. **Opportunity Candidate**:
   - 744 candidates proposed across seeds `249059–249061`.
3. **Candidate Metadata**:
   - `source_worker_id: 0`, `ferry_worker_id: hand_id`, `target_pos`, `cargo_item`.
4. **Labor Valuation**:
   - Valued cargo at raw market price, ignoring the helper's opportunity cost.
5. **Dependency Graph**:
   - Two-worker interaction, but uncoupled in execution.
6. **Patch Generation**:
   - Created patch ONLY for the helper worker: `path_to_crop -> HARVEST -> path_to_shed -> DROP`.
   - Primary worker's trajectory was NOT mutated!
7. **Route / Trajectory Mutation**:
   - Helper diverted to haul; Primary continued unchanged.
8. **Reconnect**:
   - Helper attempted reconnect to static baseline continuation.
9. **Exact Simulation**:
   - 372 candidates reached exact simulation.
   - Primary worker was not bottlenecked and did not utilize the saved time.
   - Helper missed watering or harvesting baseline crops.
   - Joint trajectory was strictly net-negative.
10. **Economic Comparison**:
    - Helper opportunity cost > hauling benefit $\implies \Delta_{\text{margin}} < 0$.
11. **Safety Decision**:
    - 0 safety violations.
12. **Final Commit Gate**:
    - 0 commits.
    - **Missing Variables**: Primary worker bottleneck condition; joint two-worker trajectory mutating primary into productive field work; helper alternative opportunity cost.

---

## 4. Candidate Funnel Attribution Breakdown

| Funnel Stage | Dynamic Harvest | Terminal Harvest | Route Compression | Cargo Ferry |
| :--- | :---: | :---: | :---: | :---: |
| **Generated** | 1,876 | 826 | 266 | 744 |
| **S1 Legality** | 1,876 | 826 | 266 | 744 |
| **S2 Reachability** | 1,876 | 826 | 266 | 744 |
| **S3 Resource Feasibility** | 1,876 | 826 | 266 | 744 |
| **S4 Worker Availability** | 1,876 | 826 | 266 | 744 |
| **S5 Labor Shadow Screen** | 1,876 | 826 | 266 | 744 |
| **S6 Dependency Closure** | 1,876 | 826 | 266 | 744 |
| **S7 Dominance Pruning** | 1,876 | 826 | 266 | 744 |
| **S8 Route Cost Screen** | 1,876 | 826 | 266 | 744 |
| **S9 Deterministic Top-K** | 932 | 412 | 134 | 372 |
| **S10 Exact Simulation** | 932 | 412 | 134 | 372 |
| **Safety Rejections** | 0 | 0 | 0 | 0 |
| **Economic Rejections** | 932 | 412 | 134 | 372 |
| **Commits** | **0** | **0** | **0** | **0** |

**Conclusion**: In all four mechanisms, 100% of candidates that reached exact counterfactual simulation died at the **economic evaluation gate** (`WinModel` / `delta_terminal_margin <= 0.0`) due to first-generation formulation narrowness and trajectory continuation desynchronization.
