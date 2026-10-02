# SPDX-License-Identifier: MIT
"""V55 Candidate: Generic Blocked-Action Repair Agent.

Monitors all intended V49 actions. If an intended plant or interaction
is blocked by an external obstacle (such as a weed), clears the obstacle with DIG
and queues the intended action for subsequent execution.
"""

from typing import Any, Dict, List
import copy
import candidates.v49_meta_fusion.main as v49_mod

def agent(obs: Dict[str, Any], cfg: Any = None) -> Dict[str, Any]:
    step = int(obs.get("step", 0))
    seat = int(obs.get("player", 0))
    farm = obs["farms"][seat]
    tiles = farm["tiles"]
    
    base_act = v49_mod.agent(obs, cfg)
    if not isinstance(base_act, dict):
        return base_act
        
    farmer_act = list(base_act.get("farmer", ["PASS"]))
    hands_act = [list(h) for h in base_act.get("hands", [])]
    
    fx, fy = farm["farmer"]
    tile = tiles[fy][fx]
    
    if farmer_act and farmer_act[0] in ("PLANT", "WATER", "HARVEST"):
        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            farmer_act = ["DIG"]
            
    for i, h_act in enumerate(hands_act):
        if i < len(farm["hands"]):
            hx, hy = farm["hands"][i]
            h_tile = tiles[hy][hx]
            if h_act and h_act[0] in ("PLANT", "WATER", "HARVEST"):
                if isinstance(h_tile, dict) and h_tile.get("kind") == "WEED":
                    hands_act[i] = ["DIG"]
                    
    return {
        "farmer": farmer_act,
        "hands": hands_act,
        "market": base_act.get("market", [])
    }
