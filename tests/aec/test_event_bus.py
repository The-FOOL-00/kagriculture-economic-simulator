# SPDX-License-Identifier: MIT
"""Test B — Event Bus and Event Detectors."""

from aec.events import EventBus, EventType, detect_events
from aec.ir import build_economic_state


def test_no_event_fast_path(normal_opening_obs):
    state = build_economic_state(normal_opening_obs)
    events = detect_events(state)
    
    # Standard normal opening step 0 should trigger zero alarms
    assert len(events) == 0


def test_obstruction_detection(weed_obstruction_obs):
    state = build_economic_state(weed_obstruction_obs)
    events = detect_events(state)
    
    types = [e.event_type for e in events]
    assert EventType.E1_FARM_OBSTRUCTION in types
    
    obs_event = next(e for e in events if e.event_type == EventType.E1_FARM_OBSTRUCTION)
    assert 0 in obs_event.payload["worker_ids"]
    assert obs_event.severity >= 0.6


def test_cash_deficit_detection(cash_deficit_obs):
    state = build_economic_state(cash_deficit_obs)
    events = detect_events(state)
    
    types = [e.event_type for e in events]
    assert EventType.E2_CASH_DEVIATION in types
    
    cash_event = next(e for e in events if e.event_type == EventType.E2_CASH_DEVIATION)
    assert cash_event.payload["cash"] == 110.0


def test_shed_capacity_detection(shed_capacity_obs):
    state = build_economic_state(shed_capacity_obs)
    events = detect_events(state)
    
    types = [e.event_type for e in events]
    assert EventType.E3_SHED_CAPACITY_RISK in types


def test_event_bus_deterministic_ordering():
    bus = EventBus()
    from aec.events import Event
    bus.publish(Event(EventType.E2_CASH_DEVIATION, step=10, severity=0.4))
    bus.publish(Event(EventType.E1_FARM_OBSTRUCTION, step=10, severity=0.9))
    bus.publish(Event(EventType.E4_MARKET_REGIME_SHIFT, step=10, severity=0.6))
    
    ordered = bus.get_events()
    assert ordered[0].event_type == EventType.E1_FARM_OBSTRUCTION  # 0.9
    assert ordered[1].event_type == EventType.E4_MARKET_REGIME_SHIFT # 0.6
    assert ordered[2].event_type == EventType.E2_CASH_DEVIATION  # 0.4
