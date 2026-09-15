# SPDX-License-Identifier: MIT
"""Identity tests: H1 == baseline outside adopted plans (B5/R3, §18/P-PURE).

Covers pre-terminal identity (all steps < 712), abstention identity
(every ABSTAIN_* reason), abandonment identity, post-window
passthrough, plan-record reset on rewind, and the shadow_only harness
purity property (emission always baseline).
"""

import copy

import pytest

from conftest import make_obs, wheat_tile


@pytest.mark.parametrize("step", [0, 1, 71, 72, 143, 144, 288, 360,
                                  576, 699, 700, 711])
def test_pre_entry_identity(overlay, fresh_baseline, full_config,
                            step):
    obs = make_obs(step)
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert out == live
    assert overlay.plans == {}


def test_pre_entry_identity_yarn_route(overlay, fresh_baseline,
                                       full_config):
    obs = make_obs(700, shops=("YARN_STORE",))
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert out == live


def test_post_window_passthrough(overlay, fresh_baseline,
                                 full_config):
    # Defensive: step > 718 can never carry a plan; must pass through.
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=3))],
                   shed={"WHEAT": 5})
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert 0 in overlay.plans
    obs719 = make_obs(719)
    live = fresh_baseline.call(copy.deepcopy(obs719),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs719),
                      copy.deepcopy(full_config))
    assert out == live


def test_rewind_discards_plan(overlay, fresh_baseline, full_config):
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=3))],
                   shed={"WHEAT": 5})
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert overlay.open_records[0]["reason"] == "OK_ACTIVATED"
    assert 0 in overlay.plans
    # Rewind to step 0: plan forgotten, record finalized.
    obs0 = make_obs(0)
    overlay.act(copy.deepcopy(obs0), copy.deepcopy(full_config))
    assert 0 not in overlay.plans
    assert len(overlay.records) == 1
    assert overlay.records[0]["reason"] == "OK_ACTIVATED"


def test_duplicate_step_resets_seat(overlay, fresh_baseline,
                                    full_config):
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=3))],
                   shed={"WHEAT": 5})
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert 0 in overlay.plans
    # Duplicate step-712 callback: treated as a new lifetime, plan
    # discarded, fresh planning runs.
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert overlay.open_records[0]["reason"] in (
        "OK_ACTIVATED", "ABSTAIN_HANDSHAKE", "ABSTAIN_NO_GAIN",
        "ABSTAIN_DOMINANCE", "ABSTAIN_NOSTEAL", "ABSTAIN_ACCEPT",
        "ABSTAIN_BUDGET", "ABSTAIN_CONFIG", "ABSTAIN_SHED",
        "ABSTAIN_ITEMS", "ABSTAIN_WINDOW_OPS", "ABSTAIN_MARKET_OP",
        "ABSTAIN_BUY_COVERAGE")


@pytest.mark.parametrize("seat", [0, 1])
def test_per_seat_isolation(overlay, fresh_baseline, full_config,
                            seat):
    other = 1 - seat
    obs = make_obs(712, seat=seat,
                   tiles=[(4, 4, wheat_tile(yield_units=3))],
                   shed={"WHEAT": 5})
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert seat in overlay.plans
    assert other not in overlay.plans
    obs_o = make_obs(100, seat=other)
    live = fresh_baseline.call(copy.deepcopy(obs_o),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs_o),
                      copy.deepcopy(full_config))
    assert out == live


def test_abstention_identity_all_reasons(fresh_baseline, full_config):
    # Every abstention path returns the live action object-equal.
    from h1_agent import H1Overlay
    cases = [
        make_obs(712, shed={"WHEAT": 101}),          # SHED
        make_obs(712, shed={"GOOSE": 1}),            # ITEMS
        make_obs(712, money=100.0,                   # BUY_COVERAGE
                 shops=("YARN_STORE",)),
        make_obs(712),                               # NO_GAIN (barren)
    ]
    hour23 = make_obs(712, shed={"WHEAT": 90, "MILK": 9},
                      inventories=[{"WOOL": 5}, {}, {}])
    hour23["hour"] = 23
    cases.append(hour23)                             # HANDSHAKE
    reasons = set()
    for obs in cases:
        overlay = H1Overlay(fresh_baseline)
        live = fresh_baseline.call(copy.deepcopy(obs),
                                   copy.deepcopy(full_config))
        out = overlay.act(copy.deepcopy(obs),
                          copy.deepcopy(full_config))
        record = overlay.open_records.get(int(obs["player"]))
        reasons.add(record["reason"])
        assert record["reason"] != "OK_ACTIVATED"
        assert out == live
    assert reasons == {"ABSTAIN_SHED", "ABSTAIN_ITEMS",
                       "ABSTAIN_BUY_COVERAGE", "ABSTAIN_NO_GAIN",
                       "ABSTAIN_HANDSHAKE"}


def test_shadow_only_never_emits_plan(fresh_baseline, full_config):
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline, shadow_only=True)
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=3))],
                   shed={"WHEAT": 5})
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "OK_ACTIVATED"
    assert record["shadow_only"] is True
    assert out == live  # planning ran; emission forced to baseline


def test_closed_loop_verification_end_to_end(fresh_baseline,
                                             full_config):
    # Shadow-closed-loop: feed the plan's expected states back as live
    # obs with live baseline actions == predicted schedule; every
    # step must verify and emitted markets must equal live markets.
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline)
    obs_e = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=3))],
                     shed={"WHEAT": 5})
    overlay.act(copy.deepcopy(obs_e), copy.deepcopy(full_config))
    assert overlay.open_records[0]["reason"] == "OK_ACTIVATED"
    plan = overlay.plans[0]
    for offset in range(1, 7):
        t = 712 + offset
        farm, private = plan["expected_states"][offset]
        live_obs = make_obs(t)
        live_obs["farms"][0] = dict(farm, money=9000.0)
        live_obs["private"] = copy.deepcopy(private)
        live_action = copy.deepcopy(plan["baseline"][offset])
        # Play the live baseline action through the real wrapper path
        # by monkeypatching the live call for this step only.
        import h1_agent as _mod
        orig_call = fresh_baseline.call
        fresh_baseline.call = lambda o, c=None: copy.deepcopy(
            live_action)
        try:
            out = overlay.act(copy.deepcopy(live_obs),
                              copy.deepcopy(full_config))
        finally:
            fresh_baseline.call = orig_call
        assert overlay.open_records[0]["reason"] == "OK_ACTIVATED"
        assert out["market"] == live_action["market"]
        stored_units = [plan["actions"][offset].get("farmer")] + \
            list(plan["actions"][offset].get("hands", []))
        out_units = [out.get("farmer")] + list(out.get("hands", []))
        assert out_units == stored_units
