# SPDX-License-Identifier: MIT
"""V32 P7 state-derived macro-phase detector (H2, gated).

Deterministic function of CURRENT OBSERVABLE STATE ONLY. Uses physical /
economic fields of ess (hands, shed, carried inventory, tile histogram). Uses
NO step index, NO day/hour clock, NO teacher tape, NO seed ID, NO future
knowledge. Same ess -> same phase, always (covered by tests/test_v32_p7.py).

Phases (indices stable for the phase):
  0 OPENING_CAPITAL: no hired hands yet (pre-workforce).
  1 WORKFORCE_SETUP: hands hired but no livestock secured (shed + carried).
  2 LIVESTOCK_SETUP: livestock secured but no pasture/coop structures yet.
  3 PRODUCTION_SETUP: structures exist but no stocked animals on tiles yet.
  4 ECONOMIC_CONTINUATION: stocked animals present (or any later state).
"""

ANIMALS = ("COW", "SHEEP", "GOOSE")

PHASES = (
    "OPENING_CAPITAL",
    "WORKFORCE_SETUP",
    "LIVESTOCK_SETUP",
    "PRODUCTION_SETUP",
    "ECONOMIC_CONTINUATION",
)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _animals_total(ess):
    """All secured livestock: shed + carried + stocked on tiles (thist[8]).

    Stocked tile animals must count: once placed into pastures they leave shed
    and carried inventories but remain secured productive livestock. Without
    this term the detector regresses to WORKFORCE_SETUP mid-production.
    """
    shed = ess.get("shed", {}) or {}
    tot = sum(_f(shed.get(k, 0)) for k in ANIMALS)
    for inv in (ess.get("inv", []) or []):
        if isinstance(inv, dict):
            tot += sum(_f(inv.get(k, 0)) for k in ANIMALS)
    th = list(ess.get("thist", [0] * 10) or [0] * 10)
    if len(th) > 8:
        tot += _f(th[8])
    return tot


def detect_phase(ess):
    """Current macro phase index from observable state only."""
    hands = ess.get("hands", []) or []
    if len(hands) == 0:
        return 0
    if _animals_total(ess) <= 0:
        return 1
    th = list(ess.get("thist", [0] * 10) or [0] * 10)
    past = _f(th[5]) if len(th) > 5 else 0.0
    coop = _f(th[7]) if len(th) > 7 else 0.0
    stocked = _f(th[8]) if len(th) > 8 else 0.0
    if past + coop <= 0:
        return 2
    if stocked <= 0:
        return 3
    return 4


def phase_name(ess):
    return PHASES[detect_phase(ess)]
