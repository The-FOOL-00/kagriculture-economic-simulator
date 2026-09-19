# AEC PHASE 012: GROUP 2 RESCUE REPLAY LOG
## Canonical Experiment Ledger of Paired Mirror Matches, Empirical Deltas, and Telemetry

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19 (Forensically Reconciled & Frozen)  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Empirical Control**: Frozen Live Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)  
**Evaluation Protocol**: Paired Common Random Numbers (CRN) Mirror-Seat Evaluation  
**Seed Governance**: Certified Fresh Development Cohorts (`249171..249205`), zero overlap with protected cohorts (`340050..340199`, `214200..214249`, `340300..340349`) or retired cohorts.  
**Total Mirror Matches Executed**: **130 full-horizon matches** (80 pilot matches + 50 formal qualification matches across 35 unique seeds).

---

## 1. Master Experiment Overview & Ledger Summary

| Mechanism | Cohort Stage | Seed Range | Seeds ($N$) | Mirror Matches | Control Configuration | Treatment Configuration | Target Candidates | Exact Sims | Target Commits | Commit Rate | Mean Paired $\Delta$ | Median Paired $\Delta$ | Record (W / L / T) | Final Evidence Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`TOWN_CYCLE`** | Pilot | `249171..80` | 10 | 20 | Frozen Foundation | Control + TOWN_CYCLE | 1,342 | 1,180 | 118 | 8.79% | -423.60 | -74.00 | 3W / 7L / 0T | **FUNCTIONALLY COMPLETE / QUARANTINED** |
| **`EMERGENCY_RECOVERY`** | Pilot | `249171..80` | 10 | 20 | Frozen Foundation | Control + EMERGENCY_RECOVERY | 442 | 442 | 120 | 27.15% | +0.00 | +0.00 | 0W / 0L / 10T | **FUNCTIONALLY COMPLETE / DORMANT** |
| **`OPPONENT_PREEMPT_SELL`** | Pilot | `249171..80` | 10 | 20 | Frozen Foundation | Control + OPPONENT_PREEMPT_SELL | 4,136 | 1,420 | 142 | 3.43% | +112.40 | +36.00 | 6W / 4L / 0T | Pilot Screen Passed |
| **`OPPONENT_PREEMPT_SELL`** | Formal Q1 | `249181..205` | 25 | 50 | Frozen Foundation | Control + OPPONENT_PREEMPT_SELL | 10,674 | 3,750 | 375 | 3.51% | -58.76 | -49.00 | 8W / 16L / 1T | **FUNCTIONALLY COMPLETE / QUARANTINED** |
| **`RESOURCE_CONVERSION`** | Pilot | `249171..80` | 10 | 20 | Frozen Foundation | Control + RESOURCE_CONVERSION | 13,360 | 13,360 | 0 | 0.00% | +0.00 | +0.00 | 0W / 0L / 10T | **FUNCTIONALLY COMPLETE / DORMANT** |
| **TOTALS** | — | — | **65** | **130** | — | — | **29,952** | **20,152** | **755** | — | — | — | — | — |

*Note on Total Counts*: Across the four mechanisms, 65 seed-level evaluations were conducted (35 unique seeds). Each seed-level evaluation ran 2 mirror matches, totaling 130 qualification matches. All completed the full 719-step simulation horizon without crashes or timeouts. (In addition, 2 exploratory single-seed runs exist in `results/phase012`, yielding 134 total match rows on disk).

---

## 2. Pilot Evaluation Replay (N=10 Seeds, 20 Matches per Mechanism)

Cohort: `249171..249180` (N=10 fresh seeds)  
Each seed executes two matches under Common Random Numbers:
- **Match A (Seat 0)**: Treatment = Seat 0, Control = Seat 1
- **Match B (Seat 1)**: Treatment = Seat 1, Control = Seat 0
- **Net Paired Delta**: $\Delta_{\text{net}} = \frac{1}{2} \Big( (R_{\text{trt}, 0} - R_{\text{ctrl}, 1}) + (R_{\text{trt}, 1} - R_{\text{ctrl}, 0}) \Big)$

---

### 2.1 `TOWN_CYCLE` Pilot Replay
- **Mechanism**: `TOWN_CYCLE`
- **Cohort Stage**: Pilot
- **Seed Range**: `249171..249180` (N=10 seeds, 20 mirror matches)
- **Control**: Frozen Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)
- **Treatment**: Control + `TOWN_CYCLE`
- **Candidates Generated**: 1,342
- **Simulations Executed**: 1,180
- **Commits**: 118 (8.79% commit rate)
- **Mean Paired Delta**: **-423.60 pts**
- **Median Paired Delta**: **-74.00 pts**
- **Std Dev / Std Error**: 711.68 pts / 225.05 pts
- **95% Confidence Interval**: `[-932.67, +85.47]`
- **$t$-Statistic ($p$-value)**: -1.882 ($p = 0.0925$)
- **Record**: 3W / 7L / 0T (30.0% Win Rate)
- **Safety Violations**: 0
- **Simulator Horizon**: 719/719 steps completed (100% fidelity)
- **Status**: **FUNCTIONALLY COMPLETE / QUARANTINED** (negative pilot evidence; formal qualification not pursued)

#### Seed-by-Seed Match Log: `TOWN_CYCLE` Pilot

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Result |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | -393.0 | -549.0 | -471.0 | 16 | 2 | Loss |
| 249172 | -18.0 | -18.0 | -18.0 | 12 | 2 | Loss |
| 249173 | -69.0 | -69.0 | -69.0 | 8 | 4 | Loss |
| 249174 | -2096.0 | -2096.0 | -2096.0 | 12 | 2 | Loss |
| 249175 | -1044.0 | -1044.0 | -1044.0 | 12 | 0 | Loss |
| 249176 | -773.0 | -773.0 | -773.0 | 8 | 0 | Loss |
| 249177 | -79.0 | -79.0 | -79.0 | 18 | 2 | Loss |
| 249178 | +111.0 | +111.0 | +111.0 | 10 | 2 | Win |
| 249179 | +47.0 | +47.0 | +47.0 | 10 | 4 | Win |
| 249180 | +156.0 | +156.0 | +156.0 | 12 | 0 | Win |

---

### 2.2 `EMERGENCY_RECOVERY` Pilot Replay
- **Mechanism**: `EMERGENCY_RECOVERY`
- **Cohort Stage**: Pilot
- **Seed Range**: `249171..249180` (N=10 seeds, 20 mirror matches)
- **Control**: Frozen Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)
- **Treatment**: Control + `EMERGENCY_RECOVERY`
- **Candidates Generated**: 442
- **Simulations Executed**: 442
- **Commits**: 120 (27.15% commit rate)
- **Mean Paired Delta**: **+0.00 pts**
- **Median Paired Delta**: **+0.00 pts**
- **Std Dev / Std Error**: 0.00 pts / 0.00 pts
- **95% Confidence Interval**: `[+0.00, +0.00]`
- **$t$-Statistic ($p$-value)**: 0.000 ($p = 1.000$)
- **Record**: 0W / 0L / 10T (100% Tie Rate)
- **Safety Violations**: 0
- **Simulator Horizon**: 719/719 steps completed (100% fidelity)
- **Status**: **FUNCTIONALLY COMPLETE / DORMANT** (safe and functional; baseline already handled emergency states)

#### Seed-by-Seed Match Log: `EMERGENCY_RECOVERY` Pilot

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Result |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | +78.0 | -78.0 | +0.0 | 12 | 2 | Tie |
| 249172 | +0.0 | +0.0 | +0.0 | 12 | 2 | Tie |
| 249173 | +0.0 | +0.0 | +0.0 | 12 | 2 | Tie |
| 249174 | +0.0 | +0.0 | +0.0 | 12 | 2 | Tie |
| 249175 | +0.0 | +0.0 | +0.0 | 12 | 0 | Tie |
| 249176 | +0.0 | +0.0 | +0.0 | 12 | 0 | Tie |
| 249177 | +0.0 | +0.0 | +0.0 | 12 | 2 | Tie |
| 249178 | +0.0 | +0.0 | +0.0 | 12 | 4 | Tie |
| 249179 | +0.0 | +0.0 | +0.0 | 12 | 4 | Tie |
| 249180 | +0.0 | +0.0 | +0.0 | 12 | 4 | Tie |

*Diagnostic Note*: In seed 249171, Seat 0 held an inherent board-asymmetry advantage of +78.0 points in both matches. Because Treatment and Control produced identical actions, Treatment gained +78.0 in Seat 0 and lost -78.0 in Seat 1, netting an exact 0.0 paired delta. Across all 10 seeds, the mechanism produced move-for-move identical actions to baseline.

---

### 2.3 `OPPONENT_PREEMPT_SELL` Pilot Replay
- **Mechanism**: `OPPONENT_PREEMPT_SELL`
- **Cohort Stage**: Pilot (Screening)
- **Seed Range**: `249171..249180` (N=10 seeds, 20 mirror matches)
- **Control**: Frozen Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)
- **Treatment**: Control + `OPPONENT_PREEMPT_SELL`
- **Candidates Generated**: 4,136
- **Simulations Executed**: 1,420
- **Commits**: 142 (3.43% commit rate)
- **Mean Paired Delta**: **+112.40 pts**
- **Median Paired Delta**: **+36.00 pts**
- **Std Dev / Std Error**: 334.61 pts / 105.81 pts
- **95% Confidence Interval**: `[-126.95, +351.75]`
- **$t$-Statistic ($p$-value)**: +1.062 ($p = 0.3158$)
- **Record**: 6W / 4L / 0T (60.0% Win Rate)
- **Safety Violations**: 0
- **Simulator Horizon**: 719/719 steps completed (100% fidelity)
- **Pilot Outcome**: Passed pilot screening hurdle for continuation to Formal Qualification (`formal_q1`).

#### Seed-by-Seed Match Log: `OPPONENT_PREEMPT_SELL` Pilot

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Result |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | -40.0 | -196.0 | -118.0 | 18 | 0 | Loss |
| 249172 | +28.0 | +28.0 | +28.0 | 14 | 0 | Win |
| 249173 | -109.0 | -109.0 | -109.0 | 16 | 2 | Loss |
| 249174 | +962.0 | +962.0 | +962.0 | 8 | 2 | Win |
| 249175 | +307.0 | +307.0 | +307.0 | 12 | 0 | Win |
| 249176 | +218.0 | +218.0 | +218.0 | 8 | 0 | Win |
| 249177 | -83.0 | -83.0 | -83.0 | 26 | 2 | Loss |
| 249178 | +44.0 | +44.0 | +44.0 | 12 | 0 | Win |
| 249179 | -171.0 | -171.0 | -171.0 | 14 | 2 | Loss |
| 249180 | +46.0 | +46.0 | +46.0 | 14 | 0 | Win |

---

### 2.4 `RESOURCE_CONVERSION` Pilot Replay
- **Mechanism**: `RESOURCE_CONVERSION`
- **Cohort Stage**: Pilot
- **Seed Range**: `249171..249180` (N=10 seeds, 20 mirror matches)
- **Control**: Frozen Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)
- **Treatment**: Control + `RESOURCE_CONVERSION`
- **Candidates Generated**: 13,360
- **Simulations Executed**: 13,360
- **Commits**: **0** (0.00% commit rate)
- **Mean Paired Delta**: **+0.00 pts**
- **Median Paired Delta**: **+0.00 pts**
- **Std Dev / Std Error**: 0.00 pts / 0.00 pts
- **95% Confidence Interval**: `[+0.00, +0.00]`
- **$t$-Statistic ($p$-value)**: 0.000 ($p = 1.000$)
- **Record**: 0W / 0L / 10T (100% Tie Rate)
- **Safety Violations**: 0
- **Simulator Horizon**: 719/719 steps completed (100% fidelity)
- **Status**: **FUNCTIONALLY COMPLETE / DORMANT** (margin-first valuation correctly abstained on 100% of candidates)

#### Seed-by-Seed Match Log: `RESOURCE_CONVERSION` Pilot

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Result |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | +78.0 | -78.0 | +0.0 | 0 | 2 | Tie |
| 249172 | +0.0 | +0.0 | +0.0 | 0 | 4 | Tie |
| 249173 | +0.0 | +0.0 | +0.0 | 0 | 2 | Tie |
| 249174 | +0.0 | +0.0 | +0.0 | 0 | 2 | Tie |
| 249175 | +0.0 | +0.0 | +0.0 | 0 | 0 | Tie |
| 249176 | +0.0 | +0.0 | +0.0 | 0 | 0 | Tie |
| 249177 | +0.0 | +0.0 | +0.0 | 0 | 2 | Tie |
| 249178 | +0.0 | +0.0 | +0.0 | 0 | 4 | Tie |
| 249179 | +0.0 | +0.0 | +0.0 | 0 | 4 | Tie |
| 249180 | +0.0 | +0.0 | +0.0 | 0 | 2 | Tie |

*Diagnostic Note*: Across 13,360 opportunities evaluated by margin-first labor valuation, conversion never surpassed direct agricultural cultivation. The compiler abstained on 100% of candidates, producing actions identical to baseline.

---

## 3. Formal Qualification Replay: `OPPONENT_PREEMPT_SELL`

Cohort: `formal_q1` (Seeds `249181..249205`, N=25 fresh seeds, 50 mirror matches)  
Execution Runtime: 2,116.1s (4 parallel workers)  
Control: Frozen Live Foundation  
Treatment: Control + `OPPONENT_PREEMPT_SELL`

### 3.1 Formal Statistical Outcome
- **Mean Paired Delta**: **-58.76 pts**
- **Median Paired Delta**: **-49.00 pts**
- **Standard Error (SE)**: **44.15 pts**
- **Standard Deviation (SD)**: **220.75 pts**
- **95% Confidence Interval**: **[-149.89, +32.37]**
- **$t$-Statistic ($p$-value)**: **-1.331** ($p = 0.1957$)
- **Record**: **8W / 16L / 1T** (Win Rate: **32.0%**)
- **Min / Max Delta**: -697.0 pts / +358.0 pts
- **Target Candidates**: 10,674
- **Target Commits**: 375 (3.51% commit rate)
- **Safety Violations**: 0
- **Simulator Fidelity**: 100.0% (50/50 matches completed 719 steps)
- **Qualification Verdict**: **FAILED FORMAL QUALIFICATION** -> **FUNCTIONALLY COMPLETE / QUARANTINED**

### 3.2 Seed-by-Seed Match Log: `OPPONENT_PREEMPT_SELL` Formal Q1

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Result |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249181 | +358.0 | +358.0 | +358.0 | 14 | 0 | Win |
| 249182 | +269.0 | +269.0 | +269.0 | 20 | 2 | Win |
| 249183 | -224.0 | -224.0 | -224.0 | 14 | 0 | Loss |
| 249184 | +120.0 | +120.0 | +120.0 | 10 | 0 | Win |
| 249185 | -4122.0 | +3637.0 | -242.5 | 19 | 2 | Loss |
| 249186 | +4618.0 | -4164.0 | +227.0 | 9 | 0 | Win |
| 249187 | -103.0 | -103.0 | -103.0 | 22 | 0 | Loss |
| 249188 | -5.0 | -5.0 | -5.0 | 14 | 0 | Loss |
| 249189 | +65.0 | +65.0 | +65.0 | 18 | 2 | Win |
| 249190 | -248.0 | -248.0 | -248.0 | 10 | 2 | Loss |
| 249191 | -169.0 | -169.0 | -169.0 | 16 | 0 | Loss |
| 249192 | -697.0 | -697.0 | -697.0 | 12 | 0 | Loss |
| 249193 | +1024.0 | -1235.0 | -105.5 | 16 | 0 | Loss |
| 249194 | +95.0 | +95.0 | +95.0 | 18 | 0 | Win |
| 249195 | -96.0 | -96.0 | -96.0 | 16 | 2 | Loss |
| 249196 | -169.0 | -169.0 | -169.0 | 28 | 0 | Loss |
| 249197 | -301.0 | -301.0 | -301.0 | 14 | 2 | Loss |
| 249198 | -49.0 | -49.0 | -49.0 | 16 | 0 | Loss |
| 249199 | -46.0 | -46.0 | -46.0 | 18 | 4 | Loss |
| 249200 | -12.0 | -12.0 | -12.0 | 18 | 2 | Loss |
| 249201 | +0.0 | +0.0 | +0.0 | 4 | 2 | Tie |
| 249202 | -261.0 | -105.0 | -183.0 | 16 | 6 | Loss |
| 249203 | -206.0 | -206.0 | -206.0 | 20 | 0 | Loss |
| 249204 | +4080.0 | -3588.0 | +246.0 | 7 | 0 | Win |
| 249205 | +7.0 | +7.0 | +7.0 | 6 | 0 | Win |

---

## 4. Stage Attribution & Authoritative Evidence

Under scientific governance:
1. **Authoritative Qualification Standard**: The 25-seed `formal_q1` cohort is the authoritative qualification test for `OPPONENT_PREEMPT_SELL`. The earlier +112.40 pilot result was an exploratory screening signal and cannot be cited as proof of live advantage.
2. **Quarantine Justification**: Because `OPPONENT_PREEMPT_SELL` failed to demonstrate positive incremental economic value in the formal cohort (-58.76 pts, 8W / 16L / 1T), it is definitively quarantined.
3. **Pilot Quarantine Justification**: For `TOWN_CYCLE`, `EMERGENCY_RECOVERY`, and `RESOURCE_CONVERSION`, pilot outcomes (-423.60, +0.00, +0.00) demonstrated that formal qualification was not warranted. They are quarantined or classified dormant without expending prospective seeds.
