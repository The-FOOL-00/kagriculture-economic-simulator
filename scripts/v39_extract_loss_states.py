"""
V39 Loss State Extraction
Extracts immutable decision states immediately preceding divergence at Step 693/694.
Stores them in scratch/v39/loss_states/
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPLAY_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live", "replays")
OUT_DIR = os.path.join(BASE_DIR, "scratch", "v39", "loss_states")
os.makedirs(OUT_DIR, exist_ok=True)

TARGET_CASES = [
    {"eid": 113183263, "name": "loss_yassine_chritt", "step": 694, "v35_seat": 1},
    {"eid": 113171441, "name": "loss_lisan_al_gaib", "step": 694, "v35_seat": 1},
    {"eid": 113164394, "name": "loss_junxing_peng", "step": 694, "v35_seat": 1},
    {"eid": 113166778, "name": "loss_noncaffeine", "step": 694, "v35_seat": 1},
    {"eid": 113176099, "name": "near_win_kowalskii", "step": 694, "v35_seat": 1},
    {"eid": 113184429, "name": "near_win_zeel_vavliya", "step": 694, "v35_seat": 1},
    {"eid": 113186749, "name": "near_win_lllleeeo", "step": 694, "v35_seat": 1},
]

def extract():
    for case in TARGET_CASES:
        eid = case["eid"]
        path = os.path.join(REPLAY_DIR, f"episode-{eid}-replay.json")
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            
        step_idx = case["step"]
        v35_seat = case["v35_seat"]
        opp_seat = 1 - v35_seat
        
        step_data = data["steps"][step_idx]
        obs_v35 = step_data[v35_seat]["observation"]
        obs_opp = step_data[opp_seat]["observation"]
        
        act_v35 = step_data[v35_seat].get("action", {})
        act_opp = step_data[opp_seat].get("action", {})
        
        state_fixture = {
            "episode_id": eid,
            "case_name": case["name"],
            "seed": data["info"].get("seed"),
            "step": step_idx,
            "v35_seat": v35_seat,
            "opp_seat": opp_seat,
            "opp_team_name": data["info"].get("TeamNames", ["", ""])[opp_seat],
            "v35_money": obs_v35["farms"][v35_seat]["money"],
            "opp_money": obs_opp["farms"][opp_seat]["money"],
            "v35_shed": obs_v35.get("private", {}).get("shed", {}),
            "opp_shed": obs_opp.get("private", {}).get("shed", {}),
            "v35_inventories": obs_v35.get("private", {}).get("inventories", []),
            "opp_inventories": obs_opp.get("private", {}).get("inventories", []),
            "market_prices": obs_v35.get("market", {}).get("prices", {}),
            "market_inventory": obs_v35.get("market", {}).get("inventory", {}),
            "v35_default_action": act_v35,
            "opp_actual_action": act_opp,
            "full_step_observation_v35": obs_v35,
            "full_step_observation_opp": obs_opp
        }
        
        out_file = os.path.join(OUT_DIR, f"{case['name']}_step{step_idx}.json")
        with open(out_file, "w", encoding="utf-8") as out_fp:
            json.dump(state_fixture, out_fp, indent=2)
            
        print(f"Extracted fixture '{case['name']}' at Step {step_idx} -> {out_file}")

if __name__ == "__main__":
    extract()
