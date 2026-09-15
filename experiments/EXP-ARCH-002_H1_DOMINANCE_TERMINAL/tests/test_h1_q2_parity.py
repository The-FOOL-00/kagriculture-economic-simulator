# SPDX-License-Identifier: MIT
"""Q2 baseline-prediction parity (prereg §11/Q2).

Pure V54++ self-play games (NO H1 code runs inside any game loop)
on CONSUMED seeds, followed by OFFLINE H1 planning on the recorded
entry states.  Asserts the Q2 property: zero adoptions on
disagreeing trajectories.  The agreement RATE is reported (printed)
as an exposure diagnostic; no numeric bar is set on it (prereg).

Governance: seeds are drawn ONLY from the consumed DEV-006 fresh-
replication cohort (248000–248049); disjointness from every
protected range is asserted in-test.  No H1 treatment is emitted
into any game; no performance delta is computed anywhere.
"""

import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
H1_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(H1_DIR, "..", ".."))
PORT_DIR = os.path.join(
    REPO_ROOT, "experiments/EXP-DEV-006_HORIZON_KILLTEST/port")
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)

from kagsim_py import api as papi  # noqa: E402

# Consumed DEV-006 fresh-replication cohort (handoff §7: executed).
# 248012 covers the yarn route (BUY-containing window markets); the
# rest cover backbone.  All inside 248000–248049 (consumed).
Q2_SEEDS = (248000, 248001, 248002, 248012)

# Every protected range (prereg §13.2/§22/G-QUAR + handoff §2–§3).
PROTECTED_RANGES = (
    (214200, 214249),    # virgin final holdout
    (310000, 310499),    # DEV-007 RESERVED (unexecuted)
    (410000, 410499),    # DEV-007 fallback 1
    (510000, 510499),    # DEV-007 fallback 2
    (320000, 320499),    # ARCH-002 experimental cohort
    (50000, 50499),      # consumed/benchmark block
    (50100, 50149),      # audited benchmark
    (50150, 50199),      # contaminated benchmark
    (50050, 50099),      # DEV-006 qualification
    (60000, 60049),      # sweep-contaminated
    (1000, 2683),        # stride-reachable executions
    (249000, 249049), (250000, 250049), (255000, 255049),
    (260000, 260049), (300000, 300049),  # named reserved
)


def test_q2_seeds_consumed_and_disjoint():
    for seed in Q2_SEEDS:
        assert 248000 <= seed <= 248049, seed
        for lo, hi in PROTECTED_RANGES:
            assert not (lo <= seed <= hi), (seed, lo, hi)


def _full_config():
    return {"boardSize": 10, "turnsPerDay": 24, "episodeSteps": 720,
            "shedCapacity": 100, "maxMarketOrdersPerTurn": 10,
            "townShopSellInterval": 4, "townCenterSellInterval": 24}


def _play_baseline_game(seed, configuration):
    """Pure baseline self-play; records E-states + 712–718 actions."""
    from h1_baseline import load_baseline
    baseline = load_baseline()
    game = papi.Game(seed)
    context = {}
    while not game.done:
        t = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        if t == 712:
            for seat, obs in ((0, obs0), (1, obs1)):
                route = baseline.active_route(t, obs)
                context[seat] = {
                    "route": route,
                    "obs_E": copy.deepcopy(obs),
                    "ledgers_E": baseline.clone_ledgers(route, seat),
                    "live_actions": [], "configuration": configuration,
                }
        acts = []
        for seat, obs in ((0, obs0), (1, obs1)):
            action = baseline.call(copy.deepcopy(obs),
                                   copy.deepcopy(configuration))
            acts.append(action)
            if t >= 712:
                context[seat]["live_actions"].append(
                    copy.deepcopy(action))
        game.step(acts[0], acts[1])
    return baseline, context


def _g5_equal(baseline, live, shadow, obs):
    norm_live = baseline.align_hands(copy.deepcopy(live), obs)
    norm_shadow = baseline.align_hands(copy.deepcopy(shadow), obs)
    return (norm_live.get("farmer") == norm_shadow.get("farmer")
            and norm_live.get("hands") == norm_shadow.get("hands")
            and norm_live.get("market") == norm_shadow.get("market"))


def _audit_seat_game(baseline, seat, ctx):
    """Offline planning + agreement audit for one seat-game."""
    from h1_agent import H1Overlay
    from h1_telemetry import H1Abstain, blank_record
    overlay = H1Overlay(baseline)
    record = blank_record(seat)
    live_e = ctx["live_actions"][0]
    try:
        plan = overlay._plan_at_entry(
            seat, 712, ctx["obs_E"], ctx["configuration"],
            ctx["route"], copy.deepcopy(ctx["ledgers_E"]),
            copy.deepcopy(live_e), record)
        reason = "OK_ACTIVATED"
        subcause = {}
    except H1Abstain as exc:
        reason = exc.reason
        subcause = exc.subcause
    schedule = overlay._last_shadow_schedule.get(seat)
    result = {"seed": ctx.get("seed"), "seat": seat,
              "route": ctx["route"], "reason": reason,
              "subcause": subcause, "agree": None, "steps": 0}
    if schedule is not None:
        assert len(schedule) == 7
        assert len(ctx["live_actions"]) == 7
        per_step = [_g5_equal(baseline, live, pred, ctx["obs_E"])
                    for live, pred in zip(ctx["live_actions"],
                                          schedule)]
        result["agree"] = per_step
        result["steps"] = len(per_step)
        if reason == "OK_ACTIVATED":
            # Q2 PROPERTY: adoption requires full agreement.
            assert all(per_step), (seat, per_step)
        if reason == "ABSTAIN_HANDSHAKE":
            # Handshake fires ⟺ first-step prediction ≠ live.
            assert per_step[0] is False, seat
    return result


@pytest.mark.parametrize("seed", Q2_SEEDS)
def test_q2_parity_on_consumed_seed(seed):
    configuration = None if seed == 248002 else _full_config()
    baseline, context = _play_baseline_game(seed, configuration)
    for seat in (0, 1):
        context[seat]["seed"] = seed
    results = [_audit_seat_game(baseline, seat, context[seat])
               for seat in (0, 1)]
    # Report (harvested into the validation report).
    for result in results:
        agree = result["agree"]
        rate = ("n/a" if agree is None else
                "%d/7" % sum(1 for a in agree if a))
        print("\nQ2 seed=%d seat=%d route=%s reason=%s sub=%s agree=%s"
              % (result["seed"], result["seat"], result["route"],
                 result["reason"], result.get("subcause"), rate))
    # Q2 property restated at game level (belt + suspenders).
    for result in results:
        if result["reason"] == "OK_ACTIVATED":
            assert result["agree"] is not None
            assert all(result["agree"])
