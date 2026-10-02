# V32 P9 EXECUTION FORENSICS: SIMULATOR DIVERGENCE & LEGALITY AUDIT

**Author**: Kagriculture V32 Research Program  
**Date**: 2026-09-23  
**Focus**: Detailed failure forensics, simulator edge-case handling, and legality filter design  

---

## 1. LEGALITY & SAFETY GATES: EXPERIMENT EXP-V32-P9-01

The legality smoke test evaluated the HMEH execution engine across 1,000 randomized valid unit/state configurations with randomized board quadrant locks, crop ages, animal structures, and inventory states.

```
Total Trials Evaluated:       1,000
Total Simulator Crashes:          0  (Gate A Requirement: 0)
Unexpected Illegal Actions:       0  (Gate A Requirement: 0)
Malformed Action Detections:      0
Out-of-Bounds Rejections:       100% caught and mapped to PASS
Status:                       PASSED
```

---

## 2. THE THREE CRITICAL EXECUTION TRAPS IDENTIFIED & RESOLVED

During Phase 4 integration, three non-obvious simulator execution dynamics were uncovered and formally resolved:

### Trap 1: Movement onto `LOCKED` Quadrant Tiles
- **Symptom**: Replacing `MOVES` onto `LOCKED` tiles with `["PASS"]` caused agent performance to collapse from $59,603 to $22,450.
- **Root Cause**: In Kaggle Environments (`_apply_unit_action`), units spawn on inner shed-access tiles (e.g. `(4, 4)`, `(5, 4)`, `(4, 5)`, `(5, 5)`). Three of these four inner-shed tiles start the game in `LOCKED` quadrants (NE, SW, SE). To prevent newly hired hands from being permanently trapped, the simulator engine explicitly permits units to traverse locked tiles (`_set_farmer_position(farm, idx, (nx, ny))`). Tile mutations (`PLANT`, `WATER`) remain disabled on locked tiles, but physical transit is 100% legal.
- **Fix**: The legality filter was corrected to allow movement across any coordinate within board boundaries (`0 <= x < 10` and `0 <= y < 10`), strictly rejecting only off-board moves.

### Trap 2: Intra-Step Sequential State Mutations
- **Symptom**: Water actions on newly planted crops were rejected as `WATER on non-plant tile`.
- **Root Cause**: Units act sequentially in index order within a single simulator turn (Farmer $\to$ Hand 0 $\to$ Hand 1 $\to$ ...). When Hand 0 planted a crop, the environment's observation at turn start showed an empty tile. A naive filter evaluating Hand 1's subsequent `WATER` action against the static observation snapshot misidentified the tile as empty and replaced `WATER` with `["PASS"]`, causing crops to wilt unwatered on their planting day.
- **Fix**: The legality filter now maintains a working copy of board tiles, inventories, seeds, and shed cargo, updating local state dynamically as each unit in the turn resolves.

### Trap 3: Market Queue Race Alignment via Dummy Orders
- **Symptom**: Divergence at Step 121 on Seed 249677 (`A7: [['HIRE'], []]` vs `HMEH: [['HIRE']]`).
- **Root Cause**: The simulator clears market orders by interleaving slots between players (Player 0 Slot 0, Player 1 Slot 0, Player 0 Slot 1, Player 1 Slot 1...). A7 intentionally emits empty list placeholders (`[]`) to preserve downstream market queue timing and suppress duplicate orders without losing later execution slots. Stripping empty order placeholders altered the opponent's relative queue position.
- **Fix**: Market order slot order is preserved without truncating valid dummy orders.

---

## 3. FALLBACK AND STALL FORENSICS

The 4-state fallback machine was monitored across all 120 benchmark legs:

```
Total Steps Evaluated:         86,280  (120 legs x 719 steps)
Total Fallback Activations:         0  (Emergency A7 fallback was never required)
Consecutive Stalls >= 3:            0
Runway Stress Triggers:             0  (Cash never dipped below $30.00 safety floor)
Terminal Window Transitions:      120  (Cleanly entered at Step 712 on all runs)
```

---

## 4. REPRESENTATIVE EXECUTION TRACE: SEED 249675

```
STEP 000: CASH=$3000.00 | REGIME=NORMAL | INTENT=A7 Step 0 Wash Preservation
          ACTION: farmer=['PASS'] | market=[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]
          POST-WASH CASH: $3054.00 (+$1,286 alpha preserved)

STEP 001: CASH=$3054.00 | REGIME=NORMAL | INTENT=Opening Livestock Setup
          ACTION: farmer=['NORTH'] | market=[['SELL', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 5], ['HIRE']*5, ['BUY_ANIMAL', 'COW', 2], ['BUY_ANIMAL', 'SHEEP', 2]]

STEP 150: CASH=$ 4200.00 | REGIME=NORMAL | INTENT=Quadrant 2 Expansion
          ACTION: market=[['BUY_LAND']] | UNLOCKED_QUADS=['NW', 'NE']

STEP 648: CASH=$47949.00 | REGIME=NORMAL | INTENT=Day 27 Terminal Harvest Surge
          ACTION: market=[['HIRE']*10] | ACTIVE_HANDS=10 | CHORES_EXECUTED=18

STEP 718: CASH=$59603.00 | REGIME=LIQUIDATION | INTENT=Terminal Liquidation
          ACTION: market=[['SELL', 'MILK', 12], ['SELL', 'WOOL', 8], ['SELL', 'STRAWBERRY', 16]]
          TERMINAL SHED CARGO: 0 | TERMINAL HAND CARGO: 0 | TERMINAL CASH: $59,603.00
```
