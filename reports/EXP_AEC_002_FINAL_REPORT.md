# EXP-AEC-002 Final Scientific Evaluation Report

**Experiment Identifier:** `EXP-AEC-002`  
**Protocol Identifier:** `PREREG-EXP-AEC-002-20260917-FINAL` (`reports/EXP_AEC_002_PREREGISTRATION_FINAL.md`)  
**Cohort Audit Document:** `reports/EXP_AEC_002_COHORT_AUDIT.md`  
**Execution Manifest:** `experiments/EXP-AEC-002/EXECUTION_MANIFEST.json`  
**Execution Date:** 2026-09-17  
**Governance Standard:** Strict Scientific Governance & Prospective Double-Blind CRN Evaluation  
**Evaluation Status:** **COMPLETED & AUDITED**  
**Final Scientific Verdict:** **ACTIVE_NEGATIVE / FALSIFIED**

---

## 1. Executive Summary

| Governance Dimension | Specification & Audit Metric | Final Empirical Measurement | Status |
|---|---|---|---|
| **Experimental Status** | Complete execution under frozen protocol | 50 seeds, 100 matches, 71,900 turns | **VALID** |
| **Prospective Cohort** | Seeds `340200–340249` ($N = 50$ seeds) | 50 unique seeds, zero prior execution | **CERTIFIED VIRGIN** |
| **Locked Holdout** | Seeds `340050–340199` ($N = 150$ seeds) | 0 simulations, 0 touches | **PRISTINE & SEALED** |
| **Primary Metric ($\overline{\Delta}$)** | Paired Terminal Margin Delta ($\text{Mean}$) | **-$0.92** | **NON-INFERIORITY FAILED** |
| **One-Sided 95% Lower Bound** | Lower bound of 90% CI ($\alpha = 0.05$) | **-$2.07** ($< \$0.00$) | **FALS_2 TRIGGERED** |
| **Win-Rate Delta ($\Delta \text{WinRate}$)** | Treatment Win Rate $-$ Control Win Rate | **-4.00 pp** ($< -2.0\text{ pp}$) | **FALS_1 TRIGGERED** |
| **Match Accounting** | 100 Tournament Matches | 5 Treatment Wins, 9 Control Wins, 86 Ties | **EMPIRICAL RECORD** |
| **Mechanism Activity** | Total Committed Patches | **20 Commits** (`FRONTLOAD_ORDERS` active) | **ACTIVE TREATMENT** |
| **Quarantined Commits** | Commits from 7 quarantined families | **Exactly 0 commits** | **ACC_6 PASSED** |
| **Safety Invariants** | Disqualifications, illegal moves, shed overflows | **0 across all 71,900 turns** | **ACC_5 PASSED** |
| **Result Classification** | Protocol Classification Standard (§15) | **`ACTIVE_NEGATIVE`** | **OFFICIALLY FALSIFIED** |

---

## 2. Authoritative Frozen Configuration

The experiment was executed without any mid-flight tuning, threshold modification, or protocol deviation:

- **Baseline Control Backbone:** Frozen Teammate V3 Macro Policy loaded directly from `submission_Vj_kc_v3.tar.gz`.
  - SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
- **AEC Configuration (`AECConfig`):**
  - Canonical JSON SHA-256: `db59108d29241534cde9d9a12bdc93c588800be7ad7ec2838cee09efdea5721c`
  - Source File: `aec/config.py` (SHA-256: `240deda295ce68490bf68a1fb046be2905044e78fafafb2a51aeb8b5c2f71f63`)
  - Horizons: Short = 6, Normal = 18, Extended = 36
  - Budgets: `max_opportunities = 16`, `max_candidates = 8`, `max_simulations = 8`
  - Active Treatment: `FRONTLOAD_ORDERS`
  - Defense-in-Depth Fallbacks: `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`
  - Quarantined Mechanisms: `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`, `EMERGENCY_FEED_PURCHASE`, `TERMINAL_HARVEST_SWEEP`, `TOWN_CYCLE`

---

## 3. Cohort and CRN Match Design

- **Authorized Prospective Cohort:** Contiguous partition `340200` through `340249` inclusive ($N = 50$).
- **Mirror Common Random Numbers (CRN) Design:**
  - For each seed $s \in [340200, 340249]$, exactly two tournament games were run:
    - **Match A:** Player 0 = Treatment (AEC V1.1), Player 1 = Control (Frozen V3)
    - **Match B:** Player 0 = Control (Frozen V3), Player 1 = Treatment (AEC V1.1)
  - Total Matches: $50 \times 2 = 100$ completed games.
  - Turn Accounting: $100 \times 719 = 71,900$ treatment decision turns.
- **Seat-Averaged Paired Delta Formula:**
  $$\Delta_s = \frac{1}{2} \left[ \left(\text{Margin}_{\text{treat, Seat 0}} - \text{Margin}_{\text{ctrl, Seat 1}}\right) + \left(\text{Margin}_{\text{treat, Seat 1}} - \text{Margin}_{\text{ctrl, Seat 0}}\right) \right]$$

---

## 4. Execution Integrity Audit

An independent post-run execution audit was completed immediately upon match termination (`experiments/EXP-AEC-002/EXECUTION_AUDIT.json`). All 15 audit criteria evaluated to **TRUE**:

```json
{
  "A_cohort_completeness": { "pass": true, "seed_count": 50, "expected_count": 50, "min_seed": 340200, "max_seed": 340249 },
  "B_turn_completeness": { "pass": true, "total_treatment_turns": 71900, "expected_turns": 71900 },
  "C_seat_symmetry": { "pass": true, "note": "Match A has AEC Seat 0, Match B has AEC Seat 1 for all seeds" },
  "D_crn_integrity": { "pass": true },
  "E_baseline_call_count": { "pass": true, "total_baseline_calls": 71900, "duplicate_calls": 0 },
  "F_G_safety_and_exceptions": { "pass": true, "disqualifications": 0, "illegal_actions": 0, "unhandled_exceptions": 0 },
  "H_quarantined_commits_zero": { "pass": true },
  "I_holdout_untouched": { "pass": true, "holdout_range": "340050-340199", "overlap_count": 0 },
  "J_no_out_of_cohort_execution": { "pass": true },
  "K_L_cryptographic_hashes": { "pass": true, "v3_pass": true, "config_pass": true },
  "M_deterministic_replay": { "pass": true, "replay_seed": 340200, "original_margin": 0.0, "replay_margin": 0.0 },
  "OVERALL_AUDIT_PASS": true
}
```

---

## 5. Mechanism Activity Telemetry

Unlike `EXP-AEC-001` where the treatment remained dormant (0 commits), **`EXP-AEC-002` was an actively treated experiment**:

- **Total Turns with Detected Opportunity Events:** 70,800 turns (out of 71,900 turns)
- **Total Candidate Mutations Simulated:** 20 candidate patches
- **Total Committed Patches:** **20 commits** (all `FRONTLOAD_ORDERS`)
- **Total Abstains:** 71,880 turns
  - `NO_OPPORTUNITIES_FOUND`: 70,680 turns
  - `NO_FEASIBLE_CANDIDATE_PATCHES`: 1,200 turns
- **Quarantined Mechanism Interceptions (Evaluator strictly emitted `ABSTAIN`):**
  - `CARGO_FERRY_PRIORITY`: 169,803 proposals blocked
  - `DYNAMIC_SHADOW_HARVEST`: 38,056 proposals blocked
  - `OPPONENT_PREEMPT_SELL`: 23,713 proposals blocked
  - `EMERGENCY_FEED_PURCHASE`: 9,218 proposals blocked
  - `TERMINAL_HARVEST_SWEEP`: 2,000 proposals blocked
  - `LOCAL_WEED_DIG`: 1,494 proposals blocked
  - **Quarantined Commits:** **0** (100% adherence to quarantine covenant)

### 5.1 Committed Patches Audit Record

All 20 committed patches were executed under `FRONTLOAD_ORDERS` on 6 distinct seeds across steps 575 and 647:

| Seed | Match | Turn | Seat | Mechanism | Patch ID | CF $\Delta \text{Money}$ | Baseline Market Order | Candidate Market Order |
|---|---|---|---|---|---|---|---|---|
| `340209` | Match A | 575 | 0 | `FRONTLOAD` | `..._STEP_575` | +$37.0 | `[BUY WHEAT 16, SELL WHEAT 5, BUY FERT 11]` | `[SELL WHEAT 5, BUY WHEAT 16, BUY FERT 11]` |
| `340209` | Match A | 647 | 0 | `FRONTLOAD` | `..._STEP_647` | +$25.0 | `[BUY WHEAT 15, SELL WHEAT 6]` | `[SELL WHEAT 6, BUY WHEAT 15]` |
| `340209` | Match B | 575 | 1 | `FRONTLOAD` | `..._STEP_575` | +$37.0 | `[BUY WHEAT 16, SELL WHEAT 5, BUY FERT 11]` | `[SELL WHEAT 5, BUY WHEAT 16, BUY FERT 11]` |
| `340209` | Match B | 647 | 1 | `FRONTLOAD` | `..._STEP_647` | +$25.0 | `[BUY WHEAT 15, SELL WHEAT 6]` | `[SELL WHEAT 6, BUY WHEAT 15]` |
| `340214` | Match A | 575 | 0 | `FRONTLOAD` | `..._STEP_575` | +$48.0 | `[BUY WHEAT 16, SELL WHEAT 13, BUY FERT 11]` | `[SELL WHEAT 13, BUY WHEAT 16, BUY FERT 11]` |
| `340214` | Match A | 647 | 0 | `FRONTLOAD` | `..._STEP_647` | +$21.0 | `[BUY WHEAT 15, SELL WHEAT 6]` | `[SELL WHEAT 6, BUY WHEAT 15]` |
| `340214` | Match B | 575 | 1 | `FRONTLOAD` | `..._STEP_575` | +$48.0 | `[BUY WHEAT 16, SELL WHEAT 13, BUY FERT 11]` | `[SELL WHEAT 13, BUY WHEAT 16, BUY FERT 11]` |
| `340214` | Match B | 647 | 1 | `FRONTLOAD` | `..._STEP_647` | +$21.0 | `[BUY WHEAT 15, SELL WHEAT 6]` | `[SELL WHEAT 6, BUY WHEAT 15]` |
| `340217` | Match A | 575 | 0 | `FRONTLOAD` | `..._STEP_575` | +$63.0 | `[BUY WHEAT 16, SELL WHEAT 14, BUY FERT 11]` | `[SELL WHEAT 14, BUY WHEAT 16, BUY FERT 11]` |
| `340217` | Match B | 575 | 1 | `FRONTLOAD` | `..._STEP_575` | +$63.0 | `[BUY WHEAT 16, SELL WHEAT 14, BUY FERT 11]` | `[SELL WHEAT 14, BUY WHEAT 16, BUY FERT 11]` |
| `340224` | Match A | 575 | 0 | `FRONTLOAD` | `..._STEP_575` | +$34.0 | `[BUY WHEAT 16, SELL WHEAT 2, BUY FERT 11]` | `[SELL WHEAT 2, BUY WHEAT 16, BUY FERT 11]` |
| `340224` | Match A | 647 | 0 | `FRONTLOAD` | `..._STEP_647` | +$25.0 | `[BUY WHEAT 15, SELL WHEAT 3]` | `[SELL WHEAT 3, BUY WHEAT 15]` |
| `340224` | Match B | 575 | 1 | `FRONTLOAD` | `..._STEP_575` | +$34.0 | `[BUY WHEAT 16, SELL WHEAT 2, BUY FERT 11]` | `[SELL WHEAT 2, BUY WHEAT 16, BUY FERT 11]` |
| `340224` | Match B | 647 | 1 | `FRONTLOAD` | `..._STEP_647` | +$25.0 | `[BUY WHEAT 15, SELL WHEAT 3]` | `[SELL WHEAT 3, BUY WHEAT 15]` |
| `340226` | Match A | 575 | 0 | `FRONTLOAD` | `..._STEP_575` | +$44.0 | `[BUY WHEAT 16, SELL WHEAT 15, BUY FERT 11]` | `[SELL WHEAT 15, BUY WHEAT 16, BUY FERT 11]` |
| `340226` | Match A | 647 | 0 | `FRONTLOAD` | `..._STEP_647` | +$37.0 | `[BUY WHEAT 15, SELL WHEAT 6]` | `[SELL WHEAT 6, BUY WHEAT 15]` |
| `340226` | Match B | 575 | 1 | `FRONTLOAD` | `..._STEP_575` | +$44.0 | `[BUY WHEAT 16, SELL WHEAT 15, BUY FERT 11]` | `[SELL WHEAT 15, BUY WHEAT 16, BUY FERT 11]` |
| `340226` | Match B | 647 | 1 | `FRONTLOAD` | `..._STEP_647` | +$37.0 | `[BUY WHEAT 15, SELL WHEAT 6]` | `[SELL WHEAT 6, BUY WHEAT 15]` |
| `340249` | Match A | 575 | 0 | `FRONTLOAD` | `..._STEP_575` | +$42.0 | `[BUY WHEAT 16, SELL WHEAT 6, BUY FERT 11]` | `[SELL WHEAT 6, BUY WHEAT 16, BUY FERT 11]` |
| `340249` | Match B | 575 | 1 | `FRONTLOAD` | `..._STEP_575` | +$40.0 | `[BUY WHEAT 16, SELL WHEAT 5, BUY FERT 11]` | `[SELL WHEAT 5, BUY WHEAT 16, BUY FERT 11]` |

---

## 6. Safety and Governance Audit

- **Disqualifications:** 0
- **Illegal Actions:** 0
- **Shed Inventory Violations:** 0 (Max live shed occupancy observed: 100/100 units)
- **Shed Discard / Overflow Events:** 0
- **Unhandled Exceptions:** 0
- **Step Latency Distribution:**
  - Mean Latency: 1.15 ms
  - Median Latency: 1.12 ms
  - 95th Percentile Latency: 1.48 ms
  - 99th Percentile Latency: 2.10 ms
  - Maximum Latency: 56.76 ms (Hard fail-closed limit is 1,000 ms; 0 violations)

---

## 7. Primary Statistical Results

| Metric | Sample Estimate | 95% Confidence Interval | Inferential Statistic | $p$-value |
|---|---|---|---|---|
| **Mean Paired Margin Delta ($\overline{\Delta}$)** | **-$0.92** | Student-$t$: [-$2.29, +\$0.45$] | $t(49) = -1.3465$ | $p = 0.9078$ (one-sided) |
| **Lower 95% One-Sided Bound** | **-$2.07** | Directional: $[-\$2.07, +\infty)$ | — | Fails $\ge \$0.00$ bound |
| **Bootstrap Mean Delta ($\text{BCa}$)** | **-$0.92** | 10,000 resamples: [-$3.69, \$0.00$] | — | Entirely $\le \$0.00$ |
| **Median Paired Margin Delta** | **$0.00** | — | Wilcoxon $W = 0.0$ | $p = 0.1797$ (two-sided) |
| **Standard Deviation ($s$)** | $4.83 | — | — | — |
| **Standard Error ($\text{SE}$)** | $0.68 | — | — | — |
| **5th Percentile Margin Delta** | **$0.00** | — | — | Meets $\ge -\$250$ |
| **Minimum Paired Delta** | **-$31.00** | Observed on Seed `340224` | — | — |
| **Maximum Paired Delta** | **$0.00** | Observed on 48/50 seeds | — | — |

### 7.1 Tournament Win Accounting (100 Matches)

- **Treatment Wins:** 5 matches (5.0%)
- **Control Wins:** 9 matches (9.0%)
- **Ties:** 86 matches (86.0%)
- **Win-Rate Delta ($\Delta \text{WinRate}$):** **-4.00 percentage points** (Fails $\ge -2.0\text{ pp}$ bound)
- **Ties-Excluded Win-Rate Delta:** **-28.57 percentage points** ($\frac{5 - 9}{14}$)
- **Mean Scores:**
  - Treatment Mean Terminal Reward: 100,212.14
  - Control Mean Terminal Reward: 100,213.06
  - Raw Score Difference: **-0.92**

---

## 8. Decision Criteria Evaluation

### 8.1 Acceptance Criteria Bundle

- [ ] **`ACC_1` (Lower 95% Confidence Bound $\ge \$0.00$):** **FAIL** (Lower bound is -$2.07)
- [ ] **`ACC_2` (Win-Rate Difference $\ge -2.0\text{ pp}$):** **FAIL** ($\Delta \text{WinRate} = -4.00\text{ pp}$)
- [x] **`ACC_3` (Median Paired Margin $\ge \$0.00$):** **PASS** (Median = $0.00)
- [x] **`ACC_4` (5th Percentile Margin $\ge -\$250.00$):** **PASS** (5th percentile = $0.00)
- [x] **`ACC_5` (Zero Safety Regressions):** **PASS** (0 illegal moves, 0 overflows, 0 exceptions)
- [x] **`ACC_6` (Strict Quarantine Adherence):** **PASS** (0 commits across all 7 quarantined families)
- [x] **`ACC_7` (Two-Phase Lockstep Parity):** **PASS** (100% adherence on all 20 committed FRONTLOAD interventions)

**Acceptance Decision:** **REJECTED (2 of 7 criteria failed).**

### 8.2 Falsification Criteria Bundle

- [x] **`FALS_1` ($\Delta \text{WinRate} < -2.0\text{ pp}$):** **TRIGGERED** (-4.00 pp)
- [x] **`FALS_2` (Lower 95% Confidence Bound $< \$0.00$):** **TRIGGERED** (-$2.07)
- [ ] `FALS_3` (Disqualification / Rule violation): NOT TRIGGERED
- [ ] `FALS_4` (Shed overflow discard): NOT TRIGGERED
- [ ] `FALS_5` (Latency $\ge 1000\text{ ms}$): NOT TRIGGERED
- [ ] `FALS_6` (Quarantined mechanism commit): NOT TRIGGERED
- [ ] `FALS_7` (Frozen V3 archive altered): NOT TRIGGERED
- [ ] `FALS_8` (Holdout touched): NOT TRIGGERED
- [ ] `FALS_9` (Cohort overlap): NOT TRIGGERED

**Falsification Verdict:** **PROTOCOL OFFICIALLY FALSIFIED under `FALS_1` and `FALS_2`.**

---

## 9. Per-Seed Paired Delta Analysis

Across the 50 prospective seeds:
- **48 seeds yielded $\Delta_s = \$0.00$**
- **2 seeds yielded strictly negative deltas:**
  - **Seed `340214`:** $\Delta_s = -\$15.00$ (Match A: -$15, Match B: -$15)
  - **Seed `340224`:** $\Delta_s = -\$31.00$ (Match A: -$31, Match B: -$31)
- **0 seeds yielded a positive paired delta.**

### 9.1 Decomposition of Non-Tied Matches

Notice the distinction between seed-level paired deltas and individual match outcomes:
- In seeds `340211`, `340216`, `340222`, and `340238`, **treatment committed zero patches** (played identical baseline moves).
  - Yet individual matches had non-zero score margins due to inherent seat asymmetry (e.g. Seed `340216` Seat 0 scored +1,017 over Seat 1).
  - In Match A (treatment on Seat 0), treatment won +1,017. In Match B (treatment on Seat 1), control on Seat 0 won +1,017.
  - The paired delta was mathematically identical to $0.00$, but produced 1 treatment win and 1 control win in the raw match accounting.
- In seeds `340214` and `340224`, **treatment committed FRONTLOAD patches in both matches**, and in both matches, treatment scored lower than control:
  - Seed `340214`: Treatment lost both Match A (-15) and Match B (-15).
  - Seed `340224`: Treatment lost both Match A (-31) and Match B (-31).
  - These 4 losses account for control's $+4$ net match win advantage ($9 - 5 = 4$).

---

## 10. Root Cause Forensic Analysis: Why Did `FRONTLOAD_ORDERS` Lose?

Forensic step-by-step game replay on Seed `340224` (steps 574–718) uncovered the exact microeconomic failure mode:

### 10.1 The Economic Reversal
At Step 575 on Seed `340224`:
- The baseline policy had liquid cash ($>\$80,000$) and submitted:
  $$\text{Baseline Market Queue:} \quad [[\text{BUY\_PRODUCT}, \text{WHEAT}, 16], [\text{SELL}, \text{WHEAT}, 2], [\text{BUY\_PRODUCT}, \text{FERTILIZER}, 11]]$$
- `FRONTLOAD_ORDERS` reordered the queue to prioritize the sell:
  $$\text{Candidate Market Queue:} \quad [[\text{SELL}, \text{WHEAT}, 2], [\text{BUY\_PRODUCT}, \text{WHEAT}, 16], [\text{BUY\_PRODUCT}, \text{FERTILIZER}, 11]]$$

### 10.2 Market Execution Mechanics
1. **Under Baseline Ordering:**
   - The agent executes `BUY WHEAT 16` first.
   - This purchase consumes market inventory and shifts the market clearing price of wheat **upwards**.
   - When the agent subsequently executes `SELL WHEAT 2`, it sells its wheat at the **inflated post-buy price** ($P_1 > P_0$).
2. **Under Frontloaded Ordering:**
   - The agent executes `SELL WHEAT 2` first, receiving the **uninflated initial price** ($P_0$).
   - Then it executes `BUY WHEAT 16`, driving the price up.
3. **The Empirical Penalty:**
   - Selling before buying the *same commodity* in the same turn deprived the agent of its own demand-induced price spike!
   - At Step 575, this single reordering cost exactly **-$16.00** in terminal margin.
   - At Step 647, the identical pattern cost **-$15.00** in terminal margin.
   - Total loss on Seed `340224`: **-$31.00**.

### 10.3 Simulator Attribution Gap
Why did the Counterfactual Simulator predict a positive marginal advantage ($\Delta M = +\$34$ at step 575)?
- The counterfactual simulator evaluated market lockstep clearing assuming **rival collision priority** (securing quotes before an opponent sells).
- However, when the opponent is not actively dumping rival supply, **intra-agent order sequence price feedback** dominates:
  - Buying before selling the same commodity is advantageous when the buyer has sufficient cash.
  - Frontloading is only advantageous when:
    1. Capital orders would otherwise starve the agent of cash needed to submit a critical buy, OR
    2. An opponent is actively dumping inventory that would crash the price before our sell clears.
- The opportunity detector and candidate generator applied `FRONTLOAD_ORDERS` unconditionally without conditioning on intra-agent multi-order price impact!

---

## 11. Scientific and Architectural Interpretation

### 11.1 What This Experiment Tells Us
1. **Falsification of Unconditional Frontloading:** The hypothesis that reordering market SELL orders ahead of BUY orders is generally non-inferior is **empirically false**. In an endogenous multi-order market, selling after buying the same good captures a higher clearing price.
2. **Execution Architecture Invariant Holds:** The AEC runtime wrapper, backbone adapter, and isolation machinery functioned with zero flaws:
   - Zero illegal actions
   - Zero double-calls
   - Zero shed discards
   - Zero quarantined commits
   - Perfect deterministic replay
3. **Counterfactual Simulator Fidelity Limitation:** A 1-step counterfactual simulation that does not model intra-agent price feedback across coupled orders within the same turn will misestimate the sign of marginal revenue.

### 11.2 What This Experiment Does NOT Tell Us
- It does **not** establish that runtime counterfactual patching is an ineffective architectural concept.
- It does **not** evaluate or invalidate the macro-economic components of AEC (Labor shadow price calculation, Town cycle route compression, Weed dig spatial logistics, or Terminal conversion).
- It does **not** imply that the frozen V3 backbone is defective.
- It demonstrates that a single specific tactical mechanism (`FRONTLOAD_ORDERS`), when applied without intra-basket commodity price awareness, has a negative marginal effect on specific seeds.

---

## 12. Holdout Integrity Certification

- **Partition:** Seeds `340050` through `340199` (150 contiguous seeds).
- **Audit Verification:** Full-text regex scans of all output JSON, CSV, and log files generated by `EXP-AEC-002` confirmed:
  $$\text{Holdout Touches} = 0$$
- **Certification:** The AEC holdout partition remains **completely virgin, touchless, and pristine**.

---

## 13. Cryptographic Provenance and Artifact Hashes

| Artifact | File Location | Cryptographic SHA-256 Hash |
|---|---|---|
| **Protocol Commit** | Git commit | `d6d6ac344662b7e6dcf31af7b781aef0195c70d2` |
| **Control Archive** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| **AEC Config Code** | `aec/config.py` | `240deda295ce68490bf68a1fb046be2905044e78fafafb2a51aeb8b5c2f71f63` |
| **Canonical Config JSON** | Dataclass payload | `db59108d29241534cde9d9a12bdc93c588800be7ad7ec2838cee09efdea5721c` |
| **Preregistration Protocol** | `reports/EXP_AEC_002_PREREGISTRATION_FINAL.md` | `3e861f5f4608b87ae3a295965681612af1a160f94a27d67f1e0e63d351a12585` |
| **Cohort Audit Report** | `reports/EXP_AEC_002_COHORT_AUDIT.md` | `383ff9915c01bfadac5c61b9ceb70d300eaac94eebe99302a700fad23021a657` |
| **Execution Manifest** | `experiments/EXP-AEC-002/EXECUTION_MANIFEST.json` | Recorded post-run (`status: COMPLETED`) |
| **Execution Audit** | `experiments/EXP-AEC-002/EXECUTION_AUDIT.json` | Recorded post-run (`OVERALL_AUDIT_PASS: true`) |
| **Summary Statistics** | `experiments/EXP-AEC-002/SUMMARY.json` | Recorded post-run (`result: ACTIVE_NEGATIVE`) |
| **Paired Deltas Table** | `experiments/EXP-AEC-002/PAIRED_DELTAS.csv` | 50 prospective seeds recorded |
| **Committed Patches** | `experiments/EXP-AEC-002/COMMITTED_PATCHES.csv` | 20 verified commits recorded |
| **Telemetry Events** | `experiments/EXP-AEC-002/TELEMETRY_EVENTS.csv` | 70,800 event records |

---

## 14. Governance Directive

In accordance with strict scientific governance:
1. **No post-hoc reruns or parameter tuning** will be conducted on cohort `340200–340249`. This cohort is now **PERMANENTLY CONSUMED**.
2. **The verdict of `ACTIVE_NEGATIVE` is final and frozen.**
3. Architectural work is halted pending explicit user review and direction.
