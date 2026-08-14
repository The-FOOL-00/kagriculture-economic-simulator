"""
=============================================================================
ENGINE: TOWN DEMAND & CONSUMPTION TIMING MODEL
=============================================================================
Forecasts periodic town shop consumption ticks and identifies scarcity peaks.
=============================================================================
"""

from config import SHOPS, PRODUCTS, TOWN_CENTER_PRODUCTS, TOWN_CENTER_DEMAND_SCHEDULE


class TownDemandModel:
    def __init__(self):
        self.shops_def = SHOPS

    def get_shop_demand_weights(self, unlocked_shops):
        """
        Computes the relative demand intensity for each commodity based on active shops.
        """
        weights = {p: 0 for p in PRODUCTS}
        for shop in unlocked_shops:
            prods = self.shops_def.get(shop, [])
            # Single-product shops consume at 2x intensity
            mult = 2 if len(prods) == 1 else 1
            for p in prods:
                weights[p] += mult
        return weights

    def is_post_consumption_window(self, step):
        """
        Checks if the current step immediately follows a shop or town center consumption tick.
        Shop consumption occurs at step % 4 == 0.
        Town center consumption occurs at step % 12 == 0.
        """
        # Step % 4 == 1 or Step % 4 == 0 are peak scarcity arbitrage moments
        return (step % 4 == 0) or (step % 4 == 1) or (step % 12 == 0) or (step % 12 == 1)

    def steps_until_next_consumption(self, step):
        """
        Computes remaining steps until the next market inventory drain.
        """
        return 4 - (step % 4)
