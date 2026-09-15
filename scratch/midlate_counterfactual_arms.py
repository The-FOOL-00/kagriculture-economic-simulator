"""
scratch/midlate_counterfactual_arms.py
======================================
Wraps V54++ with local, causally isolated wheat-vs-livestock conversion controllers (Arms C0 through C9).
Preserves all other V54++ behaviors (open-loop macro schedule, shop controller, tactical overlays).
Uses strictly turn-available public observations.
"""

import os
import sys
import copy
import math
import numpy as np
from typing import Any, Dict, Optional

BASE_DIR = os.path.abspath(".")
V54PLUS_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")

if os.path.dirname(V54PLUS_PATH) not in sys.path:
    sys.path.insert(0, os.path.dirname(V54PLUS_PATH))

import importlib.util
spec = importlib.util.spec_from_file_location("v54plus_base", V54PLUS_PATH)
mod_v54plus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod_v54plus)
base_agent = mod_v54plus.agent

class MidLateConversionArm:
    def __init__(self, arm_id: str, seed_offset: int = 0):
        self.arm_id = arm_id
        self.seed_offset = seed_offset
        self.price_history = {0: {}, 1: {}}
        self.rng = np.random.RandomState(42 + seed_offset)
        
    def __call__(self, obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Get base action from frozen V54++
        action = base_agent(obs, configuration)
        
        if self.arm_id == "C0":
            return action
            
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)
            
        # Interventions only active in mid/late game (Steps 336-712)
        # Terminal overlays at 713-718 are strictly preserved
        if step < 336 or step > 712:
            return action
            
        seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
        market = obs.get("market", {}) or {}
        prices = market.get("prices", {}) or {}
        p_wheat = float(prices.get("WHEAT", 0.0))
        p_wool = float(prices.get("WOOL", 0.0))
        p_milk = float(prices.get("MILK", 0.0))
        
        # Track 24-step price history
        if step not in self.price_history[seat]:
            self.price_history[seat][step] = p_wheat
            
        priv = obs.get("private", {}) or {}
        shed = priv.get("shed", {}) or {}
        shed_wheat = int(shed.get("WHEAT", 0) or 0)
        
        cows = len(priv.get("cows", []))
        sheep = len(priv.get("sheep", []))
        livestock = cows + sheep
        feed_reserve = int(math.ceil(livestock * 1.5))
        excess_wheat = max(0, shed_wheat - feed_reserve)
        remaining_horizon = 720 - step
        
        mkt_orders = list(action.get("market", []) or [])
        
        should_sell_wheat = 0
        suppress_wheat_sell = False
        
        if self.arm_id == "C1":
            # C1: Force additional wheat liquidation during high wheat-price states
            if p_wheat >= 22.0 and excess_wheat >= 4:
                should_sell_wheat = min(excess_wheat, 8)
                
        elif self.arm_id == "C2":
            # C2: Force additional livestock conversion / wheat retention during high wool/milk states
            if p_wool >= 55.0 or p_milk >= 55.0:
                suppress_wheat_sell = True
                
        elif self.arm_id == "C3":
            # C3 (Rule R1): Price threshold only
            if p_wheat >= 24.0 and excess_wheat >= 4:
                should_sell_wheat = min(excess_wheat, 8)
                
        elif self.arm_id == "C4":
            # C4 (Rule R5): Price + Inventory
            if p_wheat >= 20.0 and shed_wheat >= 25:
                should_sell_wheat = min(shed_wheat - 12, 8)
                
        elif self.arm_id == "C5":
            # C5 (Rule R6): Price + Inventory + Livestock + Horizon
            # Compute total feed needed for rest of game
            total_feed_needed = livestock * max(1, remaining_horizon // 24)
            surplus = shed_wheat - total_feed_needed
            if surplus >= 4 and p_wheat >= 18.0:
                should_sell_wheat = min(surplus, 10)
            elif remaining_horizon <= 72 and excess_wheat >= 4 and p_wheat >= 16.0:
                should_sell_wheat = min(excess_wheat, 12)
                
        elif self.arm_id == "C6":
            # C6 (Rule R4): Price + Short Trend (Velocity)
            p_24_ago = self.price_history[seat].get(step - 24, p_wheat)
            price_delta = p_wheat - p_24_ago
            # If price is high but starting to fall (negative trend), sell before further drop
            if p_wheat >= 21.0 and price_delta < -1.0 and excess_wheat >= 4:
                should_sell_wheat = min(excess_wheat, 8)
                
        elif self.arm_id == "C7":
            # C7 (Rule R7): Full public-state relative conversion value
            # 1 wheat produces ~0.15 wool or 0.12 milk per step
            marginal_wool_val = p_wool * 0.15
            marginal_milk_val = p_milk * 0.12
            livestock_val = max(marginal_wool_val, marginal_milk_val)
            if p_wheat > livestock_val * 1.1 and excess_wheat >= 4:
                should_sell_wheat = min(excess_wheat, 8)
            elif livestock_val > p_wheat * 1.5:
                suppress_wheat_sell = True
                
        elif self.arm_id == "C8":
            # C8: Random decision control (matched ~20% frequency)
            if excess_wheat >= 4 and self.rng.rand() < 0.20:
                should_sell_wheat = min(excess_wheat, 8)
                
        elif self.arm_id == "C9":
            # C9: Deliberately inverted policy (sells when wheat price is low, hoards when high)
            if p_wheat < 14.0 and excess_wheat >= 4:
                should_sell_wheat = min(excess_wheat, 8)
            elif p_wheat >= 24.0:
                suppress_wheat_sell = True
                
        # Apply market order modifications
        if suppress_wheat_sell:
            new_mkt = []
            for ord in mkt_orders:
                if len(ord) >= 3 and ord[0] == "SELL" and ord[1] == "WHEAT":
                    continue
                new_mkt.append(ord)
            action["market"] = new_mkt
        elif should_sell_wheat > 0:
            # Check if there's already a SELL WHEAT order
            found = False
            for ord in mkt_orders:
                if len(ord) >= 3 and ord[0] == "SELL" and ord[1] == "WHEAT":
                    ord[2] = int(ord[2]) + should_sell_wheat
                    found = True
                    break
            if not found and len(mkt_orders) < 10:
                mkt_orders.append(["SELL", "WHEAT", should_sell_wheat])
            action["market"] = mkt_orders[:10]
            
        return action

def get_arm_agent(arm_id: str):
    return MidLateConversionArm(arm_id)
