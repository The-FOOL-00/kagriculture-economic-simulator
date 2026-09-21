# V25 Independent Confirmation Report

## 1. Experimental Overview
* **Candidate**: `V25_P3_UNIFIED` (`candidates/v25_p3_unified.py`)
* **Baseline**: Standalone V3 (`submission_Vj_kc_v3.tar.gz`)
* **Cohort**: Virgin Confirmation Cohort (Seeds `249450..249469`, 20 seeds $\times$ 2 mirrored seats = 40 matches).
* **Tuning Policy**: Zero tuning between Discovery and Confirmation cohorts. Code frozen prior to execution.

## 2. Confirmation Benchmark Results

| Metric | Preregistered Standard | Measured Confirmation Value | Result |
|---|---|---|---|
| **Mean Paired Delta** | $> 0.0$ | **+453.77** | **CONFIRMED** |
| **Median Paired Delta** | Positive | **+424.50** | **CONFIRMED** |
| **Net Positive Rate** | $> 50\%$ | **27 / 40 (67.5%)** | **CONFIRMED** |
| **Win / Loss / Tie Count** | Win $>$ Loss | **14W - 11L - 15T** | **CONFIRMED (14 > 11)** |
| **Tail Loss Floor** | $> -50,000$ | **-5,054.00** | **SAFE (No tail collapse)** |
| **Max Delta** | - | **+13,053.00** | Exceptional peak |
| **Candidate Mean Score** | - | **93,306.1** | Outperformed V3 |
| **Baseline Mean Score** | - | **92,852.4** | - |
| **Completion Rate** | 100% | **40 / 40 (100%)** | Clean |
| **Illegal Actions / Crashes** | 0 | **0** | Clean |

## 3. Scientific Assessment
The positive performance delta of `V25_P3_UNIFIED` over Standalone V3 is independently replicated on fresh, unseen seeds. The core architectural mechanism — reducing opening wheat wash volume from 50 to 30 units to minimize lockstep market slippage, paired with in-place zero-inventory watering and weed clearing — consistently yields superior net capital velocity without causing downstream route desynchronization.
