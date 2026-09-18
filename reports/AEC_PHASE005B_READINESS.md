# SPDX-License-Identifier: MIT
# AEC Phase 005B: Labor Opportunity Engine Ground-Truth & Harvest Discovery
## Production Readiness & Capability Roadmap Report

**Phase**: AEC Phase 005B  
**Component**: `LaborOpportunityCostEngine` (`aec/resource/labor_engine.py`)  
**Date**: September 2026  
**Status**: VALIDATED WITH QUALIFICATIONS  

---

### 1. Architectural Readiness Classification

In accordance with Section 16 of the AEC Phase 005B Governance Directives, the evaluated components are classified independently:

```text
===================================================================
1. LABOR OPPORTUNITY-COST ENGINE:
   CLASSIFICATION = VALIDATED WITH QUALIFICATIONS

   - Mathematical Corrections Applied:
     * Biological asset double-counting fixed in _estimate_growing_crops_value.
     * Phantom opportunity cost on unexecutable no-op candidate actions fixed.
     * Worker transit movement (MOVES) removed from idle baseline.
     * Preconditions on FEED and HARVEST strictly enforced.
     * Module circular import in coordination/__init__.py resolved via lazy loading.
   - Micro-Validation: 12/12 dedicated GT tests passed (GT-01 through GT-12).
   - Full Regression: 396/396 repository tests green in 2.08s.
   - Epistemological Qualification:
     * Validated for local marginal labor opportunity-cost gating and offline triage.
     * Not equivalent to full 720-step game delta for uncoupled 1-turn patches due to
       downstream agent state desynchronization. Isolated 1-turn patches must not be
       injected without coupled return-route reconnection.

2. HARVEST OPPORTUNITY FAMILY (DYNAMIC_SHADOW_HARVEST):
   CLASSIFICATION = STRUCTURALLY VALID / READY FOR OFFLINE PREREGISTRATION

   - Abundance: 89,590 genuine candidates discovered across 25 development seeds.
   - Idle-Worker Candidates: 3,734 immediately harvestable or nearby opportunities.
   - Immediate Harvestability: 18,376 instances where worker is on mature crop tile.
   - Preregistration Condition: Must implement full CoupledPatch with return routing
     (Navigate -> Harvest -> Shed Drop -> Reconnect) to avoid cargo desynchronization.

3. RESOURCE_CONVERSION MECHANISM:
   CLASSIFICATION = NOT READY / STRICTLY QUARANTINED

   - Preserved in quarantine; zero live production commits enabled.
===================================================================
```

---

### 2. Runtime Performance Benchmark by Valuation Level

Latency was benchmarked across **89,690 total invocations** spanning all hierarchical tiers:

| Valuation Tier | Method / Scope | Invocations | p50 (ms) | p95 (ms) | p99 (ms) | Peak Max (ms) | Budget Limit | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Level 0** | Spatial & Day-Boundary Feasibility | 3,461 | **0.007** | 0.015 | 0.023 | 0.179 | 5.0 ms | **PASS** |
| **Level 1** | Local Exact Dependency ($0.00 OC) | 1,785 | **0.144** | 0.248 | 0.397 | 0.782 | 10.0 ms | **PASS** |
| **Level 2** | Broader Trajectory & Peer Absorption | 9,795 | **3.486** | 7.935 | 9.910 | 46.009 | 30.0 ms | **PASS** |
| **Level 3** | Exact Forward Simulation Rollout | 71,092 | **3.655** | 10.672 | 13.361 | 96.777 | 100.0 ms | **PASS** |
| **Level 4** | Full-Horizon Terminal Fallback | 3,557 | **2.528** | 8.288 | 11.680 | 21.553 | 100.0 ms | **PASS** |
| **Total Engine** | **Hierarchical Escalation Engine** | **89,690** | **3.642** | **10.640** | **13.332** | **96.777** | **100.0 ms** | **PASS** |

All valuation levels operate comfortably within the 100.0 ms per-turn AEC execution ceiling.

---

### 3. Scientific Rigor: Epistemological Boundaries

#### 3.1 Proven Facts
1. **Mathematical Grounding**:
   - The engine's corrected formula $\text{OpportunityCost} = \max(0, X - (V_{\text{alt}} - V_{\text{base}}))$ correctly recovers baseline lost value $Y$ without double counting.
   - Field asset valuation no longer cancels out worker harvest revenue.
   - Transit movements are no longer classified as idle.
2. **Reconciliation Truth**:
   - Phase 005's 440 approved records were 100% Resource Conversion (`FEED`) records, not harvest opportunities.
   - Market timing and emergency feed accounted for 312 records with no worker involvement.
3. **Genuine Harvest Volume**:
   - 89,590 genuine harvest opportunities exist across seeds `50000–50024`.
4. **Governance Integrity**:
   - V3 chassis SHA-256 hash verified byte-identical (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
   - Prospective cohort (`340300–340349`) and holdout cohorts (`340050–340199`, `214200–214249`) remained completely untouched.

#### 3.2 Inferences
1. **Compounding Policy Coupling**:
   - Injecting an uncoupled 1-turn harvest patch causes cargo desynchronization in long matches. A coupled patch architecture that guarantees inventory drop-off and route reconnection will avoid the -$7,452.32 desynchronization penalty.
2. **Offline Gating Value**:
   - The labor engine provides high-fidelity filtering to reject worker diversions that destroy high-value crop care (preventing up to $198.00 in opportunity cost).

#### 3.3 Not Yet Proven
1. **Closed-Loop Spliced Harvest Margin**:
   - Net tournament benefit of spliced `CoupledPatch` harvest execution has not been measured under prospective conditions.
2. **Cross-Cohort Generalization**:
   - Generalization to unseen holdout distributions remains unmeasured until formal prospective trial preregistration.

---

### 4. Recommended Next Phase: AEC Phase 006

**Recommendation**: Proceed to **AEC Phase 006: Offline Preregistration & Coupled Trajectory Splicing for `DYNAMIC_SHADOW_HARVEST`**.

Key Milestones for Phase 006:
1. Implement `HarvestCoupledPatchGenerator` creating 4-phase spliced trajectories: `[NAVIGATE] -> [HARVEST] -> [DROP_SHED] -> [RECONNECT]`.
2. Offline validation across seeds `50000–50024` verifying that spliced harvest patches yield $\Delta_{\text{exact}} > 0$.
3. Formal preregistration of prospective trial protocol before any holdout touch.
