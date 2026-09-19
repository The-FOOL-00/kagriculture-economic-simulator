# SPDX-License-Identifier: MIT
"""Bounded Offline Headroom Oracle Probe (§8, §9, §10, §11)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.config import BOARD_SIZE, PRODUCTS, SHED_CAPACITY, TURNS_PER_DAY
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES
from aec.patches.coupled_patch import CoupledPatch


class OracleCategory(str, Enum):
    """Categorization of Oracle result vs AEC baseline (§10)."""
    A_NO_HEADROOM = "A_NO_HEADROOM"
    B_AEC_CAPTURED = "B_AEC_CAPTURED"
    C_DETECTOR_BLIND = "C_DETECTOR_BLIND"
    D_REPRESENTATION_DEFECT = "D_REPRESENTATION_DEFECT"
    E_RECONNECT_COMPILER_FAIL = "E_RECONNECT_COMPILER_FAIL"
    F_HORIZON_INSUFFICIENT = "F_HORIZON_INSUFFICIENT"
    G_COMPOSITION_ONLY = "G_COMPOSITION_ONLY"
    H_OPPONENT_CONTINGENT = "H_OPPONENT_CONTINGENT"
    I_MACRO_POLICY_CONSTRAINT = "I_MACRO_POLICY_CONSTRAINT"


@dataclass
class OracleAlternativeResult:
    """Evaluation result for an individual admissible alternative trajectory."""
    family: str
    description: str
    action: Dict[str, Any]
    delta_wealth: float
    delta_cash: float
    is_safe: bool
    horizon: int
    simulation_outcome: Optional[SimulationOutcome] = None


@dataclass
class OracleProbeResult:
    """Full diagnostic result of the Oracle Headroom Probe on a single state."""
    step: int
    baseline_action: Dict[str, Any]
    alternatives_evaluated: int
    best_alternative: Optional[OracleAlternativeResult] = None
    local_headroom: float = 0.0
    category: OracleCategory = OracleCategory.A_NO_HEADROOM
    category_rationale: str = ""
    aec_committed: bool = False
    aec_committed_mechanism: Optional[str] = None
    all_positive_alternatives: List[OracleAlternativeResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "alternatives_evaluated": self.alternatives_evaluated,
            "local_headroom": round(self.local_headroom, 2),
            "category": self.category.value,
            "category_rationale": self.category_rationale,
            "best_family": self.best_alternative.family if self.best_alternative else None,
            "best_description": self.best_alternative.description if self.best_alternative else None,
            "aec_committed": self.aec_committed,
            "aec_committed_mechanism": self.aec_committed_mechanism,
            "positive_alternatives_count": len(self.all_positive_alternatives),
        }


class BoundedOracleProbe:
    """Diagnostic evaluator testing whether any admissible local alternative beats baseline."""

    def __init__(self, simulator: Optional[CounterfactualSimulator] = None) -> None:
        self.simulator = simulator or CounterfactualSimulator()

    def probe_state(
        self,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        continuation_trajectory: Optional[List[Dict[str, Any]]] = None,
        aec_telemetry: Optional[Any] = None,
        horizon: int = 18,
    ) -> OracleProbeResult:
        step = econ_state.step
        admissible_alternatives = self.generate_admissible_alternatives(econ_state, baseline_action)

        best_alt: Optional[OracleAlternativeResult] = None
        best_delta: float = 0.0
        positive_alts: List[OracleAlternativeResult] = []

        for idx, (fam, desc, cand_act) in enumerate(admissible_alternatives):
            patch = CoupledPatch(
                patch_id=f"ORACLE_{fam}_{step}_{idx}",
                source_opportunity_id=f"ORACLE_OPP_{fam}",
                mechanism_family=fam,
                actions=[cand_act],
                worker_ids=list(range(len(econ_state.workers.workers))),
                start_step=step,
                end_step=step + 1,
            )

            outcome = self.simulator.evaluate(
                candidate_patch=patch,
                baseline_action=baseline_action,
                econ_state=econ_state,
                horizon=horizon,
                continuation_trajectory=continuation_trajectory,
            )

            is_safe = (
                outcome.intermediate_solvency_ok
                and outcome.spatial_consistency_ok
                and outcome.feed_security_ok
                and outcome.candidate_overflow_units == 0
            )
            wealth_delta = outcome.delta_terminal_margin
            cash_delta = outcome.delta_our_money

            res = OracleAlternativeResult(
                family=fam,
                description=desc,
                action=cand_act,
                delta_wealth=wealth_delta,
                delta_cash=cash_delta,
                is_safe=is_safe,
                horizon=horizon,
                simulation_outcome=outcome,
            )

            if is_safe and wealth_delta > 0.5:
                positive_alts.append(res)
                if wealth_delta > best_delta:
                    best_delta = wealth_delta
                    best_alt = res

        # Check deep horizon F on periodic day boundaries if no local headroom found
        deep_headroom_found = False
        if best_alt is None and horizon < 36 and (step % 24 == 0):
            deep_res = self._check_deeper_horizon(econ_state, baseline_action, continuation_trajectory, 36)
            if deep_res is not None:
                best_alt = deep_res
                best_delta = deep_res.delta_wealth
                deep_headroom_found = True

        # Categorize Oracle vs AEC telemetry
        category, rationale = self._categorize_result(
            best_alt, best_delta, deep_headroom_found, aec_telemetry, econ_state
        )

        aec_committed = bool(aec_telemetry and getattr(aec_telemetry, "decision", "") == "COMMIT")
        aec_mech = getattr(aec_telemetry, "committed_mechanism", None) if aec_telemetry else None

        return OracleProbeResult(
            step=step,
            baseline_action=baseline_action,
            alternatives_evaluated=len(admissible_alternatives),
            best_alternative=best_alt,
            local_headroom=best_delta,
            category=category,
            category_rationale=rationale,
            aec_committed=aec_committed,
            aec_committed_mechanism=aec_mech,
            all_positive_alternatives=positive_alts,
        )

    def generate_admissible_alternatives(
        self, econ_state: EconomicState, baseline_action: Dict[str, Any]
    ) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Generates bounded admissible action transformations across 7 families."""
        step = econ_state.step
        workers = econ_state.workers.workers
        shed = econ_state.farm.shed_inventory
        cash = float(econ_state.farm.cash)
        tiles = econ_state.farm.tiles

        alternatives: List[Tuple[str, str, Dict[str, Any]]] = []

        # Find mature crop locations
        mature_tiles: List[Tuple[int, int]] = []
        for r, row in enumerate(tiles):
            for c, cell in enumerate(row if isinstance(row, list) else []):
                if isinstance(cell, dict) and cell.get("crop"):
                    crop = cell.get("crop")
                    if isinstance(crop, dict) and crop.get("mature", False):
                        mature_tiles.append((r, c))

        # ---------------------------------------------------------------------
        # 1. WORKER TRANSFORMATIONS
        # ---------------------------------------------------------------------
        # Task modifications for Farmer (Worker 0)
        f_pos = workers[0].position if workers else (0, 0)
        f_base = baseline_action.get("farmer", ["PASS"])

        # Alternate Harvest if adjacent/at mature tile
        if mature_tiles:
            for mr, mc in mature_tiles[:3]:
                if (mr, mc) == f_pos and f_base != ["HARVEST"]:
                    act = copy.deepcopy(baseline_action)
                    act["farmer"] = ["HARVEST"]
                    alternatives.append(("WORKER", f"Farmer immediate harvest at ({mr},{mc})", act))
                elif abs(mr - f_pos[0]) + abs(mc - f_pos[1]) == 1:
                    dr = mr - f_pos[0]
                    dc = mc - f_pos[1]
                    cardinal = "S" if dr > 0 else ("N" if dr < 0 else ("E" if dc > 0 else "W"))
                    act = copy.deepcopy(baseline_action)
                    act["farmer"] = ["MOVE", cardinal]
                    alternatives.append(("WORKER", f"Farmer step toward mature crop ({mr},{mc})", act))

        # Alternate Drop if carrying cargo and adjacent to shed
        f_cargo = sum(workers[0].cargo.values()) if workers else 0
        if f_cargo > 0 and (f_pos[0] <= 1 and f_pos[1] <= 1) and f_base != ["DROP"]:
            act = copy.deepcopy(baseline_action)
            act["farmer"] = ["DROP"]
            alternatives.append(("WORKER", "Farmer immediate cargo drop at shed", act))

        # Worker Reassignment (Swap farmer and hand 0 tasks if hand 0 exists)
        if len(workers) > 1 and baseline_action.get("hands"):
            act = copy.deepcopy(baseline_action)
            h0_cmd = list(act["hands"][0])
            act["hands"][0] = list(f_base)
            act["farmer"] = h0_cmd
            alternatives.append(("WORKER", "Swap farmer and hand_0 assignments", act))

        # ---------------------------------------------------------------------
        # 2. MARKET TRANSFORMATIONS
        # ---------------------------------------------------------------------
        mkt_orders = baseline_action.get("market", []) or []
        has_sell = any(isinstance(o, (list, tuple)) and o and o[0] == "SELL" for o in mkt_orders)

        # Alternative Sale: immediate liquidation tranche of items in shed
        for item, qty in shed.items():
            if qty > 0 and item in PRODUCTS:
                # Tranche sell
                act = copy.deepcopy(baseline_action)
                m = list(act.get("market", []))
                m.insert(0, ["SELL", item, min(10, qty)])
                act["market"] = m[:10]
                alternatives.append(("MARKET", f"Immediate sale tranche of {item} (qty={min(10, qty)})", act))

        # Alternative Buy Timing: frontload seed buy if cash allows
        if cash >= 500.0:
            for s in ["STRAWBERRY", "MELON", "PUMPKIN"]:
                act = copy.deepcopy(baseline_action)
                m = list(act.get("market", []))
                m.insert(0, ["BUY_SEED", s, 5])
                act["market"] = m[:10]
                alternatives.append(("MARKET", f"Frontload buy 5 {s} seeds", act))

        # Delayed Sale: if baseline has a sell order, try omitting it
        if has_sell:
            act = copy.deepcopy(baseline_action)
            act["market"] = [o for o in act.get("market", []) if not (isinstance(o, (list, tuple)) and o and o[0] == "SELL")]
            alternatives.append(("MARKET", "Delay sell order by 1 turn", act))

        # ---------------------------------------------------------------------
        # 3. RESOURCE TRANSFORMATIONS
        # ---------------------------------------------------------------------
        # If raw materials exist in shed, propose local procurement / conversion
        if shed.get("STRAWBERRY", 0) >= 3 and cash >= 100:
            act = copy.deepcopy(baseline_action)
            m = list(act.get("market", []))
            m.insert(0, ["BUY_PRODUCT", "FERTILIZER", 1])
            act["market"] = m[:10]
            alternatives.append(("RESOURCE", "Arbitrage procurement of FERTILIZER", act))

        # ---------------------------------------------------------------------
        # 4. TERMINAL TRANSFORMATIONS
        # ---------------------------------------------------------------------
        if step >= 680:
            # Full liquidation dump of all products in shed
            all_sells = [["SELL", item, qty] for item, qty in shed.items() if qty > 0 and item in PRODUCTS]
            if all_sells:
                act = copy.deepcopy(baseline_action)
                act["market"] = all_sells[:10]
                alternatives.append(("TERMINAL", "Terminal complete shed inventory dump", act))

            # Terminal harvest sweep: workers within distance 2 of mature crops move to harvest
            if mature_tiles:
                act = copy.deepcopy(baseline_action)
                act["farmer"] = ["HARVEST"]
                alternatives.append(("TERMINAL", "Terminal harvest sweep priority", act))

        # ---------------------------------------------------------------------
        # 5. MULTI-WORKER TRANSFORMATIONS
        # ---------------------------------------------------------------------
        if len(workers) >= 2:
            act = copy.deepcopy(baseline_action)
            act["farmer"] = ["HARVEST"] if mature_tiles else f_base
            if len(act.get("hands", [])) > 0:
                act["hands"][0] = ["DROP"] if sum(workers[1].cargo.values()) > 0 else act["hands"][0]
            alternatives.append(("MULTI_WORKER", "Coordinated Lead Harvest / Helper Drop", act))

        # ---------------------------------------------------------------------
        # 6. EMERGENCY TRANSFORMATIONS
        # ---------------------------------------------------------------------
        # Feed emergency purchase (animals consume WHEAT)
        animals = getattr(econ_state.farm, "animals", [])
        if animals and shed.get("WHEAT", 0) < len(animals) and cash >= 100:
            act = copy.deepcopy(baseline_action)
            m = list(act.get("market", []))
            m.insert(0, ["BUY_PRODUCT", "WHEAT", len(animals) * 2])
            act["market"] = m[:10]
            alternatives.append(("EMERGENCY", "Emergency livestock feed purchase (WHEAT)", act))

        # ---------------------------------------------------------------------
        # 7. OPPONENT PREEMPTION TRANSFORMATIONS
        # ---------------------------------------------------------------------
        opp_cash = float(econ_state.opponent.observed_cash)
        if opp_cash > 0 and has_sell:
            # Shift sell order to position 0 and double tranche to frontload clearing depth
            act = copy.deepcopy(baseline_action)
            first_sell = next((o for o in mkt_orders if isinstance(o, (list, tuple)) and o and o[0] == "SELL"), None)
            if first_sell and len(first_sell) >= 3:
                item = first_sell[1]
                avail = shed.get(item, 0)
                act["market"] = [["SELL", item, min(avail, 20)]] + [o for o in mkt_orders if o != first_sell]
                alternatives.append(("OPPONENT", f"Opponent preemption frontload on {item}", act))

        return alternatives

    def _check_deeper_horizon(
        self,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        continuation_trajectory: Optional[List[Dict[str, Any]]],
        deep_horizon: int,
    ) -> Optional[OracleAlternativeResult]:
        """Checks whether alternative trajectory gains advantage at deep horizon."""
        alternatives = self.generate_admissible_alternatives(econ_state, baseline_action)
        best_deep: Optional[OracleAlternativeResult] = None
        best_delta: float = 0.0

        for idx, (fam, desc, cand_act) in enumerate(alternatives[:4]):
            patch = CoupledPatch(
                patch_id=f"ORACLE_DEEP_{fam}_{idx}",
                source_opportunity_id="OPP_DEEP",
                mechanism_family=fam,
                actions=[cand_act],
                worker_ids=list(range(len(econ_state.workers.workers))),
                start_step=econ_state.step,
                end_step=econ_state.step + 1,
            )
            outcome = self.simulator.evaluate(
                candidate_patch=patch,
                baseline_action=baseline_action,
                econ_state=econ_state,
                horizon=deep_horizon,
                continuation_trajectory=continuation_trajectory,
            )
            is_safe = (
                outcome.intermediate_solvency_ok
                and outcome.spatial_consistency_ok
                and outcome.feed_security_ok
            )
            if is_safe and outcome.delta_terminal_margin > 2.0 and outcome.delta_terminal_margin > best_delta:
                best_delta = outcome.delta_terminal_margin
                best_deep = OracleAlternativeResult(
                    family=fam,
                    description=f"{desc} (Horizon={deep_horizon})",
                    action=cand_act,
                    delta_wealth=best_delta,
                    delta_cash=outcome.delta_our_money,
                    is_safe=True,
                    horizon=deep_horizon,
                    simulation_outcome=outcome,
                )
        return best_deep

    def _categorize_result(
        self,
        best_alt: Optional[OracleAlternativeResult],
        headroom: float,
        deep_headroom_found: bool,
        aec_telemetry: Optional[Any],
        econ_state: EconomicState,
    ) -> Tuple[OracleCategory, str]:
        if best_alt is None or headroom <= 0.5:
            return (
                OracleCategory.A_NO_HEADROOM,
                "All evaluated admissible alternatives yielded delta <= baseline."
            )

        if deep_headroom_found:
            return (
                OracleCategory.F_HORIZON_INSUFFICIENT,
                f"Headroom of +${headroom:.2f} emerged only under extended horizon H=36."
            )

        # Check if AEC committed and captured this headroom
        if aec_telemetry is not None:
            dec = getattr(aec_telemetry, "decision", "")
            committed_mech = getattr(aec_telemetry, "committed_mechanism", None)

            if dec == "COMMIT" and committed_mech:
                return (
                    OracleCategory.B_AEC_CAPTURED,
                    f"AEC detected and committed {committed_mech}, successfully capturing advantage."
                )

            # Check if opportunities were detected
            opp_count = getattr(aec_telemetry, "opportunities_count", 0)
            cand_count = getattr(aec_telemetry, "candidates_count", 0)

            if opp_count == 0:
                return (
                    OracleCategory.C_DETECTOR_BLIND,
                    f"Oracle found +${headroom:.2f} in {best_alt.family}, but AEC event/opportunity detectors emitted zero opportunities."
                )

            if cand_count == 0:
                return (
                    OracleCategory.D_REPRESENTATION_DEFECT,
                    f"AEC detected {opp_count} opportunities, but candidate funnel/generator produced zero viable candidate patches."
                )

            # Candidates were generated but rejected
            cands = getattr(aec_telemetry, "candidates", [])
            for c in cands:
                sec_reason = getattr(c, "safety_rejection_reason", None)
                econ_reason = getattr(c, "economic_rejection_reason", None)
                if sec_reason and "RECONNECT" in sec_reason:
                    return (
                        OracleCategory.E_RECONNECT_COMPILER_FAIL,
                        f"Candidate matching {best_alt.family} failed trajectory reconnect / spatial consistency."
                    )
                if econ_reason and "MACRO" in econ_reason:
                    return (
                        OracleCategory.I_MACRO_POLICY_CONSTRAINT,
                        f"Candidate rejected by macro controller: {econ_reason}"
                    )

            abstain_reason = getattr(aec_telemetry, "abstain_reason", "ABSTAIN")
            return (
                OracleCategory.D_REPRESENTATION_DEFECT,
                f"AEC evaluated candidates but abstained ({abstain_reason}) while Oracle alternative gained +${headroom:.2f}."
            )

        return (
            OracleCategory.C_DETECTOR_BLIND,
            f"Oracle discovered +${headroom:.2f} headroom in {best_alt.family} without active AEC match."
        )
