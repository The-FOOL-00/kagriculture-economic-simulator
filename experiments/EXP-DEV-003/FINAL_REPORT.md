# EXP-DEV-003 FINAL EXPERIMENT REPORT
## Conditional Opportunity-Value Specialization over V54++ Residual Preemption
**Governing Standard**: Strict Zero-Leakage & Anti-Contamination Covenant  
**Experiment Version**: EXP-DEV-003 Protocol V1.2  
**Date Completed**: 2026-09-14  
**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)  
**Status**: **FINAL — EXPERIMENT TERMINATED**

---

## 1. Executive Verdict

- **Formal Epistemic Classification**: **`FAILURE`**
- **Core Hypothesis Status**: **REJECTED**. The null hypothesis $H_0$ is accepted: the opportunity-value crop specialization overlay provides no incremental economic value over V54++ and severely degrades downside protection.
- **Qualification Eligibility**: **INELIGIBLE**. Candidate `dev_003_conditional_specialization` is permanently rejected for deployment or qualification.
- **Primary Metric**: Paired Mean Final-Cash Delta $\bar{\Delta} = \mathbf{-\$835.32}$ ($t = -1.91, p = 0.062$).
- **Head-to-Head Win Record**: **0 Wins / 4 Losses / 46 Ties** (Win Rate: **0.0%**).
- **Key Insight**: V54++'s macro-route superiority relies on tightly coupled spatial-temporal worker pathing calibrated specifically to Strawberry's 2-day cycle. Overriding crop planting with Tomato without re-pathing workers causes severe harvest delays, premature vine death at Step 552, 7 days of barren tiles, and massive cashflow forfeiture (-$14,696.00 worst loss).

---

## 2. Research Question

> *"Can an information-conditioned agricultural/shop specialization policy add generalizable economic value to the current best V54++ residual-preemption architecture, without materially degrading its downside protection?"*

**Empirical Answer**: **No.** On the certified virgin Discovery partition `245000–245049`, conditional specialization failed to produce a single win across 50 paired seeds (100 matches), lost up to -$14,696.00 on activating seeds, and degraded mean cash by -$835.32.

---

## 3. Core Hypotheses

- **$H_1$ (Specialization Hypothesis)**: A current-information opportunity-value gate can selectively enter high-value specialization states and capture upside while preserving V54++ baseline behavior in ambiguous or unfavorable shop states.
- **$H_0$ (Null Hypothesis)**: The opportunity-value overlay provides no meaningful incremental economic value over V54++ and/or degrades performance.
- **Verdict**: **$H_1$ is REJECTED; $H_0$ is ACCEPTED.**

---

## 4. Frozen Baseline Identity

- **Candidate Baseline**: [`candidates/compiled_v54_plus_residual.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_residual.py)
- **Kaggle Submission Reference**: Submission `56146971`
- **Exact File Size**: `338,100 bytes`
- **Recomputed Authoritative SHA-256**:
  ```text
  18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb
  ```
- **Frozen Properties**: V54++ macroeconomic route tables coupled with verified residual preemption (`preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`).

---

## 5. Treatment Identity

- **Treatment Artifact File**: [`candidates/closed_loop_architecture/dev_003_conditional_specialization.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_003_conditional_specialization.py)
- **Authoritative SHA-256**:
  ```text
  0b152cfa544244fe813ac10c4eec66056c47c5a652f14fe7fbf0a3f7a764c5cb
  ```
- **Architectural Composition**: V54++ Residual Baseline + Conditional Opportunity-Value Gating Overlay.

---

## 6. Preregistered Parameter Freeze (Zero Post-Hoc Tuning)

All parameters were frozen in Protocol V1.2 prior to the first Discovery seed:
- **Opportunity-Value Threshold ($\tau$)**: `1500.0` coins
- **Risk Penalty Multiplier ($\lambda$)**: `0.25`
- **Minimum Liquidity Floor ($L_{\text{min}}$)**: `100.0` coins (Calibrated to V54++ tight early reinvestment schedule)
- **Specialization Tile Allocation ($k_{\text{spec}}$)**: `4` tiles
- **Switching Friction**: `200.0` coins

---

## 7. Seed Provenance & Partition Integrity

- **Discovery Partition**: `245000` to `245049` ($N=50$ contiguous seeds, 100 balanced CRN matches).
- **Provenance Certification**: Certified 100% virgin in [`SEED_PROVENANCE.md`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-003/SEED_PROVENANCE.md) (0 workspace file hits, 0 Git commits, >30k seeds separation from holdout).
- **Quarantined Partitions**:
  - `50050–50099`: EXP-DEV-002 Qualification Partition — **Untouched**.
  - `50100–50149`: Contaminated Historical Benchmark — **Permanently Decommissioned**.
  - `214200–214249`: Final Virgin Holdout (`HOLDOUT-COHORT-V1`) — **Completely Quarantined (0 simulations)**.

---

## 8. Pre-Execution Adversarial Audit Summary

All 14 preflight checks passed prior to execution (documented in [`PRECHECK.md`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-003/PRECHECK.md)):
- Protocol Hash: `f94f9b71a13842915bb20820c610e86cd597d535cb7a80b5a69a5d64dc2d6007` (Verified bit-exact).
- 14-Vector Leakage Suite: PASS (0 legal violations).
- Static AST Audit: PASS (0 prohibited imports/symbols).
- Active Containment Sandbox: PASS (719 legal steps under active containment).

---

## 9. Primary & Secondary Statistical Results

Evaluation performed across $N=50$ paired seeds (100 matches) with seat rotation:

| Metric | Preregistered Threshold | Observed Result | Pass / Fail |
| :--- | :---: | :---: | :---: |
| **Mean Paired Delta ($\bar{\Delta}$)** | $\ge +\$30.00$ | **-$835.32** | **FAIL** |
| **Median Delta** | — | **$0.00** | — |
| **Sample Standard Deviation ($s$)** | — | **$3,092.52** | — |
| **Standard Error ($\text{SE}$)** | — | **$437.35** | — |
| **Student's $t$-statistic** | — | **-1.910** | — |
| **Two-Sided $p$-value** | — | **0.062** | — |
| **95% Confidence Interval** | — | **[-$1,714.21, +$43.57]** | — |
| **10% Trimmed Mean** | $> \$0.00$ | **$0.00** | — |
| **Win Count / Rate** | $\ge 50.0\%$ | **0 wins (0.0%)** | **FAIL** |
| **Loss Count / Rate** | — | **4 losses (8.0%)** | — |
| **Tie Count / Rate** | — | **46 ties (92.0%)** | — |
| **Worst Seed Delta (Min)** | $\ge -\$350.00$ | **-$14,696.00** | **FAIL** |
| **Best Seed Delta (Max)** | — | **$0.00** | — |
| **Total Surplus** | — | **-$41,766.00** | — |
| **Active Seeds ($N_{\text{active}}$)** | $5 \le N \le 35$ | **5 seeds (10.0%)** | **PASS** |

---

## 10. Risk & Tail Distribution Analysis

Percentiles of the paired cash delta distribution:
- **p01**: -$13,270.10
- **p05**: -$8,040.90
- **p10**: $0.00
- **p25**: $0.00
- **p50 (Median)**: $0.00
- **p75**: $0.00
- **p90**: $0.00
- **p95**: $0.00
- **p99**: $0.00

**Tail Interpretation**: The distribution exhibits a heavy negative left tail with zero positive upside. Ninety percent of seeds sit exactly at $0.00$ (baseline preservation), while 8% suffer massive left-tail drawdowns between -$3,653 and -$14,696.

---

## 11. Decision-Quality Telemetry Summary

All 400 decision events (4 checkpoints $\times$ 50 seeds $\times$ 2 seats) were recorded in [`DECISION_EVENTS.csv`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-003/DECISION_EVENTS.csv).
- **Gate E Evaluation**: The gate fired on exactly **5 of 50 seeds** ($10.0\%$), satisfying the selectivity requirement ($5 \le N \le 35$).
- **Selectivity Quality**: The gate fired exclusively on `PIZZA_SHOP` worlds lacking Strawberry shops. However, the economic valuation model overestimated Tomato's realized shop value and failed to anticipate worker route desynchronization.

---

## 12. Shop-Trajectory Analysis

Across the 50 seeds:
- When Strawberry shops (`SMOOTHIE_SHOP`, `ICE_CREAM_SHOP`, `BRUNCH_SPOT`, `FARMERS_MARKET`) were unlocked, the gate correctly rejected Tomato/Carrot/Wheat specialization and preserved Strawberry bedrock.
- When `PIZZA_SHOP` was unlocked without Strawberry shops, the gate fired in 5 seeds. In all 5 cases, specializing in Tomato proved economically inferior to sticking with Strawberry.

---

## 13. Best & Worst Seed Forensic Analysis

- **Best Seed**: **Seed 245025** ($\Delta = \mathbf{\$0.00}$). The gate fired at Step 288 (Day 12), after the Day 11 planting window had closed. Zero physical tile overrides occurred, resulting in identical baseline play and a tie.
- **Worst Seed**: **Seed 245045** ($\Delta = \mathbf{-\$14,696.00}$). Tomato substitution caused a catastrophic lifespan cliff: 4 Tomato tiles died at Step 552 (Day 23) and remained barren for the rest of the game. Candidate harvested only 16 Tomatoes vs baseline's 269 Strawberries, losing over $14k in net realization.

---

## 14. Comparison with V2 Benchmark

- Unlike `ClosedLoopAgentV2`, which lacks market preemption and suffered extensive drift, `dev_003` inherited V54++'s preemption engine.
- On non-activating seeds, `dev_003` matches V54++'s championship-tier performance ($88k+ mean cash).
- However, when specialization activates, `dev_003` suffers from the same vulnerability as DEV-002: crop diversification without spatial route re-optimization collapses farm productivity.

---

## 15. Comparison with EXP-DEV-002

- **DEV-002 (Qualification)**: Failed due to unhedged secondary crop commitments and rigid shop rules ($-\$12.35$ mean delta, worst loss $-\$2,829.80$).
- **DEV-003 (Discovery)**: Enforced strict opportunity valuation and selective gating, successfully achieving 90% baseline preservation. However, on activating seeds, the loss severity was even worse ($-\$14,696.00$) because V54++'s Strawberry macro route is far more productive than V2, making the opportunity cost of forgone Strawberry vastly higher.

---

## 16. Relationship to Live Kaggle Observational Evidence

- **Observational Live Finding**: Submission `56146971` (V54++ Residual) holds Elo `1499.1` (Rank 2368 / 9001), outperforming Control `56146947` by $+46.1$ Elo and $+5,398.4$ mean cash.
- **Strategic Implication**: The live evidence demonstrates that residual market preemption is effective and essential. EXP-DEV-003 proves that attempting to close the remaining gap to Top-10 via ad-hoc crop specialization destroys value. The Top-10 gap is not a failure to plant shop crops; it is a macro-production scheduling problem.

---

## 17. Outlier Sensitivity

- **Total Surplus**: -$41,766.00
- **Mean Excluding Worst Seed**: -$552.45
- **Mean Excluding Best Seed**: -$852.37
- **Mean Excluding Best Two Seeds**: -$870.12
The negative outcome is not driven by a single outlier; all activating seeds that modified tiles lost substantial value.

---

## 18. Epistemic Classification

Under the preregistered Protocol V1.2 criteria:
- Gate A (Mean $\ge +30$): **FAIL** (-$835.32)
- Gate B (Win Rate $\ge 50\%$): **FAIL** (0.0%)
- Gate C (Worst Loss $\ge -350$): **FAIL** (-$14,696.00)
- Gate D (Outlier Non-Dominance): **FAIL** (-$852.37)
- Gate E (5 to 35 Active Seeds): **PASS** (5 active seeds)

**Final Classification**: **`FAILURE`**

---

## 19. Qualification Eligibility

Candidate `dev_003_conditional_specialization` is **COMPLETELY INELIGIBLE** for qualification or deployment. It will not be simulated on the Qualification partition (`50050–50099`) or the Virgin Holdout (`214200–214249`).

---

## 20. Recommended Next Experiment (EXP-DEV-004)

1. **Abandon Ad-Hoc Crop Swapping**: Do not attempt to override crop tiles inside compiled macro routes without re-compiling the underlying spatial pathing routes.
2. **Focus on Pure Route-Level Adaptation or Macro Scaling**: Future experiments should investigate:
   - Dynamic hiring and quadrant expansion timing within V54++.
   - End-game market liquidation optimization and preemption volume tuning.
   - Dedicated, full-game specialized routes compiled from scratch for specific shop archetypes (rather than runtime tile patches).

---

## 21. Required Claim Discipline Statements

1. *"Live observational evidence is consistent with residual preemption being beneficial and motivates controlled testing against the frozen residual baseline."*
2. *"DEV-002 failed to generalize on its Qualification partition."*
3. *"The conditional opportunity-value specialization hypothesis was formally tested on certified virgin seeds 245000–245049 in EXP-DEV-003 and decisively failed."*
4. *"Submission 56146971 remains our sole authoritative, highest-performing frozen deployment asset."*

---

## 22. Stop Condition Compliance

Execution has been immediately stopped following the generation of this Final Report.
- Zero simulations on `214200–214249` (Final Holdout untouched).
- Zero simulations on `50050–50099` (Qualification untouched).
- Zero live Kaggle submissions initiated.
- Zero parameter sweeps or post-hoc optimizations performed.
Awaiting explicit user review and directive.
