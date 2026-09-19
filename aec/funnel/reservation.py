# SPDX-License-Identifier: MIT
"""Phase 018 Repair A: mechanism-agnostic candidate-funnel reservation (§9–§13).

Implements minimal-displacement class-floor enforcement at rank-truncation points
so validated foundation mechanisms cannot be crowded out of evaluation capacity by
high-volume experimental mechanisms (Phase017 seed 249288 failure class).

Design authority: PHASE018_FUNNEL_RESERVATION_SPEC.md (preregistered).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

from aec.config import ENABLED_FOUNDATION_MECHANISMS


class SlotClass(str, Enum):
    """Funnel allocation class. The allocator only ever sees this label."""
    FOUNDATION = "FOUNDATION"
    GENERAL = "GENERAL"


# Preregistered default: quarter-share minority protection.
DEFAULT_RESERVED_FRACTION: float = 0.25


def default_slot_classifier(
    item: Any,
    reserved_mechanisms: FrozenSet[str] = frozenset(ENABLED_FOUNDATION_MECHANISMS),
) -> SlotClass:
    """Classify an opportunity/candidate into a funnel slot class.

    Mechanism-agnostic: membership is tested against a caller-supplied set; no
    family name is hardcoded in the allocation algorithm itself.
    """
    fam = str(
        getattr(item, "mechanism_family", "")
        or getattr(item, "candidate_transformation_family", "")
        or ""
    )
    if fam in reserved_mechanisms:
        return SlotClass.FOUNDATION
    return SlotClass.GENERAL


def reserved_seats_for_k(k: int, fraction: float = DEFAULT_RESERVED_FRACTION) -> int:
    """Number of foundation-reserved seats for a K-slot truncation (preregistered rule)."""
    if k <= 0:
        return 0
    return max(1, int(k * fraction))


@dataclass
class ReservationTelemetry:
    """Observable record of one reservation decision (§11, §29, §30)."""
    site: str = ""
    candidates_before: int = 0
    candidates_after: int = 0
    seats_k: int = 0
    reserved_seats_r: int = 0
    foundation_available: int = 0
    general_available: int = 0
    foundation_selected: int = 0
    general_selected: int = 0
    saved_by_reservation: List[Dict[str, str]] = field(default_factory=list)
    displaced_by_reservation: List[Dict[str, str]] = field(default_factory=list)
    funnel_saturation: bool = False
    foundation_displacement_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site": self.site,
            "before": self.candidates_before,
            "after": self.candidates_after,
            "k": self.seats_k,
            "reserved_r": self.reserved_seats_r,
            "foundation_available": self.foundation_available,
            "general_available": self.general_available,
            "foundation_selected": self.foundation_selected,
            "general_selected": self.general_selected,
            "saved": [dict(s) for s in self.saved_by_reservation],
            "displaced": [dict(d) for d in self.displaced_by_reservation],
            "saturation": self.funnel_saturation,
            "foundation_displacement_rate": round(self.foundation_displacement_rate, 4),
        }


def _item_identity(item: Any) -> Dict[str, str]:
    return {
        "id": str(
            getattr(item, "patch_id", "")
            or getattr(item, "opportunity_id", "")
            or repr(item)
        ),
        "mechanism": str(
            getattr(item, "mechanism_family", "")
            or getattr(item, "candidate_transformation_family", "")
            or ""
        ),
    }


@dataclass
class FunnelReservationPolicy:
    """Declarative reservation policy applied identically at every truncation site."""
    enabled: bool = False
    reserved_fraction: float = DEFAULT_RESERVED_FRACTION
    reserved_mechanisms: FrozenSet[str] = frozenset(ENABLED_FOUNDATION_MECHANISMS)
    last_telemetry: Optional[ReservationTelemetry] = None

    def classifier(self, item: Any) -> SlotClass:
        return default_slot_classifier(item, self.reserved_mechanisms)

    def reserved_seats(self, k: int) -> int:
        return reserved_seats_for_k(k, self.reserved_fraction)


def apply_reservation(
    ranked_items: List[Any],
    k: int,
    policy: FunnelReservationPolicy,
    site: str = "",
) -> Tuple[List[Any], ReservationTelemetry]:
    """Enforce class floors on a pre-ranked list with minimal displacement.

    `ranked_items` must already be sorted by the stage's canonical ranking key
    (best first). Returns (selected, telemetry). Pure and deterministic.
    """
    telemetry = ReservationTelemetry(
        site=site,
        candidates_before=len(ranked_items),
        seats_k=k,
        reserved_seats_r=policy.reserved_seats(k),
        funnel_saturation=len(ranked_items) > k,
    )

    if k <= 0:
        telemetry.candidates_after = 0
        return [], telemetry

    classes = [policy.classifier(it) for it in ranked_items]
    telemetry.foundation_available = sum(1 for c in classes if c == SlotClass.FOUNDATION)
    telemetry.general_available = len(ranked_items) - telemetry.foundation_available

    # No truncation pressure: everything passes through untouched.
    if len(ranked_items) <= k:
        telemetry.candidates_after = len(ranked_items)
        telemetry.foundation_selected = telemetry.foundation_available
        telemetry.general_selected = telemetry.general_available
        return list(ranked_items), telemetry

    r = telemetry.reserved_seats_r
    floor_f = min(telemetry.foundation_available, r)
    floor_g = min(telemetry.general_available, k - r)

    # Pure rank top-K baseline.
    selected_idx: List[int] = list(range(k))
    selected_set = set(selected_idx)

    def count_selected(slot: SlotClass) -> int:
        return sum(1 for i in selected_idx if classes[i] == slot)

    # Enforce foundation floor by displacing lowest-ranked general selections.
    while count_selected(SlotClass.FOUNDATION) < floor_f:
        # Lowest-ranked selected GENERAL item (largest index).
        victim = max((i for i in selected_idx if classes[i] == SlotClass.GENERAL), default=None)
        # Highest-ranked unselected FOUNDATION item (smallest index).
        rescue = min((i for i in range(len(ranked_items))
                      if i not in selected_set and classes[i] == SlotClass.FOUNDATION),
                     default=None)
        if victim is None or rescue is None:
            break
        selected_set.discard(victim)
        selected_set.add(rescue)
        selected_idx = sorted(selected_set)

    # Enforce general floor symmetrically (protects experimental search from
    # being fully swept when foundation supply exceeds K - R... only binds if
    # foundation items dominate the whole top-K).
    while count_selected(SlotClass.GENERAL) < floor_g:
        victim = max((i for i in selected_idx if classes[i] == SlotClass.FOUNDATION), default=None)
        rescue = min((i for i in range(len(ranked_items))
                      if i not in selected_set and classes[i] == SlotClass.GENERAL),
                     default=None)
        if victim is None or rescue is None:
            break
        selected_set.discard(victim)
        selected_set.add(rescue)
        selected_idx = sorted(selected_set)

    pure_top_k = set(range(k))
    for i in sorted(selected_set - pure_top_k):
        telemetry.saved_by_reservation.append({
            **_item_identity(ranked_items[i]),
            "class": classes[i].value,
        })
    for i in sorted(pure_top_k - selected_set):
        telemetry.displaced_by_reservation.append({
            **_item_identity(ranked_items[i]),
            "class": classes[i].value,
        })

    telemetry.foundation_selected = count_selected(SlotClass.FOUNDATION)
    telemetry.general_selected = count_selected(SlotClass.GENERAL)
    telemetry.candidates_after = len(selected_idx)
    if telemetry.foundation_available > 0:
        foundation_missing = telemetry.foundation_available - telemetry.foundation_selected
        telemetry.foundation_displacement_rate = max(0.0, foundation_missing / telemetry.foundation_available)

    return [ranked_items[i] for i in selected_idx], telemetry


__all__ = [
    "SlotClass",
    "DEFAULT_RESERVED_FRACTION",
    "FunnelReservationPolicy",
    "ReservationTelemetry",
    "apply_reservation",
    "default_slot_classifier",
    "reserved_seats_for_k",
]
