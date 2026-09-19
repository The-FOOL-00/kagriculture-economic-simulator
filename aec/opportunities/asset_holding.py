# SPDX-License-Identifier: MIT
"""Phase 015: Asset-Holding Valuation Trigger & Persistent Opportunity Analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    CROPS,
    PRODUCTS,
    ScientificStatus,
    SHED_CAPACITY,
    FINAL_STEP,
)
from aec.events.event_types import Event, EventType
from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES
from aec.opportunities.base import Opportunity


class OpportunityLifecycle(str, Enum):
    """Lifecycle state machine for persistent economic opportunities (§9)."""
    OPPORTUNITY_OPEN = "OPPORTUNITY_OPEN"
    PENDING = "PENDING"
    CANDIDATE_GENERATED = "CANDIDATE_GENERATED"
    COMMITTED = "COMMITTED"
    INVALIDATED = "INVALIDATED"


class RealizationOption(str, Enum):
    """Feasible realization modes identified for held inventory (§10)."""
    KEEP = "KEEP"
    SELL_NOW = "SELL_NOW"
    SELL_PARTIAL = "SELL_PARTIAL"
    SELL_LATER = "SELL_LATER"
    TERMINAL_LIQUIDATE = "TERMINAL_LIQUIDATE"
    REPOSITION = "REPOSITION"


class HoldingOpportunityType(str, Enum):
    """Six structural opportunity types defined in Phase 015 (§7)."""
    FAVOURABLE_MARKET_HOLDING = "FAVOURABLE_MARKET_HOLDING"
    TERMINAL_HOLDING_RISK = "TERMINAL_HOLDING_RISK"
    LIQUIDITY_HOLDING_CONFLICT = "LIQUIDITY_HOLDING_CONFLICT"
    MARKET_SATURATION_RISK = "MARKET_SATURATION_RISK"
    OPPONENT_PRESSURE = "OPPONENT_PRESSURE"
    DEPENDENCY_COUPLED_HOLDING = "DEPENDENCY_COUPLED_HOLDING"


@dataclass(frozen=True)
class AssetHoldingFingerprint:
    """Structural identity of an asset-holding economic state (§9, §40).
    
    Guarantees persistence without event spam: identical states across consecutive
    turns share the same fingerprint, enabling deduplication.
    """
    commodity: str
    quantity_band: int        # e.g., qty // 10
    price_band: int           # e.g., round(price_ratio / 0.05)
    terminal_phase: str       # EARLY, MID, LATE, TERMINAL
    dependency_status: str    # RESERVED vs UNCOMMITTED
    opponent_pressure: str    # LOW, HIGH

    def fingerprint_string(self) -> str:
        return (
            f"{self.commodity}_q{self.quantity_band}_p{self.price_band}_"
            f"{self.terminal_phase}_{self.dependency_status}_{self.opponent_pressure}"
        )


@dataclass
class StructuralHoldingFeatures:
    """Pure structural features of held inventory without ad-hoc dollar holding costs (§6)."""
    commodity: str
    quantity_held: int
    uncommitted_quantity: int
    current_price: float
    base_price: float
    price_ratio: float
    price_trajectory: str         # "RISING", "STABLE", "FALLING"
    storage_utilization: float    # 0.0 to 1.0
    terminal_runway: int          # steps until 718
    cash_on_hand: float
    wage_buffer_needed: float
    liquidity_deficit: float
    rival_proximity: int          # min steps of rival with cargo to town
    realization_options: List[str] = field(default_factory=list)
    fingerprint: Optional[AssetHoldingFingerprint] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commodity": self.commodity,
            "quantity_held": self.quantity_held,
            "uncommitted_quantity": self.uncommitted_quantity,
            "current_price": round(self.current_price, 2),
            "base_price": round(self.base_price, 2),
            "price_ratio": round(self.price_ratio, 3),
            "price_trajectory": self.price_trajectory,
            "storage_utilization": round(self.storage_utilization, 3),
            "terminal_runway": self.terminal_runway,
            "cash_on_hand": round(self.cash_on_hand, 2),
            "liquidity_deficit": round(self.liquidity_deficit, 2),
            "realization_options": list(self.realization_options),
            "fingerprint": self.fingerprint.fingerprint_string() if self.fingerprint else None,
        }


class AssetHoldingValuationTrigger:
    """State-level opportunity detector for persistent asset-holding value (§4, §5, §6, §7).
    
    Detects when holding vs realizing/repositioning already-held assets becomes
    economically interesting, even when delta(cash) == 0 and delta(shed) == 0.
    """

    def __init__(self) -> None:
        # History of evaluated fingerprints and their lifecycle
        self._evaluated_fingerprints: Dict[str, OpportunityLifecycle] = {}
        self._rejected_fingerprints: Set[str] = set()

    def reset_step_cache(self) -> None:
        """Clear transient state if needed at episode boundaries."""
        self._evaluated_fingerprints.clear()
        self._rejected_fingerprints.clear()

    def record_counterfactual_outcome(self, fingerprint_str: str, was_accepted: bool) -> None:
        """Record exact simulation result for fingerprint deduplication (§9, §40)."""
        if was_accepted:
            self._evaluated_fingerprints[fingerprint_str] = OpportunityLifecycle.COMMITTED
            self._rejected_fingerprints.discard(fingerprint_str)
        else:
            self._evaluated_fingerprints[fingerprint_str] = OpportunityLifecycle.INVALIDATED
            self._rejected_fingerprints.add(fingerprint_str)

    def extract_structural_features(
        self,
        econ_state: EconomicState,
        commodity: str,
        pressure_state: Any = None,
    ) -> Optional[StructuralHoldingFeatures]:
        """Extracts complete structural features for a commodity held in shed or cargo (§6)."""
        shed = econ_state.farm.shed_inventory
        qty_shed = int(shed.get(commodity, 0) or 0)
        
        # Cargo held by workers
        qty_cargo = 0
        for w in econ_state.workers.workers:
            qty_cargo += int(w.cargo.get(commodity, 0) or 0)

        total_held = qty_shed + qty_cargo
        if total_held <= 0:
            return None

        # Hard Dependency Protection (§16, §19):
        # Reserve wheat needed for livestock feed security
        reserved_qty = 0
        if commodity == "WHEAT":
            animals = getattr(econ_state.farm, "animals", [])
            herd_size = len(animals)
            if herd_size > 0:
                # 3 days of feed security buffer
                reserved_qty = herd_size * 3

        uncommitted_qty = max(0, total_held - reserved_qty)

        # Market prices
        prices = econ_state.market.current_prices
        base = float(BASE_PRICES.get(commodity, 100))
        cur_price = float(prices.get(commodity, base))
        price_ratio = cur_price / max(1.0, base)

        # Price trajectory: compare current vs historical or liquidity
        liquidity = econ_state.market.get_liquidity(commodity)
        if liquidity > 1.05:
            price_traj = "RISING"
        elif liquidity < 0.95:
            price_traj = "FALLING"
        else:
            price_traj = "STABLE"

        shed_total = econ_state.farm.shed_total_units
        storage_util = shed_total / float(SHED_CAPACITY)
        runway = max(0, FINAL_STEP - econ_state.step)

        # Liquidity and obligations
        cash = float(econ_state.farm.cash)
        n_workers = len(econ_state.workers.workers)
        # Estimated wage buffer for today
        wage_buffer = n_workers * 50.0
        deficit = max(0.0, wage_buffer - cash)

        # Terminal Phase classification
        step = econ_state.step
        if step < 400:
            term_phase = "EARLY"
        elif step < 650:
            term_phase = "MID"
        elif step < 710:
            term_phase = "LATE"
        else:
            term_phase = "TERMINAL"

        # Opponent pressure
        rival_prox = 999
        opp_level = "LOW"
        if pressure_state is not None:
            rival_prox = getattr(pressure_state, "rival_distance_to_market", 999)
            if getattr(pressure_state, "market_collision_risk", False) or rival_prox <= 3:
                opp_level = "HIGH"

        dep_status = "FEED_RESERVED" if reserved_qty > 0 else "UNCOMMITTED"

        # Construct fingerprint
        qty_band = total_held // 10
        price_band = int(round(price_ratio / 0.05))
        fp = AssetHoldingFingerprint(
            commodity=commodity,
            quantity_band=qty_band,
            price_band=price_band,
            terminal_phase=term_phase,
            dependency_status=dep_status,
            opponent_pressure=opp_level,
        )

        # Determine realization options
        options = [RealizationOption.KEEP.value]
        if uncommitted_qty > 0:
            if cur_price >= base * 0.9:
                options.append(RealizationOption.SELL_NOW.value)
                if uncommitted_qty > 10:
                    options.append(RealizationOption.SELL_PARTIAL.value)
            if term_phase in ("LATE", "TERMINAL"):
                options.append(RealizationOption.TERMINAL_LIQUIDATE.value)
            if price_traj == "RISING":
                options.append(RealizationOption.SELL_LATER.value)
        if qty_cargo > 0 and shed_total < SHED_CAPACITY:
            options.append(RealizationOption.REPOSITION.value)

        return StructuralHoldingFeatures(
            commodity=commodity,
            quantity_held=total_held,
            uncommitted_quantity=uncommitted_qty,
            current_price=cur_price,
            base_price=base,
            price_ratio=price_ratio,
            price_trajectory=price_traj,
            storage_utilization=storage_util,
            terminal_runway=runway,
            cash_on_hand=cash,
            wage_buffer_needed=wage_buffer,
            liquidity_deficit=deficit,
            rival_proximity=rival_prox,
            realization_options=options,
            fingerprint=fp,
        )

    def evaluate_opportunity(
        self,
        features: StructuralHoldingFeatures,
        baseline_has_sell: bool = False,
    ) -> Optional[Tuple[HoldingOpportunityType, str, float]]:
        """Evaluates whether structural holding features warrant candidate generation (§7).
        
        Returns (OpportunityType, rationale, estimated_relevance) or None.
        Does NOT rely on delta(cash) or delta(shed).
        """
        if features.uncommitted_quantity <= 0:
            # All inventory is reserved for feed or dependencies
            return None

        # Anti-spam check: if this identical structural state was evaluated and rejected
        # in recent turns without any structural state shift, suppress duplicate spam
        if features.fingerprint:
            fp_str = features.fingerprint.fingerprint_string()
            if fp_str in self._rejected_fingerprints:
                return None

        qty = features.uncommitted_quantity
        price = features.current_price
        ratio = features.price_ratio
        step_rem = features.terminal_runway

        # Class B: Terminal Holding Risk (§7B)
        # Near terminal horizon with unliquidated inventory
        if step_rem <= 68 and qty > 0:
            relevance = qty * price
            return (
                HoldingOpportunityType.TERMINAL_HOLDING_RISK,
                f"Terminal runway {step_rem} steps remaining with {qty} {features.commodity} held; liquidation window closing",
                relevance,
            )

        # Class C: Liquidity Holding Conflict (§7C)
        # Cash deficit for upcoming wages or urgent capital while inventory sits in shed
        if features.liquidity_deficit > 0 and qty > 0 and ratio >= 0.85:
            relevance = min(features.liquidity_deficit * 1.5, qty * price)
            return (
                HoldingOpportunityType.LIQUIDITY_HOLDING_CONFLICT,
                f"Working capital deficit ${features.liquidity_deficit:.1f} with {qty} {features.commodity} available to realize",
                relevance,
            )

        # Class E: Opponent Pressure (§7E)
        # Rival approaching market with cargo or collision risk
        if features.rival_proximity <= 3 and qty > 0 and ratio >= 0.95:
            relevance = qty * price * 0.25
            return (
                HoldingOpportunityType.OPPONENT_PRESSURE,
                f"Rival approaching market (dist={features.rival_proximity}); preemption preserves depth for {qty} {features.commodity}",
                relevance,
            )

        # Class D: Market Saturation Risk (§7D)
        # High inventory held while market price is beginning to deteriorate
        if features.storage_utilization >= 0.70 and features.price_trajectory == "FALLING" and qty >= 5:
            relevance = qty * (price - features.base_price * 0.8)
            return (
                HoldingOpportunityType.MARKET_SATURATION_RISK,
                f"Shed utilization {features.storage_utilization*100:.0f}% with falling price on {features.commodity}; frontload before saturation",
                max(10.0, relevance),
            )

        # Class A: Favourable Market Holding State (§7A)
        # Persistent high price regime: price >= 1.15 * base price (or >= 1.10 with substantial volume >= 10)
        is_favorable = (ratio >= 1.15 and qty >= 3) or (ratio >= 1.10 and qty >= 10)
        if is_favorable:
            # If baseline already emitted an optimal sell order for this commodity, defer
            if baseline_has_sell:
                return None

            premium = (price - features.base_price) * qty
            relevance = max(20.0, premium)
            return (
                HoldingOpportunityType.FAVOURABLE_MARKET_HOLDING,
                f"Favorable price ${price:.1f} (+{(ratio-1.0)*100:.1f}%) on {qty} uncommitted {features.commodity} in storage",
                relevance,
            )

        # Class F: Dependency-Coupled Holding (§7F)
        # Storage clearing when shed is congested (>80 units) even at baseline price
        if features.storage_utilization >= 0.80 and qty >= 10 and ratio >= 0.95:
            relevance = qty * 5.0
            return (
                HoldingOpportunityType.DEPENDENCY_COUPLED_HOLDING,
                f"Shed congestion ({features.storage_utilization*100:.0f}%) risks incoming harvest discard; relieve {qty} {features.commodity}",
                relevance,
            )

        return None


class AssetHoldingOpportunityAnalyzer:
    """Orchestrates asset-holding valuation across all commodities in the farm portfolio."""

    def __init__(self) -> None:
        self.trigger = AssetHoldingValuationTrigger()

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None,
        pressure_state: Any = None,
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        step = econ_state.step

        # Identify which commodities baseline is currently selling
        baseline_sells: Set[str] = set()
        if baseline_action:
            for o in baseline_action.get("market", []):
                if isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL":
                    baseline_sells.add(str(o[1]))

        # Inspect all recognized game products
        shed_inv = econ_state.farm.shed_inventory
        for commodity in PRODUCTS:
            # Quick check if commodity is held anywhere
            if shed_inv.get(commodity, 0) <= 0:
                has_cargo = any(w.cargo.get(commodity, 0) > 0 for w in econ_state.workers.workers)
                if not has_cargo:
                    continue

            features = self.trigger.extract_structural_features(econ_state, commodity, pressure_state)
            if features is None:
                continue

            baseline_selling_item = (commodity in baseline_sells)
            eval_res = self.trigger.evaluate_opportunity(features, baseline_has_sell=baseline_selling_item)
            if eval_res is None:
                continue

            opp_type, rationale, est_value = eval_res
            fp_str = features.fingerprint.fingerprint_string() if features.fingerprint else ""

            # Required simulation horizon:
            # Local market tranche needs short horizon (6); terminal or liquidity needs normal (18)
            req_horizon = 6
            if opp_type in (HoldingOpportunityType.TERMINAL_HOLDING_RISK, HoldingOpportunityType.LIQUIDITY_HOLDING_CONFLICT):
                req_horizon = 18

            opp = Opportunity(
                opportunity_id=f"ASSET_HOLDING_{commodity}_S{step}",
                category="MARKET",
                event_trigger=EventType.E13_ASSET_HOLDING_STATE,
                affected_entities=[commodity, "SHED_INVENTORY"],
                estimated_economic_relevance=float(est_value),
                candidate_transformation_family="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
                dependency_info={
                    "commodity": commodity,
                    "opportunity_type": opp_type.value,
                    "structural_features": features.to_dict(),
                    "uncommitted_quantity": features.uncommitted_quantity,
                    "current_price": features.current_price,
                    "fingerprint": fp_str,
                    "realization_options": features.realization_options,
                },
                required_horizon=req_horizon,
                rationale=rationale,
                confidence=0.95,
                scientific_status=ScientificStatus.EXPERIMENTAL,
            )
            opportunities.append(opp)

        return opportunities


__all__ = [
    "OpportunityLifecycle",
    "RealizationOption",
    "HoldingOpportunityType",
    "AssetHoldingFingerprint",
    "StructuralHoldingFeatures",
    "AssetHoldingValuationTrigger",
    "AssetHoldingOpportunityAnalyzer",
]
