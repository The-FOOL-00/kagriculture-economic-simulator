# SPDX-License-Identifier: MIT
"""Coupled Patch Representation for AEC."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CoupledPatch:
    """A small, economically coupled tactical deviation over the macro backbone (§11, §20).
    
    A single patch may coordinate:
    - Multiple worker action alterations
    - Timing adjustments
    - Market order reordering / emission
    - Terminal conversion steps
    """
    patch_id: str
    source_opportunity_id: str
    
    # Worker mutations: worker_id -> replacement command list (e.g. 0 -> ["DIG"])
    worker_mutations: Dict[int, List[str]] = field(default_factory=dict)
    
    # Market mutations: replacement market order list
    market_mutations: Optional[List[List[Any]]] = None
    
    # Timing and coordination parameters
    timing_changes: Dict[str, Any] = field(default_factory=dict)
    resource_changes: Dict[str, Any] = field(default_factory=dict)
    terminal_changes: Dict[str, Any] = field(default_factory=dict)
    
    # Execution and evaluation metadata
    mechanism_family: str = ""
    dependencies: List[str] = field(default_factory=list)
    expected_horizon: int = 12
    rationale: str = ""

    # Dynamic route splicing and continuation (§8, §14)
    spliced_continuation: Optional[List[Dict[str, Any]]] = None
    reconnect_result: Optional[Any] = None

    # Dynamic resource DAG and obligation tracking (§14)
    affected_obligations: List[str] = field(default_factory=list)
    conversion_metadata: Dict[str, Any] = field(default_factory=dict)

    def apply(self, baseline_action: Dict[str, Any]) -> Dict[str, Any]:
        """Apply patch to a deep copy of baseline action, returning modified action."""
        new_action = copy.deepcopy(baseline_action)
        
        # 1. Apply worker mutations
        for worker_id, cmd in self.worker_mutations.items():
            if worker_id == 0:
                new_action["farmer"] = list(cmd)
            else:
                hands = new_action.setdefault("hands", [])
                h_idx = worker_id - 1
                while len(hands) <= h_idx:
                    hands.append(["PASS"])
                hands[h_idx] = list(cmd)
                
        # 2. Apply market mutations
        if self.market_mutations is not None:
            new_action["market"] = copy.deepcopy(self.market_mutations)[:10]
            
        return new_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "opportunity_id": self.source_opportunity_id,
            "mechanism_family": self.mechanism_family,
            "workers_modified": list(self.worker_mutations.keys()),
            "market_modified": self.market_mutations is not None,
            "horizon": self.expected_horizon,
            "rationale": self.rationale,
            "affected_obligations": list(self.affected_obligations),
            "conversion_metadata": dict(self.conversion_metadata),
        }

