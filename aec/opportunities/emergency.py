# SPDX-License-Identifier: MIT
"""AEC-EMERGENCY: Generalized Damage Avoidance Recovery Architecture (§11–§15, §36).

Second-generation rescue of Emergency Recovery:
- Formulates recovery as selective damage avoidance rather than gross value creation.
- Implements formal 4-stage irreversibility classification:
  1. REVERSIBLE_DEGRADATION (baseline naturally recovers -> ABSTAIN)
  2. RECOVERABLE_DEGRADATION (baseline scheduled action recovers it -> ABSTAIN)
  3. EMERGING_IRREVERSIBLE_LOSS (irreversible loss imminent within <= 2 turns -> RESCUE ALLOWED)
  4. CURRENT_HARD_FAILURE (obligation violation imminent on current turn -> EMERGENCY REQUIRED)
- Replaces panic-selling dumps with minimal surgical intervention:
  liquidates only the exact deficit required for tonight's wages, preserving high-margin stock.
- Coordinates physical delivery of feed to livestock rather than disconnected shed purchases.
- Returns control immediately to the V3 backbone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.config import ANIMALS, CROPS, FINAL_STEP, PRODUCTS, TURNS_PER_DAY, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.resource.feed_security import FeedSecurityEngine


class IrreversibilityClass(str, Enum):
    """Formal classification of failure urgency (§14)."""
    REVERSIBLE_DEGRADATION = "REVERSIBLE_DEGRADATION"       # Baseline naturally recovers -> abstain
    RECOVERABLE_DEGRADATION = "RECOVERABLE_DEGRADATION"     # Scheduled baseline action recovers it -> abstain
    EMERGING_IRREVERSIBLE_LOSS = "EMERGING_IRREVERSIBLE_LOSS" # Irreversible loss within <= 2 turns -> allow
    CURRENT_HARD_FAILURE = "CURRENT_HARD_FAILURE"           # Invariant violation imminent on current step


class EmergencyThreatType(str, Enum):
    """The formal causal threat category prompting emergency intervention (§12)."""
    LIVESTOCK_STARVATION = "LIVESTOCK_STARVATION"           # Animal death within <= 2 turns
    CRITICAL_CASH_INSOLVENCY = "CRITICAL_CASH_INSOLVENCY"   # Wage default tonight with zero sales scheduled
    SHED_OVERFLOW_COLLAPSE = "SHED_OVERFLOW_COLLAPSE"       # Shed stock >= 98 with workers unable to deposit
    TERMINAL_FAILURE_TO_LIQUIDATE = "TERMINAL_FAILURE_TO_LIQUIDATE" # Unsold inventory at step >= 716
    WORKER_DEADLOCK = "WORKER_DEADLOCK"                     # Worker trapped from mandatory task


@dataclass
class EmergencyRecoveryOpportunity(Opportunity):
    """A minimal, high-priority rescue opportunity responding to an irreversible threat (§12, §13)."""
    threat_type: EmergencyThreatType = EmergencyThreatType.LIVESTOCK_STARVATION
    irreversibility_class: IrreversibilityClass = IrreversibilityClass.EMERGING_IRREVERSIBLE_LOSS
    urgency_steps: int = 2
    threatened_asset_value: float = 0.0
    threatened_value: float = 0.0
    minimal_intervention_cost: float = 0.0
    rescue_action_family: str = "EMERGENCY_FEED"

    def __post_init__(self) -> None:
        if self.threatened_value == 0.0 and self.threatened_asset_value > 0.0:
            self.threatened_value = self.threatened_asset_value
        elif self.threatened_asset_value == 0.0 and self.threatened_value > 0.0:
            self.threatened_asset_value = self.threatened_value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "threat_type": self.threat_type.value,
            "irreversibility": self.irreversibility_class.value,
            "urgency_steps": self.urgency_steps,
            "threatened_value": self.threatened_value,
            "intervention_cost": self.minimal_intervention_cost,
        })
        return d


class EmergencyRecoveryDetector:
    """Detects emerging irreversible failure states and formulates minimal surgical rescues (§13, §14).
    
    Adheres strictly to damage-avoidance principles:
    - Reversible/recoverable conditions are rejected as false alarms.
    - Low activation rate, high avoided-damage value per valid activation.
    """

    def __init__(self) -> None:
        self.feed_engine = FeedSecurityEngine()

    def _extract_active_animals(self, econ_state: EconomicState) -> List[Any]:
        """Extract animal objects or entity representations from state or tiles."""
        farm = econ_state.farm
        animals = list(getattr(farm, "animals", []) or [])
        if animals:
            return animals

        # Fallback to feed security engine
        try:
            sec_animals = self.feed_engine.extract_livestock(econ_state)
            if sec_animals:
                return sec_animals
        except Exception:
            pass

        # Fallback to inspecting raw farm tiles
        tile_animals = []
        for y, row in enumerate(farm.tiles):
            for x, tile in enumerate(row):
                if isinstance(tile, dict):
                    an = tile.get("animal") or tile.get("subtype")
                    kind = str(tile.get("kind", ""))
                    if an or kind in ("COOP", "PASTURE"):
                        atype = str(an or tile.get("animal_type") or "COW")
                        starve = tile.get("turns_to_starve")
                        if starve is None:
                            consec = int(tile.get("consecutive_unfed", 0) or 0)
                            fed = bool(tile.get("fed_today", False))
                            if consec >= 1 and not fed:
                                starve = max(1, 23 - (econ_state.step % TURNS_PER_DAY))
                            else:
                                starve = 999
                        tile_animals.append({
                            "animal_type": atype,
                            "turns_to_starve": int(starve),
                            "position": (x, y)
                        })
        return tile_animals

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[EmergencyRecoveryOpportunity]:
        opportunities: List[EmergencyRecoveryOpportunity] = []
        step = econ_state.step
        cash = econ_state.cash
        farm = econ_state.farm
        baseline_action = baseline_action or {}
        baseline_orders = baseline_action.get("market", [])

        # ---------------------------------------------------------------------
        # 1. Livestock Starvation Test (Strict Irreversibility Gate)
        # ---------------------------------------------------------------------
        # Animals starve if turns_to_starve reaches 0.
        for animal in self._extract_active_animals(econ_state):
            if isinstance(animal, dict):
                starve_steps = int(animal.get("turns_to_starve", 999))
                atype = str(animal.get("animal_type", "ANIMAL"))
                pos = animal.get("position", (0, 0))
            else:
                starve_steps = getattr(animal, "turns_to_starve", None)
                if starve_steps is None:
                    consec = getattr(animal, "consecutive_unfed", 0)
                    fed = getattr(animal, "fed_today", False)
                    starve_steps = max(1, 23 - (step % TURNS_PER_DAY)) if (consec >= 1 and not fed) else 999
                atype = getattr(animal, "animal_type", None) or getattr(animal, "subtype", "ANIMAL")
                pos = getattr(animal, "position", (0, 0))

            if starve_steps <= 8:
                # Check if a worker is already carrying wheat
                worker_carrying_feed = False
                for w in econ_state.workers.workers:
                    cargo_dict = getattr(w, "cargo", {}) or {}
                    if cargo_dict.get("WHEAT", 0) > 0:
                        worker_carrying_feed = True
                        break

                # If worker is carrying feed, baseline is actively recovering -> ABSTAIN
                if worker_carrying_feed:
                    continue

                cost = 300.0 if atype == "GOOSE" else (400.0 if atype == "COW" else 500.0)
                pos = getattr(animal, "position", (0, 0))

                # Identify minimum intervention
                wheat_in_shed = farm.get_shed_qty("WHEAT")
                feed_cost = 0.0 if wheat_in_shed > 0 else float(econ_state.market.get_price("WHEAT") or 25.0)

                if starve_steps <= 1:
                    irrev = IrreversibilityClass.CURRENT_HARD_FAILURE
                elif starve_steps <= 4:
                    irrev = IrreversibilityClass.EMERGING_IRREVERSIBLE_LOSS
                else:
                    irrev = IrreversibilityClass.RECOVERABLE_DEGRADATION

                opportunities.append(EmergencyRecoveryOpportunity(
                    opportunity_id=f"EMR_STARVE_{step}_{atype}",
                    category="RESOURCE",
                    event_trigger=None,
                    affected_entities=[atype],
                    estimated_economic_relevance=float(cost - feed_cost),
                    candidate_transformation_family="EMERGENCY_RECOVERY",
                    required_horizon=max(6, starve_steps + 2),
                    rationale=(
                        f"Damage Avoidance: {atype} will starve in {starve_steps} turns ({irrev.value}). "
                        f"Surgical feed rescue prevents irreversible asset loss of ${cost:.0f}."
                    ),
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    threat_type=EmergencyThreatType.LIVESTOCK_STARVATION,
                    irreversibility_class=irrev,
                    urgency_steps=starve_steps,
                    threatened_asset_value=cost,
                    threatened_value=cost,
                    minimal_intervention_cost=feed_cost,
                    rescue_action_family="EMERGENCY_FEED",
                    dependency_info={
                        "threat": "LIVESTOCK_STARVATION",
                        "animal_type": atype,
                        "animal_pos": list(pos) if isinstance(pos, tuple) else pos,
                        "turns_to_starve": starve_steps,
                        "wheat_in_shed": wheat_in_shed,
                        "feed_cost": feed_cost,
                    }
                ))
                break  # Address most urgent animal first

        # ---------------------------------------------------------------------
        # 2. Critical Cash Insolvency (Wage Default Risk)
        # ---------------------------------------------------------------------
        # Wages deducted at hour 23 (step % 24 == 23).
        # If steps_to_night > 2, baseline has scheduled time to sell -> RECOVERABLE.
        num_hands = max(0, len(econ_state.workers.workers) - 1)
        if num_hands > 0:
            wages_due_tonight = num_hands * 100.0
            steps_to_night = 23 - (step % TURNS_PER_DAY)

            # Wage default is an emergency only when imminent (steps_to_night <= 3, hours 20-23);
            # earlier in the day baseline operations are naturally harvesting and generating cash.
            if 0 <= steps_to_night <= 3 and cash < wages_due_tonight:
                # Calculate expected revenue from existing baseline market sales
                existing_revenue = 0.0
                prices = econ_state.market.prices
                for o in baseline_orders:
                    if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL":
                        item = o[1]
                        qty = int(o[2])
                        existing_revenue += qty * float(prices.get(item, 10))

                net_projected_cash = cash + existing_revenue
                # If baseline sales cover wages, baseline is naturally resolving -> ABSTAIN
                if net_projected_cash < wages_due_tonight:
                    deficit = wages_due_tonight - net_projected_cash
                    irrev = (
                        IrreversibilityClass.CURRENT_HARD_FAILURE
                        if steps_to_night <= 1
                        else IrreversibilityClass.EMERGING_IRREVERSIBLE_LOSS
                    )

                    # Extract livestock to protect herd feed supply
                    animals = getattr(econ_state.farm, "animals", [])
                    if not animals:
                        animals = self.feed_engine.extract_livestock(econ_state)

                    # Find commodity in shed to liquidate minimally
                    # Feed Security Invariant: NEVER liquidate WHEAT for wages if livestock exists!
                    shed = farm.shed_inventory
                    if animals:
                        priority_order = ("CARROT", "TOMATO", "EGG", "WOOL", "MILK", "STRAWBERRY", "MELON")
                    else:
                        priority_order = ("WHEAT", "CARROT", "TOMATO", "EGG", "WOOL", "MILK", "STRAWBERRY", "MELON")

                    chosen_item = None
                    qty_to_sell = 0
                    for p in priority_order:
                        available = shed.get(p, 0)
                        if available > 0:
                            unit_p = float(prices.get(p, 10))
                            needed = min(available, max(1, math.ceil(deficit / unit_p)))
                            chosen_item = p
                            qty_to_sell = needed
                            break

                    opportunities.append(EmergencyRecoveryOpportunity(
                        opportunity_id=f"EMR_WAGE_{step}",
                        category="MARKET",
                        event_trigger=None,
                        affected_entities=["WAGES"] + ([chosen_item] if chosen_item else []),
                        estimated_economic_relevance=float(deficit * 2.0),
                        candidate_transformation_family="EMERGENCY_RECOVERY",
                        required_horizon=max(6, steps_to_night + 2),
                        rationale=(
                            f"Damage Avoidance: Wage deficit of ${deficit:.1f} due in {steps_to_night} turns ({irrev.value}). "
                            f"Minimal liquidation prevents worker default."
                        ),
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        threat_type=EmergencyThreatType.CRITICAL_CASH_INSOLVENCY,
                        irreversibility_class=irrev,
                        urgency_steps=steps_to_night,
                        threatened_asset_value=wages_due_tonight,
                        threatened_value=wages_due_tonight,
                        minimal_intervention_cost=0.0,
                        rescue_action_family="EMERGENCY_LIQUIDATE",
                        dependency_info={
                            "threat": "CRITICAL_CASH_INSOLVENCY",
                            "deficit": deficit,
                            "chosen_item": chosen_item,
                            "qty_to_sell": qty_to_sell,
                            "steps_to_night": steps_to_night,
                        }
                    ))

        # ---------------------------------------------------------------------
        # 3. Terminal Failure to Liquidate (Endgame Window step >= 716)
        # ---------------------------------------------------------------------
        if step >= 716 and farm.shed_total_units > 0:
            has_sell_order = any(
                isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL"
                for o in baseline_orders
            )
            if not has_sell_order:
                total_val = sum(qty * float(econ_state.market.get_price(p)) for p, qty in farm.shed_inventory.items() if qty > 0)
                opportunities.append(EmergencyRecoveryOpportunity(
                    opportunity_id=f"EMR_TERM_LIQ_{step}",
                    category="TERMINAL",
                    event_trigger=None,
                    affected_entities=["SHED"],
                    estimated_economic_relevance=total_val,
                    candidate_transformation_family="EMERGENCY_RECOVERY",
                    required_horizon=FINAL_STEP - step + 1,
                    rationale=f"Damage Avoidance: Endgame shed liquidation to monetize ${total_val:.1f} inventory before step 718.",
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    threat_type=EmergencyThreatType.TERMINAL_FAILURE_TO_LIQUIDATE,
                    irreversibility_class=IrreversibilityClass.CURRENT_HARD_FAILURE,
                    urgency_steps=FINAL_STEP - step,
                    threatened_asset_value=total_val,
                    minimal_intervention_cost=0.0,
                    rescue_action_family="TERMINAL_SWEEP_SELL",
                    dependency_info={
                        "threat": "TERMINAL_FAILURE_TO_LIQUIDATE",
                        "total_val": total_val,
                    }
                ))

        return opportunities
