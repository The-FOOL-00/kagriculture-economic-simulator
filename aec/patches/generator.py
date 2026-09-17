# SPDX-License-Identifier: MIT
"""Candidate Patch Generator from Opportunities."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from aec.config import AECConfig, ENABLED_FOUNDATION_MECHANISMS, PRODUCTS
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.patches.patch import CoupledPatch


def reorder_frontload(market_orders: List[List[Any]]) -> List[List[Any]]:
    """Partition orders into Group A (SELLs), Group B (BUY_PRODUCT), Group C (Capital)."""
    A, B, C = [], [], []
    for o in market_orders:
        if not isinstance(o, (list, tuple)) or not o:
            continue
        op = o[0]
        if op == "SELL":
            A.append(list(o))
        elif op == "BUY_PRODUCT":
            B.append(list(o))
        else:
            C.append(list(o))
    return (A + B + C)[:10]


class PatchGenerator:
    """Compiles detected opportunities into concrete CoupledPatch proposals with mechanism gating (§8, §11)."""

    def __init__(
        self,
        config: Optional[AECConfig] = None,
        enabled_mechanisms: Optional[Any] = None
    ) -> None:
        if config is not None:
            self.enabled_mechanisms = set(config.enabled_mechanisms)
        elif enabled_mechanisms is not None:
            self.enabled_mechanisms = set(enabled_mechanisms)
        else:
            self.enabled_mechanisms = set(ENABLED_FOUNDATION_MECHANISMS)

        self.last_quarantined_count: int = 0
        self.last_quarantined_by_mechanism: Dict[str, int] = {}

    def generate_patches(
        self,
        opportunities: List[Opportunity],
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        config: Optional[AECConfig] = None
    ) -> List[CoupledPatch]:
        enabled = set(config.enabled_mechanisms) if config is not None else self.enabled_mechanisms
        self.last_quarantined_count = 0
        self.last_quarantined_by_mechanism = {}

        patches: List[CoupledPatch] = []

        for opp in opportunities:
            fam = opp.candidate_transformation_family
            
            # Layer 2 Mechanism Enforcement: Refuse any disabled transformation family
            if fam not in enabled:
                self.last_quarantined_count += 1
                self.last_quarantined_by_mechanism[fam] = self.last_quarantined_by_mechanism.get(fam, 0) + 1
                continue
            
            # 1. Route / Weed Dig
            if fam == "LOCAL_WEED_DIG":
                worker_id = opp.dependency_info.get("worker_id", 0)
                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_mutations={worker_id: ["DIG"]},
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 2. Market Front-Loading
            elif fam == "FRONTLOAD_ORDERS":
                current_orders = baseline_action.get("market", [])
                reordered = reorder_frontload(current_orders)
                if reordered != current_orders:
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        market_mutations=reordered,
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

            # 3. Opponent Preempt Sell
            elif fam == "OPPONENT_PREEMPT_SELL":
                item = opp.dependency_info.get("item")
                qty = opp.dependency_info.get("qty", 1)
                orders = copy.deepcopy(baseline_action.get("market", []))
                
                # Check if item already being sold
                merged = False
                for o in orders:
                    if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                        o[2] = int(o[2]) + qty
                        merged = True
                        break
                if not merged and len(orders) < 10:
                    orders.insert(0, ["SELL", item, qty])
                    
                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    market_mutations=orders[:10],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 4. Terminal Liquidation
            elif fam == "TERMINAL_LIQUIDATION":
                shed = econ_state.farm.shed_inventory
                prices = econ_state.market.current_prices
                # Sort products by total value descending
                sorted_items = sorted(
                    [p for p in PRODUCTS if shed.get(p, 0) > 0],
                    key=lambda p: -(shed[p] * prices.get(p, 1))
                )
                liq_orders = [["SELL", p, shed[p]] for p in sorted_items[:10]]
                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    market_mutations=liq_orders,
                    expected_horizon=1,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 5. Phase Shutdown
            elif fam == "PHASE_SHUTDOWN":
                crop = opp.dependency_info.get("crop")
                orders = copy.deepcopy(baseline_action.get("market", []))
                # Remove BUY_SEED for this crop
                trimmed = [
                    o for o in orders
                    if not (isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "BUY_SEED" and o[1] == crop)
                ]
                if trimmed != orders:
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        market_mutations=trimmed,
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

            # 6. Dynamic Shadow Harvest (Labor reallocation)
            elif fam == "DYNAMIC_SHADOW_HARVEST":
                worker_id = opp.dependency_info.get("worker_id", 0)
                target_xy = opp.dependency_info.get("target_xy")
                worker = econ_state.workers.get_worker(worker_id)
                if worker and target_xy:
                    wx, wy = worker.position
                    tx, ty = target_xy
                    # If already at tile: HARVEST. If adjacent or distant: step toward tile.
                    if (wx, wy) == (tx, ty):
                        cmd = ["HARVEST"]
                    elif tx > wx:
                        cmd = ["EAST"]
                    elif tx < wx:
                        cmd = ["WEST"]
                    elif ty > wy:
                        cmd = ["SOUTH"]
                    else:
                        cmd = ["NORTH"]
                        
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        worker_mutations={worker_id: cmd},
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

        return patches

