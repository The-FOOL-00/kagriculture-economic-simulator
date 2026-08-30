"""
=============================================================================
ENGINE: MACRO PORTFOLIO PLANNER (CORRECTED & UNIFIED)
=============================================================================
Orchestrates:
1. Opponent model & market monitoring
2. Livestock procurement, feeding & pasture logistics
3. Dynamic economic crop allocation
4. Elasticity-aware market liquidation
5. Labor hiring & spatial dispatch
=============================================================================
"""

from config import CROPS, ANIMALS, PRODUCTS, LAND_PRICES, fib_hire_cost
from engine.market_model import MarketModel
from engine.town_model import TownDemandModel
from engine.economic_evaluator import EconomicEvaluator
from engine.opponent_model import OpponentModel
from engine.livestock_engine import LivestockEngine
from engine.dynamic_allocator import DynamicEconomicAllocator
from engine.market_executor import MarketExecutor
from engine.labor_scheduler import LaborScheduler


class MacroPlanner:
    def __init__(self, target_cows=6, target_sheep=3, target_geese=0, target_melons=10, cycle2_melons=0, sell_batch=14, use_fert=False, care_animals=True, town_sync=True):
        self.market_model = MarketModel()
        self.town_model = TownDemandModel()
        self.evaluator = EconomicEvaluator(self.market_model, self.town_model)
        self.opponent_model = OpponentModel()
        self.livestock_engine = LivestockEngine(target_cows=target_cows, target_sheep=target_sheep, target_geese=target_geese, care_animals=care_animals)
        self.allocator = DynamicEconomicAllocator(default_melon_target=target_melons, max_cycle2_melons=cycle2_melons)
        self.market_executor = MarketExecutor(base_batch_size=sell_batch, town_sync=town_sync)
        self.labor_scheduler = LaborScheduler()
        self.use_fert_on_crops = use_fert
        self.care_animals = care_animals

    def plan_turn(self, world_state):
        day = world_state.day
        hour = world_state.hour
        step = world_state.step
        money = world_state.money

        # 1. Opponent Analysis
        opp_analysis = self.opponent_model.analyze_opponent_farm(world_state.opp_tiles, day)
        opp_crops = opp_analysis["crop_counts"]

        # 2. Livestock State Analysis
        live_state = self.livestock_engine.analyze_livestock_state(world_state.tiles, world_state.shed, world_state.inventories)
        unfed_animal_tiles = live_state["unfed_animal_tiles"]

        # 3. Chores Extraction
        chores = list(live_state["chores"])
        empty_tiles = world_state.get_empty_tiles()
        melon_plants = 0

        board_size = len(world_state.tiles)
        for y in range(board_size):
            for x in range(board_size):
                t = world_state.tiles[y][x]
                pos = (x, y)
                if not isinstance(t, dict):
                    continue
                kind = t.get("kind")
                if kind == "WEED":
                    chores.append({"type": "DIG", "pos": pos, "weight": 95})
                elif kind == "PLANT":
                    crop = t.get("crop")
                    if crop == "MELON": melon_plants += 1
                    age = day - t.get("planted_day", 0)
                    cd = CROPS.get(crop, {})
                    if not t.get("watered_today", False):
                        chores.append({"type": "WATER", "pos": pos, "weight": 82})
                    if self.use_fert_on_crops and t.get("fertilized_until_day", -1) < day and crop == "MELON":
                        chores.append({"type": "FERTILIZE", "pos": pos, "weight": 78})

                    is_harvest = False
                    if cd.get("ongoing", False):
                        if age >= cd["first_yield_day"] and t.get("yield_units", 0) > 0:
                            is_harvest = True
                    else:
                        if crop == "MELON" and (age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                            is_harvest = True
                        elif crop == "CARROT" and (age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                            is_harvest = True
                        elif crop == "WHEAT" and (age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                            is_harvest = True
                        elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                            is_harvest = True

                    if is_harvest:
                        chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

        if sum(world_state.seeds.values()) > 0 and day <= 26:
            for pos in empty_tiles:
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        # 4. Labor Scheduling (Hire farm hands at hour 0)
        total_pending = len(chores) + len(empty_tiles)
        target_hands = self.labor_scheduler.compute_daily_hire_count(world_state, total_pending)

        orders = []
        if hour == 0 and target_hands > world_state.hires_today:
            for _ in range(target_hands - world_state.hires_today):
                cost = fib_hire_cost(world_state.hires_today + len([o for o in orders if o[0] == "HIRE"]))
                if money >= cost + 10:
                    orders.append(["HIRE"])
                    money -= cost

        # 5. Land Expansion
        n_unlocked = len(world_state.unlocked_quadrants) - 1
        if n_unlocked < 2:
            cost = LAND_PRICES[n_unlocked]
            if n_unlocked == 0 and money >= cost + 250:
                orders.append(["BUY_LAND"])
                money -= cost
            elif n_unlocked == 1 and money >= cost + 500 and day <= 14:
                orders.append(["BUY_LAND"])
                money -= cost

        spendable = max(0.0, money - 25.0)

        # 6. Buy Animals with Mandatory Feed Protection
        live_orders, spendable, money = self.livestock_engine.generate_market_orders(
            live_state, money, spendable, day, orders
        )
        orders.extend(live_orders)

        # 7. Wheat Feed Buffer
        feed_orders, spendable = self.livestock_engine.check_wheat_feed_reserve(
            live_state, world_state.shed, world_state.inventories, spendable, day, orders
        )
        orders.extend(feed_orders)

        # 8. Seed Purchases
        seed_orders, spendable = self.allocator.allocate_seeds(
            len(empty_tiles), world_state.seeds, melon_plants, spendable, day,
            world_state.market_prices, world_state.market_inv, opp_crops
        )
        orders.extend(seed_orders)

        # 9. Selling / Liquidation
        total_active_animals = live_state["total_active_animals"] + live_state.get("cows_ordered", 0) + live_state.get("sheep_ordered", 0)
        feed_reserve = total_active_animals * 4 if day < 26 else 0
        sell_orders = self.market_executor.generate_sell_orders(
            world_state.shed, world_state.market_prices, world_state.market_inv,
            day, step, feed_reserve=feed_reserve, current_orders=orders
        )
        orders.extend(sell_orders)

        # 10. Worker Dispatch
        unplaced_pasture_animals = live_state["cows_in_transit"] + live_state["sheep_in_transit"] + live_state.get("cows_ordered", 0) + live_state.get("sheep_ordered", 0)
        pastures_to_build = max(0, min(self.livestock_engine.target_cows + self.livestock_engine.target_sheep - live_state["pasture_count"], unplaced_pasture_animals - len(live_state["empty_pastures"])))
        
        unplaced_geese = live_state["geese_in_transit"] + live_state.get("geese_ordered", 0)
        coops_to_build = max(0, min(self.livestock_engine.target_geese - live_state["coop_count"], unplaced_geese - len(live_state["empty_coops"])))

        structs = {"pastures": pastures_to_build, "coops": coops_to_build}

        worker_actions = self.labor_scheduler.assign_worker_actions(
            world_state, chores, structures_to_build=structs, unfed_animal_tiles=unfed_animal_tiles,
            care_animals=self.care_animals, use_fert_on_crops=self.use_fert_on_crops
        )

        return {
            "farmer": worker_actions["farmer"],
            "hands": worker_actions["hands"],
            "market": orders[:10]
        }
