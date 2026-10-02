# DEVELOPMENT EXPERIMENT PROTOCOL V1 (PROSPECTIVE SPECIFICATION)

## Authoritative Pre-Registered Experimental Protocols for Development Experiments `EXP-DEV-001` Through `EXP-DEV-005`

**Protocol Identifier**: `DEVELOPMENT-PROTOCOL-V1.0`  
**Governing Standard**: Prospective Scientific Pre-Registration & Anti-Publication Bias Covenant  
**Date Established**: 2026-09-11  
**Status**: **FROZEN PROSPECTIVE SPECIFICATION — PRE-EXPERIMENTAL HOLD STATE**  

---

## 1. Epistemic Provenance Statement & Preregistration Distinction

Under Section 10 and Section 14 of the Development Gate Protocol, we explicitly distinguish between historical provenance and prospective scientific freeze:

### 1.1 Historical Preregistration
> **Status**: **NOT ESTABLISHED (HISTORICALLY UNAVAILABLE)**  
> Because the earlier experimental registry (`DEVELOPMENT_EXPERIMENT_REGISTRY.md`) was untracked in Git prior to the Gate 0.1/0.2 audits, there is no immutable external timestamp certifying that the experimental hypotheses for `EXP-DEV-001` through `EXP-DEV-005` were recorded prior to the current session. We explicitly refrain from claiming historical preregistration.

### 1.2 Prospective Protocol Freeze
> **Status**: **ESTABLISHED & CRYPTOGRAPHICALLY FROZEN NOW**  
> Prior to the execution of any development experiment, this document locks all hypotheses, controls, evaluation partitions, sample sizes, primary success criteria, secondary metrics, stop criteria, analysis procedures, and multiple-testing corrections.
> 
> **Zero experimental runs for `EXP-DEV-001` through `EXP-DEV-005` have been executed on disk.** This protocol constitutes an immutable, prospective experimental pre-registration.

---

## 2. Mandatory Statistical Invariants & Governance Rules

Under Section 12 of the Governing Protocol, all subsequent experimental execution must strictly adhere to the following statistical invariants:

1. **Holdout Inviolability**:
   - The certified virgin holdout partition (**Seeds 214200–214249**, $N=50$) cannot be inspected, loaded, simulated, or evaluated prior to final candidate selection.
   - Holdout seeds **cannot** be used to tune hyper-parameters, adjust decision thresholds, or choose among candidate variants.
   - If a candidate fails on the holdout, it is permanently marked `FAILED`. Re-tuning on the same holdout is strictly prohibited.
2. **Exploratory vs. Confirmatory Separation**:
   - Results obtained on the Discovery partition (Seeds 50000–50049) are strictly exploratory.
   - P-values, confidence intervals, or performance deltas observed during Discovery cannot be reported as confirmatory evidence.
   - Formal confirmation requires advancing to the Qualification partition (Seeds 50050–50099) with frozen code.
3. **Multiple-Testing Control**:
   - Every tested code branch, parameter sweep, heuristic variation, or algorithmic trial must be logged in the centralized registry.
   - When evaluating $K$ candidate variants simultaneously against a control, significance thresholds must be adjusted using the Bonferroni correction ($\alpha / K$) or the Benjamini-Hochberg False Discovery Rate (FDR) procedure.
4. **Mandatory Reporting of Negative Results**:
   - Failed, inconclusive, or retracted experiments must remain permanently recorded with equal visibility to positive findings. Cherry-picking favorable seeds or suppressing negative trials is a catastrophic scientific violation.
5. **Zero-Leakage Active Containment**:
   - All experimental executions must run within the `ActiveContainmentSandbox` specified in [`DEVELOPMENT_GATE_0_3_LEAKAGE_VERIFICATION.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_GATE_0_3_LEAKAGE_VERIFICATION.md).
   - Any agent attempting file I/O, `gc` inspection, lookahead simulation, or network access will be immediately disqualified.

---

## 3. Seed Partition Architecture

All development experiments will be evaluated on standardized, mutually exclusive Common Random Number (CRN) partitions:

| Partition Role | Seed Range | Sample Size ($N$) | Evaluation Format | Governance Rule |
| :--- | :---: | :---: | :---: | :--- |
| **Discovery Partition** | `50000` to `50049` | 50 Seeds (100 matches) | Paired Seat 0 + Seat 1 | Exploratory hypothesis generation and parameter space mapping. |
| **Qualification Partition** | `50050` to `50099` | 50 Seeds (100 matches) | Paired Seat 0 + Seat 1 | Confirmatory validation of frozen candidate variants. Zero hyperparameter tuning. |
| **Audited Benchmark Partition** | `50100` to `50149` | 50 Seeds (100 matches) | Paired Seat 0 + Seat 1 | Cross-validation against historical Audit 2.2 benchmark data. |
| **Certified Virgin Holdout** | `214200` to `214249` | 50 Seeds (100 matches) | Paired Seat 0 + Seat 1 | Final pre-deployment qualification. Evaluated exactly ONCE per candidate. |

---

## 4. Pre-Registered Experiment Specifications (`EXP-DEV-001` to `EXP-DEV-005`)

---

### 4.1 EXP-DEV-001 (RQ1: Dynamic Crop Portfolio Allocation)

- **Research Question**: Does conditioning crop planting on revealed town shops at Day 3 (Step 72) and Day 6 (Step 144) outperform the static 19S/0T Strawberry Bedrock without increasing downside tail variance?
- **Formal Hypothesis ($H_1$)**: A dynamic policy that switches allocation to complementary crops (e.g. carrots on Pet Cafe worlds, wheat on Bakery worlds) upon shop revelation achieves a mean paired margin $\Delta \mu > +\$50.00$ over static 19S/0T in `ClosedLoopAgentV2`, with non-inferior 5th percentile downside risk ($p_{05}(\text{Candidate}) \ge p_{05}(\text{Control}) - \$50.00$).
- **Null Hypothesis ($H_0$)**: $\Delta \mu \le \$0.00$ or $p_{05}$ downside degrades by $> \$50.00$.
- **Candidate Treatment**: `dev_001_dynamic_portfolio` (conditional crop selection on Days 3 and 6).
- **Baseline Controls**: 
  1. `ClosedLoopAgentV2` (Static 19S/0T Strawberry Bedrock)
  2. `Dmitrii-LB2800` ([`extracted_agents/dmitrii_lb2800/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/extracted_agents/dmitrii_lb2800/main.py))
- **Primary Success Metric**: Mean Paired Margin vs `ClosedLoopAgentV2` in coins ($\text{Margin}(s) = (\text{Cand}_0 - \text{Ctrl}_1) + (\text{Cand}_1 - \text{Ctrl}_0)$).
- **Secondary Metrics**:
  - $p_{05}$ lower-tail quantile margin
  - Paired win rate (%)
  - Gross farm cash ($)
  - Worst paired loss ($)
- **Sample Size & Tiered Advancement**:
  1. *Stage 1 (Discovery)*: 50 seeds (50000–50049, 100 matches). Gating threshold: $\Delta \mu > +\$50.00$ and $p_{05} \ge -\$200.00$.
  2. *Stage 2 (Qualification)*: 50 seeds (50050–50099, 100 matches) with frozen code. Gating threshold: $t > 1.96$ ($p < 0.05$).
  3. *Stage 3 (Holdout)*: 50 seeds (214200–214249, 100 matches). Evaluated once prior to submission release.
- **Stop Criteria**:
  - If Discovery mean margin $< \$0.00$, mark `FAILED` and terminate.
  - If worst single-seed loss $< -\$800.00$, mark `FAILED` (tail risk unacceptable).

---

### 4.2 EXP-DEV-002 (RQ2: Rebuilt Shop Information Value Quantification)

- **Research Question**: What is the exact empirical Value of Information (VoI) of each successive town shop unlock across the 8 unlock steps (Days 3..24) when measured under authoritative C++ simulator definitions?
- **Formal Hypothesis ($H_1$)**: Shop revelations on Day 3 (Step 72) and Day 6 (Step 144) possess actionable economic value ($\text{VoI} \ge \$100.00$ per episode), whereas revelations after Day 12 (Step 288) have near-zero marginal decision value ($\text{VoI} < \$25.00$) due to biological harvest cycle horizons.
- **Null Hypothesis ($H_0$)**: $\text{VoI}(t) < \$25.00$ for all $t \ge 72$.
- **Candidate Treatment**: `dev_002_shop_voi_evaluator` (policy conditioned on realized shop unlocks at step $t$).
- **Baseline Control**: Open-loop expected value policy assuming unconditional base uniform shop draw probabilities.
- **Primary Metric**: Empirical Expected Value of Information:
  $$\text{VoI}(t) = \mathbb{E}_{\text{Shops}} \left[ V(\pi^*(\text{Shop}_{1..t})) \right] - \mathbb{E} \left[ V(\pi_0) \right]$$
- **Secondary Metrics**:
  - Policy divergence rate (frequency of action changes conditioned on shop $t$)
  - Price impact prediction accuracy
- **Sample Size**: 100 Seeds (Discovery 50000–50049 + Qualification 50050–50099).
- **Stop Criteria**: If total VoI across all regimes $< \$50.00$, conclude shop adaptation does not justify architectural complexity and decommission shop branching.

---

### 4.3 EXP-DEV-003 (RQ3: Controlled Spatial and Action Slack Utilization)

- **Research Question**: Does utilizing physically vacant farm tiles on Days 11–12 with secondary crop cycles that receive dedicated watering and harvesting actions generate positive net cash without cannibalizing the core strawberry schedule?
- **Formal Hypothesis ($H_1$)**: Deploying a secondary crop cycle on vacant SE quadrant tiles between Days 11 and 16 with pre-scheduled worker actions generates net incremental cash $\Delta \text{Cash} \ge +\$1,500.00$ with zero reduction in core strawberry yield ($Y_{\text{straw}}(\text{Cand}) \ge Y_{\text{straw}}(\text{Base})$).
- **Null Hypothesis ($H_0$)**: $\Delta \text{Cash} \le \$0.00$ or core strawberry yield drops by $\ge 1$ unit.
- **Candidate Treatment**: `dev_003_controlled_slack_arm` (scheduled additive planting with dedicated action budget).
- **Baseline Control**: Unmodified `ClosedLoopAgentV2` with identical worker hiring and cash expenditure.
- **Primary Metric**: Net Incremental Profit:
  $$\Delta \text{Profit} = \text{Added Crop Revenue} - (\text{Seed Cost} + \text{Added Water/Harvest Action Marginal Cost})$$
- **Secondary Metrics**:
  - Core strawberry harvested units
  - Dawn liquidity buffer at Day 12
  - Shed overflow discard count
- **Sample Size**: 50 Discovery seeds (50000–50049), advancing to 50 Qualification seeds (50050–50099).
- **Stop Criteria**: If core strawberry yield decreases on any single seed, mark `FAILED` immediately (cannibalization violation).

---

### 4.4 EXP-DEV-004 (RQ4: World Regime Downside Resilience and Cash Buffer)

- **Research Question**: Does dynamic liquidity reservation prior to livestock stocking (Step 216) prevent catastrophic downside collapses on tight-cash seeds (such as Seed 50081)?
- **Formal Hypothesis ($H_1$)**: Enforcing a strict $\$1,000$ cash reservation floor prior to Day 9 pasture stocking raises the 5th percentile paired margin by $p_{05} \ge +\$100.00$ and prevents the Seed 50081 loss ($-\$730.00 \to \ge -\$200.00$), while incurring a mean opportunity cost $\le \$25.00$ across all seeds.
- **Null Hypothesis ($H_0$)**: $p_{05}$ does not improve by $\ge \$50.00$ or mean margin degrades by $> \$30.00$.
- **Candidate Treatment**: `dev_004_robust_hedging` (dynamic liquidity floor $\text{CashReserve} \ge \$1,000$ at Step 216).
- **Baseline Control**: Base `ClosedLoopAgentV2` liquidity rule.
- **Primary Metric**: $p_{05}$ paired margin quantile and Seed 50081 realization.
- **Secondary Metrics**:
  - Mean paired margin across 150 seeds
  - Livestock acquisition success rate (%)
  - Dawn cash at Step 216
- **Sample Size**: 150 Paired Seeds (Discovery 50 + Qualification 50 + Audited Benchmark 50).
- **Stop Criteria**: If mean margin drops by $> \$35.00$ across the ensemble, liquidity reservation is over-conservative; mark `FAILED`.

---

### 4.5 EXP-DEV-005 (RQ5: Monte Carlo Terminal Liquidation Integration)

- **Research Question**: Does integrating a 64-simulation Monte Carlo terminal planner at Steps 712–718 into `ClosedLoopAgentV2` extract late-game worker liquidation value and close the realization gap with `Dmitrii-LB2800` on pure Strawberry worlds?
- **Formal Hypothesis ($H_1$)**: Incorporating a terminal lookahead planner over Steps 712–718 yields an incremental terminal cash gain $\Delta \text{Cash}_{712..718} \ge +\$35.00$ with per-step latency $\le 800\text{ms}$ under the active containment sandbox.
- **Null Hypothesis ($H_0$)**: Terminal gain $\le \$15.00$ or step timeout occurs.
- **Candidate Treatment**: `dev_005_mc_terminal_closure` (Monte Carlo terminal planner overlay at Steps 712–718).
- **Baseline Control**: Base `ClosedLoopAgentV2` (executing default pass/harvest policy at Steps 712–718).
- **Primary Metric**: Net Terminal Cash Delta at Steps 712–718 in dollars.
- **Secondary Metrics**:
  - Maximum per-step computational latency (ms)
  - Paired margin on pure Strawberry worlds ($N=50$)
  - Total match win rate vs Dmitrii
- **Sample Size**: 150 Paired Seeds (Discovery 50 + Qualification 50 + Audited Benchmark 50).
- **Stop Criteria**: If maximum step latency exceeds $800\text{ms}$ (Kaggle timeout risk) or terminal gain $< \$20.00$, mark `FAILED`.

---

## 5. Protocol Change Control & Immutability Standard

1. **Frozen Document**: Following creation, this file is cryptographically hashed (SHA-256) and recorded in `DEVELOPMENT_PROTOCOL_FREEZE.md`.
2. **Version Control Lock**: This file is committed to Git prior to executing any script that generates data for `EXP-DEV-001` through `EXP-DEV-005`.
3. **No Retroactive Modifications**: No hypothesis, metric, seed partition, or stop threshold may be modified after viewing experimental outcomes. If a change is required, it must be logged as a formal amendment in a separate document with explicit causal justification.
