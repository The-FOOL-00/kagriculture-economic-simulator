# SPDX-License-Identifier: MIT
"""V31R2 E2: SPLIT — frozen A7 + per-order SELL truncation (no price logic).

One mechanism: cap every SELL order quantity at K units (default 10).
Step-0 wash exempt (keeps +1286 signature). Frozen bytes untouched.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from aec.backbone.v27_ablation_adapters import V27AblationAdapter
from aec.backbone.utils import _get, _int


class V31R2SplitAdapter(V27AblationAdapter):
    def __init__(self, cap: int = 10) -> None:
        self.cap = cap
        self.splits = 0
        super().__init__(variant="V27-ABL-A7")

    def identity(self) -> str:
        return "V31R2-SPLIT-K%d" % self.cap

    def act(self, observation: Dict[str, Any],
            configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        action = super().act(observation, configuration)
        step = _int(_get(observation, "step", 0))
        if step == 0:
            return action
        mkt = action.get("market") or []
        if not mkt:
            return action
        out = []
        for o in mkt:
            if (isinstance(o, list) and o and o[0] == "SELL" and len(o) >= 3
                    and isinstance(o[2], int) and o[2] > self.cap):
                o = [o[0], o[1], self.cap] + list(o[3:])
                self.splits += 1
            out.append(o)
        action["market"] = out
        return copy.deepcopy(action)
