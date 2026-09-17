# SPDX-License-Identifier: MIT
"""Test O — Exactly One Baseline Call Discipline (§33).

Instruments the backbone callable and asserts:
    exactly one live call per game turn
under:
    1. no-op / no-event path
    2. event detection & candidate generation
    3. candidate search & rejection
    4. safety exceptions / fail-closed paths
Also verifies that double invocation on the same step raises AssertionError.
"""

from typing import Any, Dict
import pytest
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor


class CallCountingBackbone:
    def __init__(self, action: Dict[str, Any]) -> None:
        self.action = action
        self.call_count = 0
        self.call_history = []

    def __call__(self, obs: Dict[str, Any], cfg: Any = None) -> Dict[str, Any]:
        self.call_count += 1
        self.call_history.append(obs.get("step", 0))
        return dict(self.action)


def test_one_baseline_call_no_event(normal_opening_obs: Dict[str, Any]) -> None:
    """Step with no event makes exactly one live call."""
    backbone = CallCountingBackbone({"farmer": ["PASS"], "hands": [], "market": []})
    adapter = BackboneAdapter(v3_callable=backbone)
    executor = AECExecutor(backbone_adapter=adapter)

    executor.act(normal_opening_obs)
    assert backbone.call_count == 1


def test_one_baseline_call_with_event(weed_obstruction_obs: Dict[str, Any]) -> None:
    """Step with event, opportunity search, and simulation makes exactly one live call."""
    backbone = CallCountingBackbone({"farmer": ["RIGHT"], "hands": [["UP"]], "market": []})
    adapter = BackboneAdapter(v3_callable=backbone)
    executor = AECExecutor(backbone_adapter=adapter)

    executor.act(weed_obstruction_obs)
    assert backbone.call_count == 1


def test_one_baseline_call_exception_path(normal_opening_obs: Dict[str, Any]) -> None:
    """Step where an exception occurs in optimizer makes exactly one live call."""
    backbone = CallCountingBackbone({"farmer": ["PASS"], "hands": [], "market": []})
    adapter = BackboneAdapter(v3_callable=backbone)
    executor = AECExecutor(backbone_adapter=adapter)

    # Monkeypatch event detection to raise an exception
    executor.event_bus.publish_many = lambda events: (_ for _ in ()).throw(RuntimeError("Forced error"))

    action = executor.act(normal_opening_obs)
    assert backbone.call_count == 1
    assert action == {"farmer": ["PASS"], "hands": [], "market": []}
    assert executor.latest_telemetry.decision == "ABSTAIN_EXCEPTION"


def test_multi_step_one_call_per_turn() -> None:
    """Sequence of consecutive turns results in exactly one call per turn."""
    backbone = CallCountingBackbone({"farmer": ["PASS"], "hands": [], "market": []})
    adapter = BackboneAdapter(v3_callable=backbone)
    executor = AECExecutor(backbone_adapter=adapter)

    for step in range(10):
        obs = {
            "step": step, "day": 0, "hour": step, "player": 0,
            "farms": [{"money": 3000.0, "farmer": [4, 4], "hands": [], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 0},
                      {"money": 3000.0, "farmer": [4, 4], "hands": [], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 0}],
            "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
            "market": {"prices": {"WHEAT": 25}, "inventory": {"WHEAT": 10000}},
            "town": {"unlocked_shops": []}
        }
        executor.act(obs)
        assert backbone.call_count == step + 1


def test_double_call_same_step_raises_assertion(normal_opening_obs: Dict[str, Any]) -> None:
    """BackboneAdapter directly raises AssertionError if called twice on same turn."""
    backbone = CallCountingBackbone({"farmer": ["PASS"], "hands": [], "market": []})
    adapter = BackboneAdapter(v3_callable=backbone)

    adapter.call_once(normal_opening_obs)
    with pytest.raises(RuntimeError, match="invoked twice for step"):
        adapter.call_once(normal_opening_obs)
