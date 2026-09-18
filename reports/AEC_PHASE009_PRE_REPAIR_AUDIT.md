# AEC PHASE 009: PRE-REPAIR GLOBAL ARCHITECTURAL AUDIT
**Lead Implementation Engineer, Architecture Auditor, Simulation & Scientific-Governance Engineer Report**  
**Date:** 2026-09-18  
**Governance Standard:** Phase 009 Strict Scientific Protocol (Zero Prospective Matches, Zero Holdout Touches)  
**Authoritative Chassis SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (`submission_Vj_kc_v3.tar.gz`)

---

## 1. Executive Summary & Audit Mandate

In accordance with Phase 009 Part V, an exhaustive line-by-line inspection of all 44 canonical architectural items in the Adaptive Economic Compiler (AEC) codebase was conducted prior to any source code modifications.

The previous Phase 008 audit revealed that although all 44 components were nominally reachable and tested at some level, several critical opportunity families and economic mechanisms contained serious semantic gaps, development stubs, heuristic mismatches, and disconnects:
1. `TOWN_CYCLE`: Generator emitted an unmodified copy of baseline market orders (`market_mutations=copy.deepcopy(current_orders)`), and `TownCycleSignalDetector` was never invoked in `detect_opportunities()`.
2. `ROUTE_COMPRESSION`: Generator emitted a hardcoded dummy single-turn `{"HARVEST"}` command for the worker rather than compressing a multi-step worker trajectory.
3. `CARGO_FERRY`: Generator emitted a hardcoded dummy single-turn `{"HARVEST"}` command for the auxiliary hand rather than a coupled multi-worker hauling and deposit trajectory.
4. `LaborOpportunityAnalyzer`: Used a crude spatial ratio heuristic `val / max(1.0, dist + 1.0)` and emitted an unrecognized family name `"CARGO_FERRY_PRIORITY"`, while the true 5-tier marginal opportunity engine (`LaborOpportunityCostEngine`) remained confined to offline tools and funnel screening.
5. `DYNAMIC_SHADOW_HARVEST`: Functionally implemented with `HarvestCoupledPatchGenerator`, but dormant in match play because the executor's `NO_EVENT_FAST_PATH` bypassed opportunity detection on turns without E1–E8 events, ignoring worker idle states.
6. `TERMINAL_HARVEST_SWEEP`: `TerminalOpportunityAnalyzer` emitted an opportunity with `dependency_info={"mature_crops": mature_crops}` omitting `target_xy` and `crop`, causing `HarvestCoupledPatchGenerator` to reject 100% of candidate patch requests with `ROUTE_FAILURE`.
7. `SHOP_ARBITRAGE`: Generator checked `getattr(opp, "input_item", "")` while `ShopArbitrageOpportunity` defined `item: str`, resulting in empty order mutation.

Below is the complete, uncompromising audit of all 44 canonical items.

---

## 2. Global Audit Table of All 44 Canonical Architectural Items

| # | Item | Original Specification | Current Files | Current Behavior | Detection | Candidate Gen | Dep Closure | Patch Gen | Trajectory Pres | Counterfactual | Econ Eval | Safety | Commit Path | Current Enabled State | Current Qual | Defect | Required Repair | Priority |
|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|:---|:---:|
| 1 | **Frozen V3 Backbone** | ARCH-001, Checkpoint 001 | `aec/integration/backbone_adapter.py` | Calls frozen V3 once per turn; extracts baseline actions; byte-identical hash | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | YES | ENABLED | `PROSPECTIVE_VALIDATED` | None | None | P5 |
| 2 | **Economic IR** | Checkpoint 001, V1.1 | `aec/ir/` (`economic_state.py`, `farm_state.py`, `worker_state.py`, `market_state.py`, `opponent_state.py`) | Builds full immutable typed snapshot of game state every turn | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 3 | **Backbone / Macro Prior** | ARCH-001, Phase 007 | `aec/macro/macro_controller.py` | Sets cash reserve envelopes and validates tactical patch compatibility | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 4 | **Opportunity Engine** | Checkpoint 001, Phase 007 | `aec/opportunities/__init__.py`, `registry.py` | Dispatches to domain analyzers; filters via Layer 1 mechanism gate | YES | YES | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | Does not call `town_cycle_detector` in `detect_opportunities()` | Wire `town_cycle_detector.detect()` into candidate gathering | P1 |
| 5 | **Dependency Graph / Closure** | EXP-AEC-003, Checkpoint 001 | `aec/ir/dependency_graph.py` | Builds DAG of market orders; enforces same-asset order coupling | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `PROSPECTIVE_VALIDATED` | None | None | P5 |
| 6 | **Adaptive Horizon** | Checkpoint 001, Phase 006 | `aec/counterfactual/horizon.py` | Selects simulation horizon (6, 12, 18, 36) conditioned on mechanism family | N/A | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 7 | **Exact Counterfactual Simulator** | EXP-AEC-003, Checkpoint 001 | `aec/counterfactual/simulator.py` | Runs isolated state rollouts using official simulation logic | N/A | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `PROSPECTIVE_VALIDATED` | None | None | P5 |
| 8 | **Economic / Margin Evaluation** | Checkpoint 001, Phase 007 | `aec/evaluation/win_model.py` | Lexicographic ordering: Hard Safety -> Realized Margin Delta -> Tie-break | N/A | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | Sigmoid score is uncalibrated heuristic (already documented) | None (Preserve lexicographic margin order) | P5 |
| 9 | **Safety Certificate** | Checkpoint 001, Phase 004 | `aec/safety/certificate.py`, `aec/safety/checks.py` | Validates 9 strict invariants: solvency, inventory bounds, action legality, obligations | N/A | N/A | YES | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 10 | **Commit / Abstain Gate** | Checkpoint 001, Phase 007 | `aec/integration/executor.py` (L557-L620) | Enforces fail-closed semantics: commits only if certified superior, safe, and enabled | N/A | N/A | YES | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 11 | **Robust Fallback** | Phase 007 | `aec/integration/fallback.py` | Zero-latency reversion to pristine V3 baseline on any exception, timeout, or safety reject | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 12 | **Event Bus** | Checkpoint 001, Phase 007 | `aec/events/event_bus.py` | Deterministic priority queue for state-derived events | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 13 | **Event-Triggered Replanning** | Checkpoint 001, Phase 007 | `aec/replanning/event_replanner.py`, `aec/events/detectors.py` | Computes replan triggers and escalation levels | YES | YES | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | Executor checked `not event_bus.has_events` but ignored `replan_decision.should_replan`, causing fast-path exit | Connect `replan_decision.should_replan` to bypass or publish replan events to event bus | P1 |
| 14 | **Candidate Funnel** | Phase 007 | `aec/funnel/candidate_funnel.py` | 10-stage screening pipeline pruning illegal, insolvent, or dominated proposals | YES | YES | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | Stage 5 labor shadow check relied on pre-computed values without active evaluation fallback | Connect Stage 5 to `LaborOpportunityCostEngine` | P2 |
| 15 | **Inference Budget** | Phase 007 | `aec/funnel/candidate_funnel.py` | Caps simulations and bounds turn latencies (<100ms) | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 16 | **Macro Layer** | Phase 007 | `aec/macro/macro_controller.py` | Strategic governance and capital reserve envelopes | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 17 | **Tactical Layer** | Phase 007 | `aec/tactical/tactical_planner.py` | Synthesizes local bounded deviations | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 18 | **Executor** | Checkpoint 001, Phase 007 | `aec/integration/executor.py` | Orchestrates full 8-stage compiler flow | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 19 | **Patch Composition** | Phase 007 | `aec/patches/composition.py` | Composes non-conflicting multi-subsystem patches | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 20 | **Multi-Worker Coordinator** | Phase 003, Checkpoint 001 | `aec/coordination/scheduler.py` | Manages up to 3 workers with spatial/task exclusivity | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 21 | **Worker Model** | Phase 003, Phase 006 | `aec/coordination/worker_model.py` | Tracks worker capability, speed, carrying capacity, route | YES | YES | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 22 | **Worker Opportunity / Labor Valuation** | Phase 005, Phase 005B | `aec/resource/labor_engine.py`, `aec/opportunities/labor.py` | Derives marginal labor opportunity cost of worker reallocation | YES | YES | YES | YES | YES | YES | YES | YES | NO | SCREENING | `HEURISTIC_MISMATCH` | `LaborOpportunityAnalyzer` uses `val / (dist + 1)` and emits `"CARGO_FERRY_PRIORITY"` | Integrate `LaborOpportunityCostEngine` using marginal opportunity-cost formula | P1 |
| 23 | **Reconnect** | Checkpoint Phase | `aec/replanning/reconnect.py` | Collision-free dynamic route splicing back to baseline waypoints | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 24 | **Spacetime Reservation** | Checkpoint Phase | `aec/replanning/reconnect.py` | Prevents inter-worker collisions across multi-step trajectories | YES | YES | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 25 | **CoupledPatch** | Phase 006 | `aec/patches/coupled_patch.py`, `aec/patches/patch.py` | Multi-phase atomic trajectory: Navigate -> Action -> Carry -> Deposit -> Reconnect | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 26 | **Complete trajectory preservation** | Phase 006 | `aec/patches/harvest_patch.py`, `aec/patches/coupled_patch.py` | Guarantees cargo resolution, postconditions, and suffix continuity | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 27 | **Dependency-Aware Market Timing** | EXP-AEC-003 | `aec/market/transformations.py`, `aec/opportunities/market.py` | Causal DAG order sequencing respecting same-asset coupling | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `PROSPECTIVE_VALIDATED` | None | Preserve without modification | P5 |
| 28 | **Market Collision Guard** | Phase 004, Phase 007 | `aec/resource/liquidity.py`, `aec/safety/checks.py` | Evaluates order basket price impact and forward liquidity | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | None | None | P5 |
| 29 | **Opponent Pressure** | Phase 007 | `aec/counterfactual/opponent_pressure.py` | Non-blocking telemetry tracking rival cash and inventory | YES | N/A | N/A | N/A | N/A | YES | YES | N/A | N/A | ENABLED | `INTEGRATED` | None (Telemetry only) | None | P5 |
| 30 | **Opponent Supply / Harvest Pressure** | Phase 007 | `aec/counterfactual/opponent_pressure.py` | Estimates rival crop yield and expected sell volume | YES | N/A | N/A | N/A | N/A | YES | YES | N/A | N/A | ENABLED | `INTEGRATED` | None (Telemetry only) | None | P5 |
| 31 | **Opponent-Conditioned Counterfactuals** | Phase 007 | `aec/counterfactual/simulator.py` | Simulates rival reactions during forward rollouts | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None | None | P5 |
| 32 | **META Orchestrator** | Phase 007 | `aec/meta/meta_policy.py` | Modulates candidate priorities based on pressure; fallback to ROBUST | YES | N/A | YES | YES | YES | YES | YES | YES | N/A | ENABLED | `INTEGRATED` | None (Cannot bypass safety or simulation) | None | P5 |
| 33 | **Dynamic Shadow Harvest** | Phase 006 | `aec/opportunities/labor.py`, `aec/patches/harvest_patch.py` | Salvages ripe crops with idle worker capacity via CoupledPatch | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `DORMANT` | Dormant in full-game replay due to event gating and worker idle detection | Connect replan trigger, verify synthetic compilation and safety certification | P1 |
| 34 | **Terminal Harvest Sweep** | Phase 006 | `aec/opportunities/terminal.py`, `aec/patches/harvest_patch.py` | Salvages unharvested mature crops before step 718 | YES | YES | YES | NO | NO | NO | NO | NO | NO | ENABLED | `DISCONNECTED` | Opportunity omitted `target_xy` and `crop`, causing generator 100% rejection | Emit concrete tile/crop/worker tuples from terminal analyzer; add fallback | P1 |
| 35 | **Route Compression** | Phase 007 | `aec/opportunities/route_compression.py`, `aec/patches/generator.py` | Identifies redundant movement, constructs shorter legal trajectory | YES | YES | YES | NO | NO | YES | YES | NO | NO | QUARANTINED | `STUB` | Generator emits dummy single-turn `{"HARVEST"}` command | Implement full trajectory compression, task preservation, and reconnect | P1 |
| 36 | **Cargo Ferry** | Phase 007 | `aec/opportunities/cargo_ferry.py`, `aec/patches/generator.py` | Multi-worker cooperative hauling reducing transport burden | YES | YES | YES | NO | NO | YES | YES | NO | NO | QUARANTINED | `STUB` | Generator emits dummy single-turn `{"HARVEST"}` command | Implement multi-worker coupled ferry trajectory with shed deposit and reconnect | P1 |
| 37 | **Resource Conversion** | Phase 004B | `aec/resource/conversions.py`, `aec/patches/generator.py` | Animal feed & produce conversions | YES | YES | YES | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED_BUT_STRUCTURALLY_COMPLETE` | Negative empirical qualification history (-$258.96 ITT) | Verify structural completeness; retain strict quarantine | P3 |
| 38 | **Production Arbitrage** | Phase 007 | `aec/opportunities/arbitrage.py`, `aec/patches/generator.py` | Cash -> seed -> crop -> revenue lifecycle | YES | YES | YES | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED_BUT_STRUCTURALLY_COMPLETE` | Quarantined awaiting prospective protocol | Preserve structural implementation; retain quarantine | P4 |
| 39 | **Shop Arbitrage** | Phase 007 | `aec/opportunities/arbitrage.py`, `aec/patches/generator.py` | Town shop unlock boundary price arbitrage | YES | YES | YES | NO | NO | YES | YES | NO | NO | QUARANTINED | `PARTIAL` | Generator checked `opp.input_item` instead of `opp.item`, emitting no-op copy | Correct attribute lookup and generate valid market basket patch; retain quarantine | P2 |
| 40 | **Terminal Conversion** | Phase 007 | `aec/opportunities/terminal_conversion.py`, `aec/patches/generator.py` | Endgame inventory conversion and liquidation | YES | YES | YES | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED_BUT_STRUCTURALLY_COMPLETE` | Quarantined awaiting prospective protocol | Preserve structural implementation; retain quarantine | P4 |
| 41 | **Emergency Recovery / Emergency Feed** | Phase 004B, EXP-004 | `aec/opportunities/emergency.py`, `aec/resource/feed_security.py` | Feed security rescue and critical solvency liquidation | YES | YES | YES | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED_BUT_STRUCTURALLY_COMPLETE` | Quarantined per EXP-004 covenant | Preserve structural implementation; retain quarantine | P4 |
| 42 | **Town / Cycle Signal** | Phase 007 | `aec/opportunities/town_cycle.py`, `aec/patches/generator.py`, `aec/market/transformations.py` | Observes town demand cycle; times sale before/after shop absorption | NO | NO | YES | NO | NO | YES | YES | NO | NO | QUARANTINED | `DISCONNECTED` | `TownCycleSignalDetector` not called in `OpportunityEngine`; generator copied baseline orders | Implement meaningful market timing transformation, connect to pipeline; retain quarantine | P1 |
| 43 | **Phase / Economic Shutdown** | EXP-AEC-001 | `aec/opportunities/terminal.py`, `aec/patches/generator.py` | Prunes unviable late-game seed purchases after step 574 | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |
| 44 | **Terminal Liquidation** | EXP-AEC-001 | `aec/opportunities/terminal.py`, `aec/patches/generator.py` | Liquidates all remaining shed inventory at step 718 | YES | YES | YES | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | None | None | P5 |

---

## 3. Summary of Status Classifications

- **`COMPLETE`**: 25 components (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 43, 44)
- **`PARTIAL`**: 3 components (4: OpportunityEngine missing town cycle dispatch; 13: Event replanner uncoupled from fast path; 39: Shop arbitrage attribute mismatch)
- **`STUB`**: 2 components (35: Route Compression; 36: Cargo Ferry)
- **`DEAD`**: 0 components
- **`DISCONNECTED`**: 2 components (34: Terminal Harvest Sweep due to missing target_xy/crop; 42: Town Cycle Signal due to no-op generator and uncalled detector)
- **`DORMANT`**: 1 component (33: Dynamic Shadow Harvest due to event trigger fast-path gating)
- **`HEURISTIC_MISMATCH`**: 1 component (22: LaborOpportunityAnalyzer used distance ratio instead of marginal opportunity cost)
- **`QUARANTINED_BUT_STRUCTURALLY_COMPLETE`**: 4 components (30: Resource Conversion; 31: Production Arbitrage; 40: Terminal Conversion; 41: Emergency Recovery)

---

## 4. Prioritized Action Plan for Phase 009 Repairs

### P1 (Mandatory Core Repairs):
1. **Town / Market Cycle (Item 42 & 4)**:
   - Add `detect()` method to `TownCycleSignalDetector` returning `Opportunity` instances based on town absorption countdown and shop consumption.
   - Wire `town_cycle_detector.detect()` into `OpportunityEngine.detect_opportunities()`.
   - Implement real market transformation in `PatchGenerator`: delay sale when town absorption is imminent and profitable, or accelerate sale when demand peak is present.
   - Ensure patch routes through candidate funnel, dependency closure, exact simulator, safety certificate, and commit gate.
   - Add comprehensive deterministic unit tests.

2. **Route Compression (Item 35)**:
   - Replace dummy `{"HARVEST"}` in `PatchGenerator` with true multi-step route compression.
   - Analyze baseline worker trajectory, identify redundant detours or compressible task sequences, construct optimal collision-free path via `deterministic_find_path` / `ReconnectionEngine`.
   - Preserve all baseline tasks, spatial legality, cargo, and reconnect to baseline suffix.
   - Certify exact counterfactual simulation and safety.

3. **Cargo Ferry (Item 36)**:
   - Replace dummy `{"HARVEST"}` in `PatchGenerator` with true coupled multi-worker cargo ferry.
   - Pair busy primary worker with idle auxiliary hand.
   - Construct coupled trajectory: auxiliary moves to crop/cargo, harvests/collects, hauls to shed, deposits, and reconnects; primary continues field labor.
   - Validate spacetime reservations and exact counterfactual economics.

4. **True Marginal Labor Valuation (Item 22)**:
   - Refactor `LaborOpportunityAnalyzer` to replace `val / max(1.0, dist + 1.0)` with true marginal opportunity cost logic:
     $$\text{OpportunityCost} = \max\left(0, \text{CandidateGrossValue} - (V_{\text{alt}} - V_{\text{base}})\right)$$
   - Utilize `LaborOpportunityCostEngine` to evaluate reachable worker trajectory and displaced baseline tasks.
   - Ensure consistent naming (`"CARGO_FERRY"` instead of `"CARGO_FERRY_PRIORITY"`).

5. **Dynamic Shadow Harvest (Item 33) & Terminal Harvest Sweep (Item 34)**:
   - In `aec/integration/executor.py`, ensure that when `replan_decision.should_replan` is True (e.g. `WORKER_IDLE` or `CROP_MATURE`), the executor does not prematurely abort via `NO_EVENT_FAST_PATH`.
   - In `aec/opportunities/terminal.py`, scan tiles for concrete mature crop locations and emit opportunities with valid `target_xy`, `crop`, and `worker_id`.
   - Add synthetic activation states demonstrating full compilation, simulation, and certification.

### P2 (Secondary Repairs):
6. **Shop Arbitrage (Item 39)**:
   - Fix attribute lookup in `PatchGenerator` (`opp.item` vs `opp.input_item`) so that shop arbitrage generates a meaningful market order basket patch.
   - Wire into Funnel Stage 5 with active `LaborOpportunityCostEngine` reference.

### Governance Verifications:
- Frozen V3 chassis SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` byte-identical.
- Protected cohorts: `340050–340199`, `214200–214249`, `340300–340349` permanently virgin.
- Resource conversion: strictly quarantined.
