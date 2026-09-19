# SPDX-License-Identifier: MIT
"""Shop and Production Arbitrage Opportunity Architecture (§16)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import (
    CROP_GROWTH_DAYS,
    CROP_SEED_PRICE,
    EPISODE_STEPS,
    PRODUCTS,
    SHED_CAPACITY,
    SHOP_UNLOCK_INTERVAL,
    ScientificStatus,
    TURNS_PER_DAY,
)
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.opportunities.town_cycle import compute_required_liquidity


@dataclass
class ProductionArbitrageOpportunity(Opportunity):
    """An opportunity executing a full production graph: cash -> input -> production -> output -> sale (§16)."""
    input_item: str = ""
    input_cost: float = 0.0
    output_item: str = ""
    expected_output_units: int = 1
    expected_gross_revenue: float = 0.0
    production_duration_steps: int = 48
    net_projected_profit: float = 0.0
    liquidity_impact: float = 0.0


@dataclass
class ShopArbitrageOpportunity(Opportunity):
    """An opportunity exploiting realizable market arbitrage (§6, §7, §8, §9, §10)."""
    item: str = ""
    transformation_type: str = "BUY_HOLD_SELL"  # BUY_HOLD_SELL, SELL_BUY_SELL, DELAY_SALE_DEPTH
    purchase_price: float = 0.0
    target_sale_price: float = 0.0
    expected_margin: float = 0.0
    unlock_step: int = 0
    acquisition_cost: float = 0.0
    realization_value: float = 0.0
    gross_spread: float = 0.0
    worker_opportunity_cost: float = 0.0
    liquidity_cost: float = 0.0
    capacity_cost: float = 0.0
    timing_cost: float = 0.0
    dependency_risk: float = 0.0
    terminal_risk: float = 0.0
    net_realizable_spread: float = 0.0
    is_realizable: bool = True
    rejection_reason: Optional[str] = None
    market_sequence: List[List[Any]] = field(default_factory=list)


class ProductionArbitrageDetector:
    r"""Evaluates the viability of cash -> input -> production -> output -> sale.
    
    Strict constraints enforced:
    1. Upfront liquidity check ($C_{upfront} \le Cash - SafetyBuffer$).
    2. Terminal deadline check (Step + Duration < FinalStep 718).
    3. Labor requirement accounting (Worker hours valued against opportunity cost).
    """

    def detect(
        self,
        econ_state: EconomicState,
        min_net_margin: float = 50.0
    ) -> List[ProductionArbitrageOpportunity]:
        opportunities: List[ProductionArbitrageOpportunity] = []
        step = econ_state.step
        cash = econ_state.cash

        # Evaluate each crop production pipeline
        for crop, seed_cost in CROP_SEED_PRICE.items():
            growth_days = CROP_GROWTH_DAYS.get(crop, 2)
            duration_steps = growth_days * TURNS_PER_DAY + 8  # growth + planting + harvest + drop + sell
            
            # Terminal realization check: must mature and sell before step 718
            if step + duration_steps >= 718:
                continue

            # Liquidity check
            if cash < seed_cost + 100.0:
                continue

            # Market revenue estimate
            current_price = econ_state.market.prices.get(crop, 0.0)
            gross = float(current_price) * 1.0  # single crop yield
            net_profit = gross - seed_cost - 10.0  # seed cost + estimated worker labor cost ($10)

            if net_profit >= min_net_margin:
                opportunities.append(ProductionArbitrageOpportunity(
                    opportunity_id=f"PROD_ARB_{step}_{crop}",
                    category="RESOURCE",
                    event_trigger=None,
                    affected_entities=[crop],
                    estimated_economic_relevance=net_profit,
                    candidate_transformation_family="PRODUCTION_ARBITRAGE",
                    required_horizon=min(72, duration_steps),
                    rationale=f"Production arbitrage: Buy {crop} seed (${seed_cost}) -> mature {growth_days}d -> gross ${gross:.1f} -> net ${net_profit:.1f}.",
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    input_item=f"{crop}_SEED",
                    input_cost=float(seed_cost),
                    output_item=crop,
                    expected_output_units=1,
                    expected_gross_revenue=gross,
                    production_duration_steps=duration_steps,
                    net_projected_profit=net_profit,
                    liquidity_impact=-float(seed_cost),
                ))

        return opportunities


class ShopArbitrageDetector:
    """Evaluates realizable market arbitrage opportunities (§6, §7, §8, §9, §10, §11).
    
    Adheres strictly to Group 3 principles:
    1. Explanatory structural quantities: GrossSpread, AcquisitionCost, RealizationValue,
       WorkerOpportunityCost, LiquidityCost, CapacityCost, TimingCost, DependencyRisk, TerminalRisk.
    2. Exact sequential market non-commutativity: BUY -> SELL != SELL -> BUY.
    3. Hard structural liquidity safety against upcoming seed, feed, and wage obligations.
    4. Terminal realization feasibility (must complete before step 718 cutoff).
    5. Shed capacity limit (SHED_CAPACITY = 100).
    6. Opponent pressure market depth discounting.
    """

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None,
        pressure_state: Optional[Any] = None,
    ) -> List[ShopArbitrageOpportunity]:
        opportunities: List[ShopArbitrageOpportunity] = []
        step = econ_state.step
        cash = float(econ_state.farm.cash)
        shed_units = econ_state.farm.shed_total_units
        rem_steps = max(0, 718 - step)

        # 1. Terminal Realization Feasibility: No arbitrage can complete if step >= 710 or rem_steps <= 8
        if step >= 710 or rem_steps <= 8:
            return []

        req_liquidity = compute_required_liquidity(econ_state, horizon_steps=12)

        # Check town shop unlock windows (every 72 steps) and town consumption ticks (every 4 steps)
        steps_to_tick = econ_state.market.steps_to_town_tick
        next_unlock = ((step // SHOP_UNLOCK_INTERVAL) + 1) * SHOP_UNLOCK_INTERVAL
        steps_to_unlock = next_unlock - step
        is_tick_near = (1 <= steps_to_tick <= 4)
        is_unlock_near = (1 <= steps_to_unlock <= 12)

        # Evaluate across commodities
        for item in PRODUCTS:
            p_curr = float(econ_state.market.get_price(item))
            buy_price = float(getattr(econ_state.market, "buy_prices", {}).get(item, p_curr * 1.05))

            # Determine projected realization price
            # Priority: explicit fixture/override -> town consumption tick -> unlock window -> base
            projected_sale_price = None
            if hasattr(econ_state.market, "projected_prices") and item in econ_state.market.projected_prices:
                projected_sale_price = float(econ_state.market.projected_prices[item])
            elif is_tick_near and econ_state.market.expected_absorption.get(item, 0) > 0:
                abs_qty = econ_state.market.expected_absorption[item]
                projected_sale_price = p_curr * (1.10 + 0.05 * min(3, abs_qty))
            elif is_unlock_near:
                projected_sale_price = p_curr * 1.20
            else:
                projected_sale_price = p_curr

            # Must have positive gross unit margin before costs
            if projected_sale_price <= buy_price:
                continue

            # Target parcel quantity
            qty = 2
            acq_cost = buy_price * qty
            real_val = projected_sale_price * qty
            gross_spread = real_val - acq_cost

            # Explanatory quantities
            worker_opp_cost = 0.0
            liquidity_cost = 0.0
            capacity_cost = 0.0
            hold_steps = steps_to_tick if is_tick_near else steps_to_unlock
            timing_cost = 0.02 * acq_cost * max(1, hold_steps)
            dependency_risk = 0.0
            terminal_risk = 0.0
            is_realizable = True
            rejection_reason: Optional[str] = None

            # 1. Terminal Risk: Require at least 2 steps after hold for sale/liquidation
            if (step + hold_steps + 2) >= 718:
                terminal_risk = 999.0
                is_realizable = False
                rejection_reason = f"Unrealizable before terminal cutoff (step {step + hold_steps + 2} >= 718)"

            # 2. Shed Capacity Constraint
            if (shed_units + qty) > SHED_CAPACITY:
                capacity_cost = 500.0
                is_realizable = False
                rejection_reason = f"Shed capacity overflow ({shed_units + qty} > {SHED_CAPACITY})"

            # 3. Structural Liquidity Constraint
            if cash < acq_cost:
                liquidity_cost = 999.0
                is_realizable = False
                rejection_reason = f"Insufficient cash for acquisition (${cash:.1f} < ${acq_cost:.1f})"
            elif (cash - acq_cost) < req_liquidity:
                deficit = req_liquidity - (cash - acq_cost)
                liquidity_cost = deficit * 2.5
                is_realizable = False
                rejection_reason = f"Capital depletion: post-purchase cash (${cash - acq_cost:.1f}) < required liquidity (${req_liquidity:.1f})"

            # 4. Worker Opportunity Cost
            # Check if all workers are committed to field operations
            if getattr(econ_state, "workers_busy_with_harvest", False):
                worker_opp_cost = 100.0
                is_realizable = False
                rejection_reason = "Workers fully committed to higher-priority field harvest"

            # 5. Opponent Pressure on Market Depth
            opp_pressure = 0.0
            if pressure_state is not None:
                opp_pressure = getattr(pressure_state, "sale_pressure", {}).get(item, 0.0)
            elif econ_state.opponent is not None:
                opp_pressure = getattr(econ_state.opponent, "sale_pressure", {}).get(item, 0.0)
            if opp_pressure >= 0.4:
                haircut = real_val * min(0.6, opp_pressure * 0.7)
                dependency_risk += haircut
                real_val -= haircut
                gross_spread = real_val - acq_cost

            # 6. Net Realizable Spread Gate
            net_spread = gross_spread - worker_opp_cost - liquidity_cost - capacity_cost - timing_cost - dependency_risk - terminal_risk
            if is_realizable and net_spread <= 0.0:
                is_realizable = False
                rejection_reason = f"Net realizable spread <= 0 (${net_spread:.1f}) after opportunity and liquidity costs"

            # 7. Formulate Sequential Market Sequence (preserving non-commutativity)
            market_seq: List[List[Any]] = []
            trans_type = "BUY_HOLD_SELL"

            # Check if SELL_BUY_SELL resolves a temporary liquidity deficit
            if not is_realizable and ("Capital depletion" in (rejection_reason or "") or "Insufficient cash" in (rejection_reason or "")):
                # Can selling an existing shed item fund this purchase?
                shed_inv = getattr(econ_state.farm, "shed_inventory", {})
                sell_item = next((p for p, q in shed_inv.items() if q > 0 and p != item), None)
                if sell_item:
                    sell_qty = min(5, shed_inv[sell_item])
                    sell_rev = float(econ_state.market.get_price(sell_item)) * sell_qty
                    if (cash + sell_rev) >= acq_cost and (cash + sell_rev - acq_cost) >= req_liquidity:
                        # Non-commutative sequence: SELL strictly precedes BUY!
                        market_seq = [["SELL", sell_item, sell_qty], ["BUY_PRODUCT", item, qty]]
                        is_realizable = True
                        rejection_reason = None
                        liquidity_cost = 0.0
                        trans_type = "SELL_BUY_SELL"
                        net_spread = gross_spread - timing_cost - dependency_risk
                    else:
                        market_seq = [["BUY_PRODUCT", item, qty]]
                else:
                    market_seq = [["BUY_PRODUCT", item, qty]]
            else:
                market_seq = [["BUY_PRODUCT", item, qty]]


            opportunities.append(ShopArbitrageOpportunity(
                opportunity_id=f"SHOP_ARB_{step}_{item}_{qty}",
                category="MARKET",
                event_trigger=None,
                affected_entities=[item],
                estimated_economic_relevance=max(0.0, net_spread),
                candidate_transformation_family="SHOP_ARBITRAGE",
                required_horizon=min(24, hold_steps + 4),
                rationale=(
                    f"Shop arbitrage on {item}: acq=${acq_cost:.1f}, real=${real_val:.1f}, "
                    f"net=${net_spread:.1f} ({'REALIZABLE' if is_realizable else rejection_reason})"
                ),
                confidence=0.9 if is_realizable else 0.2,
                scientific_status=ScientificStatus.VERIFIED_SOURCE if is_realizable else ScientificStatus.FALSIFIED,
                item=item,
                transformation_type=trans_type,
                purchase_price=buy_price,
                target_sale_price=projected_sale_price,
                expected_margin=projected_sale_price - buy_price,
                unlock_step=next_unlock,
                acquisition_cost=acq_cost,
                realization_value=real_val,
                gross_spread=gross_spread,
                worker_opportunity_cost=worker_opp_cost,
                liquidity_cost=liquidity_cost,
                capacity_cost=capacity_cost,
                timing_cost=timing_cost,
                dependency_risk=dependency_risk,
                terminal_risk=terminal_risk,
                net_realizable_spread=net_spread,
                is_realizable=is_realizable,
                rejection_reason=rejection_reason,
                market_sequence=market_seq,
                dependency_info={
                    "item": item,
                    "market_sequence": market_seq,
                    "is_realizable": is_realizable,
                    "rejection_reason": rejection_reason,
                    "net_spread": net_spread,
                    "acq_cost": acq_cost,
                    "real_val": real_val,
                }
            ))

        return opportunities

