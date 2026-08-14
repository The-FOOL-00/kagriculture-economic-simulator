"""
Adaptive Economic & Competitor Intelligence Engine.
"""

from config import (
    CROPS, ANIMALS, PRODUCTS, SHOPS, LAND_PRICES,
    compute_market_price, fib_hire_cost
)


class EconomyManager:
    def __init__(self):
        pass

    def get_shop_demands(self, farm_state):
        """Aggregate town shop demand per product."""
        shop_demand = {p: 0 for p in PRODUCTS}
        for shop in farm_state.unlocked_shops:
            prods = SHOPS.get(shop, [])
            mult = 2 if len(prods) == 1 else 1
            for p in prods:
                shop_demand[p] += mult
        return shop_demand

    def count_opponent_crops(self, farm_state):
        """Count opponent's current crop and animal footprint."""
        counts = {p: 0 for p in PRODUCTS}
        opp_tiles = farm_state.opp_farm.get("tiles", [])
        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        crop = t.get("crop")
                        if crop in counts:
                            counts[crop] += 1
                    elif "animal" in t and t.get("animal"):
                        animal = t.get("animal")
                        if animal == "GOOSE": counts["EGG"] += 1
                        elif animal == "COW": counts["MILK"] += 1
                        elif animal == "SHEEP": counts["WOOL"] += 1
        return counts

    def evaluate_crop_demands(self, farm_state):
        """
        Assess current and forecasted market price / demand for each crop,
        accounting for opponent production and town shop demand.
        """
        scores = {}
        day = farm_state.day
        remaining_days = 29 - day
        shop_demand = self.get_shop_demands(farm_state)
        opp_counts = self.count_opponent_crops(farm_state)

        for crop, cdata in CROPS.items():
            seed_cost = cdata["seed"]
            current_price = farm_state.market_prices.get(crop, cdata.get("base_yield", 1) * 25)
            market_inv = farm_state.market_inv.get(crop, 10000)
            
            # Scarcity factor: higher score if market inventory is depleted below 10,000
            scarcity_bonus = max(0, (10000 - market_inv) * 0.05)
            # Competitor penalty: reduce score if opponent is heavily flooding this crop
            opp_penalty = opp_counts.get(crop, 0) * 1.2

            if not cdata["ongoing"]:
                min_days = cdata["first_yield_day"]
                opt_days = cdata["max_yield_day"]
                if remaining_days < min_days:
                    scores[crop] = -9999
                    continue
                
                if remaining_days >= opt_days:
                    expected_yield = cdata["max_yield"] if crop == "MELON" else (cdata["base_yield"] + 1)
                    growth_days = opt_days
                else:
                    expected_yield = cdata["base_yield"]
                    growth_days = remaining_days

                expected_revenue = expected_yield * current_price
                net_profit = expected_revenue - seed_cost
                profit_per_day = net_profit / max(1, growth_days)
                scores[crop] = profit_per_day + shop_demand.get(crop, 0) * 8.0 + scarcity_bonus - opp_penalty
            else:
                # Ongoing crop (Tomato, Strawberry)
                first_day = cdata["first_yield_day"]
                if remaining_days < first_day:
                    scores[crop] = -9999
                    continue
                intervals_possible = (remaining_days - first_day) // cdata["interval"] + 1
                intervals_possible = min(cdata["max_yield"], max(0, intervals_possible))
                if intervals_possible <= 0:
                    scores[crop] = -9999
                    continue
                expected_revenue = intervals_possible * current_price
                net_profit = expected_revenue - seed_cost
                scores[crop] = (net_profit / max(1, remaining_days)) + shop_demand.get(crop, 0) * 8.0 + scarcity_bonus - opp_penalty

        return scores

    def get_best_crop_portfolio(self, farm_state, num_slots_to_plant):
        """
        Dynamically calculate crop portfolio allocation based on ROI, opponent saturation, and game clock.
        """
        day = farm_state.day
        remaining_days = 29 - day
        
        if remaining_days < 2 or num_slots_to_plant <= 0:
            return {}

        opp_counts = self.count_opponent_crops(farm_state)
        opp_melon_heavy = opp_counts.get("MELON", 0) >= 15

        portfolio = {}
        if day <= 12 and remaining_days >= 12:
            if opp_melon_heavy:
                # Opponent flooding melons: Hedge with Melons (35%), Strawberries (25%), Carrots (25%), Wheat (15%)
                melon_count = int(num_slots_to_plant * 0.35)
                straw_count = int(num_slots_to_plant * 0.25)
                carrot_count = int(num_slots_to_plant * 0.25)
                wheat_count = num_slots_to_plant - melon_count - straw_count - carrot_count
                if melon_count > 0: portfolio["MELON"] = melon_count
                if straw_count > 0: portfolio["STRAWBERRY"] = straw_count
                if carrot_count > 0: portfolio["CARROT"] = carrot_count
                if wheat_count > 0: portfolio["WHEAT"] = wheat_count
            else:
                # Standard high-yield: 65% Melons, 25% Carrots, 10% Wheat
                melon_count = int(num_slots_to_plant * 0.65)
                carrot_count = int(num_slots_to_plant * 0.25)
                wheat_count = num_slots_to_plant - melon_count - carrot_count
                if melon_count > 0: portfolio["MELON"] = melon_count
                if carrot_count > 0: portfolio["CARROT"] = carrot_count
                if wheat_count > 0: portfolio["WHEAT"] = wheat_count

        elif day <= 19 and remaining_days >= 10:
            melon_count = int(num_slots_to_plant * 0.50)
            carrot_count = int(num_slots_to_plant * 0.35)
            wheat_count = num_slots_to_plant - melon_count - carrot_count
            if melon_count > 0: portfolio["MELON"] = melon_count
            if carrot_count > 0: portfolio["CARROT"] = carrot_count
            if wheat_count > 0: portfolio["WHEAT"] = wheat_count

        elif remaining_days >= 3:
            # Late game: Fast Carrots (75%) and Wheat (25%)
            carrot_count = int(num_slots_to_plant * 0.75)
            wheat_count = num_slots_to_plant - carrot_count
            if carrot_count > 0: portfolio["CARROT"] = carrot_count
            if wheat_count > 0: portfolio["WHEAT"] = wheat_count
        else:
            portfolio = {}

        return portfolio


class MarketManager:
    def __init__(self):
        self.economy = EconomyManager()

    def generate_market_orders(self, farm_state, planned_hires=0):
        orders = []
        money = farm_state.money
        day = farm_state.day
        hour = farm_state.hour

        # 1. HIRE FARM HANDS at hour 0
        if hour == 0 and planned_hires > farm_state.hires_today:
            needed = planned_hires - farm_state.hires_today
            for _ in range(needed):
                cost = fib_hire_cost(farm_state.hires_today + len([o for o in orders if o[0] == "HIRE"]))
                if money >= cost:
                    orders.append(["HIRE"])
                    money -= cost

        # 2. BUY LAND EXPANSION
        n_unlocked = len(farm_state.unlocked_quadrants) - 1
        if n_unlocked < len(LAND_PRICES):
            cost = LAND_PRICES[n_unlocked]
            should_buy_land = False
            if n_unlocked == 0 and money >= cost + 150: # NE
                should_buy_land = True
            elif n_unlocked == 1 and money >= cost + 400 and day <= 12: # SW
                should_buy_land = True
            elif n_unlocked == 2 and money >= cost + 2500 and day <= 14: # SE
                should_buy_land = True
            
            if should_buy_land and len(orders) < 10:
                orders.append(["BUY_LAND"])
                money -= cost

        # 3. BUY ANIMAL (Geese early on)
        num_animals = len([t for row in farm_state.tiles for t in row if isinstance(t, dict) and "animal" in t and t.get("animal")])
        num_coops = len([t for row in farm_state.tiles for t in row if isinstance(t, dict) and t.get("kind") == "COOP"])
        geese_in_shed = farm_state.shed.get("GOOSE", 0)
        
        if day <= 8 and (num_animals + geese_in_shed) < 4 and money >= 350 and len(orders) < 10:
            if geese_in_shed == 0 and num_coops > num_animals:
                orders.append(["BUY_ANIMAL", "GOOSE", 1])
                money -= 300

        # 4. BUY WHEAT FOR ANIMAL FEED
        wheat_in_shed = farm_state.shed.get("WHEAT", 0)
        if num_animals > 0 and wheat_in_shed < num_animals * 2 and money >= 50 and len(orders) < 10:
            buy_wheat = min(8, num_animals * 3 - wheat_in_shed)
            if buy_wheat > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", buy_wheat])
                money -= buy_wheat * 30

        # 5. BUY SEEDS
        empty_count = len(farm_state.empty_tiles)
        total_seeds_held = sum(farm_state.seeds.values())
        needed_seeds = max(0, empty_count - total_seeds_held)
        
        if needed_seeds > 0 and day <= 26 and len(orders) < 10:
            portfolio = self.economy.get_best_crop_portfolio(farm_state, needed_seeds)
            for crop, count in portfolio.items():
                if len(orders) >= 10:
                    break
                seed_price = CROPS[crop]["seed"]
                affordable = min(count, int(money // seed_price))
                if affordable > 0:
                    orders.append(["BUY_SEED", crop, affordable])
                    money -= affordable * seed_price

        # 6. SELL HARVESTED PRODUCTS
        sell_priority = ["MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "TOMATO", "EGG", "CARROT", "WHEAT"]
        for prod in sell_priority:
            if len(orders) >= 10:
                break
            qty = farm_state.shed.get(prod, 0)
            if qty > 0:
                cur_p = farm_state.market_prices.get(prod, 1)
                # In endgame (day >= 26) or high shed volume (>35), dump everything
                if day >= 26 or farm_state.shed_item_count() >= 35:
                    orders.append(["SELL", prod, qty])
                elif cur_p > 1:
                    # Batch sell up to 10 units per turn to allow price recovery
                    sell_amount = min(qty, 10)
                    orders.append(["SELL", prod, sell_amount])

        return orders[:10]
