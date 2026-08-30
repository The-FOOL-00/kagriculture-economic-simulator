"""
=============================================================================
ENGINE: MARKET SUPPLY & PRICE FORECASTER
=============================================================================
Computes analytical forward price trajectories given:
1. Current Town Market Inventory
2. Town Center & Shop Periodic Consumption Demand
3. Our Expected Sales
4. Opponent Forecasted Supply Dumps
=============================================================================
"""

import math
from config import MARKET_PARAMS, compute_market_price, PRODUCTS, SHOPS, TOWN_CENTER_DEMAND_SCHEDULE

class MarketSupplyAndPriceForecaster:
    def __init__(self):
        pass

    def compute_projected_price(self, product, projected_inventory):
        """
        Uses exact analytical pricing curve to calculate expected spot price.
        """
        return compute_market_price(product, projected_inventory)

    def forecast_prices(self, current_market_inv, current_prices, opp_forecast, day, step):
        """
        Forecasts spot prices across horizons k in [1, 2, 4, 8] steps.
        """
        price_forecasts = {}

        # Estimate daily town consumption baseline for each product
        town_daily_consumption = {
            "MELON": 4,
            "CARROT": 8,
            "WHEAT": 10,
            "TOMATO": 6,
            "STRAWBERRY": 4,
            "MILK": 6,
            "WOOL": 4,
            "EGG": 6,
            "FERTILIZER": 0
        }

        for prod in PRODUCTS:
            curr_inv = current_market_inv.get(prod, 10000)
            curr_p = current_prices.get(prod, MARKET_PARAMS.get(prod, {}).get("base", 25))
            opp_prod_fc = opp_forecast.get("forecast", {}).get(prod, {})

            # Expected dump in next 1-2 steps
            imminent_dump = 0
            if opp_prod_fc.get("imminent_dump_prob", 0.0) >= 0.70:
                imminent_dump = opp_prod_fc.get("min_dump_risk", 0)

            # Horizon 1 step (instant dump shock)
            inv_t1 = curr_inv + imminent_dump
            price_t1 = self.compute_projected_price(prod, inv_t1)

            # Horizon 4 steps (1 town consumption cycle)
            town_drain_4 = town_daily_consumption.get(prod, 2)
            inv_t4 = max(0, curr_inv + imminent_dump - town_drain_4)
            price_t4 = self.compute_projected_price(prod, inv_t4)

            # Horizon 8 steps
            inv_t8 = max(0, curr_inv + (opp_prod_fc.get("expected_t1", 0)) - (town_drain_4 * 2))
            price_t8 = self.compute_projected_price(prod, inv_t8)

            price_forecasts[prod] = {
                "current_price": curr_p,
                "price_t1": price_t1,
                "price_t4": price_t4,
                "price_t8": price_t8,
                "dump_price_drop": max(0, curr_p - price_t1),
                "dump_risk": opp_prod_fc.get("imminent_dump_prob", 0.0)
            }

        return price_forecasts
