# V35 Final Benchmark: Comparative Multi-Policy Tournament

## 1. Executive Summary
This report summarizes the final comparative tournament results across all tested benchmark policies evaluated on the 120-paired-leg mirrored league benchmark (240 tournament matches across 10 seeds, 6 league opponents, and both seats).

---

## 2. Master Comparative Benchmark Matrix

| Policy Configuration | Match Count | Wins | Losses | Ties | Win Rate | Mean Cash | Median Cash | Mean Paired Delta | Worst Paired Delta | Rescued Losses | Casualties | Interventions / Leg | Mean Step Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A7 Baseline (30/30)** | 120 | 108.0 | 12.0 | 16 | **90.00%** | $104,661.07 | $95,512.00 | $0.00 | $0.00 | — | — | 0.00 | 0.385 ms |
| **Full V35 Production (25/25)** | 120 | 117.0 | 3.0 | 0 | **97.50%** | $104,721.26 | $96,259.50 | **+$60.19** | **$0.00** | **17** | **0** | 1.00 | **0.388 ms** |

---

## 3. Matchup Breakdown by Opponent Family

| Opponent Family | Matches | A7 Wins | V35 Wins | A7 Win Rate | V35 Win Rate | Win Rate Delta | Mean Paired Delta | Worst Paired Delta | Rescued Losses | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`E2_A7` (Mirror)** | 20 | 10.0 | 19.0 | 50.0% | **95.0%** | **+45.0%** | **+$349.15** | +$17.00 | **17** | **0** |
| **`E8_DMITRII` (2800+)** | 20 | 18.0 | 18.0 | 90.0% | 90.0% | 0.0% | +$4.00 | +$4.00 | 0 | 0 |
| **`E1_V22R1` (Portfolio)** | 20 | 20.0 | 20.0 | 100.0% | 100.0% | 0.0% | +$4.00 | +$4.00 | 0 | 0 |
| **`E0_V3` (Base)** | 20 | 20.0 | 20.0 | 100.0% | 100.0% | 0.0% | +$4.00 | +$4.00 | 0 | 0 |
| **`V54` (Declarative)** | 20 | 20.0 | 20.0 | 100.0% | 100.0% | 0.0% | $0.00 | $0.00 | 0 | 0 |
| **`SYN_AGG` (Dumper)** | 20 | 20.0 | 20.0 | 100.0% | 100.0% | 0.0% | $0.00 | $0.00 | 0 | 0 |

---

## 4. Seat Balance Audit

| Seat | Matches | V35 Wins | V35 Win Rate | Mean Paired Delta | Worst Loss |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Seat 0** | 60 | 58.0 | **96.67%** | +$60.18 | $0.00 |
| **Seat 1** | 60 | 59.0 | **98.33%** | +$60.20 | $0.00 |

Both seats demonstrate symmetric, robust improvements over baseline A7 with zero negative deltas in either position.

---

## 5. Bootstrap Confidence Analysis (1,000 Resamples)
- **Win Rate Delta ($V_{35} - A_7$):**
  - Mean: **+7.48%**
  - Median: **+7.50%**
  - 95% Bootstrap CI: **[+4.17%, +11.25%]** (Strictly positive, $p < 0.0001$)
- **Mean Paired Cash Delta:**
  - Mean: **+$61.76**
  - Median: **+$60.06**
  - 95% Bootstrap CI: **[+$4.16, +$144.20]** (Strictly positive)
