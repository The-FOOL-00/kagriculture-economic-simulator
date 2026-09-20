# AEC PHASE 008: PREREGISTRATION PROTOCOL
**Full Integrated Offline Validation Under Common Random Numbers and Mirror Seating**  
**Date:** 2026-09-18  
**Epistemic Standard:** Pre-Committed Confirmatory Offline Protocol  
**Authoritative Chassis SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`

---

## 1. Experimental Motivation & Governance Mandate

The Adaptive Economic Compiler (AEC) architecture has completed its structural development phase. Phase 007 claimed that the integrated architecture achieved `+86.92` mean delta over baseline V3. However, the Phase 008 Canonical Architecture Audit discovered that:
1. Phase 007 evaluated Seat 0 only (unmirrored play), creating substantial first-mover bias.
2. The `+86.92` delta in Phase 007 was entirely produced by the foundation mechanism (`DEPENDENCY_AWARE_MARKET_TIMING`), while newly added harvest mechanisms had 0 commits.
3. The reported value was an arithmetic artifact of subtracting a negative single-seat control baseline ($-20.20$).

Therefore, **Phase 008** executes the first mathematically rigorous, unbiased, full-integrated offline validation of the canonical AEC architecture.

---

## 2. Experimental Design & Treatment Arms

The experiment employs a paired Common Random Numbers (CRN) design with **full mirror seating**:
For every seed $s$, two independent matches are executed:
- **Match 1 (Forward)**: Player 0 = Treatment Arm, Player 1 = Frozen V3
- **Match 2 (Reverse)**: Player 0 = Frozen V3, Player 1 = Treatment Arm

The net seed-level margin delta is computed as:
$$\Delta_{\text{net}}(s) = \frac{(\text{Reward}_{\text{Treat, M1}} - \text{Reward}_{\text{V3, M1}}) + (\text{Reward}_{\text{Treat, M2}} - \text{Reward}_{\text{V3, M2}})}{2}$$

This completely cancels out seed-level first-mover advantage, map topology asymmetries, and shop placement biases.

### Arm Specifications:

#### ARM A: FROZEN CONTROL (Baseline V3 Chassis)
- **Agent**: Unmodified Frozen V3 macro policy loaded directly from `submission_Vj_kc_v3.tar.gz`.
- **Opponent**: Unmodified Frozen V3 macro policy.
- **Expected Net Margin Delta**: Under mirror play, V3 vs V3 net margin delta is mathematically identically $0.00$.

#### ARM B: INTEGRATED ROBUST AEC
- **Agent**: `AECExecutor` configured with full compiler pipeline:
  - Economic IR (`build_economic_state`)
  - Macro Controller (`MacroController`)
  - Event-Triggered Replanning (`EventTriggeredReplanner`, E1–E8)
  - 10-Stage Candidate Funnel (`OpportunityCandidateFunnel`)
  - Tactical Planner (`TacticalPlanner`)
  - Coupled Trajectory Patch Engine (`CoupledPatchEngine`, `CoupledPatch`)
  - Dynamic Reconnection Engine (`ReconnectionEngine`)
  - Exact Counterfactual Simulator (`CounterfactualSimulator`)
  - Lexicographic Win Model (`WinModel`)
  - 9-Invariant Safety Checker (`SafetyChecker`)
  - Robust Fallback Policy (`RobustFallbackPolicy`)
  - **Enabled Mechanisms**:
    - `DEPENDENCY_AWARE_MARKET_TIMING`
    - `TERMINAL_LIQUIDATION`
    - `PHASE_SHUTDOWN`
    - `DYNAMIC_SHADOW_HARVEST`
    - `TERMINAL_HARVEST_SWEEP`
  - **Quarantined Mechanisms**: All 15 experimental/development mechanisms remain locked.
- **Opponent**: Frozen V3 macro policy (`submission_Vj_kc_v3.tar.gz`).

---

## 3. Cohort Specification & Absolute Isolation Covenant

### 3.1 Primary Evaluation Cohort: Fresh Reserved Discovery Partition
- **Seed Range**: `249000` to `249024` (Inclusive, $N = 25$ seeds, 50 paired CRN matches).
- **Provenance**: Formally established in `ARCHITECTURE_DISCOVERY_AND_14_DAY_MASTER_PLAN.md:770` and `EXP-DEV-006/SEED_PROVENANCE.md:66` as a reserved development discovery block.
- **Historical Executions**: **0 prior executions / 0 touches / 100% virgin within development registry**.
- **Separation**: Completely disjoint from all holdouts ($\min = 249000 > 214249 = \max(\text{Gate 0.3 Holdout})$; distance $> 90,000$ seeds from primary holdout).

### 3.2 Secondary Benchmark Cohort: Historical Re-Baseline
- **Seed Range**: `50000` to `50024` ($N = 25$ seeds, 50 paired CRN matches).
- **Purpose**: Direct forensic re-evaluation of Phase 007 cohort under mirror seating to measure exact mirror delta and mechanism attribution.

### 3.3 Strict Holdout Protection Covenant (Zero-Touch Invariant)
The runner script enforces hard exceptions if any of the following protected partitions are touched:
- **Primary Locked Holdout**: `340050–340199` (**STRICTLY FORBIDDEN / 0 RUNS**)
- **Gate 0.3 Final Holdout**: `214200–214249` (**STRICTLY FORBIDDEN / 0 RUNS**)
- **Prospective Tournament Cohort**: `340300–340349` (**STRICTLY FORBIDDEN / 0 RUNS**)
- **Live Competition**: Prospective matches = **0**.

---

## 4. Pre-Declared Hypotheses & Success Criteria

### Primary Hypotheses:
1. **Hypothesis 1 (Hard Safety Invariant)**:
   The Integrated ROBUST pipeline will produce **zero** safety certificate violations, zero inventory overflows, zero illegal worker moves, and zero working-capital insolvency events across all simulated game turns.
2. **Hypothesis 2 (Counterfactual Parity / Predictability)**:
   For every committed patch, the exact simulator's predicted terminal delta will match the realized simulation effect.
3. **Hypothesis 3 (Economic Superiority)**:
   Arm B (Integrated ROBUST) will demonstrate a statistically positive paired mean net margin delta ($\overline{\Delta}_{\text{net}} > 0$) relative to Frozen V3 Control under Common Random Numbers with mirror seating.

### Secondary Evaluation Metrics:
- Median net margin delta
- Standard deviation and standard error
- 95% Confidence Interval
- Win / Loss / Tie match distribution
- Overall win rate and tie-excluded win rate
- Paired two-tailed Student's $t$-test ($p$-value)
- Wilcoxon signed-rank test ($p$-value)
- Per-mechanism attribution: proposals, simulations, commits, abstentions, fallbacks
- Latency percentiles: $p_{50}, p_{95}, p_{99}$, and worst-turn latency

---

## 5. Non-Negotiable Experimental Governance Invariants

1. **V3 Hash Verification**: Immediate abort if SHA-256 of `submission_Vj_kc_v3.tar.gz` differs from `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
2. **Resource Conversion Quarantine**: Hard assert `not config.resource_conversion_enabled`.
3. **Fail-Closed Guarantee**: Any uncaught exception inside the compiler must immediately yield the unaltered baseline action without raising out-of-bounds errors.
4. **No Post-Hoc Tuning**: Under no circumstances will thresholds, weights, or code be modified after observing Phase 008 replay outcomes. If an arm underperforms, the result will be reported faithfully as empirical truth.
