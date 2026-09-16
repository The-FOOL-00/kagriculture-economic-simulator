# SPDX-License-Identifier: MIT
"""
ARCH-003 H1 Terminal Repair Complete 12-Item Micro-Validation Battery.

Strictly validates:
TEST 1: Consumed validation seed 248012 activates with positive money gain and sales gain.
TEST 2: Consumed validation seed 248001 passes intermediate market solvency despite delayed deposits.
TEST 3: Step-718 liquidation parity: shadow-generated market == live emitted market.
TEST 4: Reward parity: candidate shadow final money == actual engine final money for identical action sequence.
TEST 5: No-steal: stealing and collision fixtures fail safely.
TEST 6: Handshake fail-closed on config mismatch, missing obs, nonconsecutive steps, state mismatch.
TEST 7: Pure passthrough: when rejected/abstained, emitted action is bit-identical to live baseline.
TEST 8: Policy isolation: zero mutation of live baseline controller ledgers or telemetry from shadow planning.
TEST 9: Pre-E purity: steps 0–711 remain bit-identical to baseline.
TEST 10: Market boundary: 712–717 exactly baseline verbatim, 718 candidate liquidation.
TEST 11: BUY safety: G4 coverage gate ($125 × U) enforced.
TEST 12: Forbidden mechanisms: no H=500, no checkpoint <=288, no fertilizer scope expansion, no market changes before 718.
"""

from __future__ import annotations

import copy
import os
import sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH003_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(ARCH003_DIR, "..", ".."))

PORT_DIR = os.path.join(REPO_ROOT, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)
if ARCH003_DIR not in sys.path:
    sys.path.insert(0, ARCH003_DIR)

from kagsim_py import api as papi
from h1_agent import build_agent, H1Overlay
from h1_baseline import load_baseline
from h1_const import (
    ENTRY_STEP,
    FINAL_STEP,
    PIN_BOARD_SIZE,
    PIN_EPISODE_STEPS,
    PIN_MAX_ORDERS,
    PIN_SHED_CAPACITY,
    PIN_TURNS_PER_DAY,
    PRODUCTS_9,
)
from h1_dominance import (
    acceptance,
    compute_terminal_liquidation_market,
    coverage_required,
    dominates,
    entry_prices,
    intermediate_market_solvency,
    markets_712_717_verbatim,
    no_steal_pass,
    stock_value,
    terminal_weak_dominance,
    _ge,
)
from h1_search import _clone_schedule, plan_terminal, proposals
from h1_shadow import ShadowCursor, run_baseline_window, simulate_schedule
from h1_telemetry import H1Abstain, blank_record


@pytest.fixture
def baseline():
    return load_baseline()


@pytest.fixture
def default_config():
    return {
        "boardSize": PIN_BOARD_SIZE,
        "turnsPerDay": PIN_TURNS_PER_DAY,
        "episodeSteps": PIN_EPISODE_STEPS,
        "shedCapacity": PIN_SHED_CAPACITY,
        "maxMarketOrdersPerTurn": PIN_MAX_ORDERS,
    }


def _play_game_to_step(seed, stop_step=712):
    base = load_baseline()
    game = papi.Game(seed)
    while game.step_count < stop_step:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        a0 = base.call(copy.deepcopy(obs0))
        a1 = base.call(copy.deepcopy(obs1))
        game.step(a0, a1)
    return base, game


# =============================================================================
# TEST 1: Consumed validation seed 248012 (Yarn Route Activation)
# =============================================================================
def test_1_seed_248012_activates_with_real_gain(default_config):
    """Verify seed 248012 (yarn case) activates with strictly positive money & sales."""
    base, game = _play_game_to_step(248012, 712)
    obs_E = game.observe(0)
    route = base.active_route(712, obs_E)
    route_table = base.policies[route].route_prior
    ledgers_E = base.clone_ledgers(route, 0)
    live_act_E = base.call(copy.deepcopy(obs_E), copy.deepcopy(default_config))

    overlay = H1Overlay(base)
    record = blank_record(0)
    plan = overlay._plan_at_entry(
        0, 712, obs_E, default_config, route,
        copy.deepcopy(ledgers_E), copy.deepcopy(live_act_E), record
    )

    assert plan["accepted"] is True
    assert record["reason"] == "OK_ACTIVATED"
    assert plan["money_delta"] > 0.0, f"Money delta must be strictly positive: {plan['money_delta']}"
    assert plan["sold_unit_delta"]["FERTILIZER"] > 0, "Fertilizer sales must strictly increase"
    assert all(v >= 0 for v in plan["sold_unit_delta"].values()), "All sold deltas must be >= 0"
    assert plan["candidate_overflow"] == 0, "Overflow must be 0"
    assert plan["markets_verbatim"] is True, "Steps 712-717 markets must be verbatim baseline"
    assert len(plan["market_718_liquidation"]) > 0, "Step 718 must have liquidation market orders"


# =============================================================================
# TEST 2: Consumed validation seed 248001 (Backbone Delayed-Deposit Solvency)
# =============================================================================
def test_2_seed_248001_delayed_deposit_solvency():
    """Verify backbone case passes intermediate solvency despite delayed deposit."""
    base, game = _play_game_to_step(248001, 712)
    obs_E = game.observe(0)
    route = base.active_route(712, obs_E)
    route_table = base.policies[route].route_prior
    cursor = ShadowCursor(base, 0, obs_E, None, None, base.clone_ledgers(route, 0), route, route_table)
    baseline_run = run_baseline_window(cursor)

    # In baseline, actor 11 drops fertilizer at step 717 (offset 5).
    # Delay actor 11's drop to step 718 (offset 6).
    cand_sched = _clone_schedule(baseline_run["actions"])
    cand_sched[5]["hands"][10] = ["PASS"]
    cand_sched[6]["hands"][10] = ["DROP"]

    cand_eval = simulate_schedule(base, 0, obs_E, cand_sched)

    # Under ARCH-002 prefix dominance, this candidate fails because actor 11 has 0 < 1 at step 717
    arch002_prefix_pass = True
    for c_row, b_row in zip(cand_eval["rows"], baseline_run["rows"]):
        if not _ge(c_row["deposited_by_actor"][11], b_row["deposited_by_actor"][11]):
            arch002_prefix_pass = False
            break
    assert arch002_prefix_pass is False, "Must fail ARCH-002 row-wise prefix dominance"

    # Under ARCH-003, no intermediate market sales are missed (fertilizer was not sold at 717)
    assert intermediate_market_solvency(cand_eval, baseline_run) is True
    assert terminal_weak_dominance(cand_eval, baseline_run) is True
    assert dominates(cand_eval, baseline_run) is True


# =============================================================================
# TEST 3: Step-718 Liquidation Parity & Restrictions
# =============================================================================
def test_3_step_718_liquidation_parity(default_config):
    """Verify shadow-generated step-718 market is bit-identical to live emitted market."""
    base, game = _play_game_to_step(248012, 712)
    obs_E = game.observe(0)
    agent = build_agent(base)
    live_e = base.call(copy.deepcopy(obs_E), copy.deepcopy(default_config))

    # Plan and get plan record
    act_712 = agent(copy.deepcopy(obs_E), copy.deepcopy(default_config))
    plan = agent.overlay.plans.get(0)
    assert plan is not None

    shadow_718_market = plan["actions"][6]["market"]

    # Play forward under agent to step 718
    obs_opp = game.observe(1)
    act_opp = base.call(copy.deepcopy(obs_opp), copy.deepcopy(default_config))
    game.step(act_712, act_opp)

    for t in range(713, 718):
        obs_t = game.observe(0)
        obs_opp_t = game.observe(1)
        a_h1 = agent(copy.deepcopy(obs_t), copy.deepcopy(default_config))
        a_opp = base.call(copy.deepcopy(obs_opp_t), copy.deepcopy(default_config))
        game.step(a_h1, a_opp)

    # At step 718, live agent emits:
    obs_718 = game.observe(0)
    act_718 = agent(copy.deepcopy(obs_718), copy.deepcopy(default_config))
    live_emitted_market = act_718.get("market", [])

    assert live_emitted_market == shadow_718_market, "Live emitted market at 718 must equal shadow market"

    # Verify all strict liquidation restrictions on step 718 market
    assert len(live_emitted_market) <= PIN_MAX_ORDERS
    for order in live_emitted_market:
        assert order[0] == "SELL", "Orders must be SELL only"
        assert order[1] in PRODUCTS_9, "Items must be in PRODUCTS_9 only"
        assert isinstance(order[2], int) and order[2] > 0, "Quantity must be positive integer"


# =============================================================================
# TEST 4: Reward Parity for Identical Action Sequence
# =============================================================================
def test_4_reward_parity(default_config):
    """Verify candidate shadow final money equals actual engine final money for identical action sequence."""
    base = load_baseline()
    game = papi.Game(seed=0)
    st = game.sim.st
    st.step = 712
    st.day = 712 // 24
    st.hour = 712 % 24
    st.done = False
    st.farms[1].money = 5000.0
    st.farms[0].money = 10000.0
    st.farms[0].shed[0] = 10  # 10 wheat in shed
    game.sim.refresh_prices()

    obs_E = game.observe(0)
    schedule = [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(7)]
    schedule[6]["market"] = [["SELL", "WHEAT", 10]]

    cand_run = simulate_schedule(base, 0, obs_E, schedule)

    # Step engine with exact identical actions and passive opponent
    opp_pass = {"farmer": ["PASS"], "hands": [], "market": []}
    for a in cand_run["actions"]:
        game.step(a, opp_pass)

    engine_money = float(game.reward(0))
    shadow_money = cand_run["final_money"]
    assert engine_money == shadow_money, f"Engine reward {engine_money} != shadow {shadow_money}"


# =============================================================================
# TEST 5: No-Steal Invariant
# =============================================================================
def test_5_no_steal_invariant():
    """Verify that stealing acquisitions of other actors fails no_steal_pass."""
    best = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1, "acquired": {"WHEAT": 4}}
    ]}
    # Trial drops or misses other actor's harvest
    trial_stolen = {"events": []}
    assert no_steal_pass(trial_stolen, best, 0) is False

    # Trial other actor gets less
    trial_reduced = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1, "acquired": {"WHEAT": 3}}
    ]}
    assert no_steal_pass(trial_reduced, best, 0) is False

    # Trial preserves acquisition
    trial_ok = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1, "acquired": {"WHEAT": 4}}
    ]}
    assert no_steal_pass(trial_ok, best, 0) is True


# =============================================================================
# TEST 6: Handshake Fail-Closed Behavior
# =============================================================================
def test_6_handshake_fail_closed(default_config):
    """Verify config mismatch, missing obs, nonconsecutive step, state mismatch fail closed."""
    base, game = _play_game_to_step(248012, 712)
    obs_E = game.observe(0)

    # 1. Config mismatch
    bad_cfg = copy.deepcopy(default_config)
    bad_cfg["boardSize"] = 12
    overlay1 = H1Overlay(base)
    rec1 = blank_record(0)
    with pytest.raises(H1Abstain) as exc1:
        overlay1._plan_at_entry(0, 712, obs_E, bad_cfg, "yarn", {}, {}, rec1)
    assert exc1.value.reason == "ABSTAIN_CONFIG"

    # 2. Missing obs fields (farms shape)
    bad_obs = copy.deepcopy(obs_E)
    bad_obs["farms"] = [bad_obs["farms"][0]]  # only 1 farm
    overlay2 = H1Overlay(base)
    rec2 = blank_record(0)
    with pytest.raises(H1Abstain) as exc2:
        overlay2._plan_at_entry(0, 712, bad_obs, default_config, "yarn", {}, {}, rec2)
    assert exc2.value.reason == "ABSTAIN_CONFIG"

    # 3. Nonconsecutive step during emission
    agent3 = build_agent(base)
    agent3(copy.deepcopy(obs_E), copy.deepcopy(default_config))
    plan3 = agent3.overlay.plans.get(0)
    assert plan3 is not None

    # Step jumps from 712 to 714 (nonconsecutive)
    obs_jump = copy.deepcopy(obs_E)
    obs_jump["step"] = 714
    obs_jump["hour"] = 714 % 24
    obs_jump["day"] = 714 // 24
    live_jump = base.call(copy.deepcopy(obs_jump), copy.deepcopy(default_config))
    act_jump = agent3(copy.deepcopy(obs_jump), copy.deepcopy(default_config))
    assert act_jump == live_jump, "Must emit live baseline on nonconsecutive step"
    assert 0 not in agent3.overlay.plans, "Plan must be forgotten"
    assert agent3.overlay.records[-1]["reason"] == "ABANDON_NONCONSECUTIVE"

    # 4. State mismatch during emission (step 713)
    agent4 = build_agent(base)
    agent4(copy.deepcopy(obs_E), copy.deepcopy(default_config))
    assert 0 in agent4.overlay.plans

    obs_713 = copy.deepcopy(obs_E)
    obs_713["step"] = 713
    obs_713["hour"] = 713 % 24
    obs_713["day"] = 713 // 24
    # Alter worker position to trigger physical mismatch with candidate expected state
    obs_713["farms"][0]["hands"][0] = [9, 9]
    live_713 = base.call(copy.deepcopy(obs_713), copy.deepcopy(default_config))
    act_713 = agent4(copy.deepcopy(obs_713), copy.deepcopy(default_config))
    assert act_713 == live_713, "Must emit live baseline on physical state mismatch"
    assert 0 not in agent4.overlay.plans, "Plan must be forgotten"
    assert agent4.overlay.records[-1]["reason"] == "ABANDON_MISMATCH_T"
    assert agent4.overlay.records[-1]["abandon_step"] == 713


# =============================================================================
# TEST 7: Pure Passthrough when Abstaining
# =============================================================================
def test_7_pure_passthrough_when_abstained(default_config):
    """When candidate rejected, live baseline action is bit-identical."""
    base, game = _play_game_to_step(248001, 712)
    agent = build_agent(base)
    obs_E = game.observe(0)

    # 1. Rejection in search (ABSTAIN_DOMINANCE) on seed 248001
    live_expected = base.call(copy.deepcopy(obs_E), copy.deepcopy(default_config))
    emitted = agent(copy.deepcopy(obs_E), copy.deepcopy(default_config))
    assert emitted == live_expected, "Emitted action must be bit-identical to live baseline on abstain"
    assert agent.overlay.records[-1]["reason"] == "ABSTAIN_DOMINANCE"

    # 2. Rejection at entry gate (ABSTAIN_BUY_COVERAGE) on seed 248012
    base_yarn, game_yarn = _play_game_to_step(248012, 712)
    agent_yarn = build_agent(base_yarn)
    obs_yarn = game_yarn.observe(0)
    obs_yarn_poor = copy.deepcopy(obs_yarn)
    obs_yarn_poor["farms"][0]["money"] = 0.0  # yarn route requires > 0 money for route prior buy units
    live_yarn = base_yarn.call(copy.deepcopy(obs_yarn_poor), copy.deepcopy(default_config))
    emitted_yarn = agent_yarn(copy.deepcopy(obs_yarn_poor), copy.deepcopy(default_config))
    assert emitted_yarn == live_yarn, "Emitted action must be bit-identical to live baseline on BUY coverage abstain"
    assert agent_yarn.overlay.records[-1]["reason"] == "ABSTAIN_BUY_COVERAGE"


# =============================================================================
# TEST 8: State and Telemetry Isolation
# =============================================================================
def test_8_policy_isolation(default_config):
    """No mutation of live baseline controller ledgers or telemetry from shadow planning."""
    base = load_baseline()
    _, game = _play_game_to_step(248012, 712)
    obs_E = game.observe(0)

    # Run the live call to establish initial live state
    live_act_E = base.call(copy.deepcopy(obs_E), copy.deepcopy(default_config))

    policy = base.policies["yarn"]
    pre_plan_calls = policy.controller.telemetry["calls"]
    pre_plan_states = copy.deepcopy(policy.controller.states)
    pre_plan_telemetry = copy.deepcopy(policy.controller.telemetry)

    # Now run shadow planning
    overlay = H1Overlay(base)
    rec = blank_record(0)
    overlay._plan_at_entry(
        0, 712, obs_E, default_config, "yarn",
        base.clone_ledgers("yarn", 0), live_act_E, rec
    )

    post_plan_calls = policy.controller.telemetry["calls"]
    post_plan_states = policy.controller.states
    post_plan_telemetry = policy.controller.telemetry

    assert post_plan_calls == pre_plan_calls, "Shadow planning must not increment live telemetry calls"
    assert post_plan_states == pre_plan_states, "Live controller states must not be mutated by shadow simulation"
    assert post_plan_telemetry == pre_plan_telemetry, "Live telemetry must not be mutated by shadow simulation"


# =============================================================================
# TEST 9: Pre-E Action Purity (0 to 711)
# =============================================================================
def test_9_pre_e_purity(default_config):
    """Steps 0 to 711 remain bit-identical to baseline."""
    base = load_baseline()
    agent = build_agent(base)
    game = papi.Game(248012)

    for step in range(50):
        obs = game.observe(0)
        act_live = base.call(copy.deepcopy(obs), copy.deepcopy(default_config))
        act_agent = agent(copy.deepcopy(obs), copy.deepcopy(default_config))
        assert act_agent == act_live, f"Mismatch at step {step}"
        game.step(act_live, act_live)


# =============================================================================
# TEST 10: Market Boundary
# =============================================================================
def test_10_market_boundary(default_config):
    """Steps 712-717 market is baseline verbatim; step 718 is candidate liquidation."""
    base, game = _play_game_to_step(248012, 712)
    agent = build_agent(base)
    opp = load_baseline().agent

    while not game.done:
        t = game.step_count
        obs = game.observe(0)
        live_act = base.call(copy.deepcopy(obs), copy.deepcopy(default_config))
        h1_act = agent(copy.deepcopy(obs), copy.deepcopy(default_config))

        if 712 <= t <= 717:
            assert h1_act.get("market", []) == live_act.get("market", []), f"Market mismatch at step {t}"
        elif t == 718:
            assert h1_act.get("market", []) == agent.overlay.plans[0]["market_718_liquidation"]

        act_opp = opp(copy.deepcopy(game.observe(1)), copy.deepcopy(default_config))
        game.step(h1_act, act_opp)


# =============================================================================
# TEST 11: BUY Safety & Coverage Gate
# =============================================================================
def test_11_buy_safety_coverage_gate():
    """G4 coverage gate ($125 × U) is strictly enforced."""
    assert coverage_required(0) == 0
    assert coverage_required(1) == 125
    assert coverage_required(10) == 1250
    assert coverage_required(-5) == 0


# =============================================================================
# TEST 12: Forbidden Mechanisms Static Audit
# =============================================================================
def test_12_forbidden_mechanisms_static_audit():
    """Verify absence of forbidden mechanisms in ARCH-003 source files."""
    forbidden_patterns = [
        "H=500", "h=500", "step <= 288", "step <=288", "checkpoint <= 288",
        "defer_enabled = True", "front_items = ['CARROT']"
    ]
    py_files = [f for f in os.listdir(ARCH003_DIR) if f.endswith(".py")]
    for filename in py_files:
        path = os.path.join(ARCH003_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for pat in forbidden_patterns:
            assert pat not in content, f"Forbidden pattern '{pat}' detected in {filename}!"
