# AEC PHASE 010: MASTER MECHANISM QUALIFICATION PREREGISTRATION
**Author**: Lead Scientific Experiment Engineer, Adaptive Economic Compiler (AEC)  
**Date**: 2026-09-18  
**Architecture State**: FROZEN RESEARCH PLATFORM (Phase 009 Finalized 44-Item Architecture)  
**V3 Baseline Chassis Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Touchless Protected Holdout Protection, Mechanism-Level Empirical Isolation  

---

## 1. Executive Protocol Summary

Phase 009 established the complete architectural integration and functional verification of the 44-item Adaptive Economic Compiler (AEC), resulting in 492 passing unit/contract tests, bit-identical preservation of the V3 chassis, zero runtime crashes, and confirmed mechanism attribution in 50 mirror-seat matches on development seeds `249025–249049`.

Phase 010 is the **Mechanism Qualification Campaign**. Under the Phase 009 architecture freeze:
- **No architectural expansion**: No new mechanisms, heuristics, opportunity families, or control layers are permitted.
- **Single-Mechanism Isolation**: Every experimental evaluation isolates exactly **one** transformational mechanism against an identical frozen AEC foundation.
- **Empirical Gate**: Only mechanisms satisfying the strict 12-item Qualification Contract will be promoted from quarantine into the live-eligible `AEC_ROBUST_QUALIFIED` build.

---

## 2. Frozen Foundation Specification

Every qualification comparison utilizes the identical frozen control foundation:
- `FROZEN_V3_BACKBONE` (Unmodified Kaggle V3 chassis; SHA256 verified)
- `DEPENDENCY_AWARE_MARKET_TIMING` (Validated causal market order scheduler)
- `TERMINAL_LIQUIDATION` (Step 716-718 asset liquidation)
- `PHASE_SHUTDOWN` (Late-stage crop and animal purchase cutoff)
- `SAFETY_DEFENSE_IN_DEPTH` (Layer 3 multi-predicate safety verification)
- `EXACT_COUNTERFACTUAL` (18/36-step trajectory simulation)
- `COUPLEDPATCH` (Multi-turn, multi-worker trajectory patch representation)
- `RECONNECTION_ENGINE` (Deterministic collision-free suffix splicing)
- `MULTI_WORKER_LOGISTICS` (Spacetime reservation grid)
- `CANDIDATE_FUNNEL` (Static and dynamic pruning gates)
- `ROBUST_FALLBACK` (Instantaneous zero-drift fallback to V3 backbone on any exception)

**Experimental Arms**:
- **Control**: Frozen Foundation ($M_{\text{ctrl}}$).
- **Treatment**: Frozen Foundation + **ONE** experimental mechanism switched from `QUARANTINED` to `ENABLED` ($M_{\text{trt}}$).

---

## 3. Seed Governance & Cohort Allocation

### 3.1 Protected Holdout Partitions (IMMUTABLE & UNTOUCHED)
Under the Section 8 Holdout Protection Covenant, the following seed partitions are certified virgin and **MUST NOT BE ACCESSED OR SIMULATED**:
1. `340050–340199` ($N=150$, Primary Locked Holdout)
2. `214200–214249` ($N=50$, Gate 0.3 Virgin Final Holdout)
3. `340300–340349` ($N=50$, Prospective Tournament Cohort)

### 3.2 Historical Development Cohorts (PERMANENTLY RETIRED)
The following seed cohorts were used in prior development/remediation phases and are retired from fresh qualification:
- `50000–50024` (Phase 007 benchmark)
- `249000–249024` (Phase 008 primary cohort)
- `249025–249049` (Phase 009 development replay)

### 3.3 Certified Fresh Development Partitions for Phase 010
All seeds in the range `249050–249250` have been audited and verified 100% clean across workspace files, commit logs, and previous replays:
- **Pilot Cohort (Stage A)**: Seeds `249050–249059` ($N=10$ seeds, 20 mirror matches)
- **Cohort Q1 (Priority Group A Formal Qualification)**: Seeds `249060–249084` ($N=25$ seeds, 50 mirror matches)
- **Cohort Q2 (Priority Group A Replication / Priority Group B Qualification)**: Seeds `249085–249109` ($N=25$ seeds, 50 mirror matches)
- **Cohort Q3 (Priority Group B Replication / Priority Group C Qualification)**: Seeds `249110–249134` ($N=25$ seeds, 50 mirror matches)
- **Cohort Q4 (Priority Group C Formal Qualification)**: Seeds `249135–249159` ($N=25$ seeds, 50 mirror matches)
- **Cohort Q5 (Priority Group D/E Formal Qualification)**: Seeds `249160–249184` ($N=25$ seeds, 50 mirror matches)
- **Cohort R1 (Final Integrated Regression)**: Seeds `249185–249209` ($N=25$ seeds, 50 mirror matches)

---

## 4. Staged Testing Strategy (Two-Stage Design)

To maximize information gain and adhere to competition deadline constraints without post-hoc tuning:

### Stage A — Pilot Exposure Test
- **Purpose**: Verify natural candidate proposal and execution exposure under real full-game dynamics.
- **Cohort**: Fresh development seeds (e.g., $N=5$ to $10$ seeds, mirror seating).
- **Gate Evaluation**:
  - If **zero natural exposure / zero commits**: Classify the mechanism immediately (`DORMANT / FUNCTIONALLY COMPLETE` or `INCONCLUSIVE / INSUFFICIENT EXPOSURE`). Diagnose the root cause (rare trigger state, tight baseline schedule dominance, or conservative pruning). **Do not tune parameters or force artificial commits**. Move to the next mechanism.
  - If **natural exposure occurs** (candidates reach exact simulation and produce commits): Advance immediately to Stage B.

### Stage B — Formal Qualification & Replication
- **Cohort**: Fresh independent cohort ($\ge 25$ seeds, 50 mirror matches).
- **Execution**: Run paired Common Random Numbers (CRN) mirror matches.
- **Statistical Evaluation**: Compute paired mean net delta, SE, $t$-statistic, $p$-value, win/loss/tie, downside tail risk, and counterfactual prediction fidelity.
- **Replication**: If the primary qualification cohort is positive, replicate on a second independent $N=25$ development cohort before certifying `QUALIFIED`.

---

## 5. Formal 12-Item Qualification Contract

A mechanism is certified as `QUALIFIED` if and only if **all 12** criteria are satisfied:
1. **Implementation Verified**: Source code complete, typed, documented, and adhering to frozen architecture.
2. **Synthetic Activation Verified**: 100% pass on synthetic activation matrix tests.
3. **Real-Game Exposure Occurs**: Proposed opportunities naturally reach candidate screening in full-game replay.
4. **Candidates Reach Exact Simulation**: Non-zero candidates pass the candidate funnel and undergo exact counterfactual simulation.
5. **Predicted / Realized Effect Agrees**: Mean prediction error is bounded; predicted superior patches actually realize positive economic margins.
6. **Safety Violations = 0**: Zero safety predicate violations across all turns.
7. **No Governance Violations**: Zero touches of protected cohorts; V3 chassis hash invariant verified.
8. **Mean Paired Effect is Positive**: $\text{Mean}(\Delta_{\text{seed}}) > 0.0$.
9. **Confidence Interval Compatible with Positive Effect**: Lower bound of $95\%$ CI does not exhibit severe downside instability.
10. **No Obvious Heavy-Tail Failure**: P95 downside does not introduce game-losing catastrophic drawdowns compared to baseline.
11. **Mechanism Attribution is Pure**: Exactly 100% of non-foundation commits correspond exclusively to the tested mechanism.
12. **Result Reproduces on Independent Cohort**: Positive effect replicates on a disjoint fresh development partition.

---

## 6. Staged Qualification Order

1. **Priority Group A — Worker-Time & Harvest Economics**:
   - `DYNAMIC_SHADOW_HARVEST`
   - `TERMINAL_HARVEST_SWEEP`
   - `LABOR_SHADOW`
2. **Priority Group B — Logistics**:
   - `ROUTE_COMPRESSION`
   - `CARGO_FERRY`
3. **Priority Group C — Market & Production Arbitrage**:
   - `TOWN_CYCLE`
   - `SHOP_ARBITRAGE`
   - `PRODUCTION_ARBITRAGE`
   - `TERMINAL_CONVERSION`
4. **Priority Group D — Emergency Recovery**:
   - `EMERGENCY_FEED_PURCHASE`
   - `EMERGENCY_RECOVERY`
5. **Priority Group E — Opponent / Meta**:
   - `OPPONENT_PREEMPT_SELL`
   - `META`
6. **Priority Group F — Resource Conversion**:
   - `RESOURCE_CONVERSION` (Quarantine maintained per prior empirical falsification)

---

## 7. Metrics & Output Telemetry Standards

Every qualification test records:
- Total seeds ($N$), total matches ($2N$).
- Opportunities proposed, candidates screened, funnel survivors, exact simulations run.
- Commits, abstentions, fallback events, safety rejections.
- Predicted delta vs realized delta, mean absolute prediction error (MAE).
- Per-seed paired delta: Mean, Median, StdDev, Standard Error, $t$-statistic, $p$-value.
- Win / Loss / Tie record and tie-excluded win rate.
- Worst seed delta, best seed delta.
- Latency profile: p50, p95, p99, and worst-turn latency (ms).
- Ratios: Activation rate, commit rate conditional on exposure, commit purity, benefit purity, harmful commit rate.

Artifact outputs:
- Telemetry: `results/PHASE010_<MECHANISM>_TELEMETRY.json`
- Match results: `results/PHASE010_<MECHANISM>_RESULTS.csv`
- Formal qualification report: `reports/PHASE010_<MECHANISM>_QUALIFICATION.md`
- Master mechanism registry: `reports/AEC_PHASE010_MECHANISM_REGISTRY.md`
