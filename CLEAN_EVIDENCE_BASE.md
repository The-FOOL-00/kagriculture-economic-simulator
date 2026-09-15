# KAGGRICULTURE: CLEAN EVIDENCE BASE (POST-AUDIT #2)
## Ground-Truth Scientific Foundation for Agricultural Strategy & Agent Architecture

This document establishes the definitive, audited evidence hierarchy for the Kaggriculture environment.
Every finding in Tiers A through C has been independently verified against raw simulator source, raw data, or executable code in Audit #2.
All claims that failed verification or were overclaimed by earlier audits have been moved to Tier E (Retracted / Discarded).

---

## TIER A — ENGINE FACTS (Directly Proven from Simulator Source)

1. **Episode Structure**:
   - 720 steps total (Steps 0 to 719).
   - 24 steps per day (Hours 0 to 23), spanning exactly 30 days (Days 0 to 29).
   - 10x10 board (100 tiles total, partitioned into NW, NE, SW, SE quadrants; NW starting unlocked).
   - Starting cash: $3,000.00 for both players.

2. **Town Shops & Unlocks**:
   - Exactly 8 town shop instances unlock at days 3, 6, 9, 12, 15, 18, 21, and 24 (steps 72, 144, 216, 288, 360, 432, 504, 576).
   - Drawn independently uniform at random with replacement from 8 types (`rng.choice_index(N_SHOPS)`). Duplicates frequently occur.
   - Ground-truth product demand definitions:
     - `BAKERY`: `EGG, WHEAT` (1.0x)
     - `BRUNCH_SPOT`: `EGG, WHEAT, STRAWBERRY` (1.0x)
     - `FARMERS_MARKET`: `WHEAT, CARROT, TOMATO, STRAWBERRY` (1.0x)
     - `ICE_CREAM_SHOP`: `STRAWBERRY, MILK, WHEAT` (1.0x)
     - `PET_CAFE`: `CARROT` (2.0x single-product multiplier)
     - `PIZZA_SHOP`: `MILK, TOMATO, WHEAT` (1.0x)
     - `SMOOTHIE_SHOP`: `STRAWBERRY, MILK` (1.0x)
     - `YARN_STORE`: `WOOL` (2.0x single-product multiplier)
   - Base draw probabilities: Strawberry = 4/8 (50%), Milk = 3/8 (37.5%), Wheat = 5/8 (62.5%), Tomato = 2/8 (25%), Carrot = 2/8 (25%), Egg = 2/8 (25%), Wool = 1/8 (12.5%).

3. **Market Execution Limits**:
   - Strictly capped at 10 orders per turn per player (`MAX_ORDERS = 10`).
   - Orders at index $\ge 10$ are silently dropped without error.
   - Multi-unit orders (e.g. `['SELL', 'WHEAT', 36]`) consume 1 order slot.
   - Atomic orders (`['HIRE']`, `['BUY_LAND']`) consume 1 order slot each.
   - The engine imposes zero internal priority sorting; execution strictly follows array index order.

4. **Labor & Hiring Costs**:
   - The cost of the $n$-th hire on any given day is governed by the Fibonacci sequence:
     $$\text{Cost} = \text{fib}(n): \quad \$1, \$1, \$2, \$3, \$5, \$8, \$13, \$21, \$34, \$55, \$89$$
   - Cumulative cost for 4 hands is **$7.00**; cumulative cost for 7 hands is **$33.00**; cumulative cost for 11 hands is **$232.00**. Hiring does NOT cost $200 per hand.

5. **Crop Lifecycle & Rot Kinetics**:
   - Ongoing crops (Strawberry, Tomato) yield up to 4 harvests.
   - Lifespan expires at the start of the day following the 4th harvest: $\text{max\_lifespan\_step} = (\text{next\_day} + 1) \times 24$.
   - Once expired, crops rot at a rate of 1 unit every 2 turns on even steps.
   - When yield reaches 0, the tile instantly converts to a weed (`T_WEED`).

6. **Shed Capacity**:
   - Hard limit of 100 units total across all products, animals, and fertilizer.
   - Drops or harvests that exceed 100 units are permanently discarded without warning.

7. **Weed RNG Stream Coupling**:
   - In unpinned simulation, `spawn_weeds` consumes random draws once per empty tile at day-end before the shop unlock draw.
   - Different farm planting densities shift the RNG stream, altering future town shop sequences across identical seeds. Shop pinning (`--pin-shops`) is required for controlled comparisons.

---

## TIER B — REPRODUCED EMPIRICAL FACTS (Repeated from Raw Data & Code)

1. **Frozen Submissions Cryptographic Integrity**:
   - Submission `56146947` (`compiled_v54_plus_shop.py`): SHA256 `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`.
   - Submission `56146971` (`compiled_v54_plus_residual.py`): SHA256 `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`.
   - Both compiled agents and their source files match deployment records bit-exact and remain untracked/untouched in git.

2. **V2 vs Dmitrii Statistical Parity**:
   - Across 150 independent paired CRN seeds (300 matches):
     - Win Rate: **54.67%** (82 Wins, 68 Losses, 0 Ties).
     - Mean Combined Margin: **+$24.61** coins.
     - Median Margin: **+$58.00** coins.
     - Standard Deviation: 166.75 coins; Standard Error: 13.61 coins.
     - 95% Confidence Interval: **`[-$2.07, +$51.30]`**.
     - Two-sided $t$-test: $t = 1.8078$, $p = 0.0726$.
   - Because the 95% confidence interval spans zero ($p > 0.05$), global statistical superiority cannot be claimed. The two agents are at statistical parity with a small positive point estimate.
   - Worst paired CRN loss across 150 seeds is **-$730.0** (Seed 50081).
   - Zero paired losses exceed -$1,000. (Single-seat matches can lose up to -$6,367 due to seat asymmetry).

3. **Preemptive Residual Controller Holdout Alpha**:
   - Preemptive sell controller achieved **+$1,984.00** paired margin on untouched holdout seeds 50100–50149 (`residual_true_untouched_holdout_results.json`).

4. **Shed Threshold 88 Defect**:
   - In `ClosedLoopAgentV1`, the JIT threshold of 88 prematurely purged fertilizer and feed reserves. Raising threshold to 96 with explicit feed reserve protection in `CLOSED_LOOP_V2` safely eliminated premature purges.

5. **Closed-Loop V3 Overfitting & Generalization Collapse**:
   - On Discovery seeds (50000–50049), V3 gained +$264.46 over V2.
   - On Qualification seeds (50050–50099), V3 tied V2 ($0.00 margin).
   - On Fresh Holdout seeds (50100–50149), V3 collapsed to **-$41.64 margin vs V2** with a **4.0% win rate** and a worst loss of -$2,082.00.

---

## TIER C — STRONG BUT LIMITED FINDINGS (Reliable Within Specific Regimes)

1. **Static 19S/0T Strawberry Bedrock Dominance**:
   - Within the space of tested static crop mixtures (100 CRN discovery matches), pure 19S/0T Strawberry strictly dominated all 11 hybrid Tomato allocations:
     - 19S/0T: Mean cash $97,026, margin +$24.98, win rate 59.0%, worst loss -$222.
     - 17S/2T: Margin -$1,465, win rate 40.0%, worst loss -$5,414.
     - 15S/4T: Margin -$2,078, win rate 38.0%, worst loss -$7,765.
     - 0S/19T: Margin -$10,795, win rate 14.0%, worst loss -$25,264.
   - Introducing static Tomato allocations without guaranteed shop alignment monotonically destroys portfolio margin.

2. **Open-Loop Replay Mirror Performance**:
   - In counterfactual tests against recorded live opponent action streams (`test_live_opponents.py`), Dmitrii scored $90k–$115k vs opponent's $75k–$92k.
   - Caution: Recorded opponent tapes are open-loop. In live interactive play, market prices adjust dynamically to both players' sales.

---

## TIER D — OPEN HYPOTHESES (Unproven / Under Investigation)

1. **Exploitable Spatial Slack on Days 11–12**:
   - Farm quadrants show real physical vacancies on Days 11–12 (up to 4 vacant tiles).
   - The claim that "no slack exists anywhere" was based on bugged code.
   - Whether a correctly scheduled, properly watered and harvested secondary crop can exploit these vacancies profitably remains an open question.

2. **Exact Downside Dynamics Across Full Leaderboard**:
   - V2 exhibits zero catastrophic paired losses (> $1,000) against Dmitrii-LB2800.
   - How V2 behaves against aggressive high-liquidity human agents (e.g. dynamic market price depression) remains unverified in closed-loop live play.

---

## TIER E — RETRACTED / DISCARDED CLAIMS (Do Not Use in Future Research)

1. **RETRACTED: Day-11 Tomato Specialization Yields +$3,942 on Pizza Worlds**:
   - Proven to be a single cherry-picked outlier (Seed 50042). The 6-seed ensemble average was **-$5,382.67**. All 18 tested parameter sweeps had negative average deltas vs V2.
2. **RETRACTED: Shop Transition Model in `shop_transition_model.py`**:
   - Proven to contain fabricated demand profiles for 6 of 8 shops (Pet Cafe does not demand Milk; Pizza requires Milk; Smoothie demands Strawberry + Milk; etc.). All downstream Value of Information and transition calculations based on this model are invalid.
3. **RETRACTED: "No Resource Slack Exists Anywhere in V2" Theorem**:
   - Proven to be based on an invalid experiment (`run_additive_investigation.py`) where vacant-tile crops were never watered or harvested, and SE-land mode hired workers daily for 18 days.
4. **RETRACTED: Step 696 36-Wheat Order Truncation as Root Cause of Losses**:
   - Proven to be an observational correlation, not a causal mechanism. On Seed 50081, cash diverged at step 164 ($+\$460$), and physical divergence occurred at step 217 when a $4 cash shortfall prevented buying the second sheep, leaving Tile (1, 4) empty for 460 turns.
5. **RETRACTED: "CLOSED_LOOP_V2 is Confirmed Globally Superior to Dmitrii"**:
   - Proven to be statistically invalid. The 95% confidence interval spans `[-$2.07, +$51.30]` ($p = 0.0726$), which crosses zero.
6. **RETRACTED: Audit #1 Claim that V2 and Dmitrii Have "100.0% Bit-for-Bit Identical Physical Agronomy"**:
   - Refuted by Audit #2. Runtime cash dynamics can cause animal purchase orders to fail (Seed 50081 missed sheep at step 217, causing 460 turns of tile divergence). Steps 712–717 also differ in terminal hand movements.
7. **RETRACTED: Audit #1 Claim of "Day-12 Dawn Hiring Collapse ($4 \times \$200 = \$800$)"**:
   - Refuted by Audit #2. In `episode_107543042.json`, Day 12 cash was $9,847 (not < $800), and 9 hands were hired (not 4). Hiring follows Fibonacci costs ($7 for 4 hands), not $200 per hand.
