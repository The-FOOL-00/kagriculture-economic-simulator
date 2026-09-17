# SPDX-License-Identifier: MIT
"""Test M — Deterministic Replay (§33).

Verifies that identical observation, configuration, and state produce
identical candidate ordering, identical patch decision, and identical final action.
"""

import copy
from typing import Any, Dict
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor


def test_deterministic_replay_across_runs(weed_obstruction_obs: Dict[str, Any]) -> None:
    """Test identical candidate ordering, patch decisions, and actions across runs."""
    actions = []
    telemetries = []

    for _ in range(5):
        # Create fresh adapter with mock backbone
        mock_v3 = lambda obs, cfg=None: {"farmer": ["RIGHT"], "hands": [], "market": []}
        adapter = BackboneAdapter(v3_callable=mock_v3)
        executor = AECExecutor(backbone_adapter=adapter)

        obs_copy = copy.deepcopy(weed_obstruction_obs)
        action = executor.act(obs_copy)
        actions.append(action)
        telemetries.append(executor.latest_telemetry)

    # All 5 actions must be identical bit-for-bit
    first_action = actions[0]
    for act in actions[1:]:
        assert act == first_action

    # All telemetry decisions must be identical
    first_telem = telemetries[0]
    for telem in telemetries[1:]:
        assert telem is not None
        assert telem.decision == first_telem.decision
        assert telem.events_detected == first_telem.events_detected
        assert telem.opportunities_count == first_telem.opportunities_count
        assert telem.candidates_count == first_telem.candidates_count
        assert telem.simulations_run == first_telem.simulations_run
        assert telem.committed_patch_id == first_telem.committed_patch_id
