# SPDX-License-Identifier: MIT
"""Exact Margin and Economic Accounting for AEC (§14, §23)."""

from __future__ import annotations

from typing import Dict

from aec.config import PRODUCTS
from aec.ir.economic_state import EconomicState


def compute_net_worth(
    cash: float,
    shed: Dict[str, int],
    prices: Dict[str, int]
) -> float:
    """Compute liquid net worth: cash + sum(shed[p] * price[p])."""
    inventory_val = sum(
        int(shed.get(p, 0)) * int(prices.get(p, 1))
        for p in PRODUCTS
    )
    return float(cash) + float(inventory_val)


def compute_terminal_margin(
    our_cash: float,
    opp_cash: float,
    our_shed: Dict[str, int],
    opp_shed_estimate: Dict[str, int],
    prices: Dict[str, int]
) -> float:
    """Compute terminal margin: our net worth minus opponent estimated net worth."""
    our_val = compute_net_worth(our_cash, our_shed, prices)
    opp_val = compute_net_worth(opp_cash, opp_shed_estimate, prices)
    return our_val - opp_val
