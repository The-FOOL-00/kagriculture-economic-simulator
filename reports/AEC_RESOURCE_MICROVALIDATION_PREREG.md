# PREREGISTRATION PROTOCOL: AEC RESOURCE MICRO-VALIDATION
## Phase 002B: Controlled Evaluation of RESOURCE_CONVERSION & EMERGENCY_FEED_PURCHASE

**Protocol Identifier:** `PREREG-AEC-RESOURCE-MICRO-001`  
**Registration Date:** 2026-09-17  
**Governance Authority:** Principal Scientific Validation Engineer  
**Task Classification:** Phase 002B — Offline Deterministic Micro-Validation  
**Prospective Competition Trial:** **FALSE (STRICTLY PROHIBITED)**  
**Base Software Commit:** `5fe217d5b7d5b7252242e96f90144fee4e55267b`  
**Frozen V3 Chassis SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Engine Version:** `kagsim` 1.32.7 (C++ compiled extension `kagsim.cp314-win_amd64.pyd`)  
**Status:** **FROZEN PRIOR TO REPLAY EXECUTION**

---

### 1. Scientific Objective

The objective of Phase 002B is **NOT** to evaluate leaderboard score optimization or claim competition superiority.  
The objective is strictly to determine:

> *"Can `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE` safely generate, simulate, certify, execute, or abstain from candidate patches under deterministic historical replay conditions without violating backbone, resource conservation, temporal availability, capacity, cash liquidity, route reconnection, livestock feed security, or terminal invariants?"*

Empirical safety, mechanism isolation, counterfactual fidelity, and fail-closed adherence must be proven on deterministic historical/development traces before any prospective competition cohorts can ever be considered.

---

### 2. Replay Population & Selection Rules

#### 2.1 Authorized Replay Cohort
- **Partition:** Historical Development Benchmark Partition
- **Seed Range:** `50000–50024` ($N = 25$ contiguous seeds).
- **Match Format:** 2 matches per seed (Mirror Seat CRN: Seat 0 and Seat 1, total 50 matches, 35,950 total turns per experimental arm across 4 arms = 143,800 turns).
- **Baseline Generator:** Frozen Vj_kc_v3 control backbone executing live in `kagsim.Game(seed)`.

#### 2.2 Objective Selection Rule
- **Selection Rule:** The first contiguous block of 25 historical benchmark seeds starting at `50000`.
- **Outcome Independence:** Zero seeds were selected, filtered, or reordered based on economic performance, win rate, or favorable treatment deltas.

#### 2.3 Disjointness & Holdout Protection Proof
- **AEC Locked Holdout (`340050–340199`):** Overlap = **0**. Minimum distance = 289,951 seeds.
- **Gate 0.3 Virgin Final Holdout (`214200–214249`):** Overlap = **0**. Minimum distance = 164,151 seeds.
- **EXP-AEC-001 Consumed Archive (`340000–340049`):** Overlap = **0**.
- **EXP-AEC-002 Consumed Archive (`340200–340249`):** Overlap = **0**.
- **EXP-AEC-003 Consumed Archive (`340250–340299`):** Overlap = **0**.
- **DEV-007 Reserved Cohort (`310000–310499`):** Overlap = **0**.

#### 2.4 State Richness Verification
Audit confirms that seeds `50000–50024` under V3 baseline self-play exercise:
- Multiple shop worlds (Smoothie, Ice Cream, Bakery, Pizza).
- Extensive livestock operations (COW, SHEEP, GOOSE, coops, pastures).
- Feed stock fluctuations (wheat stock in shed/carried fluctuating between 0 and 60+).
- Thousands of conversion opportunities and hundreds of feed deficit encounters.

---

### 3. Experimental Arms & Mechanism Isolation Design

The validation enforces strict mechanism separation. Each mechanism is evaluated in isolation against the baseline control:

| Arm ID | Configuration Name | Active Mechanisms | Quarantined Mechanisms | Evaluation Purpose |
|:---|:---|:---|:---|:---|
| **Arm A** | `CONTROL` | `DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN` | All others | Control baseline (frozen foundation) |
| **Arm B** | `RESOURCE_CONVERSION_ONLY` | Control + `RESOURCE_CONVERSION` | `EMERGENCY_FEED_PURCHASE`, all others | Isolated validation of conversion DAG |
| **Arm C** | `EMERGENCY_FEED_ONLY` | Control + `EMERGENCY_FEED_PURCHASE` | `RESOURCE_CONVERSION`, all others | Isolated validation of feed security |
| **Arm D** | `COMBINED_RESOURCE` | Control + `RESOURCE_CONVERSION` + `EMERGENCY_FEED_PURCHASE` | All others | Exploratory interaction audit only |

> [!WARNING]
> Arm D is evaluated strictly for exploratory interaction checks. It does **NOT** constitute primary validation evidence. Primary evidence requires independent validation under Arm B and Arm C.

---

### 4. Configuration, Thresholds & Horizon Policy

All parameters are frozen in `AECConfig` for the micro-validation harness:
- `short_horizon`: 6 steps.
- `normal_horizon`: 18 steps.
- `extended_horizon`: 36 steps.
- `max_opportunities`: 16 proposals per turn.
- `max_candidates`: 8 candidates after static pruning.
- `max_simulations`: 8 forward simulations per turn.
- `shed_capacity`: 100 units.
- `shed_alarm_threshold`: 95 units.
- `fail_closed`: True (hard abort / abstain on any invariant breach).
- `per_step_latency_limit_ms`: 100.0 ms.

#### Horizon Escalation Policy:
1. `LOCAL`: Evaluates immediate step $t$ balance.
2. `DEPENDENCY_CLOSURE`: Automatically expands along `RESOURCE_COUPLING` and `FEED_SECURITY_COUPLING` causal edges.
3. `MEDIUM_REPLAN` (6–18 steps): Livestock feed replenishment cycles.
4. `EXTENDED_REPLAN` (18–36 steps): Multi-stage conversion chains.
5. `FULL_REPLAN`: Proximity to terminal turn 718.

---

### 5. Mandatory Acceptance Criteria (18 Conditions)

A mechanism passes micro-validation if and only if **all 18 criteria** are satisfied:

1. **Holdout Non-Consumption**: Exactly 0 touches, inspections, or executions of seeds `340050–340199` and `214200–214249`.
2. **Frozen V3 Immutability**: `submission_Vj_kc_v3.tar.gz` SHA-256 remains `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
3. **No Unrelated Mechanism Activation**: Zero commits generated by unauthorized or quarantined mechanisms (`FRONTLOAD_ORDERS`, `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`).
4. **Deterministic Reproducibility**: 100% bit-exact parity across identical repeated evaluations ($N = 5$ repetitions).
5. **Resource Conservation**: Input/output mass conservation strictly satisfied on every step.
6. **Non-Negative Inventory**: Zero negative inventory events across all commodities ($\text{qty} \ge 0$).
7. **Feed-Security Invariant**: Zero animal escapes or starvation events caused by candidate interventions.
8. **No Animal Starvation/Death**: Two consecutive days of starvation are prevented or never induced.
9. **Capacity Consistency**: Shed occupancy never exceeds 100 units at any step.
10. **Cash Liquidity**: Intermediate cash balances never drop below 0 ($\text{cash} \ge 0$).
11. **Temporal Availability**: Resources are never consumed prior to arrival turn ($t_{\text{consume}} \ge t_{\text{arrive}}$).
12. **No Stale Trajectory Execution**: All worker mutations utilize `AEC-RECONNECT` trajectory repair.
13. **Route Splicing Consistency**: Reconnected routes are collision-free and respect spacetime reservation bounds.
14. **Exact Counterfactual Parity**: Predicted deltas match realized simulation deltas ($\Delta_{\text{pred}} \equiv \Delta_{\text{sim}}$).
15. **Fail-Closed Safety**: 100% of unsafe, infeasible, or diverging candidates deterministically fail closed to `ABSTAIN`.
16. **Explicit Commit Attribution**: Every committed patch includes complete cryptographic and provenance metadata.
17. **Determinism Parity**: Bit-for-bit identical telemetry and decisions on repeated trace inputs.
18. **Regression Suite Green**: Existing regression test suite passes 100% with zero regressions (233+ tests).

---

### 6. Adversarial Benchmark Cases

#### 6.1 RESOURCE_CONVERSION (Cases RC-1 through RC-12)
- **RC-1**: No valid conversion exists $\to$ No commit.
- **RC-2**: Valid single-stage conversion exists $\to$ Candidate generated, simulator confirms, safety passes.
- **RC-3**: Symbolically feasible but temporally impossible $\to$ ABSTAIN.
- **RC-4**: Intermediate cash shortage $\to$ ABSTAIN (CashLiquidityHole).
- **RC-5**: Shed overflow $\to$ ABSTAIN (CapacityOverflow).
- **RC-6**: Downstream obligation reservation conflict $\to$ ABSTAIN.
- **RC-7**: Route change required $\to$ AEC-RECONNECT invoked and validated.
- **RC-8**: Locally profitable conversion breaks downstream production $\to$ Overridden by dependency closure.
- **RC-9**: Unfinishable near terminal turn $\to$ ABSTAIN.
- **RC-10**: Multi-stage conversion chain $\to$ Exact temporal chain preserved.
- **RC-11**: Same-turn ordering $\to$ Exact non-commutative ordering preserved.
- **RC-12**: Repeated replay $\to$ Bit-for-bit deterministic.

#### 6.2 EMERGENCY_FEED_PURCHASE (Cases EF-1 through EF-12)
- **EF-1**: Feed sufficient $\to$ No unnecessary purchase.
- **EF-2**: Future feed deficit unavoidable $\to$ Opportunity generated.
- **EF-3**: Purchase arrives too late $\to$ ABSTAIN.
- **EF-4**: Purchase creates future cash deadlock $\to$ ABSTAIN.
- **EF-5**: Purchase averts starvation/escape $\to$ Exact simulator confirms.
- **EF-6**: Purchase causes shed overflow $\to$ ABSTAIN.
- **EF-7**: Requires worker travel $\to$ AEC-RECONNECT evaluates trajectory.
- **EF-8**: Competes with higher-priority dependency $\to$ Closure rejects unsafe candidate.
- **EF-9**: Feed purchase near terminal $\to$ Pruned.
- **EF-10**: No emergency exists $\to$ No false positive.
- **EF-11**: Two consecutive days starvation risk $\to$ Correctly predicted and averted.
- **EF-12**: Historical replay already contains incoming feed $\to$ No redundant purchase.

---

### 7. Output Metrics & Logging

For each arm and across all seeds, the harness records:
- `seed`, `match_id`, `step`, `seat`.
- `events_detected`, `opportunities_proposed`, `candidates_generated`.
- `simulations_executed`, `safety_checks_passed`, `safety_checks_failed`.
- `decision` (`COMMIT` vs `ABSTAIN`), `abstain_reason`.
- `committed_patch_id`, `committed_mechanism`, `provenance_record`.
- `predicted_delta_money`, `realized_delta_money`, `parity_discrepancy`.
- `latency_ms` (detection, DAG, closure, feed engine, conversion engine, reconnect, simulation, total).
- `final_terminal_margin`, `final_our_money`, `final_opp_money`.

---

### 8. Stopping Rules & Failure Protocol

1. **Immediate Hard Abort**:
   - Any access or reference to seeds `340050–340199` or `214200–214249`.
   - Any mutation or SHA mismatch on `submission_Vj_kc_v3.tar.gz`.
   - Any execution of a quarantined mechanism outside the isolated validation harness.
   - Any crash or unhandled exception in `kagsim` or the compiler pipeline.
2. **Readiness Evaluation**:
   - If any of the 18 criteria fail for a mechanism, it is marked `NOT_READY`.
   - Each mechanism is evaluated independently; failure of one does not block reporting for the other.
3. **No Retuning Rule**:
   - Parameters and thresholds are fixed by this preregistration. No parameters will be adjusted in response to observed replay results.
