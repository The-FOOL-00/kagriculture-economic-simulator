# V32 P8 — ARCHITECTURE PROPOSAL: HIERARCHICAL MACRO-ECONOMIC HYBRID (HMEH)
**Phase:** V32 P8  
**Date:** 2026-09-23  
**Status:** PROPOSED FOR IMPLEMENTATION IN P9  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. ARCHITECTURAL OVERVIEW

The Kagriculture research program is pivoting from end-to-end neural behavioral cloning to a **Hierarchical Macro-Economic Hybrid (HMEH)** architecture.

Instead of asking a feedforward or recurrent neural network to simultaneously solve high-level economic capital allocation and low-level grid movement, HMEH strictly separates **Strategic Macro-Planning** from **Deterministic Physical Execution**:

```text
========================================================================================
                                 HMEH INFORMATION PIPELINE
========================================================================================

                                  KAGGLE OBSERVATION
                                          │
                                          ▼
                       [1. ECONOMIC STATE REPRESENTATION]
                                          │
                Extracts Capital, Production, Land, Labor, Market, Horizon
                                          │
                                          ▼
                          [2. EVENT-DRIVEN REPLANNER]
                                          │
            Fires on Shop Reveals (Day 3, 6), Price Shock, Cash/Wage Stress
                                          │
                                          ▼
                             [3. MACRO-ECONOMIC PLANNER]
                                          │
             Decides Strategic Intent: Target Crop Portfolio, Animal Caps,
               Labor Headcount, Land Expansion, Market Orders (30-Wash)
                                          │
                                          ▼
                             [4. STATEFUL CHORE EXECUTOR]
                                          │
                 4-Pass Spatial Dispatch: Stand-On Chores, Shed Operations,
                         Spatial Chore Bidding, BFS Pathfinding
                                          │
                                          ▼
                           [5. LEGALITY & SAFETY FILTER]
                                          │
                  Simulator-Grounded Validity Mask (Shed Adjacency,
                  Maturity Gating, Seed Budget, Order Clamp <= 10)
                                          │
                                          ▼
                          [6. INVARIANT FALLBACK SYSTEM]
                                          │
                 Detects Stalls, Cash-Runway Failure -> Falls Back to
                            Protected A7 Standalone Actions
                                          │
                                          ▼
                             ACTION DICT -> SIMULATOR
========================================================================================
```

---

## 2. COMPONENT 1: ECONOMIC STATE REPRESENTATION

The agent maintains an explicit, strongly typed, interpretable economic state snapshot extracted from `observation` at every turn $t$:

```python
@dataclass
class EconomicState:
    # 1. CAPITAL
    cash: float                     # Farm liquid cash balance
    committed_wages_today: float    # Projected daily wage burden for hired hands
    wage_runway_days: float         # cash / (daily wage burden + 1e-5)
    liquid_inventory_value: float   # Shed stock valued at current market bid prices
    
    # 2. PRODUCTION & FIELD ASSETS
    planted_crops: Dict[str, int]   # Active plant count by crop type
    crop_stages: Dict[str, List]    # Maturity age, yield units, watering status per tile
    unfed_animals: List[Tuple[int, int]] # Locations of animals requiring feed today
    unwatered_crops: List[Tuple[int, int]] # Locations of crops requiring water today
    shed_inventory: Dict[str, int]  # Physical stock held in central shed
    carried_inventory: Dict[str, int] # Physical stock held in worker hands
    
    # 3. LAND
    unlocked_quadrants: int         # Count of unlocked 5x5 quadrants (1 to 4)
    unused_arable_tiles: int        # Vacant, non-weed, non-structure tiles available
    weed_tiles: List[Tuple[int, int]] # Locations of tiles blocked by weeds
    
    # 4. LABOR
    active_workers: int             # Farmer (1) + hired hands count
    hires_today: int                # Hires completed during current game day
    next_hire_cost: int             # Fibonacci marginal cost for hiring next worker
    
    # 5. MARKET & TOWN
    prices: Dict[str, float]        # Current market spot prices for all 9 products
    price_trends: Dict[str, float]  # Rolling price delta over last 24/72 turns
    unlocked_shops: List[str]       # Town shops revealed on Days 3, 6, 9...
    
    # 6. HORIZON & TIME
    step: int                       # Current game turn (0 to 718)
    day: int                        # Current day (0 to 29)
    hour: int                       # Current hour within day (0 to 23)
    remaining_steps: int            # 718 - step
```

---

## 7. COMPONENT 2: EVENT-DRIVEN REPLANNER

Rather than executing a monolithic 719-step tape, the Macro-Planner evaluates strategic transitions when specific environmental triggers fire:

| Trigger | Timing | Re-planning Action |
| :--- | :---: | :--- |
| **Opening Bootstrap** | Step 0 | Execute proven 30-wash (`[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]`). Preserves ~$108 cash buffer. |
| **Opening Livestock Setup**| Steps 1–8 | Hire 5 hands, retrieve Sheep + Wheat, construct Pasture at `[3, 3]`, place animal. |
| **Day 3 Shop Reveal** | Step 72 | Inspect first unlocked shop. If `BAKERY` or `PET_CAFE`, increase Wheat/Carrot target; if `YARN_STORE`, maintain Wool production. |
| **Day 6 Shop Reveal** | Step 144 | Inspect second unlocked shop. Finalize crop portfolio: trigger Melon expansion if no Pet Cafe glut, or Strawberry specialization if high prices persist. |
| **Land Expansion Milestones**| Steps 150 & 265| Unlock Quadrants 2 and 3 if cash exceeds land price + $300 minimum operational buffer. |
| **Wage Runway Stress** | Any Turn | If `wage_runway_days < 2.0`, freeze hiring, throttle seed purchases, and initiate batch liquidation of highest-value shed inventory. |
| **Terminal Liquidation** | Steps 712–718 | Enter 7-turn terminal closure. Cease all planting/fertilizing; route all workers to final harvest and dump 100% of inventory into market. |

---

## 4. COMPONENT 3: MACRO-ECONOMIC PLANNER

The Macro-Planner outputs high-level strategic targets for the current cycle:
- **Target Labor Headcount:** $N_{\text{workers}} = \min(M_{\text{max}}, \lfloor (N_{\text{chores}} + 8) / 8 \rfloor)$, ensuring every hired worker generates positive net marginal product above Fibonacci wage cost.
- **Crop Portfolio Allocation:** Decides the planting ratio across vacant tiles:
  - Melon heavy (Days 0–12): Targets 12 melon plants to exploit early harvest compounding.
  - Strawberry continuous (Days 12–25): High recurring harvest yields without replanting.
  - Wheat feed buffer: Maintains 24 wheat units reserved in shed for animal feeding.
- **Animal Purchase Thresholds:** Buys additional cows/sheep only if cash exceeds $695 / $595 and feed reserve is guaranteed for $\ge 3$ days.
- **Market Liquidation Batches:** Groups produce into batches of 18–24 units to maximize price realization and avoid slippage traps.

---

## 5. COMPONENT 4: STATEFUL CHORE EXECUTOR

Low-level worker actions are generated by a deterministic **4-Pass Spatial Chore Dispatcher** (extending the proven `DeclarativeBackboneCompiler` from `candidates/declarative_backbone/`):

1. **Pass 1 — Stand-On Chores (Zero Movement Cost):**
   If a worker is already standing on a tile with an urgent chore (Harvest mature plant, water dry crop, feed unfed animal, dig blocking weed), execute immediately.
2. **Pass 2 — Shed Logistics:**
   If a worker is adjacent to the central shed and holds harvested produce, emit `DROP`. If the worker is designated to stock animals or feed, emit `PICKUP`.
3. **Pass 3 — Spatial Chore Assignment:**
   Unassigned workers compute Manhattan distances to all pending chores. Chores are prioritized by economic weight:
   $$\text{Weight}(\text{HARVEST}) = 100 > \text{Weight}(\text{DIG\_WEED}) = 95 > \text{Weight}(\text{FEED}) = 92 > \text{Weight}(\text{WATER}) = 82 > \text{Weight}(\text{CARE}) = 76$$
4. **Pass 4 — Pathfinding & Collision Avoidance:**
   Workers navigate along grid shortest paths using obstacle-aware step selection (`_get_next_step`). Extra hands are padded with `PASS` to strictly conform to simulator action schemas.

---

## 6. COMPONENT 5: LEGALITY & SAFETY FILTER

Every proposed action passes through a simulator-grounded validity mask before emission:
- **`PICKUP` / `DROP` / `PLACE`:** Strictly verified against `_is_shed_adjacent(pos, board_size)`. Prevents illegal pickup calls that caused P5/P6 failures.
- **`PLANT`:** Verified against `seeds[crop] > 0` and `tile is None`.
- **`WATER`:** Verified against `tile.kind == 'PLANT'` and `not tile.watered_today`.
- **`HARVEST`:** Verified against `age >= max_yield_day` to eliminate zero-yield premature harvest locks.
- **Market Orders:** Clamped to $\le 10$ orders per turn and non-negative integer quantities.

---

## 7. COMPONENT 6: INVARIANT FALLBACK SYSTEM

To guarantee zero crashes and 100% competition safety:
- All planner operations execute inside guarded `try...except` blocks.
- If an unhandled exception or contradictory state is detected, the agent falls back instantly to the protected `A7` standalone action for the current step.
- The agent never emits empty unit lists or malformed dictionaries.

---

## 8. COMPONENT 7: EVALUATION & PROMOTION LOOP

The proposed architecture will be evaluated strictly on:
1. **The 120-Leg Development Screen:**
   - 10 Seeds (249675–249684) $\times$ 6 Opponents $\times$ 2 Seats.
   - Core Opponents: `E0_V3`, `E1_V22R1`, `E2_A7`, `E8_DMITRII`, `V54`, `SYN_AGG`.
2. **Gate Criteria for Promotion:**
   - **G1:** 0 / 120 Crashes or Illegal Actions (100% legality).
   - **G2:** Median Terminal Cash $\ge \$80,000$ across the 120-leg screen.
   - **G3:** Paired Margin vs `E2_A7` $\ge +\$2,000$ mean, with positive win rate ($> 60\%$).
   - **G4:** Downside resilience vs `SYN_AGG` and `E8_DMITRII` (win rate $\ge 50\%$).
3. **Protected Holdout Integrity:**
   - Virgin holdout cohorts (`214200–214249`, `340090–340199`, `249695–249734`) remain 100% untouched until final submission release gating.
