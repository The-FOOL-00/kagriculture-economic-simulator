# AEC PHASE 007: AUTHORITATIVE ARCHITECTURE MANIFEST
**System Audit, Component Inventory, and Architectural Traceability Matrix**
**Date:** 2026-09-18  
**Governance:** Phase 007 — Zero Prospective Matches; Development Cohort Only (`50000–50024`)  
**Frozen V3 Chassis:** `submission_Vj_kc_v3.tar.gz` (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  

---

## 1. Executive Statement & Scope of Audit

Phase 006 established the critical trajectory-preserving primitive — `CoupledPatch` — and validated `DYNAMIC_SHADOW_HARVEST` and `TERMINAL_HARVEST_SWEEP` offline on development cohort `50000–50024`. However, Phase 006 did not complete all components of the originally finalized Adaptive Economic Compiler (AEC) architecture.

This manifest establishes the single authoritative source of truth across all 32 core components and opportunity families originally designed for the AEC. It inventories what is designed, what code exists, what is unit tested, what is offline validated, what is integrated into the live control graph, and what is scientifically cleared for live execution.

### Status Definitions:
* **DESIGNED:** Architecture exists conceptually and is formally documented.
* **CODE EXISTS:** Working, runnable source code exists in the repository.
* **UNIT TESTED:** Dedicated deterministic unit/adversarial test cases exist and pass.
* **OFFLINE VALIDATED:** Empirical evidence exists on development cohort (`50000–50024`) or historical offline datasets.
* **INTEGRATED:** The component is reachable in the real AEC execution graph (`AECExecutor.act`), not merely an isolated test harness.
* **LIVE ELIGIBLE:** The component has cleared all scientific activation gates and is authorized to commit actions in competition.

---

## 2. Authoritative Architecture Manifest Table

| Component | Designed | Code exists | Unit tested | Offline validated | Integrated | Live eligible | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **V3 Backbone** | YES | YES | YES | YES | YES | YES | ACTIVE / BASELINE |
| **Economic IR** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Opportunity Detector** | YES | YES | YES | YES | YES | PARTIAL | ACTIVE (Gated) |
| **Dependency Graph** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Labor Shadow** | YES | YES | YES | YES | PARTIAL | NO | SCREENING_ONLY |
| **Multi-Worker** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Reconnect** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **CoupledPatch** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Adaptive Horizon** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Event Replanning** | YES | PARTIAL | NO | NO | NO | NO | TO_BE_COMPLETED |
| **Candidate Funnel** | YES | PARTIAL | NO | NO | NO | NO | TO_BE_COMPLETED |
| **Market Timing** | YES | YES | YES | YES | YES | YES | ACTIVE / PROSPECTIVE_VALIDATED |
| **Market Collision** | YES | PARTIAL | PARTIAL | PARTIAL | YES | YES | ACTIVE (Safety) |
| **Opponent Pressure** | YES | PARTIAL | YES | PARTIAL | PARTIAL | NO | TO_BE_COMPLETED |
| **Route Compression** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Cargo Ferry** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Dynamic Harvest** | YES | YES | YES | YES | YES | NO | OFFLINE_VALIDATED |
| **Terminal Harvest** | YES | YES | YES | YES | YES | NO | OFFLINE_VALIDATED |
| **Resource Conversion** | YES | YES | YES | YES | YES | NO | QUARANTINED |
| **Production Arbitrage** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Shop Arbitrage** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Terminal Conversion** | YES | PARTIAL | PARTIAL | PARTIAL | PARTIAL | NO | TO_BE_COMPLETED |
| **Opponent Preemption** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Emergency Recovery** | YES | PARTIAL | PARTIAL | PARTIAL | PARTIAL | NO | TO_BE_COMPLETED |
| **Town/Cycle Signal** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Macro Layer** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Tactical Layer** | YES | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL | TO_BE_COMPLETED |
| **Executor** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Robust Fallback** | YES | PARTIAL | YES | YES | YES | YES | TO_BE_COMPLETED |
| **META Layer** | YES | NO | NO | NO | NO | NO | TO_BE_IMPLEMENTED |
| **Safety** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Exact Counterfactual** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |

---

## 3. Detailed Architectural Traceability Chains

Every original architectural requirement must maintain a strict, verifiable lineage from design specification to implementation, verification, and runtime authority.

### 3.1 Foundations & Cross-Cutting Infrastructures
1. **V3 Backbone Chassis**
   - Requirement: Immutable, reproducible baseline generating canonical trajectories.
   - Module: `aec/integration/backbone_adapter.py`
   - Class/Function: `BackboneAdapter.call_once()`, `get_future_trajectory()`
   - Tests: `tests/aec/test_one_baseline_call.py`, `test_backbone_fallback.py`
   - Report: `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md`
   - Integration Path: `AECExecutor.act()` Step 1
   - Activation Status: LIVE_ELIGIBLE

2. **Economic Intermediate Representation (IR)**
   - Requirement: Typed, zero-loss snapshot of spatial, economic, and inventory state.
   - Module: `aec/ir/` (`economic_state.py`, `farm_state.py`, `worker_state.py`, `market_state.py`, `opponent_state.py`, `dependency_graph.py`)
   - Class/Function: `build_economic_state()`, `EconomicState`
   - Tests: `tests/aec/test_economic_ir.py`
   - Report: `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md`
   - Integration Path: `AECExecutor.act()` Step 2
   - Activation Status: LIVE_ELIGIBLE

3. **Multi-Worker Logistics Coordination**
   - Requirement: Resolve labor cannibalization and coordinate up to 3 workers with spatial/task exclusivity.
   - Module: `aec/coordination/` (`worker_model.py`, `task_model.py`, `assignment.py`, `dominance.py`, `scheduler.py`)
   - Class/Function: `MultiWorkerLogisticsCoordinator`, `WorkerAssignment`, `MultiWorkerDominancePruner`
   - Tests: `tests/aec/test_phase003_multiworker.py`, `tests/aec/test_phase004_fixtures.py`
   - Report: `AEC_PHASE003_MULTIWORKER_ARCHITECTURE.md`, `walkthrough.md`
   - Integration Path: `aec/patches/coupled_patch_engine.py`, `AECExecutor`
   - Activation Status: LIVE_ELIGIBLE

4. **Trajectory Reconnection Engine**
   - Requirement: Dynamic collision-free splicing back into baseline waypoints.
   - Module: `aec/replanning/reconnect.py`
   - Class/Function: `ReconnectEngine.reconnect()`, `SpacetimeReservationTable`
   - Tests: `tests/aec/test_reconnect_core.py`, `test_reconnect_multiworker.py`, `test_reconnect_adversarial.py`
   - Report: `AEC_RECONNECT_ARCHITECTURE.md`, `walkthrough.md`
   - Integration Path: `CoupledPatchEngine.compile()`
   - Activation Status: LIVE_ELIGIBLE

5. **Coupled Trajectory-Preserving Patch Engine**
   - Requirement: Multi-step atomic trajectories ending in neutral cargo and legal continuation.
   - Module: `aec/patches/coupled_patch.py`, `aec/patches/coupled_patch_engine.py`
   - Class/Function: `CoupledPatch`, `CoupledPatchEngine`, `TrajectoryPreservationCertificate`
   - Tests: `tests/aec/test_coupled_patch.py`
   - Report: `AEC_PHASE006_COUPLED_PATCH_DESIGN.md`, `walkthrough.md`
   - Integration Path: `AECExecutor.act()` Step 5 & 6
   - Activation Status: LIVE_ELIGIBLE

6. **Adaptive / Receding Horizon**
   - Requirement: Dynamic simulation depth conditioned on mechanism dependency closure and step.
   - Module: `aec/counterfactual/horizon.py`
   - Class/Function: `select_adaptive_horizon()`, `MechanismHorizonPolicy`
   - Tests: `tests/aec/test_checkpoint_001_adaptive_escalation.py`
   - Report: `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md`
   - Integration Path: `AECExecutor.act()` Step 6
   - Activation Status: LIVE_ELIGIBLE

7. **Exact Counterfactual Simulator**
   - Requirement: Bit-level parity with official engine for candidate certification.
   - Module: `aec/counterfactual/simulator.py`, `aec/counterfactual/parity_harness.py`
   - Class/Function: `CounterfactualSimulator.evaluate()`
   - Tests: `tests/aec/test_trace_equivalence.py`, `test_counterfactual_isolation.py`
   - Report: `EXP_AEC_003_FINAL_REPORT.md`
   - Integration Path: `AECExecutor.act()` Step 6
   - Activation Status: LIVE_ELIGIBLE

8. **Safety Certificate & Hard Invariant Battery**
   - Requirement: Deterministic fail-closed gate verifying 9 multi-worker invariants and fidelity.
   - Module: `aec/safety/certificate.py`, `aec/safety/checks.py`
   - Class/Function: `SafetyChecker.verify()`, `SafetyCertificate`
   - Tests: `tests/aec/test_safety_certificate.py`
   - Report: `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md`
   - Integration Path: `AECExecutor.act()` Step 6 & 7
   - Activation Status: LIVE_ELIGIBLE

---

### 3.2 Opportunity Families
1. **Dependency-Aware Market Timing**
   - Requirement: Optimal intra-turn and cross-turn order sequencing avoiding intra-basket price degradation.
   - Module: `aec/opportunities/market.py`, `aec/market/transformations.py`
   - Class/Function: `MarketOpportunityAnalyzer`, `DependencyAwareMarketTransformer`
   - Tests: `tests/aec/test_dependency_aware_market_timing.py`, `test_market_transformations.py`
   - Report: `EXP_AEC_003_FINAL_REPORT.md`
   - Integration Path: Enabled in `AECConfig.enabled_mechanisms`
   - Activation Status: PROSPECTIVE_VALIDATED

2. **Dynamic Shadow Harvest & Terminal Harvest Sweep**
   - Requirement: Salvage mature cash crops using idle workers without baseline desynchronization.
   - Module: `aec/patches/harvest_patch.py`, `aec/opportunities/labor.py`
   - Class/Function: `DynamicHarvestPatchGenerator`, `TerminalHarvestSweepPatchGenerator`
   - Tests: `tests/aec/test_dynamic_shadow_harvest.py`
   - Report: `AEC_PHASE006_HARVEST_DISCOVERY.md`, `walkthrough.md`
   - Integration Path: `CoupledPatchEngine`
   - Activation Status: OFFLINE_VALIDATED (Awaiting Phase 007 full integration audit)

3. **Resource Conversion & Feed Security**
   - Requirement: In-shed processing and feed safety DAG transformations.
   - Module: `aec/resource/` (`conversions.py`, `dag.py`, `liquidity.py`, `labor.py`)
   - Class/Function: `ResourceConversionEngine`, `ConversionLiquidityAnalyzer`
   - Tests: `tests/aec/test_resource_conversions.py`, `test_resource_remediation_fixtures.py`
   - Report: `AEC_PHASE004B_RESOURCE_REMEDIATION_VALIDATION.md`, `walkthrough.md`
   - Integration Path: Quarantined in `aec/config.py`
   - Activation Status: PERMANENTLY_QUARANTINED (Negative ITT -$1,417.54)

4. **Terminal Liquidation & Phase Shutdown**
   - Requirement: Step 718 inventory dump and day-24 growth cutoff.
   - Module: `aec/terminal/transformations.py`, `aec/terminal/obligations.py`
   - Class/Function: `TerminalLiquidationTransformer`, `PhaseShutdownChecker`
   - Tests: `tests/aec/test_terminal_transformations.py`
   - Report: `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md`
   - Integration Path: `AECExecutor.act()`
   - Activation Status: LIVE_ELIGIBLE

---

### 3.3 Missing Architectural Components (To be Implemented in Phase 007)
1. **Event-Triggered Replanning (`EventTriggeredReplanner`)**
   - Target: `aec/replanning/event_replanner.py`
   - Interfaces: `ReplanTrigger`, `ReplanEvent`, `ReplanPolicy`, `EventTriggeredReplanner`
   - Escalation: Levels L1 to L5

2. **Candidate Funnel & Inference Budget Controller**
   - Target: `aec/funnel/candidate_funnel.py`
   - Interfaces: `InferenceBudget`, `CandidateBudget`, `OpportunityCandidateFunnel`
   - Pipeline: 10-stage tiered pruning with deterministic top-K

3. **Continuous Opponent Pressure Engine**
   - Target: `aec/counterfactual/opponent_pressure.py` (expansion)
   - Interfaces: `OpponentPressureState`, `ContinuousOpponentPressureAnalyzer`
   - Rule: Prioritizes and triggers, never overrides safety or counterfactual certificate.

4. **Macro / Tactical / Executor Layer Separation**
   - Target: `aec/macro/`, `aec/tactical/`, `aec/integration/fallback.py`
   - Interfaces: `MacroStrategy`, `TacticalPlanner`, `RobustFallbackPolicy`

5. **META Policy Orchestrator**
   - Target: `aec/meta/meta_policy.py`
   - Modes: `ROBUST_MODE`, `META_MODE`, `RESEARCH_MODE`

6. **Opportunity Registry & Missing Families**
   - Target: `aec/opportunities/registry.py`
   - Families: Route Compression, Cargo Ferry, Shop/Production Arbitrage, Terminal Conversion, Opponent Preemption, Emergency Recovery, Town/Cycle Signal.
   - Standard Contract: Detect -> Classify -> Feasibility -> Dependency Closure -> Generate Patch -> Evaluate Labor -> Candidate Funnel -> Exact Counterfactual -> Safety -> Commit/Abstain.

7. **Patch Composition Semantics**
   - Target: `aec/patches/composition.py`
   - Modes: Serial, Parallel, Mutually Exclusive, Dominates, Conflicts.
