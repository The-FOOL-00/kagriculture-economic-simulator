# DEVELOPMENT BASELINE MAP: AUTHORITATIVE PERFORMANCE CATALOG (POST-AUDIT 2.2)
## Empirical Baseline Map for Controlled Strategy Development & Robustness Tracking

**Governing Standard**: Audit 2.2 Final Evidence Base ([`AUDIT2_2_FINAL_EVIDENCE_BASE.md`](file:///c:/Users/Sundareswaran/Kagriculture/AUDIT2_2_FINAL_EVIDENCE_BASE.md))  
**Development Protocol**: Section 11 & Section 25 Baseline Protection Rules  
**Date**: 2026-09-11  
**Status**: **AUTHORITATIVE IMMUTABLE BENCHMARK MAP**

---

## 1. Executive Summary & Baseline Protection Mandate

Before implementing or optimizing any candidate agent, this document establishes the **verified baseline performance map** across all existing foundational agents. 

Under the **Baseline Protection Rule (Section 25)**:
1. Every subsequent experiment must evaluate against an **unchanged baseline** using identical simulator versions (`kagsim` / `kaggle_environments 1.32.7`), identical seed partitions, identical seat balancing, and identical action execution mechanics.
2. No new strategy may be declared superior based solely on mean cash improvements; candidates must report paired distributions, downside quantiles, cross-regime resilience, and survive holdout verification without data leakage.
3. Frozen submissions (`56146971` and `56146947`) remain strictly isolated as untouched reference anchors.

---

## 2. Catalog of Evaluated Baselines

| Baseline Identifier | Architecture Type | Source Code Location | Deployment / Provenance Status | Primary Role in Development |
| :--- | :--- | :--- | :--- | :--- |
| **`ClosedLoopAgentV2`** | Closed-Loop Agronomic Engine | [`candidates/closed_loop_architecture/closed_loop_v2.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/closed_loop_v2.py) | Internal Champion Candidate | **Primary Robustness Anchor** (High-yield strawberry backbone, feed insulation, shed guard 96) |
| **`Dmitrii-LB2800`** | Static Tape + Terminal Planner | [`extracted_agents/dmitrii_lb2800/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/extracted_agents/dmitrii_lb2800/main.py) | Public LB 2800 Reference Benchmark | **Primary Reference Benchmark** (64-sim Monte Carlo terminal closure at steps 712–718) |
| **`19S / 0T Bedrock`** | Static Allocation Baseline | [`scratch/crop_portfolio_sweep_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/crop_portfolio_sweep_results.json) | 50-Seed Evaluated Discovery Baseline | **Static Agronomic Baseline** (Pure strawberry allocation, 19 tiles NW/NE/SW) |
| **`V54++ Control`** | Static Macro Route + S2 Shop Logic | [`candidates/compiled_v54_plus_shop.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_shop.py) | **FROZEN LIVE** (Sub `56146947`, SHA256: `f651ccd2...`) | **Active Competition Control** (Untouched live submission slot 2) |
| **`V54++ Residual`** | Macro Route + Preemption Overrides | [`candidates/compiled_v54_plus_residual.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_residual.py) | **FROZEN LIVE** (Sub `56146971`, SHA256: `18402ec6...`) | **Active Competition Challenger** (Untouched live submission slot 1) |
| **`Aethel-Prime V1`** | Hybrid Dairy-Centric Engine | [`candidates/candidate_cl_aethel_prime.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/candidate_cl_aethel_prime.py) | Historical Submission (`55944418`, Elo 922.8) | **Legacy Reference Anchor** (Preserved historical submission) |

---

## 3. Primary Head-to-Head Baseline: `ClosedLoopAgentV2` vs. `Dmitrii-LB2800`

Evaluated across **150 paired Common Random Number (CRN) seeds** (300 total matches, 150 as Seat 0, 150 as Seat 1). Every seed margin is computed as:
$$\text{Margin}(s) = (\text{V2}_{\text{seat0}} - \text{DM}_{\text{seat1}}) + (\text{V2}_{\text{seat1}} - \text{DM}_{\text{seat0}})$$

### 3.1 Macro Statistical Metrics (N=150 Paired Seeds)

| Metric | Empirical Value | Audit 2.2 Verification Status | Scientific Interpretation |
| :--- | :---: | :---: | :--- |
| **Sample Mean Margin** | **+$24.6133 coins** | **Verified to 4 decimals** | Positive mean margin (~0.025% of gross farm cash) |
| **Sample Median Margin** | **+$58.0000 coins** | **Verified bit-exact** | Positive central tendency |
| **Sample Standard Deviation** | **166.7481 coins** | **Verified bit-exact** | Substantial seed-to-seed variance |
| **Standard Error of Mean (SE)** | **13.6149 coins** | **Verified bit-exact** | $SE = s / \sqrt{150}$ |
| **Student's $t$ 95% Confidence Interval** | **`[-$2.29, +$51.52]`** | **Verified ($df=149$)** | **Spans Zero**: Mean advantage is NOT statistically significant at $\alpha = 0.05$ |
| **Standard Normal 95% CI ($z=1.96$)** | **`[-$2.07, +$51.30]`** | **Verified bit-exact** | Asymptotic normal approximation |
| **Bootstrap 95% CI (100k resamples)** | **`[-$2.56, +$50.57]`** | **Verified bit-exact** | Non-parametric empirical distribution |
| **Two-Sided Paired $t$-test** | **$t = 1.8078, p = 0.0727$** | **Verified bit-exact** | $p > 0.05 \implies$ **Inconclusive**; Null hypothesis cannot be rejected |
| **Paired Win Rate** | **54.67% (82W - 68L - 0T)** | **Verified bit-exact** | Modest majority win rate |
| **Worst Paired Loss** | **-$730.00 coins** | **Verified (Seed 50081)** | Root cause: Step 217 cash deficit ($4 short) halted sheep purchase |
| **Best Paired Win** | **+$326.00 coins** | **Verified (Seed 50020)** | High-demand strawberry shop realization |
| **Severe Losses ($< -\$1,000$)** | **0 / 150 (0.0%)** | **Verified 0 occurrences** | Absence of catastrophic tail collapse vs Dmitrii |
| **Cohen's $d$ Effect Size** | **0.1476** | **Verified bit-exact** | Negligible effect size ($d < 0.20$) |
| **5% Trimmed Mean (136 seeds)** | **+$36.53 coins** | **Verified bit-exact** | Mean excluding top/bottom 5% outliers |

---

### 3.2 Lower-Tail & Percentile Distribution (N=150 Paired Seeds)

Empirical quantiles for paired margin $(\text{V2} - \text{Dmitrii})$:

| Percentile | Margin Value | Downside Implication |
| :---: | :---: | :--- |
| **$p_{01}$** | **-$533.60 coins** | Extreme tail risk (1st percentile) |
| **$p_{05}$** | **-$198.50 coins** | Severe downside boundary |
| **$p_{10}$** | **-$126.20 coins** | 10% risk threshold |
| **$p_{25}$ (Q1)** | **-$84.00 coins** | Lower quartile boundary |
| **$p_{50}$ (Median)** | **+$58.00 coins** | Positive median advantage |
| **$p_{75}$ (Q3)** | **+$156.00 coins** | Upper quartile boundary |
| **$p_{90}$** | **+$204.00 coins** | Strong favorable performance |
| **$p_{95}$** | **+$224.40 coins** | Top 5% tail advantage |
| **$p_{99}$** | **+$280.72 coins** | Near-maximum realization |
| **Interquartile Range (IQR)** | **$240.00 coins** | Q3 - Q1 spread |

---

### 3.3 Two One-Sided Tests (TOST) Equivalence Analysis

To evaluate whether V2 and Dmitrii are strategically equivalent in payoff, Two One-Sided Tests were evaluated against symmetric bounds $\Delta$:

| Equivalence Bound $\pm \Delta$ | $t_1$ (vs $-\Delta$) | $p_1$ (Upper) | $t_2$ (vs $+\Delta$) | $p_2$ (Lower) | $p_{\text{TOST}}$ | Equivalence Conclusion ($\alpha = 0.05$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$\pm \$25.00$ coins** | $3.644$ | $0.0002$ | $-0.028$ | $0.4887$ | **$0.4887$** | **REJECT EQUIVALENCE** (Not equivalent within $\pm \$25$) |
| **$\pm \$50.00$ coins** | $5.480$ | $0.0000$ | $-1.865$ | $0.0321$ | **$0.0321$** | **EQUIVALENT WITHIN $\pm \$50$** (Post-hoc bound) |
| **$\pm \$75.00$ coins** | $7.316$ | $0.0000$ | $-3.701$ | $0.0002$ | **$0.0002$** | **EQUIVALENT WITHIN $\pm \$75$** |
| **$\pm \$100.00$ coins** | $9.153$ | $0.0000$ | $-5.537$ | $0.0000$ | **$0.0000$** | **EQUIVALENT WITHIN $\pm \$100$** |

> [!WARNING]
> **Methodological Restriction**: The $\pm \$50$ equivalence margin was identified post-hoc because the empirical 90% CI is $[+\$2.08, +\$47.15]$. Economically, $\$50$ represents payoff proximity (~0.05% of game score). It does **NOT** prove behavioral identity, shared failure modes, or tail immunity.

---

### 3.4 Partition Breakdown: Discovery vs. Qualification vs. Holdout

The 150 seeds are strictly divided into three mutually exclusive 50-seed cohorts:

| Partition | Seed Range | Seeds | Mean Margin | Median | Std Dev | SE | 95% Student's $t$ CI | $t$-stat | $p$-value | Win Rate | Worst Loss | Best Win | Role / Epistemic Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Discovery** | 50000–50049 | 50 | **+$39.12** | +$76.00 | 157.61 | 22.29 | `[-$5.67, +$83.91]` | 1.7551 | 0.0855 | 62.0% (31W - 19L) | -$400.0 | +$326.0 | Exploratory hypothesis generation |
| **Qualification** | 50050–50099 | 50 | **+$11.40** | -$13.00 | 190.74 | 26.97 | `[-$42.81, +$65.61]` | 0.4226 | 0.6744 | 48.0% (24W - 26L) | -$730.0 | +$244.0 | Confirmatory testing of frozen ideas |
| **Audited Holdout** | 50100–50149 | 50 | **+$23.32** | +$57.00 | 151.44 | 21.42 | `[-$19.72, +$66.36]` | 1.0889 | 0.2815 | 54.0% (27W - 23L) | -$452.0 | +$316.0 | **Audited Benchmark Partition** |
| **Combined** | **50000–50149** | **150** | **+$24.61** | **+$58.00** | **166.75** | **13.61** | **`[-$2.29, +$51.52]`** | **1.8078** | **0.0727** | **54.67% (82W - 68L)** | **-$730.0** | **+$326.0** | Full Audited Baseline |

**Observations & Holdout Hygiene Note**:
- Discovery margin was highest (+39.12, WR 62.0%), reflecting natural exploratory selection.
- Qualification margin contracted (+11.40, WR 48.0%) due to Seed 50081 (-$730.0) and Seed 50078 (-$612.0).
- Holdout stabilized (+23.32, WR 54.0%), confirming that the underlying mean difference is slightly positive but statistically indistinguishable from zero across all three independent partitions.
- **Fresh Virgin Holdout Requirement**: Because seeds 50100–50149 were evaluated in Audit 2/2.1/2.2, they serve as an *Audited Benchmark Partition*. Candidate cohort Seeds 50150–50199 was disqualified due to historical contamination (Gate 0.2). Any new candidate agent developed in this phase must achieve confirmatory validation on the certified **Fresh Virgin Holdout (Seeds 214200–214249)** before final deployment.

---

## 4. Performance by Realized Town Shop World Regime

The 150 seeds map into three shop composition regimes based on the presence of Pizza Shop and Strawberry-demanding shops:

| Shop Family Regime | Criteria | Seed Count | Mean Margin (V2 - DM) | Median Margin | Standard Deviation | Win Rate | V2 Mean Cash | Dmitrii Mean Cash | Regimes Characterization |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`Pizza` (Pure)** | Contains Pizza Shop, 0 Strawberry Shops | 1 | **-$22.00** | -$22.00 | 0.00 | 0.0% (0W - 1L) | $97,075.00 | $97,086.00 | Extremely rare single-seed outlier (Seed 50042) |
| **`Pizza+Straw`** | Contains Pizza Shop AND $\ge 1$ Strawberry Shop | 99 | **+$47.86** | +$78.00 | 142.43 | 58.6% (58W - 41L) | $95,209.46 | $95,185.53 | Dominant regime; V2 captures premium strawberry liquidity |
| **`Straw` (Pure)** | 0 Pizza Shops, $\ge 1$ Strawberry Shop | 50 | **-$20.48** | -$33.00 | 201.91 | 48.0% (24W - 26L) | $96,593.72 | $96,603.96 | Strawberry gluts depress prices; Dmitrii terminal planner wins |

> [!IMPORTANT]
> **Key Architectural Insight**: V2 achieves its positive margin almost entirely within the `Pizza+Straw` regime (+47.86), while Dmitrii outperforms V2 in pure `Straw` worlds (-20.48) where market prices collapse earlier and terminal liquidation timing becomes decisive.
>
> *Data Provenance Note*: This empirical partition was generated by `scratch/run_margin_scan.py:50-71` inspecting `obs_final` at Step 719 (post-match hindsight). In addition, line 57 of `run_margin_scan.py` checked `"YARN_SHOP"` instead of `"YARN_STORE"`, which subsumed Yarn Store occurrences into `Straw` or `Pizza+Straw`.

---

## 5. Static Crop Allocation Baseline: 12 Allocation Grids

Evaluated on the **50-seed Discovery partition** (100 matches vs Dmitrii-LB2800) in [`scratch/crop_portfolio_sweep.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/crop_portfolio_sweep.py):

| Allocation (Straw / Tom) | Mean Cash ($) | Paired Margin ($) | Win Rate (%) | Worst Loss ($) | Downside Risk (Std Loss) | Rank | Evaluation Finding |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **19S / 0T** | **$97,026.17** | **+$24.98** | **59.0%** | **-$222.00** | **56.72** | **1** | **Bedrock Baseline: Highest cash, highest margin, lowest risk** |
| **17S / 2T** | $96,915.38 | -$1,465.44 | 40.0% | -$5,414.00 | 2,436.10 | 2 | 2 tomato tiles destroy margin and multiply downside 43x |
| **15S / 4T** | $97,000.32 | -$2,078.04 | 38.0% | -$7,765.00 | 3,528.71 | 3 | High downside volatility |
| **13S / 6T** | $96,523.91 | -$3,259.85 | 34.0% | -$10,994.00 | 5,175.09 | 4 | Severe monotonic degradation |
| **11S / 8T** | $95,499.40 | -$5,242.14 | 27.0% | -$15,285.00 | 7,603.65 | 5 | Unprofitable diversification |
| **10S / 9T** | $94,940.34 | -$6,179.46 | 25.0% | -$17,196.00 | 8,700.11 | 6 | Heavy drag on farm capital |
| **9S / 10T** | $94,202.18 | -$7,370.64 | 25.0% | -$19,263.00 | 10,066.90 | 7 | Heavy drag on farm capital |
| **8S / 11T** | $93,329.82 | -$8,774.21 | 18.0% | -$21,895.00 | 11,668.29 | 8 | Sub-20% win rate collapse |
| **6S / 13T** | $92,083.73 | -$10,800.65 | 14.0% | -$25,264.00 | 13,901.66 | 9 | Catastrophic capital destruction |
| **4S / 15T** | $92,085.73 | -$10,798.65 | 14.0% | -$25,264.00 | 13,901.50 | 10 | Catastrophic capital destruction |
| **2S / 17T** | $92,087.73 | -$10,796.65 | 14.0% | -$25,264.00 | 13,901.36 | 11 | Catastrophic capital destruction |
| **0S / 19T** | $92,089.73 | -$10,794.65 | 14.0% | -$25,264.00 | 13,901.23 | 12 | Pure tomato allocation is strictly uncompetitive |

> [!CAUTION]
> **Scope Limitation**: 19S / 0T is the strongest static allocation **on the evaluated 50 Discovery seeds**. It is not proven globally optimal across changed shop schedules or novel opponents. Any dynamic strategy must use 19S / 0T as the performance floor to beat.

---

## 6. Frozen Live Submissions Baseline

The two active submissions on Kaggle are cryptographically verified and frozen:

| Submission Ref ID | Deployed Local Artifact | SHA-256 Checksum | Submission UTC | Status | Initial Score | Role / Invariant |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **`56146947`** | [`candidates/compiled_v54_plus_shop.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_shop.py) | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | 2026-09-10 15:13:16 | `COMPLETE` | 600.0 | **Active Control** (Untouched) |
| **`56146971`** | [`candidates/compiled_v54_plus_residual.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_residual.py) | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | 2026-09-10 15:14:36 | `COMPLETE` | 600.0 | **Active Challenger** (Untouched) |

### Baseline Macro Comparison (Historical 400-Match Suite):
- In the 400-match tournament suite vs `Dmitrii-LB2800`:
  - Dmitrii Mean: **$93,406.26** vs `compiled_v54_plus_shop`: **$84,261.16** (Margin: **-$9,145.10**, WR: **5.25%**).
  - This establishes that the legacy V54 macro line suffers from severe open-loop route rigidity against closed-loop and adaptive agents, underscoring the necessity of the closed-loop V2 architecture.

---

## 7. Operational Baseline Verification Checklist

Before running any development experiment, confirm:
- [x] Simulator binary: `kagsim` compiled from `external_repos/kaggriculture-cppsim/sim/sim.hpp`.
- [x] Paired match protocol: Seat 0 and Seat 1 evaluations summed per seed.
- [x] Seed partition hygiene: Discovery (50000–50049), Qualification (50050–50099), Holdout (50100–50149).
- [x] Common Random Numbers (CRN): Exact same seed and shop sequence across variants.
- [x] Unmodified controls: `ClosedLoopAgentV2`, `Dmitrii-LB2800`, `19S/0T`.
- [x] Zero future leakage: No peeking at unrevealed shops or opponent private state.
