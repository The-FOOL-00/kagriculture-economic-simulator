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


from aec.ir.market_state import BASE_PRICES


@dataclass
class ProductionArbitrageOpportunity(Opportunity):
    """An opportunity executing a marginal production transformation (§12, §13, §14, §15, §16, §17)."""
    input_item: str = ""
    input_cost: float = 0.0
    output_item: str = ""
    expected_output_units: int = 1
    expected_gross_revenue: float = 0.0
    production_duration_steps: int = 48
    net_projected_profit: float = 0.0
    liquidity_impact: float = 0.0
    target_location: Optional[Tuple[int, int]] = None
    worker_id: int = 0
    worker_tasks: List[str] = field(default_factory=list)
    is_v3_redundant: bool = False
    headroom_source: str = ""
    is_realizable: bool = True
    rejection_reason: Optional[str] = None
    market_sequence: List[List[Any]] = field(default_factory=list)


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
    """Evaluates marginal production opportunities and headroom (§12, §13, §14, §15, §16, §17, §18).
    
    Adheres strictly to Group 3 principles:
    1. Marginal Headroom Detection: Evaluates whether external conditions (market spike,
       worker release, input surplus, terminal production window) create uncaptured potential.
    2. V3 Redundancy Test: Verifies whether the V3 backbone already makes this decision.
       If already captured, classifies as ALREADY_CAPTURED_BY_BACKBONE and abstains.
    3. Structural labor opportunity cost and land availability screening.
    4. Full coupled production trajectory: reassign -> acquire -> produce -> drop -> sell.
    """

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None,
        baseline_continuation: Optional[List[Dict[str, Any]]] = None,
        min_net_margin: float = 20.0,
        include_rejected: bool = False,
    ) -> List[ProductionArbitrageOpportunity]:
        opportunities: List[ProductionArbitrageOpportunity] = []
        step = econ_state.step
        cash = float(econ_state.farm.cash)
        req_liquidity = compute_required_liquidity(econ_state, horizon_steps=24)

        # 1. Extract V3 baseline production intents (redundancy analysis)
        v3_seed_orders = set()
        if baseline_action:
            for o in baseline_action.get("market", []):
                if isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "BUY_SEED":
                    v3_seed_orders.add(str(o[1]).upper())
        if baseline_continuation:
            for c_act in baseline_continuation[:8]:
                for o in c_act.get("market", []):
                    if isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "BUY_SEED":
                        v3_seed_orders.add(str(o[1]).upper())

        # Check worker availability and displaced tasks
        workers = getattr(econ_state.workers, "workers", [])
        if not workers:
            return []

        # Find worker: prefer idle auxiliary hand (e.g. wid > 0 with PASS), else worker 0
        assigned_worker = None
        assigned_wid = 0
        worker_is_free = False
        displaced_value = 0.0

        for w in workers:
            w_action = "PASS"
            if baseline_action:
                if w.worker_id == 0:
                    cmd = baseline_action.get("farmer", ["PASS"])
                    w_action = cmd[0] if cmd else "PASS"
                else:
                    h_cmds = baseline_action.get("hands", [])
                    if w.worker_id - 1 < len(h_cmds):
                        cmd = h_cmds[w.worker_id - 1]
                        w_action = cmd[0] if cmd else "PASS"
            if w_action == "PASS" and w.worker_id > 0:
                assigned_worker = w
                assigned_wid = w.worker_id
                worker_is_free = True
                break

        if assigned_worker is None:
            assigned_worker = workers[0]
            assigned_wid = workers[0].worker_id

        # Displaced task valuation: if workers are actively harvesting melons
        if getattr(econ_state, "workers_busy_with_harvest", False):
            displaced_value = 250.0  # Displaces mature melon harvest

        # Evaluate marginal headroom for each cultivable crop
        for crop, seed_cost in CROP_SEED_PRICE.items():
            seed_item = f"{crop}_SEED"
            growth_days = CROP_GROWTH_DAYS.get(crop, 2)
            duration_steps = growth_days * TURNS_PER_DAY + 6

            is_realizable = True
            is_v3_redundant = False
            rejection_reason = None
            headroom_source = ""

            # Check terminal runway
            if (step + duration_steps) >= 718:
                is_realizable = False
                rejection_reason = f"Insufficient terminal runway ({step + duration_steps} >= 718)"

            # Check if V3 already plans to purchase this seed
            if crop in v3_seed_orders:
                is_v3_redundant = True
                is_realizable = False
                rejection_reason = f"ALREADY_CAPTURED_BY_BACKBONE: V3 already plans {crop}"

            # Check input surplus (seed already in shed / carried / farm.seeds)
            shed_inv = getattr(econ_state.farm, "shed_inventory", {})
            carried_inv = getattr(econ_state.farm, "carried_inventory", {})
            farm_seeds = getattr(econ_state.farm, "seeds", {})
            has_input_surplus = (
                farm_seeds.get(crop, 0) > 0
                or farm_seeds.get(seed_item, 0) > 0
                or shed_inv.get(seed_item, 0) > 0
                or carried_inv.get(seed_item, 0) > 0
            )
            if has_input_surplus and is_realizable:
                headroom_source = "INPUT_SURPLUS"

            # Check market pricing and shocks
            current_price = float(econ_state.market.get_price(crop))
            base_price = float(BASE_PRICES.get(crop, current_price))
            projected_price = current_price

            if hasattr(econ_state.market, "projected_prices") and crop in econ_state.market.projected_prices:
                projected_price = float(econ_state.market.projected_prices[crop])

            # Market spike condition
            if projected_price >= base_price * 1.35 and is_realizable:
                headroom_source = "MARKET_SPIKE"
            elif projected_price <= base_price * 0.60:
                is_realizable = False
                rejection_reason = f"Market collapse for {crop}: projected price ${projected_price:.1f} < 60% of base"

            # Worker free headroom
            if worker_is_free and not headroom_source and is_realizable:
                headroom_source = "WORKER_FREE"

            # Terminal window headroom: short crop (<= 2 days) can finish before 718 when step is late (580-660)
            if (580 <= step <= 660) and growth_days <= 2 and (step + duration_steps) < 718 and is_realizable:
                headroom_source = "TERMINAL_PRODUCTION_WINDOW"

            # If no specific headroom detected and not redundant
            if not headroom_source and is_realizable:
                headroom_source = "MARGINAL_HEADROOM"

            # Gross revenue and cash cost
            actual_seed_cost = 0.0 if has_input_surplus else float(seed_cost)
            gross = projected_price * 1.0
            in_cost = 0.0 if has_input_surplus else float(seed_cost)
            labor_cost = displaced_value if displaced_value > 0 else 10.0
            net_profit = gross - in_cost - (displaced_value if displaced_value > 0 else 0.0)
            if has_input_surplus:
                net_profit = gross - (displaced_value if displaced_value > 0 else 0.0)

            # Liquidity check
            if not has_input_surplus and is_realizable:
                if cash < actual_seed_cost:
                    is_realizable = False
                    rejection_reason = f"Insufficient cash for seed (${cash:.1f} < ${actual_seed_cost:.1f})"
                elif (cash - actual_seed_cost) < req_liquidity:
                    is_realizable = False
                    rejection_reason = f"Capital depletion: post-seed cash (${cash - actual_seed_cost:.1f}) < required liquidity (${req_liquidity:.1f})"

            # Labor opportunity check
            if displaced_value > 0 and net_profit <= 0 and is_realizable:
                is_realizable = False
                rejection_reason = f"Labor opportunity cost excessive: displaced ${displaced_value:.1f} > gross ${gross:.1f}"

            # Margin threshold check
            if net_profit < min_net_margin and is_realizable:
                is_realizable = False
                rejection_reason = f"Net profit ${net_profit:.1f} < minimum threshold ${min_net_margin:.1f}"

            # If V3 is already executing optimal strategy and no distinct headroom exists:
            if getattr(econ_state, "v3_already_optimal", False):
                is_v3_redundant = True
                is_realizable = False
                rejection_reason = "ALREADY_CAPTURED_BY_BACKBONE: V3 macro schedule is already optimal"

            if not include_rejected and not is_realizable:
                continue

            market_seq = [] if has_input_surplus else [["BUY_SEED", crop, 1]]
            worker_tasks = ["TILL", "PLANT", "WATER"]

            opportunities.append(ProductionArbitrageOpportunity(
                opportunity_id=f"PROD_ARB_{step}_{crop}_{assigned_wid}",
                category="RESOURCE",
                event_trigger=None,
                affected_entities=[crop, assigned_wid],
                estimated_economic_relevance=max(0.0, net_profit),
                candidate_transformation_family="PRODUCTION_ARBITRAGE",
                required_horizon=min(72, duration_steps),
                rationale=(
                    f"Production arbitrage on {crop}: gross=${gross:.1f}, net=${net_profit:.1f}, "
                    f"headroom={headroom_source} ({'REALIZABLE' if is_realizable else rejection_reason})"
                ),
                confidence=0.9 if is_realizable else 0.1,
                scientific_status=ScientificStatus.VERIFIED_SOURCE if is_realizable else ScientificStatus.FALSIFIED,
                input_item=seed_item,
                input_cost=in_cost,
                output_item=crop,
                expected_output_units=1,
                expected_gross_revenue=gross,
                production_duration_steps=duration_steps,
                net_projected_profit=net_profit - (10.0 if displaced_value == 0 and not has_input_surplus else 0.0),
                liquidity_impact=-actual_seed_cost,
                worker_id=assigned_wid,
                worker_tasks=worker_tasks,
                is_v3_redundant=is_v3_redundant,
                headroom_source=headroom_source,
                is_realizable=is_realizable,
                rejection_reason=rejection_reason,
                market_sequence=market_seq,
                dependency_info={
                    "crop": crop,
                    "worker_id": assigned_wid,
                    "worker_tasks": worker_tasks,
                    "is_realizable": is_realizable,
                    "is_v3_redundant": is_v3_redundant,
                    "rejection_reason": rejection_reason,
                    "headroom_source": headroom_source,
                    "net_profit": net_profit,
                    "market_sequence": market_seq,
                }
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
        include_rejected: bool = False,
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
            hold_steps = steps_to_unlock if is_unlock_near else (steps_to_tick if is_tick_near else 4)
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


            if not include_rejected and not is_realizable:
                continue

            opportunities.append(ShopArbitrageOpportunity(
                opportunity_id=f"SHOP_ARB_{step}_{item}_{qty}",
                category="MARKET",
                event_trigger=None,
                affected_entities=[item],
                estimated_economic_relevance=max(0.0, net_spread),
                candidate_transformation_family="SHOP_ARBITRAGE",
                required_horizon=min(24, hold_steps + 6),
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

