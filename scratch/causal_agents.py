"""
=============================================================================
CAUSAL ISOLATION AGENT FACTORIAL SUITE
=============================================================================
Strictly isolated experimental treatments derived from frozen Aethel V2.
Every treatment alters EXACTLY ONE causal dimension while holding all other
dimensions 100% bitwise identical to the frozen V2 baseline.
=============================================================================
"""

import copy
import candidates.slot2_aethel_refined_v2 as v2

_BASE_TRACE = v2._TRACE
_SELLABLE = v2._SELLABLE

# ---------------------------------------------------------------------------
# BASELINE: Frozen Aethel V2
# ---------------------------------------------------------------------------
def agent_base(obs, config=None):
    return v2.agent(obs, config)


# ---------------------------------------------------------------------------
# TREATMENT 1: Q3 LAND VELOCITY ONLY
# ---------------------------------------------------------------------------
# Rule: At Turn 216 (Day 9, Hour 0), if money >= 4000 and Q3 is locked,
# purchase Q3 immediately. Suppress the baseline Turn 255 Q3 purchase if
# early Q3 was executed.
# NO changes to crops, livestock, workers, market, terminal, shop logic.
# ---------------------------------------------------------------------------
_Q3_STATE = {}

def agent_q3_only(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    
    # Reset per-game state on step 0
    if step == 0:
        _Q3_STATE[player] = {"early_q3_bought": False, "t216_satisfied": False, "actual_q3_step": None}
    
    state = _Q3_STATE.setdefault(player, {"early_q3_bought": False, "t216_satisfied": False, "actual_q3_step": None})
    farms = obs.get("farms", []) or []
    if len(farms) <= player:
        return v2.agent(obs, config)
    
    farm = farms[player]
    money = float(farm.get("money", 0) or 0)
    quads = farm.get("unlocked_quadrants", []) or []
    
    # Check at Turn 216
    if step == 216:
        if money >= 4000 and len(quads) < 3:
            state["t216_satisfied"] = True
            state["early_q3_bought"] = True
            state["actual_q3_step"] = 216
        else:
            state["t216_satisfied"] = False
            
    # Base action from V2
    action = v2.agent(obs, config)
    market = list(action.get("market", []) or [])
    
    if step == 216 and state["early_q3_bought"]:
        # Insert BUY_LAND
        market = [["BUY_LAND"]] + [o for o in market if o and o[0] != "BUY_LAND"]
        action["market"] = market[:10]
    elif step == 255 and state["early_q3_bought"]:
        # Suppress redundant BUY_LAND at 255
        market = [o for o in market if not (isinstance(o, list) and len(o) > 0 and o[0] == "BUY_LAND")]
        action["market"] = market[:10]
    elif step == 255 and not state["early_q3_bought"]:
        if len(quads) < 3:
            state["actual_q3_step"] = 255
            
    return action


# ---------------------------------------------------------------------------
# TREATMENT 2: SHOP SYNCHRONIZATION ONLY
# ---------------------------------------------------------------------------
# Rule: Keep Q3 timing at T255. Keep livestock at 8C/6S.
# Observe town unlocked_shops at Turn 72 (Day 3) and Turn 144 (Day 6).
# If town unlocked shops demand Wheat/Tomato and lack Strawberry/Melon demand,
# synchronize tillable planting on Day 6+ to the shop-demanded crop.
# ---------------------------------------------------------------------------
_SHOP_STATE = {}

def agent_shop_only(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    
    if step == 0:
        _SHOP_STATE[player] = {"synced_crop": None, "observed_shops": []}
        
    state = _SHOP_STATE.setdefault(player, {"synced_crop": None, "observed_shops": []})
    
    if step in (72, 144):
        shops = (obs.get("town") or {}).get("unlocked_shops") or []
        state["observed_shops"] = list(shops)
        
        # Check demand profile
        has_wheat_demand = any(s in ("PIZZA_SHOP", "BAKERY", "FARMERS_MARKET") for s in shops)
        has_tomato_demand = any(s in ("PIZZA_SHOP", "FARMERS_MARKET") for s in shops)
        has_berry_demand = any(s in ("SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "FARMERS_MARKET", "BRUNCH_SPOT") for s in shops)
        
        if (has_wheat_demand or has_tomato_demand) and not has_berry_demand:
            state["synced_crop"] = "TOMATO" if has_tomato_demand else "WHEAT"
        else:
            state["synced_crop"] = None  # Default Strawberry/Melon
            
    action = v2.agent(obs, config)
    
    # If a shop-synchronized crop is selected, adjust planting actions for farmer/hands
    target_crop = state["synced_crop"]
    if target_crop and step >= 144 and step < 680:
        # Check farmer and hands actions for PLANT STRAWBERRY or PLANT MELON
        for role in ["farmer", "hands"]:
            acts = action.get(role, [])
            if role == "farmer":
                if acts and isinstance(acts, list) and len(acts) >= 2 and acts[0] == "PLANT":
                    if acts[1] in ("STRAWBERRY", "MELON"):
                        action["farmer"] = ["PLANT", target_crop]
            else:
                new_hands = []
                for h_act in acts:
                    if h_act and isinstance(h_act, list) and len(h_act) >= 2 and h_act[0] == "PLANT":
                        if h_act[1] in ("STRAWBERRY", "MELON"):
                            new_hands.append(["PLANT", target_crop])
                        else:
                            new_hands.append(h_act)
                    else:
                        new_hands.append(h_act)
                action["hands"] = new_hands
                
        # Also adjust BUY_SEED in market orders
        market = []
        for o in action.get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED":
                if o[1] in ("STRAWBERRY", "MELON"):
                    market.append(["BUY_SEED", target_crop, o[2]])
                else:
                    market.append(o)
            else:
                market.append(o)
        action["market"] = market[:10]
        
    return action


# ---------------------------------------------------------------------------
# TREATMENT 3: DYNAMIC LIVESTOCK SPECIALIZATION ONLY
# ---------------------------------------------------------------------------
# Rule: Keep Q3 timing at T255. Keep crop planting at Strawberry/Melon.
# Observe town unlocked_shops at Turn 72 (Day 3).
# Explicit branching rule:
# - Cow Branch (12C / 2S): If Milk shops (ICE_CREAM_SHOP, PIZZA_SHOP) present and NO YARN_STORE.
# - Sheep Branch (4C / 12S): If YARN_STORE present.
# - Balanced (8C / 6S): Otherwise (default).
# ---------------------------------------------------------------------------
_LS_STATE = {}

def agent_livestock_only(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    
    if step == 0:
        _LS_STATE[player] = {"branch": "BALANCED", "observed_shops": []}
        
    state = _LS_STATE.setdefault(player, {"branch": "BALANCED", "observed_shops": []})
    
    if step == 72:
        shops = (obs.get("town") or {}).get("unlocked_shops") or []
        state["observed_shops"] = list(shops)
        
        has_milk = any(s in ("ICE_CREAM_SHOP", "PIZZA_SHOP", "SMOOTHIE_SHOP") for s in shops)
        has_wool = any(s in ("YARN_STORE",) for s in shops)
        
        if has_wool and not has_milk:
            state["branch"] = "SHEEP_FOCUS"
        elif has_milk and not has_wool:
            state["branch"] = "COW_FOCUS"
        elif has_wool and has_milk:
            state["branch"] = "SHEEP_FOCUS" if "YARN_STORE" in shops else "COW_FOCUS"
        else:
            state["branch"] = "BALANCED"
            
    action = v2.agent(obs, config)
    branch = state["branch"]
    
    # Adjust animal purchases in market orders based on chosen branch
    if branch != "BALANCED" and step >= 72 and step <= 300:
        market = []
        for o in action.get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL":
                animal = o[1]
                qty = o[2]
                if branch == "COW_FOCUS":
                    # Convert sheep buys to cow buys
                    market.append(["BUY_ANIMAL", "COW", qty])
                elif branch == "SHEEP_FOCUS":
                    # Convert cow buys to sheep buys
                    market.append(["BUY_ANIMAL", "SHEEP", qty])
                else:
                    market.append(o)
            else:
                market.append(o)
        action["market"] = market[:10]
        
    return action


# ---------------------------------------------------------------------------
# FACTORIAL COMBINATIONS
# ---------------------------------------------------------------------------

# Combination 1: Q3 + Shop
def agent_q3_shop(obs, config=None):
    # Apply Q3 velocity + Shop sync
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    
    if step == 0:
        _Q3_STATE[player] = {"early_q3_bought": False, "t216_satisfied": False, "actual_q3_step": None}
        _SHOP_STATE[player] = {"synced_crop": None, "observed_shops": []}
        
    # Get shop synced action
    action = agent_shop_only(obs, config)
    
    # Apply Q3 early buy overlay
    farms = obs.get("farms", []) or []
    if len(farms) > player:
        farm = farms[player]
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", []) or []
        state_q3 = _Q3_STATE[player]
        
        if step == 216:
            if money >= 4000 and len(quads) < 3:
                state_q3["early_q3_bought"] = True
                state_q3["t216_satisfied"] = True
                
        market = list(action.get("market", []) or [])
        if step == 216 and state_q3["early_q3_bought"]:
            market = [["BUY_LAND"]] + [o for o in market if o and o[0] != "BUY_LAND"]
            action["market"] = market[:10]
        elif step == 255 and state_q3["early_q3_bought"]:
            market = [o for o in market if not (isinstance(o, list) and len(o) > 0 and o[0] == "BUY_LAND")]
            action["market"] = market[:10]
            
    return action


# Combination 2: Q3 + Livestock
def agent_q3_livestock(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    
    if step == 0:
        _Q3_STATE[player] = {"early_q3_bought": False, "t216_satisfied": False, "actual_q3_step": None}
        _LS_STATE[player] = {"branch": "BALANCED", "observed_shops": []}
        
    action = agent_livestock_only(obs, config)
    
    farms = obs.get("farms", []) or []
    if len(farms) > player:
        farm = farms[player]
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", []) or []
        state_q3 = _Q3_STATE[player]
        
        if step == 216:
            if money >= 4000 and len(quads) < 3:
                state_q3["early_q3_bought"] = True
                state_q3["t216_satisfied"] = True
                
        market = list(action.get("market", []) or [])
        if step == 216 and state_q3["early_q3_bought"]:
            market = [["BUY_LAND"]] + [o for o in market if o and o[0] != "BUY_LAND"]
            action["market"] = market[:10]
        elif step == 255 and state_q3["early_q3_bought"]:
            market = [o for o in market if not (isinstance(o, list) and len(o) > 0 and o[0] == "BUY_LAND")]
            action["market"] = market[:10]
            
    return action


# Combination 3: Shop + Livestock
def agent_shop_livestock(obs, config=None):
    # Apply both Shop sync and Livestock specialization on top of V2
    action = agent_shop_only(obs, config)
    
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    state_ls = _LS_STATE.get(player, {"branch": "BALANCED"})
    branch = state_ls.get("branch", "BALANCED")
    
    if branch != "BALANCED" and step >= 72 and step <= 300:
        market = []
        for o in action.get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL":
                animal = o[1]
                qty = o[2]
                if branch == "COW_FOCUS":
                    market.append(["BUY_ANIMAL", "COW", qty])
                elif branch == "SHEEP_FOCUS":
                    market.append(["BUY_ANIMAL", "SHEEP", qty])
                else:
                    market.append(o)
            else:
                market.append(o)
        action["market"] = market[:10]
        
    return action


# Combination 4: Q3 + Shop + Livestock (Full Factorial)
def agent_full_factorial(obs, config=None):
    action = agent_shop_livestock(obs, config)
    
    step = int(obs.get("step", 0) or 0)
    player = int(obs.get("player", 0) or 0)
    farms = obs.get("farms", []) or []
    if len(farms) > player:
        farm = farms[player]
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", []) or []
        state_q3 = _Q3_STATE.setdefault(player, {"early_q3_bought": False, "t216_satisfied": False, "actual_q3_step": None})
        
        if step == 216:
            if money >= 4000 and len(quads) < 3:
                state_q3["early_q3_bought"] = True
                state_q3["t216_satisfied"] = True
                
        market = list(action.get("market", []) or [])
        if step == 216 and state_q3["early_q3_bought"]:
            market = [["BUY_LAND"]] + [o for o in market if o and o[0] != "BUY_LAND"]
            action["market"] = market[:10]
        elif step == 255 and state_q3["early_q3_bought"]:
            market = [o for o in market if not (isinstance(o, list) and len(o) > 0 and o[0] == "BUY_LAND")]
            action["market"] = market[:10]
            
    return action
