"""
EXP-DEV-001 CANDIDATE TREATMENT: DEV-001 DYNAMIC PORTFOLIO ADAPTATION
=====================================================================
Preregistered Candidate: dev_001_dynamic_portfolio
Hypothesis (H1): Conditioning crop planting on revealed town shops at Day 3 (Step 72)
and Day 6 (Step 144) to switch allocation to complementary crops (e.g. carrots on Pet Cafe
worlds, wheat on Bakery worlds) achieves a mean paired margin > +$50.00 over static 19S/0T
in ClosedLoopAgentV2 with non-inferior 5th percentile downside risk.
=====================================================================
"""

import copy
import os
import sys
from typing import Dict, List, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
dmitrii_dir = os.path.join(base_dir, "extracted_agents", "dmitrii_lb2800")
if dmitrii_dir not in sys.path:
    sys.path.insert(0, dmitrii_dir)

from closed_loop_v2 import ClosedLoopAgentV2
from router_parent import FarmView, DayState, SHOP_PLANS, ROUTE_STEP, FINAL_PLAN_STEP, LAST_STEP, MAX_ORDERS

STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
CARROT_SHOPS = {"PET_CAFE"}
WHEAT_SHOPS = {"BAKERY"}
TOMATO_SHOPS = {"PIZZA_SHOP"}
YARN_SHOPS = {"YARN_STORE"}


class Dev001DynamicPortfolioAgent(ClosedLoopAgentV2):
    """
    Evidence-Locked Dynamic Crop Portfolio Agent (dev_001_dynamic_portfolio).
    Conditions crop planting decisions dynamically on revealed town shops at Day 3 (Step 72)
    and Day 6 (Step 144) using only legal contemporaneous observations.
    """

    def __init__(
        self,
        jit_headroom_threshold: int = 96,
        base_liquidity_reserve: float = 500.0,
        enable_market_timing: bool = True,
        carrot_sale_batch: int = 6,
        tomato_sale_batch: int = 6,
    ):
        super().__init__(
            jit_headroom_threshold=jit_headroom_threshold,
            base_liquidity_reserve=base_liquidity_reserve,
            enable_market_timing=enable_market_timing,
        )
        self.carrot_sale_batch = carrot_sale_batch
        self.tomato_sale_batch = tomato_sale_batch
        self.mode_selected = {}  # player -> "STRAWBERRY", "CARROT", "WHEAT", "TOMATO", "YARN"
        self.crops_substituted = {"CARROT": 0, "TOMATO": 0, "WHEAT": 0}

    def _determine_crop_mode(self, unlocked_shops: List[str]) -> str:
        """Condition mode on revealed shops at decision checkpoints (Steps 72 & 144)."""
        if not unlocked_shops:
            return "STRAWBERRY"

        # 1. Yarn worlds always route to Dmitrii's calibrated Yarn plans
        if any(s in YARN_SHOPS for s in unlocked_shops):
            return "YARN"

        # 2. Strawberry shops lock in Strawberry Bedrock (highest proven baseline)
        if any(s in STRAWBERRY_SHOPS for s in unlocked_shops):
            return "STRAWBERRY"

        # 3. Pet Cafe worlds: Carrot complementary production
        if any(s in CARROT_SHOPS for s in unlocked_shops):
            return "CARROT"

        # 4. Bakery worlds: Wheat complementary specialization
        if any(s in WHEAT_SHOPS for s in unlocked_shops):
            return "WHEAT"

        # 5. Pizza worlds: Tomato specialization
        if any(s in TOMATO_SHOPS for s in unlocked_shops):
            return "TOMATO"

        return "STRAWBERRY"

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs.get("step", 0))
        player = int(obs.get("player", 0))
        day = step // 24
        unlocked_shops = obs.get("town", {}).get("unlocked_shops", [])

        # Checkpoint 1: Day 3 (Step 72) - First shop unlocked
        if step == 72:
            self.mode_selected[player] = self._determine_crop_mode(unlocked_shops[:1])

        # Checkpoint 2: Day 6 (Step 144) - Second shop unlocked
        elif step == 144:
            self.mode_selected[player] = self._determine_crop_mode(unlocked_shops[:2])

        mode = self.mode_selected.get(player, "STRAWBERRY")

        # 1. Base ClosedLoopAgentV2 action
        action = super().act(obs)

        # 2. If mode is default Strawberry or Yarn, preserve V2 bedrock exactly
        if mode in ("STRAWBERRY", "YARN"):
            return action

        view = FarmView(obs)
        feed_reserve = self._compute_feed_reserve(obs, player)

        # ----------------------------------------------------------------------
        # DYNAMIC COMPLEMENTARY CROP ADAPTATIONS
        # ----------------------------------------------------------------------

        # A. CARROT MODE (Pet Cafe Worlds)
        if mode == "CARROT":
            # On secondary planting days (Days 18 to 26, steps 432 to 647):
            # Substitute secondary Wheat buys and plants with Carrot, protecting feed reserve
            if 432 <= step <= 647:
                wheat_held = view.shed.get("WHEAT", 0)
                if wheat_held >= feed_reserve + 10:
                    new_market = []
                    for m in action.get("market", []):
                        if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "WHEAT":
                            new_market.append(["BUY_SEED", "CARROT", m[2]])
                            self.crops_substituted["CARROT"] += int(m[2])
                        else:
                            new_market.append(m)
                    action["market"] = new_market[:MAX_ORDERS]

                    # Substitute plant actions
                    if (
                        action.get("farmer")
                        and action["farmer"][0] == "PLANT"
                        and len(action["farmer"]) > 1
                        and action["farmer"][1] == "WHEAT"
                    ):
                        action["farmer"] = ["PLANT", "CARROT"]

                    for i, h in enumerate(action.get("hands", [])):
                        if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "WHEAT":
                            action["hands"][i] = ["PLANT", "CARROT"]

            # Active carrot market sales on step % 4 == 1 (post-pull timing)
            if day >= 18 and step % 4 == 1 and len(action.get("market", [])) < MAX_ORDERS:
                shed_carrots = view.shed.get("CARROT", 0)
                if shed_carrots > 0:
                    has_carrot_sell = any(
                        m and m[0] == "SELL" and m[1] == "CARROT" for m in action.get("market", [])
                    )
                    if not has_carrot_sell:
                        batch = min(shed_carrots, self.carrot_sale_batch)
                        action["market"].append(["SELL", "CARROT", batch])

        # B. WHEAT MODE (Bakery Worlds)
        elif mode == "WHEAT":
            # Bakery pulls 1 wheat every 4 steps.
            # On Day 19+, sell surplus wheat strictly above feed reserve on step % 4 == 1
            if day >= 12 and step % 4 == 1 and len(action.get("market", [])) < MAX_ORDERS:
                wheat_held = view.shed.get("WHEAT", 0)
                surplus_wheat = wheat_held - feed_reserve
                if surplus_wheat > 5:
                    has_wheat_sell = any(
                        m and m[0] == "SELL" and m[1] == "WHEAT" for m in action.get("market", [])
                    )
                    if not has_wheat_sell:
                        batch = min(surplus_wheat, 5)
                        action["market"].append(["SELL", "WHEAT", batch])
                        self.crops_substituted["WHEAT"] += batch

        # C. TOMATO MODE (Pizza Worlds without Strawberry)
        elif mode == "TOMATO":
            # Day 11 (steps 264 to 287): Substitute strawberry seed purchases with tomato
            if 264 <= step <= 287:
                new_market = []
                for m in action.get("market", []):
                    if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "STRAWBERRY":
                        new_market.append(["BUY_SEED", "TOMATO", m[2]])
                        self.crops_substituted["TOMATO"] += int(m[2])
                    else:
                        new_market.append(m)
                action["market"] = new_market[:MAX_ORDERS]

                if (
                    action.get("farmer")
                    and action["farmer"][0] == "PLANT"
                    and len(action["farmer"]) > 1
                    and action["farmer"][1] == "STRAWBERRY"
                ):
                    action["farmer"] = ["PLANT", "TOMATO"]

                for i, h in enumerate(action.get("hands", [])):
                    if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY":
                        action["hands"][i] = ["PLANT", "TOMATO"]

            # Active tomato market sales on step % 4 == 1
            if day >= 19 and step % 4 == 1 and len(action.get("market", [])) < MAX_ORDERS:
                shed_tom = view.shed.get("TOMATO", 0)
                if shed_tom > 0:
                    has_tom_sell = any(
                        m and m[0] == "SELL" and m[1] == "TOMATO" for m in action.get("market", [])
                    )
                    if not has_tom_sell:
                        batch = min(shed_tom, self.tomato_sale_batch)
                        action["market"].append(["SELL", "TOMATO", batch])

        return action
