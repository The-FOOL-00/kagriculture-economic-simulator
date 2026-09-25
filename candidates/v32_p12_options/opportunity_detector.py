# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Opportunity Detector.

Evaluates observable macroeconomic features to determine if a strategic
deviation from A7 should be considered, filtering out non-actionable steps
to preserve inference budget (<200 ms).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from option_library import OPTION_LIBRARY, OptionContract
    from candidates.v32_rlx2.state import EconomicFeatures
except ImportError:
    from candidates.v32_p12_options.option_library import OPTION_LIBRARY, OptionContract
    from candidates.v32_rlx2.state import EconomicFeatures


@dataclass
class DetectionResult:
    detected: bool
    candidate_options: List[OptionContract]
    reasons: List[str]


class OpportunityDetector:
    """Lightweight observable event detector for mid-game macroeconomic opportunities."""
    def __init__(self, option_library: Optional[Dict[str, OptionContract]] = None):
        self.library = option_library or OPTION_LIBRARY

    def detect(self, features: EconomicFeatures, step: int) -> DetectionResult:
        """Inspects current economic state and returns legal candidate options with evidence."""
        # Hard bounds: Quarantine terminal physical steps (>700) and step 0
        if step < 24 or step > 700:
            return DetectionResult(detected=False, candidate_options=[], reasons=["OUT_OF_BOUNDS_STEP"])

        candidates: List[OptionContract] = []
        reasons: List[str] = []

        # Check each option's observable trigger
        for opt_id, opt in self.library.items():
            if opt.is_triggered(features, step):
                candidates.append(opt)
                reasons.append(f"{opt_id}_{opt.name}_TRIGGERED")

        detected = len(candidates) > 0
        return DetectionResult(
            detected=detected,
            candidate_options=candidates,
            reasons=reasons
        )
