# KAGGRICULTURE — MASTER FORENSIC RESEARCH AUDIT REPORT
## Comprehensive Post-Submission Empirical Truth Verification & Evidence Reconstruction

**Audit Scope:** All research, benchmark experiments, reports, and codebase changes conducted strictly **AFTER** the deployment of the two frozen live Kaggle submissions (`56146971` and `56146947`) on September 10, 2026, at 15:14:36 UTC.  
**Audit Standard:** Forensic, adversarial verification against the C++ simulation source (`external_repos/kaggriculture-cppsim/sim/sim.hpp`), official environment (`kaggle_environments 1.32.7`), candidate implementations, and raw simulation result artifacts.  
**Frozen Submissions Status:** `56146971` and `56146947` remain strictly frozen and untouched.

---

## 1. EXECUTIVE VERDICT

Following an exhaustive forensic audit of the post-submission research history across eight paired-programming iterations, the core verdict is:

1. **A Real Empirical Core Exists**:
   - The deployment and exact semantic equivalence of the two frozen live submissions (`56146971` and `56146947`) are **fully verified (Grade A)**.
   - The diagnostic identifying the **Day-12 dawn hiring collapse** (triggered when cash fell below $800 in non-yarn worlds, cutting workforce from 7 to 4 and leaving crops to rot) is **fully verified (Grade A)**.
   - `CLOSED_LOOP_V2`'s preservation of Dmitrii's 61-fertilization physical agronomy while safely preventing silent shed discards via JIT shed headroom protection (threshold 96) and dawn hiring order priority is **fully verified (Grade A)**.
   - The finding that **pure 19S/0T Strawberry Bedrock strictly dominates all static hybrid crop mixtures** (17S/2T, 15S/4T, etc.) is **fully verified (Grade A)**. Diversifying static crop allocations into Tomato without dynamic shop guarantees causes catastrophic margin collapse (-$1,465 to -$10,800).

2. **Severe Methodological Failures, Hallucinations, and Bugs Compromised the Later Research**:
   - **Hallucinated Shop Demand Rules (Grade H/F)**: In `candidates/closed_loop_architecture/shop_transition_model.py`, **6 out of 8 shop demand profiles were fabricated/misstated** compared to both official Kaggle rules and C++ `sim.hpp`. Pet Cafe was coded as demanding Milk (it demands only Carrot); Pizza Shop omitted Milk; Smoothie Shop was coded as demanding Carrot and Melon (it demands Strawberry and Milk); Farmers Market included Melon; and Brunch Spot omitted Wheat. Downstream models (including Value of Information calculations and crop portfolio matrices) were built on mathematically false game rules.
   - **Bugged "Slack Capacity" Experiment (Grade F)**: The experiment claiming to prove that "no resource slack exists anywhere in V2" (`research/slack_capacity_real_option_report.md`) was severely broken in code. In `VACANT_TILES` mode, it planted tomatoes on vacant tiles without providing any watering or harvest commands, causing the crops to rot into weeds. In `SE_LAND` mode, it attempted to hire workers and purchase land every single day. The experiment did not test additive policy viability; it tested software bugs.
   - **Cherry-Picked Tomato Specialization (Grade F)**: The widely cited "+$3,942 Pizza-world cash gain" was a single cherry-picked seed (Seed 50042) out of 6 True Pizza seeds. Across the 6-seed cohort, tomato specialization produced an average loss of **-$5,382** against V2. All 18 parameter combinations in the True Pizza sweep had negative average deltas.
   - **Closed-Loop V3 Overfitting & Generalization Failure (Grade F)**: While V3 beat Dmitrii by +$266.42 on Discovery seeds, it completely collapsed on Fresh Holdout seeds (50100–50149), losing to Dmitrii by -$37.24 and regressing against V2 by -$41.64 with only a 4% win rate.
   - **Observational vs Causal Confusion in Step 696 (Grade F)**: The claim in `v2_dmitrii_residual_profit_map.md` that the Step 696 36-Wheat order truncation caused V2's worst losses against Dmitrii failed counterfactual testing. Forcing the wheat order through worsened the loss on 3 of the 7 worst seeds (e.g. Seed 50081: -$730 -> -$818).
   - **Statistical Overclaiming on Confidence Intervals (Grade C)**: `research/v2_dmitrii_residual_profit_map.md` claimed `CLOSED_LOOP_V2` was "confirmed globally superior" to Dmitrii with established alpha. In reality, the 95% confidence interval spans `[-$2.07, +$51.30]`. Because the confidence interval crosses zero ($p = 0.070$), claiming established statistical superiority is invalid.

---

## 2. COMPLETE POST-SUBMISSION TIMELINE

| Timestamp (UTC) | Event / Milestone | Artifact Created | Primary Code / Script |
|---|---|---|---|
| **2026-09-10 15:13:16** | Submission 56146947 Deployed | `candidates/compiled_v54_plus_shop.py` | `submit_agent.py` |
| **2026-09-10 15:14:36** | Submission 56146971 Deployed | `candidates/compiled_v54_plus_residual.py` | `submit_agent.py` |
| **2026-09-10 20:04:04** | Residual Validation Report | `research/championship_residual_validation.md` | `scratch/run_clean_discovery_grid.py` |
| **2026-09-10 20:27:09** | Semantic Equivalence Verification | `research/compiled_semantic_equivalence.md` | `scratch/verify_behavioral_equivalence_50seeds.py` |
| **2026-09-10 20:48:20** | Live Two-Agent Deployment Manifest | `research/final_two_agent_deployment.md` | `scratch/submit_agent.py` |
| **2026-09-10 23:57:44** | Full-Spectrum Shop Economy Report | `reports/FULL_SPECTRUM_SHOP_ECONOMY_...md` | `scratch/evaluate_dmitrii_200_seeds.py` |
| **2026-09-11 04:44:23** | Non-Yarn Economic Optimization | CID `f75512a4...` `walkthrough.md` | `scratch/reconstruct_live_losses.py` |
| **2026-09-11 10:33:21** | Live Loss Counterforensics Report | `research/live_loss_counterforensics_report.md` | `scratch/deep_audit_top3_losses.py` |
| **2026-09-11 10:44:58** | Closed-Loop Architecture Report | `research/closed_loop_architecture_report.md` | `candidates/closed_loop_architecture/closed_loop_agent.py` |
| **2026-09-11 11:13:01** | Competitive Breakthrough Architecture | `research/competitive_breakthrough_...md` | `scratch/run_architecture_scoreboard.py` |
| **2026-09-11 12:40:00** | Tomato Specialization Sweeps | `task-265.log`, `scratch/true_pizza_sweep_results.json` | `scratch/test_tomato_sweeps_true_pizza.py` |
| **2026-09-11 13:20:00** | Shop Transition Model & VoI | `candidates/closed_loop_architecture/shop_transition_model.py` | `candidates/closed_loop_architecture/shop_transition_model.py` |
| **2026-09-11 13:28:00** | 12-Crop Portfolio Sweep | `scratch/crop_portfolio_sweep_results.json` | `scratch/crop_portfolio_sweep.py` |
| **2026-09-11 13:30:00** | Closed-Loop V3 Validation | `scratch/v3_three_dataset_validation.json` | `scratch/test_v3_candidate.py` |
| **2026-09-11 14:15:08** | Slack-Capacity Real-Option Report | `research/slack_capacity_real_option_report.md` | `scratch/run_additive_investigation.py` |
| **2026-09-11 14:52:48** | V2 vs Dmitrii Profit Attribution | `research/v2_dmitrii_residual_profit_map.md` | `scratch/run_margin_scan.py` |

---

## 3. ALL AUDITED REPORTS

Fourteen substantive reports were audited:
- **R1** ([`research/championship_residual_validation.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/championship_residual_validation.md)): Verified preemptive sell controller holdout alpha (+1,984 margin). **GRADE A**.
- **R2** ([`research/compiled_semantic_equivalence.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/compiled_semantic_equivalence.md)): Verified zero-divergence standalone compilation of live controls. **GRADE A**.
- **R3** ([`research/final_two_agent_deployment.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/final_two_agent_deployment.md)): Verified deployment of 56146971 and 56146947. **GRADE A**.
- **R4** ([`reports/FULL_SPECTRUM_SHOP_ECONOMY_AND_META_FORENSICS_REPORT.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/FULL_SPECTRUM_SHOP_ECONOMY_AND_META_FORENSICS_REPORT.md)): Market elasticity and crop dynamics. Partially verified. **GRADE C**.
- **R5** (CID `f75512a4...` `walkthrough.md`): Live match loss diagnosis and hiring starvation. **GRADE B**.
- **R6** ([`research/live_loss_counterforensics_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/live_loss_counterforensics_report.md)): 161 live match replay analysis and Dmitrii counterfactuals. **GRADE B**.
- **R7** ([`research/closed_loop_architecture_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/closed_loop_architecture_report.md)): Closed-loop prototype and diagnosis of threshold 88 shed purge defect. **GRADE A**.
- **R8** ([`research/competitive_breakthrough_architecture_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/competitive_breakthrough_architecture_report.md)): 100-match unified scoreboard. **GRADE C**.
- **R9** (CID `7ceb96d7...` logs & `true_pizza_sweep_results.json`): Tomato specialization claims. False and cherry-picked. **GRADE F**.
- **R10** ([`candidates/closed_loop_architecture/shop_transition_model.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/shop_transition_model.py)): Empirical shop transition model. Hallucinated game rules. **GRADE H/F**.
- **R11** ([`scratch/crop_portfolio_sweep_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/crop_portfolio_sweep_results.json)): 12-crop portfolio grid proving 19S/0T strict dominance. **GRADE A**.
- **R12** ([`scratch/v3_three_dataset_validation.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/v3_three_dataset_validation.json)): Closed-Loop V3 three-dataset audit proving holdout regression. **GRADE A**.
- **R13** ([`research/slack_capacity_real_option_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/slack_capacity_real_option_report.md)): Slack capacity analysis. Bugged code and overclaimed conclusion. **GRADE F**.
- **R14** ([`research/v2_dmitrii_residual_profit_map.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v2_dmitrii_residual_profit_map.md)): V2 vs Dmitrii 150-seed residual decomposition. Partially verified agronomy; invalid causality and overclaimed statistics. **GRADE C/F**.

---

## 4. VERIFIED FINDINGS (GRADE A & B)

1. **Standalone Deployment Integrity**: Submissions 56146971 and 56146947 were compiled with zero behavioral drift across 72,000 steps ($0.000\%$ divergence) and remain active and frozen.
2. **Root Cause of Live Non-Yarn Collapses**: Official live match replays (e.g. `episode_107543042.json`) prove that our live submissions entering Day 10–12 with $< \$800$ cash failed the dawn hiring step ($4 \times \$200 = \$800$). Hands dropped from 7 to 4, leaving unharvested crops to rot and causing losses of -$40k to -$55k.
3. **Dmitrii's Live Immunity**: On the exact seeds where our live submissions collapsed, Dmitrii Base reached $92k–$115k and defeated the live opponents, proving that the losses were candidate-specific regressions rather than unsolvable seeds.
4. **Physical Agronomy Equivalence in V2**: Turn-by-turn tracing confirms that `CLOSED_LOOP_V2` and `Dmitrii-LB2800` execute **100.0% bit-for-bit identical physical agronomy** across all 30 days (identical tile assignments, planting schedules, watering cycles, fertilizations, animal purchases, and hand movements).
5. **Strict Dominance of 19S/0T Strawberry Bedrock**: Across 100 paired CRN discovery matches, pure Strawberry (19S/0T) strictly dominated every static hybrid allocation on mean cash ($97,026), paired margin (+$24.98), median margin (+36.0), win rate (59.0%), and downside risk (56.72). Introducing 2 tomatoes reduced margin by -$1,490; introducing 4 tomatoes reduced margin by -$2,103; replacing all strawberries with tomatoes dropped margin to -$10,800.
6. **MAX_ORDERS = 10 Engine Enforcement**: Direct engine testing confirms that submitting more than 10 market orders results in silent truncation of order slots 10+. Priority sorting of market orders is mandatory.
7. **Crop Rot Kinetics**: As defined in `sim.hpp` lines 717–726, when an ongoing crop completes 4 yield cycles, its lifespan expires on the next day. Thereafter, on every even turn, it rots at a rate of 1 unit every 2 steps until it turns into a weed.

---

## 5. PARTIALLY VALID FINDINGS (GRADE C)

1. **V2 Advantage over Dmitrii**: The 150-seed paired CRN tournament yielded an empirical mean margin of **+$24.61** and a win rate of **54.7%** (82W – 68L). The observation is real, but the margin represents a modest +0.025% gain on a ~$97,000 revenue base, and the 95% confidence interval crosses zero.
2. **Shop Economy Dominance**: Strawberry and Wool are indeed the highest-revenue assets in the game, but assertions that "shops can be predicted with 98% accuracy" overclaimed statistical certainty on tiny samples.
3. **Live Opponent Replay Mirroring**: While Dmitrii crushed live opponent replays in counterfactual tests, recorded opponent tapes are open-loop. In live interactive play, market prices dynamically adjust to both players' sales, meaning counterfactual replay gains slightly overestimate live closed-loop margins.

---

## 6. FALSE FINDINGS (GRADE F)

1. **"Pizza-World Cash Gain of +$3,942"**: Citing this number as proof that Tomato specialization is profitable was false. Seed 50042 gained +$3,942, but the other 5 True Pizza seeds lost heavily: Seed 50003 lost -$15,186; Seed 50021 lost -$12,069; Seed 50030 lost -$12,540. The 6-seed ensemble average was **-$5,382.67**.
2. **Step 696 Order Truncation as the Causal Root of Losses**: The narrative asserted that V2 lost to Dmitrii because it submitted 11 market orders at Step 696, dropping a 36-Wheat sell order. Independent execution of `scratch/test_step696_causal.py` proved that forcing the 36-Wheat order into slot 0 worsened the loss on 3 out of the 7 worst seeds (Seed 50081 worsened from -$730 to -$818; Seed 50078 worsened from -$612 to -$838; Seed 50022 worsened from -$400 to -$612). The causal claim is contradicted by experiment.
3. **Generalization of Closed-Loop V3**: The claim that V3 represents an architectural breakthrough over V2 is contradicted by holdout data. V3 regressed by -$41.64 vs V2 on Fresh Holdout seeds with a catastrophic 4% win rate against V2.

---

## 7. BUGGED EXPERIMENTS (GRADE F)

1. **Additive Tomato Investigation (`scratch/run_additive_investigation.py`)**:
   - In `VACANT_TILES` mode (lines 178–184), the overlay hijacked wheat planting actions to plant tomatoes on vacant tiles, but provided **zero watering and zero harvesting logic** for those tiles. Tomatoes require 8 days to mature and rot within 24 turns if unharvested. Every planted tomato rotted into a weed.
   - In `SE_LAND` mode (lines 143–144), the script called `market.append(["HIRE"])` at hour 1 **every single day** from Day 12 to Day 29 (18 consecutive days), rapidly compounding exponential hiring costs.
   - Conclusion: The experiment was completely invalid due to implementation bugs.

---

## 8. HALLUCINATED / UNSUPPORTED CLAIMS (GRADE H)

1. **Fabricated Shop Demands in `shop_transition_model.py`**:
   The demand profiles hardcoded into the empirical model contradicted both the C++ simulator and official Kaggle code:
   - Claimed: `PET_CAFE` demands Carrot + Milk. (Truth: demands **Carrot only**).
   - Claimed: `PIZZA_SHOP` demands Wheat + Tomato. (Truth: demands **Milk + Tomato + Wheat**).
   - Claimed: `SMOOTHIE_SHOP` demands Carrot + Strawberry + Melon. (Truth: demands **Strawberry + Milk**).
   - Claimed: `FARMERS_MARKET` demands Carrot + Tomato + Strawberry + Melon. (Truth: demands **Wheat + Carrot + Tomato + Strawberry**).
   - Claimed: `BRUNCH_SPOT` demands Egg + Milk + Strawberry. (Truth: demands **Egg + Wheat + Strawberry**).
   Six out of eight shops were misstated.
2. **Markov Shop Transitions**: Asserting that shop reveals at Day 12 conditionally depend on Day 3 reveals was mathematically baseless. In `sim.hpp` (line 748), every shop is drawn independently via `rng.choice_index(N_SHOPS)` with replacement. Apparent transition patterns were sample noise on small panels ($N \le 3$).

---

## 9. STATISTICALLY INVALID CLAIMS (GRADE C)

1. **Asserting "Global Superiority" with CI Crossing Zero**:
   In `research/v2_dmitrii_residual_profit_map.md`, the author declared V2 "confirmed globally superior" based on:
   $$\text{Mean Margin} = +\$24.61, \quad 95\%\text{ CI} = [-\$2.07, +\$51.30], \quad p = 0.070$$
   In classical hypothesis testing, when the confidence interval spans zero, the null hypothesis cannot be rejected. Labeling a non-significant result as "confirmed global superiority" is statistically invalid.
2. **Discrepancy Between Published Table 1 and Raw JSON in R14**:
   - Published Discovery Mean: `+$28.8` (28W–22L). Raw JSON Mean: `+$39.12` (31W–19L).
   - Published Qualification Mean: `+$0.5` (26W–24L). Raw JSON Mean: `+$11.40` (24W–26L).
   - Published Fresh Holdout Mean: `+$46.4` (28W–22L). Raw JSON Mean: `+$23.32` (27W–23L).
   - Published Max Win: `+$454.0`. Raw JSON Max Win: `+$326.0`.
   Table 1 in R14 contained reporting transcription errors.

---

## 10. INTERNAL CONTRADICTIONS

The audit resolved nine primary contradictions, detailed in [`CONTRADICTIONS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/CONTRADICTIONS.md):
- **V2 Superiority vs Parity**: Parity is statistically established; superiority is an unproven point estimate.
- **Worst Loss -$6,367 vs -$730**: -$6,367 is an unpooled single-match seat artifact; -$730 is the true paired CRN worst loss.
- **V3 Discovery Gain vs Holdout Loss**: V3 overfit to Discovery and regressed on Fresh Holdout.
- **Tomato Upside vs Collapse**: +$3,942 was a cherry-picked outlier; average was -$5,382.
- **Slack Exists vs No Slack Exists**: Vacancies exist, but test scripts failed to harvest crops.
- **Shop Demands**: `shop_transition_model.py` was hallucinated; `sim.hpp` is ground truth.
- **Step 696 Causality**: Correlated in observation, disproven by counterfactual intervention.
- **Physical Identity**: V1 violated identity; V2 restored it.
- **Table 1 vs JSON**: Narrative table transcribed numbers incorrectly from JSON.

---

## 11. SIMULATOR SEMANTICS THAT WERE MISSTATED

1. **Shop Unlock Frequency & Sampling**: Shops unlock every 3 days at steps 72, 144, 216, 288, 360, 432, 504, and 576. Sampling is **uniform with replacement** from 8 types. Shops can duplicate.
2. **Weed RNG Coupling**: In official unpinned Kaggle play, `spawn_weeds` draws random numbers for each empty tile before the shop draw. Suppressing planting changes the number of empty tiles, shifting the random stream and causing different shop reveals across identical seeds.
3. **Decay Mechanics**: Ongoing crops (Strawberry, Tomato) rot at 1 unit every 2 steps once lifespan expires, quickly converting to weeds. Unscheduled plantings rot before standard harvest loops arrive.
4. **Market Limits**: Maximum 10 orders per turn per player. Orders beyond index 9 are silently dropped without error.

---

## 12. BENCHMARK & HARNESS ERRORS

1. **Unpooled Single-Seat Reporting**: Reporting single-match scores (e.g. Seed 50076 Seat 0: -$6,367) created phantom catastrophic loss alarms. Single-match margins in asymmetric games confound seat bias with agent skill. Only paired CRN margins $((A_0 - B_1) + (A_1 - B_0))$ are valid.
2. **Unpinned Simulator Variance**: Rerunning candidate benchmarks without seed pinning allowed weed RNG drift to re-roll shop sequences, creating apparent agent margin shifts of up to $\pm \$25,000$ that were entirely simulator artifacts.

---

## 13. DATA LEAKAGE FINDINGS

1. **Holdout Tuning in V3**: In CID `7ceb96d7...`, gating rules were iteratively adjusted until Discovery margin peaked at +$266. When evaluated on Qualification and Fresh Holdout, the margin collapsed to $0 and -$41, demonstrating leakage and overfitting to the discovery set.
2. **Precomputed Seed Thresholds**: In early shop routing experiments, policies checked specific shop order pairs that only appeared once or twice in the dataset, effectively memorizing training seeds.

---

## 14. AGENT INVOCATION ISSUES

1. **Dmitrii Invocation Divergence**:
   - In `scratch/run_margin_scan.py`, Dmitrii was invoked via `main.py` -> `ShopClosure.act()`, executing full Monte Carlo terminal planning (64 sims) at steps 712–718.
   - In earlier ablation scripts (e.g. `run_architecture_scoreboard.py`), Dmitrii was invoked via `router_parent.Policy()`, which **omitted** the terminal planner.
   - Comparing V2 against two different Dmitrii implementations across reports created unexplained margin variances.
2. **State Reset Safety**: Both `ClosedLoopAgentV2` and `Dmitrii-LB2800` correctly reset internal state when `step == 0` or when step rewinds, preventing cross-game state contamination.

---

## 15. CRN & SEAT ASYMMETRY ISSUES

1. **Massive Seat Variance**: On Seed 50076, Seat 0 scored -$6,367 while Seat 1 scored +$6,457. A single unpooled match would report a blowout win or catastrophic loss purely based on seat assignment.
2. **CRN Balance Verification**: In `scratch/v2_dmitrii_margin_scan.json`, every seed was evaluated symmetrically across both seat orientations. Paired CRN is mandatory for all Kaggriculture benchmarking.

---

## 16. REVISED V2 PERFORMANCE

Against frozen baseline controls and top external references across balanced holdouts:
- **vs Control Submission 56146947 (`v54_plus_shop`)**: Decisive victory (+11,000 to +14,000 margin, 100% win rate).
- **vs Mohui V66**: Strong victory (+3,000 to +4,500 margin, 85% win rate).
- **vs Dmitrii-LB2800**: Statistical parity with positive point estimate (+24.61 coins, 54.7% win rate, 95% CI: `[-$2.07, +$51.30]`, worst paired loss: -$730).

---

## 17. REVISED V3 PERFORMANCE

- **Discovery (Seeds 50000–50049)**: +$266.42 margin vs Dmitrii, +$264.46 vs V2 (Overfit).
- **Qualification (Seeds 50050–50099)**: +$11.44 margin vs Dmitrii, $0.00 vs V2.
- **Fresh Holdout (Seeds 50100–50149)**: **-$37.24 margin vs Dmitrii, -$41.64 vs V2, 4.0% win rate vs V2**.
- **Verdict**: `CLOSED_LOOP_V3` is an overfit, regressive candidate that must not be deployed.

---

## 18. REVISED SLACK-CAPACITY RESULTS

- **Tested Additive Policies (A through H)**: All failed with negative margins due to implementation bugs (unwatered crops, continuous daily hiring).
- **Theoretical Impossibility Theorem**: The claim that "no slack exists anywhere in V2" is **UNPROVEN**. Physical idle tiles exist on Days 11–12. Whether a mathematically valid, correctly scheduled crop can exploit them remains an open scientific question.

---

## 19. REVISED V2-vs-DMITRII RESULTS

- **True 150-Seed Sample Size**: Exactly 150 unique seeds, 300 paired matches, balanced seating.
- **True Win Rate**: **54.7%** (82 Wins, 68 Losses, 0 Ties).
- **True Mean Margin**: **+$24.61** (not +$25.3).
- **True 95% Confidence Interval**: **`[-$2.07, +$51.30]`** (crosses zero; $p = 0.070$).
- **True Worst Paired Loss**: **-$730.0** (Seed 50081).
- **True Best Paired Win**: **+$326.0** (Seed 50000).
- **Zero Catastrophic Losses**: 0 / 150 paired losses exceeded -$1,000.
- **Physical Agronomy**: 100.0% identical between V2 and Dmitrii.

---

## 20. WHAT WE NOW ACTUALLY KNOW

1. Our active live submissions (`56146971` and `56146947`) suffer from liquidity collapse ($< \$800$) on non-yarn seeds, cutting farmhands and triggering crop rot.
2. Dmitrii's 61-fertilization agronomy is robust across non-yarn worlds, earning $90k–$115k where our live controls earned $35k–$65k.
3. `CLOSED_LOOP_V2` successfully incorporates Dmitrii's physical agronomy while preventing silent shed overflow via JIT headroom protection (threshold 96) and dawn hiring priority.
4. `CLOSED_LOOP_V2` achieves parity with Dmitrii Base across 150 seeds (+24.61 coins margin, 54.7% WR) with zero catastrophic paired losses (worst loss -$730).
5. Static crop diversification into Tomato is strictly dominated by 19S/0T Strawberry Bedrock.
6. The simulator samples 8 shops uniform at random with replacement; 4 of 8 demand Strawberry; duplicate shops occur frequently.

---

## 21. WHAT WE THOUGHT WE KNEW BUT DO NOT

1. We thought Tomato specialization yielded +$3,942 on Pizza worlds. **We do not know this**: that was a cherry-picked outlier; the 6-seed ensemble lost -$5,382.
2. We thought `CLOSED_LOOP_V3` maintained superior alpha. **We do not know this**: V3 regressed on Fresh Holdout (-$41.64 vs V2, 4% WR).
3. We thought it was proven that "no resource slack exists in V2". **We do not know this**: the experiment was invalidated by software bugs.
4. We thought Step 696 wheat order truncation caused V2's losses against Dmitrii. **We do not know this**: counterfactual intervention disproved the causal link.
5. We thought shop transition matrices could predict future shops with 98% certainty. **We do not know this**: the transition matrices were sample noise and based on false demand profiles.

---

## 22. WHAT IS STILL UNKNOWN

1. Can a correctly scheduled, properly watered and harvested secondary crop exploit Days 11–12 idle tiles profitably?
2. What is the true mathematical mechanism that causes V2 to lose up to -$730 against Dmitrii on specific seeds if physical production is identical and Step 696 order truncation is not the cause?
3. What is the true live leaderboard Elo rating of `CLOSED_LOOP_V2` relative to top competitors once tournament matchmaking stabilizes?

---

### VERIFIED FACTS WE CAN SAFELY BUILD ON

1. **Frozen Live Controls**: Submissions `56146971` (`compiled_v54_plus_residual.py`) and `56146947` (`compiled_v54_plus_shop.py`) are cryptographically verified and active.
2. **Physical Agronomy Bedrock**: Dmitrii's 61-fertilization physical engine and 13 action tapes prevent workforce starvation and represent our strongest physical agronomy foundation.
3. **CLOSED_LOOP_V2 Baseline Mechanics**: JIT shed headroom protection at threshold 96 and strict dawn hiring priority arbitration preserve 100% of physical agronomy without premature feed dumps.
4. **19S/0T Strict Dominance**: 19S/0T Strawberry Bedrock strictly dominates all static hybrid crop portfolios across discovery and qualification partitions.
5. **Bit-Exact Engine Rules**: The C++ simulator (`sim.hpp`) and official `kaggle_environments 1.32.7` enforce 720 steps, 8 shops sampled uniform with replacement, 10 market orders per turn, and rapid crop decay (1 unit per 2 turns on even steps) after lifespan expiry.

---

### FINDINGS THAT MUST BE DISCARDED OR RETRACTED

1. **RETRACT**: The claim that Day-11 Tomato specialization generates "+$3,942 alpha on Pizza worlds" (Retracted as a cherry-picked outlier from a net-negative -$5,382 distribution).
2. **RETRACT**: The shop product demand definitions in `candidates/closed_loop_architecture/shop_transition_model.py` (Retracted as fabricated/hallucinated; contradicts engine ground truth on 6 of 8 shops).
3. **RETRACT**: The claim that `CLOSED_LOOP_V3` is an established architectural improvement (Retracted due to severe holdout regression: -$41.64 margin vs V2, 4% win rate).
4. **RETRACT**: The theorem that "no resource slack exists anywhere in V2" (Retracted due to invalidating implementation bugs in `scratch/run_additive_investigation.py`).
5. **RETRACT**: The causal claim that Step 696 36-Wheat order truncation is the root cause of V2's losses against Dmitrii (Retracted due to counterfactual falsification).
6. **RETRACT**: Language asserting that `CLOSED_LOOP_V2` is "confirmed globally superior" to Dmitrii (Downgraded to statistical parity with positive point estimate, as 95% CI spans `[-$2.07, +$51.30]`).

---

### OPEN QUESTIONS REMAINING AFTER THE AUDIT

1. **Exact Mechanism of Residual Loss against Dmitrii**: If physical production is 100% identical and Step 696 wheat truncation is not the cause, what specific step and market queue interaction produces the -$730 worst loss on Seed 50081?
2. **Feasibility of True Dynamic Slack Harvesting**: If an additive policy correctly accounts for crop maturation and dedicates worker actions to watering and harvesting, can the Day 11–12 vacant tiles generate positive net margin over pure Strawberry Bedrock?
3. **Closed-Loop Opponent Reaction**: How do top human agents dynamically manipulate market prices when competing head-to-head against 19-Strawberry production?
