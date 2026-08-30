"""
=============================================================================
ENGINE: MACRO PORTFOLIO PLANNER & ARBITRAGE EXECUTOR (TITAN APEX V4)
=============================================================================
High-Throughput Harvest Liquidation Pipeline & Dynamic Arbitrage Engine.
Eliminates inventory logjams and maximizes realized harvest cash flow.
=============================================================================
"""

from config import CROPS, ANIMALS, PRODUCTS, LAND_PRICES, fib_hire_cost
from engine.market_model import MarketModel
from engine.town_model import TownDemandModel
from engine.economic_evaluator import EconomicEvaluator
from engine.opponent_model import OpponentModel
from engine.labor_scheduler import LaborScheduler


class MacroPlanner:
    def __init__(self):
        self.market_model = MarketModel()
        self.town_model = TownDemandModel()
        self.evaluator = EconomicEvaluator(self.market_model, self.town_model)
        self.opponent_model = OpponentModel()
        self.labor_scheduler = LaborScheduler()

    def plan_turn(self, world_state):
        day = world_state.day
        hour = world_state.hour
        step = world_state.step
        money = world_state.money

        # 1. Opponent Radar & Supply Monitoring
        opp_analysis = self.opponent_model.analyze_opponent_farm(world_state.opp_tiles, day)
        opp_imminent = opp_analysis["imminent_harvests"]
        opp_crops = opp_analysis["crop_counts"]

        # 2. Extract Chores & Labor Needs
        chores = []
        weed_count = 0
        unwatered_count = 0
        harvestable_count = 0

        board_size = len(world_state.tiles)
        for y in range(board_size):
            for x in range(board_size):
                t = world_state.tiles[y][x]
                pos = (x, y)
                if t is None or t == "LOCKED":
                    continue
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "WEED":
                        chores.append({"type": "DIG", "pos": pos, "weight": 92})
                        weed_count += 1
                    elif kind == "PLANT":
                        crop = t["crop"]
                        age = day - t.get("planted_day", 0)
                        cd = CROPS.get(crop, {})
                        watered = t.get("watered_today", False)
                        yield_units = t.get("yield_units", 0)

                        if not watered:
                            chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            unwatered_count += 1

                        is_harvest = False
                        if cd.get("ongoing", False):
                            if age >= cd["first_yield_day"] and yield_units > 0:
                                is_harvest = True
                        else:
                            if crop == "MELON":
                                if age >= 10 or yield_units >= 6 or (day >= 28 and yield_units >= 1):
                                    is_harvest = True
                            elif crop == "CARROT":
                                if age >= 3 or yield_units >= 3 or (day >= 28 and yield_units >= 1):
                                    is_harvest = True
                            elif crop == "WHEAT":
                                if age >= 4 or yield_units >= 4 or (day >= 28 and yield_units >= 1):
                                    is_harvest = True
                            else:
                                if age >= cd.get("max_yield_day", 4) and yield_units > 0:
                                    is_harvest = True

                        if is_harvest:
                            chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            harvestable_count += 1

        empty_tiles = world_state.get_empty_tiles()
        total_seeds_held = sum(world_state.seeds.values())
        if total_seeds_held > 0 and day <= 26:
            for pos in empty_tiles:
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        total_pending_chores = weed_count + unwatered_count + harvestable_count + len(empty_tiles)

        # 3. Plan Daily Labor Fleet
        planned_hires = self.labor_scheduler.compute_daily_hire_count(world_state, total_pending_chores)

        # 4. Generate Market Orders
        orders = []

        # A. HIRE FARM HANDS at hour 0 (Priority 1)
        if hour == 0 and planned_hires > world_state.hires_today:
            needed = planned_hires - world_state.hires_today
            for _ in range(needed):
                cost = fib_hire_cost(world_state.hires_today + len([o for o in orders if o[0] == "HIRE"]))
                if money >= cost:
                    orders.append(["HIRE"])
                    money -= cost

        # B. DAY-0 50-TILE EXPANSION & SW SCALING
        n_unlocked = len(world_state.unlocked_quadrants) - 1
        if n_unlocked < 2:
            cost = LAND_PRICES[n_unlocked]
            should_buy_land = False
            if n_unlocked == 0 and money >= cost + 250: # NE Land ($1,000)
                should_buy_land = True
            elif n_unlocked == 1 and money >= cost + 500 and day <= 13: # SW Land ($2,000)
                should_buy_land = True
            
            if should_buy_land and len(orders) < 10:
                orders.append(["BUY_LAND"])
                money -= cost

        # Labor Liquidity Protection ($30 reserve)
        RESERVE_CASH = 30.0
        spendable = max(0.0, money - RESERVE_CASH)

        # C. ADAPTIVE CROP PORTFOLIO EVALUATOR
        needed_seeds = max(0, len(empty_tiles) - total_seeds_held)

        if needed_seeds > 0 and day <= 26 and len(orders) < 10 and spendable > 0:
            remaining_days = 29 - day
            opp_melon_flood = opp_crops.get("MELON", 0) >= 16

            portfolio = {}
            if day <= 12 and remaining_days >= 12:
                # Early Season: High-yield Melon Compounding (Proven 65% Melon baseline)
                if opp_melon_flood:
                    melon_c = int(needed_seeds * 0.45)
                    straw_c = int(needed_seeds * 0.25)
                    carrot_c = int(needed_seeds * 0.20)
                    wheat_c = needed_seeds - melon_c - straw_c - carrot_c
                    if melon_c > 0: portfolio["MELON"] = melon_c
                    if straw_c > 0: portfolio["STRAWBERRY"] = straw_c
                    if carrot_c > 0: portfolio["CARROT"] = carrot_c
                    if wheat_c > 0: portfolio["WHEAT"] = wheat_c
                else:
                    melon_c = int(needed_seeds * 0.65)
                    carrot_c = int(needed_seeds * 0.25)
                    wheat_c = needed_seeds - melon_c - carrot_c
                    if melon_c > 0: portfolio["MELON"] = melon_c
                    if carrot_c > 0: portfolio["CARROT"] = carrot_c
                    if wheat_c > 0: portfolio["WHEAT"] = wheat_c

            elif day <= 19 and remaining_days >= 10:
                # Mid Season: Melons (50%) + Carrots (35%) + Wheat (15%)
                melon_c = int(needed_seeds * 0.50)
                carrot_c = int(needed_seeds * 0.35)
                wheat_c = needed_seeds - melon_c - carrot_c
                if melon_c > 0: portfolio["MELON"] = melon_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c

            elif remaining_days >= 3:
                # Late Season: Fast Carrots (75%) + Wheat (25%)
                carrot_c = int(needed_seeds * 0.75)
                wheat_c = needed_seeds - carrot_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c

            for crop, count in portfolio.items():
                if len(orders) >= 10:
                    break
                seed_price = CROPS[crop]["seed"]
                affordable = min(count, int(spendable // seed_price))
                if affordable > 0:
                    orders.append(["BUY_SEED", crop, affordable])
                    spendable -= affordable * seed_price
                    money -= affordable * seed_price

        # D. HIGH-THROUGHPUT HARVEST LIQUIDATION PIPELINE (Zero Inventory Choke)
        is_scarcity_window = self.town_model.is_post_consumption_window(step)

        sell_priority = ["MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "TOMATO", "EGG", "CARROT", "WHEAT"]
        for prod in sell_priority:
            if len(orders) >= 10:
                break
            qty = world_state.shed.get(prod, 0)
            if qty > 0:
                cur_p = world_state.market_prices.get(prod, 1)
                opp_frontrun = self.opponent_model.should_frontrun_opponent(prod, opp_imminent.get(prod, 0))

                should_sell = False
                if day >= 26 or sum(world_state.shed.values()) >= 25:
                    should_sell = True
                elif opp_frontrun:
                    should_sell = True
                elif is_scarcity_window and cur_p > 1:
                    should_sell = True
                elif cur_p > 1:
                    should_sell = True

                if should_sell:
                    # High-throughput liquidation batch: 12-16 units per turn
                    sell_amount = min(qty, 14) if day < 26 else qty
                    orders.append(["SELL", prod, sell_amount])

        # 5. Assign Worker Actions
        worker_actions = self.labor_scheduler.assign_worker_actions(world_state, chores)

        return {
            "farmer": worker_actions.get("farmer", ["PASS"]),
            "hands": worker_actions.get("hands", []),
            "market": orders[:10]
        }
