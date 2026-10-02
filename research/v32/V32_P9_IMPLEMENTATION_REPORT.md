# V32 P9 IMPLEMENTATION REPORT: HIERARCHICAL MACRO-ECONOMIC HYBRID (HMEH)

**Author**: Kagriculture V32 Research Program  
**Date**: 2026-09-23  
**Phase**: V32 P9 (Post-P8 Macro-Economic Transition)  
**Status**: COMPLETE — ALL GATES VERIFIED  

---

## 1. ARCHITECTURAL OVERVIEW

The Hierarchical Macro-Economic Hybrid (HMEH) replaces the brittle, open-loop neural Behavioral Cloning (BC) line (permanently closed in P8) with a 5-layer state-grounded, modular macro-economic architecture:

```
                  +-----------------------------------+
                  |           OBSERVATION             |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |      LAYER 1: ECONOMIC STATE      |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   LAYER 2: MACRO REPLANNER        |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |     LAYER 3: STRATEGIC INTENT     |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |    LAYER 4: CHORE EXECUTOR        |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |  LAYER 5: LEGALITY / SAFETY FILTER|
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |             SIMULATOR             |
                  +-----------------------------------+
```

---

## 2. COMPONENT MODULE SPECIFICATIONS

All research modules are cleanly partitioned in `candidates/v32_hmeh/` with zero modifications to frozen competition packages:

### Layer 1: Economic State Extractor (`economic_state.py`)
Extracts a fully interpretable, typed `EconomicState` dataclass from raw observations:
- **Capital**:
  - `cash`: Available liquid money.
  - `committed_cash`: Planned expenditure this cycle.
  - `liquid_inventory_value`: Shed goods $\times$ spot prices.
  - `wage_runway_days`: Cash / daily wage burn.
- **Labor**:
  - `active_workers`: Farmer (1) + hired hands.
  - `idle_hands`: Hands without assigned physical chores.
  - `pending_chore_count`: Queue of weeds to dig, crops to water/harvest, animals to feed/care.
  - `worker_utilization`: $(active\_workers - idle\_hands) / active\_workers$.
- **Crops & Land**:
  - `unlocked_quadrants`: Count of unlocked board sectors (1 to 4).
  - `vacant_arable_tiles`: Owned empty tiles ready for planting.
  - `planted_crops`: Breakdown by crop type (`WHEAT`, `CARROT`, `STRAWBERRY`, `MELON`).
- **Market & Town**:
  - `spot_prices`: Current prices for all 9 tradeable commodities.
  - `unlocked_shops`: Town facilities revealed at Day 3, 6, 9.
  - `is_terminal_window`: Boolean flag active on steps $\ge 712$.

### Layer 2 & 3: Event-Driven Macro Replanner & Strategic Intent (`macro_planner.py`, `strategies.py`)
Generates high-level `StrategicIntent` rather than single-step movement commands. Replanning is triggered by discrete economic milestones:
1. `EVENT_BOOTSTRAP_STEP0`: Step 0 wash trigger (exact 30/30 wheat buy/sell preservation).
2. `EVENT_LIVESTOCK_INIT`: Step 1 initial 5-hand labor burst for pasture infrastructure.
3. `EVENT_RUNWAY_STRESS`: Wage runway $< 2.0$ days; transitions fallback machine to `CAUTION`.
4. `EVENT_LAND_1` / `EVENT_LAND_2`: Quadrant expansion at steps 150 and 265.
5. `EVENT_TERMINAL_WINDOW`: Step $\ge 712$; triggers full shed liquidation.

### Layer 4: Deterministic Chore Executor (`executor.py`)
Converts `StrategicIntent` into spatial, unit-level actions:
- **Pass 1: Stand-on Chores**: High-priority immediate actions (DIG weeds underfoot, HARVEST mature crops, CARE/FEED animals).
- **Pass 2: Shed Logistics**: Adjacent units deposit harvested cargo or pick up seeds/animals.
- **Pass 3: Targeted Chore Routing**: Assigns nearest idle hands to unworked tiles via Manhattan/BFS shortest paths.
- **Pass 4: Fallback Navigation**: Routes unassigned hands toward the central shed corridor.

### Layer 5: Legality and Safety Filter (`legality.py`)
Prevents simulator errors and disqualifications:
- Bounds checks all unit moves to the $10 \times 10$ board.
- Allows legal grid movement onto `LOCKED` shed-access tiles (matching engine semantics).
- Validates seed inventory prior to planting.
- Tracks intra-step sequential mutations across units (e.g. Hand 0 plants $\to$ Hand 1 waters).
- Clamps market orders to $\le 10$ and enforces non-negative order quantities.

### Layer 6: Fallback System (`fallback.py`)
Maintains a 4-state deterministic finite state machine (`NORMAL`, `CAUTION`, `RECOVERY`, `LIQUIDATION`) and an emergency fail-safe to isolated standalone A7 execution.

---

## 3. AUDIT OF DEPENDENCIES

| Module | Source / Dependency | Status |
|---|---|---|
| `E9_AST` (A7 Standalone) | `candidates/v30_a7_standalone/main.py` | Embedded / Isolated |
| `E0_V3` (V3 Backbone) | `aec/backbone/v3_adapter.py` | Read-Only Frozen |
| `E1_V22R1` | `submission_aec_v22r1.tar.gz` | Read-Only Frozen |
| Simulator Engine | `kaggle_environments` 1.32.7 | Verified Digest |

---

## 4. GATE VERIFICATION SUMMARY

- **Gate A (Legality Smoke Test EXP-V32-P9-01)**:
  - 1,000 randomized state trials: **0 crashes, 0 unexpected illegal actions** (PASS).
- **Gate B (A7 Mechanism Preservation EXP-V32-P9-02)**:
  - Step-0 30-wash test: 0 failures / 1,000 trials (100% exact `[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]`).
  - Closed-loop post-wash cash: $3,054.00 (+$1,286 alpha preserved).
- **Gate C (Frozen Dependency Integrity)**:
  - `tests/test_v32_freeze.py`: 6/6 tests PASSED (0 drift across all 12 SHA256 hashes).
