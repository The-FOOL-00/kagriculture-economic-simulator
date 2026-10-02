# KAGGRICULTURE: RECONCILIATION OF INTERNAL RESEARCH CONTRADICTIONS
## Direct Reconciliation of Mutually Contradictory Claims in Post-Submission Research

This document identifies, analyzes, and forensically resolves nine major internal contradictions discovered across the post-submission research reports (R1 through R14).

---

### Contradiction 1: V2 vs Dmitrii Performance — "Statistical Parity" vs "Confirmed Global Superiority"

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | [`research/competitive_breakthrough_architecture_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/competitive_breakthrough_architecture_report.md) (R8) | [`research/v2_dmitrii_residual_profit_map.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v2_dmitrii_residual_profit_map.md) (R14) |
| **Exact Claim** | *"V2 vs Dmitrii-LB2800: Mean margin +$25, 95% CI crosses zero [-$5, +$5]... Performance is at statistical parity."* | *"CLOSED_LOOP_V2 is confirmed globally superior to Dmitrii-LB2800... Mean margin +$25.3, 95% CI [-$2.0, +$51.0], win rate 54.7%."* |
| **Which is Correct?** | **Report A is statistically correct; Report B is statistically overclaimed.** |
| **Evidence** | Independent recalculation of all 150 seeds in `scratch/v2_dmitrii_margin_scan.json` yields: Mean = +$24.61, Standard Error = 13.61, 95% CI = `[-$2.07, +$51.30]`. Because the 95% confidence interval crosses zero ($p = 0.070$), the null hypothesis ($H_0: \mu = 0$) cannot be rejected at the $\alpha = 0.05$ significance level. |
| **Can Both Be True?** | No. While the point estimate favors V2 (+24.6 coins per paired match on a ~$96,000 base), asserting "confirmed global superiority" violates standard statistical inference when the confidence interval spans negative values. |

---

### Contradiction 2: V2 Worst-Case Loss against Dmitrii — -$6,367 / -$1,390 vs -$730

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | [`scratch/v3_three_dataset_validation.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/v3_three_dataset_validation.json) (R12) | [`research/v2_dmitrii_residual_profit_map.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v2_dmitrii_residual_profit_map.md) (R14) |
| **Exact Claim** | Qualification Worst Loss = `-$6,367.0`; Fresh Holdout Worst Loss = `-$1,390.0`. | *"Zero games exhibited catastrophic losses (worst combined loss across all 150 seeds was -$730; 0 / 150 losses exceeded $1,000)."* |
| **Which is Correct?** | **Both are numerically real, but describe completely different quantities without methodological disclosure.** |
| **Evidence** | On Seed 50076, when V2 was in Seat 0, V2 earned $92,225 while Dmitrii in Seat 1 earned $98,592 (single-game margin: `-$6,367`). When roles were reversed on the same seed, V2 in Seat 1 earned $98,638 while Dmitrii in Seat 0 earned $92,181 (single-game margin: `+$6,457`). Combined paired margin: `-$6,367 + $6,457 = +$90.0`. Report A reported single-match margins subject to seat bias; Report B reported combined paired margins $(V2_0 - Dm_1) + (V2_1 - Dm_0)$. |
| **Can Both Be True?** | Yes, under different definitions: single-game seat-unbalanced worst loss is `-$6,367` (driven by severe seat asymmetry on Seed 50076), whereas paired CRN worst loss is `-$730` (Seed 50081). However, conflating them caused confusion regarding whether V2 has catastrophic downside risk. |

---

### Contradiction 3: Closed-Loop V3 Efficacy — "Discovery Breakthrough" vs "Holdout Regression"

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | CID `7ceb96d7...` Implementation Plan & Discovery Log | [`scratch/v3_three_dataset_validation.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/v3_three_dataset_validation.json) (R12) |
| **Exact Claim** | *"V3 achieves +$266.42 paired margin over Dmitrii on Discovery seeds (50000–50049) and beats V2 by +$264.46."* | *"On Fresh Holdout (50100–50149), V3 margin vs Dmitrii is -$37.24; margin vs V2 is -$41.64; win rate vs V2 collapses to 4%."* |
| **Which is Correct?** | **Report B reflects the true generalizable performance; Report A was discovery overfitting.** |
| **Evidence** | In `scratch/v3_three_dataset_validation.json`: Discovery: V3 vs V2 margin = +$264.46 (CI95: 232.83). Qualification: V3 vs V2 margin = $0.00 (CI95: 184.22). Fresh Holdout: V3 vs V2 margin = -$41.64 (CI95: 69.18), Win Rate = 4.0%, Worst Loss = -$2,082.0. |
| **Can Both Be True?** | Yes. This is a textbook manifestation of overfitting to a discovery seed panel. The multi-stage tomato gating captured positive noise on Discovery seeds, tied on Qualification, and strictly degraded performance on Fresh Holdout. |

---

### Contradiction 4: Tomato Specialization — "+$3,942 on Pizza Worlds" vs "Universal Portfolio Collapse"

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | Task Log `task-265.log` & R9 Narrative | [`scratch/true_pizza_sweep_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/true_pizza_sweep_results.json) & [`scratch/crop_portfolio_sweep_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/crop_portfolio_sweep_results.json) (R11) |
| **Exact Claim** | *"Day-11 Tomato specialization generates +$3,942 cash gain in Pizza worlds."* | *"Pure 19S/0T Strawberry strictly dominates all 11 hybrid portfolios. Across all 18 parameter combinations on True Pizza worlds, average delta vs V2 is -$5,382."* |
| **Which is Correct?** | **Report B is the rigorous empirical truth; Report A was cherry-picked.** |
| **Evidence** | `task-265.log` reveals the 6 tested True Pizza seeds: Seed 50003 (-$15,186), Seed 50011 (-$1,011), Seed 50021 (-$12,069), Seed 50026 (+$4,568), Seed 50030 (-$12,540), Seed 50042 (+$3,942). The average across all 6 seeds was `-$5,382.67`. Citing `+$3,942` in isolation was gross cherry-picking from a net-negative distribution. |
| **Can Both Be True?** | Only in the trivial sense that Seed 50042 specifically gained $3,942. As a strategic or policy generalization, Report A is false. |

---

### Contradiction 5: Resource Slack — "Transient Day-11 Vacancies" vs "No Slack Exists Anywhere"

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | [`candidates/closed_loop_architecture/spatial_production_compiler.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/spatial_production_compiler.py) | [`research/slack_capacity_real_option_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/slack_capacity_real_option_report.md) (R13) |
| **Exact Claim** | *"Identified 4 vacant tiles (0,0), (8,0), (9,0), (0,9) and unutilized worker hours on Days 11–12."* | *"PROVEN: All 75 tiles are load-bearing. Day-11 gap is only transient. No exploitable resource slack exists anywhere in V2."* |
| **Which is Correct?** | **Neither report is fully correct. Report A identified real spatial vacancies; Report B failed to exploit them due to a bugged implementation, but falsely claimed proof of an impossibility theorem.** |
| **Evidence** | In `scratch/run_additive_investigation.py` (lines 178–184), the script planted tomatoes on vacant tiles by overwriting wheat commands, but provided **zero** watering or harvesting instructions for those tiles. Tomato crops require 8 days to yield and rot within 24 turns if unharvested (`sim.hpp` line 720–726). The unwatered/unharvested crops rotted into weeds. In SE-land mode, the script repeatedly called `HIRE` and `BUY_LAND` every single day (lines 136–144). |
| **Can Both Be True?** | No. Physical vacancies do exist on Days 11–12, but because the test overlay failed to manage crop lifecycle physics, the experiment failed. Converting an experimental software defect into a universal theoretical claim ("no slack exists anywhere") is a severe methodological failure. |

---

### Contradiction 6: Shop Product Demands — `shop_transition_model.py` vs Engine Source Truth

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | [`candidates/closed_loop_architecture/shop_transition_model.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/shop_transition_model.py) (R10) | [`external_repos/kaggriculture-cppsim/sim/sim.hpp`](file:///c:/Users/Sundareswaran/Kagriculture/external_repos/kaggriculture-cppsim/sim/sim.hpp) & `kaggle_environments.envs.kaggriculture.kaggriculture` |
| **Exact Claim** | `PET_CAFE: [CARROT, MILK]`, `PIZZA: [WHEAT, TOMATO]`, `SMOOTHIE: [CARROT, STRAWBERRY, MELON]`, `FARMERS_MARKET: [CARROT, TOMATO, STRAWBERRY, MELON]`, `BRUNCH: [EGG, MILK, STRAWBERRY]`. | `PET_CAFE: [CARROT]`, `PIZZA: [MILK, TOMATO, WHEAT]`, `SMOOTHIE: [MILK, STRAWBERRY]`, `FARMERS_MARKET: [CARROT, STRAWBERRY, TOMATO, WHEAT]`, `BRUNCH: [EGG, STRAWBERRY, WHEAT]`. |
| **Which is Correct?** | **Report B is the bit-exact ground truth of the simulator; Report A is completely hallucinated.** |
| **Evidence** | Direct execution of `kaggle_environments.envs.kaggriculture.kaggriculture.SHOPS` and C++ bitmasks in `sim.hpp` (lines 127–136) confirm 6 out of 8 shop definitions in Report A were wrong. PET_CAFE never consumes Milk; SMOOTHIE never consumes Carrot or Melon; FARMERS_MARKET never consumes Melon; BRUNCH never consumes Milk; PIZZA requires Milk. |
| **Can Both Be True?** | Absolutely not. Report A contains factual errors about the game rules. |

---

### Contradiction 7: Step 696 Order Truncation as Root Cause of Losses vs Counterfactual Non-Improvement

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | [`research/v2_dmitrii_residual_profit_map.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v2_dmitrii_residual_profit_map.md) (R14) | [`scratch/test_step696_causal.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/test_step696_causal.py) Counterfactual Execution |
| **Exact Claim** | *"The cash gap is 100% driven by Step 696 market sell order arbitration... Truncating the 36 Wheat order is the causal mechanism of V2's losses against Dmitrii."* | Step 696 counterfactual intervention on the worst 7 loss seeds worsens margin on 3 seeds, leaves 1 seed unchanged, and improves on only 3 seeds. |
| **Which is Correct?** | **Report B is the causal truth; Report A mistook an observational correlation for a causal mechanism.** |
| **Evidence** | Direct execution of `scratch/test_step696_causal.py` on the worst loss seeds: Seed 50081 (worst loss -$730): Counterfactual was `-$818` (worse by -$88). Seed 50078: `-$612` -> `-$838` (worse by -$226). Seed 50022: `-$400` -> `-$612` (worse by -$212). Seed 50040: `-$344` -> `-$344` (no change). |
| **Can Both Be True?** | No. If truncating 36 wheat was the root cause of the loss, restoring the wheat order would universally improve the margin. The fact that it worsened margin on 3 of the worst seeds disproves the causal assertion. |

---

### Contradiction 8: Physical Production Equivalence — "100.0% Identical Agronomy" vs V1 Shed Purges

| Dimension | Report A | Report B |
|---|---|---|
| **Document** | [`research/v2_dmitrii_residual_profit_map.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v2_dmitrii_residual_profit_map.md) (R14) | [`research/closed_loop_architecture_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/closed_loop_architecture_report.md) (R7) |
| **Exact Claim** | *"Physical production, crop selection, labor scheduling, and land purchasing are 100.0% identical between V2 and Dmitrii."* | *"Closed-Loop V1 prematurely dumped 15 units of wool, wheat, and fertilizer at threshold 88, disrupting animal feed and crop cycles."* |
| **Which is Correct?** | **Both are correct when properly scoped to specific candidate versions (V1 vs V2).** |
| **Evidence** | In V1, the purge threshold was 88, which dumped items prematurely. In V2, the threshold was raised to 96, and feed reserves were strictly protected (`_compute_feed_reserve` ensures wheat $\ge 3 \times \text{animals}$). Tile-by-tile inspection on Seed 50000 confirmed identical tile states between V2 and Dmitrii. |
| **Can Both Be True?** | Yes, because V1 altered physical behavior while V2 strictly preserved physical identity. However, reports must never conflate V1 and V2 results. |

---

### Contradiction 9: Published Table 1 Metrics vs Raw Margin Scan JSON Data in R14

| Dimension | Report A (Narrative Table 1 in R14) | Report B (Raw JSON `scratch/v2_dmitrii_margin_scan.json`) |
|---|---|---|
| **Discovery Mean Margin** | `+$28.8` | `+$39.12` |
| **Discovery Wins** | 28W – 22L (56.0%) | 31W – 19L (62.0%) |
| **Qualification Mean Margin** | `+$0.5` | `+$11.40` |
| **Qualification Wins** | 26W – 24L (52.0%) | 24W – 26L (48.0%) |
| **Fresh Holdout Mean Margin**| `+$46.4` | `+$23.32` |
| **Fresh Holdout Wins** | 28W – 22L (56.0%) | 27W – 23L (54.0%) |
| **Total 150-Seed Mean Margin**| `+$25.3` | `+$24.61` |
| **Max Best Win Margin** | `+$454.0` | `+$326.0` |
| **Which is Correct?** | **Report B (the raw JSON file) is the ground-truth data; Report A contains reporting transcription errors.** |
| **Evidence** | Running `independent_audit_runner.py` directly parses `scratch/v2_dmitrii_margin_scan.json`. The sum of wins happened to match (82W, 54.7%), but the split-level breakdowns were misreported in the prose document. |
| **Can Both Be True?** | No. Table 1 in R14 was inaccurately transcribed from the script's underlying JSON data. |

