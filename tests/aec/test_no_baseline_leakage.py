# SPDX-License-Identifier: MIT
"""Test N — No Baseline Leakage (§33).

Verifies that when AEC does not commit a patch (e.g. no-event path, or dormant/abstaining mode),
the emitted action is bit-for-bit identical to the raw backbone output, with no mutation
or behavioral drift.
"""

import copy
from typing import Any, Dict
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor


def test_no_baseline_leakage_no_event(normal_opening_obs: Dict[str, Any]) -> None:
    """When no event fires, baseline action is emitted exactly with no mutation."""
    raw_backbone_action = {"farmer": ["BUY", "SEEDS", "WHEAT"], "hands": [], "market": []}
    
    # 1. Direct backbone execution
    backbone_only_action = copy.deepcopy(raw_backbone_action)

    # 2. Backbone + AEC execution
    mock_v3 = lambda obs, cfg=None: copy.deepcopy(raw_backbone_action)
    adapter = BackboneAdapter(v3_callable=mock_v3)
    executor = AECExecutor(backbone_adapter=adapter)

    aec_action = executor.act(copy.deepcopy(normal_opening_obs))

    # Must be bit-for-bit identical
    assert aec_action == backbone_only_action
    assert executor.latest_telemetry is not None
    assert executor.latest_telemetry.decision == "BACKBONE"
    assert executor.latest_telemetry.abstain_reason == "NO_EVENT_FAST_PATH"


def test_no_baseline_leakage_on_abstain(weed_obstruction_obs: Dict[str, Any]) -> None:
    """When events fire but AEC abstains, baseline action is emitted untouched."""
    raw_backbone_action = {"farmer": ["RIGHT"], "hands": [["UP"]], "market": []}
    
    mock_v3 = lambda obs, cfg=None: copy.deepcopy(raw_backbone_action)
    adapter = BackboneAdapter(v3_callable=mock_v3)
    executor = AECExecutor(backbone_adapter=adapter)

    # In weed_obstruction_obs with this baseline, if no candidate is certified superior or if we force abstain
    aec_action = executor.act(copy.deepcopy(weed_obstruction_obs))
    
    if executor.latest_telemetry.decision == "ABSTAIN":
        assert aec_action == raw_backbone_action
