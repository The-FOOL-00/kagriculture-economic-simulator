# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-003 CANDIDATE TREATMENT: CONDITIONAL OPPORTUNITY-VALUE SPECIALIZATION
=============================================================================
Candidate Identifier: dev_003_conditional_specialization
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_2.md
Frozen Baseline: candidates/compiled_v54_plus_residual.py
Baseline SHA-256: 18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb

Architectural Composition:
  Treatment = V54++ Residual Baseline + Opportunity-Value Conditional Gating Overlay

Default Invariant:
  In all ambiguous, unpromising, or unverified states, the treatment executes
  100% default V54++ baseline behavior.

Preservation Invariant:
  The overlay strictly preserves the residual-preemption engine
  (preempt_money_deficit = 2000.0, preempt_minimum_delta = 4.0, preempt_maximum_batch = 12),
  worker routes, animal management, and terminal realization.
=============================================================================
"""

import os
import sys
import copy
import importlib.util
from typing import Dict, List, Any, Optional

# Locate external repository sources and compiled baseline
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
BASELINE_PATH = os.path.join(base_dir, "candidates", "compiled_v54_plus_residual.py")

if not os.path.exists(BASELINE_PATH):
    raise FileNotFoundError(f"Authoritative baseline missing at {BASELINE_PATH}")

# Frozen Parameter Registration (Protocol V1.2 Section 7)
TAU = 1500.0                  # Opportunity-Value Threshold (coins)
LAMBDA_RISK = 0.25            # Risk Penalty Multiplier
L_MIN = 100.0                 # Minimum Liquidity Floor (coins)
K_SPEC = 4                    # Specialization Tile Allocation (tiles)
SWITCHING_FRICTION = 200.0    # Fixed Transition Friction (coins)

STRAWBERRY_SHOPS = frozenset({"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"})
PIZZA_SHOPS = frozenset({"PIZZA_SHOP"})
PET_SHOPS = frozenset({"PET_CAFE"})
BAKERY_SHOPS = frozenset({"BAKERY"})


class Dev003ConditionalSpecializationAgent:
    """
    Evidence-Locked Conditional Opportunity-Value Specialization Agent.
    Evaluates current-observation market and shop states at four observable checkpoints
    (Days 3, 6, 9, 12 / Steps 72, 144, 216, 288). Overrides crop planning ONLY when
    net incremental opportunity value exceeds tau and liquidity meets L_min.
    """

    def __init__(self, baseline_module=None, seat: int = 0, seed: int = 0):
        self.seat = seat
        self.seed = seed
        self.decision_events: List[Dict[str, Any]] = []
        self.mode = "BASELINE"
        self.specialized_crop: Optional[str] = None
        self.seeds_bought = 0
        self.tiles_planted = 0

        # Load an isolated baseline module instance to prevent shared state contamination
        if baseline_module is not None:
            self.baseline = baseline_module
        else:
            spec = importlib.util.spec_from_file_location(
                f"isolated_baseline_{id(self)}", BASELINE_PATH
            )
            self.baseline = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.baseline)

    def _assert_zero_leakage(self, obs: Dict[str, Any]):
        """Runtime assertion against future-state leakage and hidden variables."""
        forbidden_keys = {
            "future_shops", "terminal_score", "ground_truth", "future_market",
            "offline_trajectory", "oracle", "future_prices"
        }
        intersection = forbidden_keys.intersection(obs.keys())
        if intersection:
            raise RuntimeError(f"Zero-Leakage Violation: Forbidden future keys in obs: {intersection}")

    def evaluate_opportunity(self, obs: Dict[str, Any], step: int) -> Dict[str, Any]:
        """
        Preregistered Opportunity-Value Model (Protocol V1.2 Section 6.3).
        Computes net incremental expected value:
          Delta E[V] = (E[R_spec] - Cost_seed) - (E[R_base] - Cost_base) - R
        """
        farms = obs.get("farms", [])
        seat = int(obs.get("player", self.seat) or 0)
        farm = farms[seat] if seat < len(farms) else {}
        money = float(farm.get("money", 0.0) or 0.0)

        town = obs.get("town", {}) or {}
        unlocked_shops = list(town.get("unlocked_shops", []) or [])
        market = obs.get("market", {}) or {}
        prices = market.get("prices", {}) or {}
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}

        # Risk / Liquidity Penalty
        risk_penalty = LAMBDA_RISK * max(0.0, L_MIN - money) + SWITCHING_FRICTION

        # Effective price for baseline crop (Strawberry)
        has_straw_shop = any(s in STRAWBERRY_SHOPS for s in unlocked_shops)
        straw_spot = float(prices.get("STRAWBERRY", 120.0) or 120.0)
        p_eff_straw = straw_spot if has_straw_shop else (0.60 * straw_spot)

        # Baseline expected revenue for 4 tiles of Strawberry
        # Strawberry planted on Day 11 (step 264), takes 6 days (144 steps) to mature,
        # then yields 4 units every 2 days (48 steps).
        t_rem = 720 - max(step, 264)
        n_straw = max(0, (t_rem - 144) // 48 + 1) if t_rem >= 144 else 0
        e_r_base = K_SPEC * n_straw * 4 * p_eff_straw
        cost_base = K_SPEC * 100.0  # Seed cost for 4 Strawberry plants

        # Evaluate candidate crops corresponding to unlocked town shops
        best_crop = None
        best_delta = -999999.0
        best_e_r_spec = 0.0
        best_cost_seed = 0.0

        candidates = []
        if any(s in PIZZA_SHOPS for s in unlocked_shops):
            candidates.append("TOMATO")
        if any(s in PET_SHOPS for s in unlocked_shops):
            candidates.append("CARROT")
        if any(s in BAKERY_SHOPS for s in unlocked_shops):
            candidates.append("WHEAT")

        for crop in candidates:
            if crop == "TOMATO":
                tom_spot = float(prices.get("TOMATO", 60.0) or 60.0)
                p_eff = min(60.0, tom_spot)
                # Tomato: takes 5 days (120 steps) to mature, yields 4 units every 1 day (24 steps)
                n_tom = max(0, (t_rem - 120) // 24 + 1) if t_rem >= 120 else 0
                e_r_spec = K_SPEC * n_tom * 4 * p_eff
                cost_seed = K_SPEC * 50.0
            elif crop == "CARROT":
                car_spot = float(prices.get("CARROT", 35.0) or 35.0)
                p_eff = min(35.0, car_spot)
                # Carrot: takes 3 days (72 steps), yields 4 units, replanted
                n_cycles = max(0, t_rem // 72)
                e_r_spec = K_SPEC * n_cycles * 4 * p_eff
                cost_seed = K_SPEC * n_cycles * 20.0
            elif crop == "WHEAT":
                wht_spot = float(prices.get("WHEAT", 25.0) or 25.0)
                p_eff = min(25.0, wht_spot)
                # Wheat: takes 2 days (48 steps), yields 4 units, replanted
                n_cycles = max(0, t_rem // 48)
                e_r_spec = K_SPEC * n_cycles * 4 * p_eff
                cost_seed = K_SPEC * n_cycles * 10.0
            else:
                continue

            delta = (e_r_spec - cost_seed) - (e_r_base - cost_base) - risk_penalty
            if delta > best_delta:
                best_delta = delta
                best_crop = crop
                best_e_r_spec = e_r_spec
                best_cost_seed = cost_seed

        # Activation Gate Rule (Protocol V1.2 Section 6.4)
        if self.mode == "SPECIALIZE":
            decision = "SPECIALIZE"
            resulting_plan = f"SPECIALIZE_{self.specialized_crop}"
        elif best_delta >= TAU and money >= L_MIN:
            decision = "SPECIALIZE"
            resulting_plan = f"SPECIALIZE_{best_crop}"
        else:
            decision = "BASELINE"
            resulting_plan = "BASELINE_V54"

        # Telemetry record (Protocol V1.2 Section 17)
        telemetry = {
            "seed": self.seed,
            "step": step,
            "observed_shops": ";".join(unlocked_shops) if unlocked_shops else "NONE",
            "cash": money,
            "inventory": dict(shed),
            "baseline_recommendation": "STRAWBERRY_BEDROCK",
            "specialization_recommendation": best_crop or "NONE",
            "expected_specialization_value": best_e_r_spec,
            "expected_baseline_value": e_r_base,
            "incremental_value": best_delta,
            "risk_penalty": risk_penalty,
            "liquidity_state": "SUFFICIENT" if money >= L_MIN else "CONSTRAINED",
            "decision": decision,
            "resulting_plan": resulting_plan,
        }
        self.decision_events.append(telemetry)
        return telemetry

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main decision loop. Executes baseline V54++ and applies conditional overlay.
        """
        self._assert_zero_leakage(obs)

        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)

        seat = int(obs.get("player", self.seat) or 0)
        self.seat = seat

        # Checkpoints: Days 3, 6, 9, 12 (Steps 72, 144, 216, 288)
        if step in (72, 144, 216, 288):
            res = self.evaluate_opportunity(obs, step)
            if res["decision"] == "SPECIALIZE" and self.mode != "SPECIALIZE":
                self.mode = "SPECIALIZE"
                self.specialized_crop = res["specialization_recommendation"]

        # 1. Execute baseline policy (full V54++ residual architecture)
        base_action = self.baseline.agent(obs)

        # 2. If BASELINE, return untouched baseline action
        if self.mode != "SPECIALIZE" or not self.specialized_crop:
            return base_action

        # 3. Apply Specialization Overlay (preserves all non-crop actions)
        action = copy.deepcopy(base_action)
        crop = self.specialized_crop

        # Day 11 (steps 264-287): Substitute up to K_SPEC Strawberry seeds and plantings
        if 264 <= step <= 287:
            # Seed purchase substitution
            new_market = []
            for order in action.get("market", []):
                if (
                    isinstance(order, list)
                    and len(order) >= 3
                    and order[0] == "BUY_SEED"
                    and order[1] == "STRAWBERRY"
                ):
                    qty = int(order[2])
                    can_sub = min(qty, max(0, K_SPEC - self.seeds_bought))
                    if can_sub > 0:
                        new_market.append(["BUY_SEED", crop, can_sub])
                        self.seeds_bought += can_sub
                        rem = qty - can_sub
                        if rem > 0:
                            new_market.append(["BUY_SEED", "STRAWBERRY", rem])
                    else:
                        new_market.append(order)
                else:
                    new_market.append(order)
            action["market"] = new_market[:10]

            # Planting substitution
            farmer_cmd = action.get("farmer")
            if (
                isinstance(farmer_cmd, list)
                and len(farmer_cmd) >= 2
                and farmer_cmd[0] == "PLANT"
                and farmer_cmd[1] == "STRAWBERRY"
            ):
                if self.tiles_planted < K_SPEC:
                    action["farmer"] = ["PLANT", crop]
                    self.tiles_planted += 1

            for i, hand_cmd in enumerate(action.get("hands", [])):
                if (
                    isinstance(hand_cmd, list)
                    and len(hand_cmd) >= 2
                    and hand_cmd[0] == "PLANT"
                    and hand_cmd[1] == "STRAWBERRY"
                ):
                    if self.tiles_planted < K_SPEC:
                        action["hands"][i] = ["PLANT", crop]
                        self.tiles_planted += 1

        # Post-maturity monetization: sell harvested specialized crop on step % 4 == 1
        farms = obs.get("farms", [])
        farm = farms[seat] if seat < len(farms) else {}
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        crop_qty = int(shed.get(crop, 0) or 0)

        if step >= 360 and step % 4 == 1 and crop_qty > 0 and len(action.get("market", [])) < 10:
            has_sell = any(
                isinstance(m, list) and len(m) >= 2 and m[0] == "SELL" and m[1] == crop
                for m in action.get("market", [])
            )
            if not has_sell:
                batch = min(crop_qty, 4)
                action["market"].append(["SELL", crop, batch])

        # Terminal liquidation at step 718 for specialized crop
        if step == 718 and crop_qty > 0 and len(action.get("market", [])) < 10:
            has_sell = any(
                isinstance(m, list) and len(m) >= 2 and m[0] == "SELL" and m[1] == crop
                for m in action.get("market", [])
            )
            if not has_sell:
                action["market"].append(["SELL", crop, crop_qty])

        return action


# Module-level agent factory and callable for Kaggle compatibility
_ACTIVE_AGENTS = {}


def agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    step = int(obs.get("step", 0) or 0)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _ACTIVE_AGENTS or step == 0:
        _ACTIVE_AGENTS[seat] = Dev003ConditionalSpecializationAgent(seat=seat)
    return _ACTIVE_AGENTS[seat].act(obs)


def kaggle_agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return agent(obs, configuration)
