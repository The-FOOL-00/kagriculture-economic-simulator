# SPDX-License-Identifier: MIT
"""Town Shop Demand and Economic Cycle Signal Architecture (§22)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import FINAL_STEP, PRODUCTS, SHOP_UNLOCK_INTERVAL, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class TownCycleSignal:
    """Probabilistic signal representing town economic cycle phase (§22).
    
    Treated as a prior / signal, never a guaranteed deterministic event.
    """
    step: int
    cycle_phase: float              # 0.0 to 1.0 within 72-step shop interval
    steps_to_next_unlock: int
    prior_price_bump_probability: float = 0.5
    recommended_timing_bias: str = "NEUTRAL"   # "HOLD_FOR_BUMP", "SELL_NOW", "NEUTRAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "cycle_phase": round(self.cycle_phase, 3),
            "steps_to_unlock": self.steps_to_next_unlock,
            "bump_prob": round(self.prior_price_bump_probability, 2),
            "timing_bias": self.recommended_timing_bias,
        }


class TownCycleSignalDetector:
    """Analyzes town shop unlock intervals and 4-step town consumption cycles.
    
    Constructs contextual timing opportunities (delay sale or accelerate sale)
    conditioned on town absorption, shed capacity, liquidity, and opponent pressure.
    """

    def extract_signal(self, econ_state: EconomicState) -> TownCycleSignal:
        step = econ_state.step
        interval = SHOP_UNLOCK_INTERVAL  # 72
        next_unlock = ((step // interval) + 1) * interval
        steps_left = next_unlock - step
        phase = (step % interval) / float(interval)

        # In steps 60-71 of cycle, town demand refresh is imminent (higher bump likelihood)
        if steps_left <= 8:
            bias = "HOLD_FOR_BUMP"
            prob = 0.70
        elif phase <= 0.20:
            bias = "SELL_NOW"
            prob = 0.30
        else:
            bias = "NEUTRAL"
            prob = 0.50

        return TownCycleSignal(
            step=step,
            cycle_phase=phase,
            steps_to_next_unlock=steps_left,
            prior_price_bump_probability=prob,
            recommended_timing_bias=bias,
        )

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        """Detect cycle-relevant market timing opportunities.
        
        Evaluates both:
        1. DELAY_SALE: Postpone an existing baseline SELL order when town shop
           absorption tick is imminent (1-3 turns) and expected to lift price.
        2. ADVANCE_SALE: Execute a sale of shed inventory when town demand has
           just absorbed stock or peak cyclical price is active.
        """
        opportunities: List[Opportunity] = []
        step = econ_state.step
        market = econ_state.market
        farm = econ_state.farm
        steps_to_tick = market.steps_to_town_tick
        absorption = getattr(market, "expected_absorption", {})
        prices = getattr(market, "current_prices", {})
        baseline_action = baseline_action or {}
        baseline_orders = baseline_action.get("market", [])

        # Constraint Checks:
        # Near-terminal: do not delay sales past terminal safety horizon (step >= 714)
        is_near_terminal = step >= (FINAL_STEP - 4)
        # Shed capacity constraint: if shed >= 95 items, cannot safely hoard/delay
        shed_full = farm.shed_inventory_count >= 95
        # Opponent supply pressure: if opponent has massive supply ready to dump, override delay
        opp_forecast = getattr(econ_state.opponent, "supply_forecast", {}) if econ_state.opponent else {}

        # ---------------------------------------------------------------------
        # Strategy 1: DELAY_SALE
        # ---------------------------------------------------------------------
        if not is_near_terminal and not shed_full:
            # Inspect baseline SELL orders
            for o in baseline_orders:
                if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
                    item = o[1]
                    qty = int(o[2])
                    item_absorp = absorption.get(item, 0)
                    opp_dump = opp_forecast.get(item, 0)

                    # Condition: Town absorption tick imminent (1-3 steps), positive shop absorption,
                    # and no overwhelming opponent supply threat that would collapse price first
                    if 1 <= steps_to_tick <= 3 and item_absorp > 0 and opp_dump < 4:
                        projected_bump = min(20.0, float(item_absorp * 3.0))
                        est_relevance = float(qty * projected_bump)
                        opportunities.append(Opportunity(
                            opportunity_id=f"TOWN_CYCLE_DELAY_{step}_{item}",
                            category="MARKET",
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
                            },
                            required_horizon=max(6, steps_to_tick + 2),
                            rationale=(
                                f"Town cycle: Defer sale of {qty} {item} for {steps_to_tick} steps "
                                f"to capture projected +${projected_bump:.1f}/unit town shop absorption bump."
                            ),
                            confidence=0.80,
                            scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        ))

        # ---------------------------------------------------------------------
        # Strategy 2: ADVANCE_SALE
        # ---------------------------------------------------------------------
        # When town tick just fired (steps_to_tick == 4 or 0), demand is fresh and shed holds stock
        if market.is_town_tick_turn and len(baseline_orders) < 10:
            shed = farm.shed_inventory
            for item in PRODUCTS:
                units = shed.get(item, 0)
                if units > 0:
                    # Check if baseline is already selling this item
                    already_selling = any(
                        isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL" and o[1] == item
                        for o in baseline_orders
                    )
                    if not already_selling:
                        cur_p = prices.get(item, 10)
                        item_absorp = absorption.get(item, 0)
                        # More attractive if town shops actively consume it
                        if item_absorp > 0 or cur_p >= 35:
                            est_val = float(units * cur_p)
                            opportunities.append(Opportunity(
                                opportunity_id=f"TOWN_CYCLE_ADVANCE_{step}_{item}",
                                category="MARKET",
                                event_trigger=None,
                                affected_entities=[item],
                                estimated_economic_relevance=est_val * 0.2,  # Liquidity / timing value
                                candidate_transformation_family="TOWN_CYCLE",
                                dependency_info={
                                    "timing_action": "ADVANCE_SALE",
                                    "item": item,
                                    "qty": min(units, 10),
                                    "cur_price": cur_p,
                                    "steps_to_tick": steps_to_tick,
                                },
                                required_horizon=6,
                                rationale=(
                                    f"Town cycle: Advance sale of {units} {item} at post-absorption peak "
                                    f"(${cur_p}/unit) to monetize refreshed town demand."
                                ),
                                confidence=0.75,
                                scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                            ))

        return opportunities
