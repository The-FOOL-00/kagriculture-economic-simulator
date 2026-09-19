# SPDX-License-Identifier: MIT
"""Candidate Patch Generator from Opportunities."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from aec.config import AECConfig, ENABLED_FOUNDATION_MECHANISMS, PRODUCTS
from aec.coordination.scheduler import MultiWorkerLogisticsCoordinator, CoordinationStatus
from aec.coordination.worker_model import extract_farm_workers
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.patches.patch import CoupledPatch, CoupledPatchRequest
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.replanning.reconnect import ReconnectRequest, ReconnectionEngine, deterministic_find_path
from aec.resource.conversions import ConversionExecutionPlan, decompose_conversion_to_tasks
from aec.resource.feed_security import decompose_feed_rescue_to_tasks
from aec.resource.labor import ConversionLaborClass, ConversionLaborPreconditionValidator
from aec.resource.liquidity import ConversionLiquidityAnalyzer


def reorder_frontload(market_orders: List[List[Any]]) -> List[List[Any]]:
    """Partition orders into Group A (SELLs), Group B (BUY_PRODUCT), Group C (Capital)."""
    A, B, C = [], [], []
    for o in market_orders:
        if not isinstance(o, (list, tuple)) or not o:
            continue
        op = o[0]
        if op == "SELL":
            A.append(list(o))
        elif op == "BUY_PRODUCT":
            B.append(list(o))
        else:
            C.append(list(o))
    return (A + B + C)[:10]


class PatchGenerator:
    """Compiles detected opportunities into concrete CoupledPatch proposals with mechanism gating (§8, §11)."""

    def __init__(
        self,
        config: Optional[AECConfig] = None,
        enabled_mechanisms: Optional[Any] = None
    ) -> None:
        if config is not None:
            self.enabled_mechanisms = set(config.enabled_mechanisms)
        elif enabled_mechanisms is not None:
            self.enabled_mechanisms = set(enabled_mechanisms)
        else:
            self.enabled_mechanisms = set(ENABLED_FOUNDATION_MECHANISMS)

        self.reconnect_engine = ReconnectionEngine()
        self.multiworker_coordinator = MultiWorkerLogisticsCoordinator()
        self.labor_validator = ConversionLaborPreconditionValidator(self.multiworker_coordinator)
        self.liquidity_analyzer = ConversionLiquidityAnalyzer()
        self.harvest_generator = HarvestCoupledPatchGenerator(board_size=self.multiworker_coordinator.board_size)
        from aec.market.tranche_synthesizer import AutonomousTrancheOrderSynthesizer
        self.tranche_synthesizer = AutonomousTrancheOrderSynthesizer()
        self.last_quarantined_count: int = 0
        self.last_quarantined_by_mechanism: Dict[str, int] = {}

    def generate_patches(
        self,
        opportunities: List[Opportunity],
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        config: Optional[AECConfig] = None,
        baseline_continuation: Optional[List[Dict[str, Any]]] = None,
        co_worker_trajectories: Optional[Dict[int, List[Tuple[int, int]]]] = None
    ) -> List[CoupledPatch]:
        enabled = set(config.enabled_mechanisms) if config is not None else self.enabled_mechanisms
        self.last_quarantined_count = 0
        self.last_quarantined_by_mechanism = {}

        patches: List[CoupledPatch] = []

        for opp in opportunities:
            fam = opp.candidate_transformation_family
            
            # Layer 2 Mechanism Enforcement: Refuse any disabled transformation family
            # Note: LOCAL_WEED_DIG generates patches for development simulation and quarantine rejection (§3)
            if fam not in enabled and fam != "LOCAL_WEED_DIG":
                self.last_quarantined_count += 1
                self.last_quarantined_by_mechanism[fam] = self.last_quarantined_by_mechanism.get(fam, 0) + 1
                continue
            
            # 1. Route / Weed Dig
            if fam == "LOCAL_WEED_DIG":
                worker_id = opp.dependency_info.get("worker_id", 0)
                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_mutations={worker_id: ["DIG"]},
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 2. Dependency-Aware Market Timing (§8, §14)
            elif fam == "DEPENDENCY_AWARE_MARKET_TIMING":
                current_orders = baseline_action.get("market", [])
                from aec.market.transformations import transform_dependency_aware_market_timing
                reordered, _ = transform_dependency_aware_market_timing(current_orders, econ_state)
                if reordered != current_orders:
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        market_mutations=reordered,
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

            # 2B. Autonomous Tranche Order Synthesizer (Phase 015 Capability B)
            elif fam == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER":
                synth_patches = self.tranche_synthesizer.synthesize_candidates(
                    opportunity=opp,
                    econ_state=econ_state,
                    baseline_action=baseline_action,
                    boundary_safe_quantities=bool(
                        config is not None
                        and getattr(config, "enable_boundary_safe_quantities", False)
                    ),
                )
                patches.extend(synth_patches)

            # Legacy Market Front-Loading (RETIRED / FALSIFIED)
            elif fam == "FRONTLOAD_ORDERS":
                current_orders = baseline_action.get("market", [])
                reordered = reorder_frontload(current_orders)
                if reordered != current_orders:
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        market_mutations=reordered,
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

            # 3. Opponent Preempt Sell
            # 3. Opponent Preempt Sell & Purchase Preemption (§16–§19)
            elif fam == "OPPONENT_PREEMPT_SELL":
                dep = opp.dependency_info or {}
                action = dep.get("action", "SELL")
                item = dep.get("item", getattr(opp, "target_product", ""))
                qty = int(dep.get("qty", getattr(opp, "quantity", 1)))
                orders = copy.deepcopy(baseline_action.get("market", []))

                if action == "BUY_SEED" and item:
                    if len(orders) < 10:
                        orders.insert(0, ["BUY_SEED", item, qty])
                elif item:
                    # Defensive inventory preemption: bound parcel to max 10
                    parcel = min(10, qty)
                    merged = False
                    for o in orders:
                        if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                            o[2] = min(10, int(o[2]) + parcel)
                            merged = True
                            break
                    if not merged and len(orders) < 10:
                        orders.insert(0, ["SELL", item, parcel])

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    market_mutations=orders[:10],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 4. Terminal Liquidation
            elif fam == "TERMINAL_LIQUIDATION":
                shed = econ_state.farm.shed_inventory
                prices = econ_state.market.current_prices
                # Sort products by total value descending
                sorted_items = sorted(
                    [p for p in PRODUCTS if shed.get(p, 0) > 0],
                    key=lambda p: -(shed[p] * prices.get(p, 1))
                )
                liq_orders = [["SELL", p, shed[p]] for p in sorted_items[:10]]
                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    market_mutations=liq_orders,
                    expected_horizon=1,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 5. Phase Shutdown
            elif fam == "PHASE_SHUTDOWN":
                crop = opp.dependency_info.get("crop")
                orders = copy.deepcopy(baseline_action.get("market", []))
                # Remove BUY_SEED for this crop
                trimmed = [
                    o for o in orders
                    if not (isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "BUY_SEED" and o[1] == crop)
                ]
                if trimmed != orders:
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        market_mutations=trimmed,
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

            # 6. Dynamic Shadow Harvest & Terminal Harvest Sweep (§10, §13, §14)
            elif fam in ("DYNAMIC_SHADOW_HARVEST", "TERMINAL_HARVEST_SWEEP"):
                worker_id = opp.dependency_info.get("worker_id", 0)
                target_xy = opp.dependency_info.get("target_xy")
                crop = opp.dependency_info.get("crop")

                # Fallback tile resolution if target_xy not directly provided
                if target_xy is None:
                    tiles = econ_state.farm.tiles
                    w = econ_state.workers.get_worker(worker_id)
                    w_pos = w.position if w else (0, 0)
                    best_t = None
                    min_d = 999
                    for y, row in enumerate(tiles):
                        for x, tile in enumerate(row):
                            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and int(tile.get("yield_units", 0) or 0) > 0:
                                d = abs(w_pos[0] - x) + abs(w_pos[1] - y)
                                if d < min_d:
                                    min_d = d
                                    best_t = ((x, y), tile.get("crop"))
                    if best_t:
                        target_xy = best_t[0]
                        crop = best_t[1]

                # Default baseline continuation if not passed
                cont = baseline_continuation if baseline_continuation is not None else [
                    copy.deepcopy(baseline_action) for _ in range(max(12, opp.required_horizon))
                ]

                req = CoupledPatchRequest(
                    opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_ids=[worker_id],
                    start_step=econ_state.step,
                    econ_state=econ_state,
                    baseline_action=baseline_action,
                    baseline_continuation=cont,
                    target_location=target_xy,
                    target_commodity=crop,
                    co_worker_trajectories=co_worker_trajectories,
                    horizon=opp.required_horizon,
                    is_terminal_sweep=(fam == "TERMINAL_HARVEST_SWEEP" or econ_state.step >= 650)
                )

                res = self.harvest_generator.generate_harvest_patch(req)
                if res.patch is not None and res.status in ("ACCEPTED", "VERIFIED", "COMMITTED"):
                    patches.append(res.patch)
                elif res.patch is not None and res.trajectory_certificate and res.trajectory_certificate.is_valid:
                    # Provide patch for evaluation / diagnostic inspection
                    patches.append(res.patch)

            # 7. Emergency Feed Purchase (§5, §6, Phase 013 Rescue §24-§29)
            elif fam == "EMERGENCY_FEED_PURCHASE":
                # Strict realizability and alternative gate
                if hasattr(opp, "is_realizable") and not opp.is_realizable:
                    continue
                if hasattr(opp, "dependency_info") and opp.dependency_info.get("is_realizable") is False:
                    continue
                if getattr(opp, "alternative_chosen", "") in ("DO_NOTHING", "EXISTING_INVENTORY", "BASELINE_SAFE", "WHEAT_TO_HAY"):
                    continue

                deficit = getattr(opp, "deficit", opp.dependency_info.get("deficit", 1))
                orders = copy.deepcopy(baseline_action.get("market", []))
                orders.insert(0, ["BUY_PRODUCT", "WHEAT", deficit])
                worker_mutations = {}
                coord_plan = None

                workers = extract_farm_workers(econ_state, current_turn=econ_state.step)
                if len(workers) > 1:
                    from aec.resource.feed_security import FeedSecurityEngine
                    livestock_list = FeedSecurityEngine().extract_livestock(econ_state)
                    unfed = [a for a in livestock_list if not a.fed_today]
                    if unfed:
                        target_animal = unfed[0]
                        tasks = decompose_feed_rescue_to_tasks(
                            deficit=deficit,
                            animal_pos=target_animal.position,
                            current_step=econ_state.step
                        )
                        c_plan = self.multiworker_coordinator.plan_coordination(
                            candidate_tasks=tasks,
                            workers=workers,
                            baseline_action=baseline_action,
                            baseline_continuation=[],
                            current_step=econ_state.step
                        )
                        if c_plan.is_executable:
                            worker_mutations = dict(c_plan.worker_mutations)
                            coord_plan = c_plan

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_mutations=worker_mutations,
                    market_mutations=orders[:10],
                    coordination_plan=coord_plan,
                    affected_obligations=["LIVESTOCK_FEED"],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 8. Dynamic Resource Conversion (§8, §9, Phase 003/004, Phase 004B Remediation)
            elif fam == "RESOURCE_CONVERSION":
                plan_dict = opp.dependency_info.get("execution_plan")
                target = opp.dependency_info.get("target")

                # Reject generic seed purchases / non-conversions (§13, §14, §18)
                if target == "CARROT" or opp.dependency_info.get("opportunity_family") == "RESOURCE_ACQUISITION":
                    continue

                # Comparative Margin-First Precondition (§21, §22, §24)
                comp_val = opp.dependency_info.get("comparative_valuation", {})
                if comp_val and not comp_val.get("is_economically_superior", True):
                    continue

                # 1. Working-Capital Liquidity Precondition (§3, §4, §5, §6, §7, §23)
                liq_dict = opp.dependency_info.get("liquidity_profile", {})
                if liq_dict and liq_dict.get("is_solvent_trajectory") is False:
                    # Insolvent working-capital trajectory: fail closed and abstain
                    continue

                cost = float(opp.dependency_info.get("cost", 0.0))
                net_val = float(opp.dependency_info.get("net_value", 0.0))
                dur = int(opp.dependency_info.get("steps", 24))
                profile = self.liquidity_analyzer.analyze_profile(
                    candidate_target=target or "",
                    upfront_cost=cost,
                    duration_steps=dur,
                    expected_revenue=cost + net_val,
                    econ_state=econ_state
                )
                if not profile.is_solvent_trajectory:
                    continue

                market_mutations = None
                worker_mutations = {}
                reconnect_res = None
                spliced_cont = None
                coord_plan = None

                if plan_dict and plan_dict.get("is_executable"):
                    # Determine labor requirement class (§10)
                    labor_class_str = opp.dependency_info.get("labor_class") or plan_dict.get("labor_class")
                    if labor_class_str:
                        try:
                            labor_class = ConversionLaborClass(labor_class_str)
                        except Exception:
                            labor_class = ConversionLaborClass.AUXILIARY_WORKER_REQUIRED
                    else:
                        labor_class = self.labor_validator.classify_labor_requirement(
                            worker_actions=plan_dict.get("worker_actions", []),
                            target_commodity=target or "",
                            target_location=tuple(plan_dict["target_location"]) if plan_dict.get("target_location") else None
                        )

                    # 2. Physical market mutations
                    plan_market = plan_dict.get("market_actions", [])
                    if plan_market:
                        orders = copy.deepcopy(baseline_action.get("market", []))
                        for m_act in reversed(plan_market):
                            orders.insert(0, list(m_act))
                        market_mutations = orders[:10]

                    # 3. Worker scheduling with Strict Auxiliary Precondition (§9, §11, §12)
                    plan_worker_actions = plan_dict.get("worker_actions", [])
                    workers = extract_farm_workers(econ_state, current_turn=econ_state.step)

                    plan_obj = ConversionExecutionPlan(
                        plan_id=plan_dict.get("plan_id", "CONV"),
                        conversion_id=plan_dict.get("conversion_id", "CONV"),
                        target_commodity=plan_dict.get("target_commodity", target or ""),
                        required_inputs=plan_dict.get("required_inputs", {}),
                        produced_outputs=plan_dict.get("produced_outputs", {}),
                        worker_id=plan_dict.get("worker_id", 1 if len(workers) > 1 else 0),
                        target_location=tuple(plan_dict["target_location"]) if plan_dict.get("target_location") else None,
                        worker_actions=plan_worker_actions,
                        estimated_duration=plan_dict.get("estimated_duration", 1),
                        net_value_est=plan_dict.get("net_value_est", net_val),
                        labor_class=labor_class,
                    )
                    tasks = decompose_conversion_to_tasks(plan_obj, start_step=econ_state.step)

                    if tasks:
                        is_labor_feasible, c_plan, labor_reason = self.labor_validator.validate_and_schedule(
                            tasks=tasks,
                            labor_class=labor_class,
                            workers=workers,
                            baseline_action=baseline_action,
                            baseline_continuation=[],
                            current_step=econ_state.step,
                            estimated_duration=plan_obj.estimated_duration
                        )

                        if not is_labor_feasible or c_plan is None or not c_plan.is_executable:
                            # Strict worker precondition failed: fail-closed and abstain (no Farmer fallback)
                            continue

                        worker_mutations = dict(c_plan.worker_mutations)
                        coord_plan = c_plan

                    # 4. Route Reconnection integration if detour required and approved (§5, §6)
                    if plan_worker_actions and plan_dict.get("reconnect_required") and plan_dict.get("target_location"):
                        worker_id = plan_dict.get("worker_id", 0)
                        if worker_id in worker_mutations:
                            tx, ty = plan_dict["target_location"]
                            reconnect_req = ReconnectRequest(
                                worker=worker_id,
                                divergence_point=econ_state.step,
                                patched_action=plan_worker_actions,
                                intended_target_state=(tx, ty),
                                baseline_continuation=[],
                                remaining_steps=econ_state.remaining_horizon,
                                econ_state=econ_state
                            )
                            reconnect_res = self.reconnect_engine.reconnect(reconnect_req)
                            if not reconnect_res.safety:
                                continue
                            if getattr(reconnect_res, "spliced_trajectory", None):
                                spliced_cont = reconnect_res.spliced_trajectory

                elif opp.dependency_info.get("target"):
                    # Fallback physical synthesis for symbolic fixtures
                    target = opp.dependency_info["target"]
                    fam_type = opp.dependency_info.get("family")
                    if target in ("MILK", "EGG", "WOOL") or fam_type == "FEED_CONVERSION":
                        orders = copy.deepcopy(baseline_action.get("market", []))
                        orders.insert(0, ["BUY_PRODUCT", "WHEAT", 1])
                        market_mutations = orders[:10]
                    elif fam_type == "SEED_CONVERSION" or opp.dependency_info.get("is_seed"):
                        orders = copy.deepcopy(baseline_action.get("market", []))
                        orders.insert(0, ["BUY_SEED", target, 1])
                        market_mutations = orders[:10]
                    elif fam_type == "TERMINAL_CONVERSION":
                        orders = copy.deepcopy(baseline_action.get("market", []))
                        market_mutations = orders[:10]
                    else:
                        # Non-conversion targets abstain
                        continue

                conv_meta = dict(opp.dependency_info)
                conv_meta["liquidity_profile"] = profile.to_dict()

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_mutations=worker_mutations,
                    market_mutations=market_mutations,
                    coordination_plan=coord_plan,
                    spliced_continuation=spliced_cont,
                    reconnect_result=reconnect_res,
                    conversion_metadata=conv_meta,
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 9. Economic Route Compression (§14)
            elif fam == "ROUTE_COMPRESSION":
                wid = getattr(opp, "worker_id", 0)
                if hasattr(opp, "dependency_info") and "worker_id" in opp.dependency_info:
                    wid = opp.dependency_info["worker_id"]

                worker = econ_state.workers.get_worker(wid)
                if worker is None or getattr(worker, "is_frozen", False):
                    continue

                target_pos = getattr(opp, "target_pos", None)
                if target_pos is None and hasattr(opp, "dependency_info"):
                    target_pos = opp.dependency_info.get("target_pos")
                crop = opp.dependency_info.get("crop") if hasattr(opp, "dependency_info") else getattr(opp, "crop_type", None)

                # Default baseline continuation if not passed
                cont = baseline_continuation if baseline_continuation is not None else [
                    copy.deepcopy(baseline_action) for _ in range(max(12, opp.required_horizon))
                ]

                target_tasks = getattr(opp, "target_tasks", None)
                if not target_tasks and hasattr(opp, "dependency_info"):
                    target_tasks = opp.dependency_info.get("target_tasks", [])

                patch_generated = False
                if crop or (target_tasks and "HARVEST" in target_tasks):
                    req = CoupledPatchRequest(
                        opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        worker_ids=[wid],
                        start_step=econ_state.step,
                        econ_state=econ_state,
                        baseline_action=baseline_action,
                        baseline_continuation=cont,
                        target_location=target_pos,
                        target_commodity=crop,
                        co_worker_trajectories=co_worker_trajectories,
                        horizon=opp.required_horizon,
                        is_terminal_sweep=False,
                    )
                    res = self.harvest_generator.generate_harvest_patch(req)
                    if res.patch is not None and (res.status in ("ACCEPTED", "VERIFIED", "COMMITTED") or (res.trajectory_certificate and res.trajectory_certificate.is_valid)):
                        patches.append(res.patch)
                        patch_generated = True

                if not patch_generated:
                    if not target_tasks:
                        target_tasks = ["DROP"] if target_pos in SHED_TILES or target_pos == (0, 0) else ["PASS"]

                    res_table = self.reconnect_engine.build_reservation_table(
                        co_worker_trajectories, wid, opp.required_horizon
                    )

                    move_path = deterministic_find_path(
                        start=worker.position,
                        target=target_pos,
                        start_step=0,
                        reservations=res_table,
                        worker_id=wid,
                        board_size=self.multiworker_coordinator.board_size,
                        max_steps=opp.required_horizon
                    )

                    if move_path is not None or worker.position == target_pos:
                        move_actions = move_path if move_path is not None else []
                        patched_actions = move_actions + target_tasks
                        if patched_actions:
                            reconnect_req = ReconnectRequest(
                                worker=wid,
                                divergence_point=econ_state.step,
                                patched_action=patched_actions,
                                intended_target_state=target_pos,
                                baseline_continuation=cont,
                                remaining_steps=econ_state.remaining_horizon,
                                econ_state=econ_state,
                                co_worker_trajectories=co_worker_trajectories
                            )
                            reconnect_res = self.reconnect_engine.reconnect(reconnect_req)
                            if reconnect_res.safety:
                                spliced_cont = getattr(reconnect_res, "spliced_trajectory", None)
                                comp_actions = []
                                for r_idx, act_c in enumerate(patched_actions):
                                    b_act = copy.deepcopy(baseline_action if r_idx == 0 else (cont[r_idx - 1] if (r_idx - 1) < len(cont) else {}))
                                    if wid == 0:
                                        b_act["farmer"] = [act_c]
                                    else:
                                        h_list = b_act.setdefault("hands", [])
                                        while len(h_list) < wid:
                                            h_list.append(["PASS"])
                                        h_list[wid - 1] = [act_c]
                                    if act_c == "DROP":
                                        m_ord = copy.deepcopy(b_act.get("market", []) or [])
                                        if crop:
                                            m_ord.insert(0, ["SELL", crop, 1])
                                        b_act["market"] = m_ord[:10]
                                    comp_actions.append(b_act)

                                patch = CoupledPatch(
                                    patch_id=f"PATCH_{opp.opportunity_id}",
                                    source_opportunity_id=opp.opportunity_id,
                                    mechanism_family=fam,
                                    worker_ids=[wid],
                                    start_step=econ_state.step,
                                    end_step=econ_state.step + len(patched_actions) - 1,
                                    actions=comp_actions,
                                    worker_mutations={wid: [patched_actions[0]]},
                                    spliced_continuation=spliced_cont,
                                    reconnect_result=reconnect_res,
                                    expected_horizon=opp.required_horizon,
                                    rationale=opp.rationale
                                )
                                patches.append(patch)

            # 10. Multi-Worker Cargo Ferry (§15)
            elif fam == "CARGO_FERRY":
                ferry_wid = getattr(opp, "ferry_worker_id", 1)
                if hasattr(opp, "dependency_info") and "ferry_worker_id" in opp.dependency_info:
                    ferry_wid = opp.dependency_info["ferry_worker_id"]
                elif hasattr(opp, "dependency_info") and "worker_id" in opp.dependency_info:
                    ferry_wid = opp.dependency_info["worker_id"]

                ferry_worker = econ_state.workers.get_worker(ferry_wid)
                if ferry_worker is None or getattr(ferry_worker, "is_frozen", False):
                    continue

                target_pos = getattr(opp, "target_pos", None)
                if target_pos is None and hasattr(opp, "dependency_info"):
                    target_pos = opp.dependency_info.get("target_pos")
                if target_pos is None and opp.dependency_info.get("target_xy"):
                    target_pos = tuple(opp.dependency_info["target_xy"])
                crop = opp.dependency_info.get("crop") if hasattr(opp, "dependency_info") else getattr(opp, "cargo_item", None)

                cont = baseline_continuation if baseline_continuation is not None else [
                    copy.deepcopy(baseline_action) for _ in range(max(12, opp.required_horizon))
                ]

                req = CoupledPatchRequest(
                    opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_ids=[ferry_wid],
                    start_step=econ_state.step,
                    econ_state=econ_state,
                    baseline_action=baseline_action,
                    baseline_continuation=cont,
                    target_location=target_pos,
                    target_commodity=crop,
                    co_worker_trajectories=co_worker_trajectories,
                    horizon=opp.required_horizon,
                    is_terminal_sweep=False,
                )

                res = self.harvest_generator.generate_harvest_patch(req)
                if res.patch is not None and res.status in ("ACCEPTED", "VERIFIED", "COMMITTED"):
                    patches.append(res.patch)
                elif res.patch is not None and res.trajectory_certificate and res.trajectory_certificate.is_valid:
                    patches.append(res.patch)

            # 11. Realizable Shop Arbitrage (§6, §7, §8, §9, §10)
            elif fam == "SHOP_ARBITRAGE":
                # Strict feasibility gate: reject non-realizable candidates
                if hasattr(opp, "is_realizable") and not opp.is_realizable:
                    continue
                if hasattr(opp, "dependency_info") and opp.dependency_info.get("is_realizable") is False:
                    continue

                seq = getattr(opp, "market_sequence", [])
                if not seq and hasattr(opp, "dependency_info"):
                    seq = opp.dependency_info.get("market_sequence", [])

                orders = copy.deepcopy(baseline_action.get("market", []))
                if seq:
                    # Non-commutative sequential insertion:
                    # Maintain strict sequence by inserting at front in reverse
                    for o in reversed(seq):
                        orders.insert(0, copy.deepcopy(o))
                else:
                    item = getattr(opp, "item", "") or getattr(opp, "input_item", "")
                    if item:
                        orders.insert(0, ["BUY_PRODUCT", item, 1])

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    market_mutations=orders[:10],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 11B. Marginal Production Arbitrage (§12–§18)
            elif fam == "PRODUCTION_ARBITRAGE":
                # Strict feasibility and redundancy gate: abstain if not realizable or redundant
                if hasattr(opp, "is_realizable") and not opp.is_realizable:
                    continue
                if hasattr(opp, "is_v3_redundant") and opp.is_v3_redundant:
                    continue
                if hasattr(opp, "dependency_info"):
                    if opp.dependency_info.get("is_realizable") is False or opp.dependency_info.get("is_v3_redundant") is True:
                        continue

                orders = copy.deepcopy(baseline_action.get("market", []))
                seq = getattr(opp, "market_sequence", [])
                if not seq and hasattr(opp, "dependency_info"):
                    seq = opp.dependency_info.get("market_sequence", [])

                if seq:
                    for o in reversed(seq):
                        orders.insert(0, copy.deepcopy(o))
                else:
                    crop = getattr(opp, "output_item", "")
                    if crop:
                        orders.insert(0, ["BUY_SEED", crop, 1])

                wid = getattr(opp, "worker_id", 0)
                tasks = getattr(opp, "worker_tasks", [])
                if not tasks and hasattr(opp, "dependency_info"):
                    tasks = opp.dependency_info.get("worker_tasks", [])

                worker_mutations = {}
                if tasks:
                    worker_mutations[wid] = [tasks[0]]

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_mutations=worker_mutations,
                    market_mutations=orders[:10],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 12. Realizable Terminal Value Conversion (§19–§23)
            elif fam == "TERMINAL_CONVERSION":
                # Strict feasibility and direct liquidation dominance gate
                if hasattr(opp, "is_realizable") and not opp.is_realizable:
                    continue
                if hasattr(opp, "is_liquidation_dominant") and opp.is_liquidation_dominant:
                    continue
                if hasattr(opp, "dependency_info"):
                    if opp.dependency_info.get("is_realizable") is False or opp.dependency_info.get("is_liquidation_dominant") is True:
                        continue

                orders = copy.deepcopy(baseline_action.get("market", []))
                seq = getattr(opp, "market_sequence", [])
                if not seq and hasattr(opp, "dependency_info"):
                    seq = opp.dependency_info.get("market_sequence", [])

                if seq:
                    for o in reversed(seq):
                        orders.insert(0, copy.deepcopy(o))
                else:
                    out_item = getattr(opp, "output_item", "")
                    out_units = getattr(opp, "output_units", 1)
                    if out_item:
                        orders.insert(0, ["SELL", out_item, out_units])

                wid = getattr(opp, "worker_id", 0)
                tasks = getattr(opp, "worker_tasks", [])
                if not tasks and hasattr(opp, "dependency_info"):
                    tasks = opp.dependency_info.get("worker_tasks", [])

                worker_mutations = {}
                if tasks:
                    worker_mutations[wid] = [tasks[0]]

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    worker_mutations=worker_mutations,
                    market_mutations=orders[:10],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 13. Emergency Recovery (§20)
            # 13. Emergency Recovery as Damage Avoidance (§11–§15)
            elif fam == "EMERGENCY_RECOVERY":
                orders = copy.deepcopy(baseline_action.get("market", []))
                dep = opp.dependency_info or {}
                threat = dep.get("threat", "")
                if not threat:
                    threat_enum = getattr(opp, "threat_type", None)
                    threat = str(threat_enum.value) if hasattr(threat_enum, "value") else str(threat_enum or "")

                if "STARVATION" in threat:
                    wheat_in_shed = dep.get("wheat_in_shed", econ_state.farm.get_shed_qty("WHEAT"))
                    if wheat_in_shed <= 0 and len(orders) < 10:
                        orders.insert(0, ["BUY_PRODUCT", "WHEAT", 1])
                elif "INSOLVENCY" in threat:
                    chosen_item = dep.get("chosen_item")
                    qty_to_sell = int(dep.get("qty_to_sell", 1))
                    if chosen_item and qty_to_sell > 0 and len(orders) < 10:
                        orders.insert(0, ["SELL", chosen_item, qty_to_sell])
                elif "TERMINAL" in threat:
                    shed = econ_state.farm.shed_inventory
                    for p in ("STRAWBERRY", "MELON", "TOMATO", "CARROT", "WHEAT", "WOOL", "MILK", "EGG"):
                        if shed.get(p, 0) > 0 and len(orders) < 10:
                            orders.append(["SELL", p, shed[p]])

                patch = CoupledPatch(
                    patch_id=f"PATCH_{opp.opportunity_id}",
                    source_opportunity_id=opp.opportunity_id,
                    mechanism_family=fam,
                    market_mutations=orders[:10],
                    expected_horizon=opp.required_horizon,
                    rationale=opp.rationale
                )
                patches.append(patch)

            # 14. Town Cycle Signal Timing (§22)
            elif fam == "TOWN_CYCLE":
                timing_action = opp.dependency_info.get("timing_action", "DELAY_SALE")
                item = opp.dependency_info.get("item")
                qty = opp.dependency_info.get("qty", 1)
                current_orders = copy.deepcopy(baseline_action.get("market", []))
                mutated_orders = None

                if timing_action == "DELAY_SALE" and item:
                    # Defer sale by omitting SELL of this item from current turn's basket
                    filtered = [
                        o for o in current_orders
                        if not (isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL" and o[1] == item)
                    ]
                    if filtered != current_orders:
                        mutated_orders = filtered
                elif timing_action == "PARTIAL_SALE" and item:
                    # Partial staged sale: sell qty_sell now, holding remainder
                    qty_sell = opp.dependency_info.get("qty_sell", 1)
                    mutated = []
                    replaced = False
                    for o in current_orders:
                        if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                            if not replaced and qty_sell > 0:
                                mutated.append(["SELL", item, int(qty_sell)])
                                replaced = True
                        else:
                            mutated.append(o)
                    if replaced:
                        mutated_orders = mutated
                elif timing_action == "ADVANCE_SALE" and item:
                    # Accelerate sale by inserting bounded parcel SELL of shed inventory
                    parcel_qty = min(10, int(qty))
                    if len(current_orders) < 10:
                        mutated_orders = [["SELL", item, parcel_qty]] + [
                            o for o in current_orders
                            if not (isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL" and o[1] == item)
                        ][:9]
                elif item:
                    # Generic timing alteration
                    filtered = [
                        o for o in current_orders
                        if not (isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "SELL" and o[1] == item)
                    ]
                    if filtered != current_orders:
                        mutated_orders = filtered

                if mutated_orders is not None:
                    patch = CoupledPatch(
                        patch_id=f"PATCH_{opp.opportunity_id}",
                        source_opportunity_id=opp.opportunity_id,
                        mechanism_family=fam,
                        market_mutations=mutated_orders,
                        expected_horizon=opp.required_horizon,
                        rationale=opp.rationale
                    )
                    patches.append(patch)

        return patches
