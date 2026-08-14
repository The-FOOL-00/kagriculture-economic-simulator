"""
Elite Grandmaster Strategy: High-Density Animal Ranching (8C/4S) + Accelerated Fertilized Crop Engine + Town Shop Exploitation.
"""

from config import (
    CROPS, ANIMALS, PRODUCTS, SHOPS, LAND_PRICES,
    compute_market_price, fib_hire_cost
)


class GrandmasterEconomy:
    def __init__(self):
        pass

    def get_shop_demands(self, farm_state):
        shop_demand = {p: 0 for p in PRODUCTS}
        for shop in farm_state.unlocked_shops:
            prods = SHOPS.get(shop, [])
            mult = 2 if len(prods) == 1 else 1
            for p in prods:
                shop_demand[p] += mult
        return shop_demand

    def count_opponent_production(self, farm_state):
        counts = {p: 0 for p in PRODUCTS}
        opp_tiles = farm_state.opp_farm.get("tiles", [])
        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        crop = t.get("crop")
                        if crop in counts: counts[crop] += 1
                    elif "animal" in t and t.get("animal"):
                        animal = t.get("animal")
                        if animal == "GOOSE": counts["EGG"] += 1
                        elif animal == "COW": counts["MILK"] += 1
                        elif animal == "SHEEP": counts["WOOL"] += 1
        return counts

    def get_crop_portfolio(self, farm_state, available_crop_slots):
        day = farm_state.day
        remaining_days = 29 - day
        
        if remaining_days < 2 or available_crop_slots <= 0:
            return {}

        opp_counts = self.count_opponent_production(farm_state)
        opp_melon_heavy = opp_counts.get("MELON", 0) >= 15
        shop_demand = self.get_shop_demands(farm_state)

        portfolio = {}
        if day <= 12 and remaining_days >= 12:
            if opp_melon_heavy:
                melon_c = int(available_crop_slots * 0.35)
                straw_c = int(available_crop_slots * 0.25)
                carrot_c = int(available_crop_slots * 0.25)
                wheat_c = available_crop_slots - melon_c - straw_c - carrot_c
                if melon_c > 0: portfolio["MELON"] = melon_c
                if straw_c > 0: portfolio["STRAWBERRY"] = straw_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c
            else:
                # 60% Melons, 25% Carrots, 15% Wheat (for animal feed and market)
                melon_c = int(available_crop_slots * 0.60)
                carrot_c = int(available_crop_slots * 0.25)
                wheat_c = available_crop_slots - melon_c - carrot_c
                if melon_c > 0: portfolio["MELON"] = melon_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c

        elif day <= 19 and remaining_days >= 10:
            melon_c = int(available_crop_slots * 0.45)
            carrot_c = int(available_crop_slots * 0.35)
            wheat_c = available_crop_slots - melon_c - carrot_c
            if melon_c > 0: portfolio["MELON"] = melon_c
            if carrot_c > 0: portfolio["CARROT"] = carrot_c
            if wheat_c > 0: portfolio["WHEAT"] = wheat_c

        elif remaining_days >= 3:
            # Fast Carrots (70%) and Wheat (30%)
            carrot_c = int(available_crop_slots * 0.70)
            wheat_c = available_crop_slots - carrot_c
            if carrot_c > 0: portfolio["CARROT"] = carrot_c
            if wheat_c > 0: portfolio["WHEAT"] = wheat_c

        return portfolio


class GrandmasterMarket:
    def __init__(self):
        self.economy = GrandmasterEconomy()

    def generate_orders(self, farm_state, planned_hires=0):
        orders = []
        money = farm_state.money
        day = farm_state.day
        hour = farm_state.hour

        # 1. HIRE WORKERS at hour 0
        if hour == 0 and planned_hires > farm_state.hires_today:
            needed = planned_hires - farm_state.hires_today
            for _ in range(needed):
                cost = fib_hire_cost(farm_state.hires_today + len([o for o in orders if o[0] == "HIRE"]))
                if money >= cost:
                    orders.append(["HIRE"])
                    money -= cost

        # 2. EXPAND LAND (NE at Day 0-2, SW at Day 4-10, SE at Day 8-13)
        n_unlocked = len(farm_state.unlocked_quadrants) - 1
        if n_unlocked < len(LAND_PRICES):
            cost = LAND_PRICES[n_unlocked]
            should_buy = False
            if n_unlocked == 0 and money >= cost + 150: # NE ($1k)
                should_buy = True
            elif n_unlocked == 1 and money >= cost + 300 and day <= 11: # SW ($2k)
                should_buy = True
            elif n_unlocked == 2 and money >= cost + 2000 and day <= 13: # SE ($4k)
                should_buy = True

            if should_buy and len(orders) < 10:
                orders.append(["BUY_LAND"])
                money -= cost

        # 3. ANIMAL LIVESTOCK EXPANSION (6 Geese + 4 Sheep)
        # Count current animals + animals in shed
        num_geese = sum(1 for row in farm_state.tiles for t in row if isinstance(t, dict) and t.get("animal") == "GOOSE")
        num_sheep = sum(1 for row in farm_state.tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        
        geese_in_shed = farm_state.shed.get("GOOSE", 0)
        sheep_in_shed = farm_state.shed.get("SHEEP", 0)

        # Count empty structures
        empty_coops = sum(1 for row in farm_state.tiles for t in row if isinstance(t, dict) and t.get("kind") == "COOP" and not t.get("animal"))
        empty_pastures = sum(1 for row in farm_state.tiles for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE" and not t.get("animal"))

        # Buy Geese if coops available and needed
        if day <= 10 and (num_geese + geese_in_shed) < 6 and money >= 350 and len(orders) < 10:
            if empty_coops > geese_in_shed:
                orders.append(["BUY_ANIMAL", "GOOSE", 1])
                money -= 300
                geese_in_shed += 1

        # Buy Sheep if pastures available and needed
        if day <= 12 and (num_sheep + sheep_in_shed) < 4 and money >= 550 and len(orders) < 10:
            if empty_pastures > sheep_in_shed:
                orders.append(["BUY_ANIMAL", "SHEEP", 1])
                money -= 500
                sheep_in_shed += 1

        # 4. FEED BUFFER (Ensure enough wheat in shed for all animals)
        total_live_animals = num_geese + num_sheep
        wheat_in_shed = farm_state.shed.get("WHEAT", 0)
        if total_live_animals > 0 and wheat_in_shed < total_live_animals * 2 and money >= 60 and len(orders) < 10:
            needed_wheat = min(10, total_live_animals * 3 - wheat_in_shed)
            if needed_wheat > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", needed_wheat])
                money -= needed_wheat * 30

        # 5. BUY SEEDS FOR REMAINING CROP TILES
        empty_count = len(farm_state.empty_tiles)
        total_seeds_held = sum(farm_state.seeds.values())
        needed_seeds = max(0, empty_count - total_seeds_held)
        
        if needed_seeds > 0 and day <= 26 and len(orders) < 10:
            portfolio = self.economy.get_crop_portfolio(farm_state, needed_seeds)
            for crop, count in portfolio.items():
                if len(orders) >= 10:
                    break
                seed_price = CROPS[crop]["seed"]
                affordable = min(count, int(money // seed_price))
                if affordable > 0:
                    orders.append(["BUY_SEED", crop, affordable])
                    money -= affordable * seed_price

        # 6. STRATEGIC SELLING OF SHED INVENTORY
        # Prioritize high-value items and smooth pacing
        sell_order = ["MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "TOMATO", "EGG", "CARROT", "WHEAT"]
        for prod in sell_order:
            if len(orders) >= 10:
                break
            qty = farm_state.shed.get(prod, 0)
            if qty > 0:
                cur_p = farm_state.market_prices.get(prod, 1)
                # Keep some wheat for animals
                if prod == "WHEAT" and day < 27 and total_live_animals > 0:
                    reserve = total_live_animals * 2
                    qty = max(0, qty - reserve)
                    if qty <= 0:
                        continue

                # In endgame (day >= 26) or high shed volume (>35), liquidate!
                if day >= 26 or farm_state.shed_item_count() >= 35:
                    orders.append(["SELL", prod, qty])
                elif cur_p > 1:
                    sell_amount = min(qty, 12)
                    orders.append(["SELL", prod, sell_amount])

        return orders[:10]
