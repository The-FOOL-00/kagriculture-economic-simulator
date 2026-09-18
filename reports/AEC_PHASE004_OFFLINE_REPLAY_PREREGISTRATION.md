# AEC Phase 004: Offline Replay Evaluation Preregistration

**Protocol Identifier**: `PREREG-PHASE-004-REPLAY-20260918-FINAL`  
**Phase**: AEC-004  
**Date**: 2026-09-18  
**Status**: FROZEN & BINDING  

---

## 1. Executive Summary & Experimental Intent

Phase 004 executes a deterministic offline re-validation across development seeds `50000–50024` to evaluate whether **Multi-Worker Logistics Coordination (Phase 003)** successfully eliminates the labor cannibalization failure modes historically observed in `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE`.

### Key Experimental Questions:
1. **QUESTION A (Resource Conversion Cannibalization)**: Does multi-worker coordination eliminate the physical diversion of the primary Farmer, allowing an auxiliary worker (Hand 1 / Hand 2) to execute conversion tasks while the Farmer continues high-value crop operations?
2. **QUESTION B (Feed Rescue Preservation)**: Does multi-worker coordination allow emergency feed purchases to be physically picked up and delivered by an auxiliary worker without diverting the Farmer from critical harvest duties?
3. **QUESTION C (Physical Safety Across Workers)**: Do multi-worker conversion and feed actions remain 100% collision-free, handoff-legal, and compliant with all 9 safety invariants?
4. **QUESTION D (Net Economic Utility)**: Does multi-worker dispatch produce non-negative offline development margin deltas without introducing hidden opportunity costs?

---

## 2. Experimental Population & Audit

### 2.1 Fixed Development Population
- **Cohort**: Seeds `50000–50024` ($N = 25$ contiguous seeds).
- **Match Design**: 2 mirror seats per seed $\times$ 4 experimental arms = **200 total matches** (720 turns per match, 144,000 total turns).
- **Opponent**: Identical mirror opponent (Frozen V3 baseline loaded in memory).

### 2.2 Governance & Holdout Isolation
- **Primary Holdout (`340050–340199`)**: Untouched ($0$ touches).
- **Secondary Holdout (`214200–214249`)**: Untouched ($0$ touches).
- **Prospective Continuums (`340000–340049`, `340200–340249`, `340250–340299`, `340300–340349`)**: Untouched ($0$ touches).
- **Prospective Competition Matches Run**: Exactly **0**.

---

## 3. Experimental Arms & Mechanism Isolation

| Arm ID | Arm Name | Enabled Mechanisms | Quarantined Mechanisms | Multi-Worker Status | Role |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Arm A** | `CONTROL` | Foundation (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`) | `RESOURCE_CONVERSION`, `EMERGENCY_FEED_PURCHASE` | N/A | Authoritative Frozen Baseline |
| **Arm B** | `RESOURCE_CONVERSION_ONLY` | Foundation + `RESOURCE_CONVERSION` | `EMERGENCY_FEED_PURCHASE` | Active | Target Mechanism Isolated |
| **Arm C** | `EMERGENCY_FEED_ONLY` | Foundation + `EMERGENCY_FEED_PURCHASE` | `RESOURCE_CONVERSION` | Active | Target Mechanism Isolated |
| **Arm D** | `COMBINED_RESOURCE` | Foundation + `RESOURCE_CONVERSION` + `EMERGENCY_FEED_PURCHASE` | None (of target mechanisms) | Active | Exploratory Cross-Interaction Only |

All other experimental parameters (engine constants, V3 backbone, simulator seed, and market models) remain bit-for-bit identical across all arms.

---

## 4. Labor Cannibalization & Operational Metrics

For every match and committed candidate, the runner records:
1. `PRIMARY_WORKER_DISPLACEMENT_RATE`: Fraction of candidates where Farmer was diverted from baseline.
2. `AUXILIARY_WORKER_ABSORPTION_RATE`: Fraction of candidates where Hand 1/2 absorbed the deviation.
3. `BASELINE_TASKS_PRESERVED`: Number and fraction of baseline tasks completed without disruption.
4. `BASELINE_TASKS_DELAYED`: Number of baseline tasks completed later within valid deadline.
5. `BASELINE_TASKS_CANCELLED`: Optional tasks superseded vs mandatory tasks lost (mandatory lost must be 0).
6. `HIGH_VALUE_HARVESTS_DISPLACED`: Explicit count of ripe crop harvests ($>\$50$) missed due to deviation (must be 0).
7. `TERMINAL_MARGIN_DELTA`: Both all-seed ITT delta ($\overline{\Delta}_{ITT}$) and triggered-subset delta ($\overline{\Delta}_{trig}$).

---

## 5. Hard Safety Criteria (Fail-Closed Gates)

Zero tolerance for:
- Gate 1: Illegal worker actions or invalid coordinates.
- Gate 2: Direct worker-to-worker handoffs (must route through shed).
- Gate 3: Spacetime vertex collisions or edge swaps.
- Gate 4: Resource double-allocations or building contention.
- Gate 5: Shed capacity overflows ($>100$ units).
- Gate 6: Negative cash balance ($<\$0.00$).
- Gate 7: Counterfactual prediction divergence ($>0.00$ residual on realized steps).

---

## 6. Predeclared Binding Commitments

1. **No Retuning**: No priority weights, scheduler parameters, or opportunity thresholds will be adjusted during or after the run.
2. **No Cherry-Picking**: All 25 seeds `50000–50024` will be evaluated regardless of whether individual seeds yield positive or negative deltas.
3. **No Claim Inflation**: Outcomes will be reported strictly as *offline development replay evidence*, not prospective competition validation.
