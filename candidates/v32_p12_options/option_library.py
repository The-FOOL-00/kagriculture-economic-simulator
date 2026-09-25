# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Option Library & Option Contracts.

Defines the formal OptionContract schema, governance statuses, and the explicit
library of discrete macroeconomic options (O01..O06).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class OptionStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SCREENED = "SCREENED"
    QUALIFIED = "QUALIFIED"
    PROMOTED = "PROMOTED"
    QUARANTINED = "QUARANTINED"
    RETIRED = "RETIRED"


@dataclass
class OptionContract:
    """Formal contract governing a discrete macroeconomic option intervention."""
    option_id: str
    name: str
    candidate_action: int
    duration: int = 4
    
    # Economics & Triggers
    trigger_description: str = ""
    expected_mechanism: str = ""
    min_cash_required: float = 0.0
    earliest_step: int = 0
    latest_step: int = 718
    
    # Performance & Safety Metrics
    expected_delta: float = 0.0
    validated_delta: float = 0.0
    worst_case_delta: float = 0.0
    
    # Invariants & Governance
    required_resync_status: str = "SYNCED"
    termination_condition: str = "4_TICKS_OR_DESYNC_OR_INSOLVENCY"
    promotion_status: OptionStatus = OptionStatus.DISCOVERED
    activation_count: int = 0
    
    # Functional Trigger Check
    trigger_fn: Optional[Callable[[Dict[str, Any], int], bool]] = None

    def is_triggered(self, features: Any, step: int) -> bool:
        if self.promotion_status in (OptionStatus.QUARANTINED, OptionStatus.RETIRED):
            return False
        if step < self.earliest_step or step > self.latest_step:
            return False
        if getattr(features, "cash", 0.0) < self.min_cash_required:
            return False
        if self.trigger_fn:
            return self.trigger_fn(features, step)
        return True


# ==============================================================================
# OPTION LIBRARY DEFINITIONS (O01 - O06)
# ==============================================================================

def trigger_o01_expand_land(features: Any, step: int) -> bool:
    """O01 Trigger: Mid-game capital expansion when:
    1. Quadrants == 3 (4th quadrant unlock available)
    2. Step in [288, 336] (Day 12 to Day 14: post-livestock completion)
    3. Cash >= 14,000.0 (strong capital buffer: $4k land + $10k working capital)
    4. 'BAKERY' in unlocked_shops (guaranteed town grain demand)
    """
    quads = getattr(features, "unlocked_quadrants", 1)
    cash = getattr(features, "cash", 0.0)
    shops = getattr(features, "unlocked_shops", [])
    
    return (
        quads == 3
        and 288 <= step <= 336
        and cash >= 14000.0
        and "BAKERY" in shops
    )


OPTION_LIBRARY: Dict[str, OptionContract] = {
    "O01": OptionContract(
        option_id="O01",
        name="EXPAND_LAND",
        candidate_action=9,
        duration=4,
        trigger_description="Quads==3, Step in [288, 336], Cash >= $14,000, 'BAKERY' in shops",
        expected_mechanism="Unlocks 25 arable plots on Day 12 when town Bakery demand absorbs high crop yield",
        min_cash_required=14000.0,
        earliest_step=288,
        latest_step=336,
        expected_delta=16226.0,
        promotion_status=OptionStatus.QUALIFIED,
        trigger_fn=trigger_o01_expand_land
    ),
    "O02": OptionContract(
        option_id="O02",
        name="CROP_EXPANSION_MELON",
        candidate_action=4,
        duration=4,
        trigger_description="QUARANTINED: False positive risk disrupting feed supply",
        expected_mechanism="Preempts wheat plantings required for livestock feeding",
        min_cash_required=0.0,
        earliest_step=0,
        latest_step=0,
        expected_delta=0.0,
        promotion_status=OptionStatus.QUARANTINED,
        trigger_fn=lambda f, s: False
    ),
    "O03": OptionContract(
        option_id="O03",
        name="LIQUIDATE_SURPLUS",
        candidate_action=3,
        duration=4,
        trigger_description="QUARANTINED: Low alpha, high inventory volatility",
        expected_mechanism="Marginal liquidity benefit",
        min_cash_required=0.0,
        earliest_step=0,
        latest_step=0,
        expected_delta=0.0,
        promotion_status=OptionStatus.QUARANTINED,
        trigger_fn=lambda f, s: False
    ),
    "O04": OptionContract(
        option_id="O04",
        name="OPPORTUNISTIC_SELL",
        candidate_action=1,
        duration=4,
        trigger_description="QUARANTINED: High variance market timing",
        expected_mechanism="Price decay hazard",
        min_cash_required=0.0,
        earliest_step=0,
        latest_step=0,
        expected_delta=0.0,
        promotion_status=OptionStatus.QUARANTINED,
        trigger_fn=lambda f, s: False
    ),
    "O05": OptionContract(
        option_id="O05",
        name="PRESERVE_CASH",
        candidate_action=8,
        duration=4,
        trigger_description="QUARANTINED: Fatal tail risk canceling early hires (-$55k)",
        expected_mechanism="Labor starvation",
        min_cash_required=0.0,
        earliest_step=0,
        latest_step=0,
        expected_delta=-55000.0,
        promotion_status=OptionStatus.QUARANTINED,
        trigger_fn=lambda f, s: False
    ),
    "O06": OptionContract(
        option_id="O06",
        name="SELECTIVE_PREEMPT_SELL",
        candidate_action=2,
        duration=4,
        trigger_description="QUARANTINED: P10 R01 lineage preemption failure",
        expected_mechanism="Negative price slippage",
        min_cash_required=0.0,
        earliest_step=0,
        latest_step=0,
        expected_delta=0.0,
        promotion_status=OptionStatus.QUARANTINED,
        trigger_fn=lambda f, s: False
    ),
}
