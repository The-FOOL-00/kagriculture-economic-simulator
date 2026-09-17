# SPDX-License-Identifier: MIT
"""Deterministic Event Detectors for AEC."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import (
    AECConfig,
    CROPS,
    PRODUCTS,
    SHOP_UNLOCK_INTERVAL,
)
from aec.events.event_types import Event, EventType
from aec.ir.economic_state import EconomicState


def detect_events(
    econ_state: EconomicState,
    previous_state: Optional[EconomicState] = None,
    baseline_action: Optional[Dict[str, Any]] = None,
    config: Optional[AECConfig] = None
) -> List[Event]:
    """Detect events deterministically from the current Economic IR."""
    cfg = config or AECConfig()
    events: List[Event] = []
    step = econ_state.step

    # -------------------------------------------------------------------------
    # E1: Farm Obstruction Detector
    # -------------------------------------------------------------------------
    tiles = econ_state.farm.tiles
    obstructed_workers: List[int] = []
    for w in econ_state.workers.workers:
        x, y = w.position
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
            t = tiles[y][x]
            if isinstance(t, dict) and t.get("kind") == "WEED":
                obstructed_workers.append(w.worker_id)
                
    if obstructed_workers:
        events.append(Event(
            event_type=EventType.E1_FARM_OBSTRUCTION,
            step=step,
            severity=0.7,
            rationale=f"Workers {obstructed_workers} standing on weed tile",
            payload={"worker_ids": obstructed_workers},
            confidence=1.0
        ))

    # -------------------------------------------------------------------------
    # E2: Cash Deviation Detector
    # -------------------------------------------------------------------------
    cash = econ_state.farm.cash
    if cash < cfg.cash_deviation_threshold:
        severity = min(1.0, (cfg.cash_deviation_threshold - cash) / cfg.cash_deviation_threshold)
        events.append(Event(
            event_type=EventType.E2_CASH_DEVIATION,
            step=step,
            severity=max(0.4, severity),
            rationale=f"Low cash balance: ${cash:.2f} < ${cfg.cash_deviation_threshold:.2f}",
            payload={"cash": cash, "threshold": cfg.cash_deviation_threshold},
            confidence=1.0
        ))

    # -------------------------------------------------------------------------
    # E3: Shed Capacity Risk Detector
    # -------------------------------------------------------------------------
    shed_units = econ_state.farm.shed_total_units
    total_phys = econ_state.farm.total_physical_inventory
    is_late_hour = econ_state.hour >= 20
    
    if shed_units >= cfg.shed_alarm_threshold or (is_late_hour and total_phys >= 95):
        events.append(Event(
            event_type=EventType.E3_SHED_CAPACITY_RISK,
            step=step,
            severity=0.9 if total_phys >= 98 else 0.6,
            rationale=f"Shed capacity risk: shed={shed_units}, total_phys={total_phys} at hour {econ_state.hour}",
            payload={"shed_units": shed_units, "total_phys": total_phys, "hour": econ_state.hour},
            confidence=1.0
        ))

    # -------------------------------------------------------------------------
    # E4: Market Regime Shift Detector
    # -------------------------------------------------------------------------
    shifted_products: Dict[str, float] = {}
    for p in PRODUCTS:
        liquidity = econ_state.market.get_liquidity(p)
        if abs(liquidity - 1.0) >= cfg.price_shock_relative:
            shifted_products[p] = round(liquidity, 2)
            
    if shifted_products:
        events.append(Event(
            event_type=EventType.E4_MARKET_REGIME_SHIFT,
            step=step,
            severity=0.5,
            rationale=f"Significant price shifts in: {shifted_products}",
            payload={"price_liquidity": shifted_products},
            confidence=0.9
        ))

    # -------------------------------------------------------------------------
    # E5: Opponent Supply Shock Detector
    # -------------------------------------------------------------------------
    high_opp_supply = {
        p: qty for p, qty in econ_state.opponent.supply_forecast.items()
        if qty >= float(cfg.opponent_supply_shock_qty)
    }
    if high_opp_supply:
        events.append(Event(
            event_type=EventType.E5_OPPONENT_SUPPLY_SHOCK,
            step=step,
            severity=0.6,
            rationale=f"High opponent supply forecast: {high_opp_supply}",
            payload={"supply_forecast": high_opp_supply},
            confidence=0.85
        ))

    # -------------------------------------------------------------------------
    # E6: Shop Information Reveal Detector
    # -------------------------------------------------------------------------
    if step > 0 and step % SHOP_UNLOCK_INTERVAL == 0 and step <= 576:
        events.append(Event(
            event_type=EventType.E6_SHOP_INFORMATION_REVEAL,
            step=step,
            severity=0.8,
            rationale=f"Shop unlock boundary at step {step}: shops={econ_state.market.unlocked_shops}",
            payload={"unlocked_shops": list(econ_state.market.unlocked_shops)},
            confidence=1.0
        ))

    # -------------------------------------------------------------------------
    # E7: Production Feasibility / Deadline Detector
    # -------------------------------------------------------------------------
    # Major biological shutdown milestones
    if step in (574, 622, 670):
        events.append(Event(
            event_type=EventType.E7_PRODUCTION_DEADLINE,
            step=step,
            severity=0.85,
            rationale=f"Biological crop cutoff milestone at step {step}",
            payload={"step": step, "feasibility": econ_state.crop_feasibility},
            confidence=1.0
        ))

    # -------------------------------------------------------------------------
    # E8: Terminal Transition Detector
    # -------------------------------------------------------------------------
    if step >= 670:
        events.append(Event(
            event_type=EventType.E8_TERMINAL_TRANSITION,
            step=step,
            severity=1.0 if step >= 712 else 0.8,
            rationale=f"In terminal endgame window: {econ_state.remaining_horizon} steps remaining",
            payload={"remaining_horizon": econ_state.remaining_horizon},
            confidence=1.0
        ))

    return events
