# SPDX-License-Identifier: MIT
"""Phase 015: Autonomous Tranche Order Synthesizer (§11, §12, §13, §14, §15, §16)."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, FINAL_STEP, PRODUCTS, ScientificStatus, SHED_CAPACITY
from aec.counterfactual.macro_detector import V3_CASH_GATES
from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES
from aec.patches.patch import CoupledPatch


# Phase 018 Repair B: effective cash-boundary set mirrored from the frozen probe
# (read-only; the probe itself is never modified).
# - V3_CASH_GATES: any cross escalates (probe §3).
# - 8000.0: cash-bracket edge 2->3 (classify_cash_bracket).
# - 11000.0: Day-18 tomato proximity tripwire, only when step < 432 (probe §3).
CASH_BRACKET_EDGE_EXTRA: float = 8000.0
TOMATO_PROXIMITY_LEVEL: float = 11000.0
BOUNDARY_SAFE_EPSILON: float = 1.0
BOUNDARY_NOISE_MARGIN: float = 150.0  # probe §4 budget-guard cash tripwire
FEED_SAFE_WHEAT_FLOOR: int = 12       # probe §6: post-sale shed wheat floor
FEED_SAFE_MAX_DROP: int = 3           # probe §6: wheat drop must stay < 4
MAX_BOUNDARY_QUANTITIES: int = 4


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

    def effective_cash_boundaries(self, step: int) -> List[float]:
        """Cash levels whose crossing escalates, mirrored from the frozen probe."""
        levels = set(float(g) for g in V3_CASH_GATES)
        levels.add(CASH_BRACKET_EDGE_EXTRA)
        if step < 432:
            levels.add(TOMATO_PROXIMITY_LEVEL)
        return sorted(levels)

    def project_post_queue_cash(
        self,
        econ_state: EconomicState,
        baseline_market_orders: List[Any],
        commodity: str,
        quantity: int,
    ) -> Tuple[float, Dict[str, int]]:
        """Project post-queue (cash, shed) mirroring probe §2 arithmetic exactly.

        Uses the same merged-queue construction, price source, 20.0 fallback,
        and min(shed, qty) realization cap as MacroRegimeTransitionDetector, so
        the generator's prediction agrees with the probe's escalation input.
        """
        merged = self.construct_sequential_market_orders(
            baseline_market_orders or [], commodity, quantity
        )
        cash = float(econ_state.farm.cash)
        shed = {k: int(v) for k, v in econ_state.farm.shed_inventory.items()}
        prices = econ_state.market.current_prices
        for o in merged:
            if not isinstance(o, (list, tuple)) or len(o) < 2:
                continue
            op = o[0]
            if op == "SELL" and len(o) >= 3:
                item, qty = o[1], int(o[2])
                price = float(prices.get(item, 20.0))
                real_qty = min(shed.get(item, 0), qty)
                cash += real_qty * price
                shed[item] = max(0, shed.get(item, 0) - real_qty)
            elif op == "BUY_PRODUCT" and len(o) >= 3:
                item, qty = o[1], int(o[2])
                price = float(prices.get(item, 20.0))
                cash -= qty * price
                shed[item] = shed.get(item, 0) + qty
        return cash, shed

    def _herd_size(self, econ_state: EconomicState) -> int:
        """Livestock census using the same cascade as realizability gating."""
        herd_size = 0
        if getattr(econ_state.farm, "animals", None):
            herd_size = len(econ_state.farm.animals)
        elif getattr(econ_state.farm, "production_pipeline", None):
            herd_size = sum(
                1 for p in econ_state.farm.production_pipeline
                if getattr(p, "item_type", "") == "ANIMAL"
            )
        if herd_size == 0 and getattr(econ_state.farm, "tiles", None):
            for row in econ_state.farm.tiles:
                for cell in row:
                    if isinstance(cell, dict) and (
                        "animal" in cell or cell.get("kind") in ("COW", "SHEEP", "GOOSE")
                    ):
                        herd_size += 1
        return herd_size

    def _max_qty_under_cash(
        self,
        econ_state: EconomicState,
        baseline_market_orders: List[Any],
        commodity: str,
        uncommitted_qty: int,
        cash_cap: float,
    ) -> int:
        """Largest q in [0, uncommitted] with projected cash <= cash_cap."""
        best = 0
        for q in range(1, uncommitted_qty + 1):
            cash, _ = self.project_post_queue_cash(
                econ_state, baseline_market_orders, commodity, q
            )
            if cash <= cash_cap:
                best = q
        return best

    def _apply_feed_clamp(
        self, econ_state: EconomicState, commodity: str, quantity: int
    ) -> int:
        """Clamp a wheat quantity to the probe §6 non-escalating envelope."""
        if commodity != "WHEAT" or quantity <= 0:
            return quantity
        if self._herd_size(econ_state) <= 0:
            return quantity
        shed_wheat = int(econ_state.farm.shed_inventory.get("WHEAT", 0) or 0)
        headroom = shed_wheat - FEED_SAFE_WHEAT_FLOOR
        if headroom <= 0:
            return 0
        return max(0, min(quantity, headroom, FEED_SAFE_MAX_DROP))

    def compute_boundary_safe_quantities(
        self,
        econ_state: EconomicState,
        commodity: str,
        uncommitted_qty: int,
        baseline_market_orders: List[Any],
    ) -> List[Tuple[int, str]]:
        """Boundary-aware anchors: largest value capture without an avoidable cross."""
        if uncommitted_qty <= 1:
            return []
        cash0 = float(econ_state.farm.cash)
        gates = [g for g in self.effective_cash_boundaries(econ_state.step) if g > cash0]
        out: List[Tuple[int, str]] = []
        if gates:
            gate = min(gates)
            q_current = min(5, uncommitted_qty)
            cash_current, _ = self.project_post_queue_cash(
                econ_state, baseline_market_orders, commodity, q_current
            )
            q_safe = self._max_qty_under_cash(
                econ_state, baseline_market_orders, commodity, uncommitted_qty,
                gate - BOUNDARY_SAFE_EPSILON,
            )
            q_safe = self._apply_feed_clamp(econ_state, commodity, q_safe)
            binds = bool(cash_current >= gate) or (
                commodity == "WHEAT"
                and self._apply_feed_clamp(econ_state, commodity, q_current) < q_current
            )
            if binds and q_safe >= 1 and q_safe != q_current:
                out.append((q_safe, "BOUNDARY_SAFE"))
            if binds:
                q_minus = self._max_qty_under_cash(
                    econ_state, baseline_market_orders, commodity, uncommitted_qty,
                    gate - BOUNDARY_NOISE_MARGIN,
                )
                q_minus = self._apply_feed_clamp(econ_state, commodity, q_minus)
                taken = {1, q_current} | {q for q, _ in out}
                if q_minus >= 1 and q_minus not in taken:
                    out.append((q_minus, "BOUNDARY_MINUS"))
        elif commodity == "WHEAT" and self._herd_size(econ_state) > 0:
            # No cash gate binds, but a feed-safe wheat anchor may still add value.
            q_current = min(5, uncommitted_qty)
            q_feed = self._apply_feed_clamp(econ_state, commodity, uncommitted_qty)
            if q_feed >= 1 and q_feed not in (1, q_current):
                out.append((q_feed, "BOUNDARY_SAFE"))
        return out

    def compute_structural_quantities(
        self,
        econ_state: EconomicState,
        commodity: str,
        uncommitted_qty: int,
        baseline_market_orders: Optional[List[Any]] = None,
        boundary_safe: bool = False,
    ) -> List[Tuple[int, str]]:
        """Generates bounded structural candidate quantities without combinatorial explosion (§12, §15).
        
        Anchors:
        - q_min: minimal feasible tranche (1 or 5)
        - q_dependency: capital needed to service pending wage/expansion liabilities
        - q_storage_clearing: relieve shed congestion
        - q_market_depth: single-order max parcel (up to 10)
        - q_terminal: endgame dump (steps >= 680)
        - q_full: complete uncommitted inventory

        Phase 018 Repair B (boundary_safe=True): the B1 menu {q_small,
        q_current, q_boundary_safe?, q_boundary_minus?} replaces the legacy
        anchors. Legacy path executes verbatim when boundary_safe=False.
        """
        if uncommitted_qty <= 0:
            return []

        if boundary_safe:
            return self._compute_boundary_menu(
                econ_state, commodity, uncommitted_qty,
                baseline_market_orders or [],
            )

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

    def _compute_boundary_menu(
        self,
        econ_state: EconomicState,
        commodity: str,
        uncommitted_qty: int,
        baseline_market_orders: List[Any],
    ) -> List[Tuple[int, str]]:
        """Phase 018 B1 menu: {q_small, q_current} + boundary alternatives (≤4)."""
        menu: List[Tuple[int, str]] = [(1, "Q_SMALL")]
        q_current = min(5, uncommitted_qty)
        if q_current != 1:
            menu.append((q_current, "Q_CURRENT"))
        for q, reason in self.compute_boundary_safe_quantities(
            econ_state, commodity, uncommitted_qty, baseline_market_orders
        ):
            menu.append((q, reason))
        seen: Set[int] = set()
        deduped: List[Tuple[int, str]] = []
        for q, reason in menu:
            q_clamped = max(1, min(int(q), uncommitted_qty))
            if q_clamped not in seen:
                seen.add(q_clamped)
                deduped.append((q_clamped, reason))
        return deduped[:MAX_BOUNDARY_QUANTITIES]

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
        
        # Partition base orders into buys vs sells vs atomics (HIRE, etc.)
        buys = [o for o in base_orders if isinstance(o, (list, tuple)) and o and o[0].startswith("BUY")]
        sells = [o for o in base_orders if isinstance(o, (list, tuple)) and o and o[0] == "SELL"]
        others = [o for o in base_orders if isinstance(o, (list, tuple)) and o and not (o[0].startswith("BUY") or o[0] == "SELL")]

        # Insert new sell orders first (unlocks liquidity), then existing sells, then others, then buys
        merged = sell_orders + sells + others + buys
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
        boundary_safe_quantities: bool = False,
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
            econ_state,
            commodity,
            max_realizable,
            baseline_market_orders=baseline_action.get("market", []),
            boundary_safe=boundary_safe_quantities,
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
