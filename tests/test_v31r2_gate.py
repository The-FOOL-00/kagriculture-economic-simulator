# SPDX-License-Identifier: MIT
"""V31R2 E1: focused gate-behavior tests (no matches, no seeds consumed)."""

import copy

from aec.backbone.v31r2_gate_adapter import BASE, V31R2GateAdapter


def _obs(step, prices):
    return {"step": step, "market": {"prices": dict(prices)}}


def _canned(action):
    g = V31R2GateAdapter(gate_frac=0.5)
    g._v3_agent_callable = lambda obs, cfg=None: copy.deepcopy(action)
    return g


def test_gate_drops_crashed_sell_keeps_recovered():
    g = _canned({"farmer": ["PASS"], "hands": [],
                 "market": [["SELL", "MELON", 100], ["SELL", "WOOL", 50]]})
    # MELON base 250 -> gate 125; WOOL base 200 -> gate 100
    out = g.act(_obs(100, {"MELON": 30, "WOOL": 210}), None)
    assert out["market"] == [["SELL", "WOOL", 50]]
    assert g.gate_drops == 1 and g.gate_keeps == 1


def test_gate_boundary_inclusive():
    g = _canned({"farmer": ["PASS"], "hands": [],
                 "market": [["SELL", "WHEAT", 10]]})
    out = g.act(_obs(50, {"WHEAT": 12.5}), None)  # 25*0.5 exactly
    assert out["market"] == [["SELL", "WHEAT", 10]]


def test_step0_wash_exempt():
    wash = [["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]
    g = _canned({"farmer": ["PASS"], "hands": [], "market": wash})
    out = g.act(_obs(0, {"WHEAT": 1}), None)  # crashed price, still kept + resized
    assert out["market"] == [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
    assert g.step0_rewritten is True


def test_fertilizer_exempt():
    g = _canned({"farmer": ["PASS"], "hands": [],
                 "market": [["SELL", "FERTILIZER", 99], ["SELL", "MILK", 9]]})
    out = g.act(_obs(200, {"FERTILIZER": 1, "MILK": 160}), None)
    assert out["market"] == [["SELL", "FERTILIZER", 99], ["SELL", "MILK", 9]]


def test_non_sell_orders_pass_through():
    mkt = [["BUY_PRODUCT", "WHEAT", 5], ["HIRE"], ["BUY_SEED", "MELON", 2]]
    g = _canned({"farmer": ["PASS"], "hands": [], "market": mkt})
    out = g.act(_obs(10, {"WHEAT": 1}), None)
    assert out["market"] == mkt
    assert g.gate_drops == 0


def test_base_table_matches_engine():
    assert BASE == {"WHEAT": 25, "CARROT": 35, "TOMATO": 60,
                    "STRAWBERRY": 120, "MELON": 250, "EGG": 50,
                    "MILK": 160, "WOOL": 200, "FERTILIZER": 100}


def test_split_truncates_bulk_sell():
    from aec.backbone.v31r2_split_adapter import V31R2SplitAdapter
    s = V31R2SplitAdapter(cap=10)
    s._v3_agent_callable = lambda obs, cfg=None: {
        "farmer": ["PASS"], "hands": [],
        "market": [["SELL", "MELON", 1000], ["SELL", "EGG", 4]]}
    out = s.act({"step": 200, "market": {"prices": {}}}, None)
    assert out["market"] == [["SELL", "MELON", 10], ["SELL", "EGG", 4]]
    assert s.splits == 1


def test_split_step0_exempt():
    from aec.backbone.v31r2_split_adapter import V31R2SplitAdapter
    s = V31R2SplitAdapter(cap=10)
    wash = [["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]
    s._v3_agent_callable = lambda obs, cfg=None: {
        "farmer": ["PASS"], "hands": [], "market": wash}
    out = s.act({"step": 0, "market": {"prices": {}}}, None)
    assert out["market"] == [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]


def test_wash_rewrite_custom():
    from aec.backbone.v31r2_wash_adapter import V31R2WashAdapter, WASHES
    w = V31R2WashAdapter(wash="W2015")
    w._v3_agent_callable = lambda obs, cfg=None: {
        "farmer": ["PASS"], "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]}
    out = w.act({"step": 0, "market": {"prices": {}}}, None)
    assert out["market"] == WASHES["W2015"]
    assert w.step0_rewritten_custom is True


def test_wash_split_compose():
    from aec.backbone.v31r2_wash_adapter import V31R2WashAdapter
    w = V31R2WashAdapter(wash="W72", split_cap=10)
    w._v3_agent_callable = lambda obs, cfg=None: {
        "farmer": ["PASS"], "hands": [], "market": [["SELL", "MILK", 500]]}
    out = w.act({"step": 300, "market": {"prices": {}}}, None)
    assert out["market"] == [["SELL", "MILK", 10]]
