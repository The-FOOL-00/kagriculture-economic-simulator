# SPDX-License-Identifier: MIT
"""Tests for V26 AEC Infrastructure Null Parity (§11, §12)."""

import copy
import pytest
from kaggle_environments import make

from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
from aec.config import AECConfig
from aec.integration.executor import AECExecutor


def test_v25_aec_infra_only_null_parity():
    """Verify ARM 2 (V25 + AEC Infra-only, no commits) matches pure V25 action stream 100%."""
    seed = 249376
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 100})

    # Pure V25 P3 control
    adapter_pure = V25P3BackboneAdapter()

    # V25 P3 wrapped in AEC infrastructure with 0 enabled intervention mechanisms
    cfg = AECConfig(
        enabled_mechanisms=(),  # No intervention mechanisms authorized
        operational_mode="ROBUST_MODE",
    )
    adapter_aec = V25P3BackboneAdapter(config=cfg)
    executor = AECExecutor(backbone_adapter=adapter_aec, config=cfg)

    obs = env.reset()[0]["observation"]
    for step in range(50):
        if env.done:
            break

        obs_pure = copy.deepcopy(obs)
        obs_aec = copy.deepcopy(obs)

        pure_act = adapter_pure.act(obs_pure)
        aec_act = executor.act(obs_aec)

        # Invariant: 100% bit-exact equality on all non-committed turns
        assert aec_act == pure_act, (
            f"AEC Infrastructure perturbed baseline at step {step}!\n"
            f"Pure V25: {pure_act}\n"
            f"AEC Infra: {aec_act}"
        )
        assert executor._latest_committed_patch is None

        # Advance environment
        state = env.step([aec_act, {"farmer": ["PASS"], "hands": [], "market": []}])
        obs = state[0]["observation"]

    print("50 turns evaluated: 100% exact match between V25 pure and V25 AEC infra-only.")
