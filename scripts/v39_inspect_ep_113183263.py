"""
V39 Forensic Deep Dive: Episode 113183263 (Margin -$791 vs Yassine Chritt)
Inspects turns 680 to 719: inventory, market sales, shed, and cash.
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPLAY_PATH = os.path.join(BASE_DIR, "scratch", "v39", "live", "replays", "episode-113183263-replay.json")

def inspect_endgame():
    with open(REPLAY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data["steps"]
    v35_seat = 1
    opp_seat = 0
    
    print("=== TURNS 680 TO 719 IN EPISODE 113183263 ===")
    for t in range(680, 720):
        s = steps[t]
        obs_v35 = s[v35_seat]["observation"]
        obs_opp = s[opp_seat]["observation"]
        
        m_v35 = obs_v35["farms"][v35_seat]["money"]
        m_opp = obs_opp["farms"][opp_seat]["money"]
        
        # Check market actions in this step
        act_v35 = s[v35_seat].get("action", {})
        act_opp = s[opp_seat].get("action", {})
        
        mkt_v35 = act_v35.get("market", [])
        mkt_opp = act_opp.get("market", [])
        
        shed_v35 = obs_v35.get("private", {}).get("shed", {})
        shed_opp = obs_opp.get("private", {}).get("shed", {})
        
        non_zero_shed_v35 = {k: v for k, v in shed_v35.items() if v > 0}
        non_zero_shed_opp = {k: v for k, v in shed_opp.items() if v > 0}
        
        if mkt_v35 or mkt_opp or t >= 710:
            print(f"Step {t:03d} (Day {t//24}, Hr {t%24:02d}): "
                  f"V35 ${m_v35:,.0f} | Opp ${m_opp:,.0f} | Diff ${m_v35 - m_opp:+,.0f}")
            if mkt_v35:
                print(f"   V35 Market: {mkt_v35}")
            if mkt_opp:
                print(f"   Opp Market: {mkt_opp}")
            if non_zero_shed_v35 or non_zero_shed_opp:
                print(f"   Shed V35: {non_zero_shed_v35} | Shed Opp: {non_zero_shed_opp}")
                
    # Terminal step 719 inspection
    s719 = steps[719]
    obs_v35 = s719[v35_seat]["observation"]
    obs_opp = s719[opp_seat]["observation"]
    print("\n--- FINAL STEP 719 DETAILS ---")
    print(f"Final V35 Shed: {obs_v35.get('private', {}).get('shed', {})}")
    print(f"Final Opp Shed: {obs_opp.get('private', {}).get('shed', {})}")
    print(f"Final V35 Inventories: {[inv for inv in obs_v35.get('private', {}).get('inventories', []) if inv]}")
    print(f"Final Opp Inventories: {[inv for inv in obs_opp.get('private', {}).get('inventories', []) if inv]}")

if __name__ == "__main__":
    inspect_endgame()
