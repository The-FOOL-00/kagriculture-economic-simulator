# SPDX-License-Identifier: MIT
"""R1 labels: hard/soft/admissible targets from completed rollout vectors."""

import math

EPS_BAND = 500.0
TEMP_CASH = 2000.0


def admissible_set(cash, band=EPS_BAND):
    """Indices within `band` of max (never invent winners from noise)."""
    m = max(cash)
    return [i for i, c in enumerate(cash) if m - c <= band]


def soft_target(cash, band=EPS_BAND):
    """Uniform over the admissible set (primary TARGET A formulation)."""
    adm = admissible_set(cash, band)
    return [1.0 / len(adm) if i in adm else 0.0 for i in range(len(cash))]


def hard_target(cash):
    """Argmax with fixed tie-break (lowest index). Reported, not primary."""
    m = max(cash)
    return next(i for i, c in enumerate(cash) if c == m)


def preference_target(cash, temp=TEMP_CASH):
    """TARGET C: softmax over cash (robust: demeaned, fixed temperature)."""
    mu = sum(cash) / len(cash)
    ex = [math.exp((c - mu) / temp) for c in cash]
    s = sum(ex)
    return [e / s for e in ex]


def wl_target(win, cash):
    """TARGET B: best win-score, tie-break by cash, then lowest index."""
    best = max(range(len(win)), key=lambda i: (win[i], cash[i], -i))
    return best
