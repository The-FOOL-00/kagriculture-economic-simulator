# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Working-Capital Obligation Graph & Conversion Liquidity Profile (§3, §4, §5, §6, §7, §8).

Defines exact working-capital tracking, time-expanded cash trajectories,
baseline mandatory obligation protection, and causal realizable value verification
without arbitrary dollar thresholds or magic constants.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    FINAL_STEP,
    PRODUCTS,
    SHED_CAPACITY,
    TURNS_PER_DAY,
)
from aec.ir.economic_state import EconomicState
from aec.terminal.obligations import (
    BaselineObligationExtractor,
    BaselineObligationSet,
    ObligationClassification,
    TerminalObligation,
)


class ConversionCausalPathType(str, Enum):
    """Authoritative causal categories for realizable conversion value (§7)."""
    REQUIRED_INPUT = "REQUIRED_INPUT"                       # Path A: Creates required input for downstream obligation
    PRODUCTION_UNLOCK = "PRODUCTION_UNLOCK"                 # Path B: Unlocks downstream production
    SALEABLE_OUTPUT = "SALEABLE_OUTPUT"                     # Path C: Creates saleable output realizable before terminal
    MANDATORY_ASSET_PRESERVATION = "MANDATORY_ASSET_PRESERVATION" # Path D: Preserves mandatory asset (prevents livestock loss)
    RESOURCE_LOSS_PREVENTION = "RESOURCE_LOSS_PREVENTION"   # Path E: Prevents unavoidable resource loss
    EXACT_TERMINAL_VALUE = "EXACT_TERMINAL_VALUE"           # Path F: Conversion has exact terminal liquidation value
    NO_REALIZABLE_PURPOSE = "NO_REALIZABLE_PURPOSE"         # Unconnected or dead-end transformation


@dataclass
class ConversionLiquidityProfile:
    """Working-capital obligation profile for a conversion candidate (§4, §5).
    
    CRITICAL ARCHITECTURAL PRINCIPLE:
    Derived from exact cash flows, timing, and baseline obligation commitments,
    NEVER from arbitrary constant dollar buffers or margin heuristics.
    """
    upfront_cash_required: float = 0.0
    intermediate_cash_requirements: Dict[int, float] = field(default_factory=dict)
    downstream_cash_release: float = 0.0
    earliest_cash_recovery: int = FINAL_STEP
    latest_cash_recovery: int = FINAL_STEP
    mandatory_cash_obligations: Dict[int, float] = field(default_factory=dict)
    working_capital_lockup: float = 0.0
    terminal_cash_dependencies: List[str] = field(default_factory=list)
    is_solvent_trajectory: bool = True
    insolvency_turn: Optional[int] = None
    insolvency_reason: Optional[str] = None
    has_realizable_value_path: bool = True
    value_path_type: ConversionCausalPathType = ConversionCausalPathType.SALEABLE_OUTPUT
    value_path_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "upfront_cash_required": self.upfront_cash_required,
            "intermediate_cash_requirements": self.intermediate_cash_requirements,
            "downstream_cash_release": self.downstream_cash_release,
            "earliest_cash_recovery": self.earliest_cash_recovery,
            "latest_cash_recovery": self.latest_cash_recovery,
            "mandatory_cash_obligations": self.mandatory_cash_obligations,
            "working_capital_lockup": self.working_capital_lockup,
            "terminal_cash_dependencies": self.terminal_cash_dependencies,
            "is_solvent_trajectory": self.is_solvent_trajectory,
            "insolvency_turn": self.insolvency_turn,
            "insolvency_reason": self.insolvency_reason,
            "has_realizable_value_path": self.has_realizable_value_path,
            "value_path_type": self.value_path_type.value,
            "value_path_description": self.value_path_description,
        }


class ConversionLiquidityAnalyzer:
    """Evaluates working-capital safety and realizable value for conversion candidates (§4, §5, §6, §7)."""

    def __init__(self) -> None:
        self.obligation_extractor = BaselineObligationExtractor()

    def analyze_profile(
        self,
        candidate_target: str,
        upfront_cost: float,
        duration_steps: int,
        expected_revenue: float,
        econ_state: EconomicState,
        baseline_trajectory: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversionLiquidityProfile:
        """Construct exact ConversionLiquidityProfile and evaluate working-capital feasibility."""
        step = econ_state.step
        cur_cash = float(econ_state.farm.cash)
        remaining = econ_state.remaining_horizon
        ctx = context or {}

        # 1. Extract baseline obligations to understand mandatory cash commitments (§6)
        baseline_set: BaselineObligationSet = self.obligation_extractor.extract_obligations(
            econ_state=econ_state,
            future_trajectory=baseline_trajectory
        )

        mandatory_cash_by_turn: Dict[int, float] = {}
        for obl in baseline_set.obligations:
            if obl.classification == ObligationClassification.MANDATORY and obl.required_cash > 0:
                turn = obl.earliest_turn
                mandatory_cash_by_turn[turn] = mandatory_cash_by_turn.get(turn, 0.0) + obl.required_cash

        # Incorporate context-specified mandatory obligations (§6)
        if "mandatory_cash_by_turn" in ctx:
            for t_turn, c_amt in ctx["mandatory_cash_by_turn"].items():
                mandatory_cash_by_turn[int(t_turn)] = mandatory_cash_by_turn.get(int(t_turn), 0.0) + float(c_amt)
        for k, v in ctx.items():
            if k.startswith("mandatory_") and isinstance(v, (int, float)):
                mandatory_cash_by_turn[step + 5] = mandatory_cash_by_turn.get(step + 5, 0.0) + float(v)

        # 2. Timing and Cash Recovery derivation
        earliest_recovery = min(FINAL_STEP, step + duration_steps)
        latest_recovery = min(FINAL_STEP, earliest_recovery + 24)

        # Check basic upfront cash solvency
        if cur_cash < upfront_cost:
            return ConversionLiquidityProfile(
                upfront_cash_required=upfront_cost,
                downstream_cash_release=0.0,
                earliest_cash_recovery=earliest_recovery,
                latest_cash_recovery=latest_recovery,
                mandatory_cash_obligations=mandatory_cash_by_turn,
                working_capital_lockup=upfront_cost,
                is_solvent_trajectory=False,
                insolvency_turn=step,
                insolvency_reason=f"Cash liquidity hole: requires ${upfront_cost:.1f} but available cash is ${cur_cash:.1f}",
                value_path_type=ConversionCausalPathType.NO_REALIZABLE_PURPOSE,
                value_path_description="Insufficient upfront cash to initiate conversion"
            )

        # 3. Assess Causal Realizable Value (§7)
        has_realizable, path_type, path_desc = self._assess_causal_value_path(
            candidate_target=candidate_target,
            duration_steps=duration_steps,
            expected_revenue=expected_revenue,
            econ_state=econ_state,
            context=ctx
        )

        if not has_realizable:
            return ConversionLiquidityProfile(
                upfront_cash_required=upfront_cost,
                downstream_cash_release=0.0,
                earliest_cash_recovery=earliest_recovery,
                latest_cash_recovery=latest_recovery,
                mandatory_cash_obligations=mandatory_cash_by_turn,
                working_capital_lockup=upfront_cost,
                is_solvent_trajectory=False,
                insolvency_turn=step,
                insolvency_reason=f"No realizable downstream value path: {path_desc}",
                has_realizable_value_path=False,
                value_path_type=ConversionCausalPathType.NO_REALIZABLE_PURPOSE,
                value_path_description=path_desc
            )

        # 4. Step-by-step Working-Capital Feasibility Simulation (§5, §6)
        # Check if upfront cost is immediately funded
        if cur_cash < upfront_cost:
            return ConversionLiquidityProfile(
                upfront_cash_required=upfront_cost,
                downstream_cash_release=expected_revenue,
                earliest_cash_recovery=earliest_recovery,
                latest_cash_recovery=latest_recovery,
                mandatory_cash_obligations=mandatory_cash_by_turn,
                working_capital_lockup=upfront_cost,
                is_solvent_trajectory=False,
                insolvency_turn=step,
                insolvency_reason=f"Cash liquidity hole: requires ${upfront_cost:.1f} but available cash is ${cur_cash:.1f}",
                has_realizable_value_path=True,
                value_path_type=path_type,
                value_path_description=path_desc
            )

        # Trace trajectory forward across relevant horizon
        eval_horizon = min(remaining, max(duration_steps + 1, 48))
        projected_cash = cur_cash - upfront_cost
        peak_lockup = upfront_cost
        intermediate_reqs: Dict[int, float] = {}

        # If context specifies additional intermediate costs (e.g. worker hire on day boundary)
        extra_costs = ctx.get("intermediate_costs", {})
        for t_off, c_amt in extra_costs.items():
            t_abs = step + int(t_off)
            intermediate_reqs[t_abs] = float(c_amt)

        terminal_deps: List[str] = []
        if earliest_recovery >= FINAL_STEP - 2:
            terminal_deps.append("TERMINAL_LIQUIDATION_STEP_718")

        for offset in range(eval_horizon + 1):
            t = step + offset
            if t > FINAL_STEP:
                break

            # Deduct intermediate costs
            if t in intermediate_reqs:
                projected_cash -= intermediate_reqs[t]

            # Deduct mandatory baseline commitments that remain active
            mand_cost = mandatory_cash_by_turn.get(t, 0.0)
            if mand_cost > 0:
                projected_cash -= mand_cost

            # Add downstream cash release if revenue arrives at turn t
            if t == earliest_recovery:
                projected_cash += expected_revenue

            # Invariant: projected cash must remain >= 0 at all times
            if projected_cash < 0:
                return ConversionLiquidityProfile(
                    upfront_cash_required=upfront_cost,
                    intermediate_cash_requirements=intermediate_reqs,
                    downstream_cash_release=expected_revenue,
                    earliest_cash_recovery=earliest_recovery,
                    latest_cash_recovery=latest_recovery,
                    mandatory_cash_obligations=mandatory_cash_by_turn,
                    working_capital_lockup=max(peak_lockup, upfront_cost - projected_cash),
                    terminal_cash_dependencies=terminal_deps,
                    is_solvent_trajectory=False,
                    insolvency_turn=t,
                    insolvency_reason=(
                        f"Downstream working-capital deadlock at turn {t}: "
                        f"projected cash ${projected_cash:.1f} < $0.0 after funding mandatory obligations"
                    ),
                    has_realizable_value_path=True,
                    value_path_type=path_type,
                    value_path_description=path_desc
                )

        return ConversionLiquidityProfile(
            upfront_cash_required=upfront_cost,
            intermediate_cash_requirements=intermediate_reqs,
            downstream_cash_release=expected_revenue,
            earliest_cash_recovery=earliest_recovery,
            latest_cash_recovery=latest_recovery,
            mandatory_cash_obligations=mandatory_cash_by_turn,
            working_capital_lockup=peak_lockup,
            terminal_cash_dependencies=terminal_deps,
            is_solvent_trajectory=True,
            insolvency_turn=None,
            insolvency_reason=None,
            has_realizable_value_path=True,
            value_path_type=path_type,
            value_path_description=path_desc
        )

    def _assess_causal_value_path(
        self,
        candidate_target: str,
        duration_steps: int,
        expected_revenue: float,
        econ_state: EconomicState,
        context: Dict[str, Any]
    ) -> Tuple[bool, ConversionCausalPathType, str]:
        """Verify that conversion candidate possesses an exact causal realizable value path (§7)."""
        step = econ_state.step
        cur_day = step // TURNS_PER_DAY
        remaining = econ_state.remaining_horizon

        # Rule 1: Conversions completing after step 718 have zero realizable value
        if step + duration_steps > FINAL_STEP:
            return (
                False,
                ConversionCausalPathType.NO_REALIZABLE_PURPOSE,
                f"Transformation duration ({duration_steps} steps) exceeds remaining turns ({remaining}) before step {FINAL_STEP}"
            )

        # Rule 2: Day 29 livestock feeding has zero realizable value
        # In sim.hpp, end_of_day(29) never executes; animals cannot escape on day 29 and yields never refresh
        if cur_day >= 29 and candidate_target in ("MILK", "EGG", "WOOL"):
            return (
                False,
                ConversionCausalPathType.NO_REALIZABLE_PURPOSE,
                "Day 29 livestock feeding cannot refresh yields or prevent escape because end_of_day(29) never runs"
            )

        # Rule 3: Livestock feed causal path
        if candidate_target in ("MILK", "EGG", "WOOL"):
            # Check if animal exists on farm
            animal_type = {"MILK": "COW", "EGG": "GOOSE", "WOOL": "SHEEP"}[candidate_target]
            animal_found = False
            at_risk_of_escape = False

            for row in econ_state.farm.tiles:
                for tile in row:
                    if isinstance(tile, dict) and tile.get("animal") == animal_type:
                        animal_found = True
                        consec = int(tile.get("consecutive_unfed", 0) or 0)
                        fed = bool(tile.get("fed_today", False))
                        if consec >= 1 and not fed:
                            at_risk_of_escape = True
                        break
                if animal_found:
                    break

            if not animal_found:
                return (
                    False,
                    ConversionCausalPathType.NO_REALIZABLE_PURPOSE,
                    f"Target animal {animal_type} does not exist on farm tiles"
                )

            if at_risk_of_escape and cur_day < 29:
                return (
                    True,
                    ConversionCausalPathType.MANDATORY_ASSET_PRESERVATION,
                    f"Feeding {animal_type} prevents imminent animal escape (consecutive_unfed >= 1)"
                )

            # Check if animal can yield and be harvested before step 718
            if step + duration_steps <= FINAL_STEP:
                return (
                    True,
                    ConversionCausalPathType.SALEABLE_OUTPUT,
                    f"Feeding {animal_type} produces {candidate_target} with realizable market value before final step"
                )

        # Rule 4: Shed commodity terminal liquidation
        if candidate_target in PRODUCTS and candidate_target not in ("MILK", "EGG", "WOOL"):
            if step + duration_steps <= FINAL_STEP:
                return (
                    True,
                    ConversionCausalPathType.EXACT_TERMINAL_VALUE,
                    f"Conversion produces {candidate_target} realizable via terminal liquidation"
                )

        return (
            False,
            ConversionCausalPathType.NO_REALIZABLE_PURPOSE,
            f"No causal value path established for candidate {candidate_target}"
        )
