# SPDX-License-Identifier: MIT
"""V27: ledger/first-divergence logic on synthetic trajectories.

Fast unit tests (no engine). Validate divergence classification,
emergence locking, wash P&L, and labor-gap accounting in
scripts/v27_ledger.py.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v27_ledger import (  # noqa: E402
    first_crossing,
    first_persistent_crossing,
    ledger_one,
)


def synth(n=720, money_gap=None, wash_c=None, wash_b=None,
          chore_c_at=(), chore_b_at=()):
    """Two-seat synthetic trajectory record (cand at seat 0)."""
    money_gap = money_gap or (lambda t: 0.0)
    seats = []
    for s in (0, 1):
        sg = 1 if s == 0 else -1
        tiles = {"plant": 10, "dry": 0, "weed": 0, "pasture": 5,
                 "coop": 0, "yield": 0, "cow": 2, "sheep": 2,
                 "goose": 0, "unfed": 0, "wheat": 5, "melon": 1,
                 "strawberry": 1, "carrot": 1, "tomato": 2}
        f_op, h_ops, market = [], [], []
        for t in range(n):
            f_op.append(["WATER"] if (s == 0 and t in chore_c_at) or
                        (s == 1 and t in chore_b_at) else ["PASS"])
            h_ops.append([])
            market.append([])
        if wash_c is not None and s == 0:
            market[0] = wash_c
        if wash_b is not None and s == 1:
            market[0] = wash_b
        seats.append({
            "money": [3000.0 + sg * money_gap(t) / 2.0 for t in range(n)],
            "hands_n": [9] * n,
            "farmer": [[0, 0]] * n,
            "hands": [[[1, 1]]] * n,
            "quads_n": [4] * n,
            "hires": [0] * n,
            "shed": [[0] * 12 for _ in range(n)],
            "seeds": [[0] * 5 for _ in range(n)],
            "tiles": [dict(tiles) for _ in range(n)],
            "f_op": f_op, "h_ops": h_ops, "market": market,
        })
    # post-wash money step 1 (P3 +54 / V3 -54 pattern)
    seats[0]["money"][1] = 3054.0
    seats[1]["money"][1] = 2946.0
    snaps = [{"step": 0, "prices": [25, 60, 90, 120, 200, 40, 160, 150, 30],
              "inventory": [100] * 9}]
    return {"key": "SYN:1:0", "series": "SYN", "seed": 1, "seat": 0,
            "delta": seats[0]["money"][-1] - seats[1]["money"][-1],
            "cand_reward": seats[0]["money"][-1],
            "base_reward": seats[1]["money"][-1],
            "traj": {"n_steps": n, "seats": seats, "market": snaps,
                     "shop_unlocks": []}}


class TestCrossings:
    def test_first_crossing(self):
        assert first_crossing([0, 1, 5, 3], 4) == 2
        assert first_crossing([0, 1, -5, 3], 4) == 2
        assert first_crossing([0, 1, 2], 4) is None

    def test_persistent_crossing_requires_hold(self):
        gap = [0.0] * 720
        gap[100] = 300.0  # transient spike, no hold
        assert first_persistent_crossing(gap, 250, 12) is None
        for t in range(200, 230):
            gap[t] = 300.0
        assert first_persistent_crossing(gap, 250, 12) == 200


class TestLedgerOne:
    def test_opening_and_labor(self):
        rec = synth(wash_c=[["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]],
                    wash_b=[["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]],
                    chore_c_at=tuple(range(10, 22)), chore_b_at=(10,))
        led = ledger_one(rec)
        assert led["opening"]["wash_pnl_c"] == 54.0
        assert led["opening"]["wash_pnl_b"] == -54.0
        assert led["labor_totals"]["chore_c"] == 12
        assert led["labor_totals"]["chore_b"] == 1

    def test_capital_first_and_emergence(self):
        rec = synth(money_gap=lambda t: 0.0 if t < 252 else 400.0)
        led = ledger_one(rec)
        assert led["divergence_primary"] == "CAPITAL"
        assert led["divergence_t"] == 252
        assert led["emergence_t"] == 252

    def test_no_crossing_zero_terminal(self):
        rec = synth()
        led = ledger_one(rec)
        assert led["terminal_delta"] == 0.0
        assert led["divergence_primary"] == "NONE"
        assert led["emergence_t"] is None

    def test_late_growth_is_terminal(self):
        rec = synth(money_gap=lambda t: 0.0 if t < 700 else 600.0)
        led = ledger_one(rec)
        assert led["divergence_primary"] == "TERMINAL"
        assert led["divergence_t"] == 700
