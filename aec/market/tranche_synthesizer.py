# SPDX-License-Identifier: MIT
"""Phase 015: Autonomous Tranche Order Synthesizer (§11, §12, §13, §14, §15, §16)."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, FINAL_STEP, PRODUCTS, ScientificStatus, SHED_CAPACITY
from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES
from aec.patches.patch import CoupledPatch


@dataclass
class SynthesizedTrancheOrder:
    """A synthesized market sell tranche candidate with complete causal telemetry (§12, §24)."""
    commodity: str
    quantity: int
    reason: str
    market_orders: List[List[Any]]
    expected_horizon: int
    structural_fingerprint: str
    estimated_revenue: float
    is_realizable: bool = True
    rejection_reason: Optional[str] = None
    why_v3_did_not_do_this: str = "V3_PASSIVE_MARKET_QUEUE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commodity": self.commodity,
            "quantity": self.quantity,
            "reason": self.reason,
            "orders": self.market_orders,
            "horizon": self.expected_horizon,
            "fingerprint": self.structural_fingerprint,
            "estimated_revenue": round(self.estimated_revenue, 2),
            "realizable": self.is_realizable,
            "rejection": self.rejection_reason,
            "why_v3_did_not_do_this": self.why_v3_did_not_do_this,
        }


class AutonomousTrancheOrderSynthesizer:
    """Synthesizes autonomous market sell actions when baseline queue is empty or passive (§11–§16)."""

    def __init__(self) -> None:
        pass

    def verify_inventory_realizability(
        self,
        econ_state: EconomicState,
        commodity: str,
        desired_quantity: int,
    ) -> Tuple[bool, int, Optional[str]]:
        """Validates the 7 hard realizability preconditions (§16).
        
        Returns (is_realizable, max_realizable_quantity, rejection_reason).
        """
        # 1. Product admissibility
        if commodity not in PRODUCTS:
            return False, 0, f"UNADMISSIBLE_PRODUCT: {commodity}"

        # 2. Total physical units in shed
        shed_qty = int(econ_state.farm.shed_inventory.get(commodity, 0) or 0)
        
        # 3. Cargo carried by workers if shed is empty
        cargo_qty = sum(int(w.cargo.get(commodity, 0) or 0) for w in econ_state.workers.workers)
        
        total_physical = shed_qty + cargo_qty
        if total_physical <= 0:
            return False, 0, f"ZERO_PHYSICAL_INVENTORY: {commodity}"

        # 4. Hard Feed Dependency Protection (§16, §19):
        # Never sell wheat needed to prevent livestock starvation
        reserved_qty = 0
        if commodity == "WHEAT":
            herd_size = 0
            if getattr(econ_state.farm, "animals", None):
                herd_size = len(econ_state.farm.animals)
            elif getattr(econ_state.farm, "production_pipeline", None):
                herd_size = sum(1 for p in econ_state.farm.production_pipeline if getattr(p, "item_type", "") == "ANIMAL")
            if herd_size == 0 and getattr(econ_state.farm, "tiles", None):
                for row in econ_state.farm.tiles:
                    for cell in row:
                        if isinstance(cell, dict) and ("animal" in cell or cell.get("kind") in ("COW", "SHEEP", "GOOSE")):
                            herd_size += 1
            if herd_size > 0:
                # 3 days of feed reserve (1 wheat/animal/day)
                reserved_qty = herd_size * 3

        uncommitted = max(0, total_physical - reserved_qty)
        if uncommitted <= 0:
            return False, 0, f"FEED_SECURITY_RESERVED: {commodity} (held={total_physical}, reserved={reserved_qty})"

        # Cap desired quantity to realizable uncommitted units
        realizable_qty = min(desired_quantity, uncommitted)
        if realizable_qty <= 0:
            return False, 0, f"INSUFFICIENT_UNCOMMITTED_QUANTITY: {desired_quantity} requested, {uncommitted} available"

        return True, realizable_qty, None

    def compute_structural_quantities(
        self,
        econ_state: EconomicState,
        commodity: str,
        uncommitted_qty: int,
    ) -> List[Tuple[int, str]]:
        """Generates bounded structural candidate quantities without combinatorial explosion (§12, §15).
        
        Anchors:
        - q_min: minimal feasible tranche (1 or 5)
        - q_dependency: capital needed to service pending wage/expansion liabilities
        - q_storage_clearing: relieve shed congestion
        - q_market_depth: single-order max parcel (up to 10)
        - q_terminal: endgame dump (steps >= 680)
        - q_full: complete uncommitted inventory
        """
        if uncommitted_qty <= 0:
            return []

        prices = econ_state.market.current_prices
        base = float(BASE_PRICES.get(commodity, 100))
        cur_price = float(prices.get(commodity, base))
        cash = float(econ_state.farm.cash)
        n_workers = len(econ_state.workers.workers)
        wage_needed = n_workers * 50.0
        cash_deficit = max(0.0, wage_needed - cash)
        shed_total = econ_state.farm.shed_total_units
        step = econ_state.step

        anchors: List[Tuple[int, str]] = []

        # 1. q_min: minimal test tranche
        q_min = 1 if uncommitted_qty < 5 else 5
        anchors.append((q_min, "MINIMAL_TRANCHE"))

        # 2. q_dependency / q_liquidity: working capital clearing
        if cash_deficit > 0 and cur_price > 0:
            q_dep = min(uncommitted_qty, max(1, int(math.ceil(cash_deficit / cur_price))))
            anchors.append((q_dep, "LIQUIDITY_CLEARING"))

        # 3. q_storage_clearing: relieve congestion if shed > 80
        if shed_total >= 80:
            excess_storage = shed_total - 75
            q_stor = min(uncommitted_qty, max(1, excess_storage))
            anchors.append((q_stor, "STORAGE_CLEARING"))

        # 4. q_market_depth: single depth parcel (up to 10)
        q_depth = min(10, uncommitted_qty)
        anchors.append((q_depth, "DEPTH_COMPATIBLE_TRANCHE"))

        # 5. q_terminal: full liquidation in endgame
        if step >= 680:
            anchors.append((uncommitted_qty, "TERMINAL_LIQUIDATION"))

        # 6. q_full: full realizable liquidation
        if uncommitted_qty > 10:
            anchors.append((uncommitted_qty, "FULL_UNCOMMITTED_LIQUIDATION"))

        # Deduplicate quantities while preserving reasons
        unique_quantities: List[Tuple[int, str]] = []
        seen_q: Set[int] = set()
        for q, reason in anchors:
            q_clamped = max(1, min(q, uncommitted_qty))
            if q_clamped not in seen_q:
                seen_q.add(q_clamped)
                unique_quantities.append((q_clamped, reason))

        # Bound to at most 4 candidate quantities per turn
        return unique_quantities[:4]

    def construct_sequential_market_orders(
        self,
        baseline_market_orders: List[Any],
        commodity: str,
        quantity: int,
    ) -> List[List[Any]]:
        """Constructs valid market orders respecting engine limits and sequential semantics (§14).
        
        Rules:
        1. Max 10 orders per turn.
        2. Max 10 units per atomic order: if quantity > 10, partition into multiple orders.
        3. Non-commutativity: SELL orders placed ahead of BUY orders to unlock liquidity.
        """
        # Partition quantity into atomic orders of at most 10 units each
        sell_orders: List[List[Any]] = []
        rem = quantity
        while rem > 0:
            parcel = min(10, rem)
            sell_orders.append(["SELL", commodity, parcel])
            rem -= parcel

        # If baseline already had market orders, evaluate sequential interleaving
        base_orders = copy.deepcopy(baseline_market_orders or [])
        
        # Partition base orders into buys vs sells
        buys = [o for o in base_orders if isinstance(o, (list, tuple)) and o and o[0].startswith("BUY")]
        sells = [o for o in base_orders if isinstance(o, (list, tuple)) and o and o[0] == "SELL"]

        # Insert new sell orders first (unlocks liquidity), then existing sells, then buys
        merged = sell_orders + sells + buys
        return merged[:10]

    def determine_why_v3_did_not_do_this(
        self,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        commodity: str,
    ) -> str:
        """Determines the exact causal reason why V3 omitted this action (§35)."""
        base_mkt = baseline_action.get("market", [])
        if not base_mkt:
            # Check worker status
            workers = econ_state.workers.workers
            if workers:
                f_act = baseline_action.get("farmer", ["PASS"])
                if f_act and f_act[0] == "MOVE":
                    return "V3_WORKER_TRAVELING: Backbone macro scheduler prioritized field transit over market clearing."
                if f_act and f_act[0] in ("PLANT", "TEND", "WATER", "HARVEST"):
                    return "V3_FIELD_PRODUCTION: Backbone scheduled field production tasks with zero market order emission."
            return "V3_PASSIVE_MARKET_QUEUE: Backbone emitted empty market queue []."
        
        # If baseline had buy orders but no sell orders
        has_sell = any(isinstance(o, (list, tuple)) and o and o[0] == "SELL" for o in base_mkt)
        if not has_sell:
            return "V3_BUY_ONLY_QUEUE: Backbone scheduled capital purchases without liquidating stored produce."

        return "V3_DIFFERENT_PORTFOLIO: Baseline sold different commodities or quantities."

    def synthesize_candidates(
        self,
        opportunity: Any,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
    ) -> List[CoupledPatch]:
        """Compiles an asset-holding opportunity into a set of candidate CoupledPatch objects (§12)."""
        commodity = opportunity.affected_entities[0] if opportunity.affected_entities else ""
        if not commodity or commodity not in PRODUCTS:
            dep = opportunity.dependency_info or {}
            commodity = dep.get("commodity", "")
        if not commodity:
            return []

        dep_info = opportunity.dependency_info or {}
        fp_str = dep_info.get("fingerprint", f"{commodity}_s{econ_state.step}")
        desired_uncommitted = int(dep_info.get("uncommitted_quantity", 0) or 0)

        # Realizability verification
        is_realizable, max_realizable, reason = self.verify_inventory_realizability(
            econ_state, commodity, desired_uncommitted or 100
        )
        if not is_realizable or max_realizable <= 0:
            return []

        # Generate structural candidate quantities
        structural_quantities = self.compute_structural_quantities(
            econ_state, commodity, max_realizable
        )
        if not structural_quantities:
            return []

        why_v3 = self.determine_why_v3_did_not_do_this(econ_state, baseline_action, commodity)
        base_market = baseline_action.get("market", [])
        prices = econ_state.market.current_prices
        base_price = float(BASE_PRICES.get(commodity, 100))
        cur_price = float(prices.get(commodity, base_price))

        patches: List[CoupledPatch] = []

        for q, q_reason in structural_quantities:
            # Construct sequential market orders
            market_mutations = self.construct_sequential_market_orders(base_market, commodity, q)

            # Adaptive horizon selection (§38):
            # Short horizon (6) for quick market clearing; medium (18) if liquidity or terminal
            req_horizon = 6
            if q_reason in ("LIQUIDITY_CLEARING", "TERMINAL_LIQUIDATION") or econ_state.step >= 650:
                req_horizon = 18

            patch_id = f"PATCH_AUTONOMOUS_TRANCHE_{commodity}_q{q}_S{econ_state.step}"
            est_rev = q * cur_price

            patch = CoupledPatch(
                patch_id=patch_id,
                source_opportunity_id=opportunity.opportunity_id,
                mechanism_family="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
                market_mutations=market_mutations,
                expected_horizon=req_horizon,
                rationale=f"Autonomous sell tranche: {q} {commodity} ({q_reason}) at ${cur_price:.1f}",
            )

            # Attach causal and structural metadata
            patch.dependency_info = {
                "commodity": commodity,
                "quantity": q,
                "reason": q_reason,
                "structural_fingerprint": fp_str,
                "estimated_revenue": est_rev,
                "uncommitted_quantity": max_realizable,
                "why_v3_did_not_do_this": why_v3,
                "is_autonomous_synthesis": True,
            }
            patches.append(patch)

        return patches


__all__ = [
    "SynthesizedTrancheOrder",
    "AutonomousTrancheOrderSynthesizer",
]
