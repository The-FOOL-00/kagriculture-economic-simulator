# SPDX-License-Identifier: MIT
"""Kagriculture V38 Macro Action Interface, Preconditions, and Deterministic Executors."""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from config import (
        MACRO_ACTIONS, NUM_MACRO_ACTIONS, MIN_LIQUID_CASH_BUFFER,
        PRODUCTS, SEED_PRICES, ANIMAL_COSTS, LAND_PRICES
    )
    from state_features import StateAbstraction
except ImportError:
    from candidates.v38_heuristic_ppo.config import (
        MACRO_ACTIONS, NUM_MACRO_ACTIONS, MIN_LIQUID_CASH_BUFFER,
        PRODUCTS, SEED_PRICES, ANIMAL_COSTS, LAND_PRICES
    )
    from candidates.v38_heuristic_ppo.state_features import StateAbstraction


def get_macro_action_mask(state: StateAbstraction) -> np.ndarray:
    """Computes boolean legality mask for all 11 macro actions."""
    mask = np.zeros(NUM_MACRO_ACTIONS, dtype=bool)
    
    econ = state.economic
    phys = state.physical
    cash = econ.cash
    step = econ.step
    
    # Action 0: TRUST_HEURISTIC is unconditionally legal (Bedrock)
    mask[0] = True
    
    # Action 1: EXPAND_LAND
    if phys.unlocked_quadrants < 4 and step < 480:
        if cash >= (econ.next_quadrant_cost + MIN_LIQUID_CASH_BUFFER):
            mask[1] = True
            
    # Action 2: HIRE_WORKER
    if phys.worker_count < 8 and step < 500 and (step % 24 == 0):
        if cash >= (econ.next_hire_cost + MIN_LIQUID_CASH_BUFFER):
            if (phys.empty_tiles + phys.weed_tiles) > (phys.worker_count * 2):
                mask[2] = True
                
    # Action 3: ANIMAL_EXPANSION (Cow)
    if phys.empty_pastures > 0 and step < 450 and econ.feed_runway_days >= 3.0:
        if cash >= (ANIMAL_COSTS["COW"] + MIN_LIQUID_CASH_BUFFER):
            mask[3] = True
            
    # Action 4: CROP_EXPANSION (Melon)
    if phys.empty_tiles > 0 and step < 450:
        if cash >= (SEED_PRICES["MELON"] + MIN_LIQUID_CASH_BUFFER):
            mask[4] = True
            
    # Action 5: SHOP_SUPPLY (Front-run Town consumption)
    if (step % 4 == 0) and step < 710:
        has_valuable_stock = any(
            econ.shed_inventory.get(p, 0) >= 2 and econ.spot_prices.get(p, 0) >= 20.0
            for p in ("MILK", "WOOL", "MELON", "STRAWBERRY")
        )
        if has_valuable_stock:
            mask[5] = True
            
    # Action 6: SELL_INVENTORY (General surplus liquidation)
    if step < 712:
        has_surplus = any(
            (econ.shed_inventory.get(p, 0) >= 4 and econ.spot_prices.get(p, 0) >= 15.0)
            for p in PRODUCTS if p != "WHEAT"
        )
        if has_surplus:
            mask[6] = True
            
    # Action 7: HOLD_INVENTORY (Speculative price rebound)
    if step < 650:
        depressed = any(
            econ.shed_inventory.get(p, 0) >= 2 and econ.price_deltas.get(p, 0.0) < -2.0
            for p in PRODUCTS
        )
        if depressed and sum(econ.shed_inventory.values()) < 75:
            mask[7] = True
            
    # Action 8: MARKET_OPPORTUNITY (Preemptive front-running)
    if step < 700:
        high_price = any(
            econ.shed_inventory.get(p, 0) >= 1 and econ.spot_prices.get(p, 0) >= 35.0
            for p in ("MILK", "WOOL", "MELON", "STRAWBERRY")
        )
        if high_price:
            mask[8] = True
            
    # Action 9: LIQUIDITY_PROTECT (Emergency cash buffer restoration)
    if econ.days_of_wage_runway < 2.0 and step < 680:
        mask[9] = True
        
    # Action 10: RECOVERY (Critical distress)
    if (cash < 50.0 or econ.days_of_wage_runway < 1.0 or phys.unfed_animals > 0) and step < 710:
        mask[10] = True
        
    return mask


def execute_macro_option(
    macro_option: int,
    base_action: Dict[str, Any],
    state: StateAbstraction,
    observation: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    """Executes a bounded macro option on top of the base action.
    
    Returns:
        (modified_action, success_flag)
    """
    if macro_option == 0:
        return base_action, True
        
    action = copy.deepcopy(base_action)
    mkt = list(action.get("market") or [])
    econ = state.economic
    phys = state.physical
    
    # 1. EXPAND_LAND
    if macro_option == 1:
        if phys.unlocked_quadrants < 4 and econ.cash >= (econ.next_quadrant_cost + MIN_LIQUID_CASH_BUFFER):
            if len(mkt) < 10 and not any(o and o[0] == "BUY_LAND" for o in mkt):
                mkt.append(["BUY_LAND"])
                action["market"] = mkt
                return action, True
                
    # 2. HIRE_WORKER
    elif macro_option == 2:
        if econ.cash >= (econ.next_hire_cost + MIN_LIQUID_CASH_BUFFER) and len(mkt) < 10:
            if not any(o and o[0] == "HIRE" for o in mkt):
                mkt.append(["HIRE"])
                action["market"] = mkt
                return action, True
                
    # 3. ANIMAL_EXPANSION (Cow)
    elif macro_option == 3:
        if econ.cash >= (ANIMAL_COSTS["COW"] + MIN_LIQUID_CASH_BUFFER) and phys.empty_pastures > 0:
            if len(mkt) < 10 and not any(o and o[0] == "BUY_ANIMAL" and o[1] == "COW" for o in mkt):
                mkt.append(["BUY_ANIMAL", "COW", 1])
                action["market"] = mkt
                return action, True
                
    # 4. CROP_EXPANSION (Melon seeds)
    elif macro_option == 4:
        avail_cash = econ.cash - MIN_LIQUID_CASH_BUFFER
        qty = min(4, int(avail_cash // SEED_PRICES["MELON"]))
        if qty > 0 and len(mkt) < 10:
            mkt.append(["BUY_SEED", "MELON", qty])
            action["market"] = mkt
            return action, True
            
    # 5. SHOP_SUPPLY (Front-run Town consumption)
    elif macro_option == 5:
        existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
        added = False
        for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY"):
            qty = econ.shed_inventory.get(prod, 0)
            if qty >= 2 and prod not in existing_sells and len(mkt) < 10:
                mkt.append(["SELL", prod, qty])
                added = True
        if added:
            action["market"] = mkt
            return action, True
            
    # 6. SELL_INVENTORY (Surplus liquidation)
    elif macro_option == 6:
        existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
        added = False
        for prod in PRODUCTS:
            if prod == "WHEAT":
                continue
            qty = econ.shed_inventory.get(prod, 0)
            if qty >= 4 and prod not in existing_sells and len(mkt) < 10:
                mkt.append(["SELL", prod, qty])
                added = True
        if added:
            action["market"] = mkt
            return action, True
            
    # 7. HOLD_INVENTORY (Suppresses planned non-critical sales)
    elif macro_option == 7:
        kept = []
        for o in mkt:
            if o and o[0] == "SELL" and len(o) >= 3:
                prod = o[1]
                # Hold if price dropped recently
                if econ.price_deltas.get(prod, 0.0) < -2.0 and econ.step < 680:
                    continue
            kept.append(o)
        action["market"] = kept
        return action, True
        
    # 8. MARKET_OPPORTUNITY (Targeted peak sell)
    elif macro_option == 8:
        existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
        added = False
        for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY"):
            qty = econ.shed_inventory.get(prod, 0)
            px = econ.spot_prices.get(prod, 0.0)
            if qty >= 1 and px >= 35.0 and prod not in existing_sells and len(mkt) < 10:
                mkt.append(["SELL", prod, qty])
                added = True
        if added:
            action["market"] = mkt
            return action, True
            
    # 9. LIQUIDITY_PROTECT (Cancel buys, fund cash buffer)
    elif macro_option == 9:
        # Strip speculative BUY orders
        kept = [o for o in mkt if o and o[0] == "SELL"]
        # Add high-value sales to reach safe cash
        existing_sells = {o[1] for o in kept if len(o) > 1}
        for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY", "CARROT"):
            qty = econ.shed_inventory.get(prod, 0)
            if qty > 0 and prod not in existing_sells and len(kept) < 10:
                kept.append(["SELL", prod, qty])
        action["market"] = kept
        return action, True
        
    # 10. RECOVERY (Emergency intervention)
    elif macro_option == 10:
        # Clear buys, sell all available surplus
        kept = []
        for prod in PRODUCTS:
            qty = econ.shed_inventory.get(prod, 0)
            if prod == "WHEAT":
                qty = max(0, qty - 5)  # Preserve minimal feed
            if qty > 0 and len(kept) < 10:
                kept.append(["SELL", prod, qty])
        action["market"] = kept
        return action, True
        
    return base_action, False
