# SPDX-License-Identifier: MIT
"""Tests for V26 quarantine-scan skip neutrality (perf gate, action-identical)."""

import copy

import pytest
from kaggle_environments import make

from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
from aec.config import AECConfig
from aec.integration.executor import AECExecutor


@pytest.mark.parametrize("enabled", [(), ("DEPENDENCY_AWARE_MARKET_TIMING",)])
def test_quarantine_scan_skip_action_parity(enabled):
    """enable_quarantine_scan=False must produce the identical action stream.

    Skipped detectors could only have emitted quarantined (non-actionable)
    opportunities, so the actionable stream, commits, and actions are unchanged.
    Only quarantine telemetry counts may differ.
    """
    seed = 249376
    n_steps = 50

    executors = {}
    for scan in (True, False):
        cfg = AECConfig(
            enabled_mechanisms=enabled,
            operational_mode="ROBUST_MODE",
            enable_quarantine_scan=scan,
        )
        adapter = V25P3BackboneAdapter(config=cfg)
        executors[scan] = AECExecutor(backbone_adapter=adapter, config=cfg)

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 100})
    obs = env.reset()[0]["observation"]
    for step in range(n_steps):
        if env.done:
            break

        act_full = executors[True].act(copy.deepcopy(obs))
        act_skip = executors[False].act(copy.deepcopy(obs))
        assert act_skip == act_full, (
            f"Quarantine-scan skip diverged at step {step} (enabled={enabled})!\n"
            f"Full scan: {act_full}\n"
            f"Skip scan: {act_skip}"
        )
        commit_full = executors[True]._latest_committed_patch
        commit_skip = executors[False]._latest_committed_patch
        assert (commit_skip is None) == (commit_full is None), (
            f"Commit-state diverged at step {step} (enabled={enabled})"
        )
        if commit_full is not None:
            assert commit_skip.mechanism_family == commit_full.mechanism_family

        state = env.step([act_full, {"farmer": ["PASS"], "hands": [], "market": []}])
        obs = state[0]["observation"]
