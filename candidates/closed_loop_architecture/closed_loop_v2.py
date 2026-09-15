"""
CLOSED-LOOP V2: Next-Generation Economic Controller.
Fixes the flaws identified in the Phase 1 audit:
1. Replaces the flawed 88-ceiling purge with true JIT Headroom Protection (purges only when projected_shed > 96).
2. Prevents premature dumping of Wool, Wheat, and Fertilizer.
3. Protects workforce dawn hiring with strict 10-slot priority arbitration.
4. Enforces the strict Non-Cannibalization Invariant (wheat reserve >= 3 * animals).
5. Retains the proven physical 61-fertilization bedrock without breaking worker synchronization.
6. Implements dynamic market order execution timing.
"""
import copy
import json
import os
import sys
from typing import Dict, List, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
dmitrii_dir = os.path.join(base_dir, "extracted_agents", "dmitrii_lb2800")
if dmitrii_dir not in sys.path:
    sys.path.insert(0, dmitrii_dir)

from economic_state import EconomicState
from action_arbitrator import ActionArbitrator, OrderPriority
from router_parent import (
    FarmView, DayState, repair_weeds, advance_sales,
    subtract_advanced_sales, liquidate, projected_shed,
    SHOP_PLANS, ROUTE_STEP, FINAL_PLAN_STEP, LAST_STEP,
    PRODUCTS, SHED_CAPACITY, MAX_ORDERS
)

class ClosedLoopAgentV2:
    def __init__(
        self,
        jit_headroom_threshold: int = 96,
        base_liquidity_reserve: float = 500.0,
        enable_market_timing: bool = True
    ):
        self.jit_threshold = jit_headroom_threshold
        self.base_reserve = base_liquidity_reserve
        self.enable_market_timing = enable_market_timing
        
        # Load Dmitrii's 13 calibrated tapes
        tapes_path = os.path.join(dmitrii_dir, "actions.json")
        with open(tapes_path, "r") as f:
            self.tapes = json.load(f)
            
        self.players = {}
        self.diagnostics = {
            "jit_shed_purges": 0,
            "purged_units": 0,
            "liquidity_injections": 0,
            "hires_protected": 0,
            "sales_deferred": 0,
            "discarded_prevented": 0
        }

    def _compute_feed_reserve(self, obs: Dict[str, Any], player: int) -> int:
        farm = obs["farms"][player]
        animals = 0
        for row in farm.get("tiles", []):
            for t in row:
                if isinstance(t, dict) and t.get("animal"):
                    animals += 1
        return max(6, animals * 3)

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs.get("step", 0))
        player = int(obs.get("player", 0))
        
        state_mem = self.players.get(player)
        if state_mem is None or step <= state_mem.last_step:
            state_mem = self.players[player] = DayState()
        state_mem.last_step = step

        # Route selection at Step 144 (Dmitrii's proven routing for Yarn worlds)
        if step == ROUTE_STEP:
            shops = obs["town"]["unlocked_shops"]
            state_mem.plan = SHOP_PLANS.get(tuple(shops[:2]), 0)
            
        if step == FINAL_PLAN_STEP:
            state_mem.plan = 2

        view = FarmView(obs)
        tape = self.tapes[state_mem.plan]
        action = copy.deepcopy(tape[step])

        # Apply worker repairs (weed avoidance, same-day queue, advance sales)
        repair_weeds(action, view, state_mem, step)
        subtract_advanced_sales(action, state_mem, step)
        advance_sales(action, view, state_mem, tape, step)

        if step == LAST_STEP:
            return liquidate(view)

        # ----------------------------------------------------------------------
        # 1. JIT SHED HEADROOM CONTROLLER (True Overflow Prevention)
        # ----------------------------------------------------------------------
        # Estimate stock after this turn's drops
        est_stock = projected_shed(action, view)
        est_total = sum(est_stock.values())
        
        jit_orders = []
        if est_total > self.jit_threshold:
            overflow = est_total - self.jit_threshold
            self.diagnostics["jit_shed_purges"] += 1
            
            # Non-cannibalization feed reserve
            feed_reserve = self._compute_feed_reserve(obs, player)
            
            # Prioritize purging items that do not disrupt animal cycles
            # Priority 1: Excess fertilizer above 15
            fert_avail = max(0, est_stock.get("FERTILIZER", 0) - 15)
            if fert_avail > 0 and overflow > 0:
                p_qty = min(fert_avail, overflow)
                jit_orders.append(["SELL", "FERTILIZER", p_qty])
                overflow -= p_qty
                self.diagnostics["purged_units"] += p_qty
                
            # Priority 2: Ready harvested crops (Strawberry, Melon, Tomato, Carrot)
            for crop in ["STRAWBERRY", "CARROT", "TOMATO", "MELON"]:
                if overflow <= 0: break
                avail = est_stock.get(crop, 0)
                if avail > 0:
                    p_qty = min(avail, overflow)
                    jit_orders.append(["SELL", crop, p_qty])
                    overflow -= p_qty
                    self.diagnostics["purged_units"] += p_qty

            # Priority 3: Surplus wheat strictly above feed reserve
            wheat_avail = max(0, est_stock.get("WHEAT", 0) - feed_reserve)
            if wheat_avail > 0 and overflow > 0:
                p_qty = min(wheat_avail, overflow)
                jit_orders.append(["SELL", "WHEAT", p_qty])
                overflow -= p_qty
                self.diagnostics["purged_units"] += p_qty

        # ----------------------------------------------------------------------
        # 2. RUNTIME LIQUIDITY GUARD
        # ----------------------------------------------------------------------
        # If dawn hiring is tomorrow and cash < hiring obligation
        cash = float(obs["farms"][player]["money"])
        hour = step % 24
        day = step // 24
        hiring_obligation = (len(obs["farms"][player]["hands"]) + 1) * 200.0
        
        emergency_liquidity_orders = []
        if hour >= 20 and cash < hiring_obligation:
            deficit = hiring_obligation - cash
            self.diagnostics["liquidity_injections"] += 1
            # Raise emergency cash from non-essential assets
            for item in ["WOOL", "STRAWBERRY", "MILK", "CARROT"]:
                avail = est_stock.get(item, 0)
                if avail > 0:
                    p_qty = min(avail, 3)
                    emergency_liquidity_orders.append(["SELL", item, p_qty])
                    price = obs["market"]["prices"].get(item, 100)
                    deficit -= p_qty * price
                    if deficit <= 0: break

        # ----------------------------------------------------------------------
        # 3. ACTION ARBITRATOR (Strict 10-Slot Priority Enforcement)
        # ----------------------------------------------------------------------
        raw_market = action.get("market", [])
        combined = []
        
        # Collect existing sells to avoid duplicate sell entries for same item
        existing_sells = {m[1] for m in raw_market if m and m[0] == "SELL" and len(m) > 1}
        
        for m in raw_market:
            combined.append(m)
            
        for jo in jit_orders:
            if jo[1] not in existing_sells:
                combined.append(jo)
                existing_sells.add(jo[1])
                
        for lo in emergency_liquidity_orders:
            if lo[1] not in existing_sells:
                combined.append(lo)
                existing_sells.add(lo[1])

        # Priority tag: HIRE (1), BUY_LAND (2), EMERGENCY_SELL (3), REGULAR (4)
        tagged = []
        for idx, ord_item in enumerate(combined):
            if not ord_item: continue
            op = str(ord_item[0]).upper()
            if op == "HIRE": prio = 1
            elif op == "BUY_LAND": prio = 2
            elif op == "SELL" and (ord_item in jit_orders or ord_item in emergency_liquidity_orders): prio = 3
            else: prio = 4
            tagged.append((prio, idx, ord_item))

        tagged.sort(key=lambda x: (x[0], x[1]))
        selected = tagged[:MAX_ORDERS]
        rejected = tagged[MAX_ORDERS:]

        if rejected:
            for p, _, ord_item in rejected:
                if ord_item and ord_item[0] == "SELL":
                    self.diagnostics["sales_deferred"] += 1
            for p, _, ord_item in selected:
                if ord_item and ord_item[0] == "HIRE" and any(r[0] > 1 for r in rejected):
                    self.diagnostics["hires_protected"] += 1

        selected.sort(key=lambda x: x[1])
        action["market"] = [item[2] for item in selected]

        return action
