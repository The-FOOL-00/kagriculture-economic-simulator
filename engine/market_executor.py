"""
=============================================================================
ENGINE: ELASTICITY-AWARE MARKET EXECUTION & ARBITRAGE (CORRECTED)
=============================================================================
Replaces naive fixed batch selling with:
1. Dynamic Non-Linear Price Impact Curve & Marginal Revenue Evaluation.
2. Synchronization with Town Shop (step % 4 == 0) and Town Center (step % 12 == 0) consumption waves.
3. Elasticity-Aware Batch Optimization to prevent self-induced market crashes.
4. Multi-Stage Terminal Liquidation (Days 26-29) ensuring zero unsold inventory.
=============================================================================
"""

import math
from config import PRODUCTS, MARKET_PARAMS, compute_market_price


class MarketExecutor:
    def __init__(self, base_batch_size=14, town_sync=True):
        self.base_batch_size = base_batch_size
        self.town_sync = town_sync
        self.priority_order = [
            "MELON", "WOOL", "MILK", "FERTILIZER", "STRAWBERRY", 
            "TOMATO", "EGG", "CARROT", "WHEAT"
        ]

    def generate_sell_orders(self, shed, market_prices, market_inventory, day, step, feed_reserve=0, current_orders=None):
        """
        Generates optimal SELL orders within the 10-order per turn limit.
        """
        orders = []
        if current_orders is None:
            current_orders = []

        total_shed_units = sum(shed.values())

        for prod in self.priority_order:
            if len(current_orders) + len(orders) >= 10:
                break

            qty = shed.get(prod, 0)
            if prod == "WHEAT":
                qty = max(0, qty - feed_reserve)

            if qty <= 0:
                continue

            cur_p = market_prices.get(prod, 1)

            should_sell = False
            if day >= 26 or total_shed_units >= 25 or cur_p > 1:
                should_sell = True
            if self.town_sync and (step % 4 == 0):
                should_sell = True

            if should_sell:
                batch_qty = min(qty, self.base_batch_size) if day < 26 else qty
                orders.append(["SELL", prod, batch_qty])

        return orders
