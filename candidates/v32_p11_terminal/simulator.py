# SPDX-License-Identifier: MIT
"""
Exact Forward Shadow Simulator for Terminal Window (712-718).
Evaluates candidate physical paths without altering steps 0-711.
"""
import copy
from typing import Dict, List, Any, Tuple
import kaggle_environments.envs.kaggriculture.kaggriculture as kag

class ShadowSimulator:
    def __init__(self, board_size: int = 10, shed_capacity: int = 100):
        self.board_size = board_size
        self.shed_capacity = shed_capacity

    def step_simulation(
        self,
        farm: Dict[str, Any],
        private: Dict[str, Any],
        market: Dict[str, Any],
        action: Dict[str, Any],
        step: int,
        turns_per_day: int = 24
    ) -> float:
        """
        Executes one step of shadow simulation for a single player:
        1. Apply unit actions (farmer, hands)
        2. Apply market actions
        3. Plant decay
        Returns: money earned this step.
        """
        day = step // turns_per_day
        farmer_act = action.get("farmer", ["PASS"])
        hands_act = action.get("hands", [])
        
        # 1. Unit actions
        kag._apply_unit_action(
            farm, private, 0, farmer_act, self.board_size, day, turns_per_day, self.shed_capacity
        )
        for h_idx, h_act in enumerate(hands_act):
            kag._apply_unit_action(
                farm, private, h_idx + 1, h_act, self.board_size, day, turns_per_day, self.shed_capacity
            )
            
        # 2. Market actions
        # For unilateral shadow simulation, execute SELL orders directly against current prices.
        money_before = float(farm.get("money", 0.0))
        market_orders = action.get("market", [])
        for order in market_orders:
            if not isinstance(order, list) or len(order) < 3:
                continue
            op, item, qty = order[0], order[1], order[2]
            if op == "SELL" and item in kag.PRODUCTS:
                available = private["shed"].get(item, 0)
                to_sell = min(qty, available)
                if to_sell > 0:
                    price = kag.market_price(item, market["inventory"][item], market.get("params"))
                    private["shed"][item] -= to_sell
                    farm["money"] = farm.get("money", 0.0) + to_sell * price
                    if price > 1:
                        market["inventory"][item] += to_sell
                        
        # 3. Plant decay
        kag._decay_plants(farm, step)
        
        return float(farm.get("money", 0.0)) - money_before

    def simulate_schedule(
        self,
        obs: Dict[str, Any],
        schedule: List[Dict[str, Any]],
        seat: int = 0
    ) -> Dict[str, Any]:
        """
        Rolls out an entire action schedule from obs['step'] through obs['step'] + len(schedule) - 1.
        Returns final farm, private, market, and final cash.
        """
        start_step = obs.get("step", 712)
        farm = copy.deepcopy(obs["farms"][seat])
        private = copy.deepcopy(obs["private"])
        market = copy.deepcopy(obs["market"])
        
        for offset, action in enumerate(schedule):
            cur_step = start_step + offset
            self.step_simulation(farm, private, market, action, cur_step)
            
        return {
            "final_money": float(farm.get("money", 0.0)),
            "farm": farm,
            "private": private,
            "market": market
        }
