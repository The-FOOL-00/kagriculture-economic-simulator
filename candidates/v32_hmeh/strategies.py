# SPDX-License-Identifier: MIT
"""HMEH Strategic Intent and Candidate Strategy Definitions.

Defines the contract between the Macro Planner (Tier 1) and Chore Executor (Tier 2).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StrategicIntent:
    # High-level strategic objective description
    objective: str
    
    # Labor Targets
    target_worker_count: int
    
    # Crop Portfolio Allocation (desired seed purchases & plant counts)
    crop_targets: Dict[str, int]
    
    # Livestock Targets
    cow_target: int
    sheep_target: int
    
    # Capital Floors
    min_cash_reserve: float
    
    # Land Expansion Milestones
    land_expansion_target: int       # 0, 1, or 2 (number of expansions)
    
    # Market Directives
    market_orders: List[List[Any]]   # e.g. [["BUY_PRODUCT", "WHEAT", 30], ...]
    
    # Operational Fallback Regime ("NORMAL", "CAUTION", "RECOVERY", "LIQUIDATION")
    fallback_mode: str = "NORMAL"
    
    # Stage Identifier for Ablation ("HMEH-0", "HMEH-1", "HMEH-2", "HMEH-3", "HMEH-4")
    stage: str = "HMEH-0"
    
    # Metadata for Diagnostics & Forensics
    reason: str = ""
    event_trigger: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
