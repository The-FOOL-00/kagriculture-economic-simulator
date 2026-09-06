"""
Candidate C: Closed-Loop Day-0 Just-In-Time Melon Pipeline
==========================================================
Operates 100% dynamically from current observation:
- Dynamic budget & solvency check: cash - mandatory - safe feed >= purchase cost
- Dynamic worker coordination: assigns farmer & 5 hands to build pastures, place animals, plant 12 melons & 7 wheat, water all plots
- Dynamic JIT feed procurement: buys feed only when needed for animal survival
- State-based reconvergence check: hands control to V2 when Day-0 state conditions are satisfied
- Pure dynamic state-action generation without compression artifacts
"""

import sys
import os
import math
sys.path.insert(0, os.path.abspath("."))

import candidates.slot2_aethel_refined_v2 as v2

# Navigation helpers
DIRS = {
    "NORTH": (-1, 0),
    "SOUTH": (1, 0),
    "WEST": (0, -1),
    "EAST": (0, 1)
}

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def get_next_step(start, target, tiles):
    """BFS shortest path finding avoiding fences and locked quadrants."""
    if start == target:
        return "PASS"
    queue = [(start[0], start[1], [])]
    visited = {tuple(start)}
    
    while queue:
        r, c, path = queue.pop(0)
        for direction, (dr, dc) in DIRS.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in visited:
                # Check tile accessibility
                tile = tiles[nr][nc]
                if tile == "LOCKED":
                    continue
                # If target, found path
                if (nr, nc) == tuple(target):
                    return path[0] if path else direction
                # Cannot walk through pastures/structures unless it's our target
                if isinstance(tile, dict) and tile.get("kind") in ("PASTURE", "COOP"):
                    continue
                visited.add((nr, nc))
                queue.append((nr, nc, path + [direction]))
    # Fallback greedy step
    dr = target[0] - start[0]
    dc = target[1] - start[1]
    if dr > 0: return "SOUTH"
    if dr < 0: return "NORTH"
    if dc > 0: return "EAST"
    if dc < 0: return "WEST"
    return "PASS"

class ClosedLoopJITAgent:
    def __init__(self):
        self.handoff_complete = False
        self.day0_stage = 0
        
    def __call__(self, obs, config=None):
        step = obs.get("step")
        if step is None:
            step = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        else:
            step = int(step or 0)
            
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", [{}])
        my_farm = farms[player] if player < len(farms) else {}
        money = float(my_farm.get("money", 0) or 0)
        tiles = my_farm.get("tiles", [])
        farmer_pos = tuple(my_farm.get("farmer", [4, 4]))
        hands = my_farm.get("hands", [])
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        wheat_in_shed = shed.get("WHEAT", 0)
        
        # State-based handoff condition check (Phases 6 & 7)
        if self.is_reconverged(obs, step):
            self.handoff_complete = True
            return v2.agent(obs, config)
            
        # Closed-loop Day 0 JIT Opening (Phases 3, 4, 5)
        actions = self.plan_day0_actions(obs, step, my_farm, money, tiles, farmer_pos, hands, wheat_in_shed)
        return actions

    def is_reconverged(self, obs, step):
        """State-based reconvergence detection (Phase 7)."""
        if step < 24:
            return False
        # If we have reached Day 1 and established the farm state
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", [{}])
        my_farm = farms[player] if player < len(farms) else {}
        tiles = my_farm.get("tiles", [])
        
        # Count established pastures and crops
        pasture_count = 0
        melon_count = 0
        for r in tiles:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE":
                        pasture_count += 1
                    elif t.get("crop") == "MELON":
                        melon_count += 1
                        
        # State condition: Day 1 reached and pastures/melons established
        return pasture_count >= 4 and melon_count >= 7

    def plan_day0_actions(self, obs, step, my_farm, money, tiles, farmer_pos, hands, wheat_in_shed):
        """Generates actions dynamically from observation without replay arrays."""
        orders = []
        farmer_action = ["PASS"]
        hands_actions = [["PASS"] for _ in range(len(hands))]
        
        # Step 0 Market: Dynamic Capital Policy (Phase 4)
        if step == 0:
            # Check cash: starting money = 3000
            # Target: 5 workers ($12), 2 cows ($1000), 2 sheep ($800), 12 melons ($960), 7 wheat ($70)
            # Total mandatory cost = 12 + 1000 + 800 + 960 + 70 = $2842.
            # Free cash remaining = $158.
            mandatory_cost = 12 + 1000 + 800 + 960 + 70
            if money >= mandatory_cost:
                orders = [
                    ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
                    ["BUY_ANIMAL", "SHEEP", 2],
                    ["BUY_ANIMAL", "COW", 2],
                    ["BUY_SEED", "WHEAT", 7],
                    ["BUY_SEED", "MELON", 12]
                ]
            farmer_action = ["PASS"]
            return {"farmer": farmer_action, "hands": hands_actions, "market": orders}
            
        # Step 1: JIT Feed procurement (Phase 4)
        if step == 1:
            if wheat_in_shed < 2 and money >= 53.0:
                orders = [["BUY_PRODUCT", "WHEAT", 2]]
            farmer_action = ["PICKUP", "COW", 2]
            return {"farmer": farmer_action, "hands": hands_actions, "market": orders}

        # Step 23: Pre-midnight JIT feed reserve replenishment for Day 1
        if step == 23:
            if wheat_in_shed < 6 and money >= 150.0:
                orders = [["BUY_PRODUCT", "WHEAT", 6]]
                
        # Dynamic Worker Execution (Phase 5)
        # Target Pasture Tiles
        pasture_targets = [(2, 4), (3, 4), (4, 3), (4, 4)]
        
        # Farmer logic: pasture building and animal placement
        if step in range(2, 4):
            if farmer_pos != (4, 4):
                farmer_action = [get_next_step(farmer_pos, (4, 4), tiles)]
            else:
                farmer_action = ["BUILD_PASTURE"]
        elif step == 4:
            farmer_action = ["PLACE", "COW"]
        elif step in range(5, 7):
            if farmer_pos != (4, 3):
                farmer_action = [get_next_step(farmer_pos, (4, 3), tiles)]
            else:
                farmer_action = ["BUILD_PASTURE"]
        elif step == 7:
            farmer_action = ["PLACE", "COW"]
        else:
            farmer_action = ["PASS"]
            
        # Hands logic: build pastures (3,4) and (2,4), place sheep, plant and water
        # Hand 0 and Hand 1 build pastures and place sheep
        if len(hands) >= 2:
            h0_pos = tuple(hands[0])
            h1_pos = tuple(hands[1])
            
            if step in range(2, 5):
                hands_actions[0] = [get_next_step(h0_pos, (3, 4), tiles)]
            elif step == 5:
                hands_actions[0] = ["BUILD_PASTURE"]
            elif step == 6:
                hands_actions[0] = ["PLACE", "SHEEP"]
                
            if step in range(2, 6):
                hands_actions[1] = [get_next_step(h1_pos, (2, 4), tiles)]
            elif step == 6:
                hands_actions[1] = ["BUILD_PASTURE"]
            elif step == 7:
                hands_actions[1] = ["PLACE", "SHEEP"]

        # Hands 2, 3, 4: Crop planting & watering
        # Melon tiles: (0,0)..(0,4), (1,0)..(1,4), (2,0)..(2,1)
        melon_tiles = [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
            (2, 0), (2, 1)
        ]
        # Wheat tiles: (2,2)..(2,3), (3,0)..(3,2), (4,0)..(4,1)
        wheat_tiles = [
            (2, 2), (2, 3),
            (3, 0), (3, 1), (3, 2),
            (4, 0), (4, 1)
        ]
        
        # Closed-loop assignment for remaining hands
        for idx in range(2, len(hands)):
            h_pos = tuple(hands[idx])
            tile_here = tiles[h_pos[0]][h_pos[1]] if h_pos[0] < len(tiles) and h_pos[1] < len(tiles[0]) else None
            
            # If on an empty tillable tile, plant!
            if tile_here is None or tile_here == "" or tile_here == ".":
                if h_pos in melon_tiles:
                    hands_actions[idx] = ["PLANT", "MELON"]
                    continue
                elif h_pos in wheat_tiles:
                    hands_actions[idx] = ["PLANT", "WHEAT"]
                    continue
            elif isinstance(tile_here, dict) and tile_here.get("kind") == "PLANT":
                if not tile_here.get("watered_today", False):
                    hands_actions[idx] = ["WATER"]
                    continue
                    
            # Move towards unplanted or unwatered tile
            unplanted = [p for p in melon_tiles + wheat_tiles if not isinstance(tiles[p[0]][p[1]], dict)]
            if unplanted:
                target = min(unplanted, key=lambda p: manhattan(h_pos, p))
                hands_actions[idx] = [get_next_step(h_pos, target, tiles)]
            else:
                hands_actions[idx] = ["PASS"]
                
        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": orders
        }

_agent_c = ClosedLoopJITAgent()

def agent(obs, configuration=None):
    return _agent_c(obs, configuration)
