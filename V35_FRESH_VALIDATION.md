# V35 Fresh Development Validation Report

## 1. Executive Summary
To prevent benchmark overfitting and guarantee generalizability, V35 subjected the frozen candidate (`OPENING_WASH25` in `candidates/v35_a7_opening/main.py`) to an expanded 120-paired-leg (240 tournament matches) benchmark. This benchmark rigorously tests performance across:
1. **Development Cohort (Seeds 249675–249679):** 60 paired legs.
2. **Fresh Development Cohort (Seeds 249680–249684):** 60 paired legs never evaluated during earlier candidate exploration.
3. **All Six League Opponents:** `E2_A7`, `E1_V22R1`, `E0_V3`, `E8_DMITRII`, `V54`, `SYN_AGG`.
4. **Both Seats:** Seat 0 and Seat 1 mirrored for every seed-opponent pair.

---

## 2. Dev vs Fresh Cohort Performance Comparison

| Cohort | Policy | Matches | Wins | Losses | Win Rate | Mean Paired Delta | Rescued Losses | Casualties |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dev Cohort** (`249675..249679`) | A7 Baseline | 60 | 53.0 | 7.0 | 88.33% | $0.00 | — | — |
| | **V35 Full (25/25)** | 60 | 57.0 | 3.0 | **95.00%** | **+$4.83** | **8** | **0** |
| **Fresh Cohort** (`249680..249684`) | A7 Baseline | 60 | 55.0 | 5.0 | 91.67% | $0.00 | — | — |
| | **V35 Full (25/25)** | 60 | 60.0 | 0.0 | **100.00%** | **+$115.55** | **9** | **0** |
| **Combined 120-Leg Benchmark** | A7 Baseline | 120 | 108.0 | 12.0 | 90.00% | $0.00 | — | — |
| | **V35 Full (25/25)** | 120 | 117.0 | 3.0 | **97.50%** | **+$60.19** | **17** | **0** |

---

## 3. Fresh Cohort Seed-by-Seed Breakdown

| Fresh Seed | A7 Wins | V35 Wins | Win Rate | Mean Paired Delta | Rescued Mirror Non-Wins | Casualties on Wins |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **249680** | 11.0 / 12 | 12.0 / 12 | **100.0%** | +$4.83 | 2 (Seat 0 & 1 vs A7) | **0** |
| **249681** | 11.0 / 12 | 12.0 / 12 | **100.0%** | +$558.42 | 1 (Decisive mirror rescue) | **0** |
| **249682** | 11.0 / 12 | 12.0 / 12 | **100.0%** | +$4.83 | 2 (Seat 0 & 1 vs A7) | **0** |
| **249683** | 11.0 / 12 | 12.0 / 12 | **100.0%** | +$4.83 | 2 (Seat 0 & 1 vs A7) | **0** |
| **249684** | 11.0 / 12 | 12.0 / 12 | **100.0%** | +$4.83 | 2 (Seat 0 & 1 vs A7) | **0** |

---

## 4. Fresh Validation Findings
1. **Zero Degradation on Fresh Seeds:** The win rate of V35 Full reached **100.00% (60/60)** on the fresh cohort vs 91.67% (55/60) for A7 Baseline (+8.33% net win rate gain).
2. **Deterministic Tie Rescue Across All Seeds:** On every seed where A7 baseline tied itself in the mirror match, V35's 25/25 wash broke the tie in V35's favor by $+\$17.00$ to $+\$28.00$, securing 1.0 full win credit.
3. **Zero Casualty Invariant Preserved:** Across all 120 evaluated match legs (both dev and fresh cohorts), V35 produced exactly **0 casualties** ($N_{\text{casualty}} = 0$). Not a single A7 win was converted into a loss or tie.
