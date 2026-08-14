"""
=============================================================================
ENGINE: MARKET DYNAMICS & PRICE SLIPPAGE MODEL
=============================================================================
Models non-linear price curves, inventory slippage, and optimal batch sizing.
=============================================================================
"""

import math
from config import MARKET_PARAMS, PRICE_FLOOR, _shape, compute_market_price, PRODUCTS


class MarketModel:
    def __init__(self):
        self.params = MARKET_PARAMS

    def get_spot_price(self, item, inventory):
        return compute_market_price(item, inventory, self.params)

    def simulate_sell_revenue(self, item, starting_inventory, quantity):
        """
        Simulate total revenue from selling `quantity` units sequentially,
        accounting for progressive market price depression as inventory increases.
        """
        if quantity <= 0:
            return 0.0

        total_revenue = 0.0
        cur_inv = starting_inventory
        for _ in range(quantity):
            price = self.get_spot_price(item, cur_inv)
            total_revenue += price
            cur_inv += 1
            
        return total_revenue

    def calculate_price_slippage(self, item, starting_inventory, quantity):
        """
        Calculates the percentage price drop caused by selling `quantity` units.
        """
        if quantity <= 0:
            return 0.0
        p_initial = self.get_spot_price(item, starting_inventory)
        p_final = self.get_spot_price(item, starting_inventory + quantity)
        return max(0.0, (p_initial - p_final) / max(1.0, float(p_initial)))

    def get_optimal_sell_batch(self, item, starting_inventory, available_qty, max_allowed_slippage=0.20):
        """
        Computes the maximum batch quantity to sell without depressing price
        beyond `max_allowed_slippage`.
        """
        if available_qty <= 0:
            return 0

        p_initial = self.get_spot_price(item, starting_inventory)
        best_qty = available_qty

        for q in range(1, available_qty + 1):
            p_curr = self.get_spot_price(item, starting_inventory + q)
            slippage = (p_initial - p_curr) / max(1.0, float(p_initial))
            if slippage > max_allowed_slippage:
                return max(1, q - 1)

        return best_qty
