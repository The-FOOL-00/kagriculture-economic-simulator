# V49 — Elite Gap Matrix & Missing Mechanism Taxonomy

## 1. Cross-Architecture Feature Comparison

| Capability / Mechanism | 2945 Baseline | V48 Challenger | abhinav_cha22 | arsgorynich_herdsafe_v3 | statma_ca25 | kaitofukami_3009 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Engine Core** | Chassis Tape | Chassis Tape | Chassis Tape | Chassis Tape | Custom | Static Tape |
| **Step-144 Router** | Static 41 | Selective Route 105 | Static 41 | Static 41 | Heuristic | Fixed Route |
| **Rival Harvest Tracking (`ORDERPRI2`)** | YES | YES | YES | YES | Partial | NO |
| **Terminal Sweeps (Route 2)** | YES | YES | YES | YES | Custom | NO |
| **Late Seed Cap (`E402`)** | **NO** | **NO** | **YES** | **YES** | NO | NO |
| **SELL Compaction (`MG`)** | **NO** | **NO** | **YES** | **YES** | NO | NO |
| **Queue Hole Closure (`IG`)** | **NO** | **NO** | **YES** | **YES** | NO | NO |
| **Shop Herd Swapping (`V44Y`)** | **NO** | **NO** | **YES** | **YES** | NO | NO |
| **Tomato Price Gating (`Counter T-B`)**| **NO** | **NO** | NO | **YES** | NO | NO |
| **Best-Response Market Ordering (`Counter D`)** | NO | NO | **YES** | **YES** | NO | NO |

---

## 2. Top Candidate Missing Mechanisms Identified for V49

1. **Mechanism M1: `E402` Late Seed Cap (Step $\ge 624$)**
   - **Hypothesis**: The tape continues to issue `BUY_SEED` orders for wheat and carrots during late steps (days 26–29) even when there are fewer planting steps left than seeds in inventory.
   - **Action**: Clamp `BUY_SEED` orders to `remaining_plants - inventory_seeds`.
   - **Predicted Gain**: Zero risk, pure cash savings from preventing dead inventory (+100 to +300 coins per match).

2. **Mechanism M2: `MG` Same-Item SELL Compaction**
   - **Hypothesis**: When multiple layers generate SELL orders for the same commodity on the same step, they consume separate slots in the 10-order market limit.
   - **Action**: Merge duplicate commodity orders into a single order with summed quantity.
   - **Predicted Gain**: Frees up slots for other products or animal purchases.

3. **Mechanism M3: `IG` Queue Hole-Closure**
   - **Hypothesis**: Zero-quantity orders leave holes in the market queue that can block downstream orders.
   - **Action**: Filter zero-quantity orders and pull active orders forward into contiguous leading slots.
   - **Predicted Gain**: Improves market execution reliability.

4. **Mechanism M4: `Counter D` Cash-Flow Priority Ordering**
   - **Hypothesis**: In turns where the agent both sells products and makes purchases (`HIRE`, `BUY_SEED`, `BUY_ANIMAL`), placing SELLs ahead of purchases provides immediate cash liquidity, preventing failed purchases or cash insolvency.
   - **Action**: Permute SELL orders before fixed-price purchases.
   - **Predicted Gain**: Eliminates execution stalls due to temporary liquidity shortfalls.

5. **Mechanism M5: `V44Y` Days 8–11 Shop Herd Adaptation**
   - **Hypothesis**: At days 8–11 (steps 192–264), revealed shops indicate whether `YARN_STORE` exists. Converting cows or geese to sheep under yarn demand maximizes textile revenue.
   - **Action**: Conditionally switch animal purchase type based on confirmed town shop unlock.
   - **Predicted Gain**: Exploits yarn market premium when supported by town demand.

6. **Mechanism M6: `Counter T-B` Tomato Price Gating**
   - **Hypothesis**: Planting tomatoes when market inventory is saturated ($\ge 10,200$) collapses margins.
   - **Action**: Gate tomato seeding based on projected market inventory and clearing price.
   - **Predicted Gain**: Avoids catastrophic agricultural losses in flooded regimes.
