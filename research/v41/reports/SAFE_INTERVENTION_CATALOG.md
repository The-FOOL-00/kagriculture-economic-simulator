# V41 Safe Strategic Intervention Catalog & Classification

**Document ID:** `research/v41/reports/SAFE_INTERVENTION_CATALOG.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Scope:** Formal classification, preconditions, invariants, and failure modes for all candidate strategic interventions under the V41 Safe Residual RL architecture.

---

## 1. Safety Classification Hierarchy

Every candidate strategic decision is formally assigned to one of four authoritative safety classes:

```text
┌────────────────────────────────────────────────────────┐
│                      SAFE_ATOMIC                       │
│  Zero physical mutation; touches only market buffers   │
│  and unallocated inventory. Requires NO replan.        │
└────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────┐
│                   CONDITIONALLY_SAFE                   │
│  Safe only under strict economic / timing thresholds.  │
│  Preconditions must be formally proved at runtime.     │
└────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────┐
│                    SAFE_WITH_REPLAN                    │
│  Mutates physical resources (land, workers, crops).    │
│  Requires StateAwareExecutor to regenerate valid       │
│  worker waypoint trajectories before execution.        │
└────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────┐
│                         UNSAFE                         │
│  Inherently breaks chore synchronization or destroys   │
│  incumbent capital invariants. PERMANENTLY PROHIBITED. │
└────────────────────────────────────────────────────────┘
```

---

## 2. Complete Intervention Catalog

### A. SAFE_ATOMIC Interventions (Zero Replan Overhead)

#### 1. `TERMINAL_LIQUIDATE_STEP_694` (The V39 Proven Liquidation)
- **Class:** `SAFE_ATOMIC`
- **Preconditions:** `step in (693, 694)`; shed contains marketable goods (`STRAWBERRY`, `MILK`, `WOOL`, `MELON`).
- **Mechanical Action:** Injects `["SELL", item, qty]` into the market order queue up to the 10-order limit.
- **Safety Proof:** Physical chores are already completed for the day or do not depend on sold goods; front-runs opponent's Step 695 market dump, preserving $10,000–$15,000 in terminal value.
- **Historical Evidence:** 100% win rate across all verified V39 tournament evaluations.

#### 2. `OPPORTUNISTIC_SPOT_SALE`
- **Class:** `SAFE_ATOMIC`
- **Preconditions:** Shed inventory of commodity $C \ge 2$; current spot price $P(C) \ge \text{Threshold}(C)$ (e.g. Milk $\ge \$35$, Wool $\ge \$40$); item is not reserved for animal feed.
- **Mechanical Action:** Injects atomic `["SELL", C, qty]` into market queue without modifying worker movements.
- **Safety Proof:** Unallocated inventory in the shed is liquid. Selling it increases farm cash balance, expanding the budget buffer for `_budget_guard`.

#### 3. `ENDGAME_FULL_FLUSH`
- **Class:** `SAFE_ATOMIC`
- **Preconditions:** `step >= 710`; shed contains any non-zero marketable products.
- **Mechanical Action:** Generates full `SELL` orders for all commodities in shed before the simulation closes at step 718.
- **Safety Proof:** No further planting, feeding, or watering cycles can occur before episode end. Zero physical dependency risk.

#### 4. `CANCEL_SPECULATIVE_MARKET_ORDERS`
- **Class:** `SAFE_ATOMIC`
- **Preconditions:** Liquid cash drops below the critical liquidity buffer ($200); unexecuted non-essential buy orders exist in the market buffer.
- **Mechanical Action:** Removes speculative buy orders to protect working capital.
- **Safety Proof:** Prevents bankruptcy defaults and order bouncing.

---

### B. CONDITIONALLY_SAFE Interventions

#### 5. `SELECTIVE_HOLD_DEPRESSED_GOODS`
- **Class:** `CONDITIONALLY_SAFE`
- **Preconditions:** `step < 650`; commodity spot price is severely depressed ($P < \$18$); shed capacity utilization is below 75% (at least 25 slots free); upcoming production will not trigger shed overflow.
- **Mechanical Action:** Filters out planned sales of the depressed commodity from the current step's market order list.
- **Failure Risk:** If shed reaches capacity (100 items) at hour 23, `_room_guard` will forcibly dump items at the prevailing price anyway.
- **Safety Guard:** Must verify `projected_shed_volume(t + 24) <= 90`.

#### 6. `DEFER_EXPANSION_ON_LOW_CASH`
- **Class:** `CONDITIONALLY_SAFE`
- **Preconditions:** `step < 500`; cash $< \text{LandCost} + \$500$; the planned route included `["BUY_LAND"]`.
- **Mechanical Action:** Defers `["BUY_LAND"]` to the next 72-turn block.
- **Safety Guard:** Must verify that no worker trajectory in the subsequent 24 turns routes into the locked quadrant. If a worker has waypoints on the locked quadrant, deferral must be REJECTED.

---

### C. SAFE_WITH_REPLAN Interventions

#### 7. `MIDGAME_LAND_EXPANSION_F5` (RLX2 / F5 Discovery)
- **Class:** `SAFE_WITH_REPLAN`
- **Preconditions:** `280 <= step <= 312`; liquid cash $\ge \$12,000$; unlocked quadrants $< 4$.
- **Mechanical Action:** Executes `["BUY_LAND"]` to unlock Quadrant 2 or 3.
- **Required Replan:**
  1. Update spatial tile grid status from `LOCKED` to `EMPTY`.
  2. Synthesize worker plow/plant/water trajectories for the newly unlocked acreage.
  3. Recompute budget guard expectations for future quadrant prices.
- **Status in V40:** Unsafe (caused $-8,615 loss due to lack of chore routing).
- **Status in V41:** Permitted ONLY when `StateAwareExecutor` confirms dynamic trajectory splicing.

#### 8. `DYNAMIC_LABOR_REALLOCATION`
- **Class:** `SAFE_WITH_REPLAN`
- **Preconditions:** Crop maturity status warrants multi-worker harvesting; or emergency weed outbreak detected.
- **Mechanical Action:** Temporarily diverts worker $W_i$ from routine watering/patrol to localized task execution.
- **Required Replan:** Trajectory reconnect bridge (`aec.replanning.reconnect.ReconnectRequest`) ensuring worker returns to baseline waypoint queue before the next mandatory chore cycle.

---

### D. UNSAFE Interventions (Permanently Prohibited)

#### 9. `UNRESTRICTED_FREEZE_HIRING`
- **Class:** `UNSAFE`
- **Rationale:** Canceling a scheduled hire while the base controller executes a multi-worker route causes immediate chore truncation via `_hand_align`. Fields are abandoned, watering is missed, weeds proliferate, causing $-11,466 average casualty.
- **Governance:** **PERMANENTLY PROHIBITED.**

#### 10. `BLIND_UNBUDGETED_HIRE`
- **Class:** `UNSAFE`
- **Rationale:** Hiring an unbudgeted worker creates an idle agent executing `PASS` that burns exponential daily Fibonacci wages ($F_{hires}$) with zero economic contribution.
- **Governance:** **PERMANENTLY PROHIBITED.**

#### 11. `UNCOORDINATED_ANIMAL_PURCHASE`
- **Class:** `UNSAFE`
- **Rationale:** Purchasing cows or sheep without dedicated pasture structures and daily wheat feeding chores wastes $400–$500 in capital and produces zero milk/wool.
- **Governance:** **PERMANENTLY PROHIBITED.**

#### 12. `UNCOORDINATED_SEED_PURCHASE`
- **Class:** `UNSAFE`
- **Rationale:** Buying melon or carrot seeds when the chore schedule only plants wheat leaves seeds permanently idle in shed inventory.
- **Governance:** **PERMANENTLY PROHIBITED.**

---

## 3. Summary Table: Intervention Safety & Execution Protocol

| Intervention Name | Target Subsystem | Safety Class | Replan Engine | Counterfactual Gating Horizon | Allowed in V41? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `NO_INTERVENTION` | None | `SAFE_ATOMIC` | None (V35 native) | 0 (Identity) | **YES (Default)** |
| `TERMINAL_LIQUIDATE_694` | Market | `SAFE_ATOMIC` | None | Full episode rollout | **YES** |
| `OPPORTUNISTIC_SPOT_SALE` | Market | `SAFE_ATOMIC` | None | 24 turns | **YES** |
| `ENDGAME_FULL_FLUSH` | Market | `SAFE_ATOMIC` | None | 8 turns | **YES** |
| `SELECTIVE_HOLD` | Market | `CONDITIONALLY_SAFE` | None (Capacity check) | 24 turns | **YES** |
| `DEFER_EXPANSION` | Land / Market | `CONDITIONALLY_SAFE` | Route check | 72 turns | **YES (Gated)** |
| `MIDGAME_LAND_EXPANSION` | Land / Physical | `SAFE_WITH_REPLAN` | `StateAwareExecutor` | 72 turns | **Gated by Replan** |
| `FREEZE_HIRING` | Labor | `UNSAFE` | Broken in tape | N/A | **PROHIBITED** |
| `BLIND_HIRE` | Labor | `UNSAFE` | Idle wage drain | N/A | **PROHIBITED** |
| `BLIND_BUY_ANIMAL` | Animals | `UNSAFE` | Unfed / unplaced | N/A | **PROHIBITED** |
| `BLIND_BUY_SEED` | Crops | `UNSAFE` | Unplanted stock | N/A | **PROHIBITED** |
