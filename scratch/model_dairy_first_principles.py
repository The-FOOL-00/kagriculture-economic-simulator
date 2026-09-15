import json
import os
import sys

def model_dairy_first_principles():
    print("=" * 75)
    print("STEP 2 & 3: MATHEMATICAL MODELING OF DAIRY WORLD FROM FIRST PRINCIPLES")
    print("Target World: SMOOTHIE_SHOP + ICE_CREAM_SHOP (Revealed at Step 144 / Day 6)")
    print("=" * 75)
    
    # 1. Town Absorption Capacity
    # Remaining steps from step 144: 720 - 144 = 576 steps.
    # Town consumption occurs every 4 steps (steps 148, 152, ..., 716) = 144 pulses.
    # SMOOTHIE_SHOP consumes: 1 STRAWBERRY, 1 MILK per pulse.
    # ICE_CREAM_SHOP consumes: 1 STRAWBERRY, 1 MILK, 1 WHEAT per pulse.
    # Combined per pulse: 2 STRAWBERRY, 2 MILK, 1 WHEAT.
    # Total pulses = 144 pulses over Days 6-29 (24 days).
    
    pulses = 144
    demand = {
        "STRAWBERRY": 2 * pulses, # 288 units
        "MILK":       2 * pulses, # 288 units
        "WHEAT":      1 * pulses, # 144 units
        "WOOL":       0,          # 0 units!
        "EGG":        0,          # 0 units!
        "CARROT":     0,          # 0 units!
        "TOMATO":     0,          # 0 units!
    }
    
    base_prices = {"STRAWBERRY": 120, "MILK": 160, "WHEAT": 25, "WOOL": 200, "FERTILIZER": 100}
    
    print("\n--- 1. TOWN DEMAND OVER REMAINING 24 DAYS (Days 6–29) ---")
    total_absorption_dollars = 0
    for item, qty in demand.items():
        val = qty * base_prices.get(item, 0)
        total_absorption_dollars += val
        daily = qty / 24.0
        print(f"  {item:12}: {qty:4d} units ({daily:4.1f} units/day) | Base Rev: ${val:7,d}")
    print(f"Total Town Absorption Capacity: ${total_absorption_dollars:,.2f}")
    
    # 2. Production Requirements
    # To satisfy 288 MILK over 24 days:
    # A Cow yields MILK every 2 days (yield = 1 unit base, +bonus if cared).
    # If cared daily:
    # Day t (feed + care) -> pending_care_bonus = 1.
    # Day t+1 (yield day, feed + care) -> yields 1 + 1 = 2 units of Milk!
    # A cared cow yields 2 Milk every 2 days = 1 Milk per cow per day!
    # Therefore, 12 cows cared daily yield 12 Milk per day = exactly 288 Milk over 24 days!
    # If uncared (fed only): 1 cow yields 1 Milk every 2 days = 0.5 Milk/day -> needs 24 cows.
    
    print("\n--- 2. COW PRODUCTION DYNAMICS (Cared vs Uncared) ---")
    print("  Cow Feed Interval:  Every 2 days (consumes 1 Wheat feed per 2 days = 0.5 Wheat/cow/day)")
    print("  Cow Yield Interval: Every 2 days")
    print("  Uncared Cow Yield:  1 Milk every 2 days (0.5 Milk/day) | Feed cost: 1 Wheat ($25) per 2 Milk ($320)")
    print("  Cared Cow Yield:    2 Milk every 2 days (1.0 Milk/day) | Feed cost: 1 Wheat ($25) per 2 Milk ($320)")
    print("  Net Value/day/cared cow: $160 (Milk) + $100 (Manure) - $12.50 (Wheat feed) = $247.50 / cow / day!")
    print("  Net Value/day/uncared cow: $80 (Milk) + $100 (Manure) - $12.50 (Wheat feed) = $167.50 / cow / day!")
    
    # 3. Fertilizer & Manure Invariant
    # 33 Strawberry plants fruit every 2 days for 20 days.
    # To keep 33 plants continuously fertilized (fertilizer lasts 2 days):
    # Daily fertilizer needed = 33 / 2 = 16.5 units of fertilizer/day.
    # Total fertilizer needed over 20 fruiting days = ~330 units.
    # Each animal (Cow or Sheep or Goose) produces 1 manure/fertilizer per day.
    # To generate 16.5 fertilizer per day:
    # We need >= 16 animals on the farm!
    # In Window 0, Dmitrii has: 4 Cows + 2 Sheep = 6 animals on Day 5.
    # To reach 16+ animals:
    # On Day 6-8: Buy 6-8 additional Cows (bringing herd to 10-12 Cows + 2 Sheep = 14-16 animals).
    # Those 16 animals produce 16 fertilizer every single day, exactly matching strawberry requirements!
    
    print("\n--- 3. THE MANURE / FERTILIZER INVARIANT ---")
    print("  Strawberry Plants:       33 plants")
    print("  Fertilizer Duration:     2 days per application (bonus = 2 units vs 1 unfertilized)")
    print("  Daily Fertilizer Demand: 33 / 2 = 16.5 units / day")
    print("  Animal Manure Yield:     1.0 Fertilizer / animal / day")
    print("  Required Animals:        >= 14–16 animals")
    print("  Window 0 Baseline:       4 Cows + 2 Sheep = 6 animals")
    print("  Required New Animals:    Buy +8–10 Cows across Days 6, 7, 8")
    
    # 4. Escape Mechanics & Feeding Synchronization
    # sim.hpp Line 785-790:
    # t.consecutive_dry = t.fed_today ? 0 : t.consecutive_dry + 1;
    # if (t.consecutive_dry >= 2) -> ANIMAL ESCAPES!
    # Therefore, Cow MUST be fed at least once every 2 days (never 2 consecutive unfed days).
    # Ideal feeding schedule:
    # Feed on Even Days (Day 6, Day 8, Day 10, Day 12, Day 14, Day 16, Day 18, Day 20, Day 22, Day 24, Day 26, Day 28).
    # On Even Days, consecutive_dry resets to 0.
    # On Odd Days, consecutive_dry becomes 1.
    # Animal NEVER reaches consecutive_dry == 2! Zero escapes!
    
    print("\n--- 4. SYNCHRONIZED 2-DAY COW CHOREOGRAPHY ---")
    print("  Feeding Schedule:        Every Even Day (Days 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28)")
    print("  Feeding Turn:            Turn 1–4 of each Even Day (before morning chores)")
    print("  Max Consecutive Unfed:   1 (escapes occur at >= 2 -> ZERO ESCAPES)")
    print("  Milk Collection:         Every Even Day (end of day transition yields milk into pasture tile)")
    print("  Manure Collection:       Every Day (collected by dedicated morning hand)")
    
    # 5. Labor & Farmhand Allocation
    # At Step 144, hiring 8–10 hands:
    # Hand 1: Dedicated Manure Collector (sweeps 14 pastures, drops fertilizer into shed)
    # Hand 2: Strawberry Waterer (Quadrant NW)
    # Hand 3: Strawberry Waterer (Quadrant NE)
    # Hand 4: Strawberry Harvester / Planter
    # Hand 5: Cow Feeder (Even Days: feeds 12 cows; Odd Days: assists watering/weeding)
    # Hand 6: Cow Milker (Even Days: collects 24 milk, drops to shed)
    # Hand 7–8: Field expansion / melon harvest / quadrant clearing
    
    print("\n--- 5. OPTIMAL LABOR ALLOCATION (8–10 Hands) ---")
    print("  Hand 1: Manure Sweeper (daily collection from 14 animal tiles)")
    print("  Hand 2–3: Strawberry Irrigation (33 tiles)")
    print("  Hand 4: Strawberry Harvesting (every 2 days)")
    print("  Hand 5: Cow Feeding Loop (Even Days)")
    print("  Hand 6: Milk Pickup & Shed Logistics (Even Days)")
    print("  Farmer: Market purchases (Wheat feed, seeds) & emergency repairs")

if __name__ == "__main__":
    model_dairy_first_principles()
