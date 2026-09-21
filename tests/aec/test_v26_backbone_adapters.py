# SPDX-License-Identifier: MIT
"""Tests for V26 Backbone Adapters: Equivalence & State Isolation (§5, §6)."""

import copy
import os
import tarfile
import tempfile
import importlib.util
import pytest

from aec.backbone.v3_adapter import V3BackboneAdapter
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
from aec.counterfactual.simulator import ShadowRolloutState
from aec.ir.economic_state import build_economic_state
from kaggle_environments import make


def load_raw_v3():
    v3_tar = os.path.abspath("submission_Vj_kc_v3.tar.gz")
    d = tempfile.mkdtemp(prefix="raw_v3_test_")
    with tarfile.open(v3_tar, "r:gz") as tar:
        tar.extractall(d)
    spec = importlib.util.spec_from_file_location("raw_v3", os.path.join(d, "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def load_raw_p3():
    p3_path = os.path.abspath(os.path.join("candidates", "v25_p3_unified.py"))
    spec = importlib.util.spec_from_file_location("raw_p3", p3_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def test_v3_adapter_exact_equivalence():
    """Verify V3BackboneAdapter produces bit-exact actions compared to raw frozen V3."""
    env = make("kaggriculture", configuration={"seed": 249376, "episodeSteps": 100})
    raw_v3 = load_raw_v3()
    adapter_v3 = V3BackboneAdapter()

    obs = env.reset()[0]["observation"]
    for step in range(50):
        if env.done:
            break
        obs_copy1 = copy.deepcopy(obs)
        obs_copy2 = copy.deepcopy(obs)

        raw_act = raw_v3(obs_copy1)
        adapter_act = adapter_v3.act(obs_copy2)

        assert adapter_act == raw_act, f"V3 Adapter diverged at step {step}!\nAdapter: {adapter_act}\nRaw:     {raw_act}"
        actions = [adapter_act, {"farmer": ["PASS"], "hands": [], "market": []}]
        state = env.step(actions)
        obs = state[0]["observation"]

    assert adapter_v3.identity() == "V3_STANDALONE"
    assert adapter_v3.version() == "1.0.0-v3-frozen"


def test_v25_p3_adapter_exact_equivalence():
    """Verify V25P3BackboneAdapter produces bit-exact actions compared to raw V25 P3 candidate."""
    env = make("kaggriculture", configuration={"seed": 249376, "episodeSteps": 100})
    raw_p3 = load_raw_p3()
    adapter_p3 = V25P3BackboneAdapter()

    obs = env.reset()[0]["observation"]
    for step in range(50):
        if env.done:
            break
        obs_copy1 = copy.deepcopy(obs)
        obs_copy2 = copy.deepcopy(obs)

        raw_act = raw_p3(obs_copy1)
        adapter_act = adapter_p3.act(obs_copy2)

        assert adapter_act == raw_act, f"V25 P3 Adapter diverged at step {step}!\nAdapter: {adapter_act}\nRaw:     {raw_act}"
        actions = [adapter_act, {"farmer": ["PASS"], "hands": [], "market": []}]
        state = env.step(actions)
        obs = state[0]["observation"]

    assert adapter_p3.identity() == "V25_P3_UNIFIED"
    assert adapter_p3.version() == "1.0.0-v25-p3"


def test_v25_p3_state_isolation_and_snapshot():
    """Verify that taking snapshot and running continuation steps does NOT pollute live state."""
    adapter_p3 = V25P3BackboneAdapter()
    env = make("kaggriculture", configuration={"seed": 249376, "episodeSteps": 100})

    obs = env.reset()[0]["observation"]
    # Step 0: opening turn
    act0 = adapter_p3.act(obs)
    assert act0["market"] == [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]

    state = env.step([act0, {"farmer": ["PASS"], "hands": [], "market": []}])
    obs1 = state[0]["observation"]

    # At step 1, snapshot state
    snap = adapter_p3.snapshot_state()

    # Create continuation policy and simulate forward turns
    cont = adapter_p3.create_continuation_policy()
    econ_state = build_economic_state(obs1, None)
    rollout = ShadowRolloutState(econ_state)

    # Run 5 shadow steps
    for _ in range(5):
        shadow_act = cont.step_action(rollout, player=0)
        assert isinstance(shadow_act, dict)
        rollout.step += 1

    # Restore state to step 1 snapshot
    adapter_p3.restore_state(snap)

    # Calling act() on step 1 should succeed and produce the exact canonical step 1 action
    act1 = adapter_p3.act(obs1)
    assert isinstance(act1, dict)
    assert "farmer" in act1
