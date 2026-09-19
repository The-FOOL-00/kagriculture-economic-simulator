# SPDX-License-Identifier: MIT
"""Unit and diagnostic tests for Phase 014 State Profiler and Oracle Probe."""

import pytest
from aec.audit.state_profiler import StateProfiler, StateClassification
from aec.audit.oracle_probe import BoundedOracleProbe, OracleCategory, OracleProbeResult
from aec.ir.economic_state import build_economic_state
from aec.config import AECConfig
from aec.integration.executor import AECExecutor
import kagsim


def test_state_profiler_taxonomy():
    profiler = StateProfiler()
    game = kagsim.Game(249241)
    obs = game.observe(0)
    econ_state = build_economic_state(obs)
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}

    sc = profiler.classify_turn(econ_state, baseline_action)
    assert isinstance(sc, StateClassification)
    assert sc.worker_state in ("productive", "traveling", "idle", "carrying", "blocked", "reconnecting")
    assert sc.farm_state in ("cash-rich", "cash-constrained", "seed-constrained", "feed-constrained", "shed-constrained", "terminal-constrained", "resource-constrained", "normal")
    assert sc.market_state in ("normal", "favorable", "unfavorable", "opportunity_window", "saturation_risk", "liquidity-sensitive")
    assert sc.terminal_state in ("far_from_terminal", "terminal_runway_sufficient", "terminal_runway_tight", "liquidation_phase", "shutdown_phase")


def test_bounded_oracle_probe_execution():
    probe = BoundedOracleProbe()
    game = kagsim.Game(249241)
    obs = game.observe(0)
    econ_state = build_economic_state(obs)
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}

    res = probe.probe_state(econ_state, baseline_action, horizon=6)
    assert isinstance(res, OracleProbeResult)
    assert res.alternatives_evaluated >= 1
    assert res.category in OracleCategory
    assert isinstance(res.local_headroom, float)


def test_interesting_state_indicators_detection():
    profiler = StateProfiler()
    game = kagsim.Game(249241)
    obs = game.observe(0)
    # Inject a mature crop near worker
    obs["farms"][0]["tiles"][4][3] = {
        "tilled": True,
        "crop": {"type": "STRAWBERRY", "age": 10, "mature": True}
    }
    econ_state = build_economic_state(obs)
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}

    sc = profiler.classify_turn(econ_state, baseline_action)
    assert sc.is_interesting is True
    assert "IDLE_WORKER_MATURE_CROP" in sc.triggered_indicators
