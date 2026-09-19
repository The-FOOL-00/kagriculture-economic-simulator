# SPDX-License-Identifier: MIT
"""AEC State-Space Profiler and Potential Headroom Classifier (§6, §7)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES
from aec.config import BOARD_SIZE, SHED_CAPACITY, PRODUCTS


@dataclass
class StateClassification:
    """Multi-dimensional classification of a single game turn."""
    step: int
    worker_state: str        # productive, traveling, idle, carrying, blocked, reconnecting
    farm_state: str          # cash-rich, cash-constrained, seed-constrained, feed-constrained, shed-constrained, terminal-constrained, resource-constrained, normal
    market_state: str        # normal, favorable, unfavorable, opportunity_window, saturation_risk, liquidity-sensitive
    production_state: str    # normal, bottlenecked, idle, dependency-limited, terminal-focused
    terminal_state: str      # far_from_terminal, terminal_runway_sufficient, terminal_runway_tight, liquidation_phase, shutdown_phase
    opponent_state: str      # low_pressure, moderate_pressure, high_pressure, ambiguous_pressure

    is_interesting: bool = False
    triggered_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "worker_state": self.worker_state,
            "farm_state": self.farm_state,
            "market_state": self.market_state,
            "production_state": self.production_state,
            "terminal_state": self.terminal_state,
            "opponent_state": self.opponent_state,
            "is_interesting": self.is_interesting,
            "indicators": self.triggered_indicators,
        }


class StateProfiler:
    """Profiles foundation game turns and detects potential headroom states."""

    def __init__(self) -> None:
        self._history: List[StateClassification] = []

    def classify_turn(
        self,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        pressure_state: Any = None,
    ) -> StateClassification:
        step = econ_state.step

        # 1. Worker State
        worker_state = self._classify_worker_state(econ_state, baseline_action)

        # 2. Farm State
        farm_state = self._classify_farm_state(econ_state)

        # 3. Market State
        market_state = self._classify_market_state(econ_state, baseline_action)

        # 4. Production State
        production_state = self._classify_production_state(econ_state)

        # 5. Terminal State
        terminal_state = self._classify_terminal_state(step)

        # 6. Opponent State
        opponent_state = self._classify_opponent_state(pressure_state)

        # Detect 16 Diagnostic Indicators
        indicators = self._detect_interesting_indicators(
            econ_state, baseline_action, pressure_state,
            worker_state, farm_state, market_state, production_state, terminal_state, opponent_state
        )
        is_interesting = len(indicators) > 0

        classification = StateClassification(
            step=step,
            worker_state=worker_state,
            farm_state=farm_state,
            market_state=market_state,
            production_state=production_state,
            terminal_state=terminal_state,
            opponent_state=opponent_state,
            is_interesting=is_interesting,
            triggered_indicators=indicators,
        )
        self._history.append(classification)
        return classification

    def _classify_worker_state(
        self, econ_state: EconomicState, baseline_action: Dict[str, Any]
    ) -> str:
        workers = econ_state.workers.workers
        if not workers:
            return "idle"

        # Check farmer action
        f_act = baseline_action.get("farmer", ["PASS"])
        h_acts = baseline_action.get("hands", [])

        all_actions = [f_act] + list(h_acts)
        has_idle = any(
            not a or (isinstance(a, (list, tuple)) and a[0] in ("PASS", "IDLE"))
            for a in all_actions[:len(workers)]
        )
        if has_idle:
            return "idle"

        # Check carrying
        high_cargo = any(
            sum(w.cargo.values()) >= 8 for w in workers
        )
        if high_cargo:
            return "carrying"

        # Check traveling
        is_moving = any(
            isinstance(a, (list, tuple)) and a and a[0] in ("MOVE", "MOVE_TO", "N", "S", "E", "W")
            for a in all_actions[:len(workers)]
        )
        if is_moving:
            return "traveling"

        return "productive"

    def _classify_farm_state(self, econ_state: EconomicState) -> str:
        step = econ_state.step
        cash = float(econ_state.farm.cash)
        shed_stock = sum(econ_state.farm.shed_inventory.values())

        if step >= 680 and shed_stock > 10:
            return "terminal-constrained"
        if shed_stock >= 90:
            return "shed-constrained"

        # Feed check
        animals = getattr(econ_state.farm, "animals", [])
        if animals:
            feed_units = econ_state.farm.shed_inventory.get("FEED", 0)
            if feed_units < len(animals) * 2:
                return "feed-constrained"

        # Daily wage requirement
        n_workers = len(econ_state.workers.workers)
        daily_wages = max(0, n_workers - 1) * 200.0
        step_in_day = step % 24
        if step_in_day >= 18 and cash < daily_wages:
            return "cash-constrained"

        # Cash rich
        if cash >= 5000.0:
            return "cash-rich"

        # Seed constrained: open tilled tiles with zero seeds
        open_tilled = sum(
            1 for row in econ_state.farm.tiles
            for cell in (row if isinstance(row, list) else [])
            if isinstance(cell, dict) and cell.get("tilled", False) and not cell.get("crop")
        )
        total_seeds = sum(econ_state.farm.seeds.values())
        if open_tilled > 0 and total_seeds == 0:
            return "seed-constrained"

        return "normal"

    def _classify_market_state(
        self, econ_state: EconomicState, baseline_action: Dict[str, Any]
    ) -> str:
        step = econ_state.step
        prices = econ_state.market.current_prices

        # Check town consumption cycle (step % 72)
        steps_to_town = 72 - (step % 72)
        if steps_to_town <= 6:
            return "opportunity_window"

        # Check price shock vs base
        fav_count = 0
        unfav_count = 0
        for p, cur_pr in prices.items():
            base = BASE_PRICES.get(p, 100)
            if base > 0:
                ratio = cur_pr / base
                if ratio >= 1.15:
                    fav_count += 1
                elif ratio <= 0.85:
                    unfav_count += 1

        if fav_count >= 2:
            return "favorable"
        if unfav_count >= 2:
            return "unfavorable"

        # Check liquidity sensitivity
        cash = float(econ_state.farm.cash)
        if cash < 300.0:
            return "liquidity-sensitive"

        return "normal"

    def _classify_production_state(self, econ_state: EconomicState) -> str:
        step = econ_state.step
        if step >= 680:
            return "terminal-focused"

        # Count mature unharvested crops
        mature_count = 0
        active_planted = 0
        for row in econ_state.farm.tiles:
            for cell in (row if isinstance(row, list) else []):
                if isinstance(cell, dict) and cell.get("crop"):
                    active_planted += 1
                    crop_info = cell.get("crop")
                    if isinstance(crop_info, dict) and crop_info.get("mature", False):
                        mature_count += 1

        if mature_count >= 3:
            return "bottlenecked"
        if active_planted == 0 and step > 48:
            return "idle"

        return "normal"

    def _classify_terminal_state(self, step: int) -> str:
        if step < 600:
            return "far_from_terminal"
        elif step < 680:
            return "terminal_runway_sufficient"
        elif step < 710:
            return "terminal_runway_tight"
        elif step < 718:
            return "liquidation_phase"
        else:
            return "shutdown_phase"

    def _classify_opponent_state(self, pressure_state: Any) -> str:
        if pressure_state is None:
            return "low_pressure"
        score = getattr(pressure_state, "composite_pressure_score", 0.0)
        if score >= 0.7:
            return "high_pressure"
        elif score >= 0.35:
            return "moderate_pressure"
        elif score > 0.0:
            return "low_pressure"
        return "ambiguous_pressure"

    def _detect_interesting_indicators(
        self,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        pressure_state: Any,
        worker_state: str,
        farm_state: str,
        market_state: str,
        production_state: str,
        terminal_state: str,
        opponent_state: str = "low_pressure",
    ) -> List[str]:
        step = econ_state.step
        indicators: List[str] = []

        # Find mature crops
        mature_coords: List[Tuple[int, int]] = []
        for r, row in enumerate(econ_state.farm.tiles):
            for c, cell in enumerate(row if isinstance(row, list) else []):
                if isinstance(cell, dict) and cell.get("crop"):
                    crop_info = cell.get("crop")
                    if isinstance(crop_info, dict) and crop_info.get("mature", False):
                        mature_coords.append((r, c))

        # 1. IDLE_WORKER_MATURE_CROP
        workers = econ_state.workers.workers
        f_act = baseline_action.get("farmer", ["PASS"])
        h_acts = baseline_action.get("hands", [])
        all_acts = [f_act] + list(h_acts)

        if mature_coords:
            for idx, w in enumerate(workers):
                act = all_acts[idx] if idx < len(all_acts) else ["PASS"]
                if not act or (isinstance(act, (list, tuple)) and act[0] in ("PASS", "IDLE")):
                    # check distance to any mature crop
                    w_pos = w.position
                    min_dist = min(abs(w_pos[0] - mr) + abs(w_pos[1] - mc) for mr, mc in mature_coords)
                    if min_dist <= 5:
                        indicators.append("IDLE_WORKER_MATURE_CROP")
                        break

        # 2. WORKER_BOTTLENECK
        if mature_coords and worker_state == "traveling" and len(mature_coords) >= 3:
            indicators.append("WORKER_BOTTLENECK")

        # 3. LARGE_UNCOMMITTED_INVENTORY
        shed_stock = sum(econ_state.farm.shed_inventory.values())
        mkt_orders = baseline_action.get("market", [])
        has_sell = any(isinstance(o, (list, tuple)) and o and o[0] == "SELL" for o in mkt_orders)
        if shed_stock >= 50 and not has_sell:
            indicators.append("LARGE_UNCOMMITTED_INVENTORY")

        # 4. CASH_TEMPORARILY_IDLE
        cash = float(econ_state.farm.cash)
        if cash >= 3000.0 and (step % 24 <= 2) and not mkt_orders:
            indicators.append("CASH_TEMPORARILY_IDLE")

        # 5. CASH_SHORTAGE_WAGE_RISK
        if farm_state == "cash-constrained":
            indicators.append("CASH_SHORTAGE_WAGE_RISK")

        # 6. MARKET_PRICE_SPIKE
        prices = econ_state.market.current_prices
        for p, amt in econ_state.farm.shed_inventory.items():
            if amt > 0 and p in prices:
                base = BASE_PRICES.get(p, 100)
                if prices[p] >= 1.25 * base:
                    indicators.append("MARKET_PRICE_SPIKE")
                    break

        # 7. MARKET_PRICE_COLLAPSE
        if market_state == "unfavorable" and shed_stock > 20:
            indicators.append("MARKET_PRICE_COLLAPSE")

        # 8. MATURE_CROP_NEAR_TERMINAL
        if step >= 680 and mature_coords:
            indicators.append("MATURE_CROP_NEAR_TERMINAL")

        # 9. UNUSED_SHED_CAPACITY
        if 150 <= step <= 600 and shed_stock < 20 and mature_coords:
            indicators.append("UNUSED_SHED_CAPACITY")

        # 10. UNUSED_WORKER_CAPACITY
        for idx, w in enumerate(workers):
            if sum(w.cargo.values()) == 0:
                w_pos = w.position
                is_near = any(abs(w_pos[0] - mr) + abs(w_pos[1] - mc) <= 1 for mr, mc in mature_coords)
                if is_near:
                    indicators.append("UNUSED_WORKER_CAPACITY")
                    break

        # 11. PRODUCTION_INPUT_MISMATCH
        # Raw produce present in shed with available worker but no conversion
        raw_items = ["STRAWBERRY", "MELON", "PUMPKIN", "GRAPE", "MILK", "WOOL"]
        has_raw = any(econ_state.farm.shed_inventory.get(item, 0) >= 5 for item in raw_items)
        if has_raw and worker_state == "idle":
            indicators.append("PRODUCTION_INPUT_MISMATCH")

        # 12. DEPENDENCY_BOTTLENECK
        if production_state == "dependency-limited":
            indicators.append("DEPENDENCY_BOTTLENECK")

        # 13. MARKET_COLLISION
        if pressure_state and getattr(pressure_state, "market_collision_risk", False):
            indicators.append("MARKET_COLLISION")

        # 14. OPPONENT_PRESSURE
        if opponent_state == "high_pressure":
            indicators.append("OPPONENT_PRESSURE")

        # 15. ROUTE_CONGESTION
        if len(workers) > 1:
            for i in range(len(workers)):
                for j in range(i + 1, len(workers)):
                    p1 = workers[i].position
                    p2 = workers[j].position
                    if abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) <= 1:
                        indicators.append("ROUTE_CONGESTION")
                        break

        # 16. TERMINAL_RUNWAY_ASYMMETRY
        if terminal_state in ("terminal_runway_tight", "liquidation_phase") and shed_stock > 0 and not has_sell:
            indicators.append("TERMINAL_RUNWAY_ASYMMETRY")

        return indicators
