# TEAMMATE AGENT ARCHITECTURE AUDIT: Vj_kc_v24 & Vj_kc_v27

**Subject Artifacts**:
- `team_submissions/submission_Vj_kc_v24.tar.gz` (SHA256: `4C9EF1DC189DE6185AFADE682CB8A758139390E4BAA8B6A010500443C75BD5CE`)
- `team_submissions/submission_Vj_kc_v27.tar.gz` (SHA256: `EEE5AD4D7C67B27D7713E70B4B9E56220E92A8E8B90E6C59656A93ECE74B9A6C`)
- Inner Decoded Sources: `research/final_synthesis/teammates/v24/decoded_inner.py` & `.../v27/decoded_inner.py`

---

## 1. High-Level Architectural Decomposition

The teammate submissions represent an advanced multi-layered hybrid architecture integrating the historical public "2945 Farm" base (Hayashi, Tschinkel, destbreso, aurax7) with Dmitrii Gluzdov's productive opening alterations, Ahmed Berat Ozer's market/crop orderings, and a long iterative chain of micro-optimization wrappers.

```
+-------------------------------------------------------------------------------+
| Layer 12: Production Safety Wrapper (_v24_safety_agent / _v27_safety_agent)   |
|   - Try/catch top-level fallback to PASS                                      |
|   - Shape sanitation: dict, farmer, hands list, market list trimmed to <= 10  |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 11: PET_CAFE Demand Margin Tilt (Active in v24; omitted in v27)        |
|   - Day 10..23 when 'PET_CAFE' in town shops: _CA_MARGIN = -30.0              |
|   - Heavily biases crop production toward high-value CARROT sales             |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 10: Fixed-Sell Multi-Pass Closures (Steps 720..1009)                    |
|   - 41 sequential closure passes applying _s793_reorder                       |
|   - Compares action keys; moves sales ahead of spend turns without lockouts   |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 9: Endgame Asset Preemption & Tail Move Wrappers (Steps 928..953)       |
|   - Move tail crop sales before first spend (_S951)                           |
|   - Move day-high animal sales before first spend (_S953)                     |
|   - Merge day-high animal sales into same-item order (_S952)                  |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 8: Fixed Anchor Orbit Agents (_S834, _S836, _S837)                      |
|   - Terminal cycles and orbit step adjustments (steps 711..717)               |
|   - Fertilizer salvage and care-to-fertilizer optimization                    |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 7: Market Order Microstructure & Lead Sell (_S758, _S752, _S730)        |
|   - ModelPX lead sell: executes front-running sales against opponent queue    |
|   - Guarded same-side market compacting                                       |
|   - Queue compacting: removes empty slot holes                                |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 6: Seed Float Trim (_S731)                                              |
|   - Computes exact future planting requirements (w_ahead, c_ahead)            |
|   - Automatically trims BUY_SEED CARROT and BUY_SEED WHEAT orders             |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 5: Herd / Animal Controller (_V233 sheep worker, _V234 rescue)          |
|   - Compact 6-target sheep feeding, wool harvest, fertilizer collection       |
|   - v24 stranded rescue fix: requires nonzero PICKUP WHEAT quantity           |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 4: Opening Controller: Dmitrii Gluzdov HybridOpening (_ALT_INSTALL)     |
|   - Reassigns idle workers on days 0..3                                       |
|   - Day 0 (turn 5): plants WHEAT on (2,4) pasture site; waters turn 6         |
|   - Day 1 (turn 29): waters instead of building early pasture                 |
|   - Day 2 (turn 52): waters; matures temporary wheat extra day                |
|   - Day 3 (turn 84..91): waters, harvests 10 wheat, restores pasture, drops   |
|   - Extra +3 WHEAT delivered to shed on Day 3 without delaying animal pens    |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 3: Strategic Route Tape & Town Shop Router                              |
|   - Base 2945 route tapes (routes 0, 100, 105, etc.)                          |
|   - Evaluates unlocked town shops at step 144                                 |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 2: Chassis Environment Adapter                                          |
|   - Simulates internal farm view, forward projection, pending command queues  |
+-------------------------------------------------------------------------------+
                                        |
+-------------------------------------------------------------------------------+
| Layer 1: Config Settings (_SETTINGS in v24 vs v27)                            |
|   - v24: room_guard=True, dead_stock=True                                     |
|   - v27: room_guard=False, dead_stock=False                                   |
|   - room_guard: prevents shed overflow deletion at hour 23                    |
|   - dead_stock: liquidates surplus inventory unreachable by route             |
+-------------------------------------------------------------------------------+
```

---

## 2. Layer-by-Layer Evaluation

### Layer 1: Settings (`_SETTINGS`)
- **v24**: `{'hand_align': True, 'weed_repair': True, 'sell_lead': True, 'budget_guard': False, 'room_guard': True, 'clamp_sells': False, 'dead_stock': True, 'terminal_liquidation': False, 'front_run': False}`
- **v27**: `{'hand_align': True, 'weed_repair': True, 'sell_lead': True, 'budget_guard': False, 'room_guard': False, 'clamp_sells': False, 'dead_stock': False, 'terminal_liquidation': False, 'front_run': False}`
- **Empirical Finding**: Ablating `room_guard` and `dead_stock` in v24 reduced mean cash by 55.2 cash per game. `room_guard` actively fired 6 times per game preventing end-of-day shed destruction. `dead_stock` successfully monetized excess yield.
- **Verdict**: **RETAIN v24 SETTINGS (`room_guard=True, dead_stock=True`)**.

### Layer 4: Dmitrii Gluzdov HybridOpening & Wheat Maturation
- **Code**: `_alt_install('HybridOpening')` & `_CL_INSTALL` (lines 6471–6620).
- **Mechanism**: Idle hands 0, 1, and 2 in turns 0–91 are diverted to plant, water, mature, and harvest an extra wheat crop on the (2,4) pasture before the pasture is legally required.
- **Empirical Finding**: Provides 3 extra wheat in the shed at turn 91. This jumpstarts capital accumulation: leads by +29 cash at turn 216, +543 cash at turn 500, +1,028 cash at turn 600, and +2,226 cash at turn 718.
- **Verdict**: **ESSENTIAL CORE ALPHA (RETAIN)**.

### Layer 5: Sheep Worker Controller & Rescue (`_v233_worker`, `_v234_rescue`)
- **Bug in v27**: `if command==['FEED'] or command[:2]==['PICKUP','WHEAT']: return action`
  - When shed wheat = 0, worker attempts `['PICKUP', 'WHEAT', 0]`.
  - v27 treats this as "handled" and loops forever, starving sheep.
- **Fix in v24**: `if command==['FEED'] or (command[:2]==['PICKUP','WHEAT'] and len(command)>2 and command[2]>0): return action`
  - Correctly detects 0 wheat pickup and invokes `_v234_rescue` to buy emergency wheat feed.
- **Verdict**: **CRITICAL BUGFIX (RETAIN v24 LOGIC)**.

### Layer 6: Seed Float Trim (`step731_seed_float_trim_agent`)
- **Mechanism**: Analyzes remaining plant steps in the active route tape (`w_ahead`, `c_ahead`) and trims `BUY_SEED` orders to exact requirements.
- **Empirical Finding**: Completely supersedes V49's external E402 seed-cap wrapper. Active across all games; trims excess seed capital.
- **Verdict**: **RETAIN**.

### Layer 11: PET_CAFE Demand Margin Tilt (`pet_any_demand_agent`)
- **Mechanism**: When `10 <= day <= 23` and `PET_CAFE` is unlocked, adjusts `_CA_MARGIN = -30.0` (from `-15.0`).
- **Empirical Finding**: Ablating PET tilt in v24 reduced head-to-head win rate against v27 from 7/8 (87.5%) to 5/8 (62.5%), and reduced mean reward.
- **Verdict**: **RETAIN**.

### Layer 12: Production Safety Wrapper
- **Mechanism**: Outer exception catching, deep copying, guaranteeing `farmer`, `hands`, and `market[:10]`.
- **Verdict**: **RETAIN**.
