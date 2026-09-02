"""
=============================================================================
LiveFlooder_V1: Replay-Derived Feedback-Driven Live-Meta Adversary
=============================================================================
"""

import math
import copy

_CROPS = {
    "WHEAT": {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
}

_ANIMALS = {
    "SHEEP": {"cost": 500, "structure": "PASTURE", "product": "WOOL"},
}

_SELLABLE = ["WOOL", "FERTILIZER", "WHEAT", "MILK", "EGG", "STRAWBERRY", "MELON", "CARROT", "TOMATO"]

def _lf_move_toward(start, target):
    sx, sy = start
    tx, ty = target
    if sx == tx and sy == ty:
        return ["PASS"]
    dx = tx - sx
    dy = ty - sy
    if abs(dx) > abs(dy):
        step_x = 1 if dx > 0 else -1
        return ["MOVE", "RIGHT" if step_x > 0 else "LEFT"]
    else:
        step_y = 1 if dy > 0 else -1
        return ["MOVE", "DOWN" if step_y > 0 else "UP"]

def agent(obs, config=None):
    player = int(obs.get("player", 0) or 0)
    farms = obs.get("farms", []) or []
    if len(farms) <= player:
        return {"farmer": ["PASS"], "hands": [], "market": []}
        
    farm = farms[player]
    private = obs.get("private", {}) or {}
    step = int(obs.get("step", 0) or 0)
    day = step // 24
    hour = step % 24
    
    tiles = farm.get("tiles", []) or []
    size = len(tiles)
    farmer_pos = farm.get("farmer", [0, 0])
    hands_pos = farm.get("hands", []) or []
    units = [farmer_pos] + hands_pos
    
    money = float(farm.get("money", 0) or 0)
    quads = farm.get("unlocked_quadrants", ["NW"]) or ["NW"]
    quad_count = len(quads)
    
    # 1. Market Orders:
    market_orders = []
    
    # Buy initial wheat seeds on Day 0
    if step == 0:
        market_orders.append(["BUY_SEED", "WHEAT", 20])
    
    # Check Hires (up to 12-14 workers)
    target_hands = 4 if day < 2 else (8 if day < 7 else (13 if day < 25 else 11))
    current_hands = len(hands_pos)
    if hour == 0 and current_hands < target_hands and money > 300:
        market_orders.append(["HIRE"])
        
    # Check Land Unlocks
    if quad_count == 1 and money >= 4000 and day >= 3:
        market_orders.append(["BUY_LAND", "NE"])
    elif quad_count == 2 and money >= 4000 and day >= 6:
        market_orders.append(["BUY_LAND", "SW"])
        
    # Check Animal Buys (Sheep)
    sheep_count = 0
    for r in tiles:
        for t in r:
            if isinstance(t, dict) and t.get("animal") == "SHEEP":
                sheep_count += 1
                
    if sheep_count < 8 and money >= 500 and day >= 4:
        market_orders.append(["BUY_ANIMAL", "SHEEP"])
        
    # Continuous blanket selling across all sellable items
    shed = private.get("shed", {}) or {}
    for item in _SELLABLE:
        qty = int(shed.get(item, 0) or 0)
        if qty > 0:
            market_orders.append(["SELL", item, qty])
        
    # 2. Worker / Farmer Unit Actions:
    actions = []
    
    shed_tiles = []
    pasture_tiles = []
    tillable_tiles = []
    harvestable_tiles = []
    fertilizer_tiles = []
    
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "SHED":
                shed_tiles.append((x, y))
            elif kind == "PASTURE" or tile.get("animal") == "SHEEP":
                pasture_tiles.append((x, y))
            elif tile.get("fertilizer_available"):
                fertilizer_tiles.append((x, y))
            elif int(tile.get("yield_units", 0) or 0) > 0:
                harvestable_tiles.append((x, y))
            elif kind == "SOIL" and not tile.get("crop") and not tile.get("animal"):
                tillable_tiles.append((x, y))
                
    inventories = list(private.get("inventories") or [])
    while len(inventories) < len(units):
        inventories.append({})
        
    for u_idx, (pos, inv) in enumerate(zip(units, inventories)):
        x, y = pos[0], pos[1]
        load = sum(int(v or 0) for v in (inv or {}).values())
        tile = tiles[y][x] if 0 <= y < size and 0 <= x < size else {}
        
        # Priority 1: Drop if loaded and at shed
        if load > 0 and (x, y) in shed_tiles:
            actions.append(["DROP"])
            continue
            
        # Priority 2: Move to shed if heavily loaded
        if load >= 8 and shed_tiles:
            target = min(shed_tiles, key=lambda s: abs(s[0] - x) + abs(s[1] - y))
            actions.append(_lf_move_toward((x, y), target))
            continue
            
        # Priority 3: Collect fertilizer if on tile
        if isinstance(tile, dict) and tile.get("fertilizer_available"):
            actions.append(["COLLECT_FERTILIZER"])
            continue
            
        # Priority 4: Harvest if crop ready on tile
        if isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0:
            actions.append(["HARVEST"])
            continue
            
        # Priority 5: Shear sheep / collect wool if on sheep pasture tile
        if isinstance(tile, dict) and tile.get("animal") == "SHEEP" and tile.get("product_available"):
            actions.append(["COLLECT_PRODUCT"])
            continue
            
        # Priority 6: Move to nearest pasture/fertilizer/harvest tile
        targets = pasture_tiles + fertilizer_tiles + harvestable_tiles
        if targets:
            target = min(targets, key=lambda t: abs(t[0] - x) + abs(t[1] - y))
            actions.append(_lf_move_toward((x, y), target))
            continue
            
        # Priority 7: Plant Wheat if on tillable soil and day < 20
        if isinstance(tile, dict) and tile.get("kind") == "SOIL" and not tile.get("crop") and day < 20:
            actions.append(["PLANT", "WHEAT"])
            continue
            
        actions.append(["PASS"])
        
    return {
        "farmer": actions[0] if actions else ["PASS"],
        "hands": actions[1:] if len(actions) > 1 else [],
        "market": market_orders[:10]
    }
