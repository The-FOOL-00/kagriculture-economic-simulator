# V53 Engine Parity Matrix

## 1. Parity Test Specifications

This matrix evaluates mathematical and behavioral equivalence across all 18 core game mechanics between `kaggle_environments.make("kaggriculture")` and `FastKagricultureSim`:

| Subsystem | Tested Mechanism | Verification Method | Status |
|---|---|---|---|
| **1. Initial State** | Grid dimensions (10x10), starting cash ($3,000), starting seeds (20 wheat, 10 carrot), shed capacity (100) | Observation equality comparison at Step 0 | **VERIFIED (BIT-EXACT)** |
| **2. Shop Generation** | Daily shop unlock schedule (every 24 steps / 1 day) | Compared `unlocked_shops` sequence across 719 steps | **VERIFIED (BIT-EXACT)** |
| **3. Sampling Replacement** | Duplicate shop instances permitted up to 8 max | Verified multi-instance shop consumption logic | **VERIFIED (BIT-EXACT)** |
| **4. Town Center Demand** | Demand consumption every 24 steps for all products | Compared market inventory decrements at multiples of 24 | **VERIFIED (BIT-EXACT)** |
| **5. Shop Demand** | Multiplier = 2 for single-product shops, 1 for multi-product shops every 4 steps | Compared market inventory decrements at multiples of 4 | **VERIFIED (BIT-EXACT)** |
| **6. Market Prices** | Dynamic price formula with saturation clamping | Compared `market["prices"]` across all goods on every turn | **VERIFIED (BIT-EXACT)** |
| **7. Order Processing** | BUY, SELL, BUY_LAND, BUY_ANIMAL, BUILD order validation and execution | Compared cash, inventory, land ownership, and animals | **VERIFIED (BIT-EXACT)** |
| **8. Crop Growth** | Planting, growth stages (WHEAT 12, CARROT 24, MELON 36, STRAWBERRY 48) | Compared tile contents `farm["tiles"]` on every turn | **VERIFIED (BIT-EXACT)** |
| **9. Crop Decay** | Lifespan decay to WEED if unharvested | Tile state monitoring during crop lifecycle | **VERIFIED (BIT-EXACT)** |
| **10. Animal Production** | Milk, Wool, and Egg generation timing | Shed inventory increments on collection turns | **VERIFIED (BIT-EXACT)** |
| **11. Animal Feeding & Care** | Feed consumption, CARE multiplier scaling (1.25x diversity) | Product yield formulas and shed inventory levels | **VERIFIED (BIT-EXACT)** |
| **12. Fertilizer Collection** | Daily fertilizer production from animals | Shed fertilizer inventory and soil fertility tracking | **VERIFIED (BIT-EXACT)** |
| **13. Shed Overflow** | Capacity clamping at 100 units; drop inventory at day end | Day-boundary inventory checks at step % 24 == 0 | **VERIFIED (BIT-EXACT)** |
| **14. Worker Movement** | Cardinal movements, obstacle collisions, boundary checks | Unit `[x, y]` positions for farmer and hands | **VERIFIED (BIT-EXACT)** |
| **15. Hand Hiring** | Max 10 hands, wage deductions, spawn positions | Farm `hands` array and cash deductions | **VERIFIED (BIT-EXACT)** |
| **16. Action Legality** | Atomic PLANT seed check (drops all if insufficient seeds) | Validation of blocked action handling | **VERIFIED (BIT-EXACT)** |
| **17. Route Timing** | Pre-scripted action synchronization over 719 steps | Step counter and action dispatch synchronization | **VERIFIED (BIT-EXACT)** |
| **18. Terminal Scoring** | Final cash liquidation, rewards, episode completion at step 719 | Final `reward` and `status` values | **VERIFIED (BIT-EXACT)** |

---

## 2. Parity Methodology

Because `FastKagricultureSim` directly calls `official_kg.interpreter(self.state, self)`, both harnesses share the exact same underlying Python function implementation. The parity tests confirm that:
1. State representations (`structify` vs standard dicts) do not introduce drift in arithmetic or logic.
2. The lack of JSON serialization in FastSim does not preserve mutable references across steps that would alter decision paths.
3. Observations provided to agents are 100% bit-for-bit identical on every step.
