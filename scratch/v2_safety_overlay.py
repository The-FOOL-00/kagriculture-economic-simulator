"""
scratch/v2_safety_overlay.py
V2 Safety Overlay: Wraps Frozen V2 with Minimal Exception Handling and Invariant Guards.

Guarantees 100% Bit-Identical Non-Interference on Standard Games.
Intervenes ONLY when an external perturbation causes actual state to diverge from expected invariant.
"""

import copy
import candidates.slot2_aethel_refined_v2 as v2

_DAY0_MELON_TILES = [(0, 0), (1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (4, 0)]
_TURNS_PER_DAY = 24

# Expected minimum watered days for the 7 Day-0 melons
_MELON_WATER_DAYS = {0, 1, 2, 3, 6, 7, 8, 9, 10}

class V2SafetyOverlayAgent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_step = -1
        self.guard_interventions = 0

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

        farmer_act = list(base_action.get("farmer", ["PASS"]))
        hands_acts = [list(h) for h in base_action.get("hands", [])]
        market_orders = list(base_action.get("market", []))

        day = step // _TURNS_PER_DAY
        hour = step % _TURNS_PER_DAY
        intervened = False

        # -------------------------------------------------------------
        # GUARD 1: Critical Crop Watering Invariant (Hour 23 Strict Check)
        # -------------------------------------------------------------
        # At the final hour of the day (Hour 23), if a Day-0 melon is unwatered
        # on a required watering day AND a worker is currently on that tile, water it!
        if day in _MELON_WATER_DAYS and hour == 23 and tiles:
            all_workers = [tuple(my_farm.get("farmer", [4, 4]))] + [tuple(h) for h in my_farm.get("hands", [])]
            for (mx, my) in _DAY0_MELON_TILES:
                if 0 <= my < len(tiles) and 0 <= mx < len(tiles[my]):
                    t = tiles[my][mx]
                    if isinstance(t, dict) and t.get("crop") == "MELON" and not t.get("watered_today"):
                        # If a worker happens to be standing on this unwatered melon, water it!
                        for w_idx, w_pos in enumerate(all_workers):
                            if w_pos == (mx, my):
                                if w_idx == 0 and farmer_act != ["WATER"]:
                                    farmer_act = ["WATER"]
                                    intervened = True
                                elif w_idx > 0:
                                    h_idx = w_idx - 1
                                    if h_idx < len(hands_acts) and hands_acts[h_idx] != ["WATER"]:
                                        hands_acts[h_idx] = ["WATER"]
                                        intervened = True

        if intervened:
            self.guard_interventions += 1

        return {
            "farmer": farmer_act,
            "hands": hands_acts,
            "market": market_orders
        }


_overlay_inst = V2SafetyOverlayAgent()

def agent(obs, config=None):
    return _overlay_inst(obs, config)
