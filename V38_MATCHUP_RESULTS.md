# V38 Head-to-Head & Tournament Matchup Results

## 1. Overview & Evaluation Protocol

This report documents the exhaustive head-to-head and paired panel tournament evaluations comparing **V38** (Heuristic, BC, and Bounded Residual PPO) directly against the frozen live production baseline **V35**.

### 1.1 Governance & Safeguards
- **Frozen Baseline:** V35 (`candidates/v35_a7_opening/main.py`, SHA-256 `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`) remained strictly untouched.
- **Quarantined Seeds:** Protected holdout cohorts (`214200–214249`, `340090–340199`, `249695–249734`) were 100% untouched.
- **Paired Exact Matching:** Every match was run synchronously across identical seed, opponent, and seat configurations.

---

## 2. Master Tournament Summary

### 2.1 Cohort 1: Dev Benchmark (Seeds 249675..249679)
- **Design:** 5 seeds × 3 opponents (`E2_A7`, `E8_DMITRII`, `SYN_AGG`) × 2 seats = 30 paired scenarios per candidate (120 total matches).

| Candidate Policy | Matches | W / L / T | Points | Win Rate | Mean Cash ($) | Paired Delta vs V35 ($) | Worst Delta ($) | Rescues | Casualties | Mean Interv. |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V35 (Reference)** | 30 | 27 / 3 / 0 | 27.0 | **90.0%** | $113,509.0 | $0.00 | $0.00 | — | — | 1.00 (open) |
| **V38_HEURISTIC** | 30 | 27 / 3 / 0 | 27.0 | **90.0%** | $113,509.0 | $0.00 | $0.00 | 0 | 0 | 0.00 |
| **V38_BC** | 30 | 27 / 3 / 0 | 27.0 | **90.0%** | $113,509.3 | +$0.27 | $0.00 | 0 | 0 | 0.27 |
| **V38_PPO** | 30 | 27 / 3 / 0 | 27.0 | **90.0%** | $113,509.0 | $0.00 | $0.00 | 0 | 0 | 0.00 |

---

### 2.2 Cohort 2: Fresh Held-Out Benchmark (Seeds 249685..249689)
- **Design:** 5 strictly unseen safe seeds × 3 opponents × 2 seats = 30 paired scenarios per candidate (120 total matches).

| Candidate Policy | Matches | W / L / T | Points | Win Rate | Mean Cash ($) | Paired Delta vs V35 ($) | Worst Delta ($) | Rescues | Casualties | Mean Interv. |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V35 (Reference)** | 30 | 30 / 0 / 0 | 30.0 | **100.0%** | $123,199.8 | $0.00 | $0.00 | — | — | 1.00 (open) |
| **V38_HEURISTIC** | 30 | 30 / 0 / 0 | 30.0 | **100.0%** | $123,199.8 | $0.00 | $0.00 | 0 | 0 | 0.00 |
| **V38_BC** | 30 | 30 / 0 / 0 | 30.0 | **100.0%** | $123,199.8 | $0.00 | $0.00 | 0 | 0 | 0.00 |
| **V38_PPO** | 30 | 30 / 0 / 0 | 30.0 | **100.0%** | $123,199.8 | $0.00 | $0.00 | 0 | 0 | 0.00 |

---

## 3. Disaggregated Forensic Breakdown

### 3.1 Opponent Breakdown (Combined Dev + Fresh, N=60 per candidate)

| Opponent | Total Matches | V35 Win Rate | V38_PPO Win Rate | V38_BC Win Rate | Paired Delta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Synthetic Aggressive (`SYN_AGG`)** | 20 | **100.0%** (20/20) | **100.0%** (20/20) | **100.0%** (20/20) | $0.00 |
| **Incumbent A7 (`E2_A7`)** | 20 | **95.0%** (19/20) | **95.0%** (19/20) | **95.0%** (19/20) | $0.00 |
| **Dmitrii Grandmaster (`E8_DMITRII`)** | 20 | **90.0%** (18/20) | **90.0%** (18/20) | **90.0%** (18/20) | +$0.40 (BC) / $0.00 (PPO) |

### 3.2 Analysis of V35 Non-Wins
In 60 paired matches across Dev and Fresh, V35 recorded exactly 3 non-wins (all in Dev):
1. **Seed 249679 vs E2_A7 (Seat 0):**
   - V35: $73,419.0 vs Opp: $73,514.0 (Loss by $95).
   - V38 Heuristic, BC, and PPO: Identical cash ($73,419.0). All policies correctly identified that no macro intervention could bridge the gap without violating safe liquidity floors.
2. **Seed 249677 vs E8_DMITRII (Seat 0):**
   - V35: $92,596.0 vs Opp: $93,752.0 (Loss by $1,156).
   - V38 Heuristic, BC, and PPO: Identical cash ($92,596.0).
3. **Seed 249677 vs E8_DMITRII (Seat 1):**
   - V35: $92,596.0 vs Opp: $93,752.0 (Loss by $1,156).
   - V38 Heuristic, BC, and PPO: Identical cash ($92,596.0).

**Rescue Count:** `0 / 3`. V38 was unable to rescue any V35 loss.
**Casualty Count:** `0 / 57`. V38 never lost any game that V35 won.

### 3.3 Seat Symmetry Analysis

| Seat Position | Matches Evaluated | V35 Win Rate | V38_PPO Win Rate | Seat Asymmetry Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Seat 0 (First Player)** | 30 | 93.3% (28/30) | 93.3% (28/30) | 0.0% |
| **Seat 1 (Second Player)** | 30 | 96.7% (29/30) | 96.7% (29/30) | 0.0% |

Both V35 and V38 demonstrate near-perfect seat symmetry with zero bias or divergence.

---

## 4. Matchup Conclusion
V38 is functionally and competitively identical to V35. While it successfully preserves 100% of V35's stability and avoids all RL-X2 failure modes, **PPO produces 0 additional wins, 0 rescues, and zero statistically meaningful advantage**.
