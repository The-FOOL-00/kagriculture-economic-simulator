# EXP-AEC-004 Final Preregistration Protocol: Isolated Prospective Validation of Emergency Feed Purchase

**Protocol Identifier:** `PREREG-EXP-AEC-004-20260918-FINAL`  
**Date Established:** 2026-09-18  
**Governance Standard:** Absolute Scientific Governance, Prospective Double-Blind Mirror Common Random Numbers (CRN) Protocol  
**Execution Status:** **FROZEN PROTOCOL — EXECUTION STRICTLY HALTED**  
**Authoritative Directive:** **DO NOT EXECUTE IN THIS TASK.** This protocol is frozen for audit and system review. No prospective seed may be executed, simulated, or scouted without separate explicit formal user authorization.

---

## 1. Executive Summary & Experimental Objective

### 1.1 Context and Scientific Lineage
Following the prospective certification of **EXP-AEC-003** (where `DEPENDENCY_AWARE_MARKET_TIMING` achieved statistically significant economic superiority: $\overline{\Delta} = +\$57.36$, lower 95% bound $= +\$23.17$, win-rate delta $= +56.00\text{ pp}$ against Frozen V3), the next phase of the Autonomous Economic Coordinator (AEC) architecture focuses on resource and animal welfare mechanisms.

In Phase 002A–002C:
1. `RESOURCE_CONVERSION` was architecturally completed with physical action synthesis, but exhibited severe labor cannibalization destroying $-\$13,848.92$ mean margin without multi-worker logistics coordination. It was formally classified as **`ARCHITECTURALLY FIXED BUT NOT READY`** and placed under strict quarantine pending **Phase 003 Multi-Worker Logistics**.
2. `EMERGENCY_FEED_PURCHASE` underwent deterministic micro-validation and terminal remediation (Phase 002C). Arbitrary thresholds (the static $\$150.00$ liquidity buffer and the $-\$50.00$ margin degradation gate) were excised and replaced by an exact, deterministic, engine-derived **Terminal Obligation Model** and **Feed Terminal Causal Analyzer**.
3. Re-validation across development seeds `50000–50024` demonstrated clean safety, elimination of terminal-blind commits, and positive economic protection ($\overline{\text{Margin}} = +\$87.16$ vs Control $+\$86.92$). The mechanism was classified as **`MICRO_VALIDATED`** and placed under strict quarantine awaiting prospective trial preregistration.

### 1.2 Primary Experimental Question
The preregistered primary experimental question is:

> *"Does enabling `EMERGENCY_FEED_PURCHASE`, while holding the rest of the AEC configuration fixed, preserve non-inferior terminal economic performance relative to the frozen-control lineage while maintaining zero safety violations and correct mechanism isolation?"*

This is strictly a **mechanism validation experiment**. It is:
- **NOT** an AEC vs. V3 architecture experiment.
- **NOT** a top-$K$ tournament or leaderboard submission run.
- **NOT** an optimization run or hyperparameter search.
- **NOT** an evaluation of combined resource conversion.

---

## 2. Experimental Hypotheses & Statistical Estimators

### 2.1 Primary Null Hypothesis ($H_0$)
$$H_0: \mu_\Delta < \$0.00$$

### 2.2 Primary Alternative Hypothesis ($H_1$)
$$H_1: \mu_\Delta \ge \$0.00$$

where $\mu_\Delta$ is the population mean paired terminal-margin delta between the Treatment agent (`EMERGENCY_FEED_PURCHASE` active on validated AEC backbone) and the Control agent (validated AEC backbone with `EMERGENCY_FEED_PURCHASE` quarantined).

### 2.3 Paired Margin Delta Estimator
For each seed $s \in \{340300, \dots, 340349\}$, two mirror matches are executed:
- **Match A:** Treatment = Player 0, Control = Player 1
- **Match B:** Treatment = Player 1, Control = Player 0

The seed-paired delta $\Delta_s$ is unbiasedly estimated as:
$$\Delta_s = \frac{1}{2} \left[ \left(\text{Margin}_{\text{treat, Seat 0}}(s) - \text{Margin}_{\text{ctrl, Seat 1}}(s)\right) + \left(\text{Margin}_{\text{treat, Seat 1}}(s) - \text{Margin}_{\text{ctrl, Seat 0}}(s)\right) \right]$$

The cohort mean paired delta is:
$$\overline{\Delta} = \frac{1}{N} \sum_{s=1}^N \Delta_s \quad (N = 50)$$

### 2.4 Primary Statistical Test
- **Test:** One-sided paired Student's $t$-test on $\Delta_s$.
- **Significance Level ($\alpha$):** $0.05$
- **Degrees of Freedom ($df$):** $N - 1 = 49$ ($N = 50$ paired seeds, $M = 100$ mirror CRN matches).
- **Decision Criterion:** One-sided lower 95% confidence bound for $\mu_\Delta$:
  $$\text{Lower 95\% Bound} = \overline{\Delta} - t_{0.05, 49} \times \frac{s_\Delta}{\sqrt{50}} \ge \$0.00 \quad (t_{0.05, 49} \approx 1.6766)$$

### 2.5 Secondary Endpoints & Estimators
1. **Win-Rate Delta:**
   $$\Delta \text{WinRate} = \frac{W_{\text{treat}} - W_{\text{ctrl}}}{M} \times 100\text{ percentage points} \quad (M = 100)$$
   - Safeguard standard: $\Delta \text{WinRate} \ge -2.0\text{ pp}$.
2. **Ties-Excluded Win-Rate:**
   $$\Delta \text{WinRate}_{\text{excl}} = \frac{W_{\text{treat}} - W_{\text{ctrl}}}{W_{\text{treat}} + W_{\text{ctrl}}} \times 100\text{ percentage points} \quad (\text{if } W_{\text{treat}} + W_{\text{ctrl}} > 0)$$
3. **Non-Parametric Wilcoxon Signed-Rank Test:** Paired test on non-zero $\Delta_s$.
4. **Distributional Quantiles:** Median delta, Interquartile Range (IQR), 5th percentile ($p_{05}$), 95th percentile ($p_{95}$).
5. **Intention-to-Treat (ITT) Invariance:** The primary statistical analysis includes all $N = 50$ paired seeds regardless of whether `EMERGENCY_FEED_PURCHASE` triggered or abstained. Conditioning on mechanism triggers is strictly secondary/descriptive.

---

## 3. Seed Partition Architecture & Holdout Quarantine Covenant

### 3.1 Partition Map
```
[340000 -- 340049] [340050 ----------- 340199] [340200 -- 340249] [340250 -- 340299] [340300 ----------- 340349]
   EXP-AEC-001          AEC LOCKED HOLDOUT         EXP-AEC-002        EXP-AEC-003          EXP-AEC-004 (PROPOSED)
    (CONSUMED)          (STRICTLY TOUCHLESS)        (CONSUMED)         (CONSUMED)             (VIRGIN COHORT)
```

### 3.2 Partition Ledger
| Partition ID | Seed Range | Size ($N$) | Lifecycle Status | Governance Covenant |
| :--- | :---: | :---: | :---: | :--- |
| `HISTORICAL-AEC-001` | `340000–340049` | 50 | **CONSUMED** | Historical archive. Zero modification. |
| `LOCKED-HOLDOUT-AEC` | `340050–340199` | 150 | **LOCKED HOLDOUT** | **Touchless.** Strictly quarantined. Zero access, zero simulation. |
| `GATE-0.3-HOLDOUT`   | `214200–214249` | 50 | **LOCKED HOLDOUT** | **Touchless.** Strictly quarantined secondary holdout. |
| `HISTORICAL-AEC-002` | `340200–340249` | 50 | **CONSUMED** | Historical archive. Frontload falsification evidence. |
| `HISTORICAL-AEC-003` | `340250–340299` | 50 | **CONSUMED** | Historical archive. Dependency market timing certification. |
| **`PROSPECTIVE-AEC-004`** | **`340300–340349`** | **50** | **PROPOSED PROSPECTIVE** | Predeclared virgin cohort. Completely unexecuted and uninspected. |

### 3.3 Cohort Selection Rule
The cohort selection rule is defined deterministically prior to observing any treatment outcomes:
> *"Select the first $N = 50$ eligible contiguous seeds from the predeclared prospective validation continuum immediately following the most recently consumed prospective cohort (`340250–340299`), satisfying deterministic availability, zero historical contamination, and complete disjointness from all locked holdout partitions."*

- Next available block: `340300` to `340349` inclusive ($N = 50$).
- Distance to Primary Locked Holdout (`340050–340199`): $340300 - 340199 = 101\text{ seeds}$ of safety separation.
- Distance to Secondary Locked Holdout (`214200–214249`): $> 126,000\text{ seeds}$ of separation.
- Prior repository occurrences: **0 hits** across git history, commit diffs, and tracked workspace files.

---

## 4. Control and Treatment Specifications

### 4.1 Control Agent Specification (`CONTROL`)
- **Backbone:** Frozen V3 chassis (`submission_Vj_kc_v3.tar.gz`, SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
- **AEC Wrapper:** Active `AECExecutor` operating in `frozen_mode: True`.
- **Enabled Foundation Mechanisms:**
  1. `DEPENDENCY_AWARE_MARKET_TIMING` (Validated in EXP-AEC-003)
  2. `TERMINAL_LIQUIDATION` (Defense-in-depth, step 718)
  3. `PHASE_SHUTDOWN` (Defense-in-depth, dead seed capital filter)
- **Quarantined Mechanisms (100% Inactive / Return `ABSTAIN`):**
  - `EMERGENCY_FEED_PURCHASE` (Quarantined in Control)
  - `RESOURCE_CONVERSION` (Quarantined)
  - `FRONTLOAD_ORDERS` (Permanently retired / falsified)
  - `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`, `TERMINAL_HARVEST_SWEEP`, `TOWN_CYCLE`

### 4.2 Treatment Agent Specification (`TREATMENT`)
- **Backbone:** Identical Frozen V3 chassis.
- **AEC Wrapper:** Identical `AECExecutor` operating in `frozen_mode: True`.
- **Enabled Mechanisms:**
  1. `DEPENDENCY_AWARE_MARKET_TIMING`
  2. `TERMINAL_LIQUIDATION`
  3. `PHASE_SHUTDOWN`
  4. **`EMERGENCY_FEED_PURCHASE`** (Target mechanism under test)
- **Quarantined Mechanisms (100% Inactive / Return `ABSTAIN`):**
  - `RESOURCE_CONVERSION` (Strictly quarantined awaiting Phase 003)
  - `FRONTLOAD_ORDERS` (Permanently retired / falsified)
  - `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`, `TERMINAL_HARVEST_SWEEP`, `TOWN_CYCLE`

### 4.3 Mechanism Isolation Matrix
| Mechanism | Category | Role | Control Arm | Treatment Arm | Difference |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`EMERGENCY_FEED_PURCHASE`** | RESOURCE | EXPERIMENTAL TARGET | **QUARANTINED** | **ENABLED** | **+1 TARGET MECHANISM** |
| `DEPENDENCY_AWARE_MARKET_TIMING` | MARKET | VALIDATED FOUNDATION | ENABLED | ENABLED | Identical (0 Diff) |
| `TERMINAL_LIQUIDATION` | TERMINAL | DEFENSE IN DEPTH | ENABLED | ENABLED | Identical (0 Diff) |
| `PHASE_SHUTDOWN` | TERMINAL | DEFENSE IN DEPTH | ENABLED | ENABLED | Identical (0 Diff) |
| `RESOURCE_CONVERSION` | RESOURCE | QUARANTINED (PHASE 003) | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `FRONTLOAD_ORDERS` | MARKET | RETIRED / FALSIFIED | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `LOCAL_WEED_DIG` | ROUTE | QUARANTINED | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `DYNAMIC_SHADOW_HARVEST` | HARVEST | QUARANTINED | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `CARGO_FERRY_PRIORITY` | LOGISTICS | QUARANTINED | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `OPPONENT_PREEMPT_SELL` | MARKET | QUARANTINED | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `TERMINAL_HARVEST_SWEEP` | HARVEST | QUARANTINED | QUARANTINED | QUARANTINED | Identical (0 Diff) |
| `TOWN_CYCLE` | MARKET | QUARANTINED | QUARANTINED | QUARANTINED | Identical (0 Diff) |

**Conclusion:** Exactly one mechanism differs between Control and Treatment. Zero co-treatments exist.

---

## 5. Causal Mechanism & Safety Derivation

### 5.1 Authoritative Engine Mechanics (`sim.hpp`)
`EMERGENCY_FEED_PURCHASE` operates strictly under the immutable rules of Kagriculture:
- **Episode Duration:** 720 steps (Steps 0 to 719).
- **Final Action Step:** Step 718 (Step 719 observations reflect final rewards).
- **Day 29 Truncation:** Day 29 ends at step 719, but `end_of_day()` does **not** execute on the final day. Feed consumed on Day 29 does not yield livestock products or prevent escapes beyond the episode.
- **Scoring Invariant:** Strict cash scoring ($Cash - Penalty$). Inventory and live animals hold zero salvage scrap value at step 719.

### 5.2 Terminal Obligation Architecture
In Phase 002C, all ungrounded economic heuristics were excised:
1. The static `$150.00` liquidity buffer was replaced with dynamic schedule $R(t) = \sum \text{cost}(\text{MandatoryBaselineActions}(t'))$.
2. The arbitrary `-$50.00` margin degradation gate was replaced with formal obligation feasibility.
3. `FeedTerminalCausalAnalyzer` verifies causal paths: a feed purchase is authorized if and only if:
   - It prevents animal starvation / escape before step 718; OR
   - The fed animal produces yield that can be collected, transported to shed, and sold at market on or before step 718.
4. If neither causal path exists (e.g. late Day 29 feed purchases), the opportunity is classified as `TERMINAL_NO_REALIZABLE_PURPOSE` and safely abstains.

---

## 6. Pre-Specified Decision & Acceptance Criteria

### 6.1 Hard Acceptance Gates (All 8 Must Pass)
1. **`GATE_1_ZERO_SAFETY_VIOLATIONS`:** Exactly 0 safety certificate failures, 0 disqualifications, 0 illegal engine moves, 0 negative cash balances, and 0 livestock escapes caused by candidate actions.
2. **`GATE_2_ZERO_SHED_OVERFLOW`:** Maximum shed inventory across all turns must not exceed 100 units. Exactly 0 shed overflows and 0 discards.
3. **`GATE_3_ZERO_ISOLATION_VIOLATIONS`:** 100% of committed patches in Treatment must belong to `EMERGENCY_FEED_PURCHASE` (or active foundation). Exactly 0 feed commits in Control. Exactly 0 commits of `RESOURCE_CONVERSION` or other quarantined families.
4. **`GATE_4_ZERO_HOLDOUT_TOUCHES`:** Exactly 0 touches, executions, or inspections on Primary Holdout (`340050–340199`) and Secondary Holdout (`214200–214249`).
5. **`GATE_5_EXACT_V3_CHASSIS_INTEGRITY`:** Runtime SHA-256 hash of `submission_Vj_kc_v3.tar.gz` must equal `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
6. **`GATE_6_COUNTERFACTUAL_FIDELITY`:** 100% of committed patches must have `counterfactual_fidelity == VERIFIED`. Candidates with `FAILED` or `UNKNOWN` must fail closed.
7. **`GATE_7_ECONOMIC_NON_INFERIORITY`:** The one-sided lower 95% Student's $t$ confidence bound for paired margin delta must satisfy:
   $$\text{Lower 95\% Bound for } \mu_\Delta \ge \$0.00$$
8. **`GATE_8_WIN_RATE_PRESERVATION`:** Tournament win-rate delta across all $M = 100$ matches must satisfy:
   $$\Delta \text{WinRate} \ge -2.0\text{ percentage points}$$

### 6.2 Falsification Conditions (Any Triggers Rejection / Quarantine Retention)
1. `FALS_1`: Any safety violation, illegal move, shed overflow, or exception.
2. `FALS_2`: Any commit of `RESOURCE_CONVERSION` or other quarantined mechanisms.
3. `FALS_3`: Any execution of seeds within locked holdout partitions.
4. `FALS_4`: One-sided lower 95% confidence bound for $\mu_\Delta < \$0.00$.
5. `FALS_5`: Win-rate delta $\Delta \text{WinRate} < -2.0\text{ percentage points}$.
6. `FALS_6`: Degradation in 5th percentile margin delta below $-\$250.00$.

### 6.3 Classification Decision Matrix
| Classification | Conditions | Scientific Interpretation | Action |
| :--- | :--- | :--- | :--- |
| **`ACTIVE_POSITIVE`** | All 8 gates pass, $\overline{\Delta} > \$0.00$, commits $\ge 5$. | Statistically certified economic superiority; safe for deployment consideration. | Eligible for controlled live staging. |
| **`ACTIVE_NON_INFERIOR`**| All 8 gates pass, $\overline{\Delta} \ge \$0.00$, commits $\ge 5$. | Statistically non-inferior; provides downside protection without economic penalty. | Eligible for controlled live staging. |
| **`ACTIVE_NEGATIVE`** | Any `FALS_*` triggers, commits $\ge 5$. | Mechanism degrades baseline economics; candidate falsified. | Retain in quarantine; flag for redesign. |
| **`DORMANT_INCONCLUSIVE`**| All safety checks pass, but commits $< 5$. | Insufficient activation events in cohort to establish causal efficacy. | Retain in quarantine; report dormant status. |
| **`INVALID`** | Safety violations, unquarantined commits, or holdout breach. | Execution integrity breached; entire trial voided. | Immediate investigation; discard data. |

---

## 7. Match Execution Design & CRN Architecture

- **Total Seeds:** $N = 50$ contiguous seeds (`340300–340349`).
- **Total Matches:** $M = 50 \times 2 = 100$ matches.
- **Total Treatment Turns:** $100 \times 719 = 71,900$ turns.
- **Common Random Numbers (CRN):** Both Match A and Match B for each seed share identical world layout, shop opening pairs, crop and animal RNG sequences, and initial conditions.
- **Mirror Pairing:**
  - `Match_A`: Seat 0 = Treatment (`EMERGENCY_FEED_PURCHASE` active), Seat 1 = Control (AEC baseline).
  - `Match_B`: Seat 0 = Control (AEC baseline), Seat 1 = Treatment (`EMERGENCY_FEED_PURCHASE` active).
- **Sequential Execution:** Matches are executed strictly sequentially in a single process to eliminate Windows process-pool recycling hazards and race conditions.

---

## 8. Stopping Rules & Crash Recovery

1. **Deterministic Sequential Progress:** Match results and telemetry events are flushed atomically to disk per seed.
2. **Fail-Closed Stopping Invariants:** The runner halts execution immediately with an unhandled exception if:
   - Any seed in a protected range is supplied.
   - Any unquarantined mechanism commits.
   - Any shed overflow ($> 100$ units) occurs.
   - Any runtime exception or unhandled move occurs in either agent.
   - V3 chassis hash mismatch is detected.
   - Turn latency exceeds $1,000.0\text{ ms}$.
3. **No Dynamic Resumption Under Changed Code:** If the runner halts due to a software defect, the entire prospective cohort must be audited. Completed matches must never be combined with matches run under a modified code commit.

---

## 9. Immutable Freeze Verification Hashes

| Artifact Entity | Path | SHA-256 Digest |
| :--- | :--- | :--- |
| **Control Backbone Tarball** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| **AEC Configuration** | `aec/config.py` | `8989283ca8f528d38b74203cf0e8239c242ae0bf6f0d9ee779e59b91141131f6` |
| **EXP-004 Control Config** | `experiments/EXP-AEC-004/CONFIG_CONTROL.json` | `858b59ad0ab02ca6ae3d3e506fb1c517f29fe8c3088f4315c2e741e95231ed74` |
| **EXP-004 Treatment Config** | `experiments/EXP-AEC-004/CONFIG_TREATMENT.json` | `56256ef2d1befea4461e2d1f55ce72e0642958ade8313e1e344418856b801fe3` |
| **EXP-004 Manifest** | `experiments/EXP-AEC-004/EXECUTION_MANIFEST.json` | `74d11d5f2f68399d6e8b59b6a82cdf76c2f6a29333fa04c798089a8b6bf64cd5` |
| **EXP-004 Runner** | `experiments/EXP-AEC-004/run_experiment.py` | `0b1c528a96c6fbe67df922d638a244e8f149887b3ade4ce05a08e0c63359696e` |
| **EXP-004 Cohort Audit** | `reports/EXP_AEC_004_COHORT_AUDIT.md` | `7d596c1dce034b2d8495b0aaee9ecf81ae33110210fa25dc642672562ef42c55` |
| **EXP-004 Prelaunch Audit**| `reports/EXP_AEC_004_PRELAUNCH_AUDIT.md` | `a58885660d6f7ad3f1b1cb32f320847f62634daf65f990ead1481a7cee73bc32` |

---

## 10. Execution Governance Directive

**EXECUTION IS STRICTLY HALTED.**  
This document represents the formal prelaunch preregistration. No prospective matches (`340300–340349`) may be executed in this task.
Prospective execution must be triggered only under a separate, independently authorized task after complete preflight verification and peer review.
