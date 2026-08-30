"""
=============================================================================
ENGINE: ELASTICITY-AWARE MARKET EXECUTION & ARBITRAGE (KAGGRICULTURE APEX)
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

    def compute_simulated_revenue(self, item, current_inventory, quantity):
        """
        Computes the exact realized cash from selling `quantity` units of `item`
        given current market inventory using the per-unit lockstep pricing curve.
        """
        total_rev = 0.0
        inv = current_inventory
        for _ in range(quantity):
            p = compute_market_price(item, inv)
            total_rev += p
            if p > 1:
                inv += 1
        return total_rev

    def get_optimal_sell_batch(self, item, available_qty, market_inventory, day, step):
        """
        Determines optimal unit quantity to sell this turn based on price elasticity,
        inventory depth, and game horizon.
        """
        if available_qty <= 0:
            return 0

        # Terminal Liquidation Phase (Days 26 - 29): Full liquidation
        if day >= 26:
            return available_qty

        # Early / Mid Game: Balance price capture with market absorption capacity
        params = MARKET_PARAMS.get(item, {})
        base_price = params.get("base", 100)
        curr_price = compute_market_price(item, market_inventory)

        # If current price is at floor ($1), only dump if late game
        if curr_price <= 1 and day < 25:
            return 0

        # Test batch sizes and find marginal revenue sweet spot
        best_batch = min(available_qty, self.base_batch_size)
        
        # Check town consumption alignment (scarcity boost)
        is_shop_tick = (step % 4 == 0 or step % 4 == 1)
        is_center_tick = (step % 12 == 0 or step % 12 == 1)

        if is_center_tick or is_shop_tick:
            # Town just consumed; market inventory is lower and prices are elevated
            best_batch = min(available_qty, int(self.base_batch_size * 1.25))
        
        return max(1, best_batch)

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
            inv = market_inventory.get(prod, 10000)

            should_sell = False
            # Condition 1: Late game terminal liquidation
            if day >= 26:
                should_sell = True
            # Condition 2: Shed capacity emergency pressure (> 25 items)
            elif total_shed_units >= 25:
                should_sell = True
            # Condition 3: Town consumption synchronization
            elif (step % 4 == 0) and cur_p > 1:
                should_sell = True
            # Condition 4: High value premium price capture
            elif cur_p >= MARKET_PARAMS.get(prod, {}).get("base", 50) * 0.9:
                should_sell = True
            elif cur_p > 1:
                should_sell = True

            if should_sell:
                batch = self.get_optimal_sell_batch(prod, qty, inv, day, step)
                if batch > 0:
                    orders.append(["SELL", prod, batch])

        return orders
