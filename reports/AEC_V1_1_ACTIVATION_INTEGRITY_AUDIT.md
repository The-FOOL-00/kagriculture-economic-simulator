# AEC V1.1 Scientific Activation Integrity Audit

**Author:** Independent Scientific Audit Agent  
**Date:** 2026-09-17  
**Git HEAD:** `179dd2fb3151b9f89f479375db6a71b6debfaa64`  
**Frozen V3 Tarball SHA256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (`submission_Vj_kc_v3.tar.gz`)  
**Holdout Partition:** `340050–340199` (Status: **VIRGIN / UNTOUCHED**)  
**Audit Purpose:** Evaluate whether the newly activated mechanisms in AEC V1.1 are scientifically justified, causally sound, and mathematically grounded enough to enter a prospective experiment.

---

## A. Executive Verdict

### **Verdict: READY ONLY AFTER SPECIFIC DEVELOPMENT FIXES**

The AEC V1.1 activation represents significant software engineering progress over V1.0: unit tests execute rapidly (84/84 passed), safety invariants are strictly enforced, fail-closed abstention returns bit-exact baseline actions, and the frozen V3 backbone hash remains unchanged.

However, a rigorous scientific audit of the activation mechanisms reveals **critical mathematical, causal, and empirical discrepancies** that disqualify V1.1 from immediate prospective deployment:

1. **Critical Fixture Discrepancy in `FRONTLOAD_ORDERS`:**
   The development test report (`TR-AEC-V1.1-20260917`) claimed 4 synthetic mechanism commits. In reality, **`FRONTLOAD_ORDERS` does NOT commit in its own positive synthetic fixture** (`test_synthetic_frontload_positive`). When `executor.act()` executes in that fixture, it produces `Decision: ABSTAIN` (`NO_CANDIDATE_CERTIFIED_SUPERIOR`) because the simulator produces `delta_margin = $0.0` and `delta_money = $0.0`. The test silently passed because it only asserted that an opportunity was detected and a patch was generated; it never asserted a commit!
2. **Ungrounded Labor Wage Parameter ($100/day):**
   The labor opportunity cost $C_{\text{labor}} = \$100 / 24 = \$4.1667/\text{step}$ in `LOCAL_WEED_DIG` is **not an actual game constant**. Kaggle Agriculture defines worker hire costs via a daily Fibonacci sequence ($1, $1, $2, $3, $5, $8...), while the starting farmer has zero wage. The $100 flat daily rate is an assumed heuristic introduced in V1.1.
3. **100% Extrapolated Downstream Asset Value:**
   In `LOCAL_WEED_DIG`, the 18-step simulation horizon is physically incapable of observing wheat maturity (requires 48 steps / 2 days). The reported $+85.83$ economic gain is **not simulated**; it is 100% extrapolated by a static formula based on nominal yield and spot price.
4. **Open-Loop Continuation Desynchronization:**
   AEC continues candidate simulation using the frozen V3 baseline route tape ("baseline future tape plus local patch"). If a worker executes `DIG` at step 0 instead of moving, subsequent route steps assume the worker is at the baseline position, desynchronizing all downstream physical operations.
5. **Redundancy of Terminal and Phase Mechanisms:**
   `TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` are verified to be effectively unreachable under normal V3 play (0 commits in EXP-AEC-001) and function purely as defense-in-depth fallbacks.

Immediate prospective evaluation (EXP-AEC-002) MUST BE HALTED until these specific flaws are corrected and verified.

---

## B. LOCAL_WEED_DIG Validity

### 1. Complete Mathematical & Execution Path
The complete evaluation path proceeds as follows:
$$\text{OBSERVE} \to \text{WEED DETECTION} \to \text{DOWNSTREAM DEPENDENCY} \to \text{ASSET VALUE} \to \text{COUNTERFACTUAL} \to \text{WIN MODEL} \to \text{SAFETY} \to \text{COMMIT}$$

* Code Locations:
  - Detection: [`aec/opportunities/route.py:26-45`](file:///c:/Users/Sundareswaran/Kagriculture/aec/opportunities/route.py#L26-L45)
  - Patch Generation: [`aec/patches/generator.py:71-83`](file:///c:/Users/Sundareswaran/Kagriculture/aec/patches/generator.py#L71-L83)
  - Horizon Selection: [`aec/counterfactual/horizon.py:41-53`](file:///c:/Users/Sundareswaran/Kagriculture/aec/counterfactual/horizon.py#L41-L53)
  - Asset Valuation: [`aec/evaluation/asset_value.py:74-205`](file:///c:/Users/Sundareswaran/Kagriculture/aec/evaluation/asset_value.py#L74-L205)
  - Strategic Gate: [`aec/evaluation/win_model.py:137-171`](file:///c:/Users/Sundareswaran/Kagriculture/aec/evaluation/win_model.py#L137-L171)
  - Safety & Commit: [`aec/integration/executor.py:337-405`](file:///c:/Users/Sundareswaran/Kagriculture/aec/integration/executor.py#L337-L405)

### 2. Origin and Classification of the $100 Parameter
- **Finding:** In Kaggle Agriculture (`sim.hpp`, `config.py:89-95`), there is **no game-defined wage of $100**.
- **Game Mechanics:** Farmer labor is free. Hired farm hands cost `fib_hire_cost(hires_today)`: $1 for 1st hand, $1 for 2nd, $2 for 3rd, $3 for 4th, $5 for 5th, $8 for 6th, $13 for 7th, $21 for 8th, $34 for 9th, $55 for 10th, $89 for 11th. A team hiring 11 hands spends a total of $232 for the entire day across all 11 hands.
- **Classification:** **MODELING ASSUMPTION / HEURISTIC**. The $100 figure was chosen as an intuitive round proxy for daily worker productivity / marginal hire cost of an 11th worker ($89), but it has no formal status as a game constant.

### 3. Verification of Units
- Equation: $C_{\text{labor}} = \frac{\$100.0}{\text{TURNS\_PER\_DAY}} = \frac{\$100.0}{24} = \$4.1667 \text{ per worker-turn}$.
- In the simulation, each step consists of 1 turn per active worker. If an entire worker-day is valued at $100, then allocating 1 worker for 1 turn represents $\frac{1}{24}$ of that worker's daily capacity ($\$4.1667$).
- **Legitimacy:** The units ($\$/\text{worker-turn}$) are dimensionally consistent with step-level opportunity cost, but the magnitude is arbitrary.

### 4. Double Counting Audit
Does the system count economic value multiple times across simulation, asset valuation, and terminal margin?
- **Analysis:**
  In `WinModel.evaluate` ([`aec/evaluation/win_model.py:158`](file:///c:/Users/Sundareswaran/Kagriculture/aec/evaluation/win_model.py#L158)):
  ```python
  if weed_asset_val > 0.0 and delta_margin >= -(weed_val.opportunity_cost + 0.05):
      is_superior = True
  ```
  And in `EvaluationResult`:
  `terminal_margin_delta = delta_margin` (from simulation)
  `weed_asset_value = weed_asset_val` (from asset evaluator)
- **Equation of Quantities:**
  $$\text{Strategic Metric} = \begin{cases} \text{Candidate Accepted} & \text{if } \text{WEED\_VALUE} > 0 \text{ and } \Delta \text{TerminalMargin}_{\text{sim}} \ge -(C_{\text{labor}} + 0.05) \\ \text{Candidate Rejected} & \text{otherwise} \end{cases}$$
- **Numerical Cases:**
  *Case 1: Standard Short Horizon ($H = 18 < 48$ growth steps)*
  - Simulation output: $\Delta \text{money}_{\text{sim}} = \$0.0$, $\Delta \text{TerminalMargin}_{\text{sim}} = \$0.0$.
  - Asset valuation: $\text{WEED\_VALUE} = \$90.0 - \$4.17 = +\$85.83$.
  - Result: No double counting occurs because the simulation captures $0.0$ crop profit. The benefit is counted **strictly once** by asset valuation.
  *Case 2: Long Horizon ($H \ge 48$ growth steps with mature harvest)*
  - If a simulation ran for 60 steps and completed a harvest and sale:
    $\Delta \text{TerminalMargin}_{\text{sim}} = +\$90.0$.
    $\text{WEED\_VALUE} = +\$85.83$.
  - In `AEC_V1_1_DESIGN.md` line 110, the theoretical formula was specified as:
    $$\Delta \text{strategic} = \Delta \text{terminal\_margin} + \text{WEED\_VALUE}$$
    If this summation were evaluated, total delta would be $\$90.0 + \$85.83 = \$175.83$ (DOUBLE COUNTING).
  - **Code Audit:** In `aec/evaluation/win_model.py`, this summation is **NOT computed**. Instead, `estimate_p_win` uses only `outcome.delta_terminal_margin`, and candidate sorting uses `expected_p_win`. However, because `delta_terminal_margin` is $0.0$ in short horizons, multiple weed candidates receive identical heuristic p_win ($0.5000$).
- **Classification of Asset Value:** **EXTRAPOLATED OPPORTUNITY VALUE**. It is neither realized cash nor simulated margin; it is a modeled future expectation.

---

## C. FRONTLOAD_ORDERS Validity

### 1. Verification of the Positive Synthetic Fixture
In `tests/aec/test_v1_1_activation.py` lines 554–580 (`test_synthetic_frontload_positive`):
```python
base_act = {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1], ["SELL", "WHEAT", 5]]}
obs = copy.deepcopy(normal_opening_obs)
obs["private"]["shed"]["WHEAT"] = 10
obs["farms"][0]["money"] = 150.0

adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
executor = AECExecutor(backbone_adapter=adapter)
action = executor.act(obs)
```
- **Audit Execution Result:**
  Running this exact snippet through Python yields:
  ```
  Decision: ABSTAIN
  Committed mech: None
  Abstain reason: NO_CANDIDATE_CERTIFIED_SUPERIOR
  Action returned: {'farmer': ['PASS'], 'hands': [], 'market': [['BUY_SEED', 'WHEAT', 1], ['SELL', 'WHEAT', 5]]}
  Candidate 0: delta_margin: 0.0, delta_money: 0.0, commit: False
  Economic rejection reason: Frontload produces identical monetary outcome: margin delta $0.0, cash delta $0.0
  ```
- **Finding:** The positive synthetic fixture **FAILS TO COMMIT**.
  AEC rejected the patch because baseline and candidate achieved identical cash ($255.0) and margin ($0.0).
  The test only asserted:
  `assert len(frontload_opps) == 1` and `assert len(patches) == 1`.
  It NEVER asserted `assert executor.latest_telemetry.decision == "COMMIT"`.
  The claim in `AEC_V1_1_TEST_REPORT.md` that 4 mechanism commits were verified is **factually incorrect**.

### 2. Lockstep Simulation & Price Mechanics Classification
Tracing `execute_market_lockstep` in `aec/counterfactual/simulator.py:111-171`:

| Component | Classification | Finding / Flaw |
|---|---|---|
| Order Reordering (`reorder_frontload`) | **REAL CODE LOGIC** | Partitions SELL before BUY_PRODUCT before Capital orders deterministically. |
| Opponent Order Generation | **MOCKED / INACTIVE** | In `test_synthetic_frontload_positive`, opponent has no crops, so `opp_orders = []`. Zero rival orders exist. |
| Price Degradation Rule | **TOY MOCK MECHANIC** | Simulator uses `max(1, price - actual_sell // 2)`. Real Kaggle Agriculture uses non-linear curves (`compute_market_price`) where 5 wheat changes price by $< \$0.01$. |
| Price Update Timing | **ENGINE DIVERGENCE** | Simulator degrades price per order within step. In Kaggle Agriculture, prices update at step boundary after all orders resolve. |
| Hire Cost in Market | **MOCKED ASSUMPTION** | Simulator hardcodes `hire_cost = 100.0`. Real engine uses Fibonacci. |

**Conclusion:** `FRONTLOAD_ORDERS` does not have a working positive synthetic validation and its simulation model is detached from real engine price physics.

---

## D. TERMINAL_LIQUIDATION Validity

### 1. Reachability Analysis under Frozen V3
- `TerminalOpportunityAnalyzer` checks `step == 718` and `shed_total > 0`.
- In standard V3 play: V3 includes the `H1_DOMINANCE_TERMINAL` / `H1_TERMINAL_REPAIR` endgame overlay, which systematically sweeps and liquidates all shed inventory between steps 712 and 718.
- Empirical evidence from EXP-AEC-001: Across 100 matches (71,900 turns), `shed_total` was exactly 0 at step 718 in **100% of matches** (0 opportunities generated).
- Reachability Path: A state with unsold inventory at step 718 is reachable **only** if:
  1. A late harvest occurs at step 717 and the worker drops cargo into the shed at step 718, after V3's primary liquidation schedule has completed; or
  2. The shed contains more than 10 distinct items, exceeding the per-step 10-order cap.
- **Classification:** **DEFENSE-IN-DEPTH / FALLBACK**. It is not an expected source of tournament Elo improvement against standard opponents.

---

## E. PHASE_SHUTDOWN Validity

### 1. Reachability Analysis under Frozen V3
- `TerminalOpportunityAnalyzer` checks `step >= 574` and unfeasible crops.
- The positive fixture manually injects `["BUY_SEED", "MELON", 1]` at step 600.
- Analysis of V3's native purchase policy (`engine/dynamic_allocator.py:87-110`):
  V3 stops buying Melon seeds after Day 19 (step 456). In Phase 3 (steps 480–624), it buys only Carrots and Wheat. After step 624, it issues 0 seed orders.
- Empirical evidence from EXP-AEC-001: While 53,488 opportunities were flagged, in **100% of cases**, V3's baseline orders contained zero dead-crop seed purchases. Exactly 0 patches were generated.
- **Classification:** **DEFENSE-IN-DEPTH / REDUNDANT WITH V3**. Reachable only through synthetic mutation or an unexpected tactical branch failure.

---

## F. Synthetic Fixture Independence Audit

Detailed audit of the four positive synthetic fixtures in `tests/aec/test_v1_1_activation.py`:

| Positive Fixture | Manually Constructed State | Naturally Derived State | Actual Simulator Delta? | Causal Commit Verified? | Could Fail in Other Legal States? |
|---|---|---|---|---|---|
| `test_synthetic_local_weed_dig_positive` | Tile (4, 4) WEED; Farmer at [4, 4]; Continuation tape forced to 12 `["PLANT", "WHEAT"]` steps. | Economic IR parsing. | **NO**. Sim produces $\Delta \text{money}=0, \Delta \text{margin}=0$. Gain is 100% extrapolated. | **YES** (commits via `weed_asset_value`). | Yes. If continuation does not plant on (4, 4), or if remaining steps $< 48$, it abstains. |
| `test_synthetic_frontload_positive` | Shed wheat=10, money=150, baseline order: [BUY_SEED, SELL]. | Economic IR parsing. | **NO**. Sim produces $\Delta \text{money}=0, \Delta \text{margin}=0$. | **NO (FAILS)**. Telemetry shows `ABSTAIN`. | Fails even in this test fixture! |
| `test_synthetic_terminal_liquidation_positive` | Step 718; shed with 40 units; baseline action with no SELL orders. | Economic IR parsing. | **YES**. Sim executes SELL orders, recovers $+\$8,250$ cash. | **YES** (commits via $\Delta \text{money} > 0$). | In standard V3 play, shed is empty, so it naturally abstains. |
| `test_synthetic_phase_shutdown_positive` | Step 600; baseline order manually injected with `["BUY_SEED", "MELON", 1]`. | Crop feasibility cutoff model. | **YES**. Sim avoids spending $\$80$ seed cost, preserving $+\$80$ cash. | **YES** (commits via $\Delta \text{money} > 0$). | In standard V3 play, V3 never buys melon seeds at step 600, so it abstains. |

---

## G. Route-Tape Consistency & Open-Loop Continuation

### 1. Mechanical Continuation Trace
When AEC evaluates a candidate action at step $t$:
1. Step $t$: Action is mutated to `cand_action = patch.apply(baseline_action)` (e.g., worker 0 executes `["DIG"]`).
2. Steps $t+1 \dots t+H-1$: The simulator passes `continuation_actions = future_trajectory[:H-1]`.
3. `future_trajectory` is extracted directly from the frozen V3 Chassis route tape (`BackboneAdapter.get_future_trajectory`).
4. **The simulator DOES NOT recompute worker routing after the DIG.**
   It mechanically feeds the baseline tape into `_apply_unit_action`.

### 2. Failure Modes & False-Positive Risks
- **Coordinate Desynchronization:** If baseline action at step 0 was `["NORTH"]` (moving from (4, 4) to (4, 3)), but candidate action replaces it with `["DIG"]` at (4, 4):
  - At step 1, baseline worker is at (4, 3); candidate worker is at (4, 4).
  - Continuation tape at step 1 says `["EAST"]`. Baseline moves to (5, 3); candidate moves to (5, 4).
  - All subsequent tile operations (planting, harvesting, watering) in candidate are executed at **permanently offset coordinates**!
- **Missing Agricultural Completion:** If `DownstreamAssetEvaluator` awards $+\$85.83$ because step 1 was `PLANT`, but V3's future tape has the worker assigned to herd sheep in the SE quadrant for the rest of the game, the wheat will NEVER be harvested or sold. The $+\$85.83$ asset value is a false-positive hallucination.
- **Classification:** Current architecture is **"baseline future tape plus local patch" (open-loop continuation)**, NOT a true counterfactual rollout.

---

## H. Horizon Validity

| Mechanism Family | Policy Rule | Horizon $H$ | Deterministic? | Sufficient to Observe Effect? | Blindness / False-Positive Risk |
|---|---|---|---|---|---|
| `LOCAL_WEED_DIG` | Dependency at $s_{\text{dep}}$: $\min(\text{rem}, \max(6, s_{\text{dep}}+3, 18))$. No dep: 6. | 18 | Yes | **NO**. Wheat needs 48 steps; Melon needs 240 steps. | High. Cannot observe harvest, watering failure, rot, or market collapse. |
| `FRONTLOAD_ORDERS` | Rival active: $\min(\text{rem}, 18)$. Inactive: 6. | 18 / 6 | Yes | **Excessive / Mismatched**. Order execution is intra-step ($t=0$). | 18 steps introduces spurious noise from periodic opponent model. |
| `TERMINAL_LIQUIDATION` | $\min(\text{rem}, 2)$ | 1 or 2 | Yes | **YES**. Liquidation is immediate at step 718. | None. Terminal boundary prevents future side effects. |
| `PHASE_SHUTDOWN` | $\min(\text{rem}, 6)$ | 6 | Yes | **YES**. Seed avoidance is immediate at step 0. | None. Cash preservation is instant and verified. |

---

## I. Acceptance-Rule Audit

1. **`LOCAL_WEED_DIG` Acceptance Rule:**
   $$\text{weed\_asset\_value} > 0 \quad \text{AND} \quad \Delta \text{TerminalMargin} \ge -(C_{\text{labor}} + 0.05)$$
   - *Rationale:* Allows an immediate simulation margin deficit up to the cost of 1 worker-step ($\$4.17$) because the downstream benefit ($\$85.83$) is expected in the unobserved future.
   - *Audit Assessment:* **HEURISTIC COMPROMISE**.
     Allowing $\Delta \text{margin} \ge -4.22$ prevents immediate cash disasters, but because $H=18$ cannot observe the mature crop, any delayed negative side effect (e.g. crop rotting at step 30 due to worker diversion) is tolerated without penalty.
2. **`FRONTLOAD_ORDERS` Acceptance Rule:**
   $$\Delta \text{TerminalMargin} > 0 \quad \text{OR} \quad \Delta \text{money} > 0$$
   - *Rationale:* Mathematically sound in principle, but completely inert in practice because real engine order resolution does not cause intra-step price degradation between player order slots.
3. **`TERMINAL_LIQUIDATION` Acceptance Rule:**
   $$\Delta \text{money} > 0 \quad \text{OR} \quad \Delta \text{TerminalMargin} > 0$$
   - *Rationale:* **MATHEMATICALLY SOUND**. End of game inventory has zero scrap value; selling it is strictly dominant.
4. **`PHASE_SHUTDOWN` Acceptance Rule:**
   $$\Delta \text{money} > 0 \quad \text{OR} \quad \Delta \text{TerminalMargin} \ge 0$$
   - *Rationale:* **MATHEMATICALLY SOUND**. Canceling an unfeasible seed purchase strictly preserves cash with zero opportunity cost.

---

## J. Prospective Contamination & Cryptographic Audit

Strict verification of governance covenant invariants:
1. **Holdout Partition Status (`340050–340199`):**
   - Verified virgin. Exactly **0 executions**, **0 logs**, **0 touches**.
2. **EXP-AEC-001 Cohort (`340000–340049`):**
   - Untouched during V1.1 development. Zero tuning loops executed on this cohort.
3. **EXP-AEC-001 Frozen Artifacts:**
   - `RAW_RESULTS.json`, `PAIRED_DELTAS.csv`, `SUMMARY.json`, `EXECUTION_MANIFEST.json` remain bit-exact identical.
4. **Frozen V3 Tarball Checksum:**
   - Target: `submission_Vj_kc_v3.tar.gz`
   - Registered SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
   - Live Computed SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
   - Result: **EXACT MATCH (VERIFIED IMMUTABLE)**.
5. **Git Repository Status:**
   - Commit HEAD: `179dd2fb3151b9f89f479375db6a71b6debfaa64`
   - Working tree: Clean, with only uncommitted scratch analysis scripts and untracked experiment logs.

---

## K. Required Mechanism Table

| Mechanism | Software Activation | Synthetic Validation | Game-Mechanic Validation | Main Risk | Prospective Status |
|---|---|---|---|---|---|
| **`LOCAL_WEED_DIG`** | **PASS** (runs, computes, patches) | **PASS** (positive commits, negative abstains) | **PARTIAL** (extrapolated asset value, ungrounded $100 wage) | Divergent continuation path; delayed agricultural failure unobserved | **READY ONLY AFTER FIXES** |
| **`FRONTLOAD_ORDERS`** | **PASS** (reorders queue) | **FAIL** (fixture quietly abstained; 0 commits) | **FAIL** (toy price degradation rule, unrealized slippage) | 100% dormancy in tournament matches | **BLOCKED / NOT READY** |
| **`TERMINAL_LIQUIDATION`** | **PASS** (detects, patches) | **PASS** (positive commits, negative abstains) | **PASS** (game rules convert dead units to cash) | 100% redundant with V3 native endgame | **READY AS DEFENSE-IN-DEPTH** |
| **`PHASE_SHUTDOWN`** | **PASS** (trims bad seed buy) | **PASS** (positive commits, negative abstains) | **PASS** (game rules avoid dead expenditure) | 100% redundant with V3 native midgame | **READY AS DEFENSE-IN-DEPTH** |

---

## L. Required Numerical Trace: LOCAL_WEED_DIG (+85.83)

Independent mathematical reconstruction of the positive weed dig fixture (`weed_obstruction_obs`, step 48, worker 0 at (4, 4), continuation with `PLANT WHEAT` at step 49):

```
Step 1: Labor Opportunity Cost (C_labor)
   = $100.0 / TURNS_PER_DAY = 100.0 / 24
   = $4.166666666666667                                    [ASSUMED HEURISTIC]

Step 2: Expected Crop Yield (Y)
   = EXPECTED_CROP_YIELDS["WHEAT"]
   = 4 units                                               [ASSUMED HEURISTIC]

Step 3: Base Market Price (P)
   = current_prices.get("WHEAT", 25)
   = $25.0 / unit                                          [EXTRAPOLATED SPOT PRICE]

Step 4: Seed Purchase Cost (S)
   = CROP_SEED_PRICE["WHEAT"]
   = $10.0                                                 [REAL GAME CONSTANT]

Step 5: Gross Downstream Revenue (R)
   = Y * P = 4 * 25.0
   = $100.0                                                [EXTRAPOLATED]

Step 6: Gross Downstream Profit (B_downstream)
   = R - S = 100.0 - 10.0
   = $90.0                                                 [EXTRAPOLATED]

Step 7: Route Detour Savings
   = 0 steps * C_labor
   = $0.0                                                  [SIMULATED]

Step 8: Net Weed Asset Value (WEED_VALUE)
   = B_downstream - C_labor = 90.0 - 4.166666666666667
   = +$85.83333333333333                                   [EXTRAPOLATED MODEL VALUE]

Step 9: Forward Simulation Delta (Horizon H = 18, steps 48 to 66)
   - Baseline Final Money:   $2,500.0
   - Candidate Final Money:  $2,500.0
   - delta_our_money:        $0.0                          [SIMULATED]
   - delta_terminal_margin:  $0.0                          [SIMULATED]

Step 10: WinModel Acceptance Evaluation
   - Condition 1: weed_asset_value > 0
     85.8333 > 0                                           -> TRUE
   - Condition 2: delta_margin >= -(C_labor + 0.05)
     0.0 >= -(4.1667 + 0.05) = -4.2167                     -> TRUE
   - is_superior = TRUE

Step 11: Final Commit Decision
   - Safety Certificate: PASSED
   - Commit Decision: TRUE (Committed Mechanism: LOCAL_WEED_DIG)
```

### Component Breakdown
- **SIMULATED:** `delta_our_money = $0.0`, `delta_terminal_margin = $0.0`, `intermediate_solvency = True`.
- **EXTRAPOLATED:** Gross revenue ($100.0), Gross profit ($90.0), Net asset value (+$85.83).
- **ASSUMED:** Labor wage ($100/day = $4.17/step), Nominal wheat yield (4 units), Tolerance buffer ($0.05).

---

## M. Identified Scientific Flaws & Required Corrections

### Flaw 1: `test_synthetic_frontload_positive` Silently Abstains
- **Location:** [`tests/aec/test_v1_1_activation.py:554-580`](file:///c:/Users/Sundareswaran/Kagriculture/tests/aec/test_v1_1_activation.py#L554-L580)
- **Why it matters:** The test suite reports a pass, giving the illusion that `FRONTLOAD_ORDERS` commits on advantage. In reality, it abstained due to zero delta margin. The commit gate was never tested for this mechanism.
- **Proposed Correction:** Supply a genuine opponent order in the test fixture that causes price slippage if the player delays their sale, and explicitly assert `assert executor.latest_telemetry.decision == "COMMIT"`.
- **Validation Test:** A revised test where candidate achieves strictly greater money than baseline and commits.

### Flaw 2: Simulator Uses Toy Price Degradation Instead of Engine Price Formula
- **Location:** [`aec/counterfactual/simulator.py:137,170`](file:///c:/Users/Sundareswaran/Kagriculture/aec/counterfactual/simulator.py#L137)
- **Why it matters:** `price - actual_sell // 2` is a fictional rule. In Kaggle Agriculture, prices are determined by non-linear saturation curves with inventory base $10,000$. Evaluating patches against a toy price model risks committing detrimental order permutations.
- **Proposed Correction:** Replace toy price formula with `compute_market_price(item, inventory)` from `config.py`.
- **Validation Test:** Unit test asserting simulated market prices match `compute_market_price()` bit-for-bit.

### Flaw 3: Ungrounded $100 Flat Labor Cost
- **Location:** [`aec/evaluation/asset_value.py:32`](file:///c:/Users/Sundareswaran/Kagriculture/aec/evaluation/asset_value.py#L32)
- **Why it matters:** Kaggle Agriculture uses a Fibonacci hiring cost. An arbitrary $100 flat wage distorts the threshold between worthwhile and wasteful actions.
- **Proposed Correction:** Ground $C_{\text{labor}}$ in the actual marginal cost of hiring on the current day (`fib_hire_cost(hires_today)` / 24), or document $C_{\text{labor}}$ strictly as an empirical shadow opportunity cost parameter.
- **Validation Test:** Parameterized test verifying labor cost matches current day hire expenditure.

### Flaw 4: Open-Loop Continuation Ignores Physical Position Desynchronization
- **Location:** [`aec/counterfactual/simulator.py:321-328`](file:///c:/Users/Sundareswaran/Kagriculture/aec/counterfactual/simulator.py#L321-L328)
- **Why it matters:** If candidate action replaces a movement step with `DIG`, the worker's physical position diverges from the baseline tape. Executing subsequent baseline movement commands causes the worker to wander off-path.
- **Proposed Correction:** In `DownstreamAssetEvaluator` and `CounterfactualSimulator`, check whether candidate step 0 mutated a movement action. If so, invalidate continuation route lookahead unless a local realignment path is provided.
- **Validation Test:** Synthetic test where baseline moves North but candidate digs; simulator must detect position divergence and avoid executing invalid downstream tile operations.

---

## N. Final Classification

### **READY ONLY AFTER SPECIFIC DEVELOPMENT FIXES**

**Justification:**
1. While software infrastructure (isolation, fail-closed abstention, determinism, V3 hash immutability, holdout virginity) is 100% verified,
2. `FRONTLOAD_ORDERS` has not achieved a verified commit in synthetic testing (it secretly abstained),
3. `LOCAL_WEED_DIG` relies on 100% extrapolated downstream value with an ungrounded labor cost assumption and open-loop continuation desynchronization risk,
4. `TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` are verified to be redundant defense-in-depth mechanisms with zero expected activation in regular play.

Launching EXP-AEC-002 prior to resolving Flaws 1, 2, and 4 would risk repeating the dormancy or false-positive divergence of EXP-AEC-001. All prospective testing remains strictly paused.
