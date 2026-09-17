# EXP-AEC-002 Preregistration: Final Prospective Evaluation Protocol

**Protocol Identifier:** `PREREG-EXP-AEC-002-20260917-FINAL`  
**Date Established:** 2026-09-17  
**Governance Authority:** Scientific Governance & Implementation Agent  
**Execution Status:** **FROZEN_NOT_LAUNCHED**  
**Authoritative Directive:** **STRICT EXECUTION HALT.** No prospective seed may be executed, simulated, or scouted without explicit formal user authorization.

---

## 1. Parent Studies & Contextual Continuity

This preregistration establishes the authoritative prospective evaluation protocol for **AEC V1.1** against the frozen **V3 Control** baseline. It directly succeeds and isolates from the following studies:

1. **`EXP-AEC-001` (Historical / Consumed):**
   - Cohort: Seeds `340000–340049` ($N=50$, 100 matches).
   - Finding: Valid baseline non-inferiority demonstrated; treatment remained completely dormant due to conservative trigger calibration and mechanism isolation.
   - Status: **Historical artifact. Permanently consumed and immutable.**
2. **`AEC V1.1 Final Readiness Audit` (`reports/AEC_V1_1_FINAL_READINESS_AUDIT.md`):**
   - Verdict: Conditionally ready, requiring market lockstep parity repair and quarantine enforcement prior to cohort freeze.
3. **`AEC V1.1 Final Development Fix Verification` (`reports/AEC_V1_1_DEVELOPMENT_FIX_RESULTS.md`):**
   - Ground-truth lockstep parity confirmed on FRONTLOAD fixture: $\Delta M_{\text{our}} = +\$31$, $\Delta M_{\text{opp}} = -\$30$, $\Delta \text{Margin} = +\$61$.
   - 110/110 regression and unit tests passing.
   - `LOCAL_WEED_DIG` scientifically quarantined.

---

## 2. Partition Allocations & Cohort Governance

The experimental partitions are strictly partitioned and immutable:

```
[340000 ----------------- 340049] [340050 ----------------- 340199] [340200 ----------------- 340249]
  EXP-AEC-001 (HISTORICAL)            AEC LOCKED HOLDOUT (150 SEEDS)      EXP-AEC-002 (PROSPECTIVE)
     PERMANENTLY CONSUMED                  STRICTLY TOUCHLESS                  VIRGIN & REGISTERED
```

### 2.1 Partition Table

| Partition Identifier | Seed Range | Size ($N$) | Governance Status | Permitted Operations |
|---|---|---|---|---|
| **`HISTORICAL-AEC-001`** | `340000–340049` | 50 seeds | **CONSUMED / RETIRED** | Historical read-only auditing. Never reuse for prospective treatment. |
| **`LOCKED-HOLDOUT-AEC`** | `340050–340199` | 150 seeds | **LOCKED HOLDOUT** | **Touchless.** Strictly quarantined. Zero simulation, zero inspection, zero tuning. |
| **`PROSPECTIVE-AEC-002`** | `340200–340249` | 50 seeds | **FROZEN PROSPECTIVE** | Prospective confirmatory CRN evaluation under this protocol only. |

### 2.2 Cohort Provenance and Virginity Evidence
In accordance with `reports/EXP_AEC_002_COHORT_AUDIT.md`:
- Exhaustive regex search across all workspace files confirmed **zero occurrences** of seeds `340200–340249`.
- Git log pickaxe search confirmed **zero historical mentions** in repository commit history.
- The cohort does not overlap the holdout partition ($\min(\text{Cohort}) = 340200 > 340199 = \max(\text{Holdout})$).
- The cohort was selected strictly via pre-committed contiguous policy (first 50 available seeds following the holdout upper bound), completely blind to seed characteristics, topology, or outcomes.

---

## 3. Frozen Baseline Control Specification

- **Control Agent:** Frozen Teammate V3 macro policy.
- **Source Archive:** `submission_Vj_kc_v3.tar.gz` (workspace root).
- **Immutable Cryptographic SHA-256:**  
  `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
- **Execution Mode:** Direct, unmodified baseline agent execution via internal simulation runner. Zero AEC wrappers, interceptors, or modifications.
- **Archive Validation Invariant:** The runner must re-verify the SHA-256 hash of `submission_Vj_kc_v3.tar.gz` immediately before launching any match. Any hash mismatch aborts execution immediately.

---

## 4. Treatment Specification & Mechanism Governance

### 4.1 Treatment Definition
The treatment agent consists of the frozen Teammate V3 macro policy wrapped by `AECExecutor` (`aec/integration/executor.py`), adhering to:
1. **Exactly One Baseline Call Invariant:** Every treatment decision invokes the live frozen V3 macro planner exactly once.
2. **Fail-Closed Boundary:** Any exception in opportunity detection, candidate generation, counterfactual simulation, or safety verification immediately yields the unaltered baseline action.
3. **Multi-Step Continuation Semantics:** Counterfactual simulations propagate future turns using the read-only backbone route tape without secondary live agent invocations.

### 4.2 Authoritative Mechanism Statuses

```python
ENABLED_FOUNDATION_MECHANISMS = (
    "FRONTLOAD_ORDERS",
    "TERMINAL_LIQUIDATION",
    "PHASE_SHUTDOWN",
)

QUARANTINED_MECHANISMS = (
    "LOCAL_WEED_DIG",
    "DYNAMIC_SHADOW_HARVEST",
    "CARGO_FERRY_PRIORITY",
    "OPPONENT_PREEMPT_SELL",
    "EMERGENCY_FEED_PURCHASE",
    "TERMINAL_HARVEST_SWEEP",
    "TOWN_CYCLE",
)
```

| Mechanism Family | Category | Scientific Status | Protocol Role | Prospective Invariant |
|---|---|---|---|---|
| **`FRONTLOAD_ORDERS`** | Market | `VERIFIED_SOURCE` | **ACTIVE TREATMENT** | Opportunistic reordering of `SELL` ahead of capital orders. Certified only under exact two-phase lockstep engine resolution. |
| **`TERMINAL_LIQUIDATION`** | Terminal | `VERIFIED_SOURCE` | **DEFENSE-IN-DEPTH** | Step 718 fail-closed liquidation. Expected commits: near-zero (redundant with V3 baseline). |
| **`PHASE_SHUTDOWN`** | Terminal | `VERIFIED_SOURCE` | **DEFENSE-IN-DEPTH** | Late-game dead capital prevention. Expected commits: near-zero (redundant with V3 baseline). |
| **`LOCAL_WEED_DIG`** | Route | `QUARANTINED` | **SCIENTIFIC QUARANTINE** | **Commits = 0.** Evaluator emits `ABSTAIN` (`abstain_reason="SCIENTIFIC_QUARANTINE"`). Baseline action returned. |
| **`DYNAMIC_SHADOW_HARVEST`** | Route | `PLAUSIBLE_UNPROVEN` | **QUARANTINED** | Blocked at generator / allowlist gate. Zero commits. |
| **`CARGO_FERRY_PRIORITY`** | Logistics | `PLAUSIBLE_UNPROVEN` | **QUARANTINED** | Blocked at generator / allowlist gate. Zero commits. |
| **`OPPONENT_PREEMPT_SELL`** | Market | `PLAUSIBLE_UNPROVEN` | **QUARANTINED** | Blocked at generator / allowlist gate. Zero commits. |
| **`EMERGENCY_FEED_PURCHASE`** | Animal | `VERIFIED_SOURCE` | **QUARANTINED** | Blocked at generator / allowlist gate. Zero commits. |
| **`TERMINAL_HARVEST_SWEEP`** | Terminal | `REUSED_SAFETY` | **QUARANTINED** | Blocked at generator / allowlist gate. Zero commits. |
| **`TOWN_CYCLE`** | Macro | `PLAUSIBLE_UNPROVEN` | **QUARANTINED** | Blocked at generator / allowlist gate. Zero commits. |

---

## 5. Causal Modeling & Scientific Role Declarations

### 5.1 Opponent Pressure Model — Conservative Characterization
- **Non-Overclaiming Rule:** The opponent pressure model is **not** claimed as an empirically validated behavioral forecast of opponent psychology or intent.
- **Scientific Role:** Observed or forecast mature rival crops simply serve as an **opportunity trigger** signaling potential market collision.
- **Causal Decider:** The counterfactual two-phase lockstep simulator alone determines whether an actual price priority advantage exists. If rival orders do not collide or market clearing prices are identical, the simulator certifies zero marginal advantage ($\Delta M = \$0$) and AEC strictly abstains.

### 5.2 `FRONTLOAD_ORDERS` Causal Role
- **Baseline Transformation:** In the baseline V3 action, market `SELL` orders may occur after capital orders (e.g. tile purchase or building construction) within the turn's submission list.
- **Candidate Patch:** Moves `SELL` orders ahead of capital orders to secure liquidity and clearing priority.
- **Commitment Threshold:** The candidate patch is accepted if and only if:
  1. It is structurally legal and passes safety certification.
  2. The counterfactual two-phase market simulation yields a non-negative economic benefit ($\Delta M_{\text{our}} \ge 0$).
  3. The action sequence physically differs from the baseline.

### 5.3 Defense-in-Depth Mechanisms
- `TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` serve solely as safety nets. Their presence is defensive and does not represent an active performance driver. Their activation frequency is expected to be near zero.

---

## 6. Primary Experimental Design

### 6.1 Common Random Numbers (CRN) Paired-Seat Design
- **Cohort Size:** $N = 50$ game seeds (`340200` to `340249` inclusive).
- **Matches per Seed:** Exactly 2 matches per seed with reversed seat assignments.
- **Total Matches:** $M = 50 \times 2 = 100$ completed tournament games.
- **Match Structure for Seed $s$:**
  - **Match A:** Treatment (AEC V1.1) in Seat 0 vs Control (Frozen V3) in Seat 1.
  - **Match B:** Control (Frozen V3) in Seat 0 vs Treatment (AEC V1.1) in Seat 1.
- **Seat-Averaged Paired Margin Delta:**
  $$\Delta_s = \frac{1}{2} \left[ \left(\text{Margin}_{\text{treat, Seat 0}} - \text{Margin}_{\text{ctrl, Seat 1}}\right) + \left(\text{Margin}_{\text{treat, Seat 1}} - \text{Margin}_{\text{ctrl, Seat 0}}\right) \right]$$
- **Inferential Unit:** The seed-paired delta $\Delta_s$ is the primary inferential unit. Unpaired per-match deltas must not be used for primary statistical inference.

### 6.2 Agent Turn Accounting
- Each Kaggle game runs for 719 decision turns (steps 0 to 718 inclusive).
- Across $M = 100$ matches, the treatment agent executes exactly:
  $$\text{Total Treatment Turns} = 50 \times 2 \times 719 = 71,900 \text{ turns}$$

---

## 7. Primary Metric & Hypotheses

### 7.1 Primary Metric
- **Primary Estimand:** Mean Seed-Averaged Paired Terminal Margin Delta:
  $$\overline{\Delta} = \frac{1}{N} \sum_{s=1}^{N} \Delta_s$$
- **Descriptive Statistics Required:** Mean, median, standard deviation, standard error, 5th percentile, 95th percentile, minimum, and maximum.

### 7.2 Primary Non-Inferiority Formulation
Let $\delta = \$0.00$ be the non-inferiority margin. The primary hypotheses are directional:
$$\begin{aligned}
H_0 &: \mu_{\Delta} < 0 \\
H_1 &: \mu_{\Delta} \ge 0
\end{aligned}$$

- **Primary Statistical Test:** One-sided paired $t$-test ($\alpha = 0.05$).
- **Primary Acceptance Rule:** The lower bound of the two-sided 90% confidence interval (equivalent to the lower one-sided 95% confidence bound) must satisfy:
  $$\text{Lower 95\% CI}(\overline{\Delta}) \ge \$0.00$$
  in conjunction with the win-rate non-inferiority condition.

### 7.3 Win-Rate Non-Inferiority Specification
- **Win-Rate Delta:**
  $$\Delta \text{WinRate} = \text{WinRate}_{\text{treatment}} - \text{WinRate}_{\text{control}}$$
- **Non-Inferiority Boundary:** $\Delta \text{WinRate} \ge -2.0 \text{ percentage points}$.
- **Counting Definitions:**
  - $W_{\text{treat}} = \sum_{m=1}^{M} \mathbb{I}(\text{Margin}_{\text{treat}, m} > \text{Margin}_{\text{ctrl}, m})$
  - $W_{\text{ctrl}} = \sum_{m=1}^{M} \mathbb{I}(\text{Margin}_{\text{ctrl}, m} > \text{Margin}_{\text{treat}, m})$
  - $T = \sum_{m=1}^{M} \mathbb{I}(\text{Margin}_{\text{treat}, m} == \text{Margin}_{\text{ctrl}, m})$
  - **Primary Denominator Standard:** Total matches $M = 100$ (matching EXP-AEC-001 governance standard):
    $$\text{WinRate}_{\text{treat}} = \frac{W_{\text{treat}}}{M}, \quad \text{WinRate}_{\text{ctrl}} = \frac{W_{\text{ctrl}}}{M}, \quad \Delta \text{WinRate} = \frac{W_{\text{treat}} - W_{\text{ctrl}}}{M} \times 100\text{ pp}$$
  - **Secondary Robustness Standard:** Ties excluded from denominator:
    $$\Delta \text{WinRate}_{\text{excl}} = \left( \frac{W_{\text{treat}}}{W_{\text{treat}} + W_{\text{ctrl}}} - \frac{W_{\text{ctrl}}}{W_{\text{treat}} + W_{\text{ctrl}}} \right) \times 100\text{ pp} \quad (\text{if } W_{\text{treat}} + W_{\text{ctrl}} > 0)$$

---

## 8. Secondary Hypotheses & Invariants

### 8.1 Secondary Hypothesis H2: Quarantine Governance Invariant
Across all 71,900 treatment agent turns, zero commits are made by `LOCAL_WEED_DIG` or any quarantined family:
$$\text{Commits}(\text{LOCAL\_WEED\_DIG}) = 0$$
$$\sum_{m \in \text{QUARANTINED}} \text{Commits}(m) = 0$$
When `LOCAL_WEED_DIG` triggers, the evaluator must record `decision="ABSTAIN"`, `abstain_reason="SCIENTIFIC_QUARANTINE"`, and return the exact baseline action.

### 8.2 Secondary Hypothesis H3: Commitment Integrity Invariant
For every committed `FRONTLOAD_ORDERS` intervention:
1. Hard safety certificate is fully validated (legality, solvency, shed limits).
2. The candidate was simulated under exact two-phase lockstep market semantics.
3. Raw reconstructed cash difference is non-negative: $\Delta M_{\text{our}} \ge 0$.
4. Returned action strictly equals the certified candidate patch.
5. No quarantined mechanism participates in the decision.

*(Note: H3 is a deterministic protocol integrity invariant, not an empirical efficacy claim).*

---

## 9. Secondary Statistical & Robustness Analyses

The following analyses must be reported in full:
1. **One-Sided Paired $t$-test** (Primary inferential test).
2. **Two-Sided Wilcoxon Signed-Rank Test** (Secondary non-parametric robustness test).
3. **95% Student-$t$ Confidence Interval** for $\mu_{\Delta}$.
4. **95% BCa Bootstrap Confidence Interval** for $\mu_{\Delta}$ ($10,000$ resamples).
5. **Mean Net Cash Delta ($\Delta \text{Cash}$)** at step 718.
6. **Per-Mechanism Commitment & Abstain Counts.**
7. **Maximum Recorded Shed Inventory** across all games (capacity $= 100$).
8. **Latency Distribution:** Mean, median, 95th percentile, 99th percentile, and maximum per-turn latency.

---

## 10. Decision Framework

### 10.1 Acceptance Criteria (All Must Be Met)
- **`ACC_1` (Statistical Non-Inferiority):** $\text{Lower 95\% CI}(\overline{\Delta}) \ge \$0.00$.
- **`ACC_2` (Win-Rate Non-Inferiority):** $\Delta \text{WinRate} \ge -2.0\text{ pp}$.
- **`ACC_3` (Non-Negative Median Margin):** $\text{Median}(\Delta) \ge \$0.00$.
- **`ACC_4` (Bounded Downside Tail Risk):** 5th percentile $\Delta_s \ge -\$250.00$.
- **`ACC_5` (Zero Safety Regressions):**
  - 0 illegal moves.
  - 0 rule violations or disqualifications.
  - 0 shed overflow discards ($> 100$ units).
  - 0 unhandled exceptions.
- **`ACC_6` (Strict Quarantine Adherence):** Exactly 0 commits across all 7 quarantined mechanisms.
- **`ACC_7` (Two-Phase Commitment Parity):** 100% of committed FRONTLOAD interventions adhere to verified two-phase market semantics.

### 10.2 Falsification Criteria (Any Triggers Rejection)
- **`FALS_1`:** $\Delta \text{WinRate} < -2.0\text{ pp}$.
- **`FALS_2`:** $\text{Lower 95\% CI}(\overline{\Delta}) < \$0.00$.
- **`FALS_3`:** Any game rule violation or disqualified match.
- **`FALS_4`:** Any shed overflow causing item discard/deletion.
- **`FALS_5`:** Any single turn computation latency $\ge 1000\text{ ms}$.
- **`FALS_6`:** Any commitment of a quarantined mechanism.
- **`FALS_7`:** Any evidence that the frozen V3 control archive changed.
- **`FALS_8`:** Any evidence that holdout seeds (`340050–340199`) were accessed.
- **`FALS_9`:** Any evidence that the prospective cohort overlaps historical or development seeds.

---

## 11. Latency & Resource Invariants

- **Per-Step Target Latency:** $< 100\text{ ms}$.
- **Hard Fail-Closed Bound:** $\ge 1000\text{ ms}$ (triggers immediate match abortion under `FALS_5`).
- **No Post-Hoc Tuning:** Search budgets (`max_opportunities=16`, `max_candidates=8`, `max_simulations=8`) and horizon lengths (`short=6`, `normal=18`, `extended=36`) are permanently frozen.

---

## 12. Execution Integrity & Failure Recovery Policy

- **Atomic Writes:** All match results, seed deltas, and telemetry records must be written atomically.
- **Seed Checkpointing:** State is checkpointed to `CHECKPOINT.json` after both matches of seed $s$ complete.
- **Fail-Closed Governance:** If a system crash or infrastructure failure occurs:
  - The runner stops immediately.
  - Zero results may be silently overwritten or modified.
  - Resumption may occur only from the uncompleted seed, preserving all previously recorded seed outputs bit-by-bit.
- **No Silent Reruns:** Seeds that yield negative economic margins must never be excluded or rerun.

---

## 13. Cryptographic Artifact Manifest

| Artifact | File Path | Authoritative SHA-256 Hash |
|---|---|---|
| **Frozen V3 Control Archive** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| **AEC Configuration File** | `aec/config.py` | `240deda295ce68490bf68a1fb046be2905044e78fafafb2a51aeb8b5c2f71f63` |
| **Canonical `AECConfig` JSON** | Serialized dataclass payload | `db59108d29241534cde9d9a12bdc93c588800be7ad7ec2838cee09efdea5721c` |
| **Cohort Audit Document** | `reports/EXP_AEC_002_COHORT_AUDIT.md` | Recorded in `experiments/EXP-AEC-002/EXECUTION_MANIFEST.json` |

---

## 14. Final Prelaunch Status

```
===============================================================================
EXP-AEC-002 PREREGISTRATION PROTOCOL: FROZEN & SEALED
EXECUTION STATUS: FROZEN_NOT_LAUNCHED
PROSPECTIVE SEEDS EXECUTED: ZERO (0)
HOLDOUT ACCESS: ZERO (0)
===============================================================================
```

Prospective evaluation of EXP-AEC-002 is completely halted pending explicit user authorization.
