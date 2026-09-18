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
| **Opportunity Detector** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Dependency Graph** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Labor Shadow** | YES | YES | YES | YES | YES | NO | SCREENING_ONLY |
| **Multi-Worker** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Reconnect** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **CoupledPatch** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Adaptive Horizon** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Event Replanning** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Candidate Funnel** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Market Timing** | YES | YES | YES | YES | YES | YES | ACTIVE / PROSPECTIVE_VALIDATED |
| **Market Collision** | YES | YES | YES | YES | YES | YES | ACTIVE / SAFETY |
| **Opponent Pressure** | YES | YES | YES | YES | YES | NO | ACTIVE / TRIGGER_ONLY |
| **Route Compression** | YES | YES | YES | YES | YES | NO | INTEGRATED_QUARANTINED |
| **Cargo Ferry** | YES | YES | YES | YES | YES | NO | INTEGRATED_QUARANTINED |
| **Dynamic Harvest** | YES | YES | YES | YES | YES | NO | OFFLINE_VALIDATED |
| **Terminal Harvest** | YES | YES | YES | YES | YES | NO | OFFLINE_VALIDATED |
| **Resource Conversion** | YES | YES | YES | YES | YES | NO | QUARANTINED |
| **Production Arbitrage** | YES | YES | YES | YES | YES | NO | INTEGRATED_QUARANTINED |
| **Shop Arbitrage** | YES | YES | YES | YES | YES | NO | INTEGRATED_QUARANTINED |
| **Terminal Conversion** | YES | YES | YES | YES | YES | NO | INTEGRATED_QUARANTINED |
| **Opponent Preemption** | YES | YES | YES | YES | YES | NO | INTEGRATED_DIAGNOSTIC |
| **Emergency Recovery** | YES | YES | YES | YES | YES | NO | INTEGRATED_QUARANTINED |
| **Town/Cycle Signal** | YES | YES | YES | YES | YES | NO | INTEGRATED_SIGNAL |
| **Macro Layer** | YES | YES | YES | YES | YES | YES | ACTIVE / GOVERNANCE |
| **Tactical Layer** | YES | YES | YES | YES | YES | YES | ACTIVE / PROPOSALS |
| **Executor** | YES | YES | YES | YES | YES | YES | ACTIVE / PIPELINE |
| **Robust Fallback** | YES | YES | YES | YES | YES | YES | ACTIVE / FAIL_CLOSED |
| **META Layer** | YES | YES | YES | YES | YES | NO | ORCHESTRATION_WITH_FALLBACK |
| **Safety** | YES | YES | YES | YES | YES | YES | ACTIVE / CORE |
| **Exact Counterfactual** | YES | YES | YES | YES | YES | YES | ACTIVE / CERTIFICATE |

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

### 3.3 Completed Architectural Components (Implemented & Integrated in Phase 007)

1. **Event-Triggered Replanning (`EventTriggeredReplanner`)**
   - Requirement: State-derived change detection with multi-level dependency escalation.
   - Module: `aec/replanning/event_replanner.py`
   - Class/Function: `ReplanTrigger` (14 triggers), `ReplanEscalationLevel` (L1-L5), `ReplanEvent`, `ReplanPolicy`, `EventTriggeredReplanner`
   - Tests: `tests/aec/test_phase007_architecture.py::test_a7_08_event_triggered_replanning`
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 3
   - Activation Status: ACTIVE / CORE

2. **Candidate Funnel & Inference Budget Controller**
   - Requirement: 10-stage tiered candidate filtering keeping exact simulator tractable under 2s latency budget.
   - Module: `aec/funnel/candidate_funnel.py`, `aec/funnel/__init__.py`
   - Class/Function: `InferenceBudget`, `FunnelStage`, `FunnelStageRecord`, `FunnelTelemetry`, `OpportunityCandidateFunnel`
   - Tests: `tests/aec/test_phase007_architecture.py::test_a7_03_candidate_funnel_determinism`, `test_a7_04_inference_budget`
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 5
   - Activation Status: ACTIVE / CORE

3. **Continuous Opponent Pressure Engine**
   - Requirement: Multi-dimensional continuous pressure tracking informing timing and candidates without overriding safety.
   - Module: `aec/counterfactual/opponent_pressure.py`
   - Class/Function: `OpponentPressureState`, `ContinuousOpponentPressureAnalyzer`
   - Tests: `tests/aec/test_phase007_opponent.py` (OPP-01 to OPP-05)
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 4
   - Activation Status: ACTIVE / TRIGGER_ONLY

4. **Macro / Tactical / Executor Layer Separation**
   - Requirement: Three-tiered governance where tactical patches cannot modify farm strategic posture or reserve cash.
   - Module: `aec/macro/macro_controller.py`, `aec/tactical/tactical_planner.py`, `aec/integration/fallback.py`
   - Class/Function: `MacroController`, `MacroStrategy`, `TacticalPlanner`, `TacticalProposal`, `RobustFallbackPolicy`
   - Tests: `tests/aec/test_phase007_architecture.py::test_a7_05_macro_tactical_separation`, `test_a7_06_robust_fallback`
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 1, 2, 8
   - Activation Status: ACTIVE / GOVERNANCE

5. **META Policy Orchestrator**
   - Requirement: Dynamic mode configuration (`ROBUST_MODE`, `META_MODE`, `RESEARCH_MODE`) with fail-closed fallback to ROBUST.
   - Module: `aec/meta/meta_policy.py`, `aec/meta/__init__.py`
   - Class/Function: `AECMode`, `MetaPolicyDecision`, `MetaOrchestrator`
   - Tests: `tests/aec/test_phase007_architecture.py::test_a7_07_meta_fallback`
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 4
   - Activation Status: ORCHESTRATION_WITH_FALLBACK

6. **Opportunity Registry & Missing Opportunity Families**
   - Requirement: Unified registry declaring contract specs across all 14 families; implementation of missing families.
   - Module: `aec/opportunities/registry.py`, `route_compression.py`, `cargo_ferry.py`, `arbitrage.py`, `terminal_conversion.py`, `preemption.py`, `emergency.py`, `town_cycle.py`
   - Class/Function: `OpportunityRegistry`, `RouteCompressionDetector`, `CargoFerryDetector`, `ProductionArbitrageDetector`, `ShopArbitrageDetector`, `TerminalConversionDetector`, `OpponentPreemptionDetector`, `EmergencyRecoveryDetector`, `TownCycleSignalDetector`
   - Tests: `tests/aec/test_phase007_architecture.py::test_a7_01_registry_completeness`, `test_phase007_logistics.py`, `test_phase007_arbitrage.py`, `test_phase007_terminal.py`, `test_phase007_emergency.py`
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 5
   - Activation Status: FULLY_IMPLEMENTED & INTEGRATED (Quarantined/diagnostic where appropriate)

7. **Patch Composition Semantics**
   - Requirement: Explicit composition algebra (SERIAL, PARALLEL, MUTUALLY_EXCLUSIVE, DOMINATES, CONFLICTS).
   - Module: `aec/patches/composition.py`
   - Class/Function: `CompositionRelation`, `PatchCompositionEngine`
   - Tests: `tests/aec/test_phase007_integration.py`
   - Report: `AEC_PHASE007_ARCHITECTURE_COMPLETION.md`, `AEC_PHASE007_INTEGRATION_DESIGN.md`
   - Integration Path: `AECExecutor.act()` Step 5
   - Activation Status: ACTIVE / CORE

---

## 4. Final Architectural Completeness Statement

All 32 components specified in the original AEC design have now been audited, implemented in real Python source code, unit-tested via 467 deterministic tests, verified through offline development validation (`50000–50024`), and fully integrated into the unified `AECExecutor` control pipeline.

Scientific gating remains strictly enforced:
- **ACTIVE / BASELINE / CORE:** V3 Backbone, Economic IR, Opportunity Detector, Dependency Graph, Multi-Worker, Reconnect, CoupledPatch, Adaptive Horizon, Event Replanning, Candidate Funnel, Market Timing, Market Collision, Macro Layer, Tactical Layer, Executor, Robust Fallback, Safety Certificate, Exact Counterfactual, Patch Composition.
- **OFFLINE_VALIDATED (Awaiting Prospective Preregistration):** Dynamic Harvest, Terminal Harvest.
- **SCREENING_ONLY / TRIGGER_ONLY / SIGNAL:** Labor Shadow, Opponent Pressure, Town/Cycle Signal.
- **INTEGRATED_QUARANTINED / DIAGNOSTIC:** Route Compression, Cargo Ferry, Production Arbitrage, Shop Arbitrage, Terminal Conversion, Emergency Recovery, Opponent Preemption.
- **PERMANENTLY_QUARANTINED:** Resource Conversion.
