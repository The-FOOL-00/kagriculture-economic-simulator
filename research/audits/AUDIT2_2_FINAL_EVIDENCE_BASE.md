# KAGGRICULTURE: AUTHORITATIVE CLEAN EVIDENCE BASE (POST-AUDIT 2.2)
## The Definitive, Forensic Knowledge Foundation for the Development Phase

**Audit Exercise**: Final Forensic Audit 2.2 Clean Evidence Base  
**Governing Standard**: Missing-Evidence Stop Rule & Absolute Anti-Hallucination Protocol  
**Date**: 2026-09-11  

---

## TIER A — SOURCE-PROVEN ENGINE FACTS (Immutable Simulator Axioms)
*Verified directly from C++ source `sim.hpp` and official Python `kaggle_environments 1.32.7`.*

### A1. Environmental & Temporal Invariants
- **Axiom**: The game runs for exactly 720 steps (Steps 0 to 719), partitioned into 30 days (Days 0 to 29) of 24 steps each. The farm board is 10x10 (100 tiles), divided into NW (unlocked), NE, SW, and SE quadrants. Starting cash is strictly $3,000.00.
- **Evidence**: `sim.hpp:142-146`, `kaggriculture.py:13-16`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

### A2. Authoritative Town Shop Demand Table & Unlock Schedule
- **Axiom**: Exactly 8 town shop instances unlock at days 3, 6, 9, 12, 15, 18, 21, and 24 (steps 72, 144, 216, 288, 360, 432, 504, 576). Instances are sampled uniform at random with replacement from 8 shop types (`rng.choice_index(N_SHOPS)`):
  - `BAKERY`: `EGG, WHEAT` (1.0x multiplier)
  - `BRUNCH_SPOT`: `EGG, WHEAT, STRAWBERRY` (1.0x multiplier)
  - `FARMERS_MARKET`: `WHEAT, CARROT, TOMATO, STRAWBERRY` (1.0x multiplier)
  - `ICE_CREAM_SHOP`: `STRAWBERRY, MILK, WHEAT` (1.0x multiplier)
  - `PET_CAFE`: `CARROT` strictly (2.0x single-product multiplier)
  - `PIZZA_SHOP`: `MILK, TOMATO, WHEAT` all 3 required (1.0x multiplier)
  - `SMOOTHIE_SHOP`: `STRAWBERRY, MILK` (1.0x multiplier)
  - `YARN_STORE`: `WOOL` strictly (2.0x single-product multiplier)
- **Base Draw Probabilities**: Wheat 62.5% (5/8), Strawberry 50.0% (4/8), Milk 37.5% (3/8), Tomato 25.0% (2/8), Carrot 25.0% (2/8), Egg 25.0% (2/8), Wool 12.5% (1/8).
- **Evidence**: `sim.hpp:127-137`, `kaggle_environments.envs.kaggriculture.kaggriculture.SHOPS`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

### A3. Market Execution Cap (`MAX_ORDERS = 10`)
- **Axiom**: The market execution queue enforces a strict per-player hard cap of 10 orders per turn (`min(n_orders, 10)`). Orders at array index $\ge 10$ are dropped silently without raising exceptions. Orders execute strictly in array index order with zero priority sorting. Multi-unit orders and atomic orders (`HIRE`, `BUY_LAND`) consume 1 slot each. Failed orders (e.g. insufficient cash) consume their slot without executing.
- **Evidence**: `sim.hpp:145, 551-575`.
- **Evidence Tier**: **E0 (Primary Source & Behavioral Reproduction)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

### A4. Labor Hiring Cost Schedule (Fibonacci Truth)
- **Axiom**: The marginal cost of the $n$-th worker hire on any day follows the Fibonacci sequence:
  $$\text{Cost} = \text{cfg.hire\_mult} \times \text{fib}(\text{hires\_today})$$
  $$\text{Schedule: } \$1, \$1, \$2, \$3, \$5, \$8, \$13, \$21, \$34, \$55, \$89$$
  Cumulative daily cost: 4 hands = $7.00; 7 hands = $33.00; 9 hands = $88.00; 11 hands = $232.00.
  *(The historical "$200 per hand" rule was an internal agent liquidity reserve heuristic from `closed_loop_v2.py:148`, not an engine rule).*
- **Evidence**: `sim.hpp:658-663`, `kaggriculture.py`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

### A5. Crop Lifecycle & Rot Kinetics
- **Axiom**: Ongoing crops (Strawberry, Tomato) yield up to 4 harvests. Lifespan expires at dawn of the day after harvest 4 ($\text{max\_lifespan\_step} = (\text{next\_day} + 1) \times 24$). Once expired, unharvested crops rot at 1 unit per 2 turns on even steps. When yield reaches 0, the tile instantly converts to a weed (`T_WEED`).
- **Evidence**: `sim.hpp:717-726, 770-776`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

### A6. Shed Capacity
- **Axiom**: Hard capacity of 100 units across all crops, products, and animals. Harvests or market purchases exceeding 100 units are permanently discarded.
- **Evidence**: `sim.hpp:147, 501-510`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

### A7. Weed RNG Stream Coupling
- **Axiom**: In unpinned simulation, `spawn_weeds` consumes random draws once per empty tile before town shop unlocking. Farm planting decisions alter the PRNG sequence, causing identical seeds to reveal completely different town shops unless `--pin-shops` is enabled.
- **Evidence**: `sim.hpp:155-165, 729-750`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% MATHEMATICAL GROUND TRUTH**.

---

## TIER B — INDEPENDENTLY REPRODUCED EMPIRICAL FACTS
*Verified through independent raw-data recomputation and deterministic script execution.*

### B1. Local Cryptographic Integrity of Compiled Submissions
- **Fact**: Local compiled single-file candidates match frozen deployment records bit-exact:
  - `candidates/compiled_v54_plus_shop.py`: 337,768 bytes, SHA256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
  - `candidates/compiled_v54_plus_residual.py`: 338,100 bytes, SHA256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
- **Scope Limitation**: Pertains strictly to local repository binaries. Under Stop Rule #6, official Kaggle server receipt is unverified due to missing server-side API receipts.
- **Evidence**: SHA256 computation against `research/final_two_agent_deployment.md`.
- **Evidence Tier**: **E0 (Local Binaries) / E3 (Server Receipts)**.
- **Status**: **VERIFIED LOCAL INTEGRITY**.

### B2. V2 vs. Dmitrii-LB2800 150-Seed Macro Baseline
- **Fact**: Across 150 paired CRN seeds (300 matches spanning Discovery, Qualification, and Holdout partitions):
  - **Sample Mean Margin**: **+$24.61 coins**
  - **Sample Median Margin**: **+$58.00 coins**
  - **Sample Standard Deviation**: **166.75 coins**
  - **Standard Error**: **13.61 coins**
  - **Student's $t$ 95% Confidence Interval ($df=149$)**: **`[-$2.29, +$51.52]`** (Spans zero)
  - **Standard Normal 95% Confidence Interval ($z=1.96$)**: **`[-$2.07, +$51.30]`** (Spans zero)
  - **Bootstrap 95% Confidence Interval (100k resamples)**: **`[-$2.56, +$50.57]`** (Spans zero)
  - **Two-Sided Paired $t$-test**: $t = 1.8078, df = 149, p = 0.0727$ ($p > 0.05$)
  - **Paired Win Rate**: **54.67% (82 Wins, 68 Losses, 0 Ties)**
  - **Worst Paired Loss**: **-$730.00 coins** (Seed 50081)
  - **Best Paired Win**: **+$326.00 coins** (Seed 50020)
  - **Losses $> \$1,000$**: **0 / 150 (0.0%)**
  - **Cohen's $d$ Effect Size**: **0.1476** (Negligible effect size)
  - **Trimmed Mean (5% cut each tail, 136 seeds)**: **+$36.53 coins**
  - **True Empirical Percentiles**: p01 = -$533.6, p05 = -$198.5, p10 = -$126.2, p25 = -$84.0, p50 = +$58.0, p75 = +$156.0, p90 = +$204.0, p95 = +$224.4, p99 = +$280.7. IQR = $240.0.
- **Inferential Rule**: Because the 95% CI spans zero ($p = 0.0727 > 0.05$), `ClosedLoopAgentV2` is **NOT proven globally superior** to Dmitrii. It is a robust parity baseline.
- **Evidence**: Full recalculation from raw match file `scratch/v2_dmitrii_margin_scan.json`.
- **Evidence Tier**: **E0 (Primary Raw Dataset)**.
- **Status**: **100% MATHEMATICALLY VERIFIED**.

### B3. TOST Statistical Equivalence Bounds
- **Fact**: Formal Two One-Sided Tests establish statistical equivalence in mean payoff within a post-hoc equivalence margin of **$\pm \$50.00$ coins ($p_{\text{TOST}} = 0.0321 < 0.05$)** and $\pm \$75.00$ coins ($p_{\text{TOST}} = 0.0002$). Equivalence is rejected at tighter bounds ($\pm \$25.00$, $p_{\text{TOST}} = 0.4887$).
- **Methodological Limitation**: The $\pm \$50$ margin was selected post-hoc because the 90% confidence interval of the data is $[+\$2.08, +\$47.15]$. Economically, $\$50$ represents mean-score proximity (0.05% of game score), but does NOT prove behavioral identity or eliminate single-seed tail risks.
- **Evidence**: TOST calculation on raw 150 paired differences.
- **Evidence Tier**: **E0 (Math) / E3 (Scientific Pre-specification)**.
- **Status**: **VERIFIED MEAN EQUIVALENCE WITHIN POST-HOC $\pm \$50$ BOUND**.

### B4. Shed Headroom Threshold 88 Defect & V2 Repair
- **Fact**: `ClosedLoopAgentV1`'s shed threshold of 88 prematurely purged fertilizer and feed reserves. Raising threshold to 96 with explicit feed reserve protection in `CLOSED_LOOP_V2` safely eliminated premature purges.
- **Evidence**: `candidates/closed_loop_architecture/closed_loop_v2.py:61-68, 100-105`.
- **Evidence Tier**: **E0 (Primary Source)**.
- **Status**: **100% VERIFIED**.

### B5. Closed-Loop V3 Overfitting Collapse
- **Fact**: `ClosedLoopAgentV3` beat Dmitrii on Discovery (+264.46), tied on Qualification ($0.00), and collapsed on Holdout (-$41.64 vs V2, 4.0% win rate, worst loss -$2,082).
- **Evidence**: `scratch/v3_three_dataset_validation.json`.
- **Evidence Tier**: **E0 (Primary Dataset)**.
- **Status**: **100% VERIFIED**.

---

## TIER C — BOUNDED EMPIRICAL FINDINGS (Strictly Partition-Bounded)
*True within explicitly evaluated parameter grids and seed partitions.*

### C1. Static 19S / 0T Strawberry Bedrock Performance
- **Finding**: Among the 12 evaluated static crop allocations strictly on the 50-seed Discovery partition (100 matches vs Dmitrii), pure 19S/0T Strawberry Bedrock achieved the highest mean cash ($97,026.17), highest margin (+24.98), highest win rate (59.0%), and lowest downside risk (56.72). Introducing static tomato tiles monotonically degraded portfolio margin and win rate.
- **Scope Restriction**: Confined to the 50 Discovery seeds (50000–50049). It was never evaluated on Qualification or Holdout partitions. It does NOT strictly dominate on every individual seed (e.g. Tomato beats Strawberry on Pizza seeds 50042 and 50026).
- **Evidence**: `scratch/crop_portfolio_sweep_results.json`, `crop_portfolio_sweep.py:188`.
- **Evidence Tier**: **E0 (Primary Sweep Dataset)**.
- **Status**: **VERIFIED WITHIN 50-SEED DISCOVERY SET**.

### C2. Agronomic Divergence Under Runtime Cash Feedback (Seed 50081)
- **Finding**: On Seed 50081, a $4 cash deficit at Step 217 ($950 vs $954) caused V2 to buy only 1 sheep instead of 2 ($497 left < $500). Hand 5 placement failed at Step 259, leaving Tile (1, 4) an empty pasture for 460 turns and producing V2's worst loss (-$730).
- **Evidence**: Turn-by-turn trace in `scratch/audit2_1_seed50081_timeline.json`.
- **Evidence Tier**: **E0 (Deterministic Trace)**.
- **Status**: **100% VERIFIED EMPIRICAL DIVERGENCE**.

### C3. Dmitrii Monte Carlo Terminal Planning
- **Finding**: Dmitrii-LB2800 executes a 64-simulation Monte Carlo terminal planner (`ShopClosure`) at steps 712–718 to optimize worker actions and fertilizer collection, while V2 executes PASS.
- **Evidence**: `extracted_agents/dmitrii_lb2800/policy.py:12-45`.
- **Evidence Tier**: **E0 (Primary Source Code)**.
- **Status**: **100% VERIFIED ARCHITECTURAL ASYMMETRY**.

### C4. Open-Loop Replay Mirror Performance
- **Finding**: When Dmitrii Base was executed against recorded live opponent action tapes on loss seeds (`test_live_opponents.py`), Dmitrii scored $90k–$115k vs opponent's $75k–$92k.
- **Scope Restriction**: Subject to open-loop limitations; does not simulate live closed-loop interactive market feedback.
- **Evidence**: `test_live_opponents.py`.
- **Evidence Tier**: **E0 (Open-Loop Playback)**.
- **Status**: **VERIFIED OPEN-LOOP STRENGTH**.

---

## TIER D — STRONG INFERENCES (Mechanistically Grounded, Non-Counterfactual)
*Economically sound explanations supported by data, lacking isolated counterfactual runs.*

### D1. Live Tournament Loss Attribution
- **Inference**: Live tournament losses (e.g. `episode_107543042.json`, -$55,096 vs ORiginators) were driven primarily by economic specialization mismatch: Eldritch produced static Strawberry into town shop reveals dominated by Double Pizza and Triple Pet Cafe (which boosted Tomato and Carrot at 2.0x, but offered zero boosted Strawberry demand).
- **Direct Observation**: Town had 2 Pizza, 3 Pet Cafe, 0 Brunch, 0 Ice Cream. Eldritch sold 0 Tomato, 12 Carrot ($71k). ORiginators sold 152 Tomato, 69 Carrot ($126k).
- **Causal Limitation**: An interactive adaptive counterfactual rerun was not executed on that exact seed. Classified strictly as a strong inference under Stop Rule #5.
- **Evidence**: Official replay `replays/live_tournament/episode_107543042.json`.
- **Evidence Tier**: **E2 (Strong Inference from Observational Replay)**.
- **Status**: **STRONG MECHANISTIC INFERENCE**.

---

## TIER E — OPEN HYPOTHESES (Unproven / Requires Empirical Validation)
*Plausible research directions that must NOT be assumed in development.*

### E1. Exploitable Spatial Slack on Days 11–12
- **Hypothesis**: Physical vacant tiles exist on farm quadrants on Days 11–12 (up to 4 vacant tiles). Whether a correctly scheduled, properly watered and harvested secondary crop can exploit these vacancies profitably without cannibalizing core strawberry revenue remains an open question.
- **Status**: Prior negative proof was invalid (tested bugged code); positive existence of profitable slack is **UNPROVEN (Tier E)**.

### E2. Step 217 Cash Buffer Protection
- **Hypothesis**: Maintaining a $1,000 cash buffer on Day 9 dawn will eliminate the sheep purchase failure on Seed 50081, raising worst-case performance against Dmitrii.
- **Status**: Mechanistically plausible; **UNTESTED IN HOLDOUT (Tier E)**.

---

## TIER F — PERMANENTLY RETRACTED & REFUTED CLAIMS (Dead Hypotheses)
*Permanently banned from development.*

1. **DISCARDED**: Day-11 Tomato specialization yields +$3,942 alpha on Pizza worlds (cherry-picked outlier on Seed 50042; 6-seed ensemble average was -$5,382.67; 18/18 sweep settings negative).
2. **DISCARDED**: `candidates/closed_loop_architecture/shop_transition_model.py` and downstream VoI derivations (6 of 8 shops misstated).
3. **DISCARDED**: Impossibility theorem claiming "no resource slack exists anywhere in V2" (experiment failed to water/harvest crops and hired daily).
4. **DISCARDED**: Step 696 order truncation as the causal root of V2 losses (V2 diverged at steps 164 and 217; Step 696 was an observational symptom; wheat sold at Step 712).
5. **DISCARDED**: Claim that "CLOSED_LOOP_V2 is confirmed globally superior to Dmitrii-LB2800" (two-sided $p = 0.0727 > 0.05$; 95% CI spans zero).
6. **DISCARDED**: The "$800 dawn hiring collapse" narrative (Day 12 dawn cash was $9,847, hired 9 hands, Fibonacci costs; manufactured by parser bug in `reconstruct_live_losses.py:66`).
7. **DISCARDED**: "CLOSED_LOOP_V2 and Dmitrii execute 100.0% bit-for-bit identical physical agronomy" (Seed 50081 diverged for 460 turns; Dmitrii runs Monte Carlo terminal planner at steps 712–718).
