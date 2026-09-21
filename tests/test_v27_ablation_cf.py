# SPDX-License-Identifier: MIT
"""V27: ablation isolation + counterfactual smoke tests.

  - Variant flag unit checks (step-0 actions, dispatch on/off).
  - V3S == V3 over a short live run (harness coherence).
  - Counterfactual restore-exactness: probe+restore+continue equals a
    clean parallel replay (no fixtures; ~15s).
"""

import copy
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from aec.backbone.v27_ablation_adapters import (  # noqa: E402
    V27AblationAdapter,
    VARIANT_IDS,
)
from kaggle_environments import make  # noqa: E402


def live_obs(seed, episode_steps=30):
    env = make("kaggriculture", configuration={"seed": seed,
                                               "episodeSteps": episode_steps})
    obs = env.reset()
    return env, obs[0]["observation"], obs[1]["observation"]


class TestAblationIsolation:
    def test_variant_ids(self):
        assert set(VARIANT_IDS) == {"V27-ABL-A1", "V27-ABL-A2",
                                    "V27-ABL-A3", "V27-ABL-V3S",
                                    "V27-ABL-A7"}

    def test_flag_matrix(self):
        expect = {
            "V27-ABL-A1": (True, 30, True, False),
            "V27-ABL-A2": (False, 50, True, False),
            "V27-ABL-A3": (False, 30, False, False),
            "V27-ABL-V3S": (True, 30, False, False),
            "V27-ABL-A7": (True, 30, False, True),
        }
        for v, (call0, units, disp, rewrite) in expect.items():
            a = V27AblationAdapter(v)
            assert (a.call_v3_at_step0, a.open_units, a.dispatch,
                    a.rewrite_step0_wash) == (call0, units, disp, rewrite)
            assert a.identity() == v

    def test_a7_rewrites_only_exact_wash(self):
        _, o0, _ = live_obs(249431)
        a7 = V27AblationAdapter("V27-ABL-A7")
        act = a7.act(copy.deepcopy(o0))
        assert act["market"] == [["BUY_PRODUCT", "WHEAT", 30],
                                 ["SELL", "WHEAT", 30]]
        assert a7.step0_rewritten is True
        assert a7.step0_unexpected_shape is False

    def test_step0_actions(self):
        _, o0, _ = live_obs(249431)
        o0 = copy.deepcopy(o0)
        o0["step"] = 0
        a1 = V27AblationAdapter("V27-ABL-A1")
        a2 = V27AblationAdapter("V27-ABL-A2")
        a3 = V27AblationAdapter("V27-ABL-A3")
        v3s = V27AblationAdapter("V27-ABL-V3S")
        v3 = V3BackboneAdapter()
        # A2/A3 bypass with fixed washes; A1/V3S call V3 through.
        assert a2.act(copy.deepcopy(o0))["market"] == [
            ["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]
        assert a3.act(copy.deepcopy(o0))["market"] == [
            ["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
        assert a1.act(copy.deepcopy(o0)) == v3.act(copy.deepcopy(o0))
        v3b = V3BackboneAdapter()
        assert v3s.act(copy.deepcopy(o0)) == v3b.act(copy.deepcopy(o0))

    def test_v3s_equals_v3_short_run(self):
        # V3S must behave EXACTLY like V3 (30 live steps, both seats).
        for seat in (0, 1):
            env = make("kaggriculture", configuration={"seed": 249431,
                                                       "episodeSteps": 30})
            v3s = V27AblationAdapter("V27-ABL-V3S")
            v3 = V3BackboneAdapter()
            a = lambda o, c=None: v3s.act(o, c)  # noqa: E731
            b = lambda o, c=None: v3.act(o, c)  # noqa: E731
            env.run([a, b] if seat == 0 else [b, a])
            import json as _json
            ta = _json.dumps([s[seat].get("action") for s in env.steps],
                             sort_keys=True)
            env2 = make("kaggriculture", configuration={"seed": 249431,
                                                        "episodeSteps": 30})
            x = V3BackboneAdapter()
            y = V3BackboneAdapter()
            xa = lambda o, c=None: x.act(o, c)  # noqa: E731
            ya = lambda o, c=None: y.act(o, c)  # noqa: E731
            env2.run([xa, ya] if seat == 0 else [ya, xa])
            tb = _json.dumps([s[seat].get("action") for s in env2.steps],
                             sort_keys=True)
            assert ta == tb

    def test_a3_emits_internal_v3_unmodified(self):
        # A3 (dispatch off) must return its internal V3's action verbatim
        # on steps >= 1 (spy, no behavioral assumptions about init).
        env = make("kaggriculture", configuration={"seed": 249431,
                                                   "episodeSteps": 30})
        obs = env.reset()
        a3 = V27AblationAdapter("V27-ABL-A3")
        calls = []
        orig = a3._v3_agent_callable

        def spy(ob, config=None):
            out = orig(ob, config)
            calls.append(copy.deepcopy(out))
            return out

        a3._v3_agent_callable = spy
        idle = {"farmer": ["PASS"], "hands": [], "market": []}
        step = 0
        while True:
            o0 = obs[0]["observation"]
            o0["step"] = step
            act_a3 = a3.act(copy.deepcopy(o0))
            if step == 0:
                assert act_a3["market"] == [["BUY_PRODUCT", "WHEAT", 30],
                                            ["SELL", "WHEAT", 30]]
                assert calls == []  # bypass: internal V3 untouched
            else:
                assert act_a3 == calls[-1]
            if step >= 29:
                break
            obs = env.step([act_a3, idle])
            step += 1


class TestCounterfactualSmoke:
    def test_probe_restore_continue_matches_clean_replay(self):
        # Replay to t=60 with V3 adapter; snapshot; probe doctored obs;
        # restore; continue to t=90. A clean replay to t=90 must match
        # the continued money exactly (restore-exactness, no fixtures).
        def run_to(seed, upto, probe_at=None, injection=0.0):
            env = make("kaggriculture", configuration={"seed": seed})
            p3 = V25P3BackboneAdapter()
            v3 = V3BackboneAdapter()
            obs = env.reset()
            step = 0
            snap = None
            while step < upto:
                o0, o1 = obs[0]["observation"], obs[1]["observation"]
                o0["step"] = step
                o1["step"] = step
                if step == probe_at:
                    snap = v3.snapshot_state()
                    doc = copy.deepcopy(o1)
                    doc["farms"][1]["money"] += injection
                    _ = v3.act(doc)
                    v3.restore_state(snap)
                a_p3 = p3.act(copy.deepcopy(o0))
                a_v3 = v3.act(copy.deepcopy(o1))
                obs = env.step([a_p3, a_v3])
                step += 1
            m0 = obs[0]["observation"]["farms"][0]["money"]
            m1 = obs[1]["observation"]["farms"][1]["money"]
            return m0, m1

        clean = run_to(249431, 90)
        probed = run_to(249431, 90, probe_at=60, injection=5000.0)
        assert clean == probed
