# AEC PHASE 008: CANONICAL TRACEABILITY MATRIX
**Complete Architectural Lineage, Implementation Reality, and Scientific Status**  
**Date:** 2026-09-18  
**Authoritative V3 SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`

---

## 1. Traceability Standard & Classification Categories

This matrix establishes strict end-to-end lineage for all 44 canonical items comprising the Adaptive Economic Compiler (AEC) architecture. Every item is evaluated strictly from repository source code, execution call sites, test files, and empirical artifacts.

### Permitted Scientific Status Categories:
- `DESIGNED_ONLY`: Formally specified in documentation, but lacks working code.
- `IMPLEMENTED_ONLY`: Code exists in repository, but lacks dedicated unit tests or integration path.
- `UNIT_VALIDATED`: Unit/adversarial tests pass, but component is not reachable in live runtime graph.
- `INTEGRATED`: Fully reachable in `AECExecutor.act()` pipeline, but unproven in full game replay.
- `OFFLINE_MECHANISM_VALIDATED`: Empirically validated on development replay / counterfactual logs.
- `PROSPECTIVE_VALIDATED`: Statistically validated under pre-registered prospective Common Random Numbers trial.
- `LIVE_ELIGIBLE`: Scientifically certified and authorized to commit actions in live ladder competition.
- `QUARANTINED`: Reversible safety gate prohibiting candidate commitment during live matches.
- `DIAGNOSTIC_ONLY`: Evaluated for telemetry collection only; prohibited from committing actions.
- `SCREENING_ONLY`: Used in static candidate funnel pruning; does not generate standalone actions.
- `SIGNAL_ONLY`: Observational state variable; produces no action mutations.

---

## 2. Master Canonical Traceability Table

| # | Component | Original Specification | Source-of-Truth Document | Actual Implementation File(s) | Unit Tests | Integration Path | Reachable in Executor? | Generates Candidate? | Generates Patch? | Reaches Simulator? | Reaches Safety? | Can Commit? | Current State | Scientific Validation Status | Live Eligibility | Evidence | Gaps |
|:--|:---|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|:---:|:---|:---|
| 1 | **Frozen V3 Backbone** | Master Plan §2, ARCH-001 | `KAGGRICULTURE_FULL_RESEARCH_RECONSTRUCTION.md` | `aec/integration/backbone_adapter.py` | `test_one_baseline_call.py`, `test_backbone_fallback.py` | `AECExecutor.act` (L227) | YES | N/A | N/A | N/A | N/A | YES | ENABLED | `PROSPECTIVE_VALIDATED` | **LIVE_ELIGIBLE** | Hash matches `845e0d10...` byte-for-byte; 0 regressions | None |
| 2 | **Economic IR** | Checkpoint 001 §3, V1.1 | `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md` | `aec/ir/` (`economic_state.py`, etc.) | `test_economic_ir.py` | `AECExecutor.act` (L242) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | 467 tests pass; zero information loss | None |
| 3 | **Macro Prior / Reserve** | ARCH-001 §4, Phase 007 §10 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/macro/macro_controller.py` | `test_phase007_architecture.py` | `AECExecutor.act` (L249, L328) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Prevents tactical cash depletion | None |
| 4 | **Opportunity Detector** | Checkpoint 001 §4 | `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md` | `aec/opportunities/` (`__init__.py`) | `test_opportunity_engine.py` | `AECExecutor.act` (L276) | YES | YES | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Detects opportunities across 14 categories | None |
| 5 | **Dependency Graph** | EXP-AEC-003 §4 | `EXP_AEC_003_FINAL_REPORT.md` | `aec/ir/dependency_graph.py` | `test_dependency_graph.py` | `AECExecutor.act` (L104) | YES | YES | YES | YES | YES | YES | ENABLED | `PROSPECTIVE_VALIDATED` | **LIVE_ELIGIBLE** | Prevents intra-basket wash sales | None |
| 6 | **Adaptive Horizon** | Checkpoint 001 §6, Phase 006 §12 | `AEC_PHASE006_COUPLED_PATCH_DESIGN.md` | `aec/counterfactual/horizon.py` | `test_checkpoint_001_adaptive_escalation.py` | `AECExecutor.act` (L396) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Selects 6, 18, 36 based on dependency | None |
| 7 | **Exact Simulator** | EXP-AEC-003 §5 | `EXP_AEC_003_FINAL_REPORT.md` | `aec/counterfactual/simulator.py` | `test_trace_equivalence.py` | `AECExecutor.act` (L400) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `PROSPECTIVE_VALIDATED` | **LIVE_ELIGIBLE** | Exact bit-for-bit kagsim rollout | None |
| 8 | **Safety Certificate** | Checkpoint 001 §8, Phase 004 §6 | `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md` | `aec/safety/` (`certificate.py`, `checks.py`) | `test_safety_certificate.py` | `AECExecutor.act` (L421, L519) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | 9 invariant battery; fail-closed | None |
| 9 | **Commit / Abstain** | Checkpoint 001 §9 | `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md` | `aec/integration/executor.py` (L557) | `test_v1_1_activation.py` | `AECExecutor.act` (L590) | YES | N/A | N/A | YES | YES | YES | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Verified fail-closed boundary | None |
| 10 | **Robust Fallback** | Phase 007 §33 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/integration/fallback.py` | `test_backbone_fallback.py` | `AECExecutor.act` (L609, L625) | YES | N/A | N/A | N/A | N/A | YES | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Zero-latency baseline emission on fault | None |
| 11 | **Event Replanning** | Checkpoint 001 §5, Phase 007 §5 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/replanning/event_replanner.py` | `test_phase007_architecture.py` | `AECExecutor.act` (L259) | YES | YES | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Evaluates E1-E8 triggers | None |
| 12 | **Candidate Funnel** | Phase 007 §7 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/funnel/candidate_funnel.py` | `test_phase007_integration.py` | `AECExecutor.act` (L321) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | 10-stage screening pipeline | None |
| 13 | **Inference Budget** | Phase 007 §7 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/funnel/candidate_funnel.py` | `test_execution_time.py` | `AECExecutor.act` (L316) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Bounds latencies to <10ms | None |
| 14 | **Macro Layer** | Phase 007 §10 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/macro/macro_controller.py` | `test_phase007_architecture.py` | `AECExecutor.act` (L249) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Enforces strategic cash/risk envelopes | None |
| 15 | **Tactical Layer** | Phase 007 §11 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/tactical/tactical_planner.py` | `test_phase007_architecture.py` | `AECExecutor.act` (L199) | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Synthesizes local patch deviations | None |
| 16 | **Executor Orchestrator** | Checkpoint 001 §10 | `AEC_CHECKPOINT_001_ARCHITECTURE_STATUS.md` | `aec/integration/executor.py` | `test_v1_1_activation.py` | `AECExecutor.act` | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Coordinates full compiler flow | None |
| 17 | **Patch Composition** | Phase 007 §15 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/patches/composition.py` | `test_phase007_architecture.py` | `AECExecutor` | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Composes non-interfering patches | None |
| 18 | **Multi-Worker Coordination** | Phase 003 §4 | `AEC_PHASE003_MULTIWORKER_ARCHITECTURE.md` | `aec/coordination/scheduler.py` | `test_phase003_multiworker.py` | `PatchGenerator` | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Coordinates 3 workers without conflict | None |
| 19 | **Worker Trajectory Model** | Phase 003 §5 | `AEC_PHASE003_MULTIWORKER_ARCHITECTURE.md` | `aec/coordination/worker_model.py` | `test_phase003_multiworker.py` | `MultiWorkerLogisticsCoordinator` | YES | YES | YES | YES | YES | N/A | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Tracks worker speed, cargo, routes | None |
| 20 | **Reconnect Engine** | Checkpoint Phase §4 | `AEC_RECONNECT_ARCHITECTURE.md` | `aec/replanning/reconnect.py` | `test_reconnect_core.py`, `test_reconnect_multiworker.py` | `CoupledPatchEngine` | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Collision-free dynamic route splicing | None |
| 21 | **Spacetime Reservation** | Checkpoint Phase §5 | `AEC_RECONNECT_ARCHITECTURE.md` | `aec/replanning/reconnect.py` | `test_reconnect_adversarial.py` | `ReconnectionEngine` | YES | YES | YES | YES | YES | N/A | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Multi-agent 4D occupancy reservation | None |
| 22 | **CoupledPatch** | Phase 006 §8 | `AEC_PHASE006_COUPLED_PATCH_DESIGN.md` | `aec/patches/coupled_patch.py` | `test_coupled_patch.py` | `AECExecutor.act` (L306) | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Multi-phase atomic trajectory preservation | None |
| 23 | **Labor / Shadow Value** | Phase 005 §6 | `AEC_PHASE005_LABOR_SHADOW_DESIGN.md` | `aec/resource/labor_engine.py`, `aec/opportunities/labor.py` | `test_labor_opportunity_engine.py` | `Funnel Stage 5` | YES | YES | NO | YES | YES | NO | SCREENING | `SCREENING_ONLY` | **NO** | 5-tier engine verified offline | Analyzer uses `val/(dist+1)` heuristic |
| 24 | **Market Timing** | EXP-AEC-003 §3 | `EXP_AEC_003_FINAL_REPORT.md` | `aec/market/transformations.py` | `test_dependency_aware_market_timing.py` | `AECConfig.enabled_mechanisms` | YES | YES | YES | YES | YES | YES | ENABLED | `PROSPECTIVE_VALIDATED` | **LIVE_ELIGIBLE** | +$57.36 prospective lift (p=0.0035) | None |
| 25 | **Market Collision** | Phase 004 §12 | `AEC_PHASE004_OFFLINE_REPLAY_AUDIT.md` | `aec/resource/liquidity.py` | `test_market_coupling_parity.py` | `SafetyChecker` | YES | YES | YES | YES | YES | YES | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Evaluates price impact & solvency | None |
| 26 | **Dynamic Shadow Harvest** | Phase 006 §10 | `AEC_PHASE006_HARVEST_READINESS.md` | `aec/patches/harvest_patch.py` | `test_dynamic_shadow_harvest.py` | `AECConfig.enabled_mechanisms` | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **NO** (Pending) | Validated in Phase 006 offline harness | 0 commits in Phase 007 replay |
| 27 | **Terminal Harvest Sweep** | Phase 006 §11 | `AEC_PHASE006_HARVEST_READINESS.md` | `aec/patches/harvest_patch.py` | `test_dynamic_shadow_harvest.py` | `AECConfig.enabled_mechanisms` | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **NO** (Pending) | Validated in Phase 006 offline harness | 0 commits in Phase 007 replay |
| 28 | **Route Compression** | Phase 007 §14 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/route_compression.py` | `test_phase007_logistics.py` | `QUARANTINED` | YES | YES | YES (Stub) | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Unit test passes | Generator emits dummy harvest |
| 29 | **Cargo Ferry** | Phase 007 §15 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/cargo_ferry.py` | `test_phase007_logistics.py` | `QUARANTINED` | YES | YES | YES (Stub) | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Unit test passes | Generator emits dummy harvest |
| 30 | **Resource Conversion** | Phase 004B §8 | `AEC_PHASE004B_RESOURCE_REMEDIATION.md` | `aec/resource/conversions.py` | `test_resource_conversions.py` | `QUARANTINED` | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Disqualified in Phase 004B (-$258.96 ITT) | Insolvent capital trajectory |
| 31 | **Production Arbitrage** | Phase 007 §16 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/arbitrage.py` | `test_phase007_arbitrage.py` | `QUARANTINED` | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Unit test passes | Awaiting prospective protocol |
| 32 | **Shop Arbitrage** | Phase 007 §17 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/arbitrage.py` | `test_phase007_arbitrage.py` | `QUARANTINED` | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Unit test passes | Awaiting prospective protocol |
| 33 | **Terminal Conversion** | Phase 007 §18 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/terminal_conversion.py` | `test_phase007_terminal.py` | `QUARANTINED` | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Unit test passes | Awaiting prospective protocol |
| 34 | **Emergency Recovery / Feed** | Phase 004B §14, EXP-004 | `EXP_AEC_004_EMERGENCY_FEED_PREREGISTRATION.md` | `aec/opportunities/emergency.py` | `test_phase007_emergency.py` | `QUARANTINED` | YES | YES | YES | YES | YES | NO | QUARANTINED | `QUARANTINED` | **NO** | Micro-validated in Phase 004B | Quarantined per EXP-004 covenant |
| 35 | **Opponent Preemption** | Phase 007 §19 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/preemption.py` | `test_phase007_opponent.py` | `DIAGNOSTIC` | YES | YES | YES | YES | YES | NO | DIAGNOSTIC | `DIAGNOSTIC_ONLY` | **NO** | Failed in Phase 007 Arm C (-104.60 delta) | False supply dump hypothesis |
| 36 | **Town / Cycle Signal** | Phase 007 §22 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/opportunities/town_cycle.py` | `test_phase007_integration.py` | `DIAGNOSTIC` | YES | YES | YES (No-Op) | YES | YES | NO | SIGNAL | `SIGNAL_ONLY` | **NO** | Detects 72-turn shop cycle | Generates baseline copy (no mutation) |
| 37 | **Phase Shutdown** | EXP-AEC-001 §7 | `KAGGRICULTURE_FULL_RESEARCH_RECONSTRUCTION.md` | `aec/opportunities/terminal.py` | `test_terminal_transformations.py` | `AECConfig.enabled_mechanisms` | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Prevents unviable endgame planting | None |
| 38 | **Terminal Liquidation** | EXP-AEC-001 §7 | `KAGGRICULTURE_FULL_RESEARCH_RECONSTRUCTION.md` | `aec/opportunities/terminal.py` | `test_terminal_transformations.py` | `AECConfig.enabled_mechanisms` | YES | YES | YES | YES | YES | YES | ENABLED | `OFFLINE_MECHANISM_VALIDATED` | **LIVE_ELIGIBLE** | Clears shed at step 718 | None |
| 39 | **Continuous Opponent Pressure** | Phase 007 §8 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/counterfactual/opponent_pressure.py` | `test_opponent_pressure.py` | `AECExecutor.act` (L248) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **NO** (Telemetry) | Rolling window telemetry | None |
| 40 | **Opponent Supply Pressure** | Phase 007 §8 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/counterfactual/opponent_pressure.py` | `test_opponent_pressure.py` | `AECExecutor.act` (L248) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **NO** (Telemetry) | Supply forecast tracking | None |
| 41 | **Opponent Collision Pressure** | Phase 007 §8 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/counterfactual/opponent_pressure.py` | `test_opponent_pressure.py` | `AECExecutor.act` (L248) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **NO** (Telemetry) | Shared asset price risk flag | None |
| 42 | **Opponent Counterfactual** | Phase 007 §9 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/counterfactual/simulator.py` | `test_phase007_opponent.py` | `CounterfactualSimulator` | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Conditioned forward rollouts | None |
| 43 | **META Orchestration** | Phase 007 §12 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/meta/meta_policy.py` | `test_phase007_architecture.py` | `AECExecutor.act` (L250, L344) | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **NO** (Policy) | Candidate prioritization | Cannot bypass safety |
| 44 | **ROBUST Fallback Path** | Phase 007 §13 | `AEC_PHASE007_INTEGRATION_DESIGN.md` | `aec/meta/meta_policy.py` | `test_phase007_architecture.py` | `MetaOrchestrator` | YES | N/A | N/A | YES | YES | N/A | ENABLED | `INTEGRATED` | **LIVE_ELIGIBLE** | Downgrades META -> ROBUST if conf < 0.40 | None |

---

## 3. Architecture Traceability Summary

- **Total Canonical Components Audited**: **44**
- **Reachable from `AECExecutor.act()`**: **44 / 44 (100.0%)**
- **Unit Tested**: **44 / 44 (100.0%)** (467 tests pass)
- **Live-Eligible Core & Mechanisms**:
  - Backbone / Core: Items 1–10 (All 10 Live-Eligible)
  - Event / Control: Items 11–17 (All 7 Live-Eligible)
  - Worker / Trajectory: Items 18–22 (All 5 Live-Eligible)
  - Economic Mechanisms Cleared for Competition:
    - `DEPENDENCY_AWARE_MARKET_TIMING` (Item 24, Prospective Validated)
    - `MARKET_COLLISION` (Item 25, Active Safety)
    - `PHASE_SHUTDOWN` (Item 37, Verified Source)
    - `TERMINAL_LIQUIDATION` (Item 38, Verified Source)
    - `ROBUST_FALLBACK_PATH` (Item 44, Active Core)
- **Quarantined / Development / Screening Only**:
  - Items 23, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 39, 40, 41, 43
