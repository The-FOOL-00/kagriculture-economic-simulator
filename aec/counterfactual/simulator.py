# SPDX-License-Identifier: MIT
"""Isolated Forward Counterfactual Simulator (§10, §17, §18)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import (
    BOARD_SIZE,
    PRODUCTS,
    SHED_CAPACITY,
    TURNS_PER_DAY,
)
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch

# Import verified unit & market physics
try:
    from extracted_agents.dmitrii_lb2800.unit_model import (
        _apply_unit_action,
        _decay_plants,
    )
except ImportError:
    # Fallback to local import if extracted_agents is mapped via repo root
    import os
    import sys
    _REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.insert(0, _REPO)
    from extracted_agents.dmitrii_lb2800.unit_model import (
        _apply_unit_action,
        _decay_plants,
    )

from aec.ir.market_state import BASE_PRICES, TOWN_SHOP_CONSUMPTION


@dataclass
class SimulationOutcome:
    """Complete economic record of an isolated counterfactual evaluation."""
    candidate_final_money: float
    baseline_final_money: float
    delta_our_money: float
    
    candidate_opp_final_money: float
    baseline_opp_final_money: float
    delta_opponent_money: float
    
    delta_terminal_margin: float
    
    candidate_overflow_units: int
    candidate_sold: Dict[str, int]
    baseline_sold: Dict[str, int]
    
    intermediate_solvency_ok: bool
    horizon: int


class ShadowRolloutState:
    """Isolated memory container for forward simulation."""

    def __init__(self, econ_state: EconomicState):
        self.step = econ_state.step
        self.day = econ_state.day
        self.money = float(econ_state.farm.cash)
        self.opp_money = float(econ_state.opponent.observed_cash)
        
        # Clone farm tiles, shed, inventories
        self.tiles = copy.deepcopy(econ_state.farm.tiles)
        self.shed = copy.deepcopy(econ_state.farm.shed_inventory)
        self.seeds = copy.deepcopy(econ_state.farm.seeds)
        
        # Workers: positions and inventories
        self.farmer_pos = list(econ_state.workers.workers[0].position)
        self.hands_pos = [list(w.position) for w in econ_state.workers.workers[1:]]
        self.inventories = [copy.deepcopy(w.cargo) for w in econ_state.workers.workers]
        
        # Market state
        self.market_prices = copy.deepcopy(econ_state.market.current_prices)
        self.market_inv = copy.deepcopy(econ_state.market.market_inventory)
        self.unlocked_shops = list(econ_state.market.unlocked_shops)
        
        # Tracking
        self.overflow_units = 0
        self.cumulative_sold: Dict[str, int] = {p: 0 for p in PRODUCTS}
        self.rows: List[Dict[str, Any]] = []

    def get_farm_dict(self) -> Dict[str, Any]:
        return {
            "money": self.money,
            "farmer": self.farmer_pos,
            "hands": self.hands_pos,
            "tiles": self.tiles,
            "hires_today": 0,
        }

    def get_private_dict(self) -> Dict[str, Any]:
        return {
            "shed": self.shed,
            "seeds": self.seeds,
            "inventories": self.inventories,
        }


def execute_market_lockstep(
    rollout: ShadowRolloutState,
    own_orders: List[List[Any]],
    opp_orders: List[List[Any]]
) -> None:
    """Execute own orders against opponent orders in lockstep per-unit semantics."""
    own_q = list(own_orders)[:10]
    opp_q = list(opp_orders)[:10]
    max_len = max(len(own_q), len(opp_q))

    for i in range(max_len):
        # 1. Own order execution
        if i < len(own_q):
            o = own_q[i]
            if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
                item = o[1]
                qty = int(o[2])
                avail = rollout.shed.get(item, 0)
                actual_sell = min(qty, avail)
                if actual_sell > 0:
                    price = rollout.market_prices.get(item, BASE_PRICES.get(item, 1))
                    rollout.money += actual_sell * price
                    rollout.shed[item] -= actual_sell
                    rollout.cumulative_sold[item] += actual_sell
                    # Increase market inventory (price depression)
                    rollout.market_inv[item] = rollout.market_inv.get(item, 10000) + actual_sell
                    rollout.market_prices[item] = max(1, price - actual_sell // 2)

        # 2. Opponent order execution
        if i < len(opp_q):
            o = opp_q[i]
            if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
                item = o[1]
                qty = int(o[2])
                price = rollout.market_prices.get(item, BASE_PRICES.get(item, 1))
                rollout.opp_money += qty * price
                rollout.market_inv[item] = rollout.market_inv.get(item, 10000) + qty
                rollout.market_prices[item] = max(1, price - qty // 2)

    # Town consumption tick every 4 steps
    if rollout.step % 4 == 0:
        for shop in rollout.unlocked_shops:
            for it, q in TOWN_SHOP_CONSUMPTION.get(shop, ()):
                if it in rollout.market_inv:
                    rollout.market_inv[it] = max(0, rollout.market_inv[it] - q)
                    base_p = BASE_PRICES.get(it, 10)
                    rollout.market_prices[it] = min(base_p * 2, rollout.market_prices[it] + 2)


def simulate_rollout(
    econ_state: EconomicState,
    initial_action: Dict[str, Any],
    horizon: int,
    opp_model: OpponentPressureModel
) -> ShadowRolloutState:
    """Run an isolated forward rollout starting with initial_action at step 0."""
    rollout = ShadowRolloutState(econ_state)
    n_workers = len(rollout.inventories)

    for offset in range(horizon):
        cur_step = econ_state.step + offset
        rollout.step = cur_step
        rollout.day = cur_step // TURNS_PER_DAY
        
        # Step action: initial_action on offset 0; passive continuation thereafter
        if offset == 0:
            action = initial_action
        else:
            action = {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n_workers - 1)], "market": []}

        # 1. Apply worker movements and tasks
        farm_dict = rollout.get_farm_dict()
        private_dict = rollout.get_private_dict()
        
        pre_market_shed = dict(rollout.shed)
        commands = [action.get("farmer", ["PASS"])] + (action.get("hands", []) or [])
        while len(commands) < n_workers:
            commands.append(["PASS"])

        for actor in range(n_workers):
            cmd = commands[actor] if actor < len(commands) and commands[actor] else ["PASS"]
            try:
                _apply_unit_action(
                    farm_dict,
                    private_dict,
                    actor,
                    cmd,
                    BOARD_SIZE,
                    rollout.day,
                    TURNS_PER_DAY,
                    SHED_CAPACITY
                )
            except Exception:
                pass  # Ignore invalid worker step in simulation

        # 2. Market execution under opponent pressure
        opp_market = opp_model.generate_simulated_opponent_market(econ_state.step, offset)
        execute_market_lockstep(rollout, action.get("market", []), opp_market)

        # 3. Plant decay
        try:
            _decay_plants(farm_dict, cur_step)
        except Exception:
            pass

        # 4. Record row
        rollout.rows.append({
            "step": cur_step,
            "pre_market_shed": pre_market_shed,
            "post_market_shed": dict(rollout.shed),
            "money": rollout.money,
            "opp_money": rollout.opp_money,
        })

    return rollout


class CounterfactualSimulator:
    """Evaluates candidate patches against baseline under opponent pressure."""

    def evaluate(
        self,
        candidate_patch: CoupledPatch,
        baseline_action: Dict[str, Any],
        econ_state: EconomicState,
        horizon: int
    ) -> SimulationOutcome:
        opp_model = OpponentPressureModel(econ_state.opponent)

        # 1. Simulate Baseline Future
        baseline_rollout = simulate_rollout(econ_state, baseline_action, horizon, opp_model)

        # 2. Simulate Candidate Future
        cand_action = candidate_patch.apply(baseline_action)
        candidate_rollout = simulate_rollout(econ_state, cand_action, horizon, opp_model)

        # 3. Compute Deltas & Margins
        delta_our_money = candidate_rollout.money - baseline_rollout.money
        delta_opp_money = candidate_rollout.opp_money - baseline_rollout.opp_money
        
        # Terminal margin delta = (Our_cand - Opp_cand) - (Our_base - Opp_base)
        cand_margin = candidate_rollout.money - candidate_rollout.opp_money
        base_margin = baseline_rollout.money - baseline_rollout.opp_money
        delta_terminal_margin = cand_margin - base_margin

        # 4. Intermediate Solvency Check
        intermediate_solvency_ok = True
        for offset in range(min(len(candidate_rollout.rows), len(baseline_rollout.rows))):
            cand_pre = candidate_rollout.rows[offset]["pre_market_shed"]
            base_pre = baseline_rollout.rows[offset]["pre_market_shed"]
            for p in PRODUCTS:
                # Candidate pre-shed must not drop below zero
                if cand_pre.get(p, 0) < 0:
                    intermediate_solvency_ok = False
                    break

        return SimulationOutcome(
            candidate_final_money=candidate_rollout.money,
            baseline_final_money=baseline_rollout.money,
            delta_our_money=delta_our_money,
            candidate_opp_final_money=candidate_rollout.opp_money,
            baseline_opp_final_money=baseline_rollout.opp_money,
            delta_opponent_money=delta_opp_money,
            delta_terminal_margin=delta_terminal_margin,
            candidate_overflow_units=candidate_rollout.overflow_units,
            candidate_sold=candidate_rollout.cumulative_sold,
            baseline_sold=baseline_rollout.cumulative_sold,
            intermediate_solvency_ok=intermediate_solvency_ok,
            horizon=horizon
        )
