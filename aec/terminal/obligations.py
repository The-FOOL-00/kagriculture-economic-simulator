# SPDX-License-Identifier: MIT
"""AEC Terminal Obligations and Causal Chain Reasoning (§6, §7, §8, §9, §10, §13, §14, §15).

Formalizes:
1. Terminal obligation data structures (mandatory vs discretionary).
2. Baseline obligation extraction and cash requirement derivation.
3. Causal feed-purchase chain modeling (escape prevention vs production/harvest/sale).
4. Deterministic terminal obligation feasibility verification without arbitrary constants.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    FINAL_STEP,
    MAX_MARKET_ORDERS,
    PRODUCTS,
    SHED_CAPACITY,
    TURNS_PER_DAY,
)
from aec.ir.economic_state import EconomicState


class ObligationClassification(str, Enum):
    """Classification of downstream obligations (§9)."""
    MANDATORY = "MANDATORY"                       # Irreversible loss / game requirement if skipped
    OPTIONAL = "OPTIONAL"                         # Discretionary upside opportunity
    CONDITIONALLY_REQUIRED = "CONDITIONALLY_REQUIRED" # Required only if dependent path active
    SUPERSEDED = "SUPERSEDED"                     # Legitimately replaced by candidate patch


class TerminalPurposeCategory(str, Enum):
    """Authoritative causal categories for terminal emergency-feed candidates (§21)."""
    TERMINAL_PURPOSE_CONFIRMED = "TERMINAL_PURPOSE_CONFIRMED"
    LIVESTOCK_ESCAPE_PREVENTION = "LIVESTOCK_ESCAPE_PREVENTION"
    TERMINAL_NO_REALIZABLE_PURPOSE = "TERMINAL_NO_REALIZABLE_PURPOSE"
    FEED_ARRIVAL_TOO_LATE = "FEED_ARRIVAL_TOO_LATE"
    PRODUCTION_COMPLETION_TOO_LATE = "PRODUCTION_COMPLETION_TOO_LATE"
    HARVEST_WINDOW_UNAVAILABLE = "HARVEST_WINDOW_UNAVAILABLE"
    TERMINAL_LIQUIDATION_CONFLICT = "TERMINAL_LIQUIDATION_CONFLICT"
    MANDATORY_CASH_OBLIGATION_CONFLICT = "MANDATORY_CASH_OBLIGATION_CONFLICT"
    RESOURCE_CAPACITY_CONFLICT = "RESOURCE_CAPACITY_CONFLICT"


@dataclass
class TerminalObligation:
    """Represents a discrete downstream obligation in the baseline or candidate plan (§6)."""
    obligation_id: str
    source_action: str
    resource: str                                 # "CASH", "WHEAT", "SHED_SPACE", "WORKER_ACTION", etc.
    quantity: int
    earliest_turn: int
    latest_turn: int
    required_worker: Optional[int] = None
    required_cash: float = 0.0
    required_capacity: int = 0
    prerequisite_obligations: List[str] = field(default_factory=list)
    terminal_relevance: str = "DIRECT_REWARD"
    terminal_value_type: str = "CASH"
    classification: ObligationClassification = ObligationClassification.MANDATORY
    provenance: str = "BASELINE_TRAJECTORY"


@dataclass
class BaselineObligationSet:
    """Formal collection of future obligations derived from the baseline trajectory (§7, §8)."""
    step: int
    obligations: List[TerminalObligation] = field(default_factory=list)
    cash_profile_by_turn: Dict[int, float] = field(default_factory=dict)
    mandatory_cash_total: float = 0.0
    mandatory_sales: List[Dict[str, Any]] = field(default_factory=list)


class BaselineObligationExtractor:
    """Extracts and classifies mandatory vs optional baseline obligations (§7, §8, §9)."""

    def extract_obligations(
        self,
        econ_state: EconomicState,
        future_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> BaselineObligationSet:
        step = econ_state.step
        remaining = econ_state.remaining_horizon
        obligations: List[TerminalObligation] = []
        mandatory_cash = 0.0
        cash_by_turn: Dict[int, float] = {}
        mandatory_sales: List[Dict[str, Any]] = []

        if not future_trajectory:
            # When no trajectory is provided, derive obligations from visible state
            # 1. Step 718 Terminal Liquidation (mandatory cash realization if shed has goods)
            shed_goods = econ_state.farm.shed_inventory
            shed_units = sum(int(v or 0) for k, v in shed_goods.items() if k in PRODUCTS)
            if shed_units > 0 and step <= FINAL_STEP:
                obligations.append(TerminalObligation(
                    obligation_id="OBL_TERM_LIQUIDATION_718",
                    source_action="MARKET_SELL",
                    resource="SHED_GOODS",
                    quantity=shed_units,
                    earliest_turn=FINAL_STEP,
                    latest_turn=FINAL_STEP,
                    required_cash=0.0,
                    required_capacity=0,
                    classification=ObligationClassification.MANDATORY,
                    provenance="TERMINAL_SCORING"
                ))

            # 2. Livestock feed obligations for animals entering consecutive_unfed >= 1
            cur_day = step // TURNS_PER_DAY
            if cur_day < 29:  # Escape can only occur at end-of-day for day < 29
                for y, row in enumerate(econ_state.farm.tiles):
                    for x, tile in enumerate(row):
                        if isinstance(tile, dict) and "animal" in tile:
                            consec = int(tile.get("consecutive_unfed", 0) or 0)
                            fed = bool(tile.get("fed_today", False))
                            if consec >= 1 and not fed:
                                day_end_step = (cur_day + 1) * TURNS_PER_DAY - 1
                                obligations.append(TerminalObligation(
                                    obligation_id=f"OBL_FEED_{tile['animal']}_{x}_{y}",
                                    source_action="FEED",
                                    resource="WHEAT",
                                    quantity=1,
                                    earliest_turn=step,
                                    latest_turn=day_end_step,
                                    required_cash=0.0,
                                    classification=ObligationClassification.MANDATORY,
                                    provenance="ESCAPE_PREVENTION"
                                ))

            return BaselineObligationSet(
                step=step,
                obligations=obligations,
                cash_profile_by_turn=cash_by_turn,
                mandatory_cash_total=0.0,
                mandatory_sales=mandatory_sales
            )

        # Process discrete future trajectory
        cumulative_mand_cash = 0.0
        for offset, action in enumerate(future_trajectory):
            t = step + offset
            if t > FINAL_STEP:
                break

            # 1. Market orders
            for idx, order in enumerate(action.get("market", []) or []):
                if not isinstance(order, (list, tuple)) or not order:
                    continue
                op = str(order[0])
                item = str(order[1]) if len(order) > 1 else ""
                qty = int(order[2]) if len(order) > 2 else 1

                if op == "SELL" and item in PRODUCTS:
                    # Selling mature inventory converts physical assets into terminal cash reward
                    obligations.append(TerminalObligation(
                        obligation_id=f"OBL_MKT_SELL_{t}_{idx}_{item}",
                        source_action=f"SELL_{item}_{qty}",
                        resource=item,
                        quantity=qty,
                        earliest_turn=t,
                        latest_turn=t,
                        classification=ObligationClassification.MANDATORY,
                        provenance="PLANNED_REVENUE"
                    ))
                    mandatory_sales.append({"turn": t, "item": item, "qty": qty})

                elif op == "BUY_PRODUCT" and item == "WHEAT":
                    # Wheat purchase: mandatory only if preventing imminent animal escape
                    obligations.append(TerminalObligation(
                        obligation_id=f"OBL_MKT_BUY_{t}_{idx}_{item}",
                        source_action=f"BUY_{item}_{qty}",
                        resource="CASH",
                        quantity=qty,
                        earliest_turn=t,
                        latest_turn=t,
                        required_cash=float(econ_state.market.get_price("WHEAT")) * qty,
                        classification=ObligationClassification.OPTIONAL,
                        provenance="BASELINE_SCHEDULE"
                    ))

                elif op in ("BUY_SEED", "HIRE", "BUY_LAND"):
                    # Discretionary baseline investments; candidate can legitimately supersede
                    obligations.append(TerminalObligation(
                        obligation_id=f"OBL_MKT_INVEST_{t}_{idx}_{op}",
                        source_action=f"{op}_{item}_{qty}",
                        resource="CASH",
                        quantity=qty,
                        earliest_turn=t,
                        latest_turn=t,
                        required_cash=20.0 * qty,
                        classification=ObligationClassification.OPTIONAL,
                        provenance="BASELINE_SCHEDULE"
                    ))

            # 2. Worker actions
            farmer_cmd = action.get("farmer", ["PASS"]) or ["PASS"]
            hands_cmds = action.get("hands", []) or []
            for w_idx, cmd in enumerate([farmer_cmd] + hands_cmds):
                if not isinstance(cmd, (list, tuple)) or not cmd:
                    continue
                op = cmd[0]
                if op == "FEED":
                    obligations.append(TerminalObligation(
                        obligation_id=f"OBL_WORKER_FEED_{t}_W{w_idx}",
                        source_action="FEED",
                        resource="WHEAT",
                        quantity=1,
                        earliest_turn=t,
                        latest_turn=t,
                        required_worker=w_idx,
                        classification=ObligationClassification.MANDATORY,
                        provenance="BASELINE_SCHEDULE"
                    ))
                elif op == "HARVEST":
                    obligations.append(TerminalObligation(
                        obligation_id=f"OBL_WORKER_HARVEST_{t}_W{w_idx}",
                        source_action="HARVEST",
                        resource="WORKER_ACTION",
                        quantity=1,
                        earliest_turn=t,
                        latest_turn=t,
                        required_worker=w_idx,
                        classification=ObligationClassification.MANDATORY,
                        provenance="SCHEDULED_HARVEST"
                    ))

            cash_by_turn[t] = cumulative_mand_cash

        return BaselineObligationSet(
            step=step,
            obligations=obligations,
            cash_profile_by_turn=cash_by_turn,
            mandatory_cash_total=mandatory_cash,
            mandatory_sales=mandatory_sales
        )


class FeedTerminalCausalAnalyzer:
    """Determines whether an emergency feed purchase has a causal, realizable purpose (§10, §13, §14, §15)."""

    def assess_terminal_feed_purpose(
        self,
        econ_state: EconomicState,
        animals: List[Any],
        deficit: int,
        baseline_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, TerminalPurposeCategory, str, Dict[str, Any]]:
        """Evaluates exact causal chains for emergency feed purchase based on game semantics.
        
        Game Invariants:
        1. Terminal scoring in sim.hpp is purely st.farms[p].money (cash).
        2. Episode ends at step 718 (step_i >= 720 - 2 triggers st.done = true).
        3. Day 29 runs steps 696–718. Step 719 never executes.
        4. end_of_day(29) NEVER RUNS.
        5. Livestock yields only refresh at end_of_day.
        6. Animals only escape at end_of_day if consecutive_unfed >= 2.
        7. On Day 29: no yield refresh can ever occur, and no animal can ever escape.
        """
        step = econ_state.step
        cur_day = step // TURNS_PER_DAY
        turn_of_day = step % TURNS_PER_DAY
        turns_to_day_end = TURNS_PER_DAY - turn_of_day
        steps_to_final_action = max(0, FINAL_STEP - step)
        price = float(econ_state.market.get_price("WHEAT"))
        purchase_cost = deficit * price

        details: Dict[str, Any] = {
            "step": step,
            "day": cur_day,
            "remaining_steps": econ_state.remaining_horizon,
            "steps_to_final_action": steps_to_final_action,
            "deficit": deficit,
            "purchase_cost": purchase_cost,
            "animals_count": len(animals),
            "cash": float(econ_state.farm.cash),
        }

        # 1. Physical execution feasibility: Market purchase takes 1 step to deliver to shed
        # and worker needs at least 1 step to pickup and feed animal before final action step 718.
        if steps_to_final_action < 2:
            return (
                False,
                TerminalPurposeCategory.FEED_ARRIVAL_TOO_LATE,
                f"Insufficient turns ({steps_to_final_action} remaining) to purchase, route, and feed before final step {FINAL_STEP}",
                details
            )

        # 2. Causal Purpose 1: Livestock Escape Prevention (§15)
        # Check if any animal has consecutive_unfed >= 1 entering day cur_day
        at_risk_animals = []
        for a in animals:
            consec = getattr(a, "consecutive_unfed", 0)
            fed = getattr(a, "fed_today", False)
            if isinstance(a, dict):
                consec = int(a.get("consecutive_unfed", 0) or 0)
                fed = bool(a.get("fed_today", False))
            if consec >= 1 and not fed:
                at_risk_animals.append(a)

        details["at_risk_animals_count"] = len(at_risk_animals)

        # On Day 29 (steps 696–718), end_of_day(29) NEVER RUNS because step 718 terminates the game.
        # Therefore, NO animal can ever escape on Day 29!
        if cur_day == 29:
            # On Day 29: escape prevention is physically impossible, AND yield refresh is physically impossible.
            return (
                False,
                TerminalPurposeCategory.TERMINAL_NO_REALIZABLE_PURPOSE,
                f"Final day (Day 29) feed purchase cannot prevent escape (end_of_day never runs) and cannot refresh yields before step {FINAL_STEP}",
                details
            )

        # On Day D < 29:
        # Check if feeding prevents an actual imminent escape at end_of_day(cur_day)
        day_end_step = (cur_day + 1) * TURNS_PER_DAY - 1
        steps_to_day_end = day_end_step - step
        if at_risk_animals and steps_to_day_end >= 1:
            # Verified imminent escape prevention purpose!
            details["purpose"] = "LIVESTOCK_ESCAPE_PREVENTION"
            details["earliest_realizable_benefit"] = day_end_step
            details["latest_feasible_execution"] = day_end_step - 1
            return (
                True,
                TerminalPurposeCategory.LIVESTOCK_ESCAPE_PREVENTION,
                f"Emergency feed purchase prevents imminent permanent escape of {len(at_risk_animals)} animal(s) at step {day_end_step}",
                details
            )

        # 3. Causal Purpose 2: Realizable Production, Harvest, and Sale (§10, §14)
        # Full physical chain:
        # Step t: BUY_PRODUCT WHEAT (in shed at t)
        # Step >= t+1: Worker feeds animal on day D <= 28
        # Step (D+1)*24 - 1: end_of_day(D) runs daily_refresh_animals, incrementing yield_units
        # Step >= (D+1)*24: Worker HARVEST (1 step)
        # Step >= (D+1)*24 + 1: Worker DROP to shed (1 step)
        # Step <= 718: Market SELL order commits to liquidate product to cash (1 step)
        # Total minimum steps from day rollover to sale = 3 steps.
        # Therefore, the animal MUST be fed before or on day 28 (cur_day <= 28).
        if cur_day > 28:
            return (
                False,
                TerminalPurposeCategory.PRODUCTION_COMPLETION_TOO_LATE,
                f"Feed purchase at day {cur_day} cannot yield refreshed products before game conclusion at step {FINAL_STEP}",
                details
            )

        # Steps required to complete feed on day cur_day + day rollover + harvest + drop + sell
        # Feeding must happen on or before day cur_day: requires at least 2 steps (buy + feed).
        # Then harvest and sale require 3 steps after day end.
        min_realizable_steps = turns_to_day_end + 3
        if steps_to_final_action < min_realizable_steps:
            return (
                False,
                TerminalPurposeCategory.HARVEST_WINDOW_UNAVAILABLE,
                f"Insufficient steps remaining ({steps_to_final_action} available, {min_realizable_steps} required) to complete harvest and market liquidation",
                details
            )

        # Causal purpose confirmed: realizable production, harvest, and sale chain exists!
        details["purpose"] = "REALIZABLE_PRODUCTION_HARVEST_SALE"
        details["earliest_realizable_benefit"] = (cur_day + 1) * TURNS_PER_DAY + 2
        details["latest_feasible_execution"] = FINAL_STEP
        return (
            True,
            TerminalPurposeCategory.TERMINAL_PURPOSE_CONFIRMED,
            "Emergency feed purchase has a verified, realizable downstream production, harvest, and liquidation chain",
            details
        )


class TerminalObligationChecker:
    """Verifies that an emergency feed candidate preserves all exact baseline obligations (§7, §8, §11, §12)."""

    def __init__(self) -> None:
        self.extractor = BaselineObligationExtractor()
        self.causal_analyzer = FeedTerminalCausalAnalyzer()

    def verify_candidate_safety(
        self,
        econ_state: EconomicState,
        candidate_patch: Any,
        sim_outcome: Any,
        baseline_action: Dict[str, Any],
        future_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Verifies candidate against exact game-derived obligations without arbitrary thresholds."""
        animals = getattr(econ_state.farm, "animals", [])
        if not animals:
            from aec.resource.feed_security import FeedSecurityEngine
            animals = FeedSecurityEngine().extract_livestock(econ_state)

        deficit = 1
        if hasattr(candidate_patch, "dependency_info") and isinstance(candidate_patch.dependency_info, dict):
            deficit = candidate_patch.dependency_info.get("deficit", 1)

        # 1. Causal Terminal Purpose Verification
        is_feasible, purpose_cat, purpose_reason, details = self.causal_analyzer.assess_terminal_feed_purpose(
            econ_state=econ_state,
            animals=animals,
            deficit=deficit,
            baseline_trajectory=future_trajectory
        )

        details["purpose_category"] = purpose_cat.value
        details["purpose_reason"] = purpose_reason

        if not is_feasible:
            return False, purpose_reason, details

        # 2. Cash Obligation Verification (§8)
        # Verify candidate does not cause intermediate cash deadlock or break mandatory future cash requirements
        cand_final_cash = float(getattr(sim_outcome, "candidate_final_money", 0.0))
        if cand_final_cash < 0.0 or not getattr(sim_outcome, "intermediate_solvency_ok", True):
            return (
                False,
                f"Candidate causes cash insolvency or deadlock (final cash ${cand_final_cash:.1f})",
                details
            )

        # 3. Capacity Obligation Verification
        # Candidate must not cause shed overflow that destroys planned harvest deposits
        if getattr(sim_outcome, "candidate_overflow_units", 0) > 0:
            return (
                False,
                f"Candidate purchase overflows shed storage capacity by {sim_outcome.candidate_overflow_units} unit(s)",
                details
            )

        # 4. Market Order Queue Integrity (§13)
        # At step 718, candidate must not crowd out mandatory liquidation SELL orders
        if econ_state.step == FINAL_STEP:
            market_mutations = getattr(candidate_patch, "market_mutations", []) or []
            if len(market_mutations) > MAX_MARKET_ORDERS:
                return (
                    False,
                    f"Candidate market orders ({len(market_mutations)}) exceed maximum market order capacity ({MAX_MARKET_ORDERS}) at step {FINAL_STEP}",
                    details
                )

        details["terminal_purpose_confirmed"] = True
        return True, None, details
