# SPDX-License-Identifier: MIT
"""AEC Event Bus for Event-Triggered Planning."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from aec.events.event_types import Event, EventType


class EventBus:
    """Explicit, inspectable event dispatcher.
    
    Guarantees:
    - Events are stored in deterministic order.
    - Has-events fast path enables cheap bypass when no replanning is required.
    """
    
    def __init__(self) -> None:
        self._events: List[Event] = []

    def publish(self, event: Event) -> None:
        self._events.append(event)

    def publish_many(self, events: List[Event]) -> None:
        self._events.extend(events)

    def clear(self) -> None:
        self._events.clear()

    @property
    def has_events(self) -> bool:
        return len(self._events) > 0

    def get_events(self) -> List[Event]:
        # Deterministic ordering: highest severity first, then by event name
        return sorted(
            self._events,
            key=lambda e: (-e.severity, e.event_type.value)
        )

    def has_event_type(self, event_type: EventType) -> bool:
        return any(e.event_type == event_type for e in self._events)

    def get_events_of_type(self, event_type: EventType) -> List[Event]:
        return [e for e in self._events if e.event_type == event_type]
