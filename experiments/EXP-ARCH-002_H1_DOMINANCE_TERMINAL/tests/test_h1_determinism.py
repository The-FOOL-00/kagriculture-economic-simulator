# SPDX-License-Identifier: MIT
"""Determinism battery (prereg §12/P-DET).

Double-run bit-identity (in-process) plus cross-process identity under
varying PYTHONHASHSEED (catches set/dict iteration-order dependence).
"""

import hashlib
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
H1_DIR = os.path.dirname(HERE)

PLAN_PROBE = r"""
import copy, hashlib, json, sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from conftest import make_obs, wheat_tile, cow_tile
from h1_baseline import load_baseline
from h1_agent import H1Overlay
fb = load_baseline()
cfg = {"boardSize": 10, "turnsPerDay": 24, "episodeSteps": 720,
       "shedCapacity": 100, "maxMarketOrdersPerTurn": 10,
       "townShopSellInterval": 4, "townCenterSellInterval": 24}
tiles = [(x, y, wheat_tile(yield_units=6)) for x in (2, 7)
         for y in (2, 7)] + [(5, 5, cow_tile())]
obs = make_obs(712, hands=tuple((x, 1) for x in range(6)),
               tiles=tiles, shed={"WHEAT": 12, "MILK": 4})
ov = H1Overlay(fb)
out = ov.act(copy.deepcopy(obs), copy.deepcopy(cfg))
rec = dict(ov.open_records.get(0)); rec.pop("planning_ms", None)
plan = ov.plans.get(0)
blob = {"out": out, "rec": rec,
        "actions": plan["actions"] if plan else None,
        "states": plan["expected_states"] if plan else None}
print(hashlib.sha256(json.dumps(
    blob, sort_keys=True, default=str).encode()).hexdigest())
print(rec["reason"], rec.get("simulations"))
"""


def _probe_digest(pythonhashseed):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(pythonhashseed)
    proc = subprocess.run(
        [sys.executable, "-c", PLAN_PROBE, H1_DIR, HERE],
        capture_output=True, text=True, env=env, cwd=HERE,
        stdin=subprocess.DEVNULL, timeout=300)
    assert proc.returncode == 0, proc.stderr[-2000:]
    lines = proc.stdout.strip().splitlines()
    return lines[0], lines[1]


@pytest.mark.parametrize("seed", ["0", "1", "42"])
def test_hashseed_determinism(seed):
    digest, summary = _probe_digest(seed)
    ref_digest, ref_summary = _probe_digest("12345")
    assert summary == ref_summary
    assert digest == ref_digest


def test_value_term_integer_exact():
    from h1_dominance import stock_value
    run = {"sold": {"WHEAT": 10**6}, "private": {"shed": {"MILK": 7}}}
    prices = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60,
              "STRAWBERRY": 120, "MELON": 250, "EGG": 50,
              "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
    value = stock_value(run, prices)
    assert type(value) is int
    assert value == 10**6 * 25 + 7 * 160


def test_entry_prices_integerized():
    from h1_dominance import entry_prices
    obs = {"market": {"prices": {"WHEAT": 25.9}}}
    prices = entry_prices(obs)
    assert prices["WHEAT"] == 25
    assert all(type(v) is int and v >= 1 for v in prices.values())
    assert len(prices) == 9
