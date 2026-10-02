# SPDX-License-Identifier: MIT
"""Evaluate Route 110 branch at T=36 across 16 seeds vs E8_DMITRII."""

from __future__ import annotations
import copy
import os
import sys
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v44_economic_portfolio.main import V44CandidateController
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v32_rlx2.opponents import load_league_opponent

seeds = [
    249635, 249636, 249637, 249638,
    249639, 249640, 249641, 249642,
    249643, 249644, 249645, 249646,
    249647, 249648, 249649, 249650
]

v44_cashes = []
v44_margins = []
r110_cashes = []
r110_margins = []

opp_master = load_league_opponent("E8_DMITRII")

for s in seeds:
    # 1. Baseline V44
    v44 = V44CandidateController()
    sim = FastKagricultureSim(seed=s)
    oc0, oc1 = sim.reset(seed=s)
    opp = copy.deepcopy(opp_master)
    while not sim.done:
        [oc0, oc1], _, _, _ = sim.step([v44.act(oc0), opp(oc1)])
    v_c0 = oc0["farms"][0]["money"]
    v_c1 = oc1["farms"][1]["money"]
    v44_cashes.append(v_c0)
    v44_margins.append(v_c0 - v_c1)

    # 2. V44 + Route 110 branch at T=36
    v44_b = V44CandidateController()
    a7_fn = v44_b.v35.a7_agent._fn
    v3_ns = a7_fn.__globals__["_V3_NS"]
    p_ns = v3_ns["_PARENT_NS"]
    orig_router = p_ns["_router"]
    def adaptive_router(obs, step, st):
        if step >= 36:
            st["route"] = 110
            return 110
        return orig_router(obs, step, st)
    p_ns["_IMPL"].chassis.router = adaptive_router

    sim_b = FastKagricultureSim(seed=s)
    oc0_b, oc1_b = sim_b.reset(seed=s)
    opp_b = copy.deepcopy(opp_master)
    while not sim_b.done:
        [oc0_b, oc1_b], _, _, _ = sim_b.step([v44_b.act(oc0_b), opp_b(oc1_b)])
    p_ns["_IMPL"].chassis.router = orig_router
    b_c0 = oc0_b["farms"][0]["money"]
    b_c1 = oc1_b["farms"][1]["money"]
    r110_cashes.append(b_c0)
    r110_margins.append(b_c0 - b_c1)

print("Across 16 seeds vs E8_DMITRII:")
print(f"V44 Mean Cash:   ${np.mean(v44_cashes):.2f} | Mean Margin: ${np.mean(v44_margins):.2f}")
print(f"R110 Mean Cash:  ${np.mean(r110_cashes):.2f} | Mean Margin: ${np.mean(r110_margins):.2f}")
delta_cash = np.array(r110_cashes) - np.array(v44_cashes)
delta_margin = np.array(r110_margins) - np.array(v44_margins)
print(f"Paired Cash Delta vs V44:   +${np.mean(delta_cash):.2f} (Median: +${np.median(delta_cash):.2f})")
print(f"Paired Margin Delta vs V44: +${np.mean(delta_margin):.2f} (Median: +${np.median(delta_margin):.2f})")
print(f"Per-seed delta cash: {[round(x, 1) for x in delta_cash]}")
