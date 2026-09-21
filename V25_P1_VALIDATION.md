# V25 Prototype P1 (Capital/Labor Planner) Validation Report

## 1. Candidate Overview
* **Candidate**: `V25_P1_MACRO` (`candidates/v25_p1_macro.py`)
* **Hypothesis**: Replacing opening capital lockup and executing in-place chores during worker idle periods improves terminal reward.
* **Cohort**: Discovery Cohort (Seeds `249430..249449`, 20 seeds $\times$ 2 mirrored seats = 40 matches).

## 2. Experimental Results vs Standalone V3

| Metric | Measured Value | Benchmark Criteria | Status |
|---|---|---|---|
| **Matches Evaluated** | 40 | 40 | Complete |
| **Mean Paired Delta** | -55.33 | $> 0.0$ | **FAILED** |
| **Median Paired Delta** | +284.50 | - | Positive |
| **Record (W / L / T)** | 16W - 8L - 16T | Win $>$ Loss | Passed (16 > 8) |
| **Win Percentage** | 40.0% | $> 50\%$ | Failed |
| **Tail Loss Floor** | -4,023.00 | $> -50,000$ | Passed |
| **Candidate Mean Reward** | 88,345.2 | - | - |
| **Baseline Mean Reward** | 88,400.5 | - | - |

## 3. Diagnostic Analysis
While P1 showed isolated gains on several seeds, uncoordinated chore execution across full 720 turns occasionally produced slight inventory clutter before terminal drops, leading to an overall negative mean paired delta (-55.33). P1 does not meet the preregistered promotion threshold on its own.
