# AUDIT 2.1: MASTER CLAIM LEDGER
## Comprehensive Forensic Verification of All Material Claims Made in Audit 2

This ledger documents the independent verification of every material claim made across the Audit 2 documentation suite (`AUDIT2_SOURCE_MAP.md`, `AUDIT2_ENGINE_FACTS.md`, `AUDIT2_REPRODUCTIONS.md`, `AUDIT2_CORRECTION_LEDGER.md`, `CLEAN_EVIDENCE_BASE.md`, and `AUDIT2_FINAL_VERDICT.md`).

Every claim has been evaluated against primary evidence according to the strict Evidence Hierarchy:
1. Actual simulator/source code (`external_repos/kaggriculture-cppsim/sim/sim.hpp`, official `kaggle_environments 1.32.7`)
2. Actual agent source code (`candidates/closed_loop_architecture/closed_loop_v2.py`, `extracted_agents/dmitrii_lb2800/`)
3. Actual frozen submission code (`candidates/compiled_v54_plus_*.py`)
4. Actual tournament replay JSON (`replays/live_tournament/episode_107543042.json`)
5. Actual experiment output JSON/CSV (`scratch/v2_dmitrii_margin_scan.json`, `scratch/true_pizza_sweep_results.json`, `scratch/crop_portfolio_sweep_results.json`)
6. Reproducible scripts

---

## 1. Master Claim Verification Table

| ID | Audit 2 Claim | Exact Evidence Source | Underlying Artifact | Independently Reproducible? | Correct? | Overstated? | Status |
|:---|:---|:---|:---|:---:|:---:|:---:|:---|
| **CLM-01** | Episode length is exactly 720 steps (Steps 0 to 719), 24 steps per day (30 days total), board size 10x10 (100 tiles), starting cash $3,000.00. | `sim.hpp:142-146`, `kaggriculture.py:13-16` | `external_repos/kaggriculture-cppsim/sim/sim.hpp` | YES | YES | NO | **VERIFIED** |
| **CLM-02** | Town shops unlock every 3 days at steps 72, 144, 216, 288, 360, 432, 504, 576 (8 total instances). | `sim.hpp:149, 745`, `kaggriculture.py` | `kagsim` C++ engine | YES | YES | NO | **VERIFIED** |
| **CLM-03** | Town shop instances are sampled uniform at random with replacement from 8 shop types; duplicate shops frequently occur. | `sim.hpp:121-124, 748` (`rng.choice_index(N_SHOPS)`) | `sim.hpp`, tournament replay `107543042` | YES | YES | NO | **VERIFIED** |
| **CLM-04** | The authoritative town shop demand table has: Bakery (Egg, Wheat), Brunch (Egg, Wheat, Strawberry), Farmers Market (Wheat, Carrot, Tomato, Strawberry), Ice Cream (Strawberry, Milk, Wheat), Pet Cafe (Carrot only, 2x), Pizza (Milk, Tomato, Wheat), Smoothie (Strawberry, Milk), Yarn Store (Wool only, 2x). | `sim.hpp:127-137`, `kaggle_environments` `kg.SHOPS` | `sim.hpp`, `kaggriculture.py` | YES | YES | NO | **VERIFIED** |
| **CLM-05** | `shop_transition_model.py` misstated demand profiles for 6 out of 8 shops, invalidating downstream transition and VoI models. | `candidates/closed_loop_architecture/shop_transition_model.py:22-31` | `shop_transition_model.py` | YES | YES | NO | **VERIFIED** |
| **CLM-06** | Engine market execution is strictly capped at `MAX_ORDERS = 10` per player per turn; orders at index $\ge 10$ are silently dropped without error. | `sim.hpp:145, 554`, behavioral injection test | `sim.hpp`, `kagsim` minimal test | YES | YES | NO | **VERIFIED** |
| **CLM-07** | Market order execution order follows array index order with zero internal priority sorting; atomic orders (HIRE, BUY_LAND) and multi-unit orders consume 1 slot each. | `sim.hpp:551-575` | `sim.hpp`, `kagsim` injection test | YES | YES | NO | **VERIFIED** |
| **CLM-08** | Worker hiring costs follow the Fibonacci sequence: $\text{Cost} = \text{cfg.hire\_mult} \times \text{fib}(\text{hires\_today})$ ($1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89$). Cumulative cost for 4 hands is $7.00; for 7 hands is $33.00; for 11 hands is $232.00. | `sim.hpp:658-663`, `kaggriculture.py` | `sim.hpp`, `kaggriculture.py` | YES | YES | NO | **VERIFIED** |
| **CLM-09** | The "$200 per hand" hiring cost cited in Audit 1 and earlier reports was an agent heuristic (`closed_loop_v2.py:148`) mistaken for an engine rule; no $800 threshold exists in the engine. | `closed_loop_v2.py:148`, `liquidity_controller.py:32` | Agent source files | YES | YES | NO | **VERIFIED** |
| **CLM-10** | Ongoing crops (Strawberry, Tomato) yield up to 4 harvests, expire at dawn of the day after harvest 4, and rot at 1 unit per 2 turns on even steps until turning into weeds. | `sim.hpp:717-726, 775` | `sim.hpp` | YES | YES | NO | **VERIFIED** |
| **CLM-11** | In unpinned simulation, `spawn_weeds` consumes random draws once per empty tile before town shop unlocking, coupling farm planting to future shop reveals. | `sim.hpp:155-165, 735, 748` | `sim.hpp` comments and code | YES | YES | NO | **VERIFIED** |
| **CLM-12** | Shed capacity is strictly 100 units; harvests or drops exceeding 100 are silently and permanently discarded. | `sim.hpp:147, 501-510` | `sim.hpp` | YES | YES | NO | **VERIFIED** |
| **CLM-13** | Tomato specialization +$3,942 cash gain on Pizza worlds was a cherry-picked single seed (50042); the 6-seed True Pizza ensemble delta vs V2 was -$5,382.67. | `scratch/test_tomato_with_sales.py`, raw execution | `test_tomato_with_sales.py` | YES | YES | NO | **VERIFIED** |
| **CLM-14** | All 18 parameter combinations in `scratch/true_pizza_sweep_results.json` produced negative mean cash deltas vs V2 (ranging from -$2,332.67 to -$2,499.33). | `scratch/true_pizza_sweep_results.json` | `true_pizza_sweep_results.json` | YES | YES | NO | **VERIFIED** |
| **CLM-15** | The additive slack capacity experiment (`run_additive_investigation.py`) was invalid because `VACANT_TILES` never scheduled watering or harvesting, and `SE_LAND` hired workers daily for 18 days. | `scratch/run_additive_investigation.py:143, 154-164, 167-193` | `run_additive_investigation.py` | YES | YES | NO | **VERIFIED** |
| **CLM-16** | The failure of `run_additive_investigation.py` invalidates the prior "no slack exists" proof, but does NOT prove that profitable slack exists. | `AUDIT2_REPRODUCTIONS.md:71`, `AUDIT2_FINAL_VERDICT.md:84` | Logical derivation | YES | YES | NO | **VERIFIED** |
| **CLM-17** | Step 696 order truncation of 36 Wheat was not the causal root of V2 losses against Dmitrii; V2 had already diverged in cash at step 164 ($+\$460$) and physically at step 217. | `scratch/audit2_1_trace_seed50081.py`, turn-by-turn trace | C++ simulator trace | YES | YES | NO | **VERIFIED** |
| **CLM-18** | On Seed 50081, V2 entered Step 217 with $950 cash vs Dmitrii's $954 ($4 deficit); V2 bought only 1 sheep ($497 left < $500), causing Hand 5 placement failure at Step 259 and 460 turns of tile divergence. | `scratch/audit2_1_trace_seed50081.py`, `timeline.json` | Turn-by-turn trace | YES | YES | NO | **VERIFIED** |
| **CLM-19** | Audit 1's counterfactual script (`test_step696_causal.py`) was imperfect because forcing Dmitrii's orders stripped V2's legitimate JIT strawberry sales, worsening loss on Seed 50081 from -$730 to -$818. | `scratch/test_step696_causal.py:25` | `test_step696_causal.py` | YES | YES | NO | **VERIFIED** |
| **CLM-20** | Across 150 paired CRN seeds (300 matches), V2 vs Dmitrii achieved: Mean combined margin +$24.61, Median +$58.00, Std 166.75, SE 13.61, Win Rate 54.67% (82W-68L), t = 1.8078, p = 0.0726. | `scratch/v2_dmitrii_margin_scan.json`, recomputed | `v2_dmitrii_margin_scan.json` | YES | YES | MINOR (Normal z used for CI) | **VERIFIED WITH SCOPE LIMIT** |
| **CLM-21** | Audit 2 reported 95% CI as `[-$2.07, +$51.30]`, which was derived using standard normal critical value $z=1.96$; Student's $t_{149}$ yields `[-$2.29, +$51.52]`. Both cross zero. | Recomputed via `scipy.stats.t.ppf(0.975, 149)` | Statistical script | YES | YES | NO | **VERIFIED WITH SCOPE LIMIT** |
| **CLM-22** | Because the 95% CI spans zero ($p = 0.0727 > 0.05$), declaring V2 "confirmed globally superior" violates classical inference; V2 is not proven superior. | `AUDIT2_REPRODUCTIONS.md:125`, statistical recomputation | Theoretical statistics | YES | YES | NO | **VERIFIED** |
| **CLM-23** | "The two agents are at statistical parity": Failure to reject $H_0$ ($p = 0.0727$) is not proof of equivalence; formal TOST proves equivalence only for margins $\Delta \ge \pm \$50$. | TOST recomputation ($p_{\text{TOST}}=0.0321$ for $\pm \$50$, $0.4887$ for $\pm \$25$) | Statistical script | YES | PARTIAL | YES | **PARTIALLY VERIFIED** |
| **CLM-24** | Zero paired CRN losses against Dmitrii exceeded -$1,000 across 150 seeds; worst combined loss was -$730.0 (Seed 50081). | `scratch/v2_dmitrii_margin_scan.json` | `v2_dmitrii_margin_scan.json` | YES | YES | NO | **VERIFIED** |
| **CLM-25** | R14 Table 1 contained reporting transcription errors: Discovery mean published +$28.8$ vs true +$39.12$; Qual published +$0.5$ vs true +$11.40$; Holdout published +$46.4$ vs true +$23.32$. | `v2_dmitrii_margin_scan.json` vs R14 Table 1 | Raw JSON vs Report | YES | YES | NO | **VERIFIED** |
| **CLM-26** | Active live submissions 56146971 (`compiled_v54_plus_residual.py`) and 56146947 (`compiled_v54_plus_shop.py`) match frozen SHA256 hashes bit-exact. | SHA256 computation: `18402ec6...` and `f651ccd2...` | Filesystem binaries | YES | YES | NO | **VERIFIED** |
| **CLM-27** | In tournament replay `episode_107543042.json`, Eldritch had $9,847 cash on Day 12 dawn, hired 9 hands (did not drop from 7 to 4), and paid Fibonacci hiring costs ($88 for 9 hires). | `replays/live_tournament/episode_107543042.json:steps[288, 289]` | Official replay JSON | YES | YES | NO | **VERIFIED** |
| **CLM-28** | The "$800 dawn hiring collapse" was a false narrative produced by a parser bug in `scratch/reconstruct_live_losses.py:66` (`f.get("units", [])` returning empty list). | `scratch/reconstruct_live_losses.py:66` | Parser script | YES | YES | NO | **VERIFIED** |
| **CLM-29** | The live loss in `episode_107543042.json` was driven by crop-demand mismatch: town unlocked Double Pizza, Triple Pet Cafe, Zero Brunch, Zero Ice Cream; opponent produced Tomato/Carrot ($126k) while Eldritch produced unboosted Strawberry ($71k). | `episode_107543042.json:final_obs`, economic breakdown | Replay JSON | YES | YES | MINOR (Inferred vs proven causal) | **VERIFIED WITH SCOPE LIMIT** |
| **CLM-30** | V2 and Dmitrii-LB2800 do NOT execute 100.0% bit-for-bit identical physical agronomy; runtime cash feedback triggers animal purchase failures (Seed 50081), and Dmitrii runs a terminal planner at 712-717 while V2 executes PASS. | `scratch/audit2_1_trace_seed50081.py`, `policy.py:12-14` | C++ trace, agent source | YES | YES | NO | **VERIFIED** |
| **CLM-31** | Dmitrii executes a 64-simulation Monte Carlo terminal planner (`ShopClosure`) at steps 712–718 that moves hands and collects fertilizer. | `extracted_agents/dmitrii_lb2800/policy.py:12-14, 129-148` | Agent source code | YES | YES | NO | **VERIFIED** |
| **CLM-32** | Pure 19S/0T Strawberry Bedrock "strictly dominates all static hybrid crop allocations" within `crop_portfolio_sweep_results.json`. | `scratch/crop_portfolio_sweep_results.json` | Sweep JSON (50 discovery seeds) | YES | YES | YES (Only mean margin on discovery set) | **VERIFIED WITH SCOPE LIMIT** |
| **CLM-33** | Replacing Strawberry with Tomato in static allocations monotonically degrades portfolio margin, win rate, and downside risk across the 12 tested configurations. | `scratch/crop_portfolio_sweep_results.json` | Sweep JSON | YES | YES | NO | **VERIFIED** |
| **CLM-34** | `ClosedLoopAgentV1` prematurely purged fertilizer and feed reserves at shed threshold 88; raising threshold to 96 with explicit feed reserve protection in V2 resolved the defect. | `candidates/closed_loop_architecture/closed_loop_v2.py:61-68, 100-105` | Agent source code | YES | YES | NO | **VERIFIED** |
| **CLM-35** | `ClosedLoopAgentV3` suffered severe holdout generalization collapse (-$41.64 margin vs V2, 4.0% win rate, worst loss -$2,082) despite winning on Discovery (+264). | `scratch/v3_three_dataset_validation.json` | Validation JSON | YES | YES | NO | **VERIFIED** |
| **CLM-36** | In counterfactual tests against recorded live opponent action streams (`test_live_opponents.py`), Dmitrii scored $90k–$115k vs opponent's $75k–$92k. | `test_live_opponents.py`, counterfactual traces | Counterfactual script | YES | YES | YES (Open-loop playback caution) | **VERIFIED WITH SCOPE LIMIT** |

---

## 2. Status Breakdown Summary

- **Total Material Claims Audited**: 36
- **VERIFIED (Fully supported without reservation)**: 30 (83.3%)
- **VERIFIED WITH SCOPE LIMIT (Correct empirical core, but requires explicit boundary/scope narrowing)**: 5 (13.9%)
  - CLM-20 / CLM-21 (Normal critical value vs Student's t critical value for CI)
  - CLM-29 (Live loss economic mismatch: strongly supported inference, not counterfactually isolated)
  - CLM-32 (19S/0T Strawberry dominance: true for mean margin on 50-seed Discovery set, not universal game-theoretic strict dominance)
  - CLM-36 (Dmitrii vs live opponents: valid open-loop playback, subject to non-interactive replay limitations)
- **PARTIALLY VERIFIED (Material conclusion overstated or statistically incomplete)**: 1 (2.8%)
  - CLM-23 (Claiming "statistical parity is established" without performing formal equivalence tests)
- **UNVERIFIED**: 0 (0.0%)
- **FALSE**: 0 (0.0%)
- **METHODOLOGICALLY INVALID**: 0 (0.0%)
- **NOT MATERIAL**: 0 (0.0%)

---

## 3. Epistemic Audit Conclusion

Audit 2 represents an extraordinarily rigorous forensic re-evaluation of Audit 1. **Zero material findings of Audit 2 are false, fabricated, or methodologically broken.** Every major retraction asserted by Audit 2 (R1 through R6) and every engine correction is confirmed bit-for-bit. The 6 claims requiring scope limitation or correction are technical refinements (Student's t CI vs normal z CI, formal equivalence margins vs informal parity, decision-theoretic definition of dominance, and explicit labeling of economic inference vs counterfactual proof).
