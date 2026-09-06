"""
scratch/v2_guarded_candidate.py
=============================================================================
Guarded V2: Minimal Closed-Loop Invariant Safety Layer on Frozen V2.
=============================================================================
Executes exact frozen V2 trace under normal conditions (100.0000% parity).
Intervenes ONLY when a verified natural/external invariant violation occurs:
1. Hour-23 Crop Watering Rescue: If a critical crop is unwatered and worker is on tile.
2. Step-122 Quadrant Unlock Fallback: Ensures land is unlocked if step-122 was missed.
3. Emergency Feed Continuity: Prevents animal starvation if wheat supply is zeroed.
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import candidates.slot2_aethel_refined_v2 as v2

_TURNS_PER_DAY = 24
_SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")

class GuardedV2Agent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_step = -1
        self.total_interventions = 0
        self.intervention_log = []

    def __call__(self, obs, config=None):
        step = min(int(obs.get("step", 0) or 0), 719)
        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step

        # 1. Base Action from Frozen V2 Agent
        base_action = v2.agent(obs, config)

        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        my_farm = farms[player] if len(farms) > player else {}
        tiles = my_farm.get("tiles") or []
        unlocked = my_farm.get("unlocked_quadrants") or []
        private = obs.get("private") or {}
        shed = private.get("shed") or {}

        farmer_act = list(base_action.get("farmer", ["PASS"]))
        hands_acts = [list(h) for h in base_action.get("hands", [])]
        market_orders = list(base_action.get("market", []))

        day = step // _TURNS_PER_DAY
        hour = step % _TURNS_PER_DAY
        intervened = False
        reason = None

        # -------------------------------------------------------------
        # GUARD 1: Step-122 Quadrant Unlock Invariant
        # -------------------------------------------------------------
        # If at step 122+ only 1 quadrant is unlocked, unlock quadrant 1 (North-East)
        if step >= 122 and len(unlocked) < 2 and my_farm.get("money", 0) >= 500:
            # Check if UNLOCK_QUADRANT is already in farmer or hands
            has_unlock = (farmer_act == ["UNLOCK_QUADRANT", 1]) or any(h == ["UNLOCK_QUADRANT", 1] for h in hands_acts)
            if not has_unlock:
                farmer_act = ["UNLOCK_QUADRANT", 1]
                intervened = True
                reason = f"Step {step}: Emergency Quadrant 1 Unlock"

        # -------------------------------------------------------------
        # GUARD 2: Critical Crop Watering Invariant (Hour 23 Strict Check)
        # -------------------------------------------------------------
        # At the final hour of the day (Hour 23), if any crop is unwatered
        # AND a worker is currently on that tile, water it!
        if hour == 23 and tiles:
            farmer_pos = tuple(my_farm.get("farmer", [4, 4]))
            hands_pos = [tuple(h) for h in my_farm.get("hands", [])]
            all_workers = [farmer_pos] + hands_pos

            for r_idx, row in enumerate(tiles):
                for c_idx, t in enumerate(row):
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        if not t.get("watered_today"):
                            target_pos = (c_idx, r_idx)
                            for w_idx, w_pos in enumerate(all_workers):
                                if w_pos == target_pos:
                                    if w_idx == 0 and farmer_act != ["WATER"]:
                                        farmer_act = ["WATER"]
                                        intervened = True
                                        reason = f"Step {step}: Rescued unwatered {t.get('crop')} at {target_pos} (Farmer)"
                                    elif w_idx > 0:
                                        h_idx = w_idx - 1
                                        if h_idx < len(hands_acts) and hands_acts[h_idx] != ["WATER"]:
                                            hands_acts[h_idx] = ["WATER"]
                                            intervened = True
                                            reason = f"Step {step}: Rescued unwatered {t.get('crop')} at {target_pos} (Hand {h_idx})"

        # -------------------------------------------------------------
        # GUARD 3: Emergency Animal Feed Buffer
        # -------------------------------------------------------------
        # If animals exist in pastures and shed wheat == 0 and market buy is missing
        if hour == 0 and day >= 1:
            has_animals = False
            for row in tiles:
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal"):
                        has_animals = True
                        break
                if has_animals:
                    break
            
            wheat_count = int(shed.get("WHEAT", 0) or 0)
            if has_animals and wheat_count == 0 and my_farm.get("money", 0) >= 30:
                has_wheat_buy = any(isinstance(o, list) and len(o) >= 2 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" for o in market_orders)
                if not has_wheat_buy and len(market_orders) < 10:
                    market_orders.append(["BUY_PRODUCT", "WHEAT", 5])
                    intervened = True
                    reason = f"Step {step}: Emergency Wheat Feed Purchase x5"

        if intervened:
            self.total_interventions += 1
            self.intervention_log.append(reason)

        return {
            "farmer": farmer_act,
            "hands": hands_acts,
            "market": market_orders
        }

_guarded_agent_inst = GuardedV2Agent()

def agent(obs, config=None):
    return _guarded_agent_inst(obs, config)
