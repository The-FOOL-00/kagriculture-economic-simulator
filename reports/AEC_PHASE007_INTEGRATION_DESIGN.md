# AEC PHASE 007: FULL INTEGRATION DESIGN SPECIFICATION
**Autonomous Economic Compiler — Complete Architecture, Governance, and Control Flow**
**Date:** 2026-09-18  
**Governance:** Phase 007 Completion Audit; Zero Prospective Competition; Development Cohort Only (`50000–50024`)  
**Frozen V3 Chassis:** `submission_Vj_kc_v3.tar.gz` (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)

---

## 1. Executive Architectural Statement

Phase 006 established the trajectory-preserving `CoupledPatch` primitive and empirically validated `DYNAMIC_SHADOW_HARVEST` and `TERMINAL_HARVEST_SWEEP` on development seeds 50000–50024. However, Phase 006 did not complete the broader, originally finalized AEC architecture.

Phase 007 fulfills the originally intended full AEC architecture without dropping capabilities or substituting heuristic shortcuts. All 32 core components and opportunity families have been brought into a unified, layered control framework:

```text
                    OBSERVATION
                        │
                        ▼
                 ECONOMIC IR
                        │
                        ▼
                V3 BACKBONE
                        │
                        ▼
              EVENT / CHANGE DETECTOR
                        │
                        ▼
              OPPORTUNITY DETECTOR
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       ECONOMIC      OPPONENT      DEPENDENCY
       CONTEXT       PRESSURE       CLOSURE
          └─────────────┼─────────────┘
                        ▼
                 CANDIDATE FUNNEL
                        │
                        ▼
               LABOR / RESOURCE
                  SCREENING
                        │
                        ▼
                PATCH GENERATOR
                        │
                        ▼
                  COUPLEDPATCH
                        │
                 ┌──────┴──────┐
                 ▼             ▼
             RECONNECT      MULTIWORKER
                 └──────┬──────┘
                        ▼
               ADAPTIVE HORIZON
                        │
                        ▼
             EXACT COUNTERFACTUAL
                        │
                        ▼
            ECONOMIC / MARGIN EVAL
                        │
                        ▼
                 SAFETY CERT
                        │
                        ▼
                COMMIT / ABSTAIN
                    │       │
                  COMMIT  ABSTAIN
                    │       │
                    └───┬───┘
                        ▼
                   V3 EXECUTOR
```

---

## 2. Structural Layer Separation: Macro, Tactical, Executor

The architecture strictly separates economic direction, local optimization, and physical action commitment:

```text
       MACRO (Farm Economic Posture & Capital Reservation)
         ↓
       TACTICAL (Opportunistic Candidates & Trajectory Splicing)
         ↓
       EXECUTOR (Certified Execution & Deterministic Fallback)
```

### 2.1 Macro Layer (`aec/macro/`)
* **Purpose:** Sets the farm's high-level economic stance across four phases: `EARLY_EXPANSION`, `BALANCED_PRODUCTION`, `LIQUIDITY_CONSERVATIVE`, and `TERMINAL_HARVEST_RUN`.
* **Capital Discipline:** Enforces `min_cash_reserve` against unhedged tactical capital expenditures. A tactical patch cannot commit if it leaves remaining cash below the reserve cushion needed for nightly worker wages and high-margin seasonal seeds.
* **Non-Subversion Invariant:** Tactical patches are strictly forbidden from silently mutating macro policy. Any macro-level shift (e.g. pivoting crop priorities or liquidating livestock) requires explicit event escalation.

### 2.2 Tactical Layer (`aec/tactical/`)
* **Purpose:** Coordinates tactical opportunity generation across 14 opportunity families.
* **Proposals:** Frames localized trajectory deviations (`TacticalProposal`) with bounded duration, explicit upfront cost, and causal profit rationale.
* **Screening:** Submits proposals through the candidate funnel and macro compatibility validator.

### 2.3 Executor Layer (`aec/integration/executor.py`)
* **Purpose:** Executes the turn loop, enforcing the hard constraint of **exactly one live baseline call per turn**.
* **Safety Oracle:** Applies the machine-readable `SafetyCertificate`. If any invariant fails or simulation budget expires, the executor cleanly triggers `RobustFallbackPolicy` and returns the baseline action without guessing.

---

## 3. Cross-Cutting Subsystems

### 3.1 Event-Triggered Replanning (`aec/replanning/event_replanner.py`)
Rather than replanning blindly every turn (which would burn computation and invite policy instability), the `EventTriggeredReplanner` responds to 14 state-derived triggers:
1. `WORKER_IDLE`
2. `TASK_COMPLETED_EARLY`
3. `CROP_MATURE`
4. `ROUTE_BLOCKED`
5. `RESOURCE_DEPENDENCY_CHANGED`
6. `CASH_STATE_CHANGED`
7. `SHED_CAPACITY_CHANGED`
8. `LIVESTOCK_SECURITY_RISK`
9. `MARKET_PRICE_CHANGED`
10. `OPPONENT_PRESSURE_CHANGED`
11. `TERMINAL_WINDOW_ENTERED`
12. `BASELINE_ROUTE_STALE`
13. `POSTCONDITION_INVALIDATED`
14. `WORKER_ASSIGNMENT_CHANGED`

#### Escalation Hierarchy (§6):
* **L1 (Local Tactical):** Single-step micro-order reordering (Horizon 4).
* **L2 (Same Worker + Resource):** Local detour or crop harvest along current path (Horizon 12).
* **L3 (Asset / Cash Dependency):** Material cash shift, seed acquisition, or animal feeding (Horizon 24).
* **L4 (Multi-Worker / Market):** Cooperative hauling, shed capacity alert, or market timing (Horizon 48).
* **L5 (Full Remaining Horizon):** Terminal endgame salvage or postcondition invalidation (Remaining horizon up to 72).

### 3.2 10-Stage Candidate Funnel (`aec/funnel/candidate_funnel.py`)
Phase 006 established that exact counterfactual simulation costs ~1.86s median per 720-step evaluation. Brute-force simulation of all proposed opportunities is computationally impossible. The `OpportunityCandidateFunnel` screens candidates through 10 linear, sub-millisecond filters:

```text
Stage 1: Cheap Legality (Basic rule compliance & step boundaries)
Stage 2: Cheap Reachability (Manhattan reachability within remaining horizon)
Stage 3: Resource Feasibility (Upfront cash & macro cash reserve cushion)
Stage 4: Worker Availability (Worker operational & unfrozen)
Stage 5: Labor Shadow Valuation (Initial displacement cost screening)
Stage 6: Dependency Closure (Shed capacity & prerequisite tiles)
Stage 7: Dominance Pruning (Pareto dominance on same worker/target)
Stage 8: Route Cost Screen (Detour step cost vs estimated net yield)
Stage 9: Deterministic Top-K (Lexicographical tie-breaking into budget slots)
Stage 10: Exact Counterfactual (The authoritative certification layer)
```

#### Inference Budgeting (§30):
* `max_raw_candidates`: 32
* `max_candidates_screened`: 8
* `max_exact_simulations`: 4 (strictly bounded)
* `max_turn_time_ms`: 100.0ms per turn

### 3.3 Continuous Opponent Pressure Analyzer (`aec/counterfactual/opponent_pressure.py`)
Replaces speculative point predictions with an interpretable continuous pressure state (`OpponentPressureState`):
* **Market Activity Level:** Tracks rival cash acceleration and trade frequency.
* **Sale & Buy Pressure:** Per-commodity rival dumping risk.
* **Market Collision Risk:** Shared trade collision in town market depth.
* **Route Interference:** Physical proximity of rival worker to our active tiles.
* **Terminal Pressure:** Endgame liquidation acceleration as step approaches 718.
* **Opponent Safety Principle (§9):** Opponent pressure may prioritize candidates or escalate horizons, but **NEVER** overrides safety invariants or bypasses exact counterfactual certification.

### 3.4 META vs ROBUST Operational Modes (`aec/meta/meta_policy.py`)
The system provides three distinct operational configurations (§33):
* **`ROBUST_MODE`:** Restricts planning to scientifically proven robust mechanisms (`DEPENDENCY_AWARE_MARKET_TIMING`, `DYNAMIC_SHADOW_HARVEST`, `TERMINAL_HARVEST_SWEEP`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`). Operates with zero reliance on opponent behavior.
* **`META_MODE`:** Authorizes opponent-sensitive mechanisms (`OPPONENT_PREEMPT_SELL`, `MARKET_COLLISION_TIMING`, `TOWN_CYCLE`). If opponent model confidence drops below 0.40, META **fails closed** and safely falls back to `ROBUST_MODE`.
* **`RESEARCH_MODE`:** Diagnostic exploration across the full candidate registry (`SHOP_ARBITRAGE`, `PRODUCTION_ARBITRAGE`, `EMERGENCY_RECOVERY`) with simulation and logging enabled, but live commit gated by scientific status.

### 3.5 Patch Composition Engine (`aec/patches/composition.py`)
When multiple opportunities fire simultaneously, the `PatchCompositionEngine` certifies their formal composition relation (§37):
* **`PARALLEL`:** Operates on disjoint workers, distinct resources, and non-colliding paths (valid for joint commitment).
* **`SERIAL`:** Ordered causal dependency (Patch B executes after Patch A reconnects).
* **`MUTUALLY_EXCLUSIVE`:** Contests the same worker or single-use asset (one must be chosen).
* **`DOMINATES`:** One candidate yields higher net profit in equal or fewer steps (inferior candidate is pruned).
* **`CONFLICTS`:** Spatiotemporal vertex or edge-swap collision detected (rejected).

---

## 4. Opportunity Registry & Family Lifecycle

All 14 intended opportunity families are formally declared in `OpportunityRegistry` (`aec/opportunities/registry.py`):

| Mechanism Family | Category | Worker Req | Economic Model | Status | Live Eligible |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEPENDENCY_AWARE_MARKET_TIMING` | MARKET | NONE | EXACT_COUNTERFACTUAL | EXPERIMENTAL | YES |
| `DYNAMIC_SHADOW_HARVEST` | LABOR | ANY | EXACT_COUNTERFACTUAL | EXPERIMENTAL | NO (Validated) |
| `TERMINAL_HARVEST_SWEEP` | TERMINAL | ANY | EXACT_COUNTERFACTUAL | EXPERIMENTAL | NO (Validated) |
| `ROUTE_COMPRESSION` | ROUTE | ANY | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `CARGO_FERRY` | LABOR | AUXILIARY_ONLY | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `RESOURCE_CONVERSION` | RESOURCE | AUXILIARY_ONLY | EXACT_COUNTERFACTUAL | QUARANTINED | NO |
| `SHOP_ARBITRAGE` | MARKET | NONE | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `PRODUCTION_ARBITRAGE` | RESOURCE | ANY | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `TERMINAL_CONVERSION` | TERMINAL | ANY | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `OPPONENT_PREEMPT_SELL` | MARKET | NONE | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `EMERGENCY_RECOVERY` | RESOURCE | ANY | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `TOWN_CYCLE` | TIMING | NONE | EXACT_COUNTERFACTUAL | PLAUSIBLE_UNPROVEN | NO |
| `TERMINAL_LIQUIDATION` | TERMINAL | NONE | EXACT_COUNTERFACTUAL | VERIFIED_SOURCE | YES |
| `PHASE_SHUTDOWN` | TERMINAL | NONE | LOCAL_MARGINAL | VERIFIED_SOURCE | YES |

---

## 5. Defense-in-Depth Quarantine Enforcement

To guarantee that unproven or quarantined mechanisms (specifically `RESOURCE_CONVERSION`) cannot commit accidental live actions, defense-in-depth is enforced at three distinct layers:
1. **Layer 1 (Opportunity Detector):** `OpportunityEngine.detect_all()` verifies that the mechanism is in `enabled_mechanisms` and not in `quarantined_mechanisms`.
2. **Layer 2 (Candidate Funnel & Patch Generator):** `PatchGenerator.generate()` and `OpportunityCandidateFunnel` reject any candidate tagged with `ScientificStatus.QUARANTINED`.
3. **Layer 3 (Executor Commit Gate):** `AECExecutor.act()` checks `config.is_family_live_eligible(patch.mechanism_family)`. If a candidate is quarantined, it is forced to `ABSTAIN` with reason `"SCIENTIFIC_QUARANTINE"` and recorded to telemetry.
