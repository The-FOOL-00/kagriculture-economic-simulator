"""
ACTION ARBITRATOR: First-Class Priority Allocator for the 10-Order Simulator Cap.
Guarantees that discretionary sales never displace mandatory dawn hiring,
land expansion, or survival feeding.
"""
from typing import List, Dict, Any, Tuple
from enum import IntEnum

class OrderPriority(IntEnum):
    MANDATORY_WORKFORCE = 1     # HIRE orders at dawn
    CRITICAL_CAPEX = 2          # BUY_LAND (e.g. Day 10 expansion)
    SURVIVAL_FEED = 3           # BUY_PRODUCT WHEAT if feed depleted
    LIVESTOCK_CAPEX = 4         # BUY_ANIMAL (sheep/cow)
    EMERGENCY_SALES = 5         # SELL to prevent cash floor violation
    HIGH_VALUE_TOWN_DELIVER = 6 # DELIVER to town with 2.0x bonus
    STANDARD_PRODUCTION_BUYS = 7# Seeds for next crop cycle
    STANDARD_MARKET_SALES = 8   # Planned market liquidation
    SPECULATIVE_OPTIONAL = 9    # Optional batch holding / purchases

class ActionArbitrator:
    MAX_ORDERS = 10

    def __init__(self):
        self.arbitration_stats = {
            "total_steps": 0,
            "orders_submitted": 0,
            "orders_rejected": 0,
            "discretionary_sales_deferred": 0,
            "hires_protected": 0
        }

    def classify_order(self, order: List[Any], economic_state: Any) -> OrderPriority:
        if not order or not isinstance(order, (list, tuple)):
            return OrderPriority.SPECULATIVE_OPTIONAL

        op = str(order[0]).upper()
        
        # 1. HIRE
        if op == "HIRE":
            return OrderPriority.MANDATORY_WORKFORCE
            
        # 2. BUY_LAND
        if op == "BUY_LAND":
            return OrderPriority.CRITICAL_CAPEX
            
        # 3. BUY_ANIMAL
        if op == "BUY_ANIMAL":
            return OrderPriority.LIVESTOCK_CAPEX
            
        # 4. BUY_PRODUCT (Seeds or Feed)
        if op == "BUY_PRODUCT":
            item = str(order[1]).upper() if len(order) > 1 else ""
            if item == "WHEAT":
                # Check if this is critical animal survival feed
                if economic_state.shed.get("WHEAT", 0) < sum(economic_state.animal_counts.values()):
                    return OrderPriority.SURVIVAL_FEED
                return OrderPriority.STANDARD_PRODUCTION_BUYS
            return OrderPriority.STANDARD_PRODUCTION_BUYS
            
        # 5. DELIVER (Town Shops)
        if op == "DELIVER":
            return OrderPriority.HIGH_VALUE_TOWN_DELIVER
            
        # 6. SELL (Market)
        if op == "SELL":
            # If cash is below safe cash floor, this is an emergency sale
            if hasattr(economic_state, "cash") and hasattr(economic_state, "next_mandatory_expenditure"):
                if economic_state.cash < economic_state.next_mandatory_expenditure + 500.0:
                    return OrderPriority.EMERGENCY_SALES
            return OrderPriority.STANDARD_MARKET_SALES
            
        return OrderPriority.SPECULATIVE_OPTIONAL

    def arbitrate_market_orders(
        self, 
        candidate_orders: List[List[Any]], 
        economic_state: Any
    ) -> List[List[Any]]:
        """
        Takes raw candidate orders, prioritizes them, and returns at most MAX_ORDERS (10).
        Discretionary sales never crowd out mandatory hires or capex.
        """
        self.arbitration_stats["total_steps"] += 1
        if not candidate_orders:
            return []

        # Tag each order with priority and original sequence index (for stability)
        tagged_orders: List[Tuple[OrderPriority, int, List[Any]]] = []
        for idx, order in enumerate(candidate_orders):
            prio = self.classify_order(order, economic_state)
            tagged_orders.append((prio, idx, order))

        # Sort by Priority ascending, then original index
        tagged_orders.sort(key=lambda x: (x[0], x[1]))

        # Select top 10
        selected = tagged_orders[:self.MAX_ORDERS]
        rejected = tagged_orders[self.MAX_ORDERS:]

        self.arbitration_stats["orders_submitted"] += len(candidate_orders)
        self.arbitration_stats["orders_rejected"] += len(rejected)

        for p, _, ord_item in rejected:
            if isinstance(ord_item, (list, tuple)) and len(ord_item) > 0 and ord_item[0] == "SELL":
                self.arbitration_stats["discretionary_sales_deferred"] += 1

        for p, _, ord_item in selected:
            if isinstance(ord_item, (list, tuple)) and len(ord_item) > 0 and ord_item[0] == "HIRE":
                self.arbitration_stats["hires_protected"] += 1

        # Preserve original relative order for the selected items to maintain execution semantics
        selected.sort(key=lambda x: x[1])
        return [item[2] for item in selected]
