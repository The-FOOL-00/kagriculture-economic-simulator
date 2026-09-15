import sys
import os
import json
from collections import defaultdict
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from candidates.candidate_cl_fert_gated import _dist, _quad
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Base Q50 Agent
class BaseQ50Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

# W2: Suppress weeds during peak days 9-14
class W2_SuppressClearingAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        if 9 <= day <= 14:
            res["weeds"] = []
        return res

# W6: Suppress weeds only when mature strawberry exists
class W6_GatedLowerValueTasksAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        has_ripe_straw = any(isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY" for p in res["ripe_crops"])
        if has_ripe_straw:
            res["weeds"] = []
        return res

# Component A_only / L3 / U1: STRAWBERRY > MELON > WHEAT
class U1_SafeWindowUrgencyAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        def crop_urgency_key(pos):
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY": return 0 if yu >= 2 else 5
            elif c == "MELON": return 10
            elif c == "WHEAT": return 20
            return 50
        res["ripe_crops"].sort(key=crop_urgency_key)
        return res

# Component B_only / B1: Weed suppression only, default crop ordering
class B1_WeedSuppressionOnlyAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        has_ripe_straw = any(isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY" for p in res["ripe_crops"])
        if has_ripe_straw:
            res["weeds"] = []
        return res

# A+B: L_Minimal
class L_MinimalAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        has_ripe_straw = False
        def crop_urgency_key(pos):
            nonlocal has_ripe_straw
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                has_ripe_straw = True
                return 0 if yu >= 2 else 5
            elif c == "MELON": return 10
            elif c == "WHEAT": return 20
            return 50
        res["ripe_crops"].sort(key=crop_urgency_key)
        if has_ripe_straw:
            res["weeds"] = []
        return res

# U2: STRAWBERRY > WHEAT > MELON
class U2_StrawWheatMelonAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        def crop_urgency_key(pos):
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            if c == "STRAWBERRY": return 0
            elif c == "WHEAT": return 10
            elif c == "MELON": return 20
            return 50
        res["ripe_crops"].sort(key=crop_urgency_key)
        return res

# U3: MELON > STRAWBERRY > WHEAT
class U3_MelonStrawWheatAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        def crop_urgency_key(pos):
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            if c == "MELON": return 0
            elif c == "STRAWBERRY": return 10
            elif c == "WHEAT": return 20
            return 50
        res["ripe_crops"].sort(key=crop_urgency_key)
        return res

# U4: Dynamic economic urgency (expected economic loss / safe hours remaining)
class U4_DynamicEconomicUrgencyAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        def crop_urgency_key(pos):
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                # Value per unit = 120, capping risk high if yu >= 2
                loss_val = 120.0 * (yu if yu >= 2 else 1)
                hours_rem = 24.0 if yu < 4 else 2.0
                return -(loss_val / hours_rem)
            elif c == "MELON":
                loss_val = 80.0 * 6.0
                hours_rem = 48.0
                return -(loss_val / hours_rem)
            elif c == "WHEAT":
                loss_val = 25.0 * 4.0
                hours_rem = 72.0
                return -(loss_val / hours_rem)
            return 0.0
        res["ripe_crops"].sort(key=crop_urgency_key)
        return res

# U5: Dynamic irreversible-loss probability / safe hours remaining
class U5_IrreversibleLossUrgencyAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        def crop_urgency_key(pos):
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                p_loss = 1.0 if yu >= 4 else (0.5 if yu >= 2 else 0.1)
                hours_rem = 6.0 if yu >= 4 else 24.0
                return -(p_loss / hours_rem)
            elif c == "MELON":
                return -(0.1 / 48.0)
            elif c == "WHEAT":
                return -(0.0 / 72.0)
            return 0.0
        res["ripe_crops"].sort(key=crop_urgency_key)
        return res

# B2: Suppress weeds only when strawberry backlog > 1
class B2_BacklogGt1Agent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        ripe_straw = [p for p in res["ripe_crops"] if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY"]
        if len(ripe_straw) > 1:
            res["weeds"] = []
        return res

# B3: Suppress weeds only during afternoon/evening rush (hours 12-23)
class B3_AfternoonGatingAgent(BaseQ50Agent):
    def __init__(self, quota=50):
        super().__init__(quota)
        self._curr_hour = 0
    def __call__(self, obs, config=None):
        self._curr_hour = obs.get("hour", 0)
        return super().__call__(obs, config)
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        has_ripe_straw = any(isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY" for p in res["ripe_crops"])
        if has_ripe_straw and self._curr_hour >= 12:
            res["weeds"] = []
        return res

# B4: Suppress only non-access peripheral digging (keep quad 0 center weeds accessible)
class B4_PreserveAccessClearingAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        has_ripe_straw = any(isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY" for p in res["ripe_crops"])
        if has_ripe_straw:
            # Only keep weeds adjacent to shed access or well access
            critical_access = {(10, 10), (10, 11), (9, 9), (9, 10), (9, 11), (11, 9), (11, 10), (11, 11)}
            res["weeds"] = [w for w in res["weeds"] if w in critical_access]
        return res

# B5: Suppress only weeds outside production zone (quad != 0 and quad != 3)
class B5_OutsideProductionZoneAgent(BaseQ50Agent):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        has_ripe_straw = any(isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "STRAWBERRY" for p in res["ripe_crops"])
        if has_ripe_straw:
            res["weeds"] = [w for w in res["weeds"] if _quad(w[0], w[1]) in {0, 3}]
        return res

SUITE_POLICIES = {
    "Raw_Q50": BaseQ50Agent,
    "W2_SuppressClearing": W2_SuppressClearingAgent,
    "W6_GatedLowerValue": W6_GatedLowerValueTasksAgent,
    "A_only_U1": U1_SafeWindowUrgencyAgent,
    "B_only_B1": B1_WeedSuppressionOnlyAgent,
    "A_plus_B_L_Minimal": L_MinimalAgent,
    "U2_StrawWheatMelon": U2_StrawWheatMelonAgent,
    "U3_MelonStrawWheat": U3_MelonStrawWheatAgent,
    "U4_EconomicUrgency": U4_DynamicEconomicUrgencyAgent,
    "U5_IrreversibleLoss": U5_IrreversibleLossUrgencyAgent,
    "B2_BacklogGt1": B2_BacklogGt1Agent,
    "B3_AfternoonGating": B3_AfternoonGatingAgent,
    "B4_PreserveAccess": B4_PreserveAccessClearingAgent,
    "B5_OutsideProdZone": B5_OutsideProductionZoneAgent
}

def run_suite_job(args):
    p_name, seed = args
    cls = SUITE_POLICIES[p_name]
    agent = cls()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    rew = float(steps[-1][0]["reward"])

    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    return p_name, seed, rew, dict(sold_qty)
