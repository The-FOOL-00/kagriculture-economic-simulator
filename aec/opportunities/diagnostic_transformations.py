# SPDX-License-Identifier: MIT
"""Phase 020: Bounded Diagnostic Transformation Library (§10, §11, §12, §13).

Generates interpretable, bounded diagnostic transformations across orthogonal
opportunity families (Market Timing, Production Timing, Worker Allocation,
Route/Spatial, Multi-Worker, Opponent Interaction, Liquidity/Capital, Terminal,
Resource Allocation).

Strictly enforces:
  - Legality, feasibility, and safety invariants.
  - CoupledPatch compatibility.
  - TRANCHE_RELATED quarantine tagging for any candidate whose core action is
    selling held produce earlier (§11).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    ANIMALS,
    BOARD_SIZE,
    CROPS,
    CROP_GROWTH_DAYS,
    CROP_SEED_PRICE,
    EPISODE_STEPS,
    MOVES,
    PRODUCTS,
    SHED_CAPACITY,
    SHED_TILES,
    TURNS_PER_DAY,
)
from aec.counterfactual.macro_detector import (
    MacroBoundaryProbeResult,
    MacroRegimeFingerprint,
    MacroRegimeTransitionDetector,
    MacroRegimeType,
    classify_cash_bracket,
)
from aec.counterfactual.simulator import (
    CounterfactualSimulator,
    SimulationOutcome,
)
from aec.ir.economic_state import EconomicState
from aec.patches.coupled_patch import CoupledPatch


class TransformationPrimitive(str, Enum):
    """The 12 Bounded Diagnostic Transformation Primitives (§12)."""
    SHIFT_ACTION_EARLIER = "SHIFT_ACTION_EARLIER"
    SHIFT_ACTION_LATER = "SHIFT_ACTION_LATER"
    SWAP_ACTION_ORDER = "SWAP_ACTION_ORDER"
    REMOVE_REDUNDANT_ACTION = "REMOVE_REDUNDANT_ACTION"
    REASSIGN_WORKER = "REASSIGN_WORKER"
    REORDER_WORK = "REORDER_WORK"
    ALTER_ROUTE = "ALTER_ROUTE"
    ALTER_PRODUCTION_TIMING = "ALTER_PRODUCTION_TIMING"
    ALTER_MARKET_TIMING = "ALTER_MARKET_TIMING"
    PRESERVE_RESOURCE = "PRESERVE_RESOURCE"
    ALLOCATE_RESOURCE_DIFFERENTLY = "ALLOCATE_RESOURCE_DIFFERENTLY"
    COORDINATE_WORKERS = "COORDINATE_WORKERS"


class OpportunityFamily(str, Enum):
    """The Orthogonal Opportunity Family Taxonomy (§10)."""
    MARKET_TIMING = "Market timing"
    PRODUCTION_TIMING = "Production timing"
    WORKER_ALLOCATION = "Worker allocation"
    ROUTE_SPATIAL = "Route/spatial"
    MULTI_WORKER = "Multi-worker"
    OPPONENT_INTERACTION = "Opponent interaction"
    LIQUIDITY_CAPITAL_TIMING = "Liquidity/capital timing"
    TERMINAL = "Terminal"
    RESOURCE_CONVERSION = "Resource conversion"


class BackboneDivergenceClass(str, Enum):
    """Backbone Divergence Taxonomy (§27)."""
    D0 = "D0_NO_MEANINGFUL_DIVERGENCE"
    D1 = "D1_TIMING_ONLY"
    D2 = "D2_ORDER_SEQUENCE"
    D3 = "D3_WORKER_ALLOCATION"
    D4 = "D4_MARKET_ACTION"
    D5 = "D5_PRODUCTION_POLICY"
    D6 = "D6_MULTI_SYSTEM"


@dataclass
class DiagnosticCandidate:
    """A bounded diagnostic candidate transformation evaluated in Phase 020."""
    candidate_id: str
    primitive: TransformationPrimitive
    family: OpportunityFamily
    patch: CoupledPatch
    is_tranche_related: bool = False
    divergence_class: BackboneDivergenceClass = BackboneDivergenceClass.D1
    rationale: str = ""
    target_worker_id: int = 0
    estimated_local_signal: float = 0.0
    long_horizon_delta: float = 0.0
    direct_intervention_effect: float = 0.0
    macro_induced_continuation_delta: float = 0.0
    macro_escalated: bool = False
    macro_regime: str = "NONE"
    divergence_turn: Optional[int] = None
    is_safe: bool = True
    safety_rejection_reason: str = ""
    is_representable: bool = True
    missing_primitive: str = "NONE"
    survival_category: str = "H0"  # H0..H5


def is_in_bounds(x: int, y: int) -> bool:
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class DiagnosticTransformationGenerator:
    """Systematic generator of legal diagnostic transformations across families."""

    def __init__(self) -> None:
        self.macro_detector = MacroRegimeTransitionDetector()

    def generate_candidates(
        self,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        continuation_trajectory: Optional[List[Dict[str, Any]]] = None,
    ) -> List[DiagnosticCandidate]:
        """Generates bounded candidate transformations from current baseline and state."""
        candidates: List[DiagnosticCandidate] = []
        step = getattr(econ_state, "step", 0)
        cash = getattr(econ_state, "cash", 0.0)
        workers = getattr(econ_state, "workers", None)
        n_workers = len(workers.workers) if workers and hasattr(workers, "workers") else 1
        shed = getattr(econ_state.farm, "shed_inventory", {}) if hasattr(econ_state, "farm") else {}
        prices = getattr(econ_state.market, "current_prices", {}) if hasattr(econ_state, "market") else {}
        plots = getattr(econ_state.farm, "plots", {}) if hasattr(econ_state, "farm") else {}

        # ---------------------------------------------------------------------
        # 1. SWAP_ACTION_ORDER / Market Timing: Reorder Market Orders (Group A)
        # ---------------------------------------------------------------------
        base_market = baseline_action.get("market", [])
        if len(base_market) >= 2:
            # Reorder market orders: put SELLs first to generate cash for BUYs
            sells = [o for o in base_market if isinstance(o, (list, tuple)) and len(o) > 0 and o[0] == "SELL"]
            buys = [o for o in base_market if isinstance(o, (list, tuple)) and len(o) > 0 and o[0] != "SELL"]
            reordered = sells + buys
            if reordered != base_market:
                patch = CoupledPatch(
                    patch_id=f"P020_SWAP_MARKET_{step}",
                    source_opportunity_id="OPP_SWAP_MARKET",
                    mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
                    start_step=step,
                    end_step=step,
                    actions=[{
                        "farmer": list(baseline_action.get("farmer", ["PASS"])),
                        "hands": copy.deepcopy(baseline_action.get("hands", [])),
                        "market": copy.deepcopy(reordered),
                    }],
                    market_mutations=copy.deepcopy(reordered),
                )
                candidates.append(DiagnosticCandidate(
                    candidate_id=patch.patch_id,
                    primitive=TransformationPrimitive.SWAP_ACTION_ORDER,
                    family=OpportunityFamily.MARKET_TIMING,
                    patch=patch,
                    is_tranche_related=False,
                    divergence_class=BackboneDivergenceClass.D2,
                    rationale="Reorder existing market orders to prioritize cash-generating sells",
                    target_worker_id=0,
                ))

        # ---------------------------------------------------------------------
        # 2. ALTER_MARKET_TIMING: Orthogonal Non-Tranche Advance Feed/Seed Purchase
        # ---------------------------------------------------------------------
        # If continuation plans to buy feed/seeds within next 3 turns and cash is available,
        # advance the purchase to lock price or avoid delay.
        if continuation_trajectory and len(continuation_trajectory) >= 1 and cash >= 100.0:
            next_act = continuation_trajectory[0]
            next_market = next_act.get("market", [])
            for order in next_market:
                if isinstance(order, (list, tuple)) and len(order) >= 3 and order[0] in ("BUY", "BUY_PRODUCT"):
                    item, qty = order[1], order[2]
                    unit_cost = prices.get(item, 20.0)
                    total_cost = unit_cost * qty
                    if total_cost <= cash * 0.5:
                        adv_market = list(base_market) + [list(order)]
                        patch = CoupledPatch(
                            patch_id=f"P020_ADV_BUY_{item}_{step}",
                            source_opportunity_id=f"OPP_ADV_BUY_{item}",
                            mechanism_family="MARKET_TIMING_ADVANCE_BUY",
                            start_step=step,
                            end_step=step,
                            actions=[{
                                "farmer": list(baseline_action.get("farmer", ["PASS"])),
                                "hands": copy.deepcopy(baseline_action.get("hands", [])),
                                "market": copy.deepcopy(adv_market[:10]),
                            }],
                            market_mutations=copy.deepcopy(adv_market[:10]),
                        )
                        candidates.append(DiagnosticCandidate(
                            candidate_id=patch.patch_id,
                            primitive=TransformationPrimitive.SHIFT_ACTION_EARLIER,
                            family=OpportunityFamily.MARKET_TIMING,
                            patch=patch,
                            is_tranche_related=False,  # Orthogonal: BUY advance, not SELL
                            divergence_class=BackboneDivergenceClass.D1,
                            rationale=f"Advance scheduled purchase of {qty} {item} from step {step+1}",
                            target_worker_id=0,
                        ))
                        break

        # ---------------------------------------------------------------------
        # 3. PRESERVE_RESOURCE / Liquidity & Capital Timing: Defer Discretionary Capex
        # ---------------------------------------------------------------------
        # If baseline purchases discretionary land or non-essential inputs when cash is low (<$800)
        has_capex = False
        pruned_market = []
        for order in base_market:
            if isinstance(order, (list, tuple)) and len(order) > 0 and order[0] in ("BUY_LAND", "BUY_STRUCTURE"):
                has_capex = True
            elif isinstance(order, (list, tuple)) and len(order) >= 3 and order[0] == "BUY" and order[1] in ("STRAWBERRY", "MELON"):
                if cash < 1000.0:
                    has_capex = True
                else:
                    pruned_market.append(order)
            else:
                pruned_market.append(order)

        if has_capex and cash < 2000.0:
            patch = CoupledPatch(
                patch_id=f"P020_PRESERVE_CASH_{step}",
                source_opportunity_id="OPP_PRESERVE_CASH",
                mechanism_family="LIQUIDITY_PRESERVATION",
                start_step=step,
                end_step=step,
                actions=[{
                    "farmer": list(baseline_action.get("farmer", ["PASS"])),
                    "hands": copy.deepcopy(baseline_action.get("hands", [])),
                    "market": copy.deepcopy(pruned_market),
                }],
                market_mutations=copy.deepcopy(pruned_market),
            )
            candidates.append(DiagnosticCandidate(
                candidate_id=patch.patch_id,
                primitive=TransformationPrimitive.PRESERVE_RESOURCE,
                family=OpportunityFamily.LIQUIDITY_CAPITAL_TIMING,
                patch=patch,
                is_tranche_related=False,
                divergence_class=BackboneDivergenceClass.D4,
                rationale="Defer discretionary purchase to maintain working capital safety buffer",
                target_worker_id=0,
            ))

        # ---------------------------------------------------------------------
        # 4. WORKER ALLOCATION: Reassign Task to Closer Worker
        # ---------------------------------------------------------------------
        if n_workers >= 2 and workers:
            farmer_w = workers.get_worker(0)
            f_pos = farmer_w.position if farmer_w else (5, 5)
            f_act = baseline_action.get("farmer", ["PASS"])

            # If farmer is performing a field work action (TILL, WATER, HARVEST, PLANT)
            if len(f_act) > 0 and f_act[0] in ("TILL", "WATER", "HARVEST", "PLANT"):
                # Check if a farmhand is on or adjacent to the tile
                for h_idx in range(n_workers - 1):
                    hand_w = workers.get_worker(h_idx + 1)
                    if hand_w and hand_w.position == f_pos:
                        # Hand can execute the task; farmer can move or pass
                        mut_action = copy.deepcopy(baseline_action)
                        mut_action["farmer"] = ["PASS"]
                        hands = mut_action.setdefault("hands", [])
                        while len(hands) <= h_idx:
                            hands.append(["PASS"])
                        hands[h_idx] = list(f_act)

                        patch = CoupledPatch(
                            patch_id=f"P020_REASSIGN_H{h_idx+1}_{step}",
                            source_opportunity_id=f"OPP_REASSIGN_{h_idx+1}",
                            mechanism_family="LABOR_REASSIGNMENT",
                            start_step=step,
                            end_step=step,
                            actions=[mut_action],
                        )
                        candidates.append(DiagnosticCandidate(
                            candidate_id=patch.patch_id,
                            primitive=TransformationPrimitive.REASSIGN_WORKER,
                            family=OpportunityFamily.WORKER_ALLOCATION,
                            patch=patch,
                            is_tranche_related=False,
                            divergence_class=BackboneDivergenceClass.D3,
                            rationale=f"Reassign {f_act[0]} on tile {f_pos} from farmer to co-located farmhand {h_idx+1}",
                            target_worker_id=h_idx + 1,
                        ))
                        break

        # ---------------------------------------------------------------------
        # 5. ROUTE / SPATIAL: Alternative Direction / Detour around Obstacle
        # ---------------------------------------------------------------------
        if workers:
            for wid in range(n_workers):
                w = workers.get_worker(wid)
                if not w:
                    continue
                w_pos = w.position
                act_list = baseline_action.get("farmer" if wid == 0 else "hands", [])
                w_act = act_list if wid == 0 else (act_list[wid - 1] if wid - 1 < len(act_list) else ["PASS"])

                if len(w_act) >= 2 and w_act[0] == "MOVE":
                    d = w_act[1]
                    # Try alternate orthogonal move if target tile is in bounds
                    alt_dirs = ["NORTH", "EAST", "SOUTH", "WEST"]
                    alt_dirs.remove(d) if d in alt_dirs else None
                    for alt_d in alt_dirs:
                        dx, dy = MOVES.get(alt_d, (0, 0))
                        nx, ny = w_pos[0] + dx, w_pos[1] + dy
                        if is_in_bounds(nx, ny):
                            mut_action = copy.deepcopy(baseline_action)
                            if wid == 0:
                                mut_action["farmer"] = ["MOVE", alt_d]
                            else:
                                mut_action.setdefault("hands", [])[wid - 1] = ["MOVE", alt_d]

                            patch = CoupledPatch(
                                patch_id=f"P020_ALT_ROUTE_W{wid}_{alt_d}_{step}",
                                source_opportunity_id=f"OPP_ROUTE_W{wid}",
                                mechanism_family="ROUTE_TRANSFORMATION",
                                start_step=step,
                                end_step=step,
                                actions=[mut_action],
                            )
                            candidates.append(DiagnosticCandidate(
                                candidate_id=patch.patch_id,
                                primitive=TransformationPrimitive.ALTER_ROUTE,
                                family=OpportunityFamily.ROUTE_SPATIAL,
                                patch=patch,
                                is_tranche_related=False,
                                divergence_class=BackboneDivergenceClass.D1,
                                rationale=f"Route detour for worker {wid} from {w_pos} via {alt_d}",
                                target_worker_id=wid,
                            ))
                            break  # Only one route probe per worker

        # ---------------------------------------------------------------------
        # 6. MULTI-WORKER COORDINATION: Synchronized Harvest / Labor Alignment
        # ---------------------------------------------------------------------
        if n_workers >= 2 and plots:
            # Check for multiple ready-to-harvest crops
            harvestable_plots = [pos for pos, p in plots.items() if getattr(p, "growth_stage", 0) >= getattr(p, "mature_stage", 999)]
            if len(harvestable_plots) >= 2:
                # If workers are adjacent to harvestable plots but passing or moving away
                for wid in range(min(n_workers, 2)):
                    w = workers.get_worker(wid)
                    if w and w.position in harvestable_plots:
                        w_act = baseline_action.get("farmer" if wid == 0 else "hands", [])
                        cur = w_act if wid == 0 else (w_act[wid - 1] if wid - 1 < len(w_act) else ["PASS"])
                        if cur != ["HARVEST"]:
                            mut_action = copy.deepcopy(baseline_action)
                            if wid == 0:
                                mut_action["farmer"] = ["HARVEST"]
                            else:
                                mut_action.setdefault("hands", [])[wid - 1] = ["HARVEST"]

                            patch = CoupledPatch(
                                patch_id=f"P020_SYNC_HARVEST_W{wid}_{step}",
                                source_opportunity_id=f"OPP_SYNC_HARVEST_{wid}",
                                mechanism_family="MULTIWORKER_SYNCHRONIZATION",
                                start_step=step,
                                end_step=step,
                                actions=[mut_action],
                            )
                            candidates.append(DiagnosticCandidate(
                                candidate_id=patch.patch_id,
                                primitive=TransformationPrimitive.COORDINATE_WORKERS,
                                family=OpportunityFamily.MULTI_WORKER,
                                patch=patch,
                                is_tranche_related=False,
                                divergence_class=BackboneDivergenceClass.D3,
                                rationale=f"Coordinated parallel harvest on tile {w.position} by worker {wid}",
                                target_worker_id=wid,
                            ))

        # ---------------------------------------------------------------------
        # 7. PRODUCTION TIMING: Advance Planting / Soil Sync
        # ---------------------------------------------------------------------
        if plots and workers:
            w0 = workers.get_worker(0)
            if w0:
                p_tile = plots.get(w0.position)
                # If tile is tilled, unplanted, and inventory has seeds
                if p_tile and getattr(p_tile, "is_tilled", False) and not getattr(p_tile, "crop", None):
                    farmer_act = baseline_action.get("farmer", ["PASS"])
                    if farmer_act != ["PLANT", "WHEAT"] and farmer_act != ["PLANT", "CARROT"]:
                        # Check if shed or cargo has seeds
                        seed_avail = any(shed.get(c, 0) > 0 for c in ("WHEAT", "CARROT", "TOMATO")) or (cash >= 50.0)
                        if seed_avail:
                            mut_action = copy.deepcopy(baseline_action)
                            mut_action["farmer"] = ["PLANT", "WHEAT"]
                            patch = CoupledPatch(
                                patch_id=f"P020_ADV_PLANT_{step}",
                                source_opportunity_id="OPP_ADV_PLANT",
                                mechanism_family="PRODUCTION_TIMING",
                                start_step=step,
                                end_step=step,
                                actions=[mut_action],
                            )
                            candidates.append(DiagnosticCandidate(
                                candidate_id=patch.patch_id,
                                primitive=TransformationPrimitive.ALTER_PRODUCTION_TIMING,
                                family=OpportunityFamily.PRODUCTION_TIMING,
                                patch=patch,
                                is_tranche_related=False,
                                divergence_class=BackboneDivergenceClass.D5,
                                rationale=f"Advance planting on tilled tile {w0.position}",
                                target_worker_id=0,
                            ))

        # ---------------------------------------------------------------------
        # 8. TERMINAL ENDGAME: Salvage Harvest before Step 718
        # ---------------------------------------------------------------------
        if step >= 680 and plots and workers:
            w0 = workers.get_worker(0)
            if w0 and w0.position in plots:
                p_tile = plots[w0.position]
                if getattr(p_tile, "growth_stage", 0) >= 1:
                    farmer_act = baseline_action.get("farmer", ["PASS"])
                    if farmer_act != ["HARVEST"]:
                        mut_action = copy.deepcopy(baseline_action)
                        mut_action["farmer"] = ["HARVEST"]
                        patch = CoupledPatch(
                            patch_id=f"P020_TERM_HARVEST_{step}",
                            source_opportunity_id="OPP_TERM_HARVEST",
                            mechanism_family="TERMINAL_TIMING",
                            start_step=step,
                            end_step=step,
                            actions=[mut_action],
                        )
                        candidates.append(DiagnosticCandidate(
                            candidate_id=patch.patch_id,
                            primitive=TransformationPrimitive.SHIFT_ACTION_EARLIER,
                            family=OpportunityFamily.TERMINAL,
                            patch=patch,
                            is_tranche_related=False,
                            divergence_class=BackboneDivergenceClass.D5,
                            rationale=f"Terminal salvage harvest on tile {w0.position} at step {step}",
                            target_worker_id=0,
                        ))

        # ---------------------------------------------------------------------
        # 9. TRANCHE-RELATED PROBE (QUARANTINE ENFORCEMENT AUDIT, §11)
        # ---------------------------------------------------------------------
        # For census completeness and quarantine audit, if shed has produce and baseline didn't sell,
        # generate a tranche candidate but STRICTLY MARK is_tranche_related = True.
        for crop in CROPS:
            qty = shed.get(crop, 0)
            if qty >= 5:
                # Check if baseline sold it
                sold_in_base = any(isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL" and o[1] == crop for o in base_market)
                if not sold_in_base:
                    tranche_market = list(base_market) + [["SELL", crop, min(qty, 10)]]
                    patch = CoupledPatch(
                        patch_id=f"P020_TRANCHE_PROBE_{crop}_{step}",
                        source_opportunity_id=f"OPP_TRANCHE_{crop}",
                        mechanism_family="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
                        start_step=step,
                        end_step=step,
                        actions=[{
                            "farmer": list(baseline_action.get("farmer", ["PASS"])),
                            "hands": copy.deepcopy(baseline_action.get("hands", [])),
                            "market": copy.deepcopy(tranche_market[:10]),
                        }],
                        market_mutations=copy.deepcopy(tranche_market[:10]),
                    )
                    candidates.append(DiagnosticCandidate(
                        candidate_id=patch.patch_id,
                        primitive=TransformationPrimitive.SHIFT_ACTION_EARLIER,
                        family=OpportunityFamily.MARKET_TIMING,
                        patch=patch,
                        is_tranche_related=True,  # §11: Strictly tagged and excluded from primary rank
                        divergence_class=BackboneDivergenceClass.D4,
                        rationale=f"Diagnostic probe: Sell {min(qty, 10)} held {crop} earlier",
                        target_worker_id=0,
                    ))
                    break  # At most 1 tranche probe per turn

        return candidates


class DiagnosticEvaluator:
    """Two-stage evaluator for Phase 020 opportunity census (§14)."""

    def __init__(self) -> None:
        self.simulator = CounterfactualSimulator()
        self.macro_detector = MacroRegimeTransitionDetector()

    def evaluate_stage1_local(
        self,
        econ_state: EconomicState,
        candidate: DiagnosticCandidate,
        baseline_action: Dict[str, Any],
    ) -> float:
        """Stage 1: Cheap local transformation probe ($O(1)$ signal)."""
        # Estimate immediate delta based on primitive and state
        patch = candidate.patch
        step0_action = patch.apply(baseline_action)
        prices = getattr(econ_state.market, "current_prices", {})

        local_delta = 0.0
        # If market orders altered
        base_market = baseline_action.get("market", [])
        cand_market = step0_action.get("market", [])

        # Cash effect of step0 market orders
        base_net = sum(
            (float(prices.get(o[1], 20.0)) * o[2] if o[0] == "SELL" else -float(prices.get(o[1], 20.0)) * o[2])
            for o in base_market if isinstance(o, (list, tuple)) and len(o) >= 3
        )
        cand_net = sum(
            (float(prices.get(o[1], 20.0)) * o[2] if o[0] == "SELL" else -float(prices.get(o[1], 20.0)) * o[2])
            for o in cand_market if isinstance(o, (list, tuple)) and len(o) >= 3
        )
        local_delta += (cand_net - base_net)

        # Worker action utility
        if candidate.primitive == TransformationPrimitive.REASSIGN_WORKER:
            local_delta += 15.0  # Heuristic labor travel saving
        elif candidate.primitive == TransformationPrimitive.COORDINATE_WORKERS:
            local_delta += 25.0  # Harvest synchronization benefit
        elif candidate.primitive == TransformationPrimitive.ALTER_PRODUCTION_TIMING:
            local_delta += 10.0  # Faster crop turnaround
        elif candidate.primitive == TransformationPrimitive.PRESERVE_RESOURCE:
            local_delta += 5.0   # Liquidity option value

        candidate.estimated_local_signal = local_delta
        return local_delta

    def evaluate_stage2_long_horizon(
        self,
        econ_state: EconomicState,
        candidate: DiagnosticCandidate,
        baseline_action: Dict[str, Any],
        continuation_trajectory: Optional[List[Dict[str, Any]]] = None,
        v3_agent_callable: Optional[Any] = None,
        horizon: int = 24,
    ) -> SimulationOutcome:
        """Stage 2: Phase 016 macro-aware exact long-horizon simulation."""
        # 1. Macro regime check
        probe_res = self.macro_detector.probe_candidate(
            patch=candidate.patch,
            baseline_action=baseline_action,
            econ_state=econ_state,
            base_horizon=horizon,
        )
        escalated = probe_res.requires_escalation
        reason = probe_res.reason
        rtype = probe_res.regime_type
        candidate.macro_escalated = escalated
        candidate.macro_regime = rtype.value if hasattr(rtype, "value") else str(rtype)

        # 2. Run simulation
        sim_res = self.simulator.simulate(
            econ_state=econ_state,
            baseline_action=baseline_action,
            candidate_patch=candidate.patch,
            horizon=horizon,
            continuation_trajectory=continuation_trajectory,
            v3_agent_callable=v3_agent_callable,
            macro_escalated=escalated,
            macro_escalation_reason=reason,
            macro_regime_type=candidate.macro_regime,
        )

        candidate.long_horizon_delta = sim_res.delta_terminal_margin
        candidate.direct_intervention_effect = getattr(sim_res, "direct_intervention_effect", 0.0)
        candidate.macro_induced_continuation_delta = getattr(sim_res, "macro_induced_continuation_delta", 0.0)
        candidate.divergence_turn = getattr(sim_res, "first_divergence_turn", None)
        candidate.is_safe = sim_res.intermediate_solvency_ok and sim_res.feed_security_ok

        # Assign survival category H0..H5 (§15)
        if candidate.long_horizon_delta <= 0.0:
            if candidate.estimated_local_signal > 0.0:
                candidate.survival_category = "H1"  # Local positive, long-horizon non-positive
            else:
                candidate.survival_category = "H0"  # Disappears
        elif candidate.long_horizon_delta < 10.0:
            candidate.survival_category = "H2"      # Below economic significance
        elif candidate.is_safe:
            candidate.survival_category = "H3"      # Long-horizon positive & safety feasible
        else:
            candidate.survival_category = "H1"      # Unsafe / solvency violation

        return sim_res
