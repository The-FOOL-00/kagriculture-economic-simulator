# V32 P4 CLOSED-LOOP EVALUATION REPORT

Date: 2026-09-23.
Evaluation Screen: 10 seeds (`249675–249684`) × 6 opponents (`E0_V3`, `E2_A7`, `E3_V25P3`, `E6_W72`, `E7_W2015`, `E8_DMITRII`) × 2 seats = **120 legs**.
Runner: `scripts/v32_p3_evaluate.py` (deterministic argmax).
Records: `results/v32_p4_eval_arm1.jsonl`.

## 1. Summary Performance Across Screen Panel

| Stat | P4 Arm 1 (Balanced Joint BC) | P3 Mixture-BC (3e-4) | P3 Mixture-BC (3e-3) | A7 Reference (P3 Screen) |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Terminal Cash** | **$108.39** | $467.00 | $60.00 | $90,965.00 |
| **Median Terminal Cash** | **$0.50** | $448.00 | $0.00 | $88,470.00 |
| **Standard Deviation** | **$309.98** | $405.00 | $322.00 | — |
| **Min – Max Cash** | **$0.00 – $2,246.00** | $0.00 – $1,243.00 | $0.00 – $2,829.00 | $59,603 – $142,499 |
| **Win Rate** | **0.0% (0/120)** | 0.0% (0/120) | 0.0% (0/120) | 100% |
| **Step-0 Wash Executed**| **120/120 (100.0%)** | **0/120 (0.0%)** | **0/120 (0.0%)** | **100.0%** |
| **Step-0 Market Action** | `[BUY30, SELL30]` | `[SELL30, BUY30]` | `[SELL30, BUY30]` | `[BUY30, SELL30]` |

## 2. Breakdown by Opponent

| Opponent | Mean Cash | Median Cash | Max Cash | Win Rate |
| :--- | :--- | :--- | :--- | :--- |
| **E0_V3** | $140.40 | $20.50 | $918.00 | 0/20 (0%) |
| **E2_A7** | $190.80 | $12.00 | $2,246.00 | 0/20 (0%) |
| **E3_V25P3** | $45.50 | $4.00 | $321.00 | 0/20 (0%) |
| **E6_W72** | $125.50 | $0.00 | $941.00 | 0/20 (0%) |
| **E7_W2015** | $146.80 | $0.00 | $1,607.00 | 0/20 (0%) |
| **E8_DMITRII** | $1.40 | $0.00 | $25.00 | 0/20 (0%) |

## 3. Breakdown by Seat
- **Seat 0**: Mean cash = $114.50, Median = $0.00.
- **Seat 1**: Mean cash = $102.20, Median = $1.50.
No material seat bias observed.

## 4. Evaluation Analysis & Interpretation
1. **Critical Market Mechanism Repaired**: Unlike all P3 models which failed the opening wash on 100% of legs (0/120), P4 Arm 1 executed the valid opening wash `[BUY30, SELL30]` on **120 out of 120 legs (100.0%)**.
2. **Opening Capital Injection Verified**: In step 0, the policy successfully locks in opening liquidity, jumping to $3,000 cash at turn 1.
3. **Compounding Economic Drift**: Despite opening capital recovery, the policy suffers from downstream behavioral-cloning drift:
   - Without execution masking or online reinforcement, the unmasked policy makes out-of-distribution choices in middle-game turns (e.g. invalid `PLACE COW`, premature building, non-vital market purchases).
   - This drains capital over 720 steps, producing a terminal mean of $108.39 and 0 wins.
4. **Economic Verdict**: The critical market ordering bottleneck is **SOLVED**, but closed-loop economic recovery remains **INSUFFICIENT**.
