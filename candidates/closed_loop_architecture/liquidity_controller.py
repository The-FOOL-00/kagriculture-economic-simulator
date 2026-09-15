"""
LIQUIDITY CONTROLLER: Runtime Cash-Runway Invariant and Emergency Liquidation.
Calculates SAFE_CASH_FLOOR(t) dynamically and triggers emergency market sales
if cash is in jeopardy of causing a hiring or feeding collapse.
"""
from typing import Dict, List, Any, Tuple

class LiquidityController:
    def __init__(self, base_reserve: float = 500.0):
        self.base_reserve = base_reserve
        self.trigger_events: List[Dict[str, Any]] = []
        self.emergency_sales_executed: int = 0

    def compute_safe_cash_floor(self, economic_state: Any) -> float:
        """
        Dynamically computes the minimum cash required at step t to prevent
        hiring failure, starvation, or capex bankruptcy.
        """
        # 1. Scaled operating reserve (higher mid-game during land unlock)
        day = economic_state.day
        hour = economic_state.hour
        
        if 9 <= day <= 11:
            reserve = 1000.0  # High volatility window around SW land purchase
        elif day > 25:
            reserve = 300.0   # End-game liquidation phase
        else:
            reserve = self.base_reserve
            
        # 2. Mandatory hiring obligation at next dawn
        workers = economic_state.workers_count
        hiring_obligation = workers * 200.0
        
        # 3. Committed CapEx in next 24 hours
        committed_capex = 0.0
        if day == 10 and hour < 12:
            committed_capex = 3000.0  # Southwest quadrant expansion
        elif day == 11 and hour < 6:
            committed_capex = 1200.0  # Bulk Strawberry seeds
            
        # 4. Animal feed buffer
        total_animals = sum(economic_state.animal_counts.values())
        available_feed = economic_state.shed.get("WHEAT", 0)
        feed_deficit = max(0, total_animals - available_feed)
        feed_obligation = feed_deficit * 250.0  # Cost to purchase feed on market if needed
        
        safe_floor = reserve + hiring_obligation + committed_capex + feed_obligation
        return safe_floor

    def check_liquidity(self, economic_state: Any) -> Tuple[bool, float, List[List[Any]]]:
        """
        Evaluates liquidity against the dynamic safe floor.
        If cash < floor, returns (True, cash_deficit, emergency_sell_orders).
        """
        floor = self.compute_safe_cash_floor(economic_state)
        cash = economic_state.cash
        deficit = floor - cash
        
        if deficit <= 0:
            return False, 0.0, []

        # Liquidity cliff detected! Generate emergency sell orders for shed inventory
        emergency_orders: List[List[Any]] = []
        shed = economic_state.shed
        prices = economic_state.market_prices
        
        # Priority order of commodities to liquidate for emergency cash:
        # 1. WOOL (high value, not needed for feed or replant)
        # 2. Surplus WHEAT (keep at least 5 for animal feed)
        # 3. CARROT / TOMATO / STRAWBERRY (harvested crops)
        # 4. MILK / EGG
        liquidation_priority = ["WOOL", "WHEAT", "STRAWBERRY", "CARROT", "TOMATO", "MILK", "EGG"]
        cash_raised = 0.0
        
        for item in liquidation_priority:
            qty = shed.get(item, 0)
            if item == "WHEAT":
                # STRICT NON-CANNIBALIZATION INVARIANT:
                # Retain at least 3 days of animal feed (3 * total_animals)
                total_animals = sum(economic_state.animal_counts.values())
                feed_reserve = max(10, total_animals * 3)
                qty = max(0, qty - feed_reserve)
                
            if qty > 0:
                price = prices.get(item, 100.0)
                emergency_orders.append(["SELL", item, qty])
                cash_raised += qty * price
                if cash_raised >= deficit:
                    break
                    
        self.emergency_sales_executed += len(emergency_orders)
        self.trigger_events.append({
            "step": economic_state.step,
            "day": economic_state.day,
            "cash": cash,
            "floor": floor,
            "deficit": deficit,
            "orders": emergency_orders
        })
        
        return True, deficit, emergency_orders
