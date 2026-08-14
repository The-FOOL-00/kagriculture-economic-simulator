"""
=============================================================================
ENGINE: DYNAMIC ECONOMIC VALUATION & ASSET EVALUATOR
=============================================================================
Computes exact Net Present Value (NPV), Marginal Expected Return on Capital (ROI),
and Payback Period for all crops, livestock, structures, and land.
=============================================================================
"""

import math
from config import CROPS, ANIMALS, PRODUCTS, LAND_PRICES


class EconomicEvaluator:
    def __init__(self, market_model, town_model):
        self.market_model = market_model
        self.town_model = town_model

    def evaluate_crop_roi(self, crop, current_day, market_inv, unlocked_shops, opp_crop_count=0):
        """
        Computes expected net profit per tile across remaining season days.
        """
        remaining_days = 29 - current_day
        if remaining_days < 2:
            return -9999.0

        cdata = CROPS[crop]
        seed_cost = cdata["seed"]
        cur_price = self.market_model.get_spot_price(crop, market_inv.get(crop, 10000))
        shop_weights = self.town_model.get_shop_demand_weights(unlocked_shops)
        
        shop_boost = shop_weights.get(crop, 0) * 8.0
        opp_penalty = opp_crop_count * 1.5
        scarcity_factor = max(0.0, (10000 - market_inv.get(crop, 10000)) * 0.03)

        if not cdata["ongoing"]:
            growth_days = cdata["max_yield_day"]
            if remaining_days < cdata["first_yield_day"]:
                return -9999.0

            cycles = remaining_days // growth_days
            rem_days = remaining_days % growth_days

            expected_units = cdata["max_yield"] if crop == "MELON" else cdata["base_yield"]
            if crop == "CARROT": expected_units = 3
            elif crop == "WHEAT": expected_units = 4

            cycle_revenue = self.market_model.simulate_sell_revenue(crop, market_inv.get(crop, 10000), expected_units)
            total_net_profit = cycles * (cycle_revenue - seed_cost)

            if rem_days >= cdata["first_yield_day"]:
                rem_units = cdata["base_yield"]
                rem_rev = self.market_model.simulate_sell_revenue(crop, market_inv.get(crop, 10000), rem_units)
                total_net_profit += (rem_rev - seed_cost)

            daily_roi = (total_net_profit / max(1.0, float(remaining_days))) + shop_boost + scarcity_factor - opp_penalty
            return daily_roi

        else:
            first_day = cdata["first_yield_day"]
            if remaining_days < first_day:
                return -9999.0

            num_harvests = (remaining_days - first_day) // cdata["interval"] + 1
            units_per_harvest = cdata["base_yield"]
            total_units = num_harvests * units_per_harvest

            total_revenue = self.market_model.simulate_sell_revenue(crop, market_inv.get(crop, 10000), total_units)
            total_net_profit = total_revenue - seed_cost

            daily_roi = (total_net_profit / max(1.0, float(remaining_days))) + shop_boost + scarcity_factor - opp_penalty
            return daily_roi

    def evaluate_animal_npv(self, animal, current_day, market_inv, unlocked_shops):
        """
        Computes expected net lifetime cash contribution for purchasing an animal on current_day.
        """
        adata = ANIMALS[animal]
        cost = adata["cost"]
        prod = adata["product"]
        remaining_days = 29 - current_day
        
        if remaining_days < adata["first_yield_day"]:
            return -cost

        num_harvests = (remaining_days - adata["first_yield_day"]) // adata["interval"] + 1
        units_per_harvest = adata["max_held"]
        total_prod_units = num_harvests * units_per_harvest

        product_rev = self.market_model.simulate_sell_revenue(prod, market_inv.get(prod, 10000), total_prod_units)
        
        # Fertilizer cash value (1 per day from placement)
        fert_units = remaining_days
        fert_rev = self.market_model.simulate_sell_revenue("FERTILIZER", market_inv.get("FERTILIZER", 10000), fert_units)

        # Feed cost: 1 wheat per day ($30 store cost, or $10 if homegrown)
        feed_cost = remaining_days * 25.0
        
        net_npv = product_rev + fert_rev - feed_cost - cost
        return net_npv

    def evaluate_land_expansion(self, current_quadrants_count, current_money, current_day, expected_daily_tile_profit):
        """
        Evaluates whether buying the next land quadrant is economically positive.
        """
        n_unlocked = current_quadrants_count - 1
        if n_unlocked >= len(LAND_PRICES):
            return False

        cost = LAND_PRICES[n_unlocked]
        remaining_days = 29 - current_day

        # 25 new tiles
        potential_gross_profit = 25 * expected_daily_tile_profit * remaining_days
        
        # Payback condition: profit must exceed cost by at least 50% buffer and preserve liquidity
        if potential_gross_profit > cost * 1.5 and current_money >= cost + 250:
            return True

        return False
