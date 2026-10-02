# WHY IT WORKS: CAUSAL MECHANISM ANALYSIS

## Mechanism 1: Dmitrii Gluzdov HybridOpening with Extra-Day Wheat Maturation

### 1. Observed State
- At turn 0, the farm board contains 1 farmer at (5,5) and 5 worker hands.
- In the canonical "2945 Farm" route (Hayashi EXP240 / R42), Hand 1 passes for several turns waiting for pasture land allocation. Hand 0 finishes initial quadrant clearing and idles on days 2–3.
- The (2,4) pasture tile is scheduled to be constructed on Day 3, leaving it completely unoccupied on Days 0, 1, and 2.

### 2. Action Difference
- **Turn 0**: Buys 1 extra WHEAT seed (`['BUY_SEED', 'WHEAT', 1]`) for $2.
- **Turns 2–6**: Idle Hand 1 walks WEST 3 tiles to (2,4), plants WHEAT at turn 5, and waters it at turn 6.
- **Turn 29 (Day 1)**: Hand 2 waters the wheat crop instead of building the pasture (which is not yet needed).
- **Turn 52 (Day 2)**: Waters the wheat crop; holds harvest for 24 extra hours to allow the crop to reach maximum maturity (10 yield units instead of 5).
- **Turns 84–91 (Day 3)**: Idle Hand 0 waters, harvests 10 wheat, builds the pasture enclosure on time, returns to the shed, and drops the wheat at turn 91.

### 3. Economic Effect
- Generates 10 units of WHEAT from previously idle worker turns.
- After feeding the newly purchased livestock, provides +3 net WHEAT in the shed at turn 91.
- V49 has 0 shed wheat at turn 91 and must divert cash to purchase feed; V24 holds a surplus.
- This early capital float compounds aggressively across the entire 719-step episode:
  - Turn 216: +29 cash lead.
  - Turn 500: +543 cash lead.
  - Turn 600: +1,028 cash lead.
  - Turn 718: +2,226 cash lead.

### 4. Failure Cases & Safety Bounds
- Hand 0 must be guaranteed free on day 3 at turns 84–91. In all 41 routes of the 2945 chassis, Hand 0 has completed its quadrant work and is idle during this exact window.
- The pasture must be built before day 3 nightfall. Hand 0 builds the pasture at turn 88, perfectly on schedule.
- Zero pasture delays or livestock placement blocks.

### 5. Benchmark Evidence
- 100% win rate across all 8 legs vs V49 (+1,532.9 mean cash advantage).
- 100% win rate (4/4) across V49's historical loss worlds on seeds 250617 and 250621 vs V44 (+822.0 mean cash advantage).

---

## Mechanism 2: V24 Stranded Sheep Rescue Fix & Tetsutani Room Guard

### 1. Observed State
- In high-production regimes or when crop substitutions tilt hard towards CARROT, shed WHEAT inventory can temporarily hit 0 while sheep in pastures require daily feeding.
- At hour 23, total shed inventory plus worker backpack cargo can exceed the hard engine shed limit of 100 items.

### 2. Action Difference
- **In V27**: When shed WHEAT = 0, the compact sheep worker issues `['PICKUP', 'WHEAT', 0]`. V27 checks `command[:2] == ['PICKUP', 'WHEAT']` and assumes the pickup succeeded. It aborts rescue, causing the worker to loop forever with 0 wheat, starving the sheep.
- **In V24**: Checks `len(command) > 2 and command[2] > 0`. When quantity is 0, it recognizes that zero feed was picked up and invokes `_v234_rescue`, which submits an immediate market purchase for WHEAT feed.
- **In V24 Room Guard**: At hour 23, `_room_guard` calculates `shed + carried + produced - consumed - 99`. If positive, it issues immediate market `SELL` orders for items that have no future route requirement, converting items that would be destroyed into cash.

### 3. Economic Effect
- Prevents catastrophic stalls on low-wheat seeds where V27 starved sheep and lost wool harvests.
- Prevents silent destruction of valuable crops/goods at hour 23, adding +55.2 mean cash per game.

### 4. Benchmark Evidence
- In direct head-to-head duels, V24 decisively defeats V27 (7 wins, 1 loss, 87.5% win rate).
- Ablating `room_guard` directly degraded mean cash across tested validation seeds.
