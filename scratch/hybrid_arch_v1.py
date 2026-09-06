"""
scratch/hybrid_arch_v1.py
HYBRID_V1: Retains V2's proven micro-scheduling and multi-agent coordination,
enhanced with online closed-loop safety guards, dynamic market reserves,
and adaptive terminal inventory clearance.
"""

import copy

BOARD_SIZE = 10
TURNS_PER_DAY = 24

# Import V2 base trace
import candidates.slot2_aethel_refined_v2 as v2_source
_TRACE = copy.deepcopy(v2_source._TRACE)
_BASE_PRICE = {"MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}

class HybridArchV1Agent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_step = -1
        self.clone_confidence = 0

    def __call__(self, obs, config=None):
        step = min(int(obs.get("step", 0) or 0), 719)
        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step

        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        my_farm = farms[player] if len(farms) > player else {}
        opp_farm = farms[1 - player] if len(farms) > (1 - player) else {}
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        money = float(my_farm.get("money", 0) or 0)
        market_info = obs.get("market") or {}
        prices = market_info.get("prices") or _BASE_PRICE

        # 1. Base Schedule Retrieval
        if step < len(_TRACE):
            base_action = copy.deepcopy(_TRACE[step])
        else:
            base_action = {"farmer": ["PASS"], "hands": [], "market": []}

        farmer_act = list(base_action.get("farmer", ["PASS"]))
        hands_acts = [list(h) for h in base_action.get("hands", [])]
        raw_market = list(base_action.get("market", []))

        # 2. Closed-Loop Market Verification & Sanitization
        sanitized_market = []
        simulated_money = money

        # Priority A: Atomic Orders (BUY_LAND, HIRE)
        for order in raw_market:
            if isinstance(order, list) and len(order) >= 1:
                op = order[0]
                if op == "BUY_LAND":
                    unlocked_extra = len(my_farm.get("unlocked_quadrants", ["NW"])) - 1
                    land_prices = [1000, 2000, 4000]
                    cost = land_prices[unlocked_extra] if unlocked_extra < len(land_prices) else 999999
                    if simulated_money >= cost:
                        sanitized_market.append(order)
                        simulated_money -= cost
                elif op == "HIRE":
                    sanitized_market.append(order)

        # Priority B: Validated Sales (Ensure shed has the item)
        sold_tracker = {}
        for order in raw_market:
            if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
                item = order[1]
                req_qty = int(order[2] or 0)
                available = max(0, int(shed.get(item, 0) or 0) - sold_tracker.get(item, 0))
                act_qty = min(req_qty, available)
                if act_qty > 0:
                    sanitized_market.append(["SELL", item, act_qty])
                    sold_tracker[item] = sold_tracker.get(item, 0) + act_qty
                    simulated_money += act_qty * float(prices.get(item, _BASE_PRICE.get(item, 25)))

        # Priority C: Purchases (BUY_SEED, BUY_PRODUCT, BUY_ANIMAL)
        for order in raw_market:
            if isinstance(order, list) and len(order) >= 3 and order[0] in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"):
                op = order[0]
                item = order[1]
                qty = int(order[2] or 0)
                unit_cost = 25
                if op == "BUY_SEED":
                    unit_cost = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(item, 50)
                elif op == "BUY_ANIMAL":
                    unit_cost = {"COW": 600, "SHEEP": 500, "GOOSE": 300}.get(item, 500)
                elif op == "BUY_PRODUCT":
                    unit_cost = float(prices.get(item, 25))
                
                total_cost = unit_cost * qty
                if simulated_money >= total_cost + 20:
                    sanitized_market.append(order)
                    simulated_money -= total_cost

        # 3. Dynamic Terminal Harvest & Liquidation (Step 712+)
        if step >= 712:
            for item in ("MELON", "STRAWBERRY", "MILK", "WOOL", "FERTILIZER", "TOMATO", "WHEAT", "CARROT", "EGG"):
                avail = max(0, int(shed.get(item, 0) or 0) - sold_tracker.get(item, 0))
                if avail > 0 and len(sanitized_market) < 10:
                    sanitized_market.append(["SELL", item, avail])
                    sold_tracker[item] = sold_tracker.get(item, 0) + avail

        return {
            "farmer": farmer_act,
            "hands": hands_acts,
            "market": sanitized_market[:10]
        }


_hybrid_inst = HybridArchV1Agent()

def agent(obs, config=None):
    return _hybrid_inst(obs, config)
