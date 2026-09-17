# SPDX-License-Identifier: MIT
"""Adaptive Counterfactual Horizon Selector and Mechanism Horizon Policy (§8, §12, §22)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aec.config import AECConfig
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


class MechanismHorizonPolicy:
    """Deterministic, explainable horizon selection policy driven by mechanism semantics and state features."""

    def select_horizon(
        self,
        patch: CoupledPatch,
        econ_state: EconomicState,
        config: AECConfig,
        future_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        horizon, _ = self.explain_horizon(patch, econ_state, config, future_trajectory)
        return horizon

    def explain_horizon(
        self,
        patch: CoupledPatch,
        econ_state: EconomicState,
        config: AECConfig,
        future_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[int, str]:
        """Returns (horizon, explanation) based strictly on state features and mechanism requirements."""
        remaining = econ_state.remaining_horizon
        if remaining <= 1:
            return 1, "End of game proximity (remaining <= 1)"

        fam = getattr(patch, "mechanism_family", "")
        patch_id = patch.source_opportunity_id or patch.patch_id

        # 1. LOCAL_WEED_DIG: short if no dependency chain, extended if downstream dependency exists
        if fam == "LOCAL_WEED_DIG" or "WEED_DIG" in patch_id:
            # Check for downstream dependency in future trajectory
            dep_step = self._find_downstream_dependency_step(patch, econ_state, future_trajectory)
            if dep_step is not None:
                # Horizon needs to capture the step of the dependent action plus verification padding
                needed = max(config.short_horizon, dep_step + 3)
                h = min(remaining, max(needed, config.normal_horizon))
                return max(1, h), f"LOCAL_WEED_DIG downstream dependency at offset +{dep_step}; horizon {h}"
            else:
                h = min(remaining, config.short_horizon)
                return max(1, h), f"LOCAL_WEED_DIG no downstream dependency detected; fast-reject short horizon {h}"

        # 2. DEPENDENCY_AWARE_MARKET_TIMING / FRONTLOAD_ORDERS
        elif fam in ("DEPENDENCY_AWARE_MARKET_TIMING", "FRONTLOAD_ORDERS") or "MARKET_TIMING" in patch_id or "FRONTLOAD" in patch_id:
            opp_active = self._has_opponent_market_activity(econ_state, patch)
            if opp_active:
                h = min(remaining, config.normal_horizon)
                return max(1, h), f"{fam} opponent market interaction active; normal horizon {h}"
            else:
                h = min(remaining, config.short_horizon)
                return max(1, h), f"{fam} isolated order reorder; short horizon {h}"

        # 3. TERMINAL_LIQUIDATION: terminal-local simulation
        elif fam == "TERMINAL_LIQUIDATION" or "TERMINAL_LIQUIDATE" in patch_id:
            h = min(remaining, 2)
            return max(1, h), f"TERMINAL_LIQUIDATION step 718 liquidation; terminal-local horizon {h}"

        # 4. PHASE_SHUTDOWN: phase-local simulation
        elif fam == "PHASE_SHUTDOWN" or "SHUTDOWN" in patch_id:
            h = min(remaining, config.short_horizon)
            return max(1, h), f"PHASE_SHUTDOWN dead-input trim verification; phase-local horizon {h}"

        # 5. EMERGENCY_FEED_PURCHASE / RESOURCE_CONVERSION (§10, §12)
        elif fam in ("EMERGENCY_FEED_PURCHASE", "RESOURCE_CONVERSION") or "FEED" in patch_id or "CONV" in patch_id:
            if remaining <= 48:
                return max(1, remaining), f"{fam} terminal proximity; evaluating full remaining horizon {remaining}"
            else:
                h = min(remaining, max(patch.expected_horizon, config.normal_horizon))
                return max(1, h), f"{fam} standard horizon {h}"

        # 6. Terminal endgame proximity overrides for all other mechanisms
        elif remaining <= 12:
            return min(remaining, 12), f"Terminal endgame window proximity; horizon {min(remaining, 12)}"

        # 7. Fallback / Standard economic patches
        else:
            h = min(remaining, max(patch.expected_horizon, config.normal_horizon))
            return max(1, h), f"Standard economic patch horizon {h}"

    def _find_downstream_dependency_step(
        self,
        patch: CoupledPatch,
        econ_state: EconomicState,
        future_trajectory: Optional[List[Dict[str, Any]]]
    ) -> Optional[int]:
        """Detect whether a worker has a scheduled plant or build action on the dug tile."""
        if not future_trajectory:
            return None

        # Find worker and target tile
        worker_id = 0
        if patch.worker_mutations:
            worker_id = next(iter(patch.worker_mutations.keys()))
        worker = econ_state.workers.get_worker(worker_id)
        if not worker:
            return None

        wx, wy = worker.position

        for offset, act in enumerate(future_trajectory):
            commands = []
            if worker_id == 0:
                commands = act.get("farmer", ["PASS"])
            else:
                hands = act.get("hands", []) or []
                h_idx = worker_id - 1
                commands = hands[h_idx] if h_idx < len(hands) else ["PASS"]

            if not isinstance(commands, (list, tuple)) or not commands:
                continue

            op = commands[0]
            if op == "NORTH":
                wy -= 1
            elif op == "SOUTH":
                wy += 1
            elif op == "EAST":
                wx += 1
            elif op == "WEST":
                wx += 1

            if (wx, wy) == worker.position:
                if op in ("PLANT", "BUILD_COOP", "BUILD_PASTURE"):
                    return offset + 1

        return None

    def _has_opponent_market_activity(
        self,
        econ_state: EconomicState,
        patch: CoupledPatch
    ) -> bool:
        """Check if opponent has forecasted supply or activity in the goods being sold."""
        if not patch.market_mutations:
            return False

        sold_items = {
            o[1] for o in patch.market_mutations
            if isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL"
        }

        # Check opponent supply forecast
        for item in sold_items:
            if econ_state.opponent.supply_forecast.get(item, 0.0) > 0.0:
                return True

        # Check general opponent cash / activity presence
        return econ_state.opponent.observed_cash > 0.0


def select_adaptive_horizon(
    patch: CoupledPatch,
    econ_state: EconomicState,
    config: AECConfig,
    future_trajectory: Optional[List[Dict[str, Any]]] = None
) -> int:
    """Wrapper function preserving backward compatibility with existing calls."""
    policy = MechanismHorizonPolicy()
    return policy.select_horizon(patch, econ_state, config, future_trajectory)
