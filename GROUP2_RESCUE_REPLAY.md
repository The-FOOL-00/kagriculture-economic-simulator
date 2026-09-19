# AEC PHASE 012: GROUP 2 RESCUE REPLAY LOG
## Comprehensive Record of Paired Mirror Matches, Empirical Deltas, and Telemetry

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Empirical Control**: Frozen Live Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)  
**Evaluation Protocol**: Paired Common Random Numbers (CRN) Mirror-Seat Evaluation  
**Seed Governance**: Certified Fresh Development Cohorts (`249171..249205`), zero overlap with protected cohorts (`340050..340199`, `214200..214249`, `340300..340349`) or retired cohorts.

---

## 1. Pilot Evaluation Replay (N=10 Seeds, 20 Matches per Mechanism)

Cohort: `249171..249180` (N=10 fresh seeds)  
Each seed executes two matches:
- Match 1 (Seat 0): Treatment = Seat 0, Control = Seat 1
- Match 2 (Seat 1): Treatment = Seat 1, Control = Seat 0
- Net Paired Delta: $\Delta_{\text{net}} = \frac{1}{2} \Big( (R_{\text{trt}, 0} - R_{\text{ctrl}, 1}) + (R_{\text{trt}, 1} - R_{\text{ctrl}, 0}) \Big)$

### 1.1 `TOWN_CYCLE` Pilot Replay
- Execution Runtime: 974.3s (4 parallel workers)
- Telemetry: 1,342 target candidates, 118 target commits (8.79% commit rate) across 10/10 seeds
- **Mean Paired Delta**: **-423.60 pts** (SE = 225.05, 95% CI `[-932.67, +85.47]`, $t=-1.88$)
- **Median Paired Delta**: **-74.00 pts**
- **Record**: 3W / 7L / 0T (30.0% Win Rate)

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Commits (Target / Total) | Result |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | -393.0 | -549.0 | -471.0 | 16 / 18 | Loss |
| 249172 | -18.0 | -18.0 | -18.0 | 12 / 14 | Loss |
| 249173 | -69.0 | -69.0 | -69.0 | 8 / 12 | Loss |
| 249174 | -2096.0 | -2096.0 | -2096.0 | 12 / 14 | Loss |
| 249175 | -1044.0 | -1044.0 | -1044.0 | 12 / 12 | Loss |
| 249176 | -773.0 | -773.0 | -773.0 | 8 / 8 | Loss |
| 249177 | -79.0 | -79.0 | -79.0 | 18 / 20 | Loss |
| 249178 | +111.0 | +111.0 | +111.0 | 10 / 12 | Win |
| 249179 | +47.0 | +47.0 | +47.0 | 10 / 14 | Win |
| 249180 | +156.0 | +156.0 | +156.0 | 12 / 12 | Win |

---

### 1.2 `EMERGENCY_RECOVERY` Pilot Replay
- Execution Runtime: 917.0s (4 parallel workers)
- Telemetry: 442 target candidates, 120 target commits (27.15% commit rate) across 10/10 seeds
- **Mean Paired Delta**: **+0.00 pts** (SE = 0.00, 95% CI `[+0.00, +0.00]`, $t=0.00$)
- **Median Paired Delta**: **+0.00 pts**
- **Record**: 0W / 0L / 10T (100% Tie Rate)

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Commits (Target / Total) | Result |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | +78.0 | -78.0 | +0.0 | 6 / 7 | Tie |
| 249172 | +0.0 | +0.0 | +0.0 | 6 / 8 | Tie |
| 249173 | +0.0 | +0.0 | +0.0 | 6 / 7 | Tie |
| 249174 | +0.0 | +0.0 | +0.0 | 6 / 7 | Tie |
| 249175 | +0.0 | +0.0 | +0.0 | 6 / 6 | Tie |
| 249176 | +0.0 | +0.0 | +0.0 | 6 / 6 | Tie |
| 249177 | +0.0 | +0.0 | +0.0 | 6 / 7 | Tie |
| 249178 | +0.0 | +0.0 | +0.0 | 6 / 8 | Tie |
| 249179 | +0.0 | +0.0 | +0.0 | 6 / 8 | Tie |
| 249180 | +0.0 | +0.0 | +0.0 | 6 / 7 | Tie |

*Diagnostic Note*: In seed 249171, Seat 0 beat Seat 1 by 78 points in both matches, regardless of whether Treatment was Seat 0 or Seat 1. Treatment produced move-for-move identical decisions to the empirical foundation.

---

### 1.3 `OPPONENT_PREEMPT_SELL` Pilot Replay
- Execution Runtime: 921.9s (4 parallel workers)
- Telemetry: 4,136 target candidates, 142 target commits (3.43% commit rate) across 10/10 seeds
- **Mean Paired Delta**: **+112.40 pts** (SE = 105.81, 95% CI `[-126.95, +351.75]`, $t=+1.06$)
- **Median Paired Delta**: **+36.00 pts**
- **Record**: 6W / 4L / 0T (60.0% Win Rate)

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Commits (Target / Total) | Result |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | -40.0 | -196.0 | -118.0 | 18 / 18 | Loss |
| 249172 | +28.0 | +28.0 | +28.0 | 14 / 14 | Win |
| 249173 | -109.0 | -109.0 | -109.0 | 16 / 18 | Loss |
| 249174 | +962.0 | +962.0 | +962.0 | 8 / 10 | Win |
| 249175 | +307.0 | +307.0 | +307.0 | 12 / 12 | Win |
| 249176 | +218.0 | +218.0 | +218.0 | 8 / 8 | Win |
| 249177 | -83.0 | -83.0 | -83.0 | 26 / 28 | Loss |
| 249178 | +44.0 | +44.0 | +44.0 | 12 / 12 | Win |
| 249179 | -171.0 | -171.0 | -171.0 | 14 / 16 | Loss |
| 249180 | +46.0 | +46.0 | +46.0 | 14 / 14 | Win |

---

### 1.4 `RESOURCE_CONVERSION` Pilot Replay
- Execution Runtime: 955.8s (4 parallel workers)
- Telemetry: 13,360 target candidates, 0 target commits (0.00% commit rate) across 0/10 seeds
- **Mean Paired Delta**: **+0.00 pts** (SE = 0.00, 95% CI `[+0.00, +0.00]`, $t=0.00$)
- **Median Paired Delta**: **+0.00 pts**
- **Record**: 0W / 0L / 10T (100% Tie Rate)

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Commits (Target / Total) | Result |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 249171 | +78.0 | -78.0 | +0.0 | 0 / 2 | Tie |
| 249172 | +0.0 | +0.0 | +0.0 | 0 / 4 | Tie |
| 249173 | +0.0 | +0.0 | +0.0 | 0 / 2 | Tie |
| 249174 | +0.0 | +0.0 | +0.0 | 0 / 2 | Tie |
| 249175 | +0.0 | +0.0 | +0.0 | 0 / 0 | Tie |
| 249176 | +0.0 | +0.0 | +0.0 | 0 / 0 | Tie |
| 249177 | +0.0 | +0.0 | +0.0 | 0 / 2 | Tie |
| 249178 | +0.0 | +0.0 | +0.0 | 0 / 4 | Tie |
| 249179 | +0.0 | +0.0 | +0.0 | 0 / 4 | Tie |
| 249180 | +0.0 | +0.0 | +0.0 | 0 / 2 | Tie |

*Diagnostic Note*: Across 13,360 opportunities evaluated by margin-first labor valuation, conversion never beat raw product liquidation. The compiler abstained on 100% of candidates, exactly matching baseline.

---

## 2. Formal Qualification Replay: `OPPONENT_PREEMPT_SELL`

Cohort: `formal_q1` (Seeds `249181..249205`, N=25 fresh seeds, 50 mirror matches)  
Execution Runtime: 2,116.1s (4 parallel workers)  
Telemetry: 10,674 target candidates, 375 target commits (3.51% commit rate) across 25/25 seeds

### 2.1 Formal Statistical Outcome
- **Mean Paired Delta**: **-58.76 pts**
- **Standard Error (SE)**: **44.15 pts**
- **95% Confidence Interval**: **[-149.89, +32.37]**
- **t-Statistic**: **-1.331** ($p = 0.1958$)
- **Median Paired Delta**: **-49.00 pts**
- **Record**: **8W / 16L / 1T** (Win Rate: **32.0%**)
- **Min / Max Delta**: -697.0 pts / +358.0 pts
- **Downside Tail (Worst Seed)**: -697.0 pts (Seed 249192)
- **Safety Violations**: 0
- **Simulator Fidelity**: 100.0%

### 2.2 Seed-by-Seed Match Log

| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Commits (Target / Total) | Result |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 249181 | +358.0 | +358.0 | +358.0 | 14 / 14 | Win |
| 249182 | +269.0 | +269.0 | +269.0 | 20 / 22 | Win |
| 249183 | -224.0 | -224.0 | -224.0 | 14 / 14 | Loss |
| 249184 | +120.0 | +120.0 | +120.0 | 10 / 10 | Win |
| 249185 | -4122.0 | +3637.0 | -242.5 | 19 / 21 | Loss |
| 249186 | +4618.0 | -4164.0 | +227.0 | 9 / 9 | Win |
| 249187 | -103.0 | -103.0 | -103.0 | 22 / 22 | Loss |
| 249188 | -5.0 | -5.0 | -5.0 | 14 / 14 | Loss |
| 249189 | +65.0 | +65.0 | +65.0 | 18 / 20 | Win |
| 249190 | -248.0 | -248.0 | -248.0 | 10 / 12 | Loss |
| 249191 | -169.0 | -169.0 | -169.0 | 16 / 16 | Loss |
| 249192 | -697.0 | -697.0 | -697.0 | 12 / 12 | Loss |
| 249193 | +1024.0 | -1235.0 | -105.5 | 16 / 16 | Loss |
| 249194 | +95.0 | +95.0 | +95.0 | 18 / 18 | Win |
| 249195 | -96.0 | -96.0 | -96.0 | 16 / 18 | Loss |
| 249196 | -169.0 | -169.0 | -169.0 | 28 / 28 | Loss |
| 249197 | -301.0 | -301.0 | -301.0 | 14 / 16 | Loss |
| 249198 | -49.0 | -49.0 | -49.0 | 16 / 16 | Loss |
| 249199 | -46.0 | -46.0 | -46.0 | 18 / 22 | Loss |
| 249200 | -12.0 | -12.0 | -12.0 | 18 / 20 | Loss |
| 249201 | +0.0 | +0.0 | +0.0 | 4 / 6 | Tie |
| 249202 | -261.0 | -105.0 | -183.0 | 16 / 22 | Loss |
| 249203 | -206.0 | -206.0 | -206.0 | 20 / 20 | Loss |
| 249204 | +4080.0 | -3588.0 | +246.0 | 7 / 7 | Win |
| 249205 | +7.0 | +7.0 | +7.0 | 6 / 6 | Win |

---

## 3. Comprehensive Pilot + Formal Combined Evaluation

For `OPPONENT_PREEMPT_SELL` across all 35 fresh development seeds (`249171..249205`):
- Total Matches: 70 mirror matches
- Total Candidates: 14,810
- Total Commits: 517 (3.49% commit rate)
- Combined Mean Paired Delta: **-9.84 pts**
- Win / Loss / Tie: **14W / 20L / 1T** (40.0% Win Rate)
- Conclusion: Under rigorous formal qualification on certified fresh cohorts, `OPPONENT_PREEMPT_SELL` does not sustain statistical dominance over the frozen live foundation. Per Governance §34, it is classified as **`FUNCTIONALLY COMPLETE / QUARANTINED`**.
