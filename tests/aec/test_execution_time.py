# SPDX-License-Identifier: MIT
"""Test Q — Execution Time & Latency Budget (§33).

Measures:
    1. No-event fast path latency
    2. Event detection latency
    3. Full candidate search and simulation path latency
Verifies all execution paths remain comfortably within the Kaggle turn budget (<1000ms).
"""

import time
from typing import Any, Dict
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor


def test_no_event_fast_path_latency(normal_opening_obs: Dict[str, Any]) -> None:
    """No-event fast path should be negligible (< 10 ms)."""
    mock_v3 = lambda obs, cfg=None: {"farmer": ["PASS"], "hands": [], "market": []}
    adapter = BackboneAdapter(v3_callable=mock_v3)
    executor = AECExecutor(backbone_adapter=adapter)

    # Warm-up call
    executor.act(dict(normal_opening_obs, step=0))

    # Measurement
    latencies = []
    for step in range(1, 21):
        obs = dict(normal_opening_obs, step=step)
        t0 = time.perf_counter()
        executor.act(obs)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 10.0, f"No-event latency too high: {avg_latency:.2f} ms"
    assert executor.latest_telemetry.abstain_reason == "NO_EVENT_FAST_PATH"


def test_event_path_latency(weed_obstruction_obs: Dict[str, Any]) -> None:
    """Full event, opportunity, candidate, and simulation path should be well within budget (< 100 ms)."""
    mock_v3 = lambda obs, cfg=None: {"farmer": ["RIGHT"], "hands": [["UP"]], "market": []}
    adapter = BackboneAdapter(v3_callable=mock_v3)
    executor = AECExecutor(backbone_adapter=adapter)

    # Measurement on event fixture
    t0 = time.perf_counter()
    action = executor.act(weed_obstruction_obs)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    telem = executor.latest_telemetry
    assert telem is not None
    assert elapsed_ms < 100.0, f"Event path latency exceeded 100 ms: {elapsed_ms:.2f} ms"
    assert telem.total_time_ms < 100.0
