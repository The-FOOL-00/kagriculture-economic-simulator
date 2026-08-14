"""
Championship Kaggriculture AI Agent.
"""

from farm_state import FarmState
from economy import MarketManager
from worker_scheduler import WorkerScheduler

_MARKET_MGR = None
_SCHEDULER = None


def get_agent_managers():
    global _MARKET_MGR, _SCHEDULER
    if _MARKET_MGR is None:
        _MARKET_MGR = MarketManager()
    if _SCHEDULER is None:
        _SCHEDULER = WorkerScheduler()
    return _MARKET_MGR, _SCHEDULER


def agent(obs):
    """
    Main entry point for Kaggle Kaggriculture agent.
    """
    try:
        farm_state = FarmState(obs)
        market_mgr, scheduler = get_agent_managers()

        # Step 1: Plan daily labor hires
        planned_hires = scheduler.plan_hires(farm_state)

        # Step 2: Formulate market orders (Hiring, Land, Animals, Seeds, Selling)
        market_orders = market_mgr.generate_market_orders(farm_state, planned_hires)

        # Step 3: Assign worker chores & conflict-free movements
        worker_actions = scheduler.assign_worker_actions(farm_state)

        return {
            "farmer": worker_actions.get("farmer", ["PASS"]),
            "hands": worker_actions.get("hands", []),
            "market": market_orders,
        }
    except Exception as e:
        # Fallback safe pass in case of unexpected exception
        print(f"Error in agent: {e}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
