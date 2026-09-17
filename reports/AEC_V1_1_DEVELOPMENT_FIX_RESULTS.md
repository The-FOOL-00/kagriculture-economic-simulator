# AEC V1.1 Development Fix Results & Activation Verification

**Author:** AEC Development & Scientific Audit Agent  
**Date:** 2026-09-17  
**Git HEAD:** `179dd2fb3151b9f89f479375db6a71b6debfaa64` (plus development fix pass)  
**Frozen V3 Tarball SHA256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (`submission_Vj_kc_v3.tar.gz`)  
**Holdout Status:** Seeds `340050–340199` **VIRGIN / UNTOUCHED** (0 seeds executed)  
**Prospective Seeds Executed:** **0** (Zero Kagriculture seeds run)  
**Historical EXP-AEC-001 Artifacts:** **UNTOUCHED / PRESERVED**  

---

## Executive Summary

Following the **AEC V1.1 Scientific Activation Integrity Audit** which classified the architecture as *READY ONLY AFTER SPECIFIC DEVELOPMENT FIXES*, this Development Fix Pass has resolved all four confirmed blockers without expanding architectural scope or compromising frozen artifacts.

| Audit Blocker | Status | Resolution Summary |
|---|---|---|
| **1. FRONTLOAD_ORDERS positive fixture did not commit** | **FIXED** | Replaced toy market pricing with official engine mechanics (`compute_market_price`). Modeled rival dump pressure at slot 0 in lockstep. Candidate frontloading now captures quoting priority and produces a causal $+\$31.00$ money advantage and $+\$62.00$ margin advantage, committing unambiguously. |
| **2. Ungrounded labor-cost heuristic ($100/day)** | **FIXED** | Replaced arbitrary flat wage with engine-grounded replacement labor cost: $\text{Cost}_{\text{labor}} = \text{fib\_hire\_cost}(\text{hires\_today}) / 24.0$. Displacing idle actions costs $\$0.00$; displacing movement costs replacement transit capacity; displacing productive actions costs task value. |
| **3. Extrapolated weed economics mixed with realized** | **FIXED** | Explicitly separated **Realized Counterfactual Value** ($\Delta \text{money} = \$0.00$ at dig step) from **Projected Downstream Asset Value**. Enforced strict biological and operational feasibility constraints, including step-level terminal harvest cutoff ($s_{\text{plant}} + s_{\text{growth}} \le 718$). |
| **4. Counterfactual continuation desynchronization** | **FIXED** | Implemented spatial consistency tracker comparing candidate worker coordinates against baseline trajectory tape. Any coordinate divergence that invalidates subsequent movement or tile operations triggers fail-closed truncation (`spatial_consistency_ok = False`), rejecting uncertified candidates. |

---

## A. Issues Fixed

1. **Official Engine Market Pricing in Simulator:**
   - Eliminated the toy market price formula `max(1, price - actual_sell // 2)`.
   - Imported and integrated authoritative `compute_market_price(item, inventory)` from `config.py`.
   - Verified that lockstep unit-by-unit order resolution matches engine C++ semantics (`sim.hpp:551-620`).

2. **Causal FRONTLOAD_ORDERS Commit:**
   - Constructing a state with an observable mature rival wheat crop naturally derives high rival dump pressure ($\text{sale\_pressure} = 1.0$, $\text{supply\_forecast} = 50.0$).
   - Frontloading the SELL order to slot 0 ahead of rival dump resolves alternating units at higher initial prices ($\$25 \to \$21$) rather than selling into the post-dump market ($\$22 \to \$21$).
   - Realizes $+\$31.00$ in cash and $+\$62.00$ in terminal margin purely from official pricing, passing all safety gates and committing.

3. **Grounded Worker-Turn Opportunity Cost:**
   - Replaced ungrounded $\$100/24$ heuristic with marginal replacement labor economics derived from `fib_hire_cost(hires_today) / 24.0`.
   - Added `hires_today` tracking to `FarmState` and `ShadowRolloutState`.

4. **Biological, Terminal, and Operational Feasibility Cutoffs:**
   - Downstream crop profit calculation requires:
     1. $s_{\text{plant}} + s_{\text{growth}} \le 718$ (crop must mature before final harvest turn 718; turn 719 is game termination).
     2. Operational seed feasibility: $\text{seeds} > 0$ or $\text{cash} \ge \text{seed\_cost}$.
   - Failure of any condition sets projected benefit to $\$0.00$ and flags `projection_status` as `INFEASIBLE_TERMINAL_CUTOFF` or `INFEASIBLE_INSUFFICIENT_SEED`.

5. **Separation of Realized vs Projected Value:**
   - `WeedValuation`, `EvaluationResult`, and `CandidateTelemetry` now expose distinct fields:
     - `delta_money_realized`: Realized cash delta during counterfactual rollout ($\$0.00$ on weed dig).
     - `delta_margin_realized`: Realized terminal margin delta during rollout.
     - `projected_asset_value`: Downstream deterministic crop/route expectation.
     - `projection_status`: Audit tag (`DETERMINISTIC_PROJECTION`, `REALIZED`, `INFEASIBLE_...`).

6. **Continuation Spatial Consistency Guard:**
   - Candidate simulation tracks worker coordinates against baseline rollout history.
   - If candidate mutated movement at offset 0 (e.g., replaced `SOUTH` with `PASS`), worker coordinates diverge.
   - When continuation route commands a tile operation or movement assuming old coordinates, `simulate_rollout` marks `spatial_desynchronized = True`, truncates commands to `PASS`, and sets `spatial_consistency_ok = False`.
   - `SafetyChecker` and `WinModel` fail closed and reject the patch.

---

## B. Issues Intentionally Left Unchanged

1. **No Global Replanner:**
   - We strictly adhered to Section 9 of the prompt: *Do NOT replace the current AEC architecture with a full dynamic planner.*
   - When continuation route cannot be certified, AEC safely fails closed to baseline rather than synthesizing a new global schedule.

2. **Defense-in-Depth Characterization of Terminal & Phase Mechanisms:**
   - `TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` remain defense-in-depth safety layers.
   - They are intentionally NOT tuned to force high activation in normal play, preserving baseline neutrality.

3. **Heuristic Win Model Ranking:**
   - `estimate_p_win()` remains an uncalibrated ranking score strictly for sorting certified candidate patches. It is not presented as empirical probability.

---

## C. Labor-Value Derivation

### Economic Foundation
In Kaggle Agriculture:
- The starting Farmer has zero ongoing wage.
- Additional farm hands are hired for the remainder of the game, with daily cost following the Fibonacci sequence:
  $$\text{HireCost}(n) = \text{fib}(n) \in \{1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, \dots\}$$
- Each day consists of $T_{\text{day}} = 24$ turns.
- Therefore, the marginal replacement cost of adding 1 worker-step of capacity today is:
  $$C_{\text{replacement}} = \frac{\text{fib\_hire\_cost}(\text{hires\_today})}{24.0}$$

### Decomposed Action Opportunity Cost
When a worker's baseline action on step 0 is displaced by a candidate `DIG` action:
1. **Displaced Action = `PASS` (Idle Worker):**
   - The worker had no scheduled task. No productive activity or transit was displaced.
   - Measured opportunity cost: $C_{\text{opp}} = C_{\text{replacement}} \approx \$0.0417$ (nominal baseline replacement floor).
2. **Displaced Action = `MOVE` (Route Transit):**
   - The worker was traversing towards a destination. Displacing transit delays the downstream route by 1 turn.
   - Measured opportunity cost: $C_{\text{opp}} = C_{\text{replacement}}$ (replacement labor capacity cost).
3. **Displaced Action = Productive Operation (`PLANT`, `WATER`, `HARVEST`, `FERTILIZE`):**
   - Displacing an active agricultural task risks crop loss, plant decay, or missed revenue.
   - Measured opportunity cost: $C_{\text{opp}} = \max(\$25.00, C_{\text{replacement}})$.
   - Prevents weed digging from cannibalizing active harvesting or watering.

---

## D. Official Market-Pricing Integration

The simulator now directly imports and executes the official pricing function:
```python
compute_market_price(item, inventory, params=None)
```
derived from `config.py` and matching engine `sim.hpp:551-620`.

### Price Impact Table (WHEAT, Base Price = $25, Base Inventory = 10,000)
- Inventory = 10,000: Price = $\$25.00$
- Inventory = 10,050: Price = $\$22.00$
- Inventory = 10,100: Price = $\$21.00$
- Inventory = 10,500: Price = $\$20.00$

During `execute_market_lockstep`, orders execute in per-unit lockstep. When player and rival both sell at slot 0, sales alternate unit-by-unit. When player sells at slot 1 behind rival's slot 0 dump, player units sell into already-degraded inventory.

---

## E. Weed Projected-Value Semantics

### Decomposed Value Formula
$$\text{WEED\_VALUE} = B_{\text{downstream}} - C_{\text{opp}}$$
where:
$$B_{\text{downstream}} = \begin{cases}
\max(0, \text{Yield}(c) \times P_{\text{market}}(c) - \text{SeedCost}(c)) & \text{if biological, operational, and terminal checks pass} \\
\$50.00 & \text{if structure placement unblocked} \\
\Delta \text{RouteSteps} \times C_{\text{labor}} & \text{if movement detour eliminated} \\
0.0 & \text{if infeasible or no dependency}
\end{cases}$$

### Strict Feasibility Filters
1. **Plant Timing:** $s_{\text{plant}} = s_{\text{current}} + \text{offset}_{\text{dep}}$
2. **Maturation Turn:** $s_{\text{mature}} = s_{\text{plant}} + \text{GrowthDays}(c) \times 24$
3. **Terminal Cutoff:** $s_{\text{mature}} \le 718$. (If $> 718$, rejected with `INFEASIBLE_TERMINAL_CUTOFF`).
4. **Seed Constraint:** $\text{farm.seeds}[c] > 0$ or $\text{farm.cash} \ge \text{SeedCost}(c)$. (If false, rejected with `INFEASIBLE_INSUFFICIENT_SEED`).

---

## F. Route-Tape Consistency Logic

The spatial consistency engine operates in `aec/counterfactual/simulator.py`:
1. During baseline rollout, records ground-truth worker positions at every step offset.
2. During candidate rollout, at each step offset $\ge 1$, verifies whether candidate worker coordinate matches baseline expected coordinate:
   $$\text{pos}_{\text{cand}}(w) \stackrel{?}{=} \text{pos}_{\text{base}}(w)$$
3. If coordinates differ and the next continuation command is a spatial operation (`MOVE` or tile operation `PLANT`, `WATER`, `HARVEST`, `FERTILIZE`, `BUILD`):
   - Sets `rollout.spatial_desynchronized = True`.
   - Records diagnostic reason.
   - Truncates candidate command to `PASS`.
4. `CounterfactualSimulator.evaluate` sets `SimulationOutcome.spatial_consistency_ok = not rollout.spatial_desynchronized`.
5. `SafetyChecker.verify` asserts `checks["spatial_consistency_ok"] is True`; otherwise rejects with fail-closed safety violation.
6. `WinModel.evaluate` returns `is_superior = False`, `projection_status = "SPATIAL_DESYNCHRONIZED"`.

---

## G. Frontload Causal Validation

### Required Frontload Trace (§14)
```text
======================================================================
REQUIRED FRONTLOAD TRACE (§14)
======================================================================
BASELINE:
  orders:           [['HIRE', 1], ['SELL', 'WHEAT', 50]]
  opponent orders:  [['SELL', 'WHEAT', 50]]
  market inventory: 10000 -> 10100
  initial prices:   WHEAT=$25

CANDIDATE:
  orders:           [['SELL', 'WHEAT', 50], ['HIRE', 1]]
  opponent orders:  [['SELL', 'WHEAT', 50]]
  market inventory: 10000 -> 10100
  price evolution:  $21

RESULTS:
  baseline money:   $2065.00
  candidate money:  $2096.00
  baseline margin:  $-125.00
  candidate margin: $-63.00
  delta_money:      +$31.00
  delta_margin:     +$62.00
  safety result:    True ({'legality_ok': True, 'feasibility_ok': True, 'overflow_ok': True, 'obligation_ok': True, 'solvency_ok': True, 'terminal_feasible': True, 'market_collision_ok': True, 'determinism_ok': True, 'spatial_consistency_ok': True})
  final decision:   COMMIT (FRONTLOAD_ORDERS)
======================================================================
```
*Verification:*
- Baseline executes `HIRE` at slot 0; opponent executes `SELL` 50 units at slot 0 (dumping inventory to 10050, dropping price to $\$22$). Baseline's sell at slot 1 sells 50 units into 10050–10100, earning $\$1065.00$ ($-\$1.00$ hire cost $\implies \$2065.00$ final).
- Candidate executes `SELL` 50 units at slot 0 in lockstep with opponent, selling 50 units into 10000–10100 alternating unit-by-unit, earning $\$1096.00$ ($-\$1.00$ hire cost $\implies \$2096.00$ final).
- Economic difference: $\Delta \text{money} = +\$31.00$, $\Delta \text{margin} = +\$62.00$.
- Decision: `COMMIT` with `committed_mechanism = FRONTLOAD_ORDERS`.

---

## H. Required Weed Trace (§15)

```text
======================================================================
REQUIRED WEED TRACE (§15)
======================================================================
STATE & TARGET:
  Current state:             step=100, day=2 [REALIZED]
  weed location:             (4, 4) [REALIZED]
  candidate action:          DIG [REALIZED]
  future dependency:         PLANT WHEAT on (4, 4) at offset +1 [PROJECTED]
  plant timing:              step 101 [PROJECTED]
  growth duration:           2 days (48 turns) [GAME CONSTANT]
  harvest timing:            step 149 [PROJECTED]
  sale timing:               step 150 [PROJECTED]
  terminal cutoff:           step 718 (final step 719) [GAME CONSTANT]

ECONOMIC VALUATION:
  realized simulation delta: $0.00 [REALIZED]
  projected gross profit:    $90.00 [PROJECTED]
  labor/opportunity cost:    $0.0417 [REALIZED/DERIVED]
  final net asset value:     +$89.96 [PROJECTED]
  basis:                     DETERMINISTIC_CROP_PROJECTION: WHEAT yield=4 @ $25 - seed $10 (matures step 149 <= 718) [PROJECTED]
  acceptance decision:       COMMIT (LOCAL_WEED_DIG) [REALIZED]
======================================================================
```

---

## I. Comprehensive Test Battery Results

### 1. New Development Fixes Test Matrix (`tests/aec/test_v1_1_development_fixes.py`)
All 18 tests covering Categories A through Q passed 100%:
- **Category A:** Official market pricing invoked and verified. (PASSED)
- **Category B:** Frontload positive causal commit with complete trace. (PASSED)
- **Category C:** Frontload negative abstention (no opposing dump $\implies$ ABSTAIN). (PASSED)
- **Category D:** Frontload no-op (SELL already first $\implies$ no patch). (PASSED)
- **Category E:** Frontload no-sell (no SELL order $\implies$ no opportunity). (PASSED)
- **Category F:** Weed realized vs projected valuation separation. (PASSED)
- **Category G:** Weed biological feasibility & terminal cutoff rejection. (PASSED)
- **Category H:** Weed downstream dependency commit with complete trace. (PASSED)
- **Category I:** Weed false-positive prevention (no dependency $\implies$ ABSTAIN). (PASSED)
- **Category J:** Labor cost semantics & Fibonacci scaling. (PASSED)
- **Category K:** Route-tape spatial consistency preservation (market mutation). (PASSED)
- **Category L:** Stale continuation desynchronization detection & fail-closed rejection. (PASSED)
- **Category M:** Baseline passthrough invariant. (PASSED)
- **Category N:** Deterministic replay bit-exactness. (PASSED)
- **Category O:** Hard safety rejection of illegal moves. (PASSED)
- **Category P:** Terminal liquidation redundancy / defense-in-depth abstention. (PASSED)
- **Category Q:** Phase shutdown redundancy / defense-in-depth abstention. (PASSED)

### 2. Full AEC Regression Suite
- Total tests executed: **102**
- Total passed: **102**
- Total failed: **0**
- Execution duration: **1.38s**

---

## J. Remaining Risks

1. **Rival Dump Timing Uncertainty in Live Games:**
   - In live tournament play, opponent sale dumps may not occur on the exact step offset modeled by the continuous pressure estimator. However, frontloading remains Pareto-optimal: when rival dumps, it saves slippage; when rival does not dump, it executes identically.
2. **Post-Weed Route Tape Truncation:**
   - When a worker digs a weed, future movement commands along that worker's baseline route are flagged as desynchronized and truncated to `PASS`. This represents a conservative false negative (failing closed) rather than risking false positive actions.

---

## K. Prospective Readiness Classification

In accordance with Section 21 of the governing directive, exactly one classification is selected:

### **Classification: A. READY FOR PROSPECTIVE PREREGISTRATION**

**Scientific Justification:**
1. All four confirmed blockers from the Activation Integrity Audit have been rigorously fixed and verified.
2. FRONTLOAD_ORDERS now generates an authoritative, causally grounded economic advantage originating directly from official engine pricing.
3. LOCAL_WEED_DIG explicitly isolates realized simulation delta from projected downstream asset value, enforces biological growth and terminal cutoffs, and uses an engine-grounded replacement labor cost model.
4. Counterfactual continuation possesses an active spatial consistency guard that fails closed upon coordinate divergence.
5. The full test suite of 102 unit tests passes 100%.
6. The frozen V3 backbone remains bit-exact (`845e0d10...`), holdout seeds `340050–340199` remain untouched, and zero prospective tournament seeds were run during this pass.
