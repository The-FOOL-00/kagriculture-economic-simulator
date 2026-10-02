# V55 Causal Branch Timing Analysis

## Executive Summary

This report analyzes the causal branch timing for post-reveal shop-regime continuation policies.
We evaluated candidate interventions across a spectrum of decision points surrounding the third town shop unlock (Shop #3):
1. **Pre-reveal** (Step 215 — Hour 23, Day 8): Before Shop #3 appears in `observation.town["unlocked_shops"]`.
2. **Reveal Callback** (Step 216 — Hour 0, Day 9): Exact step when Shop #3 first appears.
3. **One Turn Post-Reveal** (Step 217 — Hour 1, Day 9): First turn with updated engine state after reveal.
4. **First Demand Tick** (Step 220 — Hour 4, Day 9): First step where Shop #3 executes consumption (`step % 4 == 0`).
5. **Market Response Lag** (Step 240 — Hour 0, Day 10): 24 turns of consumption and price adjustment.
6. **Next Reveal Boundary** (Step 288 — Hour 0, Day 12): Unlock of Shop #4.

---

## 1. Causal Branch Table

The table below summarizes the causal impact of activating the demand-aware sale timing continuation policy (`B_DEMAND_SALE_TIMING_120`) across the critical test pair `(250416, 250436)` and negative control `250439`:

| Branch Point | Step / Hour | Information Available to Agent | 250436 Delta (Target) | 250416 Delta (Control) | 250439 Delta (Negative Control) | False Positive Casualty | Gate Verdict |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Pre-Reveal** | Step 215 (H23) | None about future shop (Identical states) | +$627.00 | **-$30,569.00** | +$541.00 | **YES (Catastrophic)** | **REJECTED (Leakage)** |
| **Reveal Callback** | Step 216 (H0) | `PIZZA_SHOP` visible in `unlocked_shops` | +$627.00 | **-$30,569.00** | +$541.00 | **YES (Catastrophic)** | **REJECTED (Unsafe)** |
| **One Turn Post** | Step 217 (H1) | Shop identity confirmed | +$627.00 | **-$30,569.00** | +$541.00 | **YES (Catastrophic)** | **REJECTED (Unsafe)** |
| **First Demand Tick**| Step 220 (H4) | Shop + realized initial demand | +$627.00 | **-$30,569.00** | +$541.00 | **YES (Catastrophic)** | **REJECTED (Unsafe)** |
| **Market Response** | Step 240 (H0) | Realized market inventory drop | +$627.00 | **-$30,569.00** | +$541.00 | **YES (Catastrophic)** | **REJECTED (Unsafe)** |
| **Late Reveal** | Step 288 (H0) | Shop #4 visible | +$589.00 | **-$30,569.00** | +$503.00 | **YES (Catastrophic)** | **REJECTED (Unsafe)** |

---

## 2. In-Depth Causal Attribution

### 2.1 Why Does Every Branch Point Suffer the Exact Same False-Positive Loss on 250416?
In Seed 250416, Shop #3 at Step 216 is `PET_CAFE` (not a dairy shop).
However, at Step 288, Seed 250416 rolls a dairy-consuming shop (`SMOOTHIE_SHOP`).
Regardless of whether the continuation policy branches at Step 216, 220, 240, or 288:
* As soon as a dairy shop appears in `unlocked_shops` on Seed 250416, the policy triggers milk withholding.
* Because the market price of milk on 250416 stays below the $120 withholding threshold, milk accumulates in the shed.
* Shed occupancy reaches 100/100 items around Step 380.
* For the remaining 338 turns of the game, every crop harvest (melons, strawberries, wheat) attempted by field workers is deleted by the official engine:
  ```python
  room = max(0, shed_capacity - sum(shed.values()))
  take = min(n, room)  # take == 0
  if take > 0:
      shed[item] = shed.get(item, 0) + take
  del inv[item]  # Crop destroyed!
  ```
* Total destroyed inventory exceeds $30,000 in value, converting an incumbent margin of -$716 into a catastrophic -$31,285 disaster.

### 2.2 Why Realized Demand Does Not Solve the Problem
Waiting for the first consumption tick (Step 220) or market price response (Step 240) provides no additional discriminative power:
* In both worlds, once a milk shop is unlocked, consumption occurs every 4 steps.
* The rate of consumption is identical (1 unit per 4 steps).
* The difference between 250436 (where milk withholding yields modest gains) and 250416 (where it causes utter destruction) is NOT the shop consumption rate — it is the **total macro-market supply equilibrium** determined by whether the opponent also produces milk.
* Realized market price cannot predict future shed saturation until it is already too late to avoid crop deletion.

---

## 3. Continuation Families Summary Table

Evaluated on Critical Seeds at legal Step 216 reveal:

| Family | Mechanism Tested | Target Gain (250436) | Target Gain (250439) | Control Loss (250416) | Net Delta Sum | Gate Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **A. Control** | Pure V49 Incumbent | $0.00 | $0.00 | $0.00 | $0.00 | **SOVEREIGN BASELINE** |
| **B. Demand Timing (120)** | Withhold milk if price < $120 | +$627.00 | +$541.00 | **-$30,569.00** | -$29,401.00 | **REJECTED (Catastrophic)** |
| **B. Demand Timing (140)** | Withhold milk if price < $140 | +$1,641.00 | +$854.00 | **-$31,123.00** | -$28,628.00 | **REJECTED (Catastrophic)** |
| **C. Production Emphasis** | Buy cow at Step 216 if shop seen | -$411.00 | -$455.00 | $0.00 | -$866.00 | **REJECTED (Negative Delta)** |
| **D. Inventory Protection**| Keep 3 milk in shed | $0.00 | $0.00 | $0.00 | $0.00 | **INACTIVE (0 delta)** |

---

## 4. Scientific Conclusion

There is **no viable legal branch point**.
* Pre-reveal branching violates physics and causal law (temporal leakage).
* Post-reveal branching triggers catastrophic false-positive casualties on valid seeds due to the engine's hard shed capacity constraint.
* V49's baseline policy of selling milk immediately upon delivery avoids the shed capacity trap entirely, maximizing net economic output.
