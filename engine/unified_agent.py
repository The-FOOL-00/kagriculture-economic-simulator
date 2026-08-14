"""
=============================================================================
ENGINE: UNIFIED AGENT ENTRY POINT
=============================================================================
"""

from engine.world_model import WorldState
from engine.macro_planner import MacroPlanner

_PLANNER = None


def get_planner():
    global _PLANNER
    if _PLANNER is None:
        _PLANNER = MacroPlanner()
    return _PLANNER


def agent(obs):
    try:
        world_state = WorldState(obs)
        planner = get_planner()
        return planner.plan_turn(world_state)
    except Exception as e:
        print(f"Error in unified agent: {e}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
