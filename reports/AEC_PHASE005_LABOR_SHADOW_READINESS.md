# SPDX-License-Identifier: MIT
# AEC Phase 005: Generic Labor Shadow Valuation & Opportunity-Cost Engine
## Production Readiness & Capability Roadmap Report

**Phase**: AEC Phase 005  
**Component**: `LaborOpportunityCostEngine` (`aec/resource/labor_engine.py`, `aec/economic/`)  
**Date**: September 2026  
**Status**: APPROVED FOR OFFLINE CONSUMPTION  

---

### 1. Architectural Readiness Classification

In accordance with Section 37 of the AEC Phase 005 Governance Charter, the components evaluated in this phase are classified independently:

```text
===================================================================
1. LABOR OPPORTUNITY-COST ENGINE:
   CLASSIFICATION = READY FOR OFFLINE CONSUMPTION / MICRO-VALIDATED
   
   - Architecture: Generic, cross-cutting, reusable service.
   - Micro-Validation: 30/30 unit, property invariant, and adversarial tests passed.
   - Full Regression: 384/384 test suite green in 2.04s.
   - Diagnostic Replay: 888 historical opportunities evaluated across 25 development seeds.
   - Latency Profile: p50 = 1.27 ms, p95 = 6.29 ms, peak = 15.84 ms (well below 100 ms limit).
   - Scope: Ready for offline filtering, diagnostic replay, and integration with candidate generators.
   - Boundary: Not yet cleared for live prospective tournament execution until closed-loop integration testing.

2. RESOURCE_CONVERSION MECHANISM:
   CLASSIFICATION = NOT READY / QUARANTINED
   
   - Phase 004B Status Preserved: Strictly quarantined in production configuration.
   - Phase 005 Directive Preserved: Zero attempts to rescue or activate RESOURCE_CONVERSION.
   - Live Commit Status: Disabled in production config and benchmark harness.
===================================================================
```

---

### 2. Scientific Rigor: Epistemological Boundaries

To maintain scientific integrity, findings are categorized across strict epistemological tiers:

#### 2.1 Proven Facts
1. **Implementation Behavior**:
   - The engine derives marginal labor opportunity cost directly from game state, worker trajectory projections, carried cargo, and counterfactual simulation.
   - Does not use ordinal scheduler priority integers (e.g. 1000, 600) for dollar valuation (§7).
   - Does not use arbitrary monetary thresholds or hand-authored constants (§12, §30).
2. **Deterministic Verification**:
   - All 20 micro-tests (LO-01 to LO-20) pass deterministically.
   - All 8 formal property invariants (Invariants A to H) are strictly satisfied.
   - Deterministic repeat assessment yields bit-identical outputs.
3. **Diagnostic Triage**:
   - Replay on 25 development seeds (`50000–50024`) demonstrated that 136 of 576 historical conversion commits displaced active crop cultivation/care workers, creating up to $198.00 in opportunity cost and destroying net margin. The engine successfully rejected all 136 instances offline.
4. **Safety & Chassis Integrity**:
   - V3 chassis archive hash verified byte-identical (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
   - Prospective cohort (`340300–340349`) and holdout cohorts (`340050–340199`, `214200–214249`) remained completely untouched.

#### 2.2 Inferences
1. **Loss Mitigation**:
   - In Phase 004B, physical conversions exhibited an ITT penalty of -$1417.54 because auxiliary labor was diverted indiscriminately. Filtering candidate patches through `LaborOpportunityCostEngine` would causally prevent the 136 destructive diversions, preserving baseline cash crop yields.
2. **Cross-Mechanism Utility**:
   - Because the engine operates on typed `WorkerEntity` and game trajectories rather than mechanism-specific rules, it will provide identical opportunity-cost protection to other labor-dependent families (e.g. harvest, weed digging, cargo ferry).

#### 2.3 Not Yet Proven
1. **Live Tournament Delta**:
   - Closed-loop prospective tournament margin benefit has not been measured (no prospective runs were performed, per scientific directives).
2. **Generalization Beyond Development Seeds**:
   - Performance on unseen holdout distributions remains unmeasured until formal prospective trial preregistration.

---

### 3. Recommended Next Capability: Evidence-Based Selection

Per Section 39 of the charter, the next phase must be selected based on architectural evidence rather than preselected mechanism preferences:

#### 3.1 Architectural Diagnostics
- The offline replay revealed that in **440 instances**, auxiliary workers were completely idle (`PASS`) while mature crops or high-margin opportunities existed nearby.
- However, mechanisms like `RESOURCE_CONVERSION` are economically unsuitable due to low commodity margins relative to capital risk.
- In contrast, crops like strawberry, tomato, and carrot represent the primary source of cash generation, but auxiliary workers often remain idle while mature crops wait in the field unharvested.

#### 3.2 Recommended Next Target: `DYNAMIC_SHADOW_HARVEST` or `TERMINAL_HARVEST_SWEEP`
- **Candidate Mechanism**: `DYNAMIC_SHADOW_HARVEST` / `TERMINAL_HARVEST_SWEEP`.
- **Architectural Synergy**:
  - The `LaborOpportunityCostEngine` is now available to verify that mobilizing an idle auxiliary hand to harvest nearby mature crops has **$0.00 opportunity cost** and generates immediate liquid cash.
  - The `MultiWorkerDominancePruner` can verify that harvest tasks strictly dominate idle waiting.
- **Action**: Proceed to formal preregistration of the harvest opportunity family using the new labor engine for offline candidate gating.
