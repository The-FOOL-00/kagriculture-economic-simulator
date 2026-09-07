import sys, os
sys.path.insert(0, os.path.abspath('.'))
import json
import candidates.slot2_aethel_refined_v2 as v2_mod

def build_adaptation_map():
    trace = v2_mod._TRACE
    print("================================================================================")
    print("PHASE 3: V2 720-TURN ADAPTATION OPPORTUNITY MAP ANALYSIS")
    print("================================================================================")
    print(f"Total steps in V2 trace: {len(trace)}")
    
    # Major phases in Kaggriculture:
    # Phase 1: Turns 0-23 (Day 0: Setup, hiring, opening crop planting, wild wheat harvest)
    # Phase 2: Turns 24-95 (Days 1-3: Early crop watering, livestock pen build, animal purchase)
    # Phase 3: Turns 96-239 (Days 4-9: Strawberry maturation & repeat harvest, melon growth)
    # Phase 4: Turns 240-287 (Days 10-11: Melon maturation window watering & yield maximization)
    # Phase 5: Turns 288-359 (Days 12-14: Melon harvest, strawberry cycle 2, wool/milk generation)
    # Phase 6: Turns 360-479 (Days 15-19: Mid-season livestock care, second crop wave)
    # Phase 7: Turns 480-679 (Days 20-28: Livestock volume accumulation, bulk milk/wool buffering)
    # Phase 8: Turns 680-711 (Days 28-29: Pre-terminal inventory liquidation, market dumping)
    # Phase 9: Turns 712-719 (Day 29: Final 8-turn observation-driven terminal controller)

    phases = [
        {
            "name": "Phase 1: Day 0 Setup & Infrastructure",
            "turn_range": "0 - 23",
            "key_actions": "Hire 5 farm hands, buy land, plant initial melon/strawberry, harvest wild wheat",
            "hidden_assumptions": [
                "Starting cash is exactly $2,500 (can afford 5 hires and parcel unlock)",
                "Adjacent tiles have wild wheat intact without weed blockage",
                "Farmer starting position at (0,0) with unobstructed movement"
            ],
            "observable": "YES (obs.players[my_idx].cash, obs.board)",
            "damage_if_wrong": "CATASTROPHIC: If cash < $1,500, hiring fails, leaving 1 worker; subsequent 711 turns collapse (-98.9% loss).",
            "candidate_correction": "Cash-gated hiring: If cash < $1,500, hire only up to max affordable without negative balance; prune chore queue."
        },
        {
            "name": "Phase 2: Days 1-3 Livestock Pen & Acquisition",
            "turn_range": "24 - 95",
            "key_actions": "Build pasture corridor, buy cow and sheep, start feeding",
            "hidden_assumptions": [
                "Cash >= $400 for animals and feed",
                "Fence placement tiles are clear of unexpected obstacles",
                "Animals arrive healthy and feed exists in shed/inventory"
            ],
            "observable": "YES (farm.animals, private.shed, obs.board)",
            "damage_if_wrong": "SEVERE: If animal starved, lose $50k+ in lifetime milk/wool output.",
            "candidate_correction": "Emergency feed override: If animal hunger > 0 and trace does not feed, prioritize immediate feeding."
        },
        {
            "name": "Phase 3: Days 4-9 First Crop Wave & Strawberry Harvest",
            "turn_range": "96 - 239",
            "key_actions": "Water strawberries daily, water melons, harvest cycle 1 strawberries, drop produce in shed",
            "hidden_assumptions": [
                "Strawberry tiles were successfully watered every turn",
                "Crop maturation clock progresses without delay",
                "Worker arrives at shed to DROP produce when inventory is full"
            ],
            "observable": "YES (tile.crop, tile.age, tile.yield_units, worker inventory)",
            "damage_if_wrong": "MODERATE: Full inventory blocks harvesting; missed watering delays crop.",
            "candidate_correction": "Drop-on-full guard: If inventory load == capacity and worker is adjacent to shed, DROP before moving."
        },
        {
            "name": "Phase 4: Days 10-11 Melon Maturation Window",
            "turn_range": "240 - 287",
            "key_actions": "Water all melon tiles during engine maturation window [Days 6-11]",
            "hidden_assumptions": [
                "Melon crops are alive and aged >= 6",
                "Watering actions hit exact melon coordinates"
            ],
            "observable": "YES (tile.crop == 'MELON', tile.age, tile.watered)",
            "damage_if_wrong": "HIGH: Missed watering drops yield from 6 to 1-2 units, losing $14k+.",
            "candidate_correction": "Melon window priority guard: If melon tile is unwatered today, guarantee worker waters it."
        },
        {
            "name": "Phase 5: Days 12-14 Melon Harvest & Secondary Planting",
            "turn_range": "288 - 359",
            "key_actions": "Harvest 6-yield melons on Day 12, reseed strawberry/wheat",
            "hidden_assumptions": [
                "Melon tile yield == 6",
                "Seed inventory has seeds available to replant"
            ],
            "observable": "YES (tile.yield_units, private.shed.seeds)",
            "damage_if_wrong": "MODERATE: Harvesting early forfeits yield; failing to replant loses parcel utilization.",
            "candidate_correction": "Harvest-on-max-yield guard: Trigger harvest only when tile.yield_units reaches max or turns run out."
        },
        {
            "name": "Phase 6: Days 15-19 Mid-Season Livestock Production",
            "turn_range": "360 - 479",
            "key_actions": "Daily milk cow, shear sheep, collect fertilizer, store in shed",
            "hidden_assumptions": [
                "Cow and sheep remain alive and producing",
                "Worker pathing to pasture corridor is unimpeded"
            ],
            "observable": "YES (animal.milk_ready, animal.wool_ready)",
            "damage_if_wrong": "MODERATE: Uncollected milk/wool caps at 1 unit, losing daily compounding yield.",
            "candidate_correction": "Livestock collection check: Collect milk/wool if ready."
        },
        {
            "name": "Phase 7: Days 20-28 Town Market Price Liquidation",
            "turn_range": "480 - 679",
            "key_actions": "Batch sell milk, wool, strawberries according to market schedule",
            "hidden_assumptions": [
                "Town shop price has not crashed due to opponent dumping",
                "Shed contains expected inventory for planned SELL orders"
            ],
            "observable": "YES (obs.market.prices, private.shed)",
            "damage_if_wrong": "HIGH: Selling during opponent price dump forfeits 30-50% unit price ($15k+).",
            "candidate_correction": "Market Price Floor Guard: If shop price < 0.70 * base_price, hold non-perishable inventory until price recovers or turn >= 680."
        },
        {
            "name": "Phase 8: Days 28-29 Pre-Terminal Clearance",
            "turn_range": "680 - 711",
            "key_actions": "Liquidate all shed inventory, prepare workers for field sweep",
            "hidden_assumptions": [
                "Market order queue has available slots",
                "All stored produce is sold before season close"
            ],
            "observable": "YES (private.shed, obs.step)",
            "damage_if_wrong": "HIGH: Unsold inventory has zero terminal value.",
            "candidate_correction": "Terminal sell order sweep: Ensure every sellable item is submitted in market orders."
        },
        {
            "name": "Phase 9: Day 29 Final 8-Turn Dynamic Controller",
            "turn_range": "712 - 719",
            "key_actions": "Dynamic harvest, drop, and sell using V2's built-in _terminal_action",
            "hidden_assumptions": [
                "Already observation-driven in V2!",
                "Finds nearest unharvested crops and brings them to shed"
            ],
            "observable": "YES (Already 100% closed-loop in V2)",
            "damage_if_wrong": "LOW: Already handles dynamic terminal state.",
            "candidate_correction": "Preserve V2's native _terminal_action exactly as designed."
        }
    ]
    
    with open('scratch/v2_adaptation_opportunity_map.json', 'w') as f:
        json.dump(phases, f, indent=2)
        
    print("\nSuccessfully compiled V2 Adaptation Opportunity Map across 9 lifecycle phases.")
    print("Saved to scratch/v2_adaptation_opportunity_map.json")

if __name__ == '__main__':
    build_adaptation_map()
