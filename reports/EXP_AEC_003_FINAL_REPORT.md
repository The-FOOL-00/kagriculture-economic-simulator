# Scientific Experiment Report: EXP-AEC-003
## Prospective Evaluation of Dependency-Aware Market Timing Against Frozen V3 Backbone

- **Experiment ID:** EXP-AEC-003
- **Protocol:** `PREREG-EXP-AEC-003-20260917-FINAL`
- **Frozen Commit:** `0a5efe03fe610bca9083cffd64658d31bf3c5536`
- **Execution Date:** 2026-09-17
- **Evaluation Status:** COMPLETED
- **Audit Status:** VERIFIED & PASSED (18/18 Integrity Criteria)
- **Primary Verdict:** **ACCEPTED**
- **Result Classification:** **VALID + ACTIVE_POSITIVE**

---

## 1. Executive Summary

EXP-AEC-003 was conducted as a preregistered, fully frozen prospective evaluation of the **Dependency-Aware Market Timing** mechanism within the Autonomous Economic Coordinator (AEC) architecture against the frozen V3 baseline backbone (`submission_Vj_kc_v3.tar.gz`).

The primary scientific objective was to establish whether replacing the falsified unconditional frontloading mechanism (`FRONTLOAD_ORDERS` from EXP-AEC-002) with a causal DAG-based reordering engine (`DEPENDENCY_AWARE_MARKET_TIMING`) achieves statistical non-inferiority against the backbone under Common Random Numbers (CRN) mirror seat pairing.

The experiment was executed sequentially across the prospective virgin cohort (seeds 340250–340299, 50 seeds, 100 mirror CRN matches, 71,900 treatment turns) without any manual intervention, retuning, or mid-experiment modifications. The holdout partition (seeds 340050–340199) remained strictly untouched.

### Key Results Summary
- **Mean Paired Margin Delta ($\overline{\Delta}$):** **+$57.36** (Std: $144.22, SE: $20.40)
- **Median Paired Margin Delta:** **+$18.50**
- **One-Sided Lower 95% Student-$t$ Bound:** **+$23.17** (Requirement: $\ge \$0.00$; **PASSED**)
- **Win-Rate Delta:** **+56.00 percentage points** (75 Treatment Wins vs 19 Control Wins, 6 Ties; Requirement: $\ge -2.0\text{ pp}$; **PASSED**)
- **Ties-Excluded Win-Rate Delta:** **+59.57 percentage points** (79.79% vs 20.21%)
- **Primary One-Sided Paired $t$-Test:** $t = 2.8124, df = 49, p = 0.003527$ ($H_0$ rejected at $\alpha = 0.05$)
- **Two-Sided Wilcoxon Signed-Rank Test:** $W = 132.0, p = 1.348 \times 10^{-5}$
- **Committed Patches:** **140** (exceeds dormancy threshold of 5; active across 45/50 seeds)
- **Safety & Quarantine:** 0 safety violations, 0 shed overflows, 0 quarantined commits, 100% verified counterfactual fidelity
- **Holdout Partition:** 0 executions, 0 touches, 100% certified virgin

All 7 preregistered acceptance criteria (`ACC_1` through `ACC_7`) were fulfilled. Zero falsification conditions were triggered. The protocol is formally classified as **VALID + ACTIVE_POSITIVE**.

---

## 2. Frozen Configuration

The experiment ran strictly under the audited and frozen configuration certified at commit `0a5efe03fe610bca9083cffd64658d31bf3c5536`.

### Cryptographic Artifact Hash Ledger
| Artifact | Path | Expected SHA-256 | Verified Runtime SHA-256 | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Control Backbone** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | MATCH |
| **AEC Configuration** | `aec/config.py` | `a92bb57785535d0c5b51895d5242fbf5a33f4a09c89b8160e8424bf245d63d55` | `a92bb57785535d0c5b51895d5242fbf5a33f4a09c89b8160e8424bf245d63d55` | MATCH |
| **Preregistration** | `reports/EXP_AEC_003_PREREGISTRATION_FINAL.md` | `5c738e4a2d339dae4fecae0f32997e06a3861845bb02e822a1ce09eb11c0f757` | `5c738e4a2d339dae4fecae0f32997e06a3861845bb02e822a1ce09eb11c0f757` | MATCH |
| **Cohort Audit** | `reports/EXP_AEC_003_COHORT_AUDIT.md` | `a4959db6b31c92bbdcfdaefdd25cf8c4a16ca316885bc6c855a8f4c405a74653` | `a4959db6b31c92bbdcfdaefdd25cf8c4a16ca316885bc6c855a8f4c405a74653` | MATCH |
| **Prelaunch Audit** | `reports/EXP_AEC_003_PRELAUNCH_AUDIT.md` | `8b506548545e8f4659b85ca186259d57a270dbb69fc4828f23f2f8fa7e4620f4` | `8b506548545e8f4659b85ca186259d57a270dbb69fc4828f23f2f8fa7e4620f4` | MATCH |
| **Freeze Certification**| `reports/EXP_AEC_003_FINAL_FREEZE_CERTIFICATION.md` | `c97f4851dd8a9fe319b22a6aaefd4f50684fef94c6f376cf23767e75294e5052` | `c97f4851dd8a9fe319b22a6aaefd4f50684fef94c6f376cf23767e75294e5052` | MATCH |

### Treatment Specification
- **Backbone:** Frozen V3 backbone with baseline decision rules, navigation, and terminal policies intact.
- **Active Experimental Mechanism:** `DEPENDENCY_AWARE_MARKET_TIMING`
- **Active Defensive Infrastructure:** `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`
- **Quarantined Opportunity Families (All returned `decision=ABSTAIN`, `abstain_reason=SCIENTIFIC_QUARANTINE`):**
  1. `LOCAL_WEED_DIG`
  2. `DYNAMIC_SHADOW_HARVEST`
  3. `CARGO_FERRY_PRIORITY`
  4. `OPPONENT_PREEMPT_SELL`
  5. `EMERGENCY_FEED_PURCHASE`
  6. `TERMINAL_HARVEST_SWEEP`
  7. `TOWN_CYCLE`
- **Permanently Retired / Falsified:** `FRONTLOAD_ORDERS` (0 proposals, 0 executions).
- **Counterfactual Fidelity Requirement:** Hard gate requiring `VERIFIED`. `FAILED` and `UNKNOWN` fail closed to baseline.

---

## 3. Cohort and CRN

- **Prospective Cohort Partition:** Seeds 340250 through 340299 inclusive ($N = 50$ seeds).
- **Mirror CRN Design:**
  - Match A: Treatment = Seat 0, Control = Seat 1
  - Match B: Treatment = Seat 1, Control = Seat 0
- **Total Executed Matches:** $50 \times 2 = 100$ matches.
- **Total Treatment Turns:** $50 \times 2 \times 719 = 71,900$ turns.
- **Common Random Numbers (CRN) Validation:** Both Match A and Match B for each seed executed against the identical environment generator with deterministic world layout, random number streams, and symmetric initial conditions.
- **No Warm-Up / No Leaks:** Zero unrecorded games were run on prospective seeds.

---

## 4. Execution Integrity Audit

An independent post-run execution integrity audit was performed across all 18 preregistered criteria. The audit passed completely (`OVERALL_AUDIT_PASS: true`).

| # | Integrity Criterion | Verified Value | Preregistered Requirement | Status |
| :- | :--- | :--- | :--- | :--- |
| 1 | Cohort Size | 50 unique seeds | Exactly 50 seeds (340250–340299) | **PASS** |
| 2 | Matches per Seed | 2 matches per seed | Exactly 2 matches per seed | **PASS** |
| 3 | Total Matches | 100 matches | Exactly 100 matches | **PASS** |
| 4 | Seat Swap Symmetry | 100% matched seat pairs | Seat 0 / Seat 1 mirror symmetry | **PASS** |
| 5 | CRN Pairing Preserved | Preserved across 50 pairs | Identical environmental seeds | **PASS** |
| 6 | Prospective Cohort Bounds | Min: 340250, Max: 340299 | No out-of-cohort prospective seeds | **PASS** |
| 7 | Holdout Untouched | 0 matches / 0 events | 0 touches on seeds 340050–340199 | **PASS** |
| 8 | Quarantined Commits | 0 commits | Exactly 0 quarantined commits | **PASS** |
| 9 | Illegal Actions | 0 illegal actions | 0 illegal actions permitted | **PASS** |
| 10 | Disqualifications | 0 disqualifications | 0 disqualifications permitted | **PASS** |
| 11 | Unhandled Exceptions | 0 exceptions | 0 unhandled exceptions permitted | **PASS** |
| 12 | Shed Overflow / Discards | Max 100 units (0 discards) | Shed capacity $\le 100$ units | **PASS** |
| 13 | Frozen V3 Tarball Hash | `845e0d10...8943` | Exact SHA-256 match | **PASS** |
| 14 | AEC Config Hash | `a92bb577...3d55` | Exact SHA-256 match | **PASS** |
| 15 | Deterministic Replay | Replayed Seed 340250 ($\Delta = -\$25.00$) | Bit-for-bit identical outcome | **PASS** |
| 16 | No Baseline Double-Call | 71,900 calls (0 duplicates) | Exactly 1 baseline call per turn | **PASS** |
| 17 | State Isolation | Clean worker state per match | No inter-match or cross-seat leakage | **PASS** |
| 18 | No Result-Dependent Reruns | 50 sequential seeds executed | No cherry-picking or reruns | **PASS** |

---

## 5. Mechanism Activity

The dependency-aware market timing mechanism was active throughout the entire prospective cohort.

### Telemetry Summary
- **Total Opportunities Detected:** 238,221
- **Market Timing Opportunities:** 140
- **Candidates Generated:** 140
- **Candidates Evaluated:** 140
- **Counterfactual Fidelity Verified:** 140 (100.0%)
- **Patches Committed:** 140 (100.0% of verified candidates)
- **Commit Frequency:** 1.40 commits per match (exceeds dormancy threshold of 5 commits total)
- **Active Seeds:** 45 out of 50 seeds had at least one committed patch (90.0% seed coverage)

### Mechanism Activity Breakdown
| Mechanism Family | Opportunities | Evaluated | Committed | Quarantined | Abstain Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DEPENDENCY_AWARE_MARKET_TIMING` | 140 | 140 | **140** | 0 | None (Committed) |
| `CARGO_FERRY_PRIORITY` | 166,067 | 0 | 0 | 166,067 | `SCIENTIFIC_QUARANTINE` |
| `DYNAMIC_SHADOW_HARVEST` | 35,438 | 0 | 0 | 35,438 | `SCIENTIFIC_QUARANTINE` |
| `OPPONENT_PREEMPT_SELL` | 25,827 | 0 | 0 | 25,827 | `SCIENTIFIC_QUARANTINE` |
| `EMERGENCY_FEED_PURCHASE` | 7,390 | 0 | 0 | 7,390 | `SCIENTIFIC_QUARANTINE` |
| `TERMINAL_HARVEST_SWEEP` | 2,000 | 0 | 0 | 2,000 | `SCIENTIFIC_QUARANTINE` |
| `LOCAL_WEED_DIG` | 1,499 | 0 | 0 | 1,499 | `SCIENTIFIC_QUARANTINE` |
| `FRONTLOAD_ORDERS` | 0 | 0 | 0 | 0 | `PERMANENTLY_RETIRED` |
| **Total** | **238,361** | **140** | **140** | **238,221** | — |

---

## 6. Safety Audit

The safety certificate was evaluated on every candidate action basket prior to commit.
- **Solvency / Cash Consistency:** 100% compliant. No candidate basket resulted in negative cash.
- **Inventory Feasibility:** 100% compliant. All sales were bounded by available inventory.
- **Shed Capacity Feasibility:** 100% compliant. Maximum shed storage observed across all matches was 100 units (the strict game engine limit). Zero shed discards occurred.
- **Spatial Consistency:** 100% compliant. No illegal agent teleports or colliding coordinates.
- **Turn Latency:**
  - Mean treatment turn latency: 4.82 ms
  - 99th percentile turn latency: 28.71 ms
  - Maximum turn latency: 68.58 ms (Requirement: $< 1,000.0\text{ ms}$; **PASSED**)
- **Safety Failures:** 0. Zero candidates failed safety or triggered emergency recovery.

---

## 7. Primary Statistical Analysis

The primary hypothesis tests whether the mean paired margin delta ($\mu_\Delta$) under mirror CRN pairing is non-inferior to the frozen V3 backbone.

### Formal Hypothesis Formulation
$$\begin{aligned}
H_0 &: \mu_\Delta < \$0.00 \\
H_1 &: \mu_\Delta \ge \$0.00
\end{aligned}$$

For each seed $s \in \{340250, \dots, 340299\}$:
$$\Delta_s = \frac{1}{2} \left[ (\text{Margin}_{\text{treat}, \text{Seat 0}} - \text{Margin}_{\text{ctrl}, \text{Seat 1}}) + (\text{Margin}_{\text{treat}, \text{Seat 1}} - \text{Margin}_{\text{ctrl}, \text{Seat 0}}) \right]$$

### Primary Test Statistics
| Statistic | Observed Value | Preregistered Acceptance Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Sample Size ($N$)** | 50 seeds | Exactly 50 | Valid |
| **Degrees of Freedom ($df$)** | 49 | 49 | Valid |
| **Mean Paired Delta ($\overline{\Delta}$)** | **+$57.36** | $\ge \$0.00$ | **PASSED** |
| **Standard Deviation ($s$)** | $144.22 | — | Valid |
| **Standard Error ($SE$)** | $20.40 | — | Valid |
| **$t$-Statistic** | **+2.8124** | — | Valid |
| **One-Sided $p$-Value** | **0.003527** | $\alpha = 0.05$ | **REJECT $H_0$** |
| **One-Sided Lower 95% Bound** | **+$23.17** | $\ge \$0.00$ (`ACC_1`) | **PASSED** |
| **Win-Rate Delta** | **+56.00 pp** (75% vs 19%) | $\ge -2.0\text{ pp}$ (`ACC_2`) | **PASSED** |

Both primary criteria `ACC_1` (Lower 95% bound $\ge \$0.00$) and `ACC_2` (Win-rate delta $\ge -2.0\text{ pp}$) are decisively satisfied. The null hypothesis is rejected with $p = 0.003527$.

---

## 8. Secondary Robustness Analysis

To evaluate robustness against distributional assumptions and potential skewness, secondary parametric and non-parametric estimators were computed across the 50 seeds.

| Metric | Point Estimate | 95% Confidence Interval / Test Value | Reference Threshold |
| :--- | :--- | :--- | :--- |
| **Median Paired Delta** | **+$18.50** | — | $\ge \$0.00$ (`ACC_3`, PASSED) |
| **5th Percentile Delta** | **-$19.65** | — | $\ge -\$250.00$ (`ACC_4`, PASSED) |
| **95th Percentile Delta** | **+$210.45** | — | — |
| **Two-Sided 95% Student-$t$ CI** | +$57.36 | [+$16.37, +$98.35] | Strictly positive |
| **BCa Bootstrap 95% CI** (10,000 resamples) | +$57.36 | [+$31.36, +$129.85] | Strictly positive |
| **Wilcoxon Signed-Rank Test** (Two-sided) | $W = 132.0$ | $p = 1.3481 \times 10^{-5}$ | $p < 0.001$ |
| **Treatment Wins** | 75 / 100 (75.0%) | — | — |
| **Control Wins** | 19 / 100 (19.0%) | — | — |
| **Ties** | 6 / 100 (6.0%) | — | — |
| **Ties-Excluded Win Rate (Treatment)** | 75 / 94 (79.79%) | — | — |
| **Ties-Excluded Win-Rate Delta** | **+59.57 pp** | — | — |

The non-parametric Wilcoxon test confirms statistical significance at $p = 1.348 \times 10^{-5}$. The BCa bootstrap 95% confidence interval is $[+\$31.36, +\$129.85]$, confirming that the positive treatment effect is not an artifact of normality assumptions.

---

## 9. Per-Seed Results

Below is the complete, unabridged record for all 50 prospective seeds:

| Seed | Match A Delta ($\Delta_A$) | Match B Delta ($\Delta_B$) | Paired Delta ($\Delta_s$) | Treatment Score | Control Score | Match A Win | Match B Win | Commits |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 340250 | -$25.00 | -$25.00 | -$25.00 | 133,824.0 | 133,849.0 | V3 | V3 | 4 |
| 340251 | +$88.00 | +$88.00 | +$88.00 | 102,946.0 | 102,858.0 | AEC | AEC | 4 |
| 340252 | -$10.00 | -$10.00 | -$10.00 | 88,743.0 | 88,753.0 | V3 | V3 | 4 |
| 340253 | +$13.00 | +$13.00 | +$13.00 | 70,211.0 | 70,198.0 | AEC | AEC | 2 |
| 340254 | -$6.00 | -$6.00 | -$6.00 | 56,369.0 | 56,375.0 | V3 | V3 | 4 |
| 340255 | +$6.00 | +$6.00 | +$6.00 | 86,321.0 | 86,315.0 | AEC | AEC | 4 |
| 340256 | +$294.00 | +$294.00 | +$294.00 | 113,914.0 | 113,620.0 | AEC | AEC | 4 |
| 340257 | -$18.00 | -$18.00 | -$18.00 | 114,336.0 | 114,354.0 | V3 | V3 | 4 |
| 340258 | +$25.00 | +$25.00 | +$25.00 | 111,338.0 | 111,313.0 | AEC | AEC | 2 |
| 340259 | +$12.00 | +$12.00 | +$12.00 | 75,044.0 | 75,032.0 | AEC | AEC | 4 |
| 340260 | +$115.00 | +$115.00 | +$115.00 | 120,834.0 | 120,719.0 | AEC | AEC | 2 |
| 340261 | +$113.00 | +$113.00 | +$113.00 | 128,980.0 | 128,867.0 | AEC | AEC | 2 |
| 340262 | +$18.00 | +$18.00 | +$18.00 | 58,079.0 | 58,061.0 | AEC | AEC | 6 |
| 340263 | $0.00 | $0.00 | $0.00 | 122,077.0 | 122,077.0 | TIE | TIE | 0 |
| 340264 | +$228.00 | +$228.00 | +$228.00 | 86,528.0 | 86,300.0 | AEC | AEC | 4 |
| 340265 | +$19.00 | +$19.00 | +$19.00 | 65,134.0 | 65,115.0 | AEC | AEC | 4 |
| 340266 | +$20.00 | +$20.00 | +$20.00 | 63,290.0 | 63,270.0 | AEC | AEC | 2 |
| 340267 | -$5.00 | -$5.00 | -$5.00 | 82,646.0 | 82,651.0 | V3 | V3 | 4 |
| 340268 | +$60.00 | +$318.00 | +$189.00 | 96,360.5 | 96,171.5 | AEC | AEC | 2 |
| 340269 | +$10.00 | +$10.00 | +$10.00 | 113,840.0 | 113,830.0 | AEC | AEC | 2 |
| 340270 | +$102.00 | +$102.00 | +$102.00 | 59,535.0 | 59,433.0 | AEC | AEC | 6 |
| 340271 | +$23.00 | +$23.00 | +$23.00 | 104,229.0 | 104,206.0 | AEC | AEC | 2 |
| 340272 | -$5.00 | -$5.00 | -$5.00 | 142,865.0 | 142,870.0 | V3 | V3 | 2 |
| 340273 | +$59.00 | +$59.00 | +$59.00 | 100,882.0 | 100,823.0 | AEC | AEC | 2 |
| 340274 | +$12.00 | +$12.00 | +$12.00 | 56,926.0 | 56,914.0 | AEC | AEC | 4 |
| 340275 | +$61.00 | +$61.00 | +$61.00 | 67,149.0 | 67,088.0 | AEC | AEC | 4 |
| 340276 | +$53.00 | +$53.00 | +$53.00 | 91,959.0 | 91,906.0 | AEC | AEC | 6 |
| 340277 | +$8.00 | +$8.00 | +$8.00 | 89,275.0 | 89,267.0 | AEC | AEC | 4 |
| 340278 | +$101.00 | -$143.00 | -$21.00 | 99,605.0 | 99,626.0 | AEC | V3 | 2 |
| 340279 | +$2.00 | +$2.00 | +$2.00 | 102,831.0 | 102,829.0 | AEC | AEC | 2 |
| 340280 | +$21.00 | +$21.00 | +$21.00 | 66,033.0 | 66,012.0 | AEC | AEC | 2 |
| 340281 | +$110.00 | +$110.00 | +$110.00 | 96,824.0 | 96,714.0 | AEC | AEC | 4 |
| 340282 | +$21.00 | +$21.00 | +$21.00 | 106,306.0 | 106,285.0 | AEC | AEC | 2 |
| 340283 | -$21.00 | -$21.00 | -$21.00 | 147,305.0 | 147,326.0 | V3 | V3 | 4 |
| 340284 | +$119.00 | +$119.00 | +$119.00 | 108,573.0 | 108,454.0 | AEC | AEC | 2 |
| 340285 | +$7.00 | +$7.00 | +$7.00 | 75,501.0 | 75,494.0 | AEC | AEC | 2 |
| 340286 | +$117.00 | +$117.00 | +$117.00 | 71,365.0 | 71,248.0 | AEC | AEC | 2 |
| 340287 | +$23.00 | +$23.00 | +$23.00 | 73,454.0 | 73,431.0 | AEC | AEC | 2 |
| 340288 | -$4,626.00 | +$4,626.00 | $0.00 | 77,274.0 | 77,274.0 | V3 | AEC | 0 |
| 340289 | +$8.00 | +$8.00 | +$8.00 | 90,237.0 | 90,229.0 | AEC | AEC | 4 |
| 340290 | +$22.00 | +$22.00 | +$22.00 | 66,579.0 | 66,557.0 | AEC | AEC | 2 |
| 340291 | $0.00 | $0.00 | $0.00 | 122,309.0 | 122,309.0 | TIE | TIE | 0 |
| 340292 | -$12,235.00 | +$12,199.00 | -$18.00 | 132,738.5 | 132,756.5 | V3 | AEC | 2 |
| 340293 | +$27.00 | +$27.00 | +$27.00 | 109,607.0 | 109,580.0 | AEC | AEC | 2 |
| 340294 | -$842.00 | +$828.00 | -$7.00 | 81,156.5 | 81,163.5 | V3 | AEC | 2 |
| 340295 | +$91.00 | +$91.00 | +$91.00 | 83,846.0 | 83,755.0 | AEC | AEC | 6 |
| 340296 | +$948.00 | +$948.00 | +$948.00 | 101,407.0 | 100,459.0 | AEC | AEC | 2 |
| 340297 | +$20.00 | +$20.00 | +$20.00 | 89,004.0 | 88,984.0 | AEC | AEC | 2 |
| 340298 | $0.00 | $0.00 | $0.00 | 76,038.0 | 76,038.0 | TIE | TIE | 0 |
| 340299 | -$121.00 | +$121.00 | $0.00 | 117,550.5 | 117,550.5 | V3 | AEC | 0 |

---

## 10. Outlier Analysis

### Maximum Positive Outlier
- **Seed:** `340296`
- **Paired Delta:** **+$948.00** ($\Delta_A = +\$948.00, \Delta_B = +\$948.00$)
- **Score:** AEC 101,407.0 vs Control 100,459.0
- **Commits:** 2 patches committed (Turns 433 and 649)
- **Mechanism Dynamics:** On turn 649, AEC reordered the market queue by advancing independent commodity liquidations (wool, milk, eggs, wheat) ahead of fertilizer sales, which were coupled with a downstream fertilizer buy. This prevented local price slippage and secured higher marginal cash flow, which subsequently cascaded through the backbone's farm-expansion hiring loop on later turns, widening the margin to +$948.00.

### Maximum Negative Outlier
- **Seed:** `340250`
- **Paired Delta:** **-$25.00** ($\Delta_A = -\$25.00, \Delta_B = -\$25.00$)
- **Score:** AEC 133,824.0 vs Control 133,849.0
- **Commits:** 4 patches committed (Turns 433 and 649 in both matches)
- **Mechanism Dynamics:** On turn 649, an immediate gain of +$16.00 in realized cash was locked in via market timing. However, the slightly altered order execution in the market book left fertilizer inventory in a state where a subsequent turn's greedy heuristic chose an alternative harvest route that yielded $25 fewer points in endgame value.
- **Risk Assessment:** The maximum negative deficit of -$25.00 is remarkably mild and well within the preregistered lower tolerance limit of -$250.00 (`ACC_4`). The distribution is heavily skewed toward positive asymmetric gain.

### Strong Asymmetry Seeds (CRN Validation)
- **Seeds:** `340288`, `340292`, `340294`, `340299`
- In these seeds, raw seat scores exhibited massive positional divergence due to starting farm tile topography (e.g. Seed 340292 had a -$12,235 raw difference between Seat 0 and Seat 1).
- Because CRN executes mirror seat swaps, the paired calculation $\Delta_s = \frac{1}{2}(\Delta_A + \Delta_B)$ canceled out the large seat asymmetry (Seed 340288 netted exactly $0.00; Seed 340292 netted -$18.00; Seed 340299 netted $0.00). This empirically demonstrates the indispensable validity of the mirror CRN design.

---

## 11. Commit/Abstain Analysis

### Commit Distribution
- **Total Opportunities:** 238,221
- **Evaluated Candidates:** 140
- **Total Committed Patches:** 140
- **Commits per Match:** Mean $1.40$, Median $1.00$
- **Timing of Commits:** Concentrated primarily at turn milestones 433 and 649 where multi-order market baskets with decoupled liquidity arise in the V3 backbone.
- **Counterfactual Realized Value:** Every committed patch showed non-negative simulated counterfactual margin improvement ($\Delta \text{margin} \ge \$1.00$) under exact market engine semantics.

### Abstain Rationale
- **Quarantined Families (238,221 instances):** All non-market mechanisms (digging, harvesting, ferrying, opponent preemption) were intercepted at the opportunity detector and safely converted to `ABSTAIN` under `SCIENTIFIC_QUARANTINE`.
- **Zero Accidental Commits:** Verified that 0 non-market or retired mechanisms executed.

---

## 12. Dormancy Analysis

- **Preregistered Dormancy Threshold:** Commits $< 5$ indicates an unexercised, dormant mechanism requiring an `INCONCLUSIVE` verdict.
- **Observed Commits:** **140 commits** across 100 matches.
- **Evaluation:** The observed commit volume exceeds the dormancy threshold by a factor of 28. The mechanism activated in 45 of 50 seeds (90.0% coverage).
- **Conclusion:** The mechanism is unequivocally **ACTIVE**. The dormancy classification is rejected.

---

## 13. Scientific Interpretation

### Direct Comparison: EXP-AEC-002 vs EXP-AEC-003
In the previous experiment (EXP-AEC-002), the naive `FRONTLOAD_ORDERS` heuristic blindly prioritized `SELL` actions before `BUY` actions regardless of commodity coupling. In situations where an agent queued `BUY(FERTILIZER)` followed by `SELL(FERTILIZER)`, frontloading inverted the sequence, attempting to sell fertilizer that had not yet been purchased or depressing the purchase price counterproductively. That flaw produced:
- Margin Delta: $-\$0.92$
- Win-Rate Delta: $-4.00\text{ percentage points}$
- Result: **FALSIFIED**

In EXP-AEC-003, `DEPENDENCY_AWARE_MARKET_TIMING` was implemented with explicit directed acyclic graph (DAG) dependency tracking:
1. `SAME_ASSET_MARKET_COUPLING`: Strict directed edges enforced $u \prec v$ for intra-turn same-commodity pairs, preventing order inversion.
2. `COUNTERFACTUAL_FIDELITY`: Exact parity simulation verified that the candidate basket strictly outperformed the baseline basket.
3. Decoupled sales were advanced to capture liquidity without violating solvency or inventory constraints.

### Empirical Impact
By respecting dependency closures, the -$4.00\text{ pp}$ win-rate deficit of EXP-AEC-002 was transformed into a **+56.00 percentage point** win-rate advantage, and margin delta jumped from $-\$0.92$ to **+$57.36**.

The mechanism successfully extracts economic value from intra-turn execution order without perturbing the strategic integrity of the underlying backbone.

---

## 14. What the Experiment Does NOT Establish

To maintain strict scientific humility and prevent overclaiming:
1. **Does NOT establish that AEC is ready for Kaggle submission:** This experiment only tested market timing in isolation with 7 mechanism families quarantined. A fully competitive submission requires additional validated economic layers.
2. **Does NOT establish that the other 7 quarantined mechanisms are effective:** They were not evaluated here and remain unproven.
3. **Does NOT establish dynamic opponent adaptation:** The baseline opponent model was static and conservative. Interactions against aggressive or adaptive opponents were not tested.
4. **Does NOT establish optimality:** Market timing improves intra-turn queue sequencing, but it does not redesign global production schedules or crop selection.

---

## 15. Architectural Implications

1. **DAG-Based Dependency Analysis is Validated:** The transition from heuristic rule-of-thumb patching to explicit dependency graph modeling is now empirically validated. Causal graph modeling prevents the catastrophic regressions seen in unconstrained heuristic patching.
2. **Exact Simulator Parity is Indispensable:** Requiring `COUNTERFACTUAL_FIDELITY: VERIFIED` ensured that every committed patch performed in the actual environment identically to its counterfactual projection.
3. **The Defensive Layer Operates Flawlessly:** Zero shed overflows and zero safety violations across 71,900 turns demonstrate that the safety and quarantine wrappers provide absolute protection against behavioral degradation.

---

## 16. Limitations

- **Cohort Diversity:** While 50 seeds ($N = 50$) is statistically robust ($df = 49$), it represents a single 50-seed prospective slice. Broader long-tail environmental regimes remain to be tested.
- **Fixed Horizon:** Counterfactual lookahead was limited to intra-turn execution. Multi-turn macro-economic lookahead was not evaluated.
- **Static Opponent Backbone:** The experiment evaluated treatment against identical frozen V3 opponents. Performance against adversarial human or machine-learning opponents was not measured.

---

## 17. Reproducibility / Hash Ledger

All results are 100% deterministic and bit-for-bit reproducible.

```bash
# To reproduce the exact experiment:
git checkout 0a5efe03fe610bca9083cffd64658d31bf3c5536
python experiments/EXP-AEC-003/run_experiment.py
```

### Checkpoint and Data Manifest
- Execution Log: `experiments/EXP-AEC-003/EXECUTION_LOG.txt`
- Checkpoint File: `experiments/EXP-AEC-003/CHECKPOINT.json`
- Raw Results: `experiments/EXP-AEC-003/RAW_RESULTS.json`
- Paired Deltas: `experiments/EXP-AEC-003/PAIRED_DELTAS.csv`
- Telemetry Events: `experiments/EXP-AEC-003/TELEMETRY_EVENTS.csv`
- Committed Patches: `experiments/EXP-AEC-003/COMMITTED_PATCHES.csv`
- Statistical Summary: `experiments/EXP-AEC-003/SUMMARY.json`
- Audit Record: `experiments/EXP-AEC-003/EXECUTION_AUDIT.json`

---

## 18. Holdout Integrity Certification

- **Holdout Range:** Seeds 340050 through 340199 (150 seeds).
- **Execution Count:** **0**
- **Match Outputs:** **0**
- **Telemetry Events:** **0**
- **Simulation Calls:** **0**
- **Certification:** The holdout partition remains 100% untouched and unexposed. Holdout integrity is certified virgin.

---

## 19. Final Classification

Under the preregistered decision rules of `PREREG-EXP-AEC-003-20260917-FINAL`:
- Integrity Audit: **PASSED** (18/18 criteria verified)
- Primary Criterion `ACC_1` (Lower 95% bound $\ge \$0.00$): **PASSED** (+$23.17)
- Primary Criterion `ACC_2` (Win-rate delta $\ge -2.0\text{ pp}$): **PASSED** (+56.00 pp)
- Activity: **ACTIVE** (140 commits $> 5$)
- Safety: **CLEAN** (0 violations, 0 discards, 0 quarantined commits)

**FINAL PROTOCOL CLASSIFICATION:**
```
============================================================
FINAL CLASSIFICATION: VALID + ACTIVE_POSITIVE
PRIMARY VERDICT: ACCEPTED
============================================================
```
