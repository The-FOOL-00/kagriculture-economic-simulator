"""
CLOSED-LOOP ECONOMIC ARCHITECTURE: Master Agent Implementation.
Combines:
A. High-profit production mechanisms (Dmitrii bedrock + modular alternatives)
B. Runtime liquidity / runway management (SAFE_CASH_FLOOR)
C. Strict max_orders=10 action arbitration (hire slot protection)
D. Explicit shed-headroom management (zero harvest discard)
E. State-dependent economic routing (Yarn, Non-Yarn High/Low Demand)
F. Controlled, conservative module switching
G. Physical worker synchronization (weed repairs, inventory drops, terminal liquidation)
"""
import copy
import json
import os
import sys
from typing import Dict, List, Any, Optional

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
dmitrii_dir = os.path.join(base_dir, "extracted_agents", "dmitrii_lb2800")
if dmitrii_dir not in sys.path:
    sys.path.insert(0, dmitrii_dir)

from economic_state import EconomicState
from action_arbitrator import ActionArbitrator
from liquidity_controller import LiquidityController
from shed_controller import ShedController
from production_modules import ProductionModuleManager
from switching_policy import SwitchingPolicy

# Worker execution components from router_parent
from router_parent import (
    FarmView, DayState, repair_weeds, advance_sales, 
    subtract_advanced_sales, liquidate, FINAL_PLAN_STEP, LAST_STEP
)

class ClosedLoopAgent:
    def __init__(
        self,
        switching_mode: str = "MILESTONE_CONSERVATIVE",
        shed_policy: str = "88_CEILING",
        base_liquidity_reserve: float = 500.0,
        actions_path: str = os.path.join(dmitrii_dir, "actions.json")
    ):
        self.switching_policy = SwitchingPolicy(mode=switching_mode)
        self.shed_controller = ShedController(policy=shed_policy)
        self.liquidity_controller = LiquidityController(base_reserve=base_liquidity_reserve)
        self.action_arbitrator = ActionArbitrator()
        self.module_manager = ProductionModuleManager(actions_path=actions_path)
        
        self.current_tape: Optional[List[Any]] = None
        self.active_module_id = "MODULE_A_FERT_STRAWBERRY"
        self._load_active_tape()
        
        self.players = {}
        
        # Telemetry & Diagnostics
        self.diagnostics = {
            "switches_performed": 0,
            "liquidity_triggers": 0,
            "shed_purges": 0,
            "hires_protected": 0,
            "sales_deferred": 0
        }

    def _load_active_tape(self):
        self.current_tape = self.module_manager.get_module_action_tape(self.active_module_id)

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs.get("step", 0))
        player = int(obs.get("player", 0))
        
        # DayState initialization for weed repair queues
        state_mem = self.players.get(player)
        if state_mem is None or step <= state_mem.last_step:
            state_mem = self.players[player] = DayState()
        state_mem.last_step = step

        # 1. Ingest Observation into Economic State
        econ_state = EconomicState.from_obs(obs)
        
        # 2. Evaluate Module Switching (e.g. at Day 6 Step 144)
        did_switch, new_mod, rationale = self.switching_policy.evaluate_switch(econ_state)
        if did_switch and new_mod != self.active_module_id:
            self.active_module_id = new_mod
            self._load_active_tape()
            self.diagnostics["switches_performed"] += 1
            
        # 3. Terminal plan override at Step 648 (switch to harvest/liquidation tape)
        if step == FINAL_PLAN_STEP and self.active_module_id == "MODULE_A_FERT_STRAWBERRY":
            # Plan 2 is Dmitrii's terminal harvest tape
            self.current_tape = self.module_manager.get_module_action_tape("MODULE_A_FERT_STRAWBERRY")
            # Load raw plan 2
            if self.module_manager._raw_plans and len(self.module_manager._raw_plans) > 2:
                self.current_tape = self.module_manager._raw_plans[2]

        # 4. Retrieve Base Action from Current Module Tape
        if self.current_tape and step < len(self.current_tape):
            action = copy.deepcopy(self.current_tape[step])
        else:
            action = {"farmer": ["PASS"], "hands": [], "market": []}
            
        # 5. Apply physical worker repairs (weed avoidance, same-day queuing)
        view = FarmView(obs)
        repair_weeds(action, view, state_mem, step)
        subtract_advanced_sales(action, state_mem, step)
        advance_sales(action, view, state_mem, self.current_tape, step)

        # 6. Terminal step check: execute full liquidation on Step 718
        if step == LAST_STEP:
            return liquidate(view)

        # 7. Liquidity Controller: Check Cash Runway & SAFE_CASH_FLOOR
        raw_market_orders = action.get("market", [])
        has_deficit, deficit_amt, emergency_sales = self.liquidity_controller.check_liquidity(econ_state)
        if has_deficit:
            self.diagnostics["liquidity_triggers"] += 1
            
        # 8. Shed Controller: Check Occupancy Headroom (prevent harvest discard)
        has_overflow, overflow_qty, purge_sales = self.shed_controller.check_headroom(econ_state)
        if has_overflow:
            self.diagnostics["shed_purges"] += 1
            
        # 9. Aggregate All Candidate Market Orders
        candidate_orders = []
        for ord_item in raw_market_orders:
            candidate_orders.append(ord_item)
            
        existing_sells = {
            ord_item[1] for ord_item in raw_market_orders 
            if isinstance(ord_item, (list, tuple)) and len(ord_item) > 1 and ord_item[0] == "SELL"
        }
        for s_ord in emergency_sales:
            if isinstance(s_ord, (list, tuple)) and len(s_ord) > 1 and s_ord[1] not in existing_sells:
                candidate_orders.append(s_ord)
                
        for p_ord in purge_sales:
            if isinstance(p_ord, (list, tuple)) and len(p_ord) > 1 and p_ord[1] not in existing_sells:
                candidate_orders.append(p_ord)
                
        # 10. Action Arbitrator: Filter, prioritize, and enforce max_orders=10
        arbitrated_orders = self.action_arbitrator.arbitrate_market_orders(candidate_orders, econ_state)
        action["market"] = arbitrated_orders
        
        self.diagnostics["hires_protected"] = self.action_arbitrator.arbitration_stats["hires_protected"]
        self.diagnostics["sales_deferred"] = self.action_arbitrator.arbitration_stats["discretionary_sales_deferred"]
        
        return action
