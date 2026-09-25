# SPDX-License-Identifier: MIT
"""
Terminal State Extractor and Realizable Value Accounting.
Models exact physical reachability and prevents stranding of existing or new cargo.
"""
from typing import Dict, List, Tuple, Optional, Any

SHED_ACCESS_TILES_10 = [(4, 4), (5, 4), (4, 5), (5, 5)]

def manhattan_dist(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def dist_to_shed(pos: Tuple[int, int]) -> int:
    return min(manhattan_dist(pos, s) for s in SHED_ACCESS_TILES_10)

def nearest_shed_tile(pos: Tuple[int, int]) -> Tuple[int, int]:
    return min(SHED_ACCESS_TILES_10, key=lambda s: manhattan_dist(pos, s))

def is_shed_adjacent(pos: Tuple[int, int]) -> bool:
    return (pos[0], pos[1]) in SHED_ACCESS_TILES_10

class TerminalState:
    def __init__(self, obs: Dict[str, Any], seat: int = 0):
        self.step = obs.get("step", 0)
        self.seat = seat
        self.farm = obs["farms"][seat]
        self.private = obs["private"]
        self.market = obs["market"]
        self.prices = self.market.get("prices", {})
        
        self.money = float(self.farm.get("money", 0.0))
        self.shed = dict(self.private.get("shed", {}))
        
        # Worker positions
        farmer_pos = self.farm.get("farmer", [4, 5])
        self.farmer_pos = (farmer_pos[0], farmer_pos[1])
        self.hands_pos = [(h[0], h[1]) for h in self.farm.get("hands", [])]
        self.worker_positions = [self.farmer_pos] + self.hands_pos
        self.worker_inventories = [dict(inv) for inv in self.private.get("inventories", [])]
        
    def worker_has_cargo(self, worker_idx: int) -> bool:
        if worker_idx < len(self.worker_inventories):
            return any(v > 0 for v in self.worker_inventories[worker_idx].values())
        return False

    def worker_cargo_value(self, worker_idx: int) -> float:
        if worker_idx >= len(self.worker_inventories):
            return 0.0
        val = 0.0
        for item, count in self.worker_inventories[worker_idx].items():
            if count > 0:
                val += count * self.prices.get(item, 1.0)
        return val

    def get_realizable_targets(self, max_step: int = 718) -> List[Dict[str, Any]]:
        """
        Identifies all physical targets on the map with yield or fertilizer.
        For each, calculates exact time to harvest and drop into shed.
        """
        remaining_steps = max_step - self.step
        targets = []
        tiles = self.farm.get("tiles", [])
        
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                t = tiles[y][x]
                if not isinstance(t, dict):
                    continue
                
                y_u = t.get("yield_units", 0)
                fert = t.get("fertilizer_available", False)
                kind = t.get("kind")
                crop = t.get("crop")
                animal = t.get("animal")
                
                item_name = None
                qty = 0
                action_op = None
                
                if y_u > 0:
                    action_op = "HARVEST"
                    if kind == "PLANT":
                        item_name = crop
                        qty = y_u
                    elif animal == "COW":
                        item_name = "MILK"
                        qty = y_u
                    elif animal == "SHEEP":
                        item_name = "WOOL"
                        qty = y_u
                    elif animal == "GOOSE":
                        item_name = "EGG"
                        qty = y_u
                elif fert:
                    action_op = "COLLECT_FERTILIZER"
                    item_name = "FERTILIZER"
                    qty = 1
                    
                if item_name and qty > 0:
                    unit_price = self.prices.get(item_name, 1.0)
                    gross_val = qty * unit_price
                    d_shed = dist_to_shed((x, y))
                    targets.append({
                        "pos": (x, y),
                        "item": item_name,
                        "qty": qty,
                        "op": action_op,
                        "unit_price": unit_price,
                        "gross_val": gross_val,
                        "dist_to_shed": d_shed,
                        # Minimum steps from target to shed + drop
                        "min_return_steps": d_shed + 1
                    })
        return targets
