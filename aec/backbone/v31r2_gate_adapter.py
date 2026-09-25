# SPDX-License-Identifier: MIT
"""V31R2 A8-GATE: frozen A7 + price gate on SELL orders (E1 pilot).

One mechanism: drop SELL orders priced below BASE*F (goods wait in shed
for town-recovered windows). Step-0 wash exempt (keeps +1286 signature).
FERTILIZER exempt (no town drain; holding it would clog the shed).
Frozen A7/V3/V22R1 bytes untouched; this subclasses the A7 adapter.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from aec.backbone.v27_ablation_adapters import V27AblationAdapter
from aec.backbone.utils import _get, _int

BASE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
        "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200,
        "FERTILIZER": 100}


class V31R2GateAdapter(V27AblationAdapter):
    def __init__(self, gate_frac: float = 0.5) -> None:
        self.gate_frac = gate_frac
        self.gate_drops = 0
        self.gate_keeps = 0
        super().__init__(variant="V27-ABL-A7")

    def identity(self) -> str:
        return "V31R2-GATE-F%g" % self.gate_frac

    def act(self, observation: Dict[str, Any],
            configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        action = super().act(observation, configuration)
        step = _int(_get(observation, "step", 0))
        if step == 0:
            return action
        mkt = action.get("market") or []
        if not mkt:
            return action
        prices = ((observation.get("market") or {}).get("prices")) or {}
        kept = []
        for o in mkt:
            if (isinstance(o, list) and o and o[0] == "SELL" and len(o) >= 3
                    and o[1] != "FERTILIZER" and o[1] in BASE):
                px = prices.get(o[1])
                if px is not None and px >= BASE[o[1]] * self.gate_frac:
                    kept.append(o)
                    self.gate_keeps += 1
                else:
                    self.gate_drops += 1
            else:
                kept.append(o)
        action["market"] = kept
        return copy.deepcopy(action)
