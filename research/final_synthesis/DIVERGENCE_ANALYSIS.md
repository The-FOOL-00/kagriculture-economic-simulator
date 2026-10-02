# DIFFERENTIAL DIVERGENCE ANALYSIS

## 1. Divergence Analysis: V49 vs Teammate (V24 / Final Candidate)

### Divergence Point 1: Opening Turn 0 Market Orders
- **Step**: Step 0 (Day 0, Hour 0)
- **State Before Action**: Initial cash 1,000.0, empty inventory, 1 farmer at (5,5), 5 hands at (4,4), (5,4), (6,4), (4,5), (5,6).
- **V49 Action**: `market: [['BUY_PRODUCT', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]` (Total cost: 43 wheat = $430)
- **V24 / Candidate Action**: `market: [['BUY_PRODUCT', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30], ['BUY_SEED', 'WHEAT', 1]]` (Additional $2 for 1 wheat seed)
- **Downstream Consequence**: V24 possesses 1 WHEAT seed at turn 0.

### Divergence Point 2: Worker Hand Reassignment (Turn 2 to 6)
- **Step**: Steps 2, 3, 4, 5, 6
- **V49 Action**: `hands[1]` issues `['PASS']` across all 5 turns.
- **V24 / Candidate Action**: `hands[1]` moves `['WEST']` 3 times from (5,4) to future pasture site (2,4), issues `['PLANT', 'WHEAT']` at step 5, and `['WATER']` at step 6.
- **Causal Analysis**: In V49, Hand 1 is completely idle, wasting 5 labor-turns. In V24, Hand 1 utilizes this surplus labor to plant and water a temporary wheat crop on land that will not be enclosed as pasture until day 3. Zero disruption to any existing building or planting schedule.

### Divergence Point 3: Maturation & Day 3 Harvest / Pasture Restoration (Turn 84 to 91)
- **Step**: Steps 84–91 (Day 3, Hours 12–19)
- **V49 Action**: Hand 0 idles after finishing early tasks at (0,4).
- **V24 / Candidate Action**: Hand 0 walks `['EAST', 'EAST']`, `['WATER']`, `['HARVEST']` (yields 10 wheat), `['BUILD_PASTURE']` (restores planned pasture exactly on schedule), walks `['EAST', 'EAST']`, and `['DROP']`s 10 wheat into the shed at step 91.
- **Economic Consequence**: At step 91, V49 shed has 0 wheat, whereas V24 shed has 3 wheat (after feeding animals). At step 144, V49 has 9 wheat vs V24's 12 wheat.
- **Causal Compounding**:
  - Step 216: V24 leads cash by +29.0.
  - Step 500: V24 leads cash by +543.0.
  - Step 600: V24 leads cash by +1,028.0.
  - Step 700: V24 leads cash by +1,932.0.
  - Step 718: V24 finishes with +2,226.0 cash advantage over V49.
- **Conclusion**: Causal, highly repeatable, 100% deterministic economic acceleration.

---

## 2. Divergence Analysis: Teammate V24 vs Teammate V27

### Divergence Point 1: `_v234_rescue` Handling of Depleted Wheat
- **Trigger**: Shed WHEAT drops to 0 while sheep are hungry.
- **V27 Action**: Sheep feeding worker issues `['PICKUP', 'WHEAT', 0]`. v27 inspects `command[:2] == ['PICKUP', 'WHEAT']` and treats this as "handled", aborting rescue logic.
- **V27 Consequence**: Worker loops `['PICKUP', 'WHEAT', 0]` indefinitely. Sheep starve, wool is unharvested, and the agent falls into an irrecoverable production stall.
- **V24 Fix**: Checks `len(command) > 2 and command[2] > 0`. Because quantity is 0, v24 falls through to `_v234_rescue`, which orders emergency feed purchases from the market. Sheep are fed, and normal production resumes.

### Divergence Point 2: Room Guard & Dead Stock Settings
- **Trigger**: Hour 23 shed inventory near capacity (99 units), and end-of-route surplus items.
- **V27 Behavior**: `room_guard=False, dead_stock=False`. Shed overflow is silently destroyed by the game engine at hour 23.
- **V24 Behavior**: `room_guard=True, dead_stock=True`. `_room_guard` detects shed total > 99 and injects emergency sales for products without future route needs, converting would-be-destroyed commodities into hard cash.
- **Empirical Win Delta**: Ablating `room_guard` and `dead_stock` in V24 caused a direct loss of 55.2 cash per game across seeds.

### Divergence Point 3: PET_CAFE Demand Margin Tilt
- **Trigger**: Days 10–23 when `PET_CAFE` is present in town unlocked shops.
- **V27 Behavior**: `_CA_MARGIN` remains fixed at `-15.0`.
- **V24 Behavior**: `pet_any_demand_agent` temporarily sets `_CA_MARGIN = -30.0`.
- **Economic Effect**: Carrots yield significantly higher prices at PET_CAFE. Biasing the crop substitution equation (`3*(p_c - drop) - 20 > 4*p_w - 10 + margin`) toward CARROT increases total realized market revenue.
- **Empirical Win Delta**: Head-to-head win rate drops from 7/8 (87.5%) down to 5/8 (62.5%) when PET tilt is removed from V24.

---

## 3. Loss Boundary Divergence: V49 vs V44 on Seeds 250617 & 250621

### Analysis of Historical V49 Losses
- In V56/V57, V49 suffered 4 losses against `v44_economic_portfolio` on seeds 250617 and 250621.
- In both worlds, V49 entered step 690 with a cash lead. However, at step 697, market queue collision resulted in V49's sell orders being executed after V44's, saturating town demand at lower prices.
- **V24 Intervention**:
  - On seed 250617: V24 enters the endgame with 116,374 cash (vs V44's 115,901) and wins both seats (+473.0 margin).
  - On seed 250621: V24 enters the endgame with 117,570 cash (vs V44's 116,399) and wins both seats (+1,171.0 margin).
  - **Result**: V24 achieves a clean 4/4 sweep on the exact seeds where V49 suffered all of its benchmark losses.
