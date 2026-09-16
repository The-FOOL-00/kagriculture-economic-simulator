# SPDX-License-Identifier: MIT
"""ARCH-003 H1 telemetry: frozen reason enum + per-game record schema.

Prereg §10.3 freezes the 15-code enum (no code may be added, split, or
redefined after execution begins).  Prereg §24.2/U-SEL requires the
structured sub-field schema to be frozen at implementation freeze.
"""

from __future__ import annotations

# --- Frozen 15-code reason enum (prereg §10.3, in prereg order) ------------
REASONS = (
    "OK_ACTIVATED",
    "ABSTAIN_CONFIG",
    "ABSTAIN_SHED",
    "ABSTAIN_ITEMS",
    "ABSTAIN_WINDOW_OPS",
    "ABSTAIN_MARKET_OP",
    "ABSTAIN_BUY_COVERAGE",
    "ABSTAIN_HANDSHAKE",
    "ABSTAIN_BUDGET",
    "ABSTAIN_NO_GAIN",
    "ABSTAIN_DOMINANCE",
    "ABSTAIN_NOSTEAL",
    "ABSTAIN_ACCEPT",
    "ABANDON_MISMATCH_T",
    "ABANDON_NONCONSECUTIVE",
)
REASON_SET = frozenset(REASONS)

GUARD_REASONS = {
    "G0": "ABSTAIN_CONFIG",
    "G1": "ABSTAIN_SHED",
    "G2": "ABSTAIN_ITEMS",
    "G3": "ABSTAIN_WINDOW_OPS",
    "G4": "ABSTAIN_BUY_COVERAGE",
    "G5": "ABSTAIN_HANDSHAKE",
    "G6": "ABSTAIN_BUDGET",
    "G7": "ABSTAIN_NO_GAIN",
}

ADOPT_REASONS = {
    "no_gain": "ABSTAIN_NO_GAIN",
    "dominance": "ABSTAIN_DOMINANCE",
    "nosteal": "ABSTAIN_NOSTEAL",
    "accept": "ABSTAIN_ACCEPT",
}

# --- Frozen sub-field schema (U-SEL; enum-stable, fixed keys) --------------
RECORD_KEYS = (
    "reason",            # one of REASONS
    "seat",              # 0/1
    "step_E",            # 712 when planning ran, else None
    "route",             # live route name at E ('backbone'/'yarn'/'bakery')
    "simulations",       # trial sims executed (<=128), None if no planning
    "planning_ms",       # wall ms for planning (telemetry only, non-gating)
    "changed_workers",   # sorted actor indices with adopted proposals
    "sold_unit_delta",   # {product: int} final vs baseline (activated only)
    "money_delta",       # float candidate_money - baseline_money (activated only)
    "stock_value_gain",  # int, frozen entry prices (activated only)
    "candidate_overflow",  # int overflow units of adopted plan
    "baseline_overflow",   # int overflow units of shadow baseline run
    "markets_verbatim",    # bool certificate 712–717 (planned vs shadow)
    "market_718_liquidation",  # candidate liquidation market orders at 718
    "buy_units_U",         # int window BUY units in shadow baseline markets
    "money_at_E",          # float own money at E
    "fertilizer_reaped",   # int fertilizer units acquired by adopted plan
    "fertilizer_baseline",  # int fertilizer units in shadow baseline run
    "subcause",            # structured failure detail (dict, schema below)
    "abandon_step",        # int t for ABANDON_MISMATCH_T, else None
    "shadow_only",         # bool harness flag (frozen treatment: False)
)

# Sub-cause schemas per reason (fixed keys; values JSON-scalars/lists).
SUBCAUSE_SCHEMA = {
    "ABSTAIN_CONFIG": ("pin", "expected", "observed"),
    "ABSTAIN_SHED": ("detail",),
    "ABSTAIN_ITEMS": ("detail",),
    "ABSTAIN_WINDOW_OPS": ("step", "op"),
    "ABSTAIN_MARKET_OP": ("step", "order"),
    "ABSTAIN_BUY_COVERAGE": ("U", "money_at_E", "required"),
    "ABSTAIN_HANDSHAKE": ("field",),
    "ABSTAIN_BUDGET": ("simulations",),
    "ABSTAIN_NO_GAIN": ("trials_evaluated",),
    "ABSTAIN_DOMINANCE": ("stage",),   # 'trial' | 'final_resim'
    "ABSTAIN_NOSTEAL": ("stage",),     # 'trial'
    "ABSTAIN_ACCEPT": (
        "worker_change", "money_gain", "money_delta", "sold_delta_min",
        "sold_delta_max", "markets_verbatim", "zero_overflow",
    ),
    "ABANDON_MISMATCH_T": ("step", "physical_match", "baseline_action_match"),
    "ABANDON_NONCONSECUTIVE": ("step", "previous"),
    "OK_ACTIVATED": (),
}


def blank_record(seat, shadow_only=False):
    """Fresh per-game record with all keys present."""
    rec = {key: None for key in RECORD_KEYS}
    rec["seat"] = int(seat)
    rec["shadow_only"] = bool(shadow_only)
    rec["subcause"] = {}
    rec["changed_workers"] = []
    return rec


def check_reason(reason):
    if reason not in REASON_SET:
        raise ValueError("unknown H1 reason code: %r" % (reason,))
    return reason


class H1Abstain(Exception):
    """Fail-safe abstention signal: abandon H1, emit the baseline action.

    Carries the frozen reason code + frozen-schema sub-cause.  Raised by
    guards, the shadow simulator, and the search/selection loop; caught
    exactly once by the wrapper, which then emits the live baseline
    action verbatim.  Never caught and retried inside planning.
    """

    def __init__(self, reason, subcause=None):
        super().__init__(reason)
        self.reason = check_reason(reason)
        self.subcause = dict(subcause or {})
