# DEVELOPMENT GATE 0.1 — EXPERIMENT AUDIT REPORT
## Audit of Historical Retractions, Pre-Registered Development Experiments (RQ1–RQ5), and Partition Integrity

**Gate Protocol**: Development Gate 0.1 Pre-Experiment Integrity Audit  
**Target Document**: [`DEVELOPMENT_EXPERIMENT_REGISTRY.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_EXPERIMENT_REGISTRY.md)  
**Governing Standard**: Section 13, 14, 15, and 16 Experimentation & Partition Rules  
**Date**: 2026-09-11  
**Status**: **AUTHORITATIVE AUDIT REPORT**

---

## 1. Primary Audit Verdict on Experiment Registry

### **VERDICT: READY WITH CORRECTIONS**

### **Core Finding**:
1. **Historical Integrity Confirmed**: All seven historical audit retractions (Tomato/Pizza alpha, shop transition model, no-slack impossibility, Step 696 causality, V2 global superiority, $800 hiring collapse, 100% physical agronomic identity) are **100% preserved in `DEVELOPMENT_EXPERIMENT_REGISTRY.md` under `RETRACTED` status**. Zero discredited historical claims have been revived.
2. **Pre-Registration Criteria Specified A Priori**: All five pre-registered development experiments (`EXP-DEV-001` through `EXP-DEV-005`) specify clear hypotheses, treatments, controls, primary metrics, sample sizes, and stop conditions **before execution**. None of the criteria depend on observing experimental results post-hoc.
3. **Methodological Defect in EXP-DEV-005**: `EXP-DEV-005` conflated two orthogonal interventions (Monte Carlo terminal planning at Steps 712–718 AND the Step 217 livestock liquidity buffer) into a single hypothesis. Under Section 20 factorial design rules, these must be decoupled: the Step 217 cash buffer belongs strictly to `EXP-DEV-004`, while `EXP-DEV-005` must isolate Monte Carlo terminal closure alone.
4. **Seed Partition Hygiene & Contamination Status**: Discovery (50000–50049), Qualification (50050–50099), and Holdout (50100–50149) partitions are mutually exclusive. However, because seeds 50100–50149 were evaluated in Audit 2/2.1/2.2 for the 150-seed baseline, they represent an **Audited Benchmark Partition**. True out-of-distribution validation for new agents will require an untouched fresh holdout cohort (e.g. seeds 50150–50199).

---

## 2. Audit of Historical Experiments (`EXP-HIST-01` to `EXP-HIST-08`)

| Experiment ID | Registered Title / Topic | Registered Status | Correct Status? | Verification Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **`EXP-HIST-01`** | V2 vs Dmitrii 150-Seed Paired Macro Study | **INCONCLUSIVE** | **YES** | Student's $t$ 95% CI `[-$2.29, +$51.52]` spans zero; $p = 0.0727 > 0.05$. Null hypothesis cannot be rejected. Not superior, not equivalent. |
| **`EXP-HIST-02`** | Static Crop Portfolio Sweep (12 Allocations) | **CONFIRMED (Discovery Scoped)** | **YES** | 19S/0T ranked #1 strictly on the evaluated 50 Discovery seeds. Monotonic degradation of tomato confirmed. |
| **`EXP-HIST-03`** | Day-11 Tomato Specialization on Pizza Worlds | **RETRACTED** | **YES** | Seed 50042 (+$3,942) confirmed cherry-picked outlier; 6-seed ensemble was -$5,382.67; 18/18 sweeps negative. Permanently dead. |
| **`EXP-HIST-04`** | Shed Headroom Threshold 88 $\to$ 96 Repair | **CONFIRMED** | **YES** | V2 threshold 96 safely preserved feed and fertilizer reserves compared to V1's threshold 88. |
| **`EXP-HIST-05`** | Additive Resource Slack Investigation | **RETRACTED** | **YES** | Script `run_additive_investigation.py` never watered or harvested crops and hired unbudgeted hands daily. Prior negative proof dead. |
| **`EXP-HIST-06`** | Closed-Loop V3 Adaptive Generalization | **FAILED** | **YES** | Beat Dmitrii on Discovery (+264.46), tied on Qual ($0.00), collapsed on Holdout (-$41.64 vs V2, 4% WR, worst loss -$2,082). |
| **`EXP-HIST-07`** | Step 696 Order Truncation Causality | **RETRACTED** | **YES** | Cash diverged at Step 164; sheep purchase failed at Step 217; already down -$292 before Step 696. Truncation was a symptom. |
| **`EXP-HIST-08`** | $800 Dawn Hiring Collapse Narrative | **RETRACTED** | **YES** | Replay 107543042 proved dawn cash was $9,847, hired 9 hands, paid $88 Fibonacci. Claim was a parser bug (`units` vs `hands`). |

**Integrity Finding**: 8/8 historical entries are perfectly aligned with the post-Audit-2.2 evidence base. Zero historical errors were revived.

---

## 3. Audit of Pre-Registered Development Experiments (`EXP-DEV-001` to `EXP-DEV-005`)

### 3.1 EXP-DEV-001 (RQ1: Dynamic vs Static Crop Portfolio)
- **Hypothesis**: Conditioning planting on revealed town shops (Days 3 & 6) outperforms static 19S/0T strawberry baseline without increasing downside tail variance.
- **Treatment**: `dev_001_dynamic_portfolio`.
- **Control**: Static 19S/0T Strawberry Bedrock (`ClosedLoopAgentV2`).
- **Primary Metric**: Paired Margin $(\text{Variant} - \text{Control})$ in coins.
- **Secondary Metrics**: $p_{05}$ lower-tail quantile, Win Rate (%), Total Farm Cash ($).
- **Sample Size & Partition**: Tiered: 50 Discovery $\to$ 50 Qual $\to$ 50 Holdout.
- **Stop Condition**: Fail if Discovery margin $< 0$ or worst loss $< -\$500$. Advance only if margin $> +\$50$ and $p_{05}$ non-inferior.
- **A Priori Status**: **VERIFIED PRE-SPECIFIED**. Criteria were defined before running.

### 3.2 EXP-DEV-002 (RQ2: Rebuilt Shop Information Value / VoI)
- **Hypothesis**: Quantifying incremental economic value of shop revelation across 8 unlock steps (Days 3..24) using authoritative simulator definitions.
- **Treatment**: Decision policy conditioned on real shop draws (C++ `sim.hpp:127-137`).
- **Control**: Open-loop expected value policy assuming base uniform draw probabilities.
- **Primary Metric**: $\text{VoI}(t) = \mathbb{E}[V | \text{Shop}_t] - \mathbb{E}[V]$.
- **Sample Size**: 100 seeds (Discovery + Qualification).
- **Stop Condition**: If $\text{VoI} < \$50$ across all regimes, mark inconclusive.
- **A Priori Status**: **VERIFIED PRE-SPECIFIED**.

### 3.3 EXP-DEV-003 (RQ3: Controlled Spatial & Action Slack)
- **Hypothesis**: Utilizing physical vacant tiles on Days 11–12 with properly watered and harvested secondary cycles generates positive net terminal cash without cannibalizing core strawberry revenue.
- **Treatment**: Controlled additive crop schedule with dedicated worker action allocation.
- **Control**: Unmodified `ClosedLoopAgentV2` with identical worker count and baseline planting.
- **Primary Metric**: Net incremental profit $\Delta \text{Profit} = \text{Added Revenue} - (\text{Seed Cost} + \text{Added Water/Harvest Cost})$.
- **Sample Size**: 50 Discovery $\to$ 50 Qualification.
- **Stop Condition**: Fail if core strawberry yield drops by $\ge 1$ unit or net profit is negative.
- **A Priori Status**: **VERIFIED PRE-SPECIFIED**.

### 3.4 EXP-DEV-004 (RQ4: World Regime Downside Resilience)
- **Hypothesis**: Enforcing a $1,000 cash floor at Day 9 dawn (Step 216) protects livestock acquisition on tight cash seeds (e.g. Seed 50081), raising $p_{05}$ margin.
- **Treatment**: Dynamic liquidity reservation rule ($\text{CashReserve} \ge \$1,000$ prior to Day 9 pasture stocking).
- **Control**: Base `ClosedLoopAgentV2` liquidity rule.
- **Primary Metric**: Seed 50081 margin, $p_{05}$ margin across 150 seeds.
- **Sample Size**: 150 paired seeds.
- **Stop Condition**: Fail if mean margin drops by $> \$30$ across the ensemble.
- **A Priori Status**: **VERIFIED PRE-SPECIFIED**.

### 3.5 EXP-DEV-005 (RQ5: Micro-Architectural Dissection)
- **Stated Hypothesis in Document**: "Monte Carlo terminal planning at Steps 712–718 and liquidity buffer at Step 217 isolate Dmitrii's advantage without adopting static macro tape."
- **Methodological Flaw**: **Conflated Interventions**.
  - Testing both the MC terminal planner AND the Step 217 liquidity buffer simultaneously makes it impossible to attribute observed performance deltas to either component.
  - The Step 217 cash buffer is already the explicit treatment of `EXP-DEV-004`.
- **Required Correction**: Decouple `EXP-DEV-005`. It must isolate strictly:
  - **Treatment**: 64-simulation Monte Carlo terminal closure (`ShopClosure`) at Steps 712–718.
  - **Control**: Base `ClosedLoopAgentV2` executing PASS at Steps 712–718.
  - **Metric**: Net cash delta at Steps 712–718, step latency ($<800$ms).

---

## 4. Audit of Seed Partitions

### 4.1 Partition Boundaries
- **Discovery**: Seeds 50000–50049 ($N=50$)
- **Qualification**: Seeds 50050–50099 ($N=50$)
- **Holdout**: Seeds 50100–50149 ($N=50$)
- **Mathematical Disjointness**:
  $$[50000, 50049] \cap [50050, 50099] \cap [50100, 50149] = \emptyset$$
  The three sets share zero seed overlap.

### 4.2 Historical Contamination & Epistemic Status of Holdout
- **Critical Finding**: Seeds 50100–50149 were previously evaluated during Audit 2, Audit 2.1, and Audit 2.2 in `scratch/v2_dmitrii_margin_scan.json` and `scratch/v3_three_dataset_validation.json`.
- Specific seed characteristics (e.g. Seed 50112 worst loss -$452.00; Seed 50113 win +$316.00) are known to the engineering team.
- **Governing Rule**: Seeds 50100–50149 must be classified as an **Audited Benchmark Partition**. While they remain a clean holdout for historical V2 (which was frozen before evaluating them), any *new* agent developed in this phase must eventually be validated against a **Fresh Virgin Holdout Cohort (Seeds 50150–50199)** before final competition deployment.

---

## 5. Summary of Required Corrections for Experiment Registry

1. **Decouple EXP-DEV-005**: Remove the Step 217 liquidity buffer from EXP-DEV-005; restrict EXP-DEV-005 exclusively to the Monte Carlo terminal planner at Steps 712–718.
2. **Clarify Holdout Status**: Formally designate Seeds 50100–50149 as the "Audited Benchmark Holdout", and specify that final confirmation before deployment requires a fresh, uninspected seed cohort (Seeds 50150–50199).
3. **Re-state Success Threshold Rationale**: Add explicit justification for the $+\$50$ margin threshold in EXP-DEV-001 as representing the upper bound of the empirical TOST equivalence window.
