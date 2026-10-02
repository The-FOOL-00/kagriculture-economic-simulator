# V39 Statistical Validation — Paired Hypothesis Testing & Bootstrap Bounds

## 1. Overview
This document formalizes the statistical validation of **V39** ([`candidates/v39_live_targeted/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v39_live_targeted/main.py)) versus frozen production baseline **V35** across:
1. Direct head-to-head paired matches (20 matches across 10 safe seeds, both seats).
2. 100 paired benchmark league matches (10 safe seeds $\times$ 5 benchmark opponents $\times$ both seats).
3. 17 live competition replay counterfactuals (6 losses, 11 narrow wins).

---

## 2. Direct Head-to-Head Evaluation (V39 vs V35)

| Metric | Measured Value | Significance |
| :--- | :---: | :--- |
| **Total Matches** | 20 | 10 Seeds (5 Dev + 5 Fresh) $\times$ Both Seats |
| **V39 Wins** | **20 (100.0%)** | Clean sweep |
| **V35 Wins** | **0 (0.0%)** | Zero wins against V39 |
| **Ties** | **0 (0.0%)** | Zero ties |
| **Mean Margin** | **+$491.70** | Liquidation price capture advantage |
| **Exact Binomial $p$-value** | **$9.54 \times 10^{-7}$** | $p < 0.0001$ (Statistically definitive) |

---

## 3. Paired Benchmark League Evaluation (100 Matches)

### 2x2 Contingency Matrix (V39 vs V35 Outcomes)

```text
                     V35 WIN        V35 LOSS / TIE
  V39 WIN              97                 1  (Rescue)
  V39 LOSS / TIE        0 (Casualty)       2
```

### Key Statistical Parameters

| Metric | V35 Baseline | V39 Candidate | $\Delta$ (V39 - V35) | 95% Bootstrap CI |
| :--- | :---: | :---: | :---: | :---: |
| **Win Rate** | 97.0% (97/100) | **98.0% (98/100)** | **+1.0%** | [-3.0%, +5.0%] |
| **Rescues ($b$)** | — | **1** | +1 | `E2_A7` Seed 249679 Seat 0 |
| **Casualties ($c$)**| — | **0** | **0** | **Zero casualties** |
| **Preserved Wins** | — | **97 / 97** | **100.0%** | All V35 wins intact |
| **Mean Cash Delta** | — | — | **+$67.59** | **[+$43.02, $+92.10]** |
| **Median Cash Delta**| — | — | **+$2.00** | Non-negative median |

### Opponent Breakdown

| Opponent | V35 Wins | V39 Wins | Net Rescues | Mean Cash Delta |
| :--- | :---: | :---: | :---: | :---: |
| **`E2_A7`** | 19 / 20 | **20 / 20** | **+1** | **+$185.60** |
| **`E1_V22R1`** | 20 / 20 | **20 / 20** | 0 | **+$213.70** |
| **`E8_DMITRII`** | 18 / 20 | 18 / 20 | 0 | -$26.20 |
| **`V54`** | 20 / 20 | 20 / 20 | 0 | -$11.30 |
| **`SYN_AGG`** | 20 / 20 | 20 / 20 | 0 | -$23.85 |
| **TOTAL** | **97 / 100** | **98 / 100** | **+1** | **+$67.59** |

---

## 4. Live Counterfactual Replay Cohort (17 Matches)

| Cohort | Matches | Baseline Margin | V39 CF Margin | Net Cash Delta | Outcome Effect |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Ep 113183263 (Yassine Chritt)** | 1 | -$791.0 | -$160.0 | **+$631.0** | Deficit collapsed by 80% |
| **Ep 113164394 (junxing peng)** | 1 | -$1,988.0 | -$1,384.0 | **+$604.0** | Deficit collapsed by 30% |
| **Ep 113153701 (Validation)** | 1 | -$640.0 | -$71.0 | **+$569.0** | Deficit collapsed by 89% |
| **Other Losses (Ep 113166778, etc.)** | 3 | -$14,873.0 | -$14,937.0 | -$21.3 | Unchanged |
| **Narrow Wins (<$10k Margin)** | 11 | +$51,939.0 | +$53,827.0 | **+$1,888.0** | **11 / 11 Preserved (0 Casualties)** |

---

## 5. Formal Validation Verdict
1. **Directional Dominance**: In direct competition, V39 is undefeated against V35 (20–0, $p < 10^{-6}$).
2. **Strict Casualty Invariance**: Across 100 benchmark tournament matches and 11 live narrow wins, V39 caused **0 casualties** (0 / 108 wins converted to non-wins).
3. **Strictly Positive Economic Value**: Mean paired cash delta across league tournament is **+$67.59** with a strictly positive 95% bootstrap lower bound of **+$43.02**.
