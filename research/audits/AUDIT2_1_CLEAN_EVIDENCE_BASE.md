# KAGGRICULTURE: CLEAN EVIDENCE BASE (POST-AUDIT 2.1)
## The Definitive, Forensic Evidence Foundation for Agricultural Strategy & Agent Architecture

This document establishes the verified scientific foundation of the Kaggriculture environment and agent performance. Every surviving finding in Tiers A through D has been independently audited and verified from primary simulator source code (`sim.hpp`, `kaggriculture.py`), official tournament replays, raw JSON datasets, and executable scripts during Audit 2.1.

---

## TIER A — SOURCE-PROVEN ENGINE FACTS (Directly Proven from C++ / Python Source)

### A1. Environmental & Temporal Constraints
- **Exact Statement**: The game runs for 720 steps total (Steps 0 to 719), partitioned into 30 days (Days 0 to 29) of 24 steps each. The farm board is 10x10 (100 tiles), divided into NW (unlocked), NE, SW, and SE quadrants. Starting cash is $3,000.00.
- **Scope**: Universal engine invariant across all game modes.
- **Evidence**: `external_repos/kaggriculture-cppsim/sim/sim.hpp:142-146`, `kaggle_environments/envs/kaggriculture/kaggriculture.py:13-16`.
- **Confidence**: 100% (Mathematical certainty).
- **Limitations**: None.

### A2. Town Shop Demand Profiles & Unlock Schedule
- **Exact Statement**: Exactly 8 town shop instances unlock at days 3, 6, 9, 12, 15, 18, 21, and 24. Instances are drawn uniform at random with replacement from 8 types (`rng.choice_index(N_SHOPS)`).
  - `BAKERY`: `EGG, WHEAT` (1.0x)
  - `BRUNCH_SPOT`: `EGG, WHEAT, STRAWBERRY` (1.0x)
  - `FARMERS_MARKET`: `WHEAT, CARROT, TOMATO, STRAWBERRY` (1.0x)
  - `ICE_CREAM_SHOP`: `STRAWBERRY, MILK, WHEAT` (1.0x)
  - `PET_CAFE`: `CARROT` (2.0x single-product multiplier)
  - `PIZZA_SHOP`: `MILK, TOMATO, WHEAT` (1.0x)
  - `SMOOTHIE_SHOP`: `STRAWBERRY, MILK` (1.0x)
  - `YARN_STORE`: `WOOL` (2.0x single-product multiplier)
  - Base draw probabilities: Strawberry 50.0% (4/8), Milk 37.5% (3/8), Wheat 62.5% (5/8), Tomato 25.0% (2/8), Carrot 25.0% (2/8), Egg 25.0% (2/8), Wool 12.5% (1/8).
- **Scope**: Universal engine invariant.
- **Evidence**: `sim.hpp:127-137`, `kaggle_environments.envs.kaggriculture.kaggriculture.SHOPS`.
- **Confidence**: 100%.
- **Limitations**: None.

### A3. Market Execution Cap (`MAX_ORDERS = 10`)
- **Exact Statement**: The market executor enforces a hard limit of 10 orders per player per turn (`std::min(n_orders, 10)`). Orders at array index $\ge 10$ are dropped silently without raising an error. Orders execute strictly in array index order with zero engine priority sorting. Multi-unit orders and atomic orders (HIRE, BUY_LAND) consume 1 slot each.
- **Scope**: Universal engine invariant.
- **Evidence**: `sim.hpp:145, 551-575`, minimal behavioral injection tests.
- **Confidence**: 100%.
- **Limitations**: None.

### A4. Labor Hiring Cost Schedule
- **Exact Statement**: The marginal cost of the $n$-th worker hire on any day follows the Fibonacci sequence: $\text{Cost} = \text{cfg.hire\_mult} \times \text{fib}(n)$ ($1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89$). Cumulative cost for 4 hands is $7.00; for 7 hands is $33.00; for 9 hands is $88.00; for 11 hands is $232.00.
- **Scope**: Universal engine invariant.
- **Evidence**: `sim.hpp:658-663`, `kaggriculture.py`.
- **Confidence**: 100%.
- **Limitations**: None.

### A5. Crop Lifecycle & Rot Kinetics
- **Exact Statement**: Ongoing crops (Strawberry, Tomato) yield up to 4 harvests. Lifespan expires at dawn of the day after harvest 4: $\text{max\_lifespan\_step} = (\text{next\_day} + 1) \times 24$. Once expired, unharvested crops rot at 1 unit per 2 turns on even steps. When yield reaches 0, the tile instantly converts to a weed (`T_WEED`).
- **Scope**: Universal engine invariant for ongoing crops.
- **Evidence**: `sim.hpp:717-726, 770-776`.
- **Confidence**: 100%.
- **Limitations**: Single-harvest crops (Wheat, Carrot, Melon) follow different maturation and lifespan cycles.

### A6. Shed Capacity
- **Exact Statement**: Hard capacity of 100 units total across all crops, products, and animals. Drops and harvests exceeding 100 units are permanently discarded.
- **Scope**: Universal engine invariant.
- **Evidence**: `sim.hpp:147, 501-510`.
- **Confidence**: 100%.
- **Limitations**: None.

### A7. Weed RNG Stream Coupling
- **Exact Statement**: In unpinned simulation, `spawn_weeds` consumes PRNG draws once per empty tile before town shop unlocking. Planting decisions alter the PRNG state, causing identical seeds to reveal completely different town shops.
- **Scope**: Unpinned simulations.
- **Evidence**: `sim.hpp:155-165, 729-750`.
- **Confidence**: 100%.
- **Limitations**: When `--pin-shops` is enabled in `kagsim`, town shops are forced to a fixed sequence.

---

## TIER B — INDEPENDENTLY REPRODUCED EMPIRICAL FACTS

### B1. Cryptographic Integrity of Frozen Submissions
- **Exact Statement**: Active Kaggle live submissions 56146971 and 56146947 match frozen standalone compiled scripts bit-for-bit:
  - `56146947`: `candidates/compiled_v54_plus_shop.py` (SHA256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`)
  - `56146971`: `candidates/compiled_v54_plus_residual.py` (SHA256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`)
- **Scope**: Deployed submission artifacts in repository.
- **Evidence**: SHA256 checksum verification, `research/final_two_agent_deployment.md`.
- **Confidence**: 100%.
- **Limitations**: Pertains strictly to the frozen submission files.

### B2. V2 vs Dmitrii-LB2800 150-Seed Macro Baseline
- **Exact Statement**: Across 150 paired CRN seeds (300 matches spanning Discovery, Qualification, and Holdout):
  - Mean Combined Margin: **+$24.61 coins**
  - Median Margin: **+$58.00 coins**
  - Standard Deviation: **166.75 coins**
  - Standard Error: **13.61 coins**
  - Student's $t$ 95% Confidence Interval ($df=149$): **`[-$2.29, +$51.52]`**
  - Two-sided $t$-test: $t = 1.8078$, $p = 0.0727$
  - Win Rate: **54.67% (82 Wins, 68 Losses, 0 Ties)**
  - Worst Paired Loss: **-$730.0 coins** (Seed 50081)
  - Best Paired Win: **+$326.0 coins** (Seed 50020)
  - Losses $> \$1,000$: **0 / 150 (0.0%)**
- **Scope**: Head-to-head CRN evaluation between `ClosedLoopAgentV2` and `Dmitrii-LB2800` across seeds 50000–50149.
- **Evidence**: Full recalculation from `scratch/v2_dmitrii_margin_scan.json`.
- **Confidence**: 100% on descriptive metrics; failure to reject $H_0$ at $\alpha = 0.05$.
- **Limitations**: Evaluates head-to-head against stationary Dmitrii agent; does not model dynamic human leaderboard meta.

### B3. Statistical Equivalence Bounds (TOST)
- **Exact Statement**: Formal Two One-Sided Tests establish that `ClosedLoopAgentV2` and `Dmitrii-LB2800` are statistically equivalent within an equivalence bound of **$\pm \$50.00$ coins ($p_{\text{TOST}} = 0.0321 < 0.05$)** and $\pm \$75.00$ coins ($p_{\text{TOST}} = 0.0002$). At tighter margins ($\pm \$25.00$), equivalence is not proven ($p_{\text{TOST}} = 0.4887$).
- **Scope**: Same 150 paired CRN seeds.
- **Evidence**: TOST calculation using Student's $t$ with $df=149$.
- **Confidence**: 95% within $\pm \$50$ margin.
- **Limitations**: Dependent on choice of equivalence margin.

### B4. Shed Headroom Threshold 88 Defect & V2 Repair
- **Exact Statement**: In `ClosedLoopAgentV1`, the JIT shed threshold of 88 prematurely purged feed reserves and fertilizer. Raising threshold to 96 with explicit feed reserve protection in `CLOSED_LOOP_V2` safely eliminated premature purges.
- **Scope**: Closed-loop agent architecture.
- **Evidence**: `test_cl_economic_v1.py` traces, `candidates/closed_loop_architecture/closed_loop_v2.py:61-68, 100-105`.
- **Confidence**: High.
- **Limitations**: Pertains to V1 vs V2 shed logic.

### B5. Closed-Loop V3 Overfitting Collapse
- **Exact Statement**: `ClosedLoopAgentV3` beat Dmitrii on Discovery (+264.46), tied on Qualification ($0.00), and collapsed on Fresh Holdout (-$41.64 vs V2, 4.0% win rate, worst loss -$2,082).
- **Scope**: Seeds 50000–50149.
- **Evidence**: `scratch/v3_three_dataset_validation.json`.
- **Confidence**: 100%.
- **Limitations**: Proves that V3 was overfit; does not preclude other adaptive architectures.

---

## TIER C — BOUNDED EMPIRICAL FINDINGS (True Within Explicitly Tested Conditions)

### C1. Static 19S / 0T Strawberry Bedrock Dominance
- **Exact Statement**: Among all 12 evaluated static crop allocations on the 50-seed Discovery partition (100 matches vs Dmitrii), pure 19S/0T Strawberry Bedrock achieved the highest mean cash ($97,026.17), highest margin (+24.98), highest win rate (59.0%), and lowest downside risk (56.72). Introducing static tomato tiles monotonically degraded portfolio margin and win rate.
- **Scope**: Static crop substitutions evaluated on the 50 Discovery seeds (50000–50049).
- **Evidence**: `scratch/crop_portfolio_sweep_results.json`.
- **Confidence**: High within evaluated static grid.
- **Limitations**: Does not evaluate dynamic shop-conditioned crop switching, nor does it guarantee victory on every individual seed.

### C2. Agronomic Divergence Under Runtime Cash Feedback (Seed 50081)
- **Exact Statement**: On Seed 50081, a $4 cash divergence at Step 217 ($950 vs $954) caused V2 to buy only 1 sheep instead of 2 ($497 left < $500). Hand 5 placement failed at Step 259, leaving Tile (1, 4) an empty pasture for 460 turns and producing V2's worst loss (-$730).
- **Scope**: Deterministic paired execution on Seed 50081.
- **Evidence**: Turn-by-turn trace in `scratch/audit2_1_trace_seed50081.py`.
- **Confidence**: 100% reproducible.
- **Limitations**: Specific to Seed 50081, but demonstrates general mechanical vulnerability to runtime cash shortfalls.

### C3. Open-Loop Replay Mirror Performance
- **Exact Statement**: When Dmitrii Base was executed against recorded live opponent action tapes on loss seeds (`test_live_opponents.py`), Dmitrii achieved $90k–$115k vs opponent's $75k–$92k.
- **Scope**: Open-loop replay playback.
- **Evidence**: `test_live_opponents.py`.
- **Confidence**: Moderate.
- **Limitations**: Opponents in recorded replays cannot react to Dmitrii's market transactions; market price feedback is open-loop.

---

## TIER D — STRONG INFERENCES (Mechanistically Supported, Not Experimentally Isolated)

### D1. Live Tournament Loss Attribution
- **Exact Statement**: Live tournament losses (e.g. `episode_107543042.json`, -$55,096 vs ORiginators) were driven primarily by economic specialization mismatch: our submissions produced pure Strawberry into town shop reveals dominated by Double Pizza and Triple Pet Cafe (which boosted Tomato and Carrot at 2.0x, but offered zero boosted Strawberry demand).
- **Scope**: Live tournament matches in non-Strawberry shop worlds.
- **Evidence**: Replay data `episode_107543042.json`, town shop configurations, opponent crop choices and revenues.
- **Confidence**: Strong economic inference.
- **Limitations**: Not counterfactually isolated with an interactive adaptive agent on that exact seed.

---

## TIER E — OPEN HYPOTHESES (Unproven / Requires Investigation)

### E1. Exploitable Spatial Slack on Days 11–12
- **Hypothesis**: Physical idle tiles exist on farm quadrants on Days 11–12 (up to 4 vacant tiles). Whether a correctly scheduled, properly watered and harvested secondary crop can exploit these vacancies profitably without cannibalizing core strawberry revenue remains an open question.
- **Status**: Prior negative proof was invalid (tested bugged code); existence of profitable slack is unproven.

### E2. Cash Buffer Protection at Step 217
- **Hypothesis**: Forcing V2 to maintain a $1,000 cash buffer on Day 9 dawn will eliminate the sheep purchase failure on Seed 50081, raising worst-case performance against Dmitrii.
- **Status**: Plausible mechanistic intervention; unverified in holdout testing.

---

## TIER F — RETRACTED / FALSE CLAIMS (Permanently Discarded)

1. **DISCARDED**: Day-11 Tomato specialization yields +$3,942 alpha on Pizza worlds (cherry-picked single-seed anomaly from -$5,382 ensemble).
2. **DISCARDED**: `shop_transition_model.py` and its Markov transition / VoI tables (6 of 8 shops misstated).
3. **DISCARDED**: Impossibility theorem claiming "no resource slack exists anywhere in V2" (experiment failed to water/harvest crops).
4. **DISCARDED**: Step 696 order truncation as the causal root of V2 losses (V2 diverged at steps 164 and 217; Step 696 was an observational symptom).
5. **DISCARDED**: "CLOSED_LOOP_V2 is confirmed globally superior to Dmitrii-LB2800" (95% CI spans zero, $p = 0.0727$).
6. **DISCARDED**: The "$800 dawn hiring collapse" narrative (Day 12 cash was $9,847, hired 9 hands, Fibonacci costs; resulted from a parser bug).
7. **DISCARDED**: "CLOSED_LOOP_V2 and Dmitrii execute 100.0% bit-for-bit identical physical agronomy" (Seed 50081 diverged for 460 turns; terminal hand planning differs).
