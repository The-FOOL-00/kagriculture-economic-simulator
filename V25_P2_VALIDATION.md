# V25 Prototype P2 (Production Planner) Validation Report

## 1. Candidate Overview
* **Candidate**: `V25_P2_PRODUCTION` (`candidates/v25_p2_production.py`)
* **Hypothesis**: Dynamic production scheduling across pre-compiled route tapes improves resource deployment.
* **Cohort**: Discovery Cohort (Seeds `249430..249449`, 20 seeds $\times$ 2 mirrored seats = 40 matches).

## 2. Experimental Results vs Standalone V3

| Metric | Measured Value | Benchmark Criteria | Status |
|---|---|---|---|
| **Matches Evaluated** | 40 | 40 | Complete |
| **Mean Paired Delta** | +0.00 | $> 0.0$ | **FAILED (Flat)** |
| **Median Paired Delta** | +0.00 | - | Neutral |
| **Record (W / L / T)** | 0W - 0L - 40T | Win $>$ Loss | Failed |
| **Win Percentage** | 0.0% | $> 50\%$ | Failed |
| **Tail Loss Floor** | -70.00 | $> -50,000$ | Passed |
| **Candidate Mean Reward** | 97,586.1 | - | - |
| **Baseline Mean Reward** | 97,586.1 | - | - |

## 3. Diagnostic Analysis
Because all 41 pre-computed routes in the underlying database share an identical opening 144 steps (`EarlyPlants = 12 Melon, 17 Wheat, 4 Strawberry`), and shop unlocks at day 6 already map deterministically via `_R108_SHOP_ROUTES`, passive route switching without altering opening capital or micro-dispatch produced effectively zero differentiation (+0.00 delta). P2 fails the promotion gate.
