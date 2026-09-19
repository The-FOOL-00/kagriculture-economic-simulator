# SPDX-License-Identifier: MIT
"""Event Type Definitions and Event Dataclass for AEC."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EventType(str, Enum):
    """Initial event categories specified by AEC architecture (§6, §7)."""
    E1_FARM_OBSTRUCTION = "E1_FARM_OBSTRUCTION"             # Weed or unit blocking planned work
    E2_CASH_DEVIATION = "E2_CASH_DEVIATION"                 # Material cash shortage or divergence
    E3_SHED_CAPACITY_RISK = "E3_SHED_CAPACITY_RISK"         # Shed approaching 100 capacity discard
    E4_MARKET_REGIME_SHIFT = "E4_MARKET_REGIME_SHIFT"       # Price shock or liquidity change
    E5_OPPONENT_SUPPLY_SHOCK = "E5_OPPONENT_SUPPLY_SHOCK"   # Rival crop dump or shearing surge
    E6_SHOP_INFORMATION_REVEAL = "E6_SHOP_INFORMATION_REVEAL" # New town shop unlocked
    E7_PRODUCTION_DEADLINE = "E7_PRODUCTION_DEADLINE"       # Biological cutoff point of no return
    E8_TERMINAL_TRANSITION = "E8_TERMINAL_TRANSITION"       # Entering terminal endgame phase
    E9_LIVESTOCK_STARVATION_RISK = "E9_LIVESTOCK_STARVATION_RISK" # Animal starvation imminent
    E10_TOWN_CYCLE_PHASE = "E10_TOWN_CYCLE_PHASE"           # Town shop refresh / absorption cycle
    E11_OPPONENT_PRESSURE_SHIFT = "E11_OPPONENT_PRESSURE_SHIFT" # Material change in rival pressure
    E12_RESOURCE_BOTTLENECK = "E12_RESOURCE_BOTTLENECK"     # Feed or input deficit for active assets


@dataclass
class Event:
    """An explicit, inspectable event detected in the game state."""
    event_type: EventType
    step: int
    severity: float = 0.5            # 0.0 (minor) to 1.0 (critical)
    rationale: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "step": self.step,
            "severity": round(self.severity, 3),
            "rationale": self.rationale,
            "payload": self.payload,
            "confidence": round(self.confidence, 3),
        }
