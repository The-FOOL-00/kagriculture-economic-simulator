# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Main Submission Entrypoint.

Sparse Option Architecture on top of protected A7 incumbent.
Default policy is A7; discrete macroeconomic options are sparse, short (H=4),
and strictly gated by physical synchronization and positive post-resync alpha.
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from selector import SparseOptionController, OptionControllerConfig
    from incumbent import verify_a7_integrity
except ImportError:
    from candidates.v32_p12_options.selector import SparseOptionController, OptionControllerConfig
    from candidates.v32_p12_options.incumbent import verify_a7_integrity

_CONTROLLER: Optional[SparseOptionController] = None


def get_controller() -> SparseOptionController:
    global _CONTROLLER
    if _CONTROLLER is None:
        verify_a7_integrity()
        cfg = OptionControllerConfig(
            max_options_per_episode=1,
            min_separation_ticks=24,
            option_horizon=4,
            require_full_sync=True,
            mode="oracle_search"
        )
        _CONTROLLER = SparseOptionController(cfg)
    return _CONTROLLER


def act(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle standard agent interface."""
    controller = get_controller()
    step = int(observation.get("step", 0) or 0)
    if step == 0:
        controller.reset()
    return controller.act(observation, configuration)


# Alias for Kaggle runner
agent = act
