"""
SPECIALIZED BRANCH AGENT
========================
Extends ClosedLoopAgentV2 with dynamically compiled demand-specialized physical branches.
At Step 144 (Milestone 1):
- If PIZZA_SHOP in town: activates the compiled physically valid TOMATO branch.
- If PET_CAFE in town: activates the compiled physically valid CARROT branch.
- Otherwise: executes the validated champion CLOSED_LOOP_V2 bedrock.
Retains all V2 safety systems:
- JIT Shed Headroom Protection (purges only when projected_shed > 96)
- Runtime Liquidity Guard
- Strict 10-slot Action Arbitration (HIRE > CAPEX > EMERGENCY_SELL > REGULAR)
- Non-Cannibalization Invariant (wheat reserve >= 3 * animals)
- Weed repairs and advance sales
"""
import os
import sys
import json
import copy
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

from closed_loop_v2 import ClosedLoopAgentV2
from spatial_production_compiler import compile_specialized_tape
from router_parent import (
    FarmView, DayState, repair_weeds, advance_sales,
    subtract_advanced_sales, liquidate, projected_shed,
    ROUTE_STEP, FINAL_PLAN_STEP, LAST_STEP, MAX_ORDERS, PRODUCTS
)

class DemandSpecializedAgent(ClosedLoopAgentV2):
    def __init__(
        self,
        tomato_tiles: int = 19,
        tomato_cohorts: int = 2,
        tomato_batch: int = 6,
        carrot_tiles: int = 80,
        enable_pizza_specialist: bool = True,
        enable_carrot_specialist: bool = True,
        tomato_custom_tape: Optional[List[Dict[str, Any]]] = None,
        carrot_custom_tape: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(jit_headroom_threshold=96, base_liquidity_reserve=500.0)
        self.enable_pizza = enable_pizza_specialist
        self.enable_carrot = enable_carrot_specialist
        
        # Pre-compile or load specialized tapes
        if tomato_custom_tape is not None:
            self.tomato_tape = tomato_custom_tape
        else:
            self.tomato_tape = compile_specialized_tape(
                crop="TOMATO",
                tiles_count=tomato_tiles,
                cohorts=tomato_cohorts,
                workers=12,
                batch=tomato_batch,
                timing=1
            )
            
        if carrot_custom_tape is not None:
            self.carrot_tape = carrot_custom_tape
        else:
            self.carrot_tape = compile_specialized_tape(
                crop="CARROT",
                tiles_count=carrot_tiles,
                cohorts=3,
                workers=12,
                batch=10,
                timing=1
            )
            
        self.active_branch = {} # player -> branch_name

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs.get("step", 0))
        player = int(obs.get("player", 0))
        
        # Route selection at Step 144
        if step == ROUTE_STEP:
            shops = obs.get("town", {}).get("unlocked_shops", [])
            has_pizza = "PIZZA_SHOP" in shops
            has_pet_cafe = "PET_CAFE" in shops
            has_yarn = "YARN_STORE" in shops
            
            # Pizza specialist triggers if PIZZA_SHOP is present
            if self.enable_pizza and has_pizza and not has_yarn:
                self.active_branch[player] = "PIZZA"
            # Carrot specialist triggers if PET_CAFE is present
            elif self.enable_carrot and has_pet_cafe and not has_yarn:
                self.active_branch[player] = "CARROT"
            else:
                self.active_branch[player] = "DEFAULT"

        branch = self.active_branch.get(player, "DEFAULT")
        
        # If branch is DEFAULT, use standard ClosedLoopV2 logic
        if branch == "DEFAULT" or step < ROUTE_STEP:
            return super().act(obs)

        # Specialized branch execution
        state_mem = self.players.get(player)
        if state_mem is None or step <= state_mem.last_step:
            state_mem = self.players[player] = DayState()
        state_mem.last_step = step

        view = FarmView(obs)
        if branch == "PIZZA":
            tape = self.tomato_tape
        elif branch == "CARROT":
            tape = self.carrot_tape
        else:
            tape = self.tapes[state_mem.plan]
            
        action = copy.deepcopy(tape[step])

        # Apply worker repairs (weed avoidance, same-day queue, advance sales)
        repair_weeds(action, view, state_mem, step)
        subtract_advanced_sales(action, state_mem, step)
        advance_sales(action, view, state_mem, tape, step)

        if step == LAST_STEP:
            return liquidate(view)

        # Apply JIT Shed Headroom Controller & Liquidity Guard from ClosedLoopV2
        est_stock = projected_shed(action, view)
        est_total = sum(est_stock.values())
        
        jit_orders = []
        if est_total > self.jit_threshold:
            overflow = est_total - self.jit_threshold
            feed_reserve = self._compute_feed_reserve(obs, player)
            
            # Prioritize excess fertilizer
            fert_avail = max(0, est_stock.get("FERTILIZER", 0) - 15)
            if fert_avail > 0 and overflow > 0:
                p_qty = min(fert_avail, overflow)
                jit_orders.append(["SELL", "FERTILIZER", p_qty])
                overflow -= p_qty
                
            # Prioritize specialty crops
            crop_priority = ["TOMATO", "CARROT", "STRAWBERRY", "MELON"] if branch == "PIZZA" else ["CARROT", "STRAWBERRY", "MELON", "TOMATO"]
            for crop in crop_priority:
                if overflow <= 0: break
                avail = est_stock.get(crop, 0)
                if avail > 0:
                    p_qty = min(avail, overflow)
                    jit_orders.append(["SELL", crop, p_qty])
                    overflow -= p_qty

            # Surplus wheat above feed reserve
            wheat_avail = max(0, est_stock.get("WHEAT", 0) - feed_reserve)
            if wheat_avail > 0 and overflow > 0:
                p_qty = min(wheat_avail, overflow)
                jit_orders.append(["SELL", "WHEAT", p_qty])
                overflow -= p_qty

        # Action Arbitrator (10-slot priority)
        raw_market = action.get("market", [])
        combined = []
        existing_sells = {m[1] for m in raw_market if m and m[0] == "SELL" and len(m) > 1}
        for m in raw_market:
            combined.append(m)
        for jo in jit_orders:
            if jo[1] not in existing_sells:
                combined.append(jo)
                existing_sells.add(jo[1])

        tagged = []
        for idx, ord_item in enumerate(combined):
            if not ord_item: continue
            op = str(ord_item[0]).upper()
            if op == "HIRE": prio = 1
            elif op == "BUY_LAND": prio = 2
            elif op == "SELL" and ord_item in jit_orders: prio = 3
            else: prio = 4
            tagged.append((prio, idx, ord_item))

        tagged.sort(key=lambda x: (x[0], x[1]))
        selected = tagged[:MAX_ORDERS]
        selected.sort(key=lambda x: x[1])
        action["market"] = [item[2] for item in selected]

        return action
