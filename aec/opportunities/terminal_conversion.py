# SPDX-License-Identifier: MIT
"""Terminal Conversion Opportunity and Detector (§19, §20, §21, §22, §23).

Realizable Terminal Value Conversion:
1. Exact remaining runway proof (must complete before step 718 cutoff).
2. Mandatory comparative valuation against direct raw liquidation.
3. Shed capacity and worker transit feasibility checks.
4. Prevention of high-value harvest task displacement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import FINAL_STEP, PRODUCTS, SHED_CAPACITY, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES
from aec.opportunities.base import Opportunity


@dataclass
class TerminalConversionOpportunity(Opportunity):
    """An opportunity executing realizable terminal value conversion (§19, §20, §21, §22, §23)."""
    input_item: str = ""
    input_units: int = 1
    output_item: str = ""
    output_units: int = 1
    raw_liquidation_value: float = 0.0
    conversion_gross_value: float = 0.0
    net_incremental_value: float = 0.0
    runway_needed: int = 4
    runway_available: int = 0
    worker_id: int = 0
    worker_tasks: List[str] = field(default_factory=list)
    target_location: Optional[Tuple[int, int]] = None
    is_runway_proven: bool = True
    is_liquidation_dominant: bool = False
    is_realizable: bool = True
    rejection_reason: Optional[str] = None
    market_sequence: List[List[Any]] = field(default_factory=list)


class TerminalConversionDetector:
    """Detects late-game (steps 670-716) conversion opportunities to maximize liquidated cash before step 718.
    
    Acceptance criteria:
    1. Runway Proof: Conversion completes before step 718 cutoff including transit and drop.
    2. Direct Liquidation Gate: Converted net terminal value > Direct raw liquidation value.
    3. Shed Capacity Feasibility: Transformed units fit within shed capacity.
    4. Worker Accessibility: Target location reachable without excessive transit delay.
    5. No Harvest Displacement: Primary workers not displaced from mature melon/crop harvests.
    """

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None,
        baseline_continuation: Optional[List[Dict[str, Any]]] = None,
    ) -> List[TerminalConversionOpportunity]:
        opportunities: List[TerminalConversionOpportunity] = []
        step = econ_state.step

        # Active in endgame window: steps 670 to 716
        if not (670 <= step <= 716):
            return []

        rem_steps = 718 - step
        if rem_steps <= 2:
            return []

        shed = getattr(econ_state.farm, "shed_inventory", {})
        shed_total = getattr(econ_state.farm, "shed_total_units", 0)
        workers = getattr(econ_state.workers, "workers", [])
        if not workers:
            return []

        # Auxiliary hands preferred, else worker 0
        assigned_worker = workers[-1] if len(workers) > 1 else workers[0]
        wid = assigned_worker.worker_id
        w_pos = assigned_worker.position

        # Standard late-game conversion paths
        # Format: (input_item, input_qty, output_item, output_qty, default_target_pos)
        paths = [
            ("WHEAT", 1, "WOOL", 1, (2, 2)),
            ("WHEAT", 1, "MILK", 1, (3, 3)),
            ("WHEAT", 1, "EGG", 1, (4, 2)),
            ("MELON", 1, "MELON_JUICE", 1, (5, 5)),
        ]

        # Check if workers are busy harvesting mature field crops
        harvest_busy = getattr(econ_state, "workers_busy_with_harvest", False)

        for in_item, in_qty, out_item, out_qty, default_pos in paths:
            curr_in_stock = shed.get(in_item, 0)
            if curr_in_stock < in_qty:
                continue

            target_pos = getattr(econ_state, f"{out_item.lower()}_target_pos", default_pos)
            if hasattr(econ_state, "override_target_pos"):
                target_pos = econ_state.override_target_pos

            # Pricing & Valuation
            p_in = float(econ_state.market.get_price(in_item))
            p_out = float(econ_state.market.get_price(out_item) if out_item in PRODUCTS else getattr(econ_state.market, "prices", {}).get(out_item, 0.0))
            if hasattr(econ_state.market, "projected_prices") and out_item in econ_state.market.projected_prices:
                p_out = float(econ_state.market.projected_prices[out_item])

            raw_val = float(in_qty * p_in)
            conv_val = float(out_qty * p_out)
            displaced_val = 250.0 if harvest_busy else 0.0
            net_delta = conv_val - raw_val - displaced_val

            # Transit & Runway Proof
            dist = abs(w_pos[0] - target_pos[0]) + abs(w_pos[1] - target_pos[1])
            transit_turns = dist
            process_turns = 1
            deposit_turns = 1
            liquidation_turns = 2  # Window to sell and liquidate
            runway_needed = transit_turns + process_turns + deposit_turns + liquidation_turns

            is_runway_proven = (runway_needed <= rem_steps)
            is_liq_dominant = False
            is_realizable = True
            rejection_reason: Optional[str] = None

            # 1. Output Salability Check
            if p_out <= 0.0 or getattr(econ_state.market, "market_closed", False):
                is_realizable = False
                rejection_reason = "Output cannot be sold / market depth exhausted"

            # 2. Runway Proof Check
            elif runway_needed > rem_steps:
                is_runway_proven = False
                is_realizable = False
                rejection_reason = f"Insufficient terminal runway (needed {runway_needed} > available {rem_steps})"

            # 3. Worker Distance Check
            elif dist > 6:
                is_realizable = False
                rejection_reason = f"Worker too far away (distance {dist} > max allowance 6)"

            # 4. Shed Capacity Check
            elif shed_total >= SHED_CAPACITY or (shed_total + (out_qty - in_qty)) > SHED_CAPACITY:
                is_realizable = False
                rejection_reason = f"Shed capacity insufficient ({shed_total + out_qty - in_qty} > {SHED_CAPACITY})"

            # 5. Scarce Resource Check
            elif getattr(econ_state, "is_input_scarce", False):
                is_realizable = False
                rejection_reason = "Conversion consumes scarce resource required for mandatory obligation"

            # 6. Direct Liquidation Comparison
            elif net_delta <= 0:
                is_liq_dominant = True
                is_realizable = False
                if harvest_busy:
                    rejection_reason = "Displaced worker value exceeds conversion margin"
                else:
                    rejection_reason = f"Dominated by direct raw liquidation (raw ${raw_val:.1f} >= conv ${conv_val:.1f})"

            market_seq = [["SELL", out_item, out_qty]] if is_realizable else []
            worker_tasks = ["MOVE", "PROCESS", "DEPOSIT"]

            opportunities.append(TerminalConversionOpportunity(
                opportunity_id=f"TERM_CONV_{step}_{in_item}_{out_item}",
                category="TERMINAL",
                event_trigger=None,
                affected_entities=[in_item, out_item, wid],
                estimated_economic_relevance=max(0.0, net_delta),
                candidate_transformation_family="TERMINAL_CONVERSION",
                required_horizon=min(rem_steps, runway_needed + 2),
                rationale=(
                    f"Terminal conversion {in_item} -> {out_item}: raw=${raw_val:.1f}, "
                    f"conv=${conv_val:.1f}, net=+${net_delta:.1f} "
                    f"({'REALIZABLE' if is_realizable else rejection_reason})"
                ),
                confidence=0.9 if is_realizable else 0.1,
                scientific_status=ScientificStatus.VERIFIED_SOURCE if is_realizable else ScientificStatus.FALSIFIED,
                input_item=in_item,
                input_units=in_qty,
                output_item=out_item,
                output_units=out_qty,
                raw_liquidation_value=raw_val,
                conversion_gross_value=conv_val,
                net_incremental_value=net_delta,
                runway_needed=runway_needed,
                runway_available=rem_steps,
                worker_id=wid,
                worker_tasks=worker_tasks,
                target_location=target_pos,
                is_runway_proven=is_runway_proven,
                is_liquidation_dominant=is_liq_dominant,
                is_realizable=is_realizable,
                rejection_reason=rejection_reason,
                market_sequence=market_seq,
                dependency_info={
                    "input_item": in_item,
                    "output_item": out_item,
                    "worker_id": wid,
                    "worker_tasks": worker_tasks,
                    "is_realizable": is_realizable,
                    "is_runway_proven": is_runway_proven,
                    "is_liquidation_dominant": is_liq_dominant,
                    "rejection_reason": rejection_reason,
                    "net_delta": net_delta,
                    "market_sequence": market_seq,
                }
            ))

        return opportunities

