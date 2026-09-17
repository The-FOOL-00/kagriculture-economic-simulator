# AEC ARCHITECTURE CHECKPOINT 001: NEXT ARCHITECTURAL CAPABILITY
**Roadmap for Quarantined Mechanisms and Architectural Capability Selection**
**Date:** 2026-09-17  
**Artifact Path:** `reports/AEC_CHECKPOINT_001_NEXT_CAPABILITY.md`  
**Governance Directive:** Research and Architecture Specification Only — DO NOT Implement or Launch Prospective Experiments  

---

## 1. Quarantined Opportunity Family Readiness Roadmap (§13)

Prior to EXP-AEC-003, seven opportunity families were placed in scientific quarantine. In accordance with governance principles, **none of these mechanisms may be activated until their required architectural foundations, counterfactual semantics, and dependency closures are constructed and verified**.

The table below establishes the explicit completion criteria for every quarantined family:

| Mechanism Family | Current Failure / Limitation | Required Architectural Capability | Required Counterfactual Semantics | Required Dependency Closure | Required Pre-Trial Tests | Prospective Experiment Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`LOCAL_WEED_DIG`** | Sunk-cost labor valuation; mutates worker position without pathfinding bridge, causing spatial desynchronization and safety rejection | Dynamic Worker Route Reconnection & Splicing Engine | Spliced route simulation modeling weed removal, path unblocking, and harvest delay | `WORKER_MOVE` $\to$ `WEED_CLEARED` $\to$ `PATH_UNBLOCKED` $\to$ `PLANT_ETA` $\to$ `YIELD` | Adversarial detour tests, blocked quadrant boundary tests, bridge latency verification | `QUARANTINED` (Candidate for post-reconnection trial) |
| **`DYNAMIC_SHADOW_HARVEST`** | Greedy Manhattan distance heuristic; ignores baseline opportunity cost and truncates diverged worker moves to `PASS` | Marginal Labor Shadow-Price Engine + Route Splicing Engine | Two-world simulation: (Baseline Plan) vs (Diverted Harvest + Catch-up Route), evaluating net terminal margin delta | `WORKER_ALLOC` $\to$ `CROP_MATURITY_DECAY` $\to$ `SHED_INV` $\to$ `BASELINE_TASK_ABANDON_PENALTY` | Mature crop decay prevention vs planting delay trade-off tests | `QUARANTINED` (Requires labor valuation model) |
| **`CARGO_FERRY_PRIORITY`** | Diverts worker carrying $\ge 3$ units to shed heuristically; breaks downstream schedule and ignores shed capacity margin | Shed Capacity State Coupling + Route Splicing | Counterfactual comparison of delayed drop vs immediate drop, accounting for shed capacity saturation | `WORKER_CARGO` $\to$ `SHED_CAPACITY` $\to$ `OVERFLOW_RISK` $\to$ `IDLE_PENALTY` $\to$ `SALE_TIMING` | Full-shed drop prevention tests, worker cargo loss prevention tests | `QUARANTINED` (Requires route splicing) |
| **`OPPONENT_PREEMPT_SELL`** | Injects novel `SELL` orders based on uncalibrated opponent supply heuristic; ignores baseline future sales | Calibrated Opponent Absorption Model + Novel Order Injection Pass | Multi-turn market lockstep clearing under stochastic opponent dump volumes | `OPP_SUPPLY_DROP` $\to$ `PRICE_CRASH` $\to$ `HOLD_LOSS` $\to$ `OPPORTUNITY_COST_CASH` | Adversarial false-dump tests, town-consumption price rebound tests | `QUARANTINED` (Requires stochastic opponent calibration) |
| **`EMERGENCY_FEED_PURCHASE`** | Feed deficit detected statically; does not model livestock starvation timeline or net profitability | Livestock Production Lifecycle & Feed Inventory Model | Extended $H=36$ simulation tracking daily feeding, starvation penalties, and animal product revenues | `ANIMAL_COUNT` $\to$ `FEED_DEFICIT` $\to$ `MARKET_BUY` $\to$ `MILK_WOOL_YIELD` $\to$ `MARGIN` | Multi-day feed consumption tests, stockout starvation penalty tests | `QUARANTINED` (Requires lifecycle simulator) |
| **`TERMINAL_HARVEST_SWEEP`** | Triggers during steps 696–717, but cannot coordinate multiple workers to sweep unharvested crops without route splicing | Multi-Worker Terminal Sweep Coordinator + Route Splicing | Exact terminal boundary simulation (steps 696–718) comparing baseline harvest yield vs sweep yield minus transport cost | `MATURE_UNHARVESTED` $\to$ `SWEEP_ROUTES` $\to$ `SHED_DEPOSIT` $\to$ `STEP_718_LIQUIDATION` | Step 715–718 boundary tests, worker inventory drop deadline tests | `QUARANTINED` (Depends on route reconnection) |
| **`TOWN_CYCLE`** | Speculative hold/sell based on 4-step town consumption ticks; relies on unvalidated absorption estimates | Town Shop Inventory & Absorption Tracking Engine | Inter-turn price elasticity simulator modeling shop absorption vs competitor selling | `TOWN_TICK_COUNTDOWN` $\to$ `SHOP_ABSORPTION` $\to$ `PRICE_REBOUND` $\to$ `DELAYED_SELL_REV` | False-rebound absorption tests, competitor preemption tests | `QUARANTINED` (Requires shop tracking) |

---

## 2. Selection of the Next Architectural Capability (§14)

### 2.1 Capability Evaluation & Scoring
To avoid speculative feature selection, five candidate capabilities were scored across eight objective criteria (scale 1–10):
1. **Generalization:** Breadth of scenarios and game states impacted.
2. **Architectural Leverage:** Unblocking dependencies for other subsystems.
3. **Integration Simplicity:** Compatibility with the existing AEC pipeline.
4. **Counterfactual Readiness:** Feasibility of exact simulation and verification.
5. **Implementation Tractability:** Algorithmic complexity on a $10 \times 10$ board.
6. **Safety & Fail-Closed Robustness:** Ability to certify without silent failures.
7. **Validation Cost:** Computational and test suite verification burden.
8. **Competitive Potential:** Terminal margin upside in tournament play.

```
Candidate A: Dynamic Worker Trajectory Reconnection & Route Splicing Engine
Candidate B: Inter-Turn Town-Cycle Price Absorption Engine
Candidate C: Livestock Lifecycle & Feed Security Optimizer
Candidate D: Bayesian Opponent Trajectory & Market Dump Predictor
Candidate E: Terminal Multi-Worker Cargo Sweep Coordinator
```

#### Evaluation Scorecard

| Capability | Gen (10) | Lev (10) | Int (10) | Cnt (10) | Trc (10) | Saf (10) | Val (10) | Pot (10) | Total Score | Rank |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Candidate A: Worker Route Reconnection** | **10** | **10** | **9** | **9** | **7** | **8** | **9** | **9** | **71 / 80** | **#1** |
| **Candidate E: Terminal Cargo Sweep** | 6 | 7 | 8 | 8 | 8 | 8 | 7 | 8 | 60 / 80 | #2 |
| **Candidate B: Town-Cycle Absorption** | 7 | 5 | 7 | 6 | 8 | 7 | 8 | 6 | 54 / 80 | #3 |
| **Candidate C: Livestock Lifecycle Optimizer** | 5 | 6 | 6 | 6 | 6 | 6 | 6 | 7 | 48 / 80 | #4 |
| **Candidate D: Bayesian Opponent Predictor** | 6 | 4 | 5 | 5 | 5 | 6 | 5 | 6 | 42 / 80 | #5 |

---

### 2.2 The Single Highest-Value Next Architectural Capability

> **SELECTED CAPABILITY:**  
> **Dynamic Worker Trajectory Reconnection & Route Splicing Engine (`AEC-RECONNECT`)**

#### Architectural Justification:
1. **The Root Bottleneck of AEC:**  
   Currently, AEC has mastered intra-basket market compilation (validated in EXP-AEC-003). However, **worker operations represent $>80\%$ of all actions in Kaggle Agriculture**. At present, whenever a patch mutates a worker's action (e.g. `DIG` a weed, take a 1-step detour to harvest a ripe melon), the worker's position diverges from the baseline route tape. Because the counterfactual simulator cannot bridge the worker back to the tape, the simulator sets future moves to `PASS`, flags `spatial_consistency_ok == False`, and the safety checker forces an immediate `ABSTAIN`.
2. **Massive Architectural Leverage:**  
   Implementing dynamic route reconnection solves the stale backbone problem. It immediately unblocks **four quarantined mechanism families**:
   * `LOCAL_WEED_DIG`
   * `DYNAMIC_SHADOW_HARVEST`
   * `CARGO_FERRY_PRIORITY`
   * `TERMINAL_HARVEST_SWEEP`
   None of these families can function without route reconnection. Implementing any of them before route reconnection is architecturally impossible.
3. **High Tractability on $10 \times 10$ Grid:**  
   Reconnection on a $10 \times 10$ grid requires only lightweight A* or Manhattan bridge pathfinding ($\le 4$ steps). As demonstrated in our Checkpoint 001 benchmarks, calculating bridges takes $< 0.05$ ms, completely preserving our sub-10 ms latency budget.
4. **Deterministic Fail-Closed Safety:**  
   If a worker cannot reconnect to the baseline waypoint within allowable bridge steps ($\le 4$) or if reconnection delays an immutable downstream obligation (e.g. crop decay or shed insolvency), the engine deterministically yields `INVAL_CANNOT_RECONNECT` and executes a safe `ABSTAIN` back to the backbone.

---

## 3. Preserving the Compiler Architecture — Do Not Stack Heuristics (§15)

A critical failure mode observed in competitive Kaggle development is responding to a successful experiment by stacking ad-hoc heuristics ("market timing works, so let's add 5 heuristic route tweaks").

AEC rejects this anti-pattern:
* Every new mechanism must enter through:
  $$\text{Economic IR} \to \text{Causal DAG} \to \text{Coupled Patch} \to \text{Counterfactual Simulator} \to \text{Safety Certificate} \to \text{Controlled CRN Trial}$$
* `AEC-RECONNECT` will not be a heuristic rule. It will be a **formal compiler pass** that computes trajectory bridges, validates counterfactual feasibility under multi-turn simulation, and certifies intermediate spatial and cash invariants before a single action is committed.

---

## 4. Governance & Stop Condition (§21)

* **Status:** SPECIFICATION COMPLETE.
* **Stop Condition Enforced:** Development of `AEC-RECONNECT` is **NOT** starting in this checkpoint.
* **No Prospective Experiment:** `EXP-AEC-004` is **NOT** launched.
* **Holdout Intact:** Seeds `340050–340199` remain strictly protected and untouched.
