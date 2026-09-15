"""
CLOSED-LOOP V3: Information-Aware Economic Portfolio Controller.
Replaces naive demand specialization with mathematically principled multi-stage information gating:
1. Retains all proven physical invariants from V2:
   - JIT Shed Headroom Protection (purges when projected_shed > 96 to prevent silent discards).
   - Dawn Workforce Hiring Priority Arbitration (order slots 0-9).
   - Strict Non-Cannibalization Feed Reserve (wheat reserve >= 3 * animals).
   - Physical 61-fertilization bedrock and zero worker collision.
2. Complete Strawberry Demand Coverage:
   - Correctly includes all 4 strawberry-demanding shops:
     SMOOTHIE_SHOP, ICE_CREAM_SHOP, BRUNCH_SPOT, and FARMERS_MARKET.
3. Multi-Stage Information-Aware Gating:
   - Step 144 (Day 6): Evaluates first 2 shops. If YARN_STORE present -> routes to Dmitrii's calibrated Yarn Plans 3-12.
   - Step 216 (Day 9): Evaluates Shop 3. If any strawberry shop is present -> locks into 100% Strawberry Bedrock.
   - Step 264 (Day 11): Pre-planting decision. Only deploys Tomato module if PIZZA_SHOP is present AND ZERO strawberry-demanding shops are present across all 3 currently unlocked shops.
4. High-Efficiency Market Execution:
   - Sells specialty crops strictly on step % 4 == 1 in batches of 4-6 units to capture post-consumption price peaks.
   - Liquidates remaining crops on Step 719.
"""
import copy
import json
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

STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
TOMATO_SHOPS = {"PIZZA_SHOP"}

class ClosedLoopAgentV3(ClosedLoopAgentV2):
    def __init__(
        self,
        jit_headroom_threshold: int = 96,
        tomato_sale_batch: int = 6,
        base_liquidity_reserve: float = 500.0
    ):
        super().__init__(
            jit_headroom_threshold=jit_headroom_threshold,
            base_liquidity_reserve=base_liquidity_reserve
        )
        self.tomato_sale_batch = tomato_sale_batch
        self.specialization_mode = {} # player -> "STRAWBERRY" or "TOMATO" or "YARN"

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs["step"])
        player = int(obs["player"])
        day = step // 24
        
        # 1. Multi-Stage Information Evaluation
        if step == 144:
            shops = obs.get("town", {}).get("unlocked_shops", [])
            has_yarn = any(s == "YARN_STORE" for s in shops[:2])
            has_straw = any(s in STRAWBERRY_SHOPS for s in shops[:2])
            has_pizza = any(s in TOMATO_SHOPS for s in shops[:2])
            
            if has_yarn:
                self.specialization_mode[player] = "YARN"
            elif has_straw:
                self.specialization_mode[player] = "STRAWBERRY"
            elif has_pizza:
                # Tentative tomato mode, subject to Day 9 check
                self.specialization_mode[player] = "TENTATIVE_TOMATO"
            else:
                self.specialization_mode[player] = "STRAWBERRY"
                
        elif step == 216: # Day 9: Shop 3 unlocked
            if self.specialization_mode.get(player) == "TENTATIVE_TOMATO":
                shops = obs.get("town", {}).get("unlocked_shops", [])
                has_straw = any(s in STRAWBERRY_SHOPS for s in shops[:3])
                if has_straw:
                    # Adversarial revelation detected! Fall back immediately to Strawberry Bedrock!
                    self.specialization_mode[player] = "STRAWBERRY"
                else:
                    self.specialization_mode[player] = "TOMATO"

        # 2. Get baseline action from V2
        action = super().act(obs)
        mode = self.specialization_mode.get(player, "STRAWBERRY")

        # 3. If in confirmed pure TOMATO mode:
        if mode == "TOMATO":
            # Day 11 (steps 264 to 287): Substitute seed buys and plants
            if 264 <= step <= 287:
                new_market = []
                for m in action.get("market", []):
                    if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "STRAWBERRY":
                        new_market.append(["BUY_SEED", "TOMATO", m[2]])
                    else:
                        new_market.append(m)
                action["market"] = new_market[:10]
                
                if action.get("farmer") and action["farmer"][0] == "PLANT" and action["farmer"][1] == "STRAWBERRY":
                    action["farmer"] = ["PLANT", "TOMATO"]
                for i, h in enumerate(action.get("hands", [])):
                    if h and h[0] == "PLANT" and h[1] == "STRAWBERRY":
                        action["hands"][i] = ["PLANT", "TOMATO"]
                        
            # Days 19 to 29: Active Tomato sales on step % 4 == 1
            if day >= 19 and step % 4 == 1:
                shed_tom = obs["private"]["shed"].get("TOMATO", 0)
                if shed_tom > 0 and len(action.get("market", [])) < 10:
                    batch = min(shed_tom, self.tomato_sale_batch)
                    action["market"].append(["SELL", "TOMATO", batch])
                    
            # Replace planned Strawberry sells with Tomato sells if shed has Tomatoes
            new_market = []
            for m in action.get("market", []):
                if m and m[0] == "SELL" and m[1] == "STRAWBERRY":
                    shed_tom = obs["private"]["shed"].get("TOMATO", 0)
                    if shed_tom > 0:
                        batch = min(shed_tom, m[2])
                        new_market.append(["SELL", "TOMATO", batch])
                    else:
                        new_market.append(m)
                else:
                    new_market.append(m)
            action["market"] = new_market[:10]

        return action
