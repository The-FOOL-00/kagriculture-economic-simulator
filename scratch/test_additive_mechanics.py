"""
PHYSICALLY RIGOROUS ADDITIVE TOMATO TEST HARNESS
Tests additive tomato mechanics on a single seed under exact kagsim simulation:
1. SE_LAND mode (SE quadrant unlocked via BUY_LAND, dedicated worker).
2. VACANT_TILES mode (Day 12 vacant tiles in NW/NE/SW).
Measures exact costs, actions, harvests, sales, and paired cash delta vs V2 baseline.
"""
import os
import sys
import copy
from typing import Dict, List, Tuple, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2

def get_manhattan_path(start: Tuple[int, int], target: Tuple[int, int]) -> List[str]:
    moves = []
    sx, sy = start
    tx, ty = target
    while sx < tx:
        moves.append("EAST"); sx += 1
    while sx > tx:
        moves.append("WEST"); sx -= 1
    while sy < ty:
        moves.append("SOUTH"); sy += 1
    while sy > ty:
        moves.append("NORTH"); sy -= 1
    return moves

class AdditiveTomatoController:
    def __init__(
        self,
        k: int = 4,
        deploy_day: int = 12,
        land_mode: str = "SE_LAND", # "SE_LAND" or "VACANT_TILES"
        condition: str = "ALWAYS" # "ALWAYS", "PIZZA_PRESENT", "PIZZA_NO_STRAW"
    ):
        self.k = k
        self.deploy_day = deploy_day
        self.land_mode = land_mode
        self.condition = condition
        
        self.active = False
        self.decided = False
        self.target_tiles = []
        self.dedicated_hand_idx = None
        self.planted = False
        
        # Telemetry
        self.stats = {
            "seeds_bought": 0,
            "plants": 0,
            "waters": 0,
            "harvests": 0,
            "sales_count": 0,
            "sales_revenue": 0.0,
            "land_bought": False,
            "hires_added": 0
        }

    def evaluate_condition(self, obs: Dict[str, Any]) -> bool:
        if self.k == 0:
            return False
        shops = obs.get("town", {}).get("unlocked_shops", [])
        has_pizza = "PIZZA_SHOP" in shops
        straw_shops = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
        has_straw = any(s in straw_shops for s in shops)
        
        if self.condition == "ALWAYS":
            return True
        elif self.condition == "PIZZA_PRESENT":
            return has_pizza
        elif self.condition == "PIZZA_NO_STRAW":
            return has_pizza and not has_straw
        return False

    def apply(self, obs: Dict[str, Any], action: Dict[str, Any], agent: Any) -> Dict[str, Any]:
        step = int(obs["step"])
        day = step // 24
        hour = step % 24
        farm = obs["farms"][obs["player"]]
        private = obs["private"]
        
        # Decision point on deploy_day at hour 0
        if day == self.deploy_day and hour == 0 and not self.decided:
            self.decided = True
            self.active = self.evaluate_condition(obs)
            if self.active:
                if self.land_mode == "SE_LAND":
                    # Choose tiles in SE quadrant near shed: (5,5), (5,6), (6,5), (6,6), (5,7)...
                    se_candidates = [(5, 5), (5, 6), (6, 5), (6, 6), (5, 7), (6, 7), (7, 5), (7, 6), (7, 7), (8, 6)]
                    self.target_tiles = se_candidates[:self.k]
                elif self.land_mode == "VACANT_TILES":
                    # Find currently empty tiles
                    empties = []
                    for y in range(10):
                        for x in range(10):
                            if farm["tiles"][y][x] is None:
                                empties.append((x, y))
                    self.target_tiles = empties[:self.k]
                    if len(self.target_tiles) == 0:
                        self.active = False # No empty land available!

        if not self.active:
            return action

        market = action.get("market", [])
        
        # 1. Market Orders: Land & Seeds
        if day == self.deploy_day:
            if hour == 1:
                # Buy land if in SE_LAND mode and not yet unlocked
                if self.land_mode == "SE_LAND" and "SE" not in farm.get("unlocked_quadrants", []):
                    if len(market) < 10:
                        market.append(["BUY_LAND"])
                        self.stats["land_bought"] = True
                        
                # Buy tomato seeds
                if len(market) < 10 and self.stats["seeds_bought"] == 0:
                    market.append(["BUY_SEED", "TOMATO", len(self.target_tiles)])
                    self.stats["seeds_bought"] = len(self.target_tiles)
                    
        # 2. Worker Hiring: If in SE_LAND mode, hire 1 extra dedicated hand each day from deploy_day
        if self.land_mode == "SE_LAND" and day >= self.deploy_day:
            if hour == 1:
                # Add 1 HIRE order if slot available
                if len(market) < 10:
                    market.append(["HIRE"])
                    self.stats["hires_added"] += 1

        # 3. Market Orders: Selling Tomatoes
        # Check shed tomatoes
        shed_tom = private.get("shed", {}).get("TOMATO", 0)
        if shed_tom > 0 and (step % 4 == 1 or step == 718):
            has_tom_sell = any(m and m[0] == "SELL" and m[1] == "TOMATO" for m in market)
            if not has_tom_sell and len(market) < 10:
                sell_qty = min(shed_tom, 6)
                market.append(["SELL", "TOMATO", sell_qty])
                self.stats["sales_count"] += 1

        action["market"] = market[:10]

        # 4. Dedicated Hand Scheduling
        # In SE_LAND mode with extra hand:
        if self.land_mode == "SE_LAND" and day >= self.deploy_day:
            hands = action.get("hands", [])
            # The extra hand is the last hand in farm["hands"]
            # If the extra hand is present in the observation:
            n_hands_obs = len(farm.get("hands", []))
            if n_hands_obs > len(hands):
                # We control the extra hand(s)
                # Extra hand starts at shed access tile (5, 5)
                # Compute task for today:
                hand_action = ["PASS"]
                extra_idx = n_hands_obs - 1
                pos = farm["hands"][extra_idx]
                
                # Daily schedule for extra worker:
                # Hours 2 to 23:
                if day == self.deploy_day:
                    # Day of planting: visit each tile, PLANT, then WATER!
                    # Construct action sequence for the day
                    hand_action = self._plan_plant_and_water_day(pos, hour, farm, private)
                elif day < self.deploy_day + 8:
                    # Growth days: visit each tile, WATER!
                    hand_action = self._plan_water_day(pos, hour, farm)
                else:
                    # Yield days: visit each tile, HARVEST, then WATER!
                    hand_action = self._plan_harvest_and_water_day(pos, hour, farm)
                    
                # Append extra hand action
                while len(hands) < n_hands_obs:
                    hands.append(["PASS"])
                hands[extra_idx] = hand_action
                action["hands"] = hands

        return action

    def _plan_plant_and_water_day(self, pos: List[int], hour: int, farm: Dict[str, Any], private: Dict[str, Any]) -> List[str]:
        # Target tiles
        # Simple schedule: each tile gets ~3-4 hours
        # Order: tile 0, tile 1, ...
        # If hour < 2: PASS (hiring just happened)
        if hour < 2:
            return ["PASS"]
            
        cur = (pos[0], pos[1])
        # Find which tile needs planting or watering
        for t in self.target_tiles:
            tile_state = farm["tiles"][t[1]][t[0]]
            if tile_state is None:
                # Needs plant
                if cur == t:
                    self.stats["plants"] += 1
                    return ["PLANT", "TOMATO"]
                else:
                    moves = get_manhattan_path(cur, t)
                    if moves: return [moves[0]]
            elif isinstance(tile_state, dict) and tile_state.get("kind") == "PLANT":
                if not tile_state.get("watered_today", False):
                    # Needs water
                    if cur == t:
                        self.stats["waters"] += 1
                        return ["WATER"]
                    else:
                        moves = get_manhattan_path(cur, t)
                        if moves: return [moves[0]]
        return ["PASS"]

    def _plan_water_day(self, pos: List[int], hour: int, farm: Dict[str, Any]) -> List[str]:
        if hour < 2:
            return ["PASS"]
        cur = (pos[0], pos[1])
        for t in self.target_tiles:
            tile_state = farm["tiles"][t[1]][t[0]]
            if isinstance(tile_state, dict) and tile_state.get("kind") == "PLANT":
                if not tile_state.get("watered_today", False):
                    if cur == t:
                        self.stats["waters"] += 1
                        return ["WATER"]
                    else:
                        moves = get_manhattan_path(cur, t)
                        if moves: return [moves[0]]
        return ["PASS"]

    def _plan_harvest_and_water_day(self, pos: List[int], hour: int, farm: Dict[str, Any]) -> List[str]:
        if hour < 2:
            return ["PASS"]
        cur = (pos[0], pos[1])
        # 1. Harvest ready crops
        for t in self.target_tiles:
            tile_state = farm["tiles"][t[1]][t[0]]
            if isinstance(tile_state, dict) and tile_state.get("kind") == "PLANT":
                if tile_state.get("yield_units", 0) > 0:
                    if cur == t:
                        self.stats["harvests"] += 1
                        return ["HARVEST"]
                    else:
                        moves = get_manhattan_path(cur, t)
                        if moves: return [moves[0]]
                        
        # 2. Water unwatered crops
        for t in self.target_tiles:
            tile_state = farm["tiles"][t[1]][t[0]]
            if isinstance(tile_state, dict) and tile_state.get("kind") == "PLANT":
                if not tile_state.get("watered_today", False):
                    if cur == t:
                        self.stats["waters"] += 1
                        return ["WATER"]
                    else:
                        moves = get_manhattan_path(cur, t)
                        if moves: return [moves[0]]
                        
        # 3. Drop inventory if beside shed
        if cur in [(4,4), (4,5), (5,4), (5,5)]:
            return ["DROP"]
            
        return ["PASS"]

def test_single_seed(seed: int, k: int, deploy_day: int, land_mode: str):
    # Run Baseline V2
    g_base = kagsim.Game(seed)
    p0_base = ClosedLoopAgentV2()
    p1_base = ClosedLoopAgentV2()
    while not g_base.done:
        g_base.step(p0_base.act(g_base.observe(0)), p1_base.act(g_base.observe(1)))
    r_base = g_base.reward(0)
    
    # Run Candidate Additive Tomato Agent
    g_cand = kagsim.Game(seed)
    controller = AdditiveTomatoController(k=k, deploy_day=deploy_day, land_mode=land_mode, condition="ALWAYS")
    p0_cand = ClosedLoopAgentV2()
    p1_cand = ClosedLoopAgentV2()
    
    while not g_cand.done:
        obs0 = g_cand.observe(0)
        act0 = p0_cand.act(obs0)
        act0_mod = controller.apply(obs0, act0, p0_cand)
        g_cand.step(act0_mod, p1_cand.act(g_cand.observe(1)))
        
    r_cand = g_cand.reward(0)
    delta = r_cand - r_base
    
    print(f"Seed {seed} | k={k} | Deploy Day {deploy_day} | Land: {land_mode}")
    print(f"  Base V2 Cash:      ${r_base:.2f}")
    print(f"  Candidate Cash:    ${r_cand:.2f}")
    print(f"  Net Delta:         ${delta:+.2f}")
    print(f"  Stats:             {controller.stats}")
    return delta

if __name__ == "__main__":
    # Test on Seed 50003 (Pizza shop unlocked at Day 0!)
    test_single_seed(50003, k=4, deploy_day=12, land_mode="SE_LAND")
