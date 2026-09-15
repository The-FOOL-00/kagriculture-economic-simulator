# KAGGRICULTURE: POST-SUBMISSION RESEARCH REPORT INDEX
## Chronological Catalog & Audit Status of Post-Submission Research
**Audit Horizon Start:** 2026-09-10 15:14:36 UTC (Deployment of Frozen Submissions 56146971 & 56146947)  
**Standard:** Strict Forensic Verification against Simulator Source, Codebase, and Raw Data Artifacts.

---

### Report Selection Methodology
Following the deployment and freezing of the two active live Kaggle submissions (`56146971` and `56146947`), a total of 14 substantive research reports, investigation milestones, and benchmark suites were generated across eight pair-programming sessions. Every substantive research event that introduced new hypotheses, quantitative evaluations, causal claims, or architectural proposals has been indexed below in exact chronological sequence.

---

## Chronological Report Index

### Report 1: Championship Residual Validation
- **Report #:** R1
- **Date / Timestamp:** 2026-09-10 20:04:04 UTC
- **Title / Filename:** [`research/championship_residual_validation.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/championship_residual_validation.md)
- **Research Question:** Does the preemptive residual sell controller (`v54_plus_residual.py`) maintain alpha over `V54++ Control` and `V66` across untuned holdout partitions?
- **Candidate(s):** `v54_plus_residual.py`, `v54_plus_shop.py`, `V54++`, `V66`, `V54`
- **Simulator Version:** `kagsim` C++ engine (1.32.7 parity)
- **Seeds:** Discovery (50000–50049), Holdout (50100–50149)
- **Method:** Paired head-to-head tournament in `kagsim` across 50 seeds with balanced seating.
- **Main Claims:** Candidate achieved +$2,118 margin over V54++ Control on Discovery and +$1,984 on Holdout; zero memory leaks; 0 / 72,000 action divergence against compiled version.
- **Raw Artifacts Referenced:** `research/residual_clean_discovery_grid.json`, `research/residual_true_untouched_holdout_results.json`
- **Code Artifacts Referenced:** `scratch/run_clean_discovery_grid.py`, `scratch/run_true_untouched_holdout.py`
- **Downstream Decision Impact:** Led directly to freezing and compiling candidate for live Kaggle submission 56146971.
- **Audit Status:** **VERIFIED (GRADE A)**. Raw data confirms margins and action parity.

---

### Report 2: Compiled Standalone Semantic Equivalence
- **Report #:** R2
- **Date / Timestamp:** 2026-09-10 20:27:09 UTC
- **Title / Filename:** [`research/compiled_semantic_equivalence.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/compiled_semantic_equivalence.md)
- **Research Question:** Are the single-file bundled submissions `compiled_v54_plus_residual.py` and `compiled_v54_plus_shop.py` bit-for-bit semantically identical to their modular source trees?
- **Candidate(s):** `candidates/compiled_v54_plus_residual.py`, `candidates/compiled_v54_plus_shop.py`
- **Simulator Version:** `kagsim` C++ engine (1.32.7 parity)
- **Seeds:** 50 validation seeds (50000–50049)
- **Method:** Step-by-step action assertion across all 720 turns and all units for both players.
- **Main Claims:** 0 action mismatches out of 72,000 steps ($0.000\%$ divergence); strict deterministic identity confirmed.
- **Raw Artifacts Referenced:** `research/compiled_behavior_mismatches.csv` (empty, 105 bytes)
- **Code Artifacts Referenced:** `scratch/verify_behavioral_equivalence_50seeds.py`
- **Downstream Decision Impact:** Certified compiled files as safe for live deployment.
- **Audit Status:** **VERIFIED (GRADE A)**. Bit-exact equivalence reproduced.

---

### Report 3: Final Deployment Manifest & Live Submission Log
- **Report #:** R3
- **Date / Timestamp:** 2026-09-10 20:48:20 UTC
- **Title / Filename:** [`research/final_two_agent_deployment.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/final_two_agent_deployment.md) / [`research/live_submission_manifest.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/live_submission_manifest.md)
- **Research Question:** Formal verification and recording of the two active championship live submissions on Kaggle.
- **Candidate(s):** `compiled_v54_plus_residual.py` (Submission 56146971), `compiled_v54_plus_shop.py` (Submission 56146947)
- **Simulator Version:** Kaggle Live Platform (1.32.7)
- **Seeds:** N/A (Live competition ladder)
- **Method:** API submission tracking and SHA256 checksum verification.
- **Main Claims:** Both submissions uploaded successfully at 15:13:16 UTC and 15:14:36 UTC; strict freeze mandate initiated (no third submission, no live tuning).
- **Raw Artifacts Referenced:** Kaggle API submission metadata, SHA256 hashes (`18402ec6...`, `f651ccd2...`).
- **Code Artifacts Referenced:** `scratch/submit_agent.py`
- **Downstream Decision Impact:** Established the permanent frozen baseline controls for all subsequent research.
- **Audit Status:** **VERIFIED (GRADE A)**. Cryptographic hashes match physical files on disk.

---

### Report 4: Full-Spectrum Shop Economy & Meta Forensics Report
- **Report #:** R4
- **Date / Timestamp:** 2026-09-10 23:57:44 UTC
- **Title / Filename:** [`reports/FULL_SPECTRUM_SHOP_ECONOMY_AND_META_FORENSICS_REPORT.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/FULL_SPECTRUM_SHOP_ECONOMY_AND_META_FORENSICS_REPORT.md)
- **Research Question:** What macro-economic mechanisms explain live leaderboard performance across the full shop matrix?
- **Candidate(s):** V54++, Shop0909, Dmitrii, Okami001
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 200 random seeds (50000–50199)
- **Method:** Micro-economic inventory tracking, price elasticity curves, and shop draw frequency census.
- **Main Claims:** Market price decays are non-linear; wool and strawberry generate >60% of champion revenue; single-crop specialization collapses when matching shops fail to unlock.
- **Raw Artifacts Referenced:** `scratch/shop_world_seeds.json`, `results/dmitrii_lb2800_200seeds_reproduction.json`
- **Code Artifacts Referenced:** `scratch/evaluate_dmitrii_200_seeds.py`
- **Downstream Decision Impact:** Motivated non-yarn liquidity research and dynamic multi-crop routing.
- **Audit Status:** **PARTIALLY VERIFIED (GRADE C)**. Macro economic observations are sound, but shop demand mappings contained unverified assertions.

---

### Report 5: Non-Yarn Economic Breakthrough & Tournament Forensics
- **Report #:** R5
- **Date / Timestamp:** 2026-09-11 04:44:23 UTC
- **Title / Filename:** CID `f75512a4-6ada-4958-ad24-7989f9c781e8` Walkthrough Artifact ([`f75512a4.../walkthrough.md`](file:///C:/Users/Sundareswaran/.gemini/antigravity-ide/brain/f75512a4-6ada-4958-ad24-7989f9c781e8/walkthrough.md))
- **Research Question:** Why did frozen live submissions 56146971 and 56146947 suffer large live losses (-$30k to -$55k) in specific tournament matchups?
- **Candidate(s):** Live submission traces (56146971, 56146947) vs Dmitrii Base vs Live Opponents
- **Simulator Version:** `kagsim` & Kaggle replay parser
- **Seeds:** Live episode seeds (e.g. 50266, 50186, 50025, 50130)
- **Method:** Replay extraction of opponent action tapes; counterfactual simulation against Dmitrii Base.
- **Main Claims:** Dmitrii decisively beat all live opponents on the exact seeds where our submissions suffered catastrophic losses; our agents suffered a "Day 12 hiring collapse" due to low liquidity ($< \$800$).
- **Raw Artifacts Referenced:** `scratch/reconstructed_live_losses_forensics.json`, downloaded live replays (`episode_107543042.json`, etc.)
- **Code Artifacts Referenced:** `scratch/reconstruct_live_losses.py`, `scratch/deep_audit_top3_losses.py`
- **Downstream Decision Impact:** Triggered the design of the Closed-Loop Liquidity Guard and dawn hiring priority arbitration.
- **Audit Status:** **STRONGLY SUPPORTED (GRADE B)**. Episode replays and cash collapse reproduced; counterfactual Dmitrii wins verified.

---

### Report 6: Live Loss Counterforensics Report
- **Report #:** R6
- **Date / Timestamp:** 2026-09-11 10:33:21 UTC
- **Title / Filename:** [`research/live_loss_counterforensics_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/live_loss_counterforensics_report.md)
- **Research Question:** Systematic decomposition of 161 official live matches to diagnose liquidity failure modes in non-yarn worlds.
- **Candidate(s):** Submissions 56146971 & 56146947 vs Dmitrii Base vs Safe Liquidity Dairy
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 161 official live tournament seeds
- **Method:** Full-corpus replay analysis, counterfactual replay simulation with action injections.
- **Main Claims:** V54++ suffered from fixed 35-fertilization caps and lack of dairy buffer; Dmitrii achieved $92k–$115k on non-yarn seeds where V54++ got $34k–$65k.
- **Raw Artifacts Referenced:** `scratch/reconstructed_live_losses_forensics.json`, `scratch/live_episodes_manifest.json`
- **Code Artifacts Referenced:** `scratch/test_safe_liquidity_dairy.py`, `scratch/run_protocol_phase1.py`
- **Downstream Decision Impact:** Provided direct empirical requirements for `ClosedLoopAgentV1` and `ClosedLoopAgentV2`.
- **Audit Status:** **STRONGLY SUPPORTED (GRADE B)**. Core diagnostic on hiring starvation and cash deficit is verified.

---

### Report 7: Closed-Loop Economic Architecture Prototype Report
- **Report #:** R7
- **Date / Timestamp:** 2026-09-11 10:44:58 UTC
- **Title / Filename:** [`research/closed_loop_architecture_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/closed_loop_architecture_report.md)
- **Research Question:** Can a modular closed-loop controller (arbitrator, shed manager, liquidity controller) prevent the hiring collapse while preserving physical execution?
- **Candidate(s):** `ClosedLoopAgentV1`, `candidate_cl_economic_v1.py`
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 50 discovery seeds
- **Method:** Prototype evaluation with JIT shed headroom threshold set at 88 units.
- **Main Claims:** Closed-loop prototype eliminated catastrophic hiring failures; however, premature shed purging at 88 dumped valuable wool and wheat prematurely.
- **Raw Artifacts Referenced:** `reports/causal_study_results.json`
- **Code Artifacts Referenced:** `candidates/closed_loop_architecture/closed_loop_agent.py`, `candidates/closed_loop_architecture/action_arbitrator.py`
- **Downstream Decision Impact:** Prompted the creation of `CLOSED_LOOP_V2`, raising the purge threshold from 88 to 96 and protecting non-cannibalization feed reserves.
- **Audit Status:** **VERIFIED (GRADE A)**. Premature purge defect at threshold 88 was real and correctly diagnosed.

---

### Report 8: Competitive Breakthrough Architecture Report
- **Report #:** R8
- **Date / Timestamp:** 2026-09-11 11:13:01 UTC
- **Title / Filename:** [`research/competitive_breakthrough_architecture_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/competitive_breakthrough_architecture_report.md)
- **Research Question:** Comprehensive balanced 100-match tournament ranking V2, V54++, V66, and Dmitrii.
- **Candidate(s):** `CLOSED_LOOP_V2`, `compiled_v54_plus_residual.py`, `mohui_v66`, `dmitrii_lb2800`
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 100 qualification seeds (50000–50099)
- **Method:** Common Random Numbers (CRN), 50 seeds × 2 seats = 100 matches per pairing.
- **Main Claims:** V2 achieved +$25 margin over Dmitrii, +$3,000 over V66, and +$11,000 over V54++ Control; worst-case loss against Dmitrii was bounded.
- **Raw Artifacts Referenced:** `scratch/scoreboard_qualification_results.json`
- **Code Artifacts Referenced:** `scratch/run_architecture_scoreboard.py`
- **Downstream Decision Impact:** Established `CLOSED_LOOP_V2` as the new internal benchmark champion.
- **Audit Status:** **PARTIALLY VERIFIED (GRADE C)**. Relative rankings are real, but margin vs Dmitrii crosses zero in formal CI.

---

### Report 9: Tomato Specialization & True Pizza Frontier Study
- **Report #:** R9
- **Date / Timestamp:** 2026-09-11 12:40:00 UTC
- **Title / Filename:** CID `7ceb96d7-1723-4032-947a-056867536bd5` Task Logs (`task-265.log`) & [`scratch/true_pizza_sweep_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/true_pizza_sweep_results.json)
- **Research Question:** Does specializing in Tomato on Day 11 generate substantial cash alpha in worlds where Pizza Shop is unlocked?
- **Candidate(s):** Tomato Specialist vs ClosedLoopAgentV2 vs Dmitrii Base
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 6 True Pizza seeds (50003, 50011, 50021, 50026, 50030, 50042)
- **Method:** Parameter sweep across 10 to 30 tomato tiles and 1 to 2 planting cohorts.
- **Main Claims:** Specialization generates "+$3,942 cash gain on Pizza worlds (Seed 50042)"; claimed tomatoes yield 4 harvests with zero decay risk.
- **Raw Artifacts Referenced:** `task-265.log`, `scratch/true_pizza_sweep_results.json`
- **Code Artifacts Referenced:** `scratch/test_tomato_sweeps_true_pizza.py`
- **Downstream Decision Impact:** Inspired the design of `CLOSED_LOOP_V3` to capture tomato upside.
- **Audit Status:** **FALSE / CHERRY-PICKED (GRADE F)**. Seed 50042 was cherry-picked; the 6-seed ensemble average was actually -$5,382 below V2. All 18 parameter combinations had negative mean margins.

---

### Report 10: Empirical Shop Transition Model & Value of Information Engine
- **Report #:** R10
- **Date / Timestamp:** 2026-09-11 13:20:00 UTC
- **Title / Filename:** [`candidates/closed_loop_architecture/shop_transition_model.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/shop_transition_model.py) / [`scratch/empirical_shop_model.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/empirical_shop_model.json)
- **Research Question:** Can an empirical transition matrix predict future shop unlocks from Day 3/6/9 visible shops to optimize crop allocation?
- **Candidate(s):** Information Gating Logic for V3
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 50 discovery seeds (50000–50049)
- **Method:** Tabulation of shop co-occurrences and calculation of expected Value of Information (VoI).
- **Main Claims:** 4 of 8 shops demand Strawberry; Pet Cafe demands Carrot and Milk; Pizza demands Wheat and Tomato; VoI of waiting to Day 12 justifies multi-stage gating.
- **Raw Artifacts Referenced:** `scratch/empirical_shop_model.json`, `scratch/shop_pair_portfolio_table.json`
- **Code Artifacts Referenced:** `candidates/closed_loop_architecture/shop_transition_model.py`
- **Downstream Decision Impact:** Directly embedded into `CLOSED_LOOP_V3` decision rules.
- **Audit Status:** **HALLUCINATED / BUGGED (GRADE H/F)**. 6 of 8 shop demand profiles were erroneously defined (contradicting `sim.hpp` and `kaggle_environments`). Independent i.i.d. draws with replacement were treated as meaningful Markov transitions on tiny samples ($N=1, 2, 3$).

---

### Report 11: 12-Crop Portfolio Allocation Grid Audit
- **Report #:** R11
- **Date / Timestamp:** 2026-09-11 13:28:00 UTC
- **Title / Filename:** [`scratch/crop_portfolio_sweep_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/crop_portfolio_sweep_results.json)
- **Research Question:** Does any hybrid portfolio of Strawberry and Tomato (e.g. 17S/2T, 15S/4T, 11S/8T) outperform pure 19S/0T Strawberry Bedrock?
- **Candidate(s):** 12 discrete crop allocation mixtures in `kagsim`
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 50 discovery seeds × 2 seats = 100 paired matches
- **Method:** Full-game execution across 12 fixed allocation policies.
- **Main Claims:** Pure Strawberry (19S/0T) strictly dominates all hybrid allocations on mean cash ($97,026), paired margin (+$24.98), win rate (59%), and downside risk.
- **Raw Artifacts Referenced:** `scratch/crop_portfolio_sweep_results.json`
- **Code Artifacts Referenced:** `scratch/crop_portfolio_sweep.py`
- **Downstream Decision Impact:** Proved that static crop diversification severely degrades performance.
- **Audit Status:** **VERIFIED (GRADE A)**. Data confirmed directly; 19S/0T is strictly superior to all static mixtures.

---

### Report 12: Closed-Loop V3 Three-Dataset Validation
- **Report #:** R12
- **Date / Timestamp:** 2026-09-11 13:30:00 UTC
- **Title / Filename:** [`scratch/v3_three_dataset_validation.json`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/v3_three_dataset_validation.json)
- **Research Question:** Does information-aware gating in `CLOSED_LOOP_V3` maintain discovery gains across Qualification and Fresh Holdout partitions?
- **Candidate(s):** `ClosedLoopAgentV3` vs `ClosedLoopAgentV2` vs `Dmitrii-LB2800`
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** Discovery (50000–50049), Qualification (50050–50099), Fresh Holdout (50100–50149)
- **Method:** 100 CRN games per partition per matchup (300 games total per pair).
- **Main Claims:** V3 beat Dmitrii by +$266.42 on Discovery; however, on Fresh Holdout, V3 dropped to -$37.24 vs Dmitrii and regressed by -$41.64 vs V2 with only a 4% win rate against V2.
- **Raw Artifacts Referenced:** `scratch/v3_three_dataset_validation.json`
- **Code Artifacts Referenced:** `scratch/test_v3_candidate.py`
- **Downstream Decision Impact:** Demonstrates that V3 overfit to Discovery and failed generalization on Fresh Holdout. V3 was rightly rejected as a production champion.
- **Audit Status:** **VERIFIED (GRADE A)**. Raw data proves V3 regression on Fresh Holdout.

---

### Report 13: Slack-Capacity Real-Option Analysis Report
- **Report #:** R13
- **Date / Timestamp:** 2026-09-11 14:15:08 UTC
- **Title / Filename:** [`research/slack_capacity_real_option_report.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/slack_capacity_real_option_report.md)
- **Research Question:** Does V2 contain exploitable resource slack (idle tiles, surplus worker hours) that can harvest additive tomatoes without harming the core 19-Strawberry engine?
- **Candidate(s):** Additive Tomato Policies A through H on `ClosedLoopAgentV2`
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** Discovery (50000–50049), Qualification (50050–50099), Fresh Holdout (50100–50149)
- **Method:** Overlay testing in `scratch/run_additive_investigation.py`.
- **Main Claims:** "All 75 tiles are load-bearing"; "Day-11 gap is transient"; "No resource slack exists anywhere in V2"; all tested policies yielded negative margins.
- **Raw Artifacts Referenced:** `scratch/additive_discovery_results.json`, `scratch/qualification_and_holdout_results.json`
- **Code Artifacts Referenced:** `scratch/run_additive_investigation.py`, `scratch/run_slack_qualification.py`
- **Downstream Decision Impact:** Caused the research team to conclude that V2's physical plan cannot be improved through additive cultivation.
- **Audit Status:** **BUGGED EXPERIMENT / OVERCLAIMED (GRADE F/C)**. The experimental overlay was deeply flawed: vacant-tile tomatoes were planted without watering/harvest scheduling (rotting into weeds), and SE-land mode attempted repeated hires every day. The local empirical failure was real, but the universal theorem that "no slack exists anywhere" was invalid.

---

### Report 14: V2 vs Dmitrii Residual-Profit Map & Attribution
- **Report #:** R14
- **Date / Timestamp:** 2026-09-11 14:52:48 UTC
- **Title / Filename:** [`research/v2_dmitrii_residual_profit_map.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v2_dmitrii_residual_profit_map.md)
- **Research Question:** What exact mechanism explains the remaining cash variance between `CLOSED_LOOP_V2` and `Dmitrii-LB2800` across 150 seeds?
- **Candidate(s):** `ClosedLoopAgentV2` vs `Dmitrii-LB2800`
- **Simulator Version:** `kagsim` C++ engine
- **Seeds:** 150 seeds (50000–50149), 300 CRN matches
- **Method:** 150-seed paired margin scan; Step 696 counterfactual intervention on loss seeds.
- **Main Claims:** Overall Win Rate = 54.7%, Mean Margin = +$25.3 (95% CI: [-$2.0, +$51.0]); 100% of physical agronomy is identical; Step 696 market order truncation of 36 Wheat caused the losses; V2 is "confirmed globally superior".
- **Raw Artifacts Referenced:** `scratch/v2_dmitrii_margin_scan.json`, `scratch/forensic_regime_analysis.json`
- **Code Artifacts Referenced:** `scratch/run_margin_scan.py`, `scratch/test_step696_causal.py`
- **Downstream Decision Impact:** Led to the conclusion that V2 is strictly superior to Dmitrii and should remain untouched.
- **Audit Status:** **PARTIALLY VERIFIED / STATISTICALLY OVERCLAIMED (GRADE C)**. 150-seed scan was legitimately run and physical agronomy is indeed identical. However, Table 1 numbers slightly diverged from raw JSON; the Step 696 causal explanation failed counterfactual testing; and claiming "confirmed superiority" when 95% CI crosses zero is statistically invalid.

---

## Summary of Audit Status Across All 14 Reports

| Audit Classification | Reports | Percentage |
|---|:---:|:---:|
| **GRADE A: Fully Verified** | R1, R2, R3, R7, R11, R12 | 42.9% (6/14) |
| **GRADE B: Strongly Supported** | R5, R6 | 14.3% (2/14) |
| **GRADE C: Partially Verified / Overclaimed** | R4, R8, R14 | 21.4% (3/14) |
| **GRADE F: False / Bugged Implementation** | R9, R13 | 14.3% (2/14) |
| **GRADE H: Hallucinated / Unsupported** | R10 | 7.1% (1/14) |

