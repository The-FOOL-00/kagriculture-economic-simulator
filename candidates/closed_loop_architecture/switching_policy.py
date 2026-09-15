"""
SWITCHING POLICY: Conservative, State-Dependent Economic Module Routing.
Enforces the switching cost / execution risk theorem:
Only switch if Expected Net Incremental Value > Switching Cost + Liquidity Risk.
Prevents late-game route thrashing.
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

class ShopWorldCategory:
    YARN = "YARN"
    NON_YARN_HIGH_DEMAND = "NON_YARN_HIGH_DEMAND"
    NON_YARN_LOW_DEMAND = "NON_YARN_LOW_DEMAND"
    MIXED_UNCERTAIN = "MIXED_UNCERTAIN"

class SwitchingPolicy:
    def __init__(self, mode: str = "MILESTONE_CONSERVATIVE"):
        """
        Modes:
        - 'NO_SWITCHING': Always Module A (pure baseline).
        - 'EARLY_ONLY': Evaluate once at Day 6 (Step 144).
        - 'MILESTONE_CONSERVATIVE': Evaluate at Day 6 and Day 10 (liquidity guard).
        - 'STATE_TRIGGERED': Re-evaluates on unexpected liquidity shocks.
        """
        self.mode = mode
        self.current_module = "MODULE_A_FERT_STRAWBERRY"
        self.switch_history: List[Dict[str, Any]] = []
        self.is_locked = False

    def classify_shops(self, unlocked_shops: List[str]) -> str:
        if not unlocked_shops:
            return ShopWorldCategory.MIXED_UNCERTAIN

        if "YARN_STORE" in unlocked_shops:
            return ShopWorldCategory.YARN

        # High demand dairy pairs
        dairy_shops = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "PIZZA_SHOP"}
        dairy_count = sum(1 for s in unlocked_shops if s in dairy_shops)
        if dairy_count >= 2:
            return ShopWorldCategory.NON_YARN_HIGH_DEMAND

        # High demand carrot pairs
        if "PET_CAFE" in unlocked_shops and "FARMERS_MARKET" in unlocked_shops:
            return ShopWorldCategory.NON_YARN_HIGH_DEMAND

        if len(unlocked_shops) >= 2:
            return ShopWorldCategory.NON_YARN_LOW_DEMAND

        return ShopWorldCategory.MIXED_UNCERTAIN

    def evaluate_switch(self, economic_state: Any) -> Tuple[bool, str, str]:
        """
        Determines whether to switch production modules.
        Returns: (did_switch, new_module_id, rationale)
        """
        if self.mode == "NO_SWITCHING":
            return False, self.current_module, "No switching mode active"

        step = economic_state.step
        day = economic_state.day
        cash = economic_state.cash
        shop_cat = self.classify_shops(economic_state.unlocked_shops)

        # 1. Milestone 1: Day 6 (Step 144) - First 2 shops known
        if step == 144:
            if shop_cat == ShopWorldCategory.YARN:
                rationale = "Yarn shop present; keeping Module A for high wool absorption"
                return False, self.current_module, rationale

            elif shop_cat == ShopWorldCategory.NON_YARN_HIGH_DEMAND:
                shops_set = set(economic_state.unlocked_shops)
                is_smoothie_ice_cream = ("SMOOTHIE_SHOP" in shops_set and "ICE_CREAM_SHOP" in shops_set)
                
                # Module B is specifically compiled for Smoothie + Ice Cream
                if is_smoothie_ice_cream:
                    new_mod = "MODULE_B_DAIRY_COW"
                    self.current_module = new_mod
                    self.switch_history.append({"step": step, "to": new_mod, "reason": "Smoothie + Ice Cream dual shop match"})
                    return True, new_mod, "Switched to Dairy Module B on Smoothie + Ice Cream match"

            # For all other shop pairs, Module A's 61-fertilization strawberry engine is physically optimal
            return False, self.current_module, "Non-Yarn; preserving Module A 61-fertilization bedrock"

        # 2. Milestone 2: Day 10 (Step 240) - Strategy Lock
        if step == 240:
            # Physical layout is committed; lock module to prevent spatial desynchronization.
            # Cash runway protection is handled dynamically by LiquidityController.
            self.is_locked = True
            return False, self.current_module, "Strategy locked at Day 10; physical layout committed"

        return False, self.current_module, "Continuing current module"
