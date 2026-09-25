# SPDX-License-Identifier: MIT
"""V31R2 E3: wash variants — frozen V3 + step-0 wash rewrite to size W.

Same rewrite mechanics as A7 (V27-ABL-A7), different target wash.
Washes: W72=[[BUY 7],[SELL 2]], W2015=20/15, W10=10/10, W5=5/5.
Optional SPLIT10 truncation composes (wash+SPLIT bouts).
Frozen bytes untouched.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from aec.backbone.v27_ablation_adapters import V27AblationAdapter, WASH50
from aec.backbone.utils import _get, _int

WASHES = {
    "W72": [["BUY_PRODUCT", "WHEAT", 7], ["SELL", "WHEAT", 2]],
    "W2015": [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15]],
    "W10": [["BUY_PRODUCT", "WHEAT", 10], ["SELL", "WHEAT", 10]],
    "W5": [["BUY_PRODUCT", "WHEAT", 5], ["SELL", "WHEAT", 5]],
}


class V31R2WashAdapter(V27AblationAdapter):
    def __init__(self, wash: str = "W2015", split_cap: Optional[int] = None) -> None:
        assert wash in WASHES, wash
        self.wash_id = wash
        self.target = [list(o) for o in WASHES[wash]]
        self.split_cap = split_cap
        self.step0_rewritten_custom = False
        super().__init__(variant="V27-ABL-A7")
        # NOTE: parent __init__ sets rewrite_step0_wash=True (A7); we
        # override act() fully for step 0, so parent rewrite never fires.
        self.rewrite_step0_wash = False

    def identity(self) -> str:
        s = "V31R2-%s" % self.wash_id
        if self.split_cap:
            s += "-SPLIT%d" % self.split_cap
        return s

    def act(self, observation: Dict[str, Any],
            configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = _int(_get(observation, "step", 0))
        if step == self._last_called_step:
            raise RuntimeError(
                "CRITICAL AEC INVARIANT BREACH: Baseline agent invoked twice for step %d!"
                % step
            )
        raw = self._v3_agent_callable(observation, configuration)
        if not isinstance(raw, dict):
            raw = {"farmer": ["PASS"], "hands": [], "market": []}
        else:
            raw = dict(raw)
        if step == 0:
            if raw.get("market") == WASH50:
                raw["market"] = [list(o) for o in self.target]
                self.step0_rewritten_custom = True
            else:
                self.step0_unexpected_shape = True
        elif self.split_cap:
            out = []
            for o in (raw.get("market") or []):
                if (isinstance(o, list) and o and o[0] == "SELL" and len(o) >= 3
                        and isinstance(o[2], int) and o[2] > self.split_cap):
                    o = [o[0], o[1], self.split_cap] + list(o[3:])
                out.append(o)
            raw["market"] = out
        self._call_count += 1
        # NOTE: parent double-call guard uses _last_called_step; mirror it.
        self._last_called_step = step
        return copy.deepcopy(raw)
