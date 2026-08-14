"""
Grandmaster Bot linking GrandmasterEconomy and GrandmasterScheduler.
"""

from farm_state import FarmState
from grandmaster_economy import GrandmasterMarket
from grandmaster_scheduler import GrandmasterScheduler

_GM_MARKET = None
_GM_SCHEDULER = None


def get_gm_managers():
    global _GM_MARKET, _GM_SCHEDULER
    if _GM_MARKET is None:
        _GM_MARKET = GrandmasterMarket()
    if _GM_SCHEDULER is None:
        _GM_SCHEDULER = GrandmasterScheduler()
    return _GM_MARKET, _GM_SCHEDULER


def gm_agent(obs):
    try:
        farm_state = FarmState(obs)
        market_mgr, scheduler = get_gm_managers()

        planned_hires = scheduler.plan_hires(farm_state)
        market_orders = market_mgr.generate_orders(farm_state, planned_hires)
        worker_actions = scheduler.assign_worker_actions(farm_state)

        return {
            "farmer": worker_actions.get("farmer", ["PASS"]),
            "hands": worker_actions.get("hands", []),
            "market": market_orders,
        }
    except Exception as e:
        print(f"Error in gm_agent: {e}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
