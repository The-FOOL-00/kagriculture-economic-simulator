# SPDX-License-Identifier: MIT
"""AEC-CYCLE: Economic Cycle Timing Architecture (§5–§10).

Second-generation rescue of Town/Cycle Intelligence:
- Replaces unconstrained DELAY_SALE with obligation-aware liquidity preservation.
- Models mandatory future purchases (seeds, nightly wages, feed security, terminal obligations).
- Enforces shed headroom invariants (<=80 units) to prevent field worker gridlock.
- Supports staged partial liquidation (PARTIAL_SALE) to satisfy working capital while preserving inventory optionality.
- Bounds market parcel sizes to avoid intra-basket price elasticity collapse.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import FINAL_STEP, PRODUCTS, SHOP_UNLOCK_INTERVAL, TURNS_PER_DAY, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class TownCycleSignal:
    """Probabilistic and deterministic signals representing town economic cycle phase."""
    step: int
    cycle_phase: float              # 0.0 to 1.0 within 72-step shop interval
    steps_to_next_unlock: int
    steps_to_town_tick: int
    prior_price_bump_probability: float = 0.5
    recommended_timing_bias: str = "NEUTRAL"   # "HOLD_FOR_BUMP", "SELL_NOW", "NEUTRAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "cycle_phase": round(self.cycle_phase, 3),
            "steps_to_unlock": self.steps_to_next_unlock,
            "steps_to_tick": self.steps_to_town_tick,
            "bump_prob": round(self.prior_price_bump_probability, 2),
            "timing_bias": self.recommended_timing_bias,
        }


def compute_required_liquidity(econ_state: EconomicState, horizon_steps: int = 6) -> float:
    """Derive structural required liquidity from actual upcoming obligations (§8).
    
    RequiredLiquidity = mandatory future purchases + mandatory feed requirements
                        + required production inputs + terminal obligations + nightly wages.
    No arbitrary fixed safety buffers.
    """
    step = econ_state.step
    horizon_steps = max(1, horizon_steps)
    required = 0.0

    # 1. Mandatory Nightly Wages
    # Wages are deducted at hour 23 (step % 24 == 23)
    num_hands = max(0, len(econ_state.workers.workers) - 1)
    if num_hands > 0:
        steps_to_night = 23 - (step % TURNS_PER_DAY)
        if 0 <= steps_to_night <= horizon_steps:
            required += num_hands * 100.0

    # 2. Mandatory Livestock Feed Requirements
    # If animals are in danger of starving within horizon and no wheat is available
    from aec.resource.feed_security import FeedSecurityEngine
    animals = getattr(econ_state.farm, "animals", [])
    if not animals:
        animals = FeedSecurityEngine().extract_livestock(econ_state)
    if not animals and hasattr(econ_state.farm, "tiles"):
        for row in econ_state.farm.tiles:
            for tile in row:
                if isinstance(tile, dict) and ("animal" in tile or "subtype" in tile or tile.get("kind") in ("PASTURE", "BARN", "COOP")):
                    animals.append(tile)

    if animals:
        wheat_shed = econ_state.farm.get_shed_qty("WHEAT")
        wheat_hands = econ_state.farm.carried_inventory.get("WHEAT", 0)
        total_wheat = wheat_shed + wheat_hands
        feed_needed = 0
        for a in animals:
            turns_to_starve = getattr(a, "turns_to_starve", None)
            if turns_to_starve is None and isinstance(a, dict):
                turns_to_starve = a.get("turns_to_starve", 2 if a.get("consecutive_unfed", 0) >= 1 else 999)
            if turns_to_starve is None:
                turns_to_starve = 2 if getattr(a, "consecutive_unfed", 0) >= 1 else 999
            if turns_to_starve <= (horizon_steps + 4):
                feed_needed += 1
        uncovered_feed = max(0, feed_needed - total_wheat)
        if uncovered_feed > 0:
            wheat_price = float(econ_state.market.get_price("WHEAT") or 25.0)
            required += uncovered_feed * wheat_price

    # 3. Mandatory Seed Purchases at Day Boundary (t % 24 == 0)
    steps_to_day_start = (TURNS_PER_DAY - (step % TURNS_PER_DAY)) % TURNS_PER_DAY
    if 0 <= steps_to_day_start <= horizon_steps and step <= 648:
        # Minimum working capital to keep fields planted with high-margin seeds (e.g. 2-4 seeds)
        required += 150.0

    return required


class TownCycleSignalDetector:
    """Economic Cycle Timing Analyzer (§5–§10).
    
    Identifies timing transformations where changing the sequence of town/market
    interactions improves the complete downstream trajectory without destroying
    working capital or shed headroom.
    """

    def extract_signal(self, econ_state: EconomicState) -> TownCycleSignal:
        step = econ_state.step
        interval = SHOP_UNLOCK_INTERVAL  # 72
        next_unlock = ((step // interval) + 1) * interval
        steps_left = next_unlock - step
        phase = (step % interval) / float(interval)
        steps_to_tick = econ_state.market.steps_to_town_tick

        if steps_left <= 8 or (1 <= steps_to_tick <= 2):
            bias = "HOLD_FOR_BUMP"
            prob = 0.70
        elif phase <= 0.20 or steps_to_tick == 4:
            bias = "SELL_NOW"
            prob = 0.30
        else:
            bias = "NEUTRAL"
            prob = 0.50

        return TownCycleSignal(
            step=step,
            cycle_phase=phase,
            steps_to_next_unlock=steps_left,
            steps_to_town_tick=steps_to_tick,
            prior_price_bump_probability=prob,
            recommended_timing_bias=bias,
        )

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        step = econ_state.step
        market = econ_state.market
        farm = econ_state.farm
        cash = farm.cash
        steps_to_tick = market.steps_to_town_tick
        absorption = getattr(market, "expected_absorption", {})
        prices = getattr(market, "current_prices", {})
        baseline_action = baseline_action or {}
        baseline_orders = baseline_action.get("market", [])

        # Hard Operational Invariants:
        # 1. Terminal Runway: near terminal (step >= 705), do not delay sales!
        if step >= 705:
            return []

        # 2. Shed Headroom: if shed stock > 80, cannot safely defer sales (shed gridlock risk)
        shed_count = farm.shed_inventory_count
        shed_headroom_critical = shed_count > 80

        # Extract active livestock for feed security guard
        from aec.resource.feed_security import FeedSecurityEngine
        active_animals = getattr(econ_state.farm, "animals", [])
        if not active_animals:
            active_animals = FeedSecurityEngine().extract_livestock(econ_state)
        if not active_animals and hasattr(econ_state.farm, "tiles"):
            for row in econ_state.farm.tiles:
                for tile in row:
                    if isinstance(tile, dict) and ("animal" in tile or tile.get("kind") in ("PASTURE", "BARN", "COOP")):
                        active_animals.append(tile)

        # 3. Structural Required Liquidity
        required_liquidity = compute_required_liquidity(econ_state, horizon_steps=max(6, steps_to_tick + 2))
        liquidity_surplus = cash - required_liquidity

        # 4. Opponent Pressure State
        opp_forecast = getattr(econ_state.opponent, "supply_forecast", {}) if econ_state.opponent else {}

        # ---------------------------------------------------------------------
        # Strategy 1: DELAY_SALE (with strict liquidity & shed headroom checks)
        # ---------------------------------------------------------------------
        if not shed_headroom_critical and liquidity_surplus >= 0:
            for o in baseline_orders:
                if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
                    item = o[1]
                    qty = int(o[2])
                    # Physical Inventory Invariant: Only delay sales if item is in shed with sufficient quantity
                    if item in farm.shed_inventory and farm.get_shed_qty(item) < qty:
                        continue
                    item_absorp = absorption.get(item, 0)
                    opp_dump = opp_forecast.get(item, 0)

                    # Only delay if:
                    # - Town consumption tick is imminent (1 to 3 steps)
                    # - Positive shop absorption exists
                    # - Opponent is not threatening an immediate flood
                    if 1 <= steps_to_tick <= 3 and item_absorp > 0 and opp_dump < 4:
                        projected_bump = min(15.0, float(item_absorp * 2.5))
                        est_relevance = float(qty * projected_bump)
                        opportunities.append(Opportunity(
                            opportunity_id=f"TOWN_CYCLE_DELAY_{step}_{item}",
                            category="TIMING",
                            event_trigger=None,
                            affected_entities=[item],
                            estimated_economic_relevance=est_relevance,
                            candidate_transformation_family="TOWN_CYCLE",
                            dependency_info={
                                "timing_action": "DELAY_SALE",
                                "item": item,
                                "qty": qty,
                                "steps_to_tick": steps_to_tick,
                                "absorption": item_absorp,
                                "projected_bump": projected_bump,
                                "liquidity_surplus": liquidity_surplus,
                                "required_liquidity": required_liquidity,
                            },
                            required_horizon=max(6, steps_to_tick + 2),
                            rationale=(
                                f"Economic Cycle Timing: Defer sale of {qty} {item} for {steps_to_tick} steps "
                                f"to capture +${projected_bump:.1f}/u bump (liquidity surplus: ${liquidity_surplus:.1f})."
                            ),
                            confidence=0.85,
                            scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        ))

        # ---------------------------------------------------------------------
        # Strategy 2: PARTIAL_SALE (Staged liquidation under tight liquidity)
        # ---------------------------------------------------------------------
        # If liquidity is tight (liquidity_surplus < 0), sell only the minimal parcel
        # needed to cover obligations, holding the remainder for the absorption tick.
        if not shed_headroom_critical and liquidity_surplus < 0:
            for o in baseline_orders:
                if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
                    item = o[1]
                    qty = int(o[2])
                    if item in farm.shed_inventory and farm.get_shed_qty(item) < qty:
                        continue
                    cur_p = prices.get(item, 20)
                    item_absorp = absorption.get(item, 0)
                    if 1 <= steps_to_tick <= 3 and item_absorp > 0 and cur_p > 0:
                        deficit = abs(liquidity_surplus)
                        qty_needed = min(qty, max(1, math.ceil(deficit / float(cur_p))))
                        qty_held = qty - qty_needed
                        if qty_held > 0:
                            projected_bump = min(15.0, float(item_absorp * 2.5))
                            est_relevance = float(qty_held * projected_bump)
                            opportunities.append(Opportunity(
                                opportunity_id=f"TOWN_CYCLE_PARTIAL_{step}_{item}",
                                category="TIMING",
                                event_trigger=None,
                                affected_entities=[item],
                                estimated_economic_relevance=est_relevance,
                                candidate_transformation_family="TOWN_CYCLE",
                                dependency_info={
                                    "timing_action": "PARTIAL_SALE",
                                    "item": item,
                                    "qty_sell": qty_needed,
                                    "qty_hold": qty_held,
                                    "steps_to_tick": steps_to_tick,
                                    "cur_price": cur_p,
                                    "projected_bump": projected_bump,
                                    "required_liquidity": required_liquidity,
                                },
                                required_horizon=max(6, steps_to_tick + 2),
                                rationale=(
                                    f"Economic Cycle Timing: Partial sale of {qty_needed} {item} to meet "
                                    f"obligations (${required_liquidity:.1f}), holding {qty_held} {item} for tick bump."
                                ),
                                confidence=0.85,
                                scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                            ))

        # ---------------------------------------------------------------------
        # Strategy 3: ADVANCE_SALE (Monetize fresh demand post-tick)
        # ---------------------------------------------------------------------
        # When town tick fired recently (steps_to_tick == 4 or 0), demand is fresh and prices are at cycle peak
        if (market.is_town_tick_turn or steps_to_tick == 4) and len(baseline_orders) < 10:
            shed = farm.shed_inventory
            for item in PRODUCTS:
                # WHEAT feed protection: never advance-sell wheat if farm owns livestock!
                if item == "WHEAT" and len(active_animals) > 0:
                    continue
                units = shed.get(item, 0)
                if units > 0:
                    already_selling = any(
                        isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL" and o[1] == item
                        for o in baseline_orders
                    )
                    if not already_selling:
                        cur_p = prices.get(item, 10)
                        item_absorp = absorption.get(item, 0)
                        # High-value commodities or actively absorbed goods
                        if item_absorp > 0 or cur_p >= 35 or shed_headroom_critical:
                            # Bound parcel size to 10 to avoid market elasticity crash
                            parcel_size = min(units, 10)
                            est_val = float(parcel_size * cur_p)
                            opportunities.append(Opportunity(
                                opportunity_id=f"TOWN_CYCLE_ADVANCE_{step}_{item}",
                                category="TIMING",
                                event_trigger=None,
                                affected_entities=[item],
                                estimated_economic_relevance=est_val * 0.15,
                                candidate_transformation_family="TOWN_CYCLE",
                                dependency_info={
                                    "timing_action": "ADVANCE_SALE",
                                    "item": item,
                                    "qty": parcel_size,
                                    "cur_price": cur_p,
                                    "steps_to_tick": steps_to_tick,
                                },
                                required_horizon=6,
                                rationale=(
                                    f"Economic Cycle Timing: Advance sale of parcel ({parcel_size} {item}) "
                                    f"at peak town demand (${cur_p}/u, headroom-safe)."
                                ),
                                confidence=0.80,
                                scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                            ))

        return opportunities
