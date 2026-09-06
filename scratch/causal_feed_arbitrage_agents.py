"""
Strict Causal Isolation Factorial Agents for Dynamic Feed Arbitrage.
Derived from frozen Aethel-Refined V2 baseline (candidates/slot2_aethel_refined_v2.py).
All treatments preserve the V2 impact-sorted market controller, terminal net, and core engine.
"""

import copy
import math
import candidates.slot2_aethel_refined_v2 as v2

_SELLABLE = v2._SELLABLE
_BASE_PRICE = v2._BASE_PRICE

class CausalAgent:
    def __init__(self, 
                 enable_dynamic_liquidation=False, 
                 enable_external_wheat=False, 
                 cow_target=8,
                 wheat_buy_threshold=40,
                 safe_wheat_buffer=20,
                 liquidation_cash_target=4000,
                 scheduled_liquidation_day=None):
        self.enable_dynamic_liquidation = enable_dynamic_liquidation
        self.enable_external_wheat = enable_external_wheat
        self.cow_target = cow_target
        self.wheat_buy_threshold = wheat_buy_threshold
        self.safe_wheat_buffer = safe_wheat_buffer
        self.liquidation_cash_target = liquidation_cash_target
        self.scheduled_liquidation_day = scheduled_liquidation_day
        
        self.q3_bought = False
        self.total_wheat_bought = 0
        self.last_step = -1

    def reset(self):
        self.q3_bought = False
        self.total_wheat_bought = 0
        self.last_step = -1

    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step
        
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", []) or []
        farm = farms[player] if len(farms) > player else {}
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", []) or []
        m_prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
        
        cows = sum(1 for row in farm.get("tiles", []) for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        
        # 1. Base action from V2
        if step >= v2._TERMINAL_START_STEP:
            return v2._terminal_action(obs)
            
        action = copy.deepcopy(v2._TRACE[min(step, len(v2._TRACE) - 1)])
        
        # If Q3 already unlocked, suppress redundant BUY_LAND from trace (e.g. at step 255)
        if len(quads) >= 3 or self.q3_bought:
            action["market"] = [order for order in action.get("market", []) if not (isinstance(order, list) and len(order) >= 1 and order[0] == "BUY_LAND")]
        
        # 2. Factor B: Dynamic Cash Liquidation / Early Q3
        if self.enable_dynamic_liquidation and len(quads) == 2 and not self.q3_bought and 168 <= step <= 250:
            if money >= self.liquidation_cash_target:
                if len(action.get("market", [])) < 10:
                    action.setdefault("market", []).append(["BUY_LAND"])
                    self.q3_bought = True
            else:
                eligible = ["MILK", "WOOL", "FERTILIZER", "STRAWBERRY", "MELON"]
                conservative_val = 0
                for item in eligible:
                    qty = int(shed.get(item, 0) or 0)
                    price = float(m_prices.get(item, _BASE_PRICE.get(item, 100))) * 0.90
                    conservative_val += qty * price
                
                if money + conservative_val >= self.liquidation_cash_target:
                    deficit = self.liquidation_cash_target - money
                    orders = action.setdefault("market", [])
                    already_selling = {o[1]: o[2] for o in orders if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL"}
                    
                    for item in eligible:
                        if deficit <= 0:
                            break
                        avail = int(shed.get(item, 0) or 0) - already_selling.get(item, 0)
                        if avail > 0:
                            price = max(1.0, float(m_prices.get(item, _BASE_PRICE.get(item, 100))) * 0.90)
                            units_needed = min(avail, int(math.ceil(deficit / price)))
                            if units_needed > 0 and len(orders) < 10:
                                orders.append(["SELL", item, units_needed])
                                deficit -= units_needed * price
                                
                    if deficit <= 0 and len(orders) < 10:
                        orders.append(["BUY_LAND"])
                        self.q3_bought = True

        # 2b. Scheduled Liquidation Day alternative
        if self.scheduled_liquidation_day is not None and len(quads) == 2 and not self.q3_bought:
            day = step // 24
            hour = step % 24
            if day == self.scheduled_liquidation_day and hour in [6, 7, 8]:
                orders = action.setdefault("market", [])
                for item in ["MILK", "WOOL", "FERTILIZER"]:
                    qty = int(shed.get(item, 0) or 0)
                    if qty > 0 and len(orders) < 10 and not any(o[0] == 'SELL' and o[1] == item for o in orders if isinstance(o, list)):
                        orders.append(["SELL", item, qty])
                if money >= self.liquidation_cash_target and len(orders) < 10:
                    orders.append(["BUY_LAND"])
                    self.q3_bought = True

        # 3. Factor C: External Wheat Feed Arbitrage
        if self.enable_external_wheat:
            wheat_count = int(shed.get("WHEAT", 0) or 0)
            wheat_price = float(m_prices.get("WHEAT", 30))
            if wheat_count < self.safe_wheat_buffer and wheat_price <= self.wheat_buy_threshold:
                orders = action.setdefault("market", [])
                if len(orders) < 10 and money >= wheat_price * 5:
                    buy_qty = min(15, max(5, self.safe_wheat_buffer - wheat_count))
                    if not any(isinstance(o, list) and len(o) >= 2 and o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT' for o in orders):
                        orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])
                        self.total_wheat_bought += buy_qty

        # 4. Factor D: Increased Cow Capacity
        if cows < self.cow_target and step >= 200 and money >= 1000 and (len(quads) >= 3 or self.q3_bought):
            orders = action.setdefault("market", [])
            pastures = sum(1 for row in farm.get("tiles", []) for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
            animals = sum(1 for row in farm.get("tiles", []) for t in row if isinstance(t, dict) and t.get("animal") in ["COW", "SHEEP"])
            if pastures > animals and len(orders) < 10:
                if not any(isinstance(o, list) and len(o) >= 2 and o[0] == 'BUY_ANIMAL' and o[1] == 'COW' for o in orders):
                    orders.append(["BUY_ANIMAL", "COW", 1])

        # Apply V2 overlays
        v2._front_run(action, obs, step)
        v2._terminal_liquidation(action, obs, step)
        
        # Apply V2 market-controller impact sorting
        try:
            orders = list(action.get("market") or [])
            keep = [
                order for order in orders
                if not (
                    isinstance(order, list) and len(order) >= 2
                    and order[0] == "SELL" and order[1] in v2._RESERVE
                )
            ]
            short = max(0.0, v2._cash_needed(keep, obs) - money)
            sells = v2._plan_sells(obs, step, 10 - len(keep), short)
            if not v2._SORT_SELLS:
                action["market"] = (sells + keep)[:10]
                return action

            def is_sell(o):
                return isinstance(o, list) and o and o[0] == "SELL"

            opp_money = None
            if v2._PROMOTE_IF_OPP_MONEY:
                farms_list = obs.get("farms") or []
                if len(farms_list) > 1:
                    opp_money = float(farms_list[1 - player].get("money", 0) or 0)

            def promotable(o):
                if not is_sell(o):
                    return False
                item = o[1]
                if item in v2._PROMOTE_IF_OPP_MONEY:
                    if opp_money is None:
                        return False
                    return opp_money >= v2._PROMOTE_IF_OPP_MONEY[item]
                if item in v2._PROMOTE_AFTER:
                    return step >= v2._PROMOTE_AFTER[item]
                return not v2._PROMOTE or item in v2._PROMOTE

            merged = [o for o in sells if promotable(o)] + [o for o in keep if promotable(o)]
            merged.sort(key=lambda o: -v2._sell_priority(o, obs, step))
            rest = [o for o in sells if not promotable(o)] + [o for o in keep if not promotable(o)]
            if v2._SELLS_FIRST:
                action["market"] = (merged + rest)[:10]
            else:
                out = []
                queue = list(merged)
                for order in keep:
                    out.append(queue.pop(0) if (promotable(order) and queue) else order)
                out.extend(queue)
                action["market"] = out[:10]
        except Exception:
            pass
            
        return action

# Factory instances for standard factorial arms A-H
agent_A = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=False, cow_target=8) # Base V2
agent_B = CausalAgent(enable_dynamic_liquidation=True,  enable_external_wheat=False, cow_target=8) # Dynamic Liq Only
agent_C = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=True,  cow_target=8) # External Wheat Only
agent_D8  = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=False, cow_target=8)
agent_D10 = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=False, cow_target=10) # Cows 10 Only
agent_D12 = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=False, cow_target=12) # Cows 12 Only
agent_D13 = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=False, cow_target=13) # Cows 13 Only

agent_E = CausalAgent(enable_dynamic_liquidation=True,  enable_external_wheat=True,  cow_target=8)  # Liq + Wheat
agent_F = CausalAgent(enable_dynamic_liquidation=True,  enable_external_wheat=False, cow_target=12) # Liq + Cows
agent_G = CausalAgent(enable_dynamic_liquidation=False, enable_external_wheat=True,  cow_target=12) # Wheat + Cows
agent_H = CausalAgent(enable_dynamic_liquidation=True,  enable_external_wheat=True,  cow_target=12) # All Three (Liq + Wheat + Cows)
agent_H13 = CausalAgent(enable_dynamic_liquidation=True, enable_external_wheat=True, cow_target=13) # All Three (13 cows)

agent_SchedD8 = CausalAgent(enable_dynamic_liquidation=False, scheduled_liquidation_day=8, cow_target=8)
