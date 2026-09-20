# SPDX-License-Identifier: MIT
"""Macro-Regime Boundary Detection and Fingerprinting (§5, §9, §10, §14).

Detects potential policy-regime transitions in the frozen V3 continuation
induced by candidate state mutations (cash, inventory, labor, capex gates).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import PRODUCTS, TURNS_PER_DAY
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


class MacroRegimeType(str, Enum):
    """Classification of V3 endogenous macro regimes (§7, §10)."""
    NONE = "NONE"
    CASH_CAPEX_GATE = "CASH_CAPEX_GATE"           # Day 12 Sheep ($10k) or Day 18 Tomato ($12k)
    BUDGET_GUARD_BLOCK = "BUDGET_GUARD_BLOCK"     # Step % 72 == 0 6-day budget shortfall
    DAY_END_ROOM_GUARD = "DAY_END_ROOM_GUARD"     # Step % 24 == 23 shed overflow risk
    ORDER_QUEUE_ALTERATION = "ORDER_QUEUE_ALTERATION" # Dropping atomic HIRE/BUY_LAND
    LIVESTOCK_FEED_RISK = "LIVESTOCK_FEED_RISK"   # Altering wheat reserves with active livestock
    TERMINAL_TRANSITION = "TERMINAL_TRANSITION"   # Step >= 672 endgame proximity


V3_CASH_GATES: Tuple[float, ...] = (500.0, 600.0, 1000.0, 2000.0, 5000.0, 7500.0, 10000.0, 12000.0)


def classify_cash_bracket(cash: float) -> int:
    """Discretizes cash into macro-relevant operational brackets (§9).
    
    0: Deep liquidity constrained (< $500)
    1: Tactical working capital ($500 - $2,000)
    2: Mid-game operational accumulation ($2,000 - $8,000)
    3: Sheep capex qualification range ($8,000 - $12,000)
    4: Tomato capex qualification range (>= $12,000)
    """
    if cash < 500.0:
        return 0
    elif cash < 2000.0:
        return 1
    elif cash < 8000.0:
        return 2
    elif cash < 12000.0:
        return 3
    else:
        return 4


@dataclass(frozen=True)
class MacroRegimeFingerprint:
    """Compact deterministic fingerprint of macro-observable farm state (§9)."""
    step: int
    day: int
    cash: float
    cash_bracket: int
    quadrants_count: int
    hands_count: int
    has_animals: bool
    animal_counts: Tuple[Tuple[str, int], ...]
    wheat_in_shed: int
    total_shed_units: int
    unlocked_shops: Tuple[str, ...]
    next_block_step: int
    next_day_end_step: int

    def differs_macro_materially(self, other: MacroRegimeFingerprint) -> Tuple[bool, List[str]]:
        """Determines if two fingerprints represent fundamentally different macro regimes."""
        reasons = []
        if self.cash_bracket != other.cash_bracket:
            reasons.append(f"CASH_BRACKET_SHIFT: {self.cash_bracket} -> {other.cash_bracket} (${self.cash:.1f} -> ${other.cash:.1f})")
        if self.hands_count != other.hands_count:
            reasons.append(f"WORKER_COUNT_SHIFT: {self.hands_count} -> {other.hands_count}")
        if self.quadrants_count != other.quadrants_count:
            reasons.append(f"QUADRANTS_COUNT_SHIFT: {self.quadrants_count} -> {other.quadrants_count}")
        if self.has_animals != other.has_animals:
            reasons.append(f"LIVESTOCK_PRESENCE_SHIFT: {self.has_animals} -> {other.has_animals}")
        if self.wheat_in_shed != other.wheat_in_shed and (self.has_animals or other.has_animals):
            reasons.append(f"GRAIN_RESERVE_SHIFT: {self.wheat_in_shed} -> {other.wheat_in_shed}")
        if self.total_shed_units > 90 or other.total_shed_units > 90:
            if abs(self.total_shed_units - other.total_shed_units) >= 5:
                reasons.append(f"SHED_SATURATION_SHIFT: {self.total_shed_units} -> {other.total_shed_units}")
        return len(reasons) > 0, reasons


@dataclass
class MacroBoundaryProbeResult:
    """Outcome of pre-simulation macro boundary probing (§14)."""
    requires_escalation: bool = False
    regime_type: MacroRegimeType = MacroRegimeType.NONE
    reason: str = ""
    recommended_horizon: int = 18
    earliest_divergence_step: int = 0
    baseline_fingerprint: Optional[MacroRegimeFingerprint] = None
    candidate_fingerprint: Optional[MacroRegimeFingerprint] = None


class MacroRegimeTransitionDetector:
    """Detects when candidate patches risk inducing V3 policy divergence (§10, §14)."""

    def __init__(self, max_escalation_horizon: int = 120) -> None:
        self.max_escalation_horizon = max_escalation_horizon

    def compute_fingerprint(
        self,
        econ_state: EconomicState,
        cash_override: Optional[float] = None,
        shed_override: Optional[Dict[str, int]] = None,
        hands_override: Optional[int] = None,
        quadrants_override: Optional[int] = None,
    ) -> MacroRegimeFingerprint:
        """Derive deterministic fingerprint from an EconomicState and optional overrides."""
        step = econ_state.step
        day = step // TURNS_PER_DAY
        cash = float(cash_override if cash_override is not None else econ_state.farm.cash)
        cash_bracket = classify_cash_bracket(cash)
        
        quad_count = (
            quadrants_override
            if quadrants_override is not None
            else len(getattr(econ_state.farm, "unlocked_quadrants", ["NW"]))
        )
        
        hands_cnt = (
            hands_override
            if hands_override is not None
            else max(0, len(econ_state.workers.workers) - 1)
        )

        shed = shed_override if shed_override is not None else econ_state.farm.shed_inventory
        wheat_qty = int(shed.get("WHEAT", 0))
        total_shed = sum(int(v) for v in shed.values())

        # Animal census across tiles, shed, and worker cargo
        animal_map: Dict[str, int] = {}
        for a in ("COW", "SHEEP", "GOOSE"):
            qty = int(shed.get(a, 0))
            for row in getattr(econ_state.farm, "tiles", []):
                for tile in row:
                    if isinstance(tile, dict) and tile.get("animal") == a:
                        qty += 1
            for w in econ_state.workers.workers:
                qty += int(w.cargo.get(a, 0))
            if qty > 0:
                animal_map[a] = qty

        animal_counts_tuple = tuple(sorted(animal_map.items()))
        has_animals = len(animal_counts_tuple) > 0

        shops = tuple(sorted(econ_state.market.unlocked_shops))
        
        # Next macro cycle milestones
        next_block = ((step // 72) + 1) * 72
        next_day_end = (day * TURNS_PER_DAY) + 23

        return MacroRegimeFingerprint(
            step=step,
            day=day,
            cash=cash,
            cash_bracket=cash_bracket,
            quadrants_count=quad_count,
            hands_count=hands_cnt,
            has_animals=has_animals,
            animal_counts=animal_counts_tuple,
            wheat_in_shed=wheat_qty,
            total_shed_units=total_shed,
            unlocked_shops=shops,
            next_block_step=next_block,
            next_day_end_step=next_day_end,
        )

    def probe_candidate(
        self,
        patch: CoupledPatch,
        baseline_action: Dict[str, Any],
        econ_state: EconomicState,
        base_horizon: int = 18,
    ) -> MacroBoundaryProbeResult:
        """Inspects candidate action and state delta to detect potential V3 policy divergence (§14)."""
        step = econ_state.step
        remaining = econ_state.remaining_horizon
        base_fp = self.compute_fingerprint(econ_state)

        # ---------------------------------------------------------------------
        # 1. Check Atomic Order Queue Alteration (HIRE, BUY_LAND, BUY_ANIMAL)
        # ---------------------------------------------------------------------
        # If baseline emitted an atomic capex or hire order and the patch modifies market:
        base_mkt = baseline_action.get("market", []) or []
        cand_action = patch.apply(baseline_action)
        cand_mkt = cand_action.get("market", []) or []

        base_atomics = [o for o in base_mkt if isinstance(o, (list, tuple)) and o and o[0] in ("HIRE", "BUY_LAND", "BUY_ANIMAL")]
        cand_atomics = [o for o in cand_mkt if isinstance(o, (list, tuple)) and o and o[0] in ("HIRE", "BUY_LAND", "BUY_ANIMAL")]

        if base_atomics != cand_atomics:
            # Atomic order dropped or mutated!
            # E.g. Missing a HIRE causes permanent labor divergence
            target_h = min(remaining, max(base_horizon, 48))
            return MacroBoundaryProbeResult(
                requires_escalation=True,
                regime_type=MacroRegimeType.ORDER_QUEUE_ALTERATION,
                reason=f"ATOMIC_ORDER_ALTERATION: Baseline {base_atomics} != Candidate {cand_atomics}",
                recommended_horizon=target_h,
                earliest_divergence_step=step,
                baseline_fingerprint=base_fp,
            )

        # ---------------------------------------------------------------------
        # 2. Estimate Candidate State Post-Action
        # ---------------------------------------------------------------------
        # Approximate immediate delta at step t
        cand_cash = base_fp.cash
        cand_shed = copy.deepcopy(econ_state.farm.shed_inventory)
        
        # Account for market order deltas
        prices = econ_state.market.current_prices
        for o in cand_mkt:
            if not isinstance(o, (list, tuple)) or len(o) < 2:
                continue
            op = o[0]
            if op == "SELL" and len(o) >= 3:
                item, qty = o[1], int(o[2])
                price = float(prices.get(item, 20.0))
                real_qty = min(cand_shed.get(item, 0), qty)
                cand_cash += real_qty * price
                cand_shed[item] = max(0, cand_shed.get(item, 0) - real_qty)
            elif op == "BUY_PRODUCT" and len(o) >= 3:
                item, qty = o[1], int(o[2])
                price = float(prices.get(item, 20.0))
                cand_cash -= qty * price
                cand_shed[item] = cand_shed.get(item, 0) + qty

        cand_fp = self.compute_fingerprint(
            econ_state,
            cash_override=cand_cash,
            shed_override=cand_shed,
        )

        # ---------------------------------------------------------------------
        # 3. Capex Boundary & Proximity Check (Day 12 Sheep, Day 18 Tomato)
        # ---------------------------------------------------------------------
        crossed_gates = [
            g for g in V3_CASH_GATES
            if (base_fp.cash < g <= cand_cash) or (cand_cash < g <= base_fp.cash)
        ]
        if crossed_gates:
            return MacroBoundaryProbeResult(
                requires_escalation=True,
                regime_type=MacroRegimeType.CASH_CAPEX_GATE,
                reason=f"CASH_GATE_CROSSED: Cash delta (${base_fp.cash:.1f} -> ${cand_cash:.1f}) crossed V3 macro threshold(s): {crossed_gates}",
                recommended_horizon=min(remaining, max(base_horizon * 2, 36)),
                earliest_divergence_step=step,
                baseline_fingerprint=base_fp,
                candidate_fingerprint=cand_fp,
            )

        # Sheep gate: Day 12 (steps 288..290)
        # Tomato gate: Day 18 (steps 432..436)
        if step < 288 and (288 - step) <= self.max_escalation_horizon:
            # Proximity to Day 12 sheep expansion gate
            if (cand_fp.cash_bracket >= 3 or cand_cash >= 7500.0) and base_fp.cash < 7500.0:
                needed_h = (288 - step) + 24
                h = min(remaining, min(self.max_escalation_horizon, max(base_horizon, needed_h)))
                return MacroBoundaryProbeResult(
                    requires_escalation=True,
                    regime_type=MacroRegimeType.CASH_CAPEX_GATE,
                    reason=f"DAY_12_SHEEP_CAPEX_RISK: Cash injection (${base_fp.cash:.1f} -> ${cand_cash:.1f}) approaches Day 12 sheep gate",
                    recommended_horizon=h,
                    earliest_divergence_step=288,
                    baseline_fingerprint=base_fp,
                    candidate_fingerprint=cand_fp,
                )

        if step < 432 and (432 - step) <= self.max_escalation_horizon:
            # Proximity to Day 18 tomato expansion gate ($12,000 threshold)
            if (cand_fp.cash_bracket >= 4 or cand_cash >= 11000.0) and base_fp.cash < 11000.0:
                needed_h = (432 - step) + 24
                h = min(remaining, min(self.max_escalation_horizon, max(base_horizon, needed_h)))
                return MacroBoundaryProbeResult(
                    requires_escalation=True,
                    regime_type=MacroRegimeType.CASH_CAPEX_GATE,
                    reason=f"DAY_18_TOMATO_CAPEX_RISK: Cash injection (${base_fp.cash:.1f} -> ${cand_cash:.1f}) approaches Day 18 tomato gate ($12k)",
                    recommended_horizon=h,
                    earliest_divergence_step=432,
                    baseline_fingerprint=base_fp,
                    candidate_fingerprint=cand_fp,
                )

        # ---------------------------------------------------------------------
        # 4. Budget Guard Shortfall Risk (Step % 72 Boundary)
        # ---------------------------------------------------------------------
        steps_to_block = base_fp.next_block_step - step
        if steps_to_block <= 18:
            # Proximity to 6-day block budget guard
            cash_delta = cand_cash - base_fp.cash
            shed_delta = cand_fp.total_shed_units - base_fp.total_shed_units
            if abs(cash_delta) >= 150.0 or abs(shed_delta) >= 5:
                needed_h = steps_to_block + 12
                h = min(remaining, min(self.max_escalation_horizon, max(base_horizon, needed_h)))
                return MacroBoundaryProbeResult(
                    requires_escalation=True,
                    regime_type=MacroRegimeType.BUDGET_GUARD_BLOCK,
                    reason=f"BUDGET_GUARD_RISK: State mutation within {steps_to_block} steps of block boundary {base_fp.next_block_step}",
                    recommended_horizon=h,
                    earliest_divergence_step=base_fp.next_block_step,
                    baseline_fingerprint=base_fp,
                    candidate_fingerprint=cand_fp,
                )

        # ---------------------------------------------------------------------
        # 5. Day-End Storage Room Guard Risk (Hour 23)
        # ---------------------------------------------------------------------
        steps_to_day_end = base_fp.next_day_end_step - step
        if steps_to_day_end <= 6 and (base_fp.total_shed_units >= 85 or cand_fp.total_shed_units >= 85):
            needed_h = steps_to_day_end + 4
            h = min(remaining, max(base_horizon, needed_h))
            return MacroBoundaryProbeResult(
                requires_escalation=True,
                regime_type=MacroRegimeType.DAY_END_ROOM_GUARD,
                reason=f"ROOM_GUARD_RISK: Shed near capacity ({cand_fp.total_shed_units}/100) near Hour 23",
                recommended_horizon=h,
                earliest_divergence_step=base_fp.next_day_end_step,
                baseline_fingerprint=base_fp,
                candidate_fingerprint=cand_fp,
            )

        # ---------------------------------------------------------------------
        # 6. Livestock Grain & Feed Security Risk
        # ---------------------------------------------------------------------
        if base_fp.has_animals and cand_fp.wheat_in_shed < base_fp.wheat_in_shed:
            wheat_drop = base_fp.wheat_in_shed - cand_fp.wheat_in_shed
            if cand_fp.wheat_in_shed < 12 or wheat_drop >= 4:
                needed_h = min(remaining, max(base_horizon, 36))
                return MacroBoundaryProbeResult(
                    requires_escalation=True,
                    regime_type=MacroRegimeType.LIVESTOCK_FEED_RISK,
                    reason=f"FEED_DEFICIT_RISK: Selling grain ({wheat_drop} wheat) with active livestock",
                    recommended_horizon=needed_h,
                    earliest_divergence_step=step,
                    baseline_fingerprint=base_fp,
                    candidate_fingerprint=cand_fp,
                )

        # ---------------------------------------------------------------------
        # 7. Material Macro Regime Shift Detection
        # ---------------------------------------------------------------------
        differs, reasons = base_fp.differs_macro_materially(cand_fp)
        if differs:
            needed_h = min(remaining, max(base_horizon, 36))
            return MacroBoundaryProbeResult(
                requires_escalation=True,
                regime_type=MacroRegimeType.CASH_CAPEX_GATE,
                reason=f"MATERIAL_REGIME_SHIFT: {'; '.join(reasons)}",
                recommended_horizon=needed_h,
                earliest_divergence_step=step,
                baseline_fingerprint=base_fp,
                candidate_fingerprint=cand_fp,
            )

        # No escalation required -> Tier 1 local horizon is sufficient
        return MacroBoundaryProbeResult(
            requires_escalation=False,
            regime_type=MacroRegimeType.NONE,
            reason="NO_MACRO_DIVERGENCE_RISK",
            recommended_horizon=base_horizon,
            baseline_fingerprint=base_fp,
            candidate_fingerprint=cand_fp,
        )
