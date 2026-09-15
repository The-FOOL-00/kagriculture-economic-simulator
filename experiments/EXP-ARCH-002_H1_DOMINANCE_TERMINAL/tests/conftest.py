# SPDX-License-Identifier: MIT
"""Shared fixtures for the ARCH-002 H1 validation battery.

All synthetic observations are hand-constructed (no game seeds, no
engine execution) unless a test explicitly uses the port (Q1/Q2).
"""

import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
H1_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(H1_DIR, "..", ".."))
if H1_DIR not in sys.path:
    sys.path.insert(0, H1_DIR)

PRODUCTS_9 = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)
BASE_PRICES = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60,
               "STRAWBERRY": 120, "MELON": 250, "EGG": 50,
               "MILK": 160, "WOOL": 200, "FERTILIZER": 100}


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def h1_dir():
    return H1_DIR


@pytest.fixture()
def full_config():
    return {"boardSize": 10, "turnsPerDay": 24, "episodeSteps": 720,
            "shedCapacity": 100, "maxMarketOrdersPerTurn": 10,
            "townShopSellInterval": 4, "townCenterSellInterval": 24}


def _blank_farm(money=9000.0, hands=((-1, -1),)):
    return {"money": float(money),
            "tiles": [[None] * 10 for _ in range(10)],
            "farmer": [4, 4],
            "hands": [list(h) for h in hands],
            "unlocked_quadrants": [],
            "hires_today": 0}


def _blank_private(n_units=3, shed=None, inventories=None):
    return {"shed": dict(shed or {}),
            "seeds": {},
            "inventories": [dict(i) for i in
                            (inventories or [{}] * n_units)]}


def make_obs(step, seat=0, money=9000.0, shops=(), hands=((4, 5), (5, 4)),
             tiles=(), shed=None, inventories=None,
             market_inventory=None, prices=None, opp_money=9000.0):
    """Hand-built coherent obs (no seeds, no engine)."""
    farm = _blank_farm(money=money, hands=hands)
    for (x, y, tile) in tiles:
        farm["tiles"][y][x] = copy.deepcopy(tile)
    n = 1 + len(farm["hands"])
    private = _blank_private(n_units=n, shed=shed,
                             inventories=inventories)
    opp = _blank_farm(money=opp_money, hands=hands)
    farms = [farm, opp] if seat == 0 else [opp, farm]
    inv = {p: 10000 for p in PRODUCTS_9}
    inv.update(market_inventory or {})
    prc = dict(BASE_PRICES)
    prc.update(prices or {})
    return {"remainingOverageTime": 60, "step": int(step),
            "player": int(seat), "farms": farms,
            "market": {"inventory": inv, "prices": prc},
            "town": {"unlocked_shops": list(shops)},
            "day": int(step) // 24, "hour": int(step) % 24,
            "private": private}


def wheat_tile(planted_day=20, yield_units=3):
    return {"kind": "PLANT", "crop": "WHEAT", "planted_day": planted_day,
            "watered_today": False, "consecutive_unwatered": 1,
            "yield_units": yield_units, "max_lifespan_step": -1,
            "fertilized_until_day": -1}


def cow_tile(yield_units=2, fertilizer=True):
    return {"kind": "PASTURE", "animal": "COW", "placed_day": 10,
            "yield_units": yield_units, "consecutive_unfed": 0,
            "fed_today": False, "cared_today": False,
            "fertilizer_available": bool(fertilizer),
            "pending_care_bonus": 0}


@pytest.fixture()
def fresh_baseline():
    from h1_baseline import load_baseline
    return load_baseline()


@pytest.fixture()
def overlay(fresh_baseline):
    from h1_agent import H1Overlay
    return H1Overlay(fresh_baseline)
