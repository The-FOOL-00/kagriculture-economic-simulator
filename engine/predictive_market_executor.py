"""
=============================================================================
ENGINE: PREDICTIVE MARKET EXECUTOR
=============================================================================
Executes state-dependent, opponent-aware market liquidation:
1. Detects imminent competitor dumps to frontrun liquidations 1 step prior.
2. Dynamically optimizes batch sizes (8, 12, 14, 18, 24) against elasticity curves.
3. Synchronizes with town consumption waves to avoid selling into depressed pools.
4. Liquidity urgency override: executes emergency cash-unlocking sales when critical capital is low.
5. Guaranteed endgame flush during steps 680 - 719.
=============================================================================
"""

class PredictiveMarketExecutor:
    def __init__(self, base_batch_size=14, enable_frontrunning=True, dynamic_batching=True):
        self.base_batch_size = base_batch_size
        self.enable_frontrunning = enable_frontrunning
        self.dynamic_batching = dynamic_batching

    def compute_optimal_batch(self, prod, qty, current_price, dump_risk, step):
        """
        Calculates optimal liquidation batch size based on price elasticity and dump threat.
        """
        if not self.dynamic_batching:
            return min(qty, self.base_batch_size)

        if step >= 680:
            return min(qty, 30)

        # High dump threat: liquidate in larger batch to secure liquidity before price crashes
        if dump_risk >= 0.70:
            if prod == "MELON":
                return min(qty, 18)
            return min(qty, 20)

        # Normal condition: optimize around town batch absorption capacity
        if prod == "MELON":
            return min(qty, 14)
        elif prod in ["MILK", "WOOL"]:
            return min(qty, 12)
        elif prod in ["CARROT", "WHEAT"]:
            return min(qty, 16)
        return min(qty, self.base_batch_size)

    def generate_orders(self, shed, market_prices, market_inv, opp_analysis, price_forecasts, 
                        day, step, money, urgent_cash_needed, feed_reserve=0, current_orders=None):
        """
        Generates intelligent, predictive sell orders.
        """
        orders = []
        rem_orders = 10 - len(current_orders or [])
        if rem_orders <= 0:
            return orders

        # 1. Endgame Clearance (Steps 680 - 719)
        if step >= 680:
            for prod in ["MELON", "WOOL", "MILK", "CARROT", "STRAWBERRY", "TOMATO", "FERTILIZER"]:
                qty = shed.get(prod, 0)
                if qty > 0 and len(orders) < rem_orders:
                    batch = min(qty, 30)
                    orders.append(["SELL", prod, batch])
            # Sell remaining wheat in excess of absolute emergency
            if shed.get("WHEAT", 0) > 0 and len(orders) < rem_orders:
                orders.append(["SELL", "WHEAT", min(shed["WHEAT"], 30)])
            return orders

        # 2. Urgent Liquidity Override (Cash < $100 and need urgent working capital)
        urgent_sale_triggered = (money < 100 and urgent_cash_needed > 0)

        # 3. Standard & Predictive Market Execution
        for prod in ["MELON", "WOOL", "MILK", "CARROT", "STRAWBERRY", "TOMATO", "FERTILIZER"]:
            qty = shed.get(prod, 0)
            if qty <= 0:
                continue

            fc = price_forecasts.get(prod, {})
            dump_risk = fc.get("dump_risk", 0.0)
            dump_price_drop = fc.get("dump_price_drop", 0)

            should_sell = False
            reason = "NONE"

            # Condition A: Frontrun Imminent Competitor Dump
            if self.enable_frontrunning and dump_risk >= 0.70 and dump_price_drop >= 15:
                should_sell = True
                reason = "FRONTRUN_DUMP"

            # Condition B: Urgent Cash Need
            elif urgent_sale_triggered:
                should_sell = True
                reason = "URGENT_LIQUIDITY"

            # Condition C: Town Modulo-4 Schedule (Default baseline wave)
            elif step % 4 == 0:
                should_sell = True
                reason = "MODULO_4_TOWN_WAVE"

            if should_sell and len(orders) < rem_orders:
                batch = self.compute_optimal_batch(prod, qty, market_prices.get(prod, 25), dump_risk, step)
                orders.append(["SELL", prod, batch])

        # Discretionary Wheat Selling (Only surplus above feed reserve target)
        if shed.get("WHEAT", 0) > feed_reserve + 8 and day < 26 and len(orders) < rem_orders:
            surplus = shed["WHEAT"] - (feed_reserve + 8)
            orders.append(["SELL", "WHEAT", min(surplus, 10)])

        return orders
