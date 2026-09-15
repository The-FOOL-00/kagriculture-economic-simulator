# EXP-ARCH-002 H1 — FINAL EXECUTION, INTEGRITY & FORENSIC REPORT

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`  
**Document**: `06_EXECUTION_AND_FORENSIC_REPORT.md`  
**Date**: 2026-09-15  
**Auditor / Principal Investigator**: Antigravity  
**Status**: **COMPLETED — RESULT CLASSIFIED: INVALID / EXECUTION-INTEGRITY FAILURE (RUNNER STATE POLLUTION) & MECHANISM-INACTIVE (0.00% EXPOSURE)**

---

## 1. ARCH-002 STATUS

The preregistered prospective execution of `EXP-ARCH-002_H1_DOMINANCE_TERMINAL` across the authorized 500-seed cohort has completed. Exactly 1,000 games (500 seeds × 2 seats in Common Random Numbers design) were executed and logged.

Following the mandatory post-execution integrity audit (§18, §22), the experimental results have been classified as:
1. **EXECUTION INTEGRITY**: **INVALID (FAIL)** due to runner-level baseline state pollution (§18 P-PURE violation).
2. **SCIENTIFIC MECHANISM**: **MECHANISM-INACTIVE / UNTESTABLE (Pattern C)** due to 0.00% exposure (0 / 1000 games activated).
3. **COMPETITIVE GATE**: **FAIL** (unmet materiality, negative mean, invalid data).
4. **DEPLOYMENT STATUS**: **REJECTED / DO NOT DEPLOY**.
5. **NEXT GOVERNANCE ACTION**: **HARD STOP**. Do NOT execute DEV-007.

---

## 2. FROZEN EXPERIMENT IDENTITY

- **Experiment Name**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`
- **Governing Preregistration**: [02_PREREGISTRATION.md](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/02_PREREGISTRATION.md) (SHA-256: `508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5`)
- **Isolation Audit Authority**: [01_ISOLATION_AUDIT.md](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/01_ISOLATION_AUDIT.md) (SHA-256: `0381a93eee7cc3d51833439ce868d51923dc9a2ff0cca68f9d692e5f81c03de4`)
- **Implementation Validation Report**: [03_IMPLEMENTATION_VALIDATION_REPORT.md](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/03_IMPLEMENTATION_VALIDATION_REPORT.md) (SHA-256: `c87e3959b0fda3b7620883c2d85dd200736d4d3305c33353c9c5123ab5c8a402`)
- **Implementation Freeze Record**: [04_FREEZE_RECORD.md](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/04_FREEZE_RECORD.md) (Commit: `862e35b75e375b49cd66e85c651fc4d463fd9b1e`)
- **Governance Seal Commit**: `2dfeedb015bf39db2bd57fc965e3b74f8316e0a7`

---

## 3. PRE-EXECUTION VERIFICATION

All pre-execution verification checks (G-HASH, G-IMPL, G-SIM, G-QUAR) were evaluated prior to execution:
- Baseline V54++ SHA-256 matched bit-identically: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`.
- Preregistration SHA-256 matched bit-identically: `508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5`.
- All 8 H1 source modules matched their freeze hashes 100%.
- All 10 H1 unit tests passed (163/163 assertions in 92.25s).
- Authoritative simulator port `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py` verified functional.

---

## 4. RUNNER IDENTITY & FREEZE COMMIT

- **Runner Script**: [run_arch002_h1_execution.py](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_execution.py)
- **Runner SHA-256**: `1599c4bb3153bb1f798a7e0e4f3cc0255f8eb304e913357fa83d850be1551fad`
- **Runner Validation Suite**: [test_h1_runner_validation.py](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/tests/test_h1_runner_validation.py)
- **Runner Freeze Record**: [05_RUNNER_FREEZE_RECORD.md](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/05_RUNNER_FREEZE_RECORD.md)
- **Runner Freeze Git Commit**: `89d981b285a8bfb8f170f78238ba4c95232b7194` (`feat(arch-002): freeze execution runner, validation tests, and runner freeze record`)

---

## 5. PROSPECTIVE COHORT SPECIFICATION

- **Preregistered Cohort**: `320000–320499` inclusive (N = 500 seeds)
- **Experimental Design**: Common Random Numbers (CRN), 2 games per seed:
  - Game a: Seat 0 = H1 treatment, Seat 1 = Baseline
  - Game b: Seat 0 = Baseline, Seat 1 = H1 treatment
- **Total Scheduled Games**: 1,000 games

---

## 6. TOTAL GAMES EXECUTED

- **Executed Seeds**: Exactly 500 seeds (Seeds 320000 to 320499)
- **Executed Games**: Exactly 1,000 games
- **Unexecuted / Omitted Seeds**: 0
- **Duplicate Seeds**: 0
- **Unauthorized Seeds**: 0
- **Raw Checkpoint Files**:
  - [RAW_RESULTS.json](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/RAW_RESULTS.json) (822,852 bytes)
  - [PAIRED_DELTAS.csv](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/PAIRED_DELTAS.csv) (42,097 bytes)
  - [TELEMETRY_EVENTS.csv](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/TELEMETRY_EVENTS.csv) (51,189 bytes)
  - [EXECUTION_MANIFEST.json](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/EXECUTION_MANIFEST.json)

---

## 7. EXECUTION INTEGRITY AUDIT (CRITICAL FAILURE FOUND)

| Check | Requirement | Result | Status |
|---|---|---|---|
| **Seed Range** | `320000 <= s <= 320499` | Min: 320000, Max: 320499 | **PASS** |
| **Seed Count** | Exactly 500 unique | 500 unique | **PASS** |
| **Game Count** | Exactly 1000 | 1000 | **PASS** |
| **DEV-007 Overlap** | Zero seeds in `310000–310499` | 0 seeds | **PASS** |
| **Final Holdout Overlap** | Zero seeds in `214200–214249` | 0 seeds | **PASS** |
| **P-PURE Pre-E Action Identity** | 100% bit-identity steps 0–711 | **975 / 1000 games FAILED (2.5% pass)** | **CRITICAL FAIL** |
| **P-PURE Verbatim Markets (712–717)** | 100% verbatim when activated | N/A (0 activated games) | **PASS** |
| **P-PURE Non-Activated Step Identity** | Delta == 0.00 when not activated | **558 / 1000 games FAILED (44.2% pass)** | **CRITICAL FAIL** |

### Root Cause of P-PURE Failure: Runner Baseline State Pollution
In [run_arch002_h1_execution.py](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_execution.py) lines 207–210:
```python
        # Check pre-E action identity (steps 0 to 711)
        if t < ENTRY_STEP:
            internal_base_act = base_inst_h1.call(copy.deepcopy(obs_h1), copy.deepcopy(cfg))
            if not _actions_equal(act_h1, internal_base_act):
                pure_pre_e_pass = False
```
1. `base_inst_h1` is the stateful baseline agent instance wrapped by `agent_h1`.
2. On each step `t`, `act_h1 = agent_h1(...)` called `base_inst_h1.call(...)`.
3. Immediately afterwards, the runner invoked `internal_base_act = base_inst_h1.call(...)` on the **same instance** with the same step observation.
4. Because `FrozenBaseline.call()` mutates internal order tracking ledgers (`m_update_flow`, `m_repay`, `m_release_pending` in `v54_plus_residual.py`), calling it a second time per step caused the internal market flow state to update twice.
5. On the subsequent turn, `base_inst_h1` executed from a corrupted internal ledger state compared to the unpolluted control baseline instance (`agent_base`).
6. As demonstrated forensically (e.g. at step 328 in seed 320000), `act_h1` scheduled a market sale while the double-called baseline returned an empty market order.
7. Consequently, the H1 seat diverged from the baseline control seat **before step 712**, producing non-zero deltas (ranging from -$1,465 to +$1,357) on games where H1 explicitly abstained.

---

## 8. BASELINE & H1 IDENTITIES

- **Baseline Identity**: `candidates/compiled_v54_plus_residual.py` (V54++ residual, Sub 56146971, SHA-256 `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`).
- **H1 Identity**: Dominance-gated terminal overlay (`h1_agent.py`, `h1_dominance.py`, `h1_search.py`, `h1_shadow.py`, `h1_units.py`, `h1_const.py`, `h1_telemetry.py`, `h1_baseline.py`).

---

## 9. MECHANISM EXPOSURE ENDPOINTS (§18)

- **Activated Games**: **0 / 1,000 (0.00%)**
- **Exposed Seeds ($k$)**: **0 / 500 (0.00%)**
- **Exact Clopper-Pearson 95% Confidence Interval**: `[0.00%, 0.74%]`

### Reason Code Histogram (All 1,000 Games)
| Reason Code | Games Count | Percentage | Description |
|---|---|---|---|
| `ABSTAIN_DOMINANCE` | 756 | 75.60% | Candidate proposal failed row-wise prefix dominance predicate (§8.1) |
| `ABSTAIN_ACCEPT` | 244 | 24.40% | Acceptance conjunction failed (`some_positive` on sold unit delta) |
| `OK_ACTIVATED` | **0** | **0.00%** | Plan adopted and emitted |

### Forensic Analysis of Mechanism Inactivity
1. **Dominance Vetoes (75.6%)**: In 756 games (primarily the `backbone` route), candidate reap-and-ferry proposals failed row-wise prefix dominance against the baseline's scheduled actions.
2. **Acceptance Conjunction Vetoes (24.4%)**: In 244 games (predominantly `yarn`), proposals were adopted during trial search, but failed `acceptance()` because `h1_dominance.py:155` requires:
   ```python
   conjuncts["some_positive"] = any(v > 0 for v in sold_delta.values())
   ```
   However, by preregistered design:
   - D3: Step-718 markets are verbatim baseline passthrough.
   - P5: Markets on 712–717 are verbatim baseline passthrough.
   - The baseline candidate never places unfulfillable sell orders.
   Therefore, the change in sold units between candidate and baseline was identically 0 (`sold_delta_min = 0`, `sold_delta_max = 0`) across all 244 candidates, causing `acceptance()` to reject 100% of candidate plans.

---

## 10. STATISTICAL PERFORMANCE SUMMARY (MEASURED COHORT)

> [!CAUTION]
> The performance metrics below reflect the measured outputs of the prospective cohort run, but are scientifically invalid as an estimate of H1 treatment effect due to the runner baseline state pollution documented in §7.

### Primary Estimand: Unconditional Paired Delta ($\Delta_i = 0.5(\delta_{i,a} + \delta_{i,b})$)
- **Mean Paired Delta ($\bar{\Delta}$)**: **-$32.8520**
- **Median Delta**: **+$0.0000**
- **Standard Deviation ($s$)**: $234.4661$
- **Standard Error ($SE$)**: $10.4856$
- **$t$-statistic ($df = 499$)**: **-$3.1330**
- **Two-sided $p$-value**: **$0.001832$ ($1.83 \times 10^{-3}$)**
- **95% Confidence Interval**: **[-$53.4535, -$12.2505]**
- **10% Trimmed Mean**: **-$19.2462**
- **Min / Max Delta**: **-$1,465.00 / +$1,357.00**
- **Wins / Losses / Ties**:
  - Wins ($\Delta_i > 0$): 64 (12.80%)
  - Losses ($\Delta_i < 0$): 209 (41.80%)
  - Ties ($\Delta_i == 0$): 227 (45.40%)
- **Non-zero Count**: 273 (54.60%)
- **Robustness Views**:
  - Mean ex-best: -$35.6373
  - Mean ex-top 2: -$38.1165

### Absolute Economy Scores (Mean ± SD Coins)
- **H1 Treatment Arm**: $86,802.82 \pm 24,933.78$
- **Baseline Control Arm**: $86,835.68 \pm 24,959.22$

### Percentiles (Linear Interpolation)
| Percentile | Value (Coins) |
|---|---|
| $p_{01}$ | -$1,168.12$ |
| $p_{05}$ | -$238.10$ |
| $p_{10}$ | -$155.20$ |
| $p_{25}$ | -$31.00$ |
| $p_{50}$ (Median) | $0.00$ |
| $p_{75}$ | $0.00$ |
| $p_{90}$ | +$9.10$ |
| $p_{95}$ | +$93.40$ |
| $p_{99}$ | +$801.23$ |

---

## 11. TAIL RISK & OUTLIER FORENSICS

- **Loss Rate**: $41.80\%$ (Threshold: $\le 5.00\%$) — **VIOLATED**
- **Minimum Delta**: -$1,465.00 (Threshold: $\ge -$800.00) — **VIOLATED**
- **Tail-Harm Bar**: **VIOLATED** (min < -$800.00)
- **Large Excursions ($|\Delta_i| \ge \$2,000$)**: 0 seeds

### Extreme Seed Tracing
All extreme gains and losses occurred on seeds where H1 **abstained** (`ABSTAIN_ACCEPT`, `yarn` route), proving conclusively that the extreme variance was entirely driven by pre-E state pollution:
- **Top Gain**: Seed 320129 (+1,357.00 coins) — H1 abstained in both seats (`ABSTAIN_ACCEPT`).
- **Top Loss**: Seed 320055 (-1,465.00 coins) — H1 abstained in both seats (`ABSTAIN_ACCEPT`).

---

## 12. ROUTE & MACRO PRESERVATION

- **Route Distribution**:
  - `backbone`: 756 games (75.60%)
  - `yarn`: 228 games (22.80%)
  - `bakery`: 16 games (1.60%)
- **Macro Route Identity**: Invariant (routes were identical between seats).
- **Macro Action Identity (Steps 0–711)**: Violated in 97.5% of games due to the runner's double-call defect.

---

## 13. PREREGISTERED DECISION RULE EVALUATION (§21)

### 1. Mechanism Pattern (§21.1)
- Criteria: $k = 0 \le 2$.
- Result: **Pattern C — Mechanism Untestable / Inactive** ("mechanism not activated in this cohort").

### 2. Overall Pattern (§21.2)
- Criteria: Two-sided $p = 0.0018 < 0.05$ with mean < 0, and min = -$1,465.00 < -$800.
- Result: **Pattern F — Overall Harmed** (driven by runner state pollution).

### 3. Combined Result Pair
- Form: **C + F**
- Scientific Significance: §21.2 notes: *"Pattern D + C [or movement without activation] is incoherent and triggers integrity investigation under P-PURE before any interpretation (§22)."* The investigation confirmed that Pattern F is an artifact of the runner defect, while the true H1 mechanism remained 100% inactive.

### 4. Scientific Success Gate
- Criteria: Mechanism Pattern A.
- Result: **FAIL**.

### 5. Competitive Success Gate
- Criteria: Pattern A AND mean $\ge +\$500$ AND CI lower $> \$0$ AND min $\ge -\$800$ AND loss rate $\le 5\%$.
- Result: **FAIL on all criteria**.

---

## 14. SCIENTIFIC VERDICT & CONCLUSIONS

1. **Mechanism Inactivity**: The frozen H1 implementation never intervened in any game across 500 seeds because its acceptance criteria required positive sold unit delta over the baseline, which is structurally incompatible with verbatim market passthrough (D3/P5) when the baseline does not queue unfulfillable orders.
2. **Runner Invalidation**: The runner contained a state pollution bug that double-stepped the baseline during steps 0–711, corrupting pre-E execution.
3. **Formal Verdict**: **EXPERIMENT INVALID / EXECUTION-INTEGRITY FAILURE**. The prospective data cannot license any scientific claim of H1 efficacy, and H1 is rejected for competitive promotion.

---

## 15. GOVERNANCE STATUS & REPOSITORY INTEGRITY

- **DEV-007 Status**: **NOT EXECUTED IN THIS PHASE**. Cohort `310000–310499` remains 100% virgin, untouched, and unexecuted.
- **Final Holdout Status**: **UNTOUCHED & PROTECTED**. Cohort `214200–214249` remains 100% virgin and unexecuted.
- **Kaggle Status**: Zero contact with Kaggle. No submissions made.
- **Repository State**: Clean. Zero tracked modifications to frozen baselines or earlier experiment records.
- **Hard Stop**: Enacted. No further experiments authorized in this session.
