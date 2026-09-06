"""
ARCH_BASE: Modular Experimental Architecture for Causal Architecture Decomposition.
Allows independent toggling of treatment flags T1 through T8.
Zero modifications to live Slot 1 or Slot 2.
"""

import copy
import json
import base64
import zlib
import math
import candidates.slot2_aethel_refined_v2 as v2

# Load V2 trace
_V2_TRACE = v2._TRACE

# Load Crop Dusta trace from replay Whyme_Labs_104824599.json (Player 1)
with open("scratch/replays/Whyme_Labs_104824599.json", "r", encoding="utf-8") as f:
    _replay_data = json.load(f)

_CD_TRACE = [s[1].get("action", {}) for s in _replay_data["steps"]]
if len(_CD_TRACE) < 720:
    _CD_TRACE.extend([{"farmer": ["PASS"], "hands": [], "market": []}] * (720 - len(_CD_TRACE)))

# Sellable items
_SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")
_BASE_PRICE = {"MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200, "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "EGG": 50, "FERTILIZER": 100}
_I0 = 10000
_PRICE_FLOOR = 1
_MP = v2._MP
_SHOP_DEMAND = v2._SHOP_DEMAND
_CENTER_ITEMS = v2._CENTER_ITEMS
_SUPPLY = v2._SUPPLY
_SUPPLY_DRIVER = v2._SUPPLY_DRIVER


class ArchBaseAgent:
    """
    Experimental Agent supporting binary treatment flags:
    T1: DAY0_SPATIAL_SCHEDULER (5 workers, 5 NW pastures, early melon/wheat)
    T2: FAST_Q2 (Unlock NE at Step 122 via Day 5 wheat + fertilizer liquidation)
    T3: MILK_HOLD_FAST_Q3 (Hold milk until Steps 198-200, liquidate 18 milk, unlock SW at Step 200)
    T4: PASTURE_16_LAYOUT (16 pastures: 5 NW, 8 NE, 3 SW vs 14 pastures)
    T5: HERD_13C_3S (13 cows, 3 sheep vs 8 cows, 6 sheep)
    T6: CASH_CROP_CONCENTRATION (59 cash crop tiles: Tomato/Strawberry/Melon vs wheat farming)
    T7: FEED_BUFFER (Active ~15-30 wheat feed buffer purchased from market)
    T8: V2_MARKET_CONTROLLER (Impact-sorted sells and dynamic promotion)
    """

    def __init__(self, flags=None):
        self.flags = {
            "T1": False,
            "T2": False,
            "T3": False,
            "T4": False,
            "T5": False,
            "T6": False,
            "T7": False,
            "T8": True,
        }
        if flags:
            self.flags.update(flags)
        self.last_step = -1
        self.activation_events = {f"T{i}": [] for i in range(1, 9)}
        self.held_milk = 0

    def reset(self):
        self.last_step = -1
        self.activation_events = {f"T{i}": [] for i in range(1, 9)}
        self.held_milk = 0

    def _get_base_action(self, obs, step):
        use_cd_spatial = (self.flags["T1"] and self.flags["T4"] and self.flags["T5"] and self.flags["T6"])
        
        if use_cd_spatial:
            action = copy.deepcopy(_CD_TRACE[step])
        elif not any([self.flags["T1"], self.flags["T2"], self.flags["T3"], self.flags["T4"], self.flags["T5"], self.flags["T6"]]):
            action = copy.deepcopy(_V2_TRACE[step])
        else:
            # Hybrid spatial dispatch
            if step < 122:
                if self.flags["T1"]:
                    action = copy.deepcopy(_CD_TRACE[step])
                    self.activation_events["T1"].append(step)
                else:
                    action = copy.deepcopy(_V2_TRACE[step])
            elif step < 198:
                if self.flags["T2"]:
                    action = copy.deepcopy(_CD_TRACE[step])
                    self.activation_events["T2"].append(step)
                else:
                    action = copy.deepcopy(_V2_TRACE[step])
            elif step < 256:
                if self.flags["T3"]:
                    action = copy.deepcopy(_CD_TRACE[step])
                    self.activation_events["T3"].append(step)
                else:
                    action = copy.deepcopy(_V2_TRACE[step])
            else:
                if self.flags["T4"] or self.flags["T5"] or self.flags["T6"]:
                    action = copy.deepcopy(_CD_TRACE[step])
                    if self.flags["T4"]: self.activation_events["T4"].append(step)
                    if self.flags["T5"]: self.activation_events["T5"].append(step)
                    if self.flags["T6"]: self.activation_events["T6"].append(step)
                else:
                    action = copy.deepcopy(_V2_TRACE[step])

        # Apply specific modular interventions:
        player = int(obs.get("player", 0) or 0)
        farm = (obs.get("farms") or [{}])[player]
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        money = float(farm.get("money", 0) or 0)
        market_orders = list(action.get("market") or [])

        # T2: FAST_Q2 override if T2 is ON but base trace was V2
        if self.flags["T2"] and not use_cd_spatial:
            if step == 121:
                wheat_qty = int(shed.get("WHEAT", 0) or 0)
                fert_qty = int(shed.get("FERTILIZER", 0) or 0)
                if wheat_qty > 0:
                    market_orders.insert(0, ["SELL", "WHEAT", wheat_qty])
                if fert_qty > 0:
                    market_orders.insert(0, ["SELL", "FERTILIZER", fert_qty])
                self.activation_events["T2"].append(step)
            elif step == 122:
                if "NE" not in (farm.get("unlocked_quadrants") or []):
                    market_orders.insert(0, ["BUY_LAND"])
                    self.activation_events["T2"].append(step)

        # T3: MILK_HOLD_FAST_Q3 override
        if self.flags["T3"]:
            if 120 <= step < 198:
                filtered = []
                for o in market_orders:
                    if isinstance(o, list) and len(o) >= 2 and o[0] == "SELL" and o[1] == "MILK":
                        self.activation_events["T3"].append(step)
                        continue
                    filtered.append(o)
                market_orders = filtered
            elif step in (198, 199):
                milk_qty = min(6, int(shed.get("MILK", 0) or 0))
                if milk_qty > 0:
                    market_orders.insert(0, ["SELL", "MILK", milk_qty])
                    self.activation_events["T3"].append(step)
            elif step == 200:
                milk_qty = min(6, int(shed.get("MILK", 0) or 0))
                if milk_qty > 0:
                    market_orders.insert(0, ["SELL", "MILK", milk_qty])
                if "SW" not in (farm.get("unlocked_quadrants") or []):
                    market_orders.append(["BUY_LAND"])
                    self.activation_events["T3"].append(step)

        # T7: FEED_BUFFER management
        if self.flags["T7"]:
            shed_wheat = int(shed.get("WHEAT", 0) or 0)
            if 48 <= step < 680:
                if shed_wheat < 15 and money >= 650:
                    already_buying = any(isinstance(o, list) and len(o) >= 2 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" for o in market_orders)
                    if not already_buying and len(market_orders) < 10:
                        buy_qty = min(15, 30 - shed_wheat)
                        market_orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])
                        self.activation_events["T7"].append(step)

        action["market"] = market_orders[:10]

        if step >= 712:
            return v2._terminal_action(obs)
        if step >= 680:
            v2._terminal_liquidation(action, obs, step)

        return action

    def __call__(self, obs, config=None):
        step = min(int(obs.get("step", 0) or 0), 719)
        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step

        action = self._get_base_action(obs, step)

        if not self.flags["T8"]:
            return action

        self.activation_events["T8"].append(step)
        try:
            if step >= 712:
                return action
            orders = list(action.get("market") or [])
            keep = [
                order for order in orders
                if not (
                    isinstance(order, list) and len(order) >= 2
                    and order[0] == "SELL" and order[1] in v2._RESERVE
                )
            ]
            player = int(obs.get("player", 0) or 0)
            money = float(((obs.get("farms") or [{}])[player]).get("money", 0) or 0)
            short = max(0.0, v2._cash_needed(keep, obs) - money)
            sells = v2._plan_sells(obs, step, 10 - len(keep), short)

            def is_sell(o):
                return isinstance(o, list) and o and o[0] == "SELL"

            opp_money = None
            if v2._PROMOTE_IF_OPP_MONEY:
                farms = obs.get("farms") or []
                if len(farms) > 1:
                    opp_money = float(farms[1 - player].get("money", 0) or 0)

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
            out = []
            queue = list(merged)
            for order in keep:
                out.append(queue.pop(0) if (promotable(order) and queue) else order)
            out.extend(queue)
            action["market"] = out[:10]
            return action
        except Exception:
            return action


def make_agent(flags):
    inst = ArchBaseAgent(flags)
    return lambda obs, cfg=None: inst(obs, cfg)
