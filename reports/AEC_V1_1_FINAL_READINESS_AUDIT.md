# FINAL SCIENTIFIC READINESS AUDIT — AEC V1.1

**Evaluation Date:** 2026-09-17  
**Auditor:** Independent Scientific Audit Agent (Read-Only Gate)  
**Codebase Branch / Git HEAD:** `179dd2fb3151b9f89f479375db6a71b6debfaa64` (with development fix pass)  
**Frozen V3 Archive Hash:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (`submission_Vj_kc_v3.tar.gz`)  
**Holdout Partition:** Seeds `340050–340199` (**VIRGIN / UNTOUCHED** — 0 seeds executed)  
**Prospective Tournament Execution:** **ZERO SEEDS EXECUTED**  
**Historical Evidence Integrity:** EXP-AEC-001 and EXP-ARCH-002/003 logs and ledgers **UNTOUCHED / PRESERVED**  

---

## Executive Summary & Final Verdict

This audit constitutes the final read-only scientific evaluation of the **Action-Event-Counterfactual (AEC) Architecture Version 1.1** prior to any prospective seed execution.

The implementation team achieved substantial software engineering improvements:
- 102/102 unit and regression tests pass in 0.73s.
- Authoritative non-linear market pricing (`compute_market_price` from `config.py` and `sim.hpp:110-118`) is integrated into the simulator.
- `FRONTLOAD_ORDERS` commits unambiguously under rival sale pressure, yielding a verifiable positive economic delta.
- The route-continuation spatial tracker immediately detects coordinate drift and prevents blind execution of stale route commands.
- The frozen V3 backbone hash is bit-exact and holdout seeds `340050–340199` remain pristine.

However, a rigorous first-principles audit across microeconomics, simulation physics, causal inference, and reachability demonstrates that **the architecture is NOT ready for immediate prospective preregistration**. Specifically:
1. **The labor opportunity cost formula ($C_{\text{labor}} = \text{fib\_hire\_cost}(\text{hires\_today})/24$) is economically invalid.** It commits a classic sunk-cost fallacy by amortizing a one-time daily acquisition fee over turn count, treating an acquisition expense as a per-step marginal opportunity cost.
2. **The weed decision rule relies on an unverified 48-step heuristic masquerading as a "DETERMINISTIC_PROJECTION".** It ignores essential intermediate dependencies (watering, plant decay, harvest scheduling, cargo drop, and price slippage).
3. **`LOCAL_WEED_DIG` is structurally incapacitated under active V3 play.** Because mutating a movement action triggers the spatial consistency guard fail-closed, the mechanism can only commit when a worker is already idle on a weed tile with an immediate plant command—a synthetic artifact that virtually never occurs in live play.
4. **The market simulation in `simulator.py` deviates from `sim.hpp:578-617`.** The simulator commits Player 0 and updates inventory before quoting Opponent, rather than using the engine's simultaneous two-phase quote-then-commit per-unit lockstep loop.

### Final Classification Verdict

**Verdict: B. READY ONLY AFTER ONE FINAL DEVELOPMENT FIX**

Scientific readiness will be achieved once the **Minimal Development Fix Pass** is executed:
1. Formally **QUARANTINE** `LOCAL_WEED_DIG` from prospective activation (preventing false commits on ungrounded labor costs and unverified 48-step heuristics).
2. Align `simulator.py:execute_market_lockstep` with `sim.hpp:578-617`'s simultaneous two-phase quote-then-commit loop.
3. Deploy AEC V1.1 prospectively solely with `FRONTLOAD_ORDERS` and defense-in-depth fallbacks.

---

## 1. Labor Opportunity Cost — Critical Analysis

### Formal Audit of the Claim
The implementation currently specifies:
$$C_{\text{labor}} = \frac{\text{fib\_hire\_cost}(\text{hires\_today})}{24.0}$$
and labels this an *"engine-grounded replacement labor cost"*.

### Economic Deconstruction & Game Truth
In Kaggle Agriculture (`sim.hpp:658-676`, `config.py:89-95`):
- **A. Recurring Worker Usage Cost:** **DOES NOT EXIST.** Workers do not receive an hourly or per-turn wage. Once a worker is on the board, having that worker execute `PASS`, `MOVE`, or `DIG` incurs exactly **$0.00 in out-of-pocket cash outlay**.
- **B. One-Time Acquisition Cost:** **YES.** The hiring fee `fib(hires_today)` is paid as a lump sum at the instant the `HIRE` order is resolved. At the end of each day (`step % 24 == 23`), all hired hands vanish (`f.n_units = 1; f.hires_today = 0;` in `sim.hpp:738-741`). Hires are strictly non-refundable sunk capital expenditures.
- **C. True Marginal Cost of Worker Assignment:** When a worker is assigned to `DIG` for one turn, the cash cost is **$0.00**. The marginal economic cost is **strictly the opportunity cost of the forgone displaced alternative action** $A_{\text{alt}}$ that the worker was scheduled to execute during that turn.
- **D. Mathematical Nature of the Opportunity Cost:**
  - It is **NOT** `hire_cost / 24`.
  - It is **the net economic payoff of the displaced action** along the worker's temporal task chain.
  - It depends on downstream schedule slack, critical path dependencies, harvest expiration windows, and market timing.
  - **It is NOT expressible as a universal, static dollar number.**

### Concrete Accounting Comparison

Consider an active worker at step $t$ on a farm with $\text{hires\_today} = 0$, where $\text{fib\_hire\_cost}(0) / 24 = 1.0 / 24.0 = \$0.0417$.

#### Case 1: Displaced Action = Route Transit to Mature Harvest
- **Context:** Worker is at (4, 3). Baseline action is `SOUTH` to move to (4, 4), where a 4-yield carrot crop matures at $t+1$. The crop must be harvested at $t+1$ because plant decay will destroy 1 yield unit at $t+2$.
- **Candidate Action:** `DIG` at (4, 3). The worker stays at (4, 3) on step $t$.
- **Downstream Consequence:** The harvest at (4, 4) is delayed by 1 step. Decay occurs before harvest, destroying 1 carrot ($35 base value).
- **Actual Economic Loss:** $-\$35.00$ in cash revenue.
- **Formula Prediction:** $\$0.0417$.
- **Discrepancy:** The formula understates the true opportunity cost by a factor of **839x** ($35.00 vs $0.0417). If decay destroys the whole plant ($140.00), the discrepancy is **3,357x**.

#### Case 2: Displaced Action = Idle Wait (Surplus Labor)
- **Context:** Worker is at (4, 4) waiting for a crop to mature on step $t+3$. Baseline action is `PASS`.
- **Candidate Action:** `DIG` a newly spawned weed at (4, 4).
- **Downstream Consequence:** No harvest, planting, watering, or transit is delayed. The worker was completely idle.
- **Actual Economic Loss:** Exactly **$0.00**.
- **Formula Prediction:** $\$0.0417$.
- **Discrepancy:** The formula penalizes the agent $\$0.0417$ for utilizing otherwise wasted, zero-cost slack capacity.

#### Case 3: Displaced Action = Active Crop Harvesting
- **Context:** Worker is at (4, 4) with baseline action `HARVEST` on mature wheat (yield = 4, price = $25).
- **Candidate Action:** `DIG` (e.g. clearing adjacent tile or invalid command).
- **Actual Economic Loss:** Loss of immediate 4 wheat units ($100.00 cash).
- **Implementation Behavior:** In `asset_value.py:155`, the code attempts to patch this with an ad-hoc clamp: `max(25.0, hire_step_cost) = $25.00`.
- **Discrepancy:** 4 wheat @ $25 = \$100.00$. The hardcoded $25 floor understates the actual lost harvest value by **$75.00** (75% error).

#### Why "Replacement Cost" is a Sunk-Cost Fallacy
The implementation justifies $\text{fib\_hire\_cost} / 24$ by claiming it represents the cost to "replace" one worker-turn of labor. This claim is economically false:
1. **Discrete Indivisibility:** In Kaggle Agriculture, an agent cannot hire a fraction of a worker for 1 turn for $\$0.0417$. An agent can only buy an entire worker for an entire day by paying the full Fibonacci price ($1, $1, $2, $3, $5, $8, $13, $21, $34, $55, $89...) in immediate liquid cash.
2. **Spatial Localization:** A newly hired worker spawns at a shed-access tile (`sim.hpp:664-675`), not at the spatial coordinate where the displaced task occurred. The new worker requires multiple travel turns to reach the task site.
3. **Cash Availability:** If the farm has less cash than the hire price, no replacement is physically possible regardless of willingness to pay.

### Mandatory Formal Statement

> **"fib_hire_cost / 24 IS NOT established as a valid marginal worker-turn opportunity cost"**

---

## 2. Decision Rule Under Projected Value

### The Current Rule
In `aec/evaluation/win_model.py:222-223`:
$$\text{is\_superior} = \text{True} \iff \text{weed\_asset\_val} > 0.0 \quad \text{and} \quad \Delta \text{TerminalMargin}_{\text{sim}} \ge -(C_{\text{opp}} + 5.0)$$

### Logical Coherence Audit
This decision rule suffers from a fundamental temporal and causal flaw:
**Can a candidate have $\text{projected\_asset\_value} > 0$ but actual eventual economic value $< \text{baseline}$?**
**YES. This failure mode is routine and mathematically guaranteed under multiple standard game conditions.**

#### Failure Modes Across the Operational Chain:
1. **Watering & Biological Decay:**
   - In `sim.hpp:756-770`, crops require daily watering. If a plant goes unwatered for 2 consecutive days (`consecutive_dry >= 2`), **it dies and transforms into a weed**.
   - `DownstreamAssetEvaluator` projects gross profit as $\text{Yield} \times \text{Price} - \text{SeedCost} = \$90.00$ based solely on seeing a single `PLANT` command in the 18-step horizon.
   - The evaluator **does NOT verify** that subsequent continuation actions water the plant on Day 1, Day 2, or Day 3.
   - If the V3 backbone does not schedule daily watering on that tile, the plant dies into a weed on Day 2. The $\$10$ seed cost is destroyed, the turn spent digging is wasted, and actual realized revenue is $\$0.00$.
2. **Harvest Scheduling & Physical Rot:**
   - Wheat requires 48 turns (2 full days) to mature. The AEC simulation horizon is $H \le 18$.
   - The simulator **never observes harvest**.
   - If V3's future schedule directs workers to sheep herding or coop maintenance after step 18, the mature wheat sits unharvested until `step_i >= max_lifespan_step`, decaying by 1 yield unit every 2 steps until it turns into a weed (`sim.hpp:720-727`).
3. **Shed Capacity & Transport Bottlenecks:**
   - When harvested, crops enter the worker's backpack. To be sold, the worker must travel to the shed, execute `DROP`, and the shed must have capacity ($< 100$).
   - If the shed is full or the worker never visits the shed, the crop cannot be sold.
4. **Market Degradation:**
   - The valuation evaluates price at current spot price: $P = \text{compute\_market\_price}(\text{crop}, \text{current\_inv})$.
   - 48 turns later, market inventory will have shifted due to rival sales, player sales, and town consumption. Spot price at $t$ is not a bound on price at $t+48$.
5. **Worker Availability Across Days:**
   - If the worker digging the weed is a hired hand (Worker $1 \dots N$), that worker is deleted at the end of the day (`sim.hpp:738`). The evaluator assumes the worker will be available to complete downstream tasks without verifying re-hiring.

### Epistemological Classification

| Classification | Definition | Applies to Weed Asset Value? |
|---|---|---|
| **A. Guaranteed Deterministic Consequence** | Directly caused by the action and guaranteed by game laws regardless of future policy choices. | **NO.** Requires a chain of 5 independent future actions. |
| **B. Conservative Lower Bound** | Minimum guaranteed payoff under adverse future execution. | **NO.** The lower bound under failed downstream execution is $-\$10.00$ (seed loss), not $+\$89.96$. |
| **C. Model-Based Forecast** | Calibrated probabilistic expectation based on empirical policy rollouts. | **NO.** No calibration or empirical transition model is used. |
| **D. Heuristic** | An unverified static point-estimate based on optimistic nominal assumptions. | **YES.** |

### Conservatism Determination
Committing irrevocable live physical actions based on an unverified **Heuristic (D)** that labels itself `DETERMINISTIC_PROJECTION` is **NOT sufficiently conservative for prospective use**. It introduces unhedged execution risk into the tournament agent.

---

## 3. Frontload Engine Semantics — `sim.hpp` vs `simulator.py`

### Background
In the synthetic fixture `test_category_b_frontload_positive_commit`:
- **Baseline:** `[["HIRE", 1], ["SELL", "WHEAT", 50]]`
- **Candidate:** `[["SELL", "WHEAT", 50], ["HIRE", 1]]`
- **Opponent:** `[["SELL", "WHEAT", 50]]`
- **Reported Outcome:** Candidate earns $+\$31.00$ cash delta and $+\$62.00$ terminal margin delta.

### Deep Trace of Engine Order Resolution (`sim.hpp:551-620`)

In `sim.hpp`, order resolution proceeds via the following exact mechanics:

1. **Order Slots:** Orders are processed in an outer loop over slot index $i \in [0, \text{max\_orders}-1]$.
2. **Atomic Resolution:** For slot $i$, atomic orders (`HIRE`, `BUY_LAND`) resolve first in player order ($p=0$, then $p=1$).
3. **Simultaneous Two-Phase Quote-Commit Lockstep:**
   For goods orders (`SELL`, `BUY_PRODUCT`, `BUY_SEED`, `BUY_ANIMAL`), the engine executes a `for (;;)` loop:
   ```cpp
   // sim.hpp:578-605
   for (;;) {
       struct Q { bool ok = false; uint8_t type = 0; uint8_t item = 0; int price = 0; };
       Q q[2];
       // PHASE 1: QUOTE BOTH PLAYERS ON PRE-COMMIT INVENTORY
       for (int p = 0; p < 2; ++p) {
           if (!os[p].live || os[p].remaining <= 0) continue;
           uint8_t t = os[p].type, it = os[p].item;
           if (t == M_SELL && is_product(it)) {
               q[p] = { true, t, it, market_price(it, st.market.inventory[it]) };
           } ...
       }
       if (!q[0].ok && !q[1].ok) break;
       // PHASE 2: COMMIT BOTH UNITS
       bool committed = false;
       for (int p = 0; p < 2; ++p) {
           if (!q[p].ok) continue;
           if (commit_unit(q[p].type, q[p].item, q[p].price, st.farms[p])) {
               os[p].remaining -= 1; committed = true;
           } ...
       }
       if (!committed) break;
   }
   ```
4. **Key Invariant:** In `sim.hpp`, **both players are quoted at the identical pre-commit inventory** before either player's unit commit modifies `st.market.inventory`!

### Forensic Comparison: `sim.hpp` vs Baseline & Candidate

Let us compute the exact mathematical outcome under `sim.hpp` physics:

#### Baseline Trajectory in `sim.hpp`:
- **Slot 0 ($i=0$):**
  - Player 0 submits `HIRE`. Resolves in atomic phase: pays $\text{fib}(0)=\$1$, spawns hand. Player 0 has no goods order (`os[0].live = false`).
  - Player 1 submits `SELL WHEAT 50`.
  - In per-unit loop: Player 0 has no order; Player 1 executes all 50 units sequentially.
  - Inventory climbs from 10,000 to 10,050. Price degrades from $\$25$ to $\$22$.
  - Player 1 earns: **$\$1,127.00$**.
- **Slot 1 ($i=1$):**
  - Player 0 submits `SELL WHEAT 50`. Player 1 has no orders.
  - Player 0 sells all 50 units into already degraded inventory (10,050 $\to$ 10,100).
  - Price degrades from $\$22$ to $\$21$.
  - Player 0 earns: **$\$1,066.00$** (net cash after $\$1$ hire = $\$2,065.00$).

#### Candidate Trajectory in `sim.hpp`:
- **Slot 0 ($i=0$):**
  - Player 0 submits `SELL WHEAT 50`. Player 1 submits `SELL WHEAT 50`.
  - Both orders enter the simultaneous per-unit loop concurrently!
  - In each pass of `for (;;)`:
    - Pass 0: Both quoted at 10,000 ($P=\$25$). Both commit unit 0. Inventory becomes 10,002.
    - Pass 1: Both quoted at 10,002. Both commit unit 1. Inventory becomes 10,004.
    - ...
    - Pass 49: Both quoted at 10,098. Both commit unit 49. Inventory becomes 10,100.
  - Sells alternate unit-by-unit. Both players share the price decline equally!
  - Player 0 earns: **$\$1,097.00$**.
  - Player 1 earns: **$\$1,097.00$**.
- **Slot 1 ($i=1$):**
  - Player 0 submits `HIRE`. Pays $\$1.00$.

#### Causal Difference Under Ground-Truth `sim.hpp`:
- $\Delta \text{money} = \$1,097 - \$1,066 = \mathbf{+\$31.00}$.
- $\Delta \text{opp\_money} = \$1,097 - \$1,127 = \mathbf{-\$30.00}$.
- $\Delta \text{terminal\_margin} = \Delta \text{money} - \Delta \text{opp\_money} = \$31 - (-\$30) = \mathbf{+\$61.00}$.

### Discrepancy in `simulator.py`

In `aec/counterfactual/simulator.py:183-233`:
```python
# Player 0 unit commit
if own_live and own_rem > 0:
    cur_inv = rollout.market_inv.get(own_item, 10000)
    unit_p = compute_market_price(own_item, cur_inv)
    rollout.money += unit_p
    rollout.market_inv[own_item] = cur_inv + 1  # <-- UPDATES INVENTORY IMMEDIATELY

# Player 1 unit commit
if opp_live and opp_rem > 0:
    cur_inv = rollout.market_inv.get(opp_item, 10000)  # <-- SEES ALREADY INCREMENTED INVENTORY
    unit_p = compute_market_price(opp_item, cur_inv)
    rollout.opp_money += unit_p
    rollout.market_inv[opp_item] = cur_inv + 1
```

`simulator.py` executes sequentially within the while loop:
- Player 0 quotes and commits at inventory $K$, updating inventory to $K+1$.
- Opponent quotes and commits at inventory $K+1$, updating inventory to $K+2$.

**Findings:**
1. **Candidate Priority is Real:** The candidate's advantage is **NOT an artifact** of sequential execution. In `sim.hpp`, frontloading produces a causal $+\$31.00$ cash advantage and $+\$61.00$ margin advantage by preventing the opponent from dumping first.
2. **Simulation Approximation:** `simulator.py` reported $+\$62.00$ margin instead of $+\$61.00$ because its sequential unit loop artificially gave Player 0 micro-priority on every individual unit quote over Opponent.
3. **Engine Ordering Parity:** The development simulator is an **approximation** of `sim.hpp`'s two-phase quote-commit structure and should be corrected to two-phase quotes for exact parity.

---

## 4. Reachability Audit

Every mechanism is evaluated against frozen V3's natural execution profile across 100 matches (71,900 turns) in EXP-AEC-001:

| Mechanism | Reachability Classification | Natural Trigger Conditions in V3 | Activation Frequency in EXP-AEC-001 | Empirical Commits |
|---|---|---|---|---|
| **`LOCAL_WEED_DIG`** | **REACHABLE ONLY UNDER SPECIAL STATES** | Worker must be idle (`PASS`) on a weed tile, with continuation tape commanding `PLANT` on that tile without moving. Displacing a `MOVE` triggers spatial desynchronization rejection. | 2,657 opportunities flagged (all abstained due to spatial or economic checks). | **0 commits** (0.00%) |
| **`FRONTLOAD_ORDERS`** | **REACHABLE ONLY UNDER SPECIAL STATES** | V3 must issue an action containing `SELL` preceded by non-`SELL` (occurs only on specific steps: 121, 396, 520, 524, 540, 548) **AND** opponent must simultaneously hold $\ge 3$ mature crop units on their field. | 118 opportunities flagged across 100 matches (~1.18 per match). | **0 commits** (abstained pre-fix; commits post-fix when rival dump is present). |
| **`TERMINAL_LIQUIDATION`** | **DEFENSE-IN-DEPTH / REDUNDANT** | Shed must hold unsold inventory at step 718. Under V3, `H1_DOMINANCE_TERMINAL` systematically liquidates shed between steps 712 and 718. | 0 opportunities flagged across 71,900 turns (shed was 100% empty at step 718). | **0 commits** (0.00%) |
| **`PHASE_SHUTDOWN`** | **DEFENSE-IN-DEPTH / REDUNDANT** | V3 must issue a dead-crop seed purchase (`MELON`) after step 574. Under V3, seed purchases for late crops halt by step 456, and all seed purchases halt after step 624. | 0 patches generated across 71,900 turns (V3 never purchased dead seeds). | **0 commits** (0.00%) |

### Detailed Reachability Findings

1. **`LOCAL_WEED_DIG` is Structurally Quarantined by the Spatial Guard:**
   - In live play, V3's workers are almost never static on weed tiles; they are navigating routes (`MOVE`).
   - If AEC mutates `MOVE` to `DIG`, candidate coordinates diverge at offset 1 (`cur_pos != exp_pos`).
   - The spatial continuation guard immediately flags `spatial_desynchronized = True`, truncates future commands to `PASS`, and rejects the patch fail-closed.
   - The only states where `LOCAL_WEED_DIG` can pass the spatial guard are synthetic fixtures where the baseline action was manually set to `PASS` on the weed tile.
2. **`FRONTLOAD_ORDERS` is the Sole Active Macro-Mechanism:**
   - It is reachable in approximately 1–2 turns per match when V3 issues multi-order actions with preceding `HIRE` orders.
   - When rival dump pressure is present, it commits cleanly without spatial desynchronization because market mutations do not affect physical worker coordinates.
3. **`TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` are Passive Fallbacks:**
   - Neither mechanism modifies normal gameplay. They exist solely as safety netting against baseline catastrophic failure.

---

## 5. Projected-Value Leakage Check

The codebase of `DownstreamAssetEvaluator` (`aec/evaluation/asset_value.py:205-248`) was audited for hidden assumptions:

| Assumption in Valuation Code | Implementation Expression | Epistemological Status | Ground-Truth Physics in `sim.hpp` |
|---|---|---|---|
| **Expected Crop Yield** | `EXPECTED_CROP_YIELDS.get(crop, 4)` | **ASSUMPTION** | In `sim.hpp:46-50, 480-488`, wheat yield is 1 at planting, increments by 1 per watering day up to 6, and decays if unharvested. Yield 4 is an unverified assumption. |
| **Market Spot Price** | `price = compute_market_price(crop, market_inv)` | **ASSUMPTION** | Price at step $t$ is evaluated. Over the 48 steps until crop maturity, town consumption and trades alter price. Future price is unmodeled. |
| **Guaranteed Future Watering** | None (assumed) | **ASSUMPTION** | If unwatered for 2 consecutive days, plant rots into a weed (`sim.hpp:765`). Code does not check continuation watering. |
| **Guaranteed Future Harvest** | None (assumed) | **ASSUMPTION** | Crop must be harvested after maturity. Continuation tape only extends 18 steps; wheat matures in 48 steps. Harvest is unobserved and unverified. |
| **Guaranteed Future Transport & Sale** | None (assumed) | **ASSUMPTION** | Harvested crop must be transported to shed, shed must have capacity, and a `SELL` order must be issued. None of these are verified. |
| **Guaranteed Worker Availability** | None (assumed) | **ASSUMPTION** | Hired hands reset at day boundary (`sim.hpp:738`). Only the main farmer persists across days. |
| **Guaranteed Field Invariance** | None (assumed) | **ASSUMPTION** | Weeds randomly spawn on empty tiles daily (`cfg.weed_chance = 0.005`). Tile status is non-deterministic over 48 turns. |

### Conclusion of Leakage Check
The label `DETERMINISTIC_PROJECTION` in `WeedValuation` is **factually false**. The valuation relies on a chain of **seven unverified assumptions**. The prospective experiment must not treat assumptions as guarantees.

---

## 6. Mechanism-by-Mechanism Readiness Table

| Mechanism | Code Location | Mathematical Grounding | Engine Ordering Parity | Safety & Determinism | Reachability Under V3 | Production Readiness |
|---|---|---|---|---|---|---|
| **`LOCAL_WEED_DIG`** | `aec/opportunities/route.py`, `aec/evaluation/asset_value.py` | **FAILED** (Ungrounded sunk-cost labor model; 7 unverified downstream assumptions). | **N/A** (Physical action; does not alter market). | **PASSED** (Fails closed on coordinate divergence). | **FAILED** (Rejected fail-closed whenever displacing a `MOVE`). | **UNREADY / MUST BE QUARANTINED** |
| **`FRONTLOAD_ORDERS`** | `aec/opportunities/market.py`, `aec/counterfactual/simulator.py` | **PASSED** (Authentic slippage capture; $+\$31$ money, $+\$61$ margin confirmed in `sim.hpp`). | **APPROXIMATE** (Sequential unit loop vs engine's simultaneous two-phase loop). | **PASSED** (Preserves spatial consistency; strictly monotonic cash delta). | **PASSED** (Reachable at steps 121, 396, 520, 524, 540, 548 under rival dump). | **READY** (Requires 2-phase quote alignment). |
| **`TERMINAL_LIQUIDATION`** | `aec/opportunities/terminal.py` | **PASSED** (Simulates immediate cash recovery at terminal boundary). | **IDENTICAL** (Resolves orders at step 718). | **PASSED** (Fail-closed; checks solvency and inventory). | **DEFENSE-IN-DEPTH** (Redundant with V3's native H1 sweep). | **READY** (Passive fallback). |
| **`PHASE_SHUTDOWN`** | `aec/opportunities/terminal.py` | **PASSED** (Prevents unfeasible seed purchase expenditures). | **IDENTICAL** (Drops order at step $t$). | **PASSED** (Fail-closed; strictly cash-preserving). | **DEFENSE-IN-DEPTH** (Redundant with V3's native crop stopping). | **READY** (Passive fallback). |

---

## 7. Exact Remaining Risks

1. **Labor Shadow Price Incomputability:**
   Without a dynamic scheduler, the true marginal opportunity cost of a worker-turn cannot be computed as a scalar. Using $\text{fib\_hire\_cost}/24$ creates ungrounded commits.
2. **Weed Downstream False Positives:**
   If `LOCAL_WEED_DIG` were left active without route splicing, any commit on a static worker would award $+\$89.96$ in projected value for a crop that may never be watered, harvested, or sold.
3. **Market Quote Timing Asymmetry:**
   The sequential unit loop in `simulator.py` introduces a $\$1.00$ margin divergence relative to `sim.hpp:578-617`.
4. **Opponent Pressure Parameter Sensitivity:**
   The rival dump heuristic (`pressure >= 0.5` triggers dump at offset 0) is an assumed behavioral model. If a rival holds mature wheat but delays harvesting/selling, frontloading produces $\$0$ delta (neutral, non-negative).

---

## 8. Final Classification & Minimal Required Fix

### Final Verdict

### **Verdict: B. READY ONLY AFTER ONE FINAL DEVELOPMENT FIX**

### Scientific Justification
AEC V1.1 cannot enter prospective preregistration in its current form because `LOCAL_WEED_DIG` is built upon an economically invalid labor cost formula ($\text{fib\_hire\_cost}/24$) and an unverified 48-step heuristic projection. Furthermore, `LOCAL_WEED_DIG` cannot execute under active V3 play because mutating movement actions triggers fail-closed spatial desynchronization.

However, AEC's architectural core—backbone isolation, fail-closed safety certification, official market pricing, and `FRONTLOAD_ORDERS`—is sound and causally verified against `sim.hpp`.

### Minimal Correction Required Prior to Prospective Preregistration

1. **QUARANTINE `LOCAL_WEED_DIG`:**
   - In `aec/opportunities/route.py` or `aec/evaluation/win_model.py`, mark `LOCAL_WEED_DIG` as `ScientificStatus.QUARANTINED` and force `is_superior = False` (or abstain).
   - This removes the ungrounded labor formula and unverified 48-step heuristic from the prospective decision path entirely.
2. **ALIGN TWO-PHASE QUOTE LOOP IN `simulator.py`:**
   - In `aec/counterfactual/simulator.py:execute_market_lockstep`, refactor the per-unit loop so that Player 0 and Player 1 are both quoted at `market_inv` before either commits their unit, matching `sim.hpp:578-617` exactly.
3. **REGISTER REVISED EXPERIMENT PLAN:**
   - Preregister EXP-AEC-002 with `FRONTLOAD_ORDERS` as the sole active intervention, accompanied by `TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` as defense-in-depth fallbacks.

**Execution Directive:** In strict accordance with the user's instructions:
- **NO SOURCE CODE MODIFICATIONS WERE PERFORMED DURING THIS AUDIT PHASE.**
- **NO PROSPECTIVE SEEDS WERE EXECUTED.**
- **ALL HISTORICAL ARCHIVES AND HOLDOUT PARTITIONS REMAIN PRISTINE.**

---

## 9. Post-Audit Implementation Addendum (2026-09-17)

Following this audit, the two mandated corrections were formally implemented and verified:
1. **`LOCAL_WEED_DIG` Quarantined:** Registered as `ScientificStatus.QUARANTINED` in `config.py`. Executor rejects with `decision="ABSTAIN"`, `abstain_reason="SCIENTIFIC_QUARANTINE"`, and returns exact baseline action.
2. **Two-Phase Lockstep Market Parity:** Refactored `execute_market_lockstep` in `simulator.py` to quote both players from identical pre-commit snapshot (`sim.hpp:578–617`). Simulator now produces exact ground truth: $\Delta M_{\text{our}} = +\$31.00$, $\Delta M_{\text{opp}} = -\$30.00$, $\Delta \text{Margin} = +\$61.00$ (eliminating the $+62$ artifact).
3. **Verification:** All 110 AEC regression tests pass. Full audit details in `reports/AEC_V1_1_FINAL_DEVELOPMENT_FIX.md`.
4. **Status:** Transitioned from **B** to **A. READY FOR PROSPECTIVE PREREGISTRATION**. Preregistration codified in `reports/EXP_AEC_002_PREREGISTRATION.md`. EXP-AEC-002 execution remains strictly halted.
