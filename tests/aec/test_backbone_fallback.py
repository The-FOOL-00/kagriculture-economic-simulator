# SPDX-License-Identifier: MIT
"""Test L — Backbone Fallback Invariant."""

from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor


def test_fallback_on_no_event(normal_opening_obs):
    adapter = BackboneAdapter()
    executor = AECExecutor(backbone_adapter=adapter)
    
    # Run executor
    action = executor.act(normal_opening_obs)
    
    # Baseline action from adapter
    cached_baseline = adapter.get_cached_result()
    assert cached_baseline is not None
    assert action == cached_baseline.action


def test_fallback_on_unhandled_exception(normal_opening_obs):
    adapter = BackboneAdapter()
    executor = AECExecutor(backbone_adapter=adapter)
    
    # Inject a faulty detector that raises an error
    def faulty_detector(*args, **kwargs):
        raise RuntimeError("Injected optimizer crash")
        
    executor.event_bus.publish_many = faulty_detector
    
    # Must fail closed: return baseline action without raising!
    action = executor.act(normal_opening_obs)
    cached_baseline = adapter.get_cached_result()
    assert cached_baseline is not None
    assert action == cached_baseline.action
    assert executor.latest_telemetry.decision == "ABSTAIN_EXCEPTION"
