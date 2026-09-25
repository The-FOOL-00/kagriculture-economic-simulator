# SPDX-License-Identifier: MIT
"""R1 oracles (upper bounds, not competitors)."""

from v32.router.labels import hard_target, wl_target


def oracle_cash(row):
    return hard_target(row["cash"])


def oracle_wl(row):
    return wl_target(row["win"], row["cash"])


def oracle_cash_value(row):
    return max(row["cash"])
