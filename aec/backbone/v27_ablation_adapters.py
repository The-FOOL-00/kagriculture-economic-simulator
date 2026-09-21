# SPDX-License-Identifier: MIT
"""V27 research-variant adapters (A1/A2/A3 + V3 sanity control).

Planner-level single-factor variants of the frozen V25 P3 program.
P3's ONLY behavioral deltas vs V3 are (1) the step-0 bypass+wash and
(2) the PASS->WATER/DIG dispatch; these flags isolate them:

  A1  call_v3_at_step0=True,  open_units=30, dispatch=True   (V3 opening)
  A2  call_v3_at_step0=False, open_units=50, dispatch=True   (V3 quantity)
  A3  call_v3_at_step0=False, open_units=30, dispatch=False  (V3 labor)
  V3S call_v3_at_step0=True,  open_units=30, dispatch=False  (= V3 exactly)

Labels are V27-ABL-*; nothing here is "V25 P3". The frozen P3 source,
the V26 adapters, and V22R1 are untouched. Coherent by construction:
no tape mutation, no action splicing; A3 emits V3's own actions and A1
feeds V3 its natural step-0 input.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from aec.backbone.interface import ContinuationPolicy
from aec.backbone.utils import _get, _int
from aec.backbone.v25_p3_adapter import (
    V25P3BackboneAdapter,
    apply_p3_labor_dispatch,
)
from aec.backbone.v3_adapter import snapshot_v3_globals, restore_v3_globals
from aec.backbone.utils import build_simulated_observation
from aec.config import AECConfig

VARIANT_IDS = ("V27-ABL-A1", "V27-ABL-A2", "V27-ABL-A3", "V27-ABL-V3S",
               "V27-ABL-A7")


WASH50 = [["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]
WASH30 = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]


class V27AblationContinuation(ContinuationPolicy):
    def __init__(self, v3_agent_callable: Any, call_v3_at_step0: bool,
                 open_units: int, dispatch: bool,
                 rewrite_step0_wash: bool = False) -> None:
        self.v3_agent_callable = v3_agent_callable
        self.call_v3_at_step0 = call_v3_at_step0
        self.open_units = open_units
        self.dispatch = dispatch
        self.rewrite_step0_wash = rewrite_step0_wash

    def step_action(self, rollout: Any, player: int = 0) -> Dict[str, Any]:
        if rollout.step == 0 and not self.call_v3_at_step0:
            return {
                "farmer": ["PASS"],
                "hands": [],
                "market": [["BUY_PRODUCT", "WHEAT", self.open_units],
                           ["SELL", "WHEAT", self.open_units]],
            }
        obs = build_simulated_observation(rollout, player=player)
        try:
            action = self.v3_agent_callable(obs)
        except TypeError:
            try:
                action = self.v3_agent_callable(obs, None)
            except Exception:
                action = {"farmer": ["PASS"], "hands": [], "market": []}
        if not isinstance(action, dict):
            action = {"farmer": ["PASS"], "hands": [], "market": []}
        if self.rewrite_step0_wash and rollout.step == 0 and \
                action.get("market") == WASH50:
            action = dict(action)
            action["market"] = [list(o) for o in WASH30]
        # Dispatch applies on steps >= 1 only (P3 never dispatches at step 0,
        # and no waterable/diggable tiles exist at step 0 anyway).
        if self.dispatch and rollout.step != 0:
            return apply_p3_labor_dispatch(action, obs)
        return action

    def snapshot(self) -> Dict[str, Any]:
        return snapshot_v3_globals(self.v3_agent_callable)

    def restore(self, snap: Dict[str, Any]) -> None:
        restore_v3_globals(self.v3_agent_callable, snap)


class V27AblationAdapter(V25P3BackboneAdapter):
    """V25P3BackboneAdapter with research-variant flags."""

    def __init__(
        self,
        variant: str,
        tarball_path: Optional[str] = None,
        candidate_path: Optional[str] = None,
        config: Optional[AECConfig] = None,
    ) -> None:
        assert variant in VARIANT_IDS, variant
        self.variant = variant
        # A7 completes the qty x call/bypass square: V3 is called at step 0
        # (full step-0 processing: route/state init intact) and ONLY the two
        # wash orders are resized 50 -> 30 (asserted exact-shape; flagged if
        # V3 ever emits anything else at step 0). Coherent: V3's step-0
        # processing runs naturally; downstream state evolves from true
        # engine-mediated observations exactly as in P3's bypass.
        self.call_v3_at_step0 = variant in ("V27-ABL-A1", "V27-ABL-V3S",
                                            "V27-ABL-A7")
        self.open_units = 50 if variant == "V27-ABL-A2" else 30
        self.dispatch = variant in ("V27-ABL-A1", "V27-ABL-A2")
        self.rewrite_step0_wash = (variant == "V27-ABL-A7")
        self.step0_rewritten = False
        self.step0_unexpected_shape = False
        super().__init__(tarball_path=tarball_path,
                         candidate_path=candidate_path, config=config)

    def identity(self) -> str:
        return self.variant

    def version(self) -> str:
        return "1.0.0-v27-abl"

    def act(self, observation: Dict[str, Any],
            configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = _int(_get(observation, "step", 0))
        if step == self._last_called_step:
            raise RuntimeError(
                "CRITICAL AEC INVARIANT BREACH: Baseline agent invoked twice for step %d!"
                % step
            )
        if step == 0 and not self.call_v3_at_step0:
            action = {
                "farmer": ["PASS"],
                "hands": [],
                "market": [["BUY_PRODUCT", "WHEAT", self.open_units],
                           ["SELL", "WHEAT", self.open_units]],
            }
            self._call_count += 1
            self._last_called_step = step
            return copy.deepcopy(action)
        raw_action = self._v3_agent_callable(observation, configuration)
        if not isinstance(raw_action, dict):
            raw_action = {"farmer": ["PASS"], "hands": [], "market": []}
        if self.rewrite_step0_wash and step == 0:
            if raw_action.get("market") == WASH50:
                raw_action = dict(raw_action)
                raw_action["market"] = [list(o) for o in WASH30]
                self.step0_rewritten = True
            else:
                self.step0_unexpected_shape = True
        final_action = (apply_p3_labor_dispatch(raw_action, observation)
                        if (self.dispatch and step != 0) else raw_action)
        self._call_count += 1
        self._last_called_step = step
        return copy.deepcopy(final_action)

    def macro_fingerprint(self, observation: Dict[str, Any],
                          player: int = 0) -> Dict[str, Any]:
        fp = super().macro_fingerprint(observation, player=player)
        fp["backbone_id"] = self.identity()
        fp["open_units"] = self.open_units
        fp["dispatch"] = self.dispatch
        fp["call_v3_at_step0"] = self.call_v3_at_step0
        return fp

    def create_continuation_policy(self) -> ContinuationPolicy:
        return V27AblationContinuation(
            self._v3_agent_callable, self.call_v3_at_step0,
            self.open_units, self.dispatch, self.rewrite_step0_wash)
