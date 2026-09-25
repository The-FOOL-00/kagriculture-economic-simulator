# V36 Independent Final Validation Report

**Harness Standard:** CLEANROOM INDEPENDENT HARNESS EXECUTION  
**Script:** `scripts/v36_independent_validation.py`  
**Execution Timestamp:** 2026-09-24 18:58:22 UTC  
**Total Paired Matches:** 120 matches (240 fresh simulation runs)  
**Independent Verdict:** **FREEZE_V35**  

---

## 1. Executive Summary & Verification

The independent harness executed fresh, untouched instances of `A7_STANDALONE` and `V35_CANDIDATE` on identical initial states without importing any prior results or promotion decisions.

| Metric | A7 Standalone | V35 Candidate | Paired Delta / Net Result | Verification Status |
|:---|:---:|:---:|:---:|:---|
| **Tournament Points** | 108.0 / 120 | **117.0 / 120** | **+9.0 pts** | Confirmed Exactly |
| **Matchup Win Rate** | 90.00% | **97.50%** | **+7.50 pp** | Confirmed Exactly |
| **Rescued Non-Wins** | -- | **17** | +17 non-wins converted | Confirmed Exactly |
| **Casualties** | -- | **0** | **0 casualties** | Confirmed Exactly |
| **Worst Paired Delta** | $0.00 | **+$0.00** | **$0.00 downside** | Confirmed Exactly |
| **Mean Cash Delta** | $0.00 | **+$60.19** | +$60.19/match | Confirmed Exactly |
| **Median Cash Delta** | $0.00 | **+$4.00** | +$4.00/match | Confirmed Exactly |

---

## 2. Independent Gate Audit

| Gate ID | Criterion | Independent Value | Pass / Fail |
|:---|:---|:---:|:---:|
| **G1** | Win Rate Superiority ($WR_{V35} > WR_{A7}$) | 97.50% vs 90.00% | **PASS** |
| **G2** | Zero Casualties ($N_{cas} == 0$) | 0 casualties | **PASS** |
| **G3** | Positive Rescues ($N_{res} > 0$) | 17 rescues | **PASS** |
| **G4** | Bounded Tail Risk ($\Delta_{worst} \ge \$0.00$) | +$0.00 | **PASS** |
| **G5** | Both Seats Robust ($WR_{V35} > WR_{A7}$ on Seat 0 & 1) | Seat 0: 96.7%, Seat 1: 98.3% | **PASS** |
| **G6** | No Opponent Degradation ($WR_{V35} \ge WR_{A7}$ $\forall$ opp) | 0 degraded opponents | **PASS** |
| **G7** | Bootstrap Confidence Positive ($CI_{95, lower} > 0$) | [4.17%, 11.25%] | **PASS** |

---

## 3. Opponent Breakdown (Independent Execution)

| Opponent | Matches | A7 Win Rate | V35 Win Rate | Rescues | Casualties | Mean Delta | Min Delta |
|:---|:---:|:---:|:---:|:---:|:---:|---:|---:|
| `E2_A7` | 20 | 50.0% | 95.0% | 17 | 0 | +$349.15 | +$17.00 |
| `E1_V22R1` | 20 | 100.0% | 100.0% | 0 | 0 | +$4.00 | +$4.00 |
| `E0_V3` | 20 | 100.0% | 100.0% | 0 | 0 | +$4.00 | +$4.00 |
| `E8_DMITRII` | 20 | 90.0% | 90.0% | 0 | 0 | +$4.00 | +$4.00 |
| `V54` | 20 | 100.0% | 100.0% | 0 | 0 | +$0.00 | +$0.00 |
| `SYN_AGG` | 20 | 100.0% | 100.0% | 0 | 0 | +$0.00 | +$0.00 |

---

## 4. Bootstrap Confidence Intervals (2,000 Resamples)

* **Win Rate Delta Mean:** +7.45 pp (Median: +7.50 pp)
* **95% Confidence Interval:** **[4.17%, +11.25%]**
* **Empirical Probability of Superiority ($P(V35 > A7)$):** **100.0%** (100.0%)
* **Mean Cash Delta 95% CI:** [$4.08, $143.78]

---

## 5. Independent Verdict

The independent validation harness confirms without caveat that V35 fulfills all preregistered criteria for production promotion:
* **FINAL VERDICT: FREEZE_V35**
