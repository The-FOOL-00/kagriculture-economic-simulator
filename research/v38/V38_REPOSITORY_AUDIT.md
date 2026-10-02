# V38 Repository and Environment Reconnaissance Audit

**Document ID:** `V38_REPOSITORY_AUDIT.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Summary

This audit establishes the environmental, algorithmic, and software foundations for the V38 research candidate. It catalogs the full mechanics of the Kagriculture simulation engine, maps the legal observation and action spaces, dissects the failure modes of previous RL efforts (specifically RL-X2 in V32), audits the mechanisms of the live production benchmark V35, and defines the inventory of reusable versus prohibited components.

---

## 2. Environment Mechanics Relevant to Planning

The Kagriculture environment (`kaggle_environments 1.32.7`) is a turn-based, multi-agent economic agricultural simulation:

1. **Horizon & Temporal Structure:**
   * Full game duration: $T = 720$ steps (30 days $\times$ 24 hours).
   * Steps 0 to 718: Both agents submit actions simultaneously.
   * Step 719: Terminal state; the engine evaluates terminal cash and assigns final rewards.
   * Daily cycle: 24 steps per day. At midnight ($hour = 24 / step \equiv 0 \pmod{24}$), daily wages are deducted ($10 per farm hand).
   * Town consumption cycle: Every 4 steps ($step \equiv 0 \pmod 4$), the town consumes inventory from the market, creating cyclic price volatility.
   * Shop unlock cycle: Every 72 steps (3 days), new shops unlock in town, expanding product demand.

2. **Spatial Topography & Land System:**
   * Board size: $10 \times 10$ grid.
   * Center shed: $2 \times 2$ tiles adjacent to coordinates $(4, 4)$, $(4, 5)$, $(5, 4)$, $(5, 5)$. All drops, pickups, and shed storage interact here.
   * Farm quadrants: 4 quadrants of $5 \times 5$ tiles.
     * Quadrant 0 (top-left) starts unlocked.
     * Quadrants 1, 2, 3 cost $1,000, $2,000, $4,000 respectively to unlock via `BUY_LAND`.
   * Tile contents:
     * `None`: empty arable tile.
     * `"LOCKED"`: tile in an unpurchased quadrant.
     * `{"kind": "WEED"}`: weed blocking tile, requires `DIG` to clear.
     * `{"kind": "PLANT", "crop": C, ...}`: growing crop.
     * `{"kind": "COOP"}`: poultry structure.
     * `{"kind": "PASTURE", "animal": A, ...}`: livestock pasture.

3. **Crops & Agronomy:**
   * Five crop types with distinct maturation times, yields, and seed costs:
     * **WHEAT:** Seed $10, 4 days to mature, yields 4 units (re-harvestable if replanted, primary animal feed).
     * **CARROT:** Seed $20, 3 days to mature, yields 3 units (fast cash turnaround).
     * **TOMATO:** Seed $50, multi-harvest ongoing crop.
     * **STRAWBERRY:** Seed $100, high-value ongoing crop.
     * **MELON:** Seed $80, 10 days to mature, yields 6 units (highest margin crop in the game, backbone of A7/V35).
   * Mandatory daily water: A planted crop that is not watered on a given day pauses growth or withers.
   * Fertilizer: Accelerates yield when applied before maturation.

4. **Livestock & Feed Logistics:**
   * Animals: **COW** ($400, produces MILK, requires PASTURE), **SHEEP** ($500, produces WOOL, requires PASTURE), **GOOSE** ($300, produces EGG, requires COOP).
   * Feed requirement: Each animal consumes 1 unit of WHEAT daily. If unfed, production halts.
   * Care requirement: Milking/shearing/care actions yield high-margin products that command $25–$60 spot prices.

5. **Labor & Wages:**
   * Units: 1 permanent Farmer + $N$ hired Farm Hands.
   * Hiring: Action `HIRE` in market orders.
   * Hiring cost: Daily Fibonacci sequence: 1st hire $1, 2nd $1, 3rd $2, 4th $3, 5th $5, 6th $8, 7th $13, 8th $21, etc.
   * Wage obligation: $10 per hired hand deducted every midnight. If cash $< \text{wages}$, penalty or bankruptcy mechanisms trigger.

6. **Market & Price Elasticity:**
   * Market order limit: Up to 10 orders per turn (`BUY_SEED`, `BUY_ANIMAL`, `BUY_PRODUCT`, `BUY_LAND`, `HIRE`, `SELL`).
   * Dynamic pricing: Prices drop when heavy supply is dumped and rise under demand pressure. Town consumption drains market inventory every 4 ticks.
   * Order execution priority: SELL orders execute before BUY orders within the same turn if properly sequenced, allowing simultaneous liquidation to fund purchases.

---

## 3. Observation Space & Information Availability

### Observable State
* `farms[player]`:
  * `money`: liquid cash float.
  * `tiles[y][x]`: state of all 100 tiles on player's farm.
  * `farmer`: $(x, y)$ coordinate of player farmer.
  * `hands`: list of $(x, y)$ coordinates of hired hands.
  * `unlocked_quadrants`: list of unlocked quadrant indices.
  * `hires_today`: count of hands hired so far today.
* `private`:
  * `shed`: inventory dict of stored products.
  * `seeds`: inventory dict of held seeds.
  * `inventories`: list of inventory dicts held by farmer and each hand.
* `market`:
  * `prices`: spot market prices for all 9 commodities.
  * `inventory`: current volume of goods available in town market.
* `town`:
  * `unlocked_shops`: list of active commercial shops.
* `farms[1 - player]` (Opponent Observable subset):
  * `money`: opponent cash float.
  * `tiles[y][x]`: opponent farm grid (visible crop types, structures, weeds).
  * `farmer`, `hands`: opponent unit positions.
  * `unlocked_quadrants`: opponent land footprint.

### Strictly Unobservable (Zero-Leakage Invariants)
* Opponent's `private.shed`, `private.seeds`, and `private.inventories`.
* Opponent's hidden internal policy state or intended future action tape.
* Opponent identity string (`opp_id`) during inference.
* Future seed-dependent market shocks or town shop orders.

---

## 4. Analysis of Previous RL Failure Modes (V32 RL-X2)

Forensic analysis of the RL-X2 program reveals four distinct failure mechanisms that caused PPO cash to collapse from $104,000 down to $1,095:

1. **Physical Desynchronization via Incomplete Macro Execution:**
   RL-X2 treated macro actions (e.g. `LIVESTOCK_EXPANSION_COW`, `CROP_EXPANSION_MELON`) merely as market order injections (`mkt.append(["BUY_ANIMAL", "COW", 1])`). It did **not** provide corresponding physical chore routines to build the pasture or plant the seed. The bought animal remained in inventory, unplaced and unfed, while the underlying A7 route had no choreography to handle it.
2. **Liquidity Buffer Starvation:**
   RL-X2 injected cash-consuming purchases during early game steps without tracking A7's razor-thin cash floor ($4.00 at step 10). Spending $80 or $400 caused subsequent planned seed buys to bounce, stalling the entire planting schedule.
3. **Exploration Drift and High Intervention Frequency:**
   Without bounded intervention rules, stochastic exploration chose non-zero actions at >80% of decision ticks. Once the deterministic tape diverged by more than 2–4 physical tiles, A7's subsequent open-loop actions executed invalid no-ops (e.g., watering empty dirt or dropping into non-adjacent shed coordinates).
4. **Lack of a Grounded Closed-Loop Heuristic:**
   RL-X2 relied on A7's frozen open-loop tape as its only execution fallback. When the state drifted, A7 had no dynamic replanning capability.

---

## 5. Audit of Production Benchmark V35

* **Implementation:** `candidates/v35_a7_opening/main.py`.
* **Mechanism:** At step 0 only, resizes A7's initial 30/30 wheat wash order to 25/25:
  `[["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]`.
  For steps 1..718, it delegates 100% bit-identically to A7.
* **Why it works:** Reserving 5 wheat units preserves $125 in liquid cash, elevating the step 10 cash floor from $4.00 to $129.00+. This guarantees 0% seed order bouncing in adverse market conditions, rescuing A7 mirror losses and achieving **97.5% win rate** across the 6-opponent league.
* **Implication for V38:** Any V38 candidate must preserve this early-game liquidity safety as an absolute invariant. Any intervention that risks cash starvation is an automatic failure.

---

## 6. Reusable vs Prohibited Components

| Component | Location | Status | Rationale |
| :--- | :--- | :---: | :--- |
| `E9_AST` (A7 Standalone) | `candidates/v30_a7_standalone/main.py` | **REUSABLE (Frozen)** | Base physical choreography reference |
| `V35OpeningController` | `candidates/v35_a7_opening/main.py` | **REUSABLE (Frozen)** | Live benchmark for paired evaluation |
| `LEAGUE_OPPONENTS` | `candidates/v32_rlx2/opponents.py` | **REUSABLE** | Standard 6-opponent league loader |
| `EconomicFeatures` | `candidates/v32_rlx2/state.py` | **REUSABLE / EXTENDABLE** | Base 71-dim observable economic state |
| `MacroPlanner` / `Chore` engine | `engine/macro_planner.py` | **REUSABLE** | Dynamic closed-loop chore extraction |
| `LaborScheduler` | `engine/labor_scheduler.py` | **REUSABLE** | Daily wage and hire cost computation |
| V33 Regime Classifier | `candidates/v33_*/` | **PROHIBITED** | Contaminated with opponent ID & seed oracles |
| Unbounded Low-Level RL | P2–P7 models | **PROHIBITED** | Proved brittle, causing complete failure |
| Direct Tape Mutation | Ad-hoc edits | **PROHIBITED** | Violates physical invariance |

---

## 7. Strategic Synthesis for V38

To succeed where RL-X2 failed, V38 must adhere to five structural architectural principles:
1. **Physical Autonomy:** Every macro option must possess its own complete deterministic physical executor (e.g. if `EXPAND_LAND` is selected, an exact worker builds or preps the new area, or returns cleanly).
2. **Strict Bounded Interventions:** Interventions must be short ($H=4$ or $8$ ticks) with mandatory automatic return to the safe heuristic.
3. **Fail-Closed Liquidity Guard:** If cash drops below the proven safety floor ($C < C_{\text{safe}}$), interventions are rejected and the policy falls back to the safe heuristic.
4. **Behavioral Cloning Warm Start:** PPO must start from a policy trained to imitate verified beneficial expert interventions, with `TRUST_HEURISTIC` as the dominant prior.
5. **Causal Advantage Validation:** No intervention is promoted based on neural probability alone; every intervention must demonstrate counterfactual terminal cash improvement over V35.
