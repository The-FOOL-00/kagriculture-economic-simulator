"""
SHED INVENTORY CONTROLLER: Explicit Headroom Protection.
Prevents the catastrophic 100-item shed capacity saturation where newly harvested
strawberries and manure are permanently discarded and deleted by the engine.
"""
from typing import Dict, List, Any, Tuple

class ShedController:
    MAX_CAPACITY = 100

    def __init__(self, policy: str = "88_CEILING"):
        self.policy = policy
        self.discard_prevention_triggers: int = 0
        self.purged_items_count: int = 0

    def get_effective_ceiling(self, economic_state: Any) -> int:
        if self.policy == "75_CEILING":
            return 75
        elif self.policy == "80_CEILING":
            return 80
        elif self.policy == "85_CEILING":
            return 85
        elif self.policy == "88_CEILING":
            return 88
        elif self.policy == "DYNAMIC":
            # In dynamic policy: lower ceiling right before major strawberry harvests (Days 19, 21, 23, 27)
            day = economic_state.day
            if day in (18, 19, 20, 21, 22, 23, 26, 27):
                return 82  # Headroom for 18 incoming strawberries
            return 90
        return 88

    def check_headroom(self, economic_state: Any) -> Tuple[bool, int, List[List[Any]]]:
        """
        Checks current shed occupancy against the policy ceiling.
        If occupancy > ceiling, generates purge sales for low-priority goods.
        """
        occupancy = economic_state.shed_occupancy
        ceiling = self.get_effective_ceiling(economic_state)
        overflow = occupancy - ceiling

        if overflow <= 0:
            return False, 0, []

        self.discard_prevention_triggers += 1
        shed = economic_state.shed
        shop_demands = economic_state.town_shop_demand
        
        # Determine items to purge in priority order:
        # 1. Non-demanded livestock products (e.g. WOOL if town doesn't have YARN_STORE)
        # 2. Excess WHEAT above animal feed buffer
        # 3. Excess FERTILIZER above 15
        # 4. Ready crops (STRAWBERRY, TOMATO, CARROT)
        purge_orders: List[List[Any]] = []
        items_to_purge = overflow

        # Check WOOL first if no town demand
        if shop_demands.get("WOOL", 0) == 0 and shed.get("WOOL", 0) > 0:
            qty = min(shed["WOOL"], items_to_purge)
            purge_orders.append(["SELL", "WOOL", qty])
            items_to_purge -= qty

        # Check excess WHEAT
        if items_to_purge > 0 and shed.get("WHEAT", 0) > 0:
            total_animals = sum(economic_state.animal_counts.values())
            safe_wheat_reserve = max(5, total_animals * 2)
            available_excess_wheat = max(0, shed["WHEAT"] - safe_wheat_reserve)
            if available_excess_wheat > 0:
                qty = min(available_excess_wheat, items_to_purge)
                purge_orders.append(["SELL", "WHEAT", qty])
                items_to_purge -= qty

        # Check excess FERTILIZER
        if items_to_purge > 0 and shed.get("FERTILIZER", 0) > 15:
            excess_fert = shed["FERTILIZER"] - 15
            qty = min(excess_fert, items_to_purge)
            purge_orders.append(["SELL", "FERTILIZER", qty])
            items_to_purge -= qty

        # Check any harvested crops that can be liquidated
        for crop in ["CARROT", "TOMATO", "MELON", "STRAWBERRY", "MILK", "EGG"]:
            if items_to_purge <= 0:
                break
            if shed.get(crop, 0) > 0:
                qty = min(shed[crop], items_to_purge)
                purge_orders.append(["SELL", crop, qty])
                items_to_purge -= qty

        total_purged = overflow - items_to_purge
        self.purged_items_count += total_purged
        return True, total_purged, purge_orders
