"""
V39 Deep Dive into Loss Details
Inspects:
1. Step 0 actions and market transactions (wheat wash) across all loss games.
2. What happened in severe outlier 113182085 at step 241.
3. Land expansion timing and quadrant unlocks (SE quadrant vs NE/SW).
4. Late-game inventory and sales in near-ties (113176099, 113184429, 113186749).
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPLAY_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live", "replays")

def inspect_losses():
    with open(os.path.join(BASE_DIR, "scratch", "v39", "loss_forensics_data.json"), "r") as f:
        losses = json.load(f)
        
    print("=== 1. STEP 0 ACTIONS IN ALL LOSSES ===")
    for l in losses:
        ep_id = l["episode_id"]
        path = os.path.join(REPLAY_DIR, f"episode-{ep_id}-replay.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        seat = l["seat"]
        opp_seat = 1 - seat
        
        act0_us = data["steps"][0][seat].get("action")
        act0_opp = data["steps"][0][opp_seat].get("action")
        print(f"Ep {ep_id} (Seed {l['seed']}, Margin ${l['margin']:,.0f}):")
        print(f"   Us  (Seat {seat}): {act0_us}")
        print(f"   Opp (Seat {opp_seat}): {act0_opp}")
        
    print("\n=== 2. SEVERE OUTLIER 113182085 (Margin -$41,494) ===")
    path = os.path.join(REPLAY_DIR, "episode-113182085-replay.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    seat = 0
    opp_seat = 1
    steps = data["steps"]
    
    # Inspect turns 230 to 260
    for t in range(235, 255):
        f_us = steps[t][seat]["observation"]["farms"][seat]
        f_opp = steps[t][opp_seat]["observation"]["farms"][opp_seat]
        act_us = steps[t][seat].get("action")
        act_opp = steps[t][opp_seat].get("action")
        m_us = f_us["money"]
        m_opp = f_opp["money"]
        print(f"Step {t:03d} (Day {t//24}, Hr {t%24}): Us ${m_us:,.0f} | Opp ${m_opp:,.0f} | Us Act: {str(act_us)[:60]}")
        
    print("\n=== 3. 4TH QUADRANT (SE) UNLOCK TIMELINE ===")
    for l in losses:
        ep_id = l["episode_id"]
        path = os.path.join(REPLAY_DIR, f"episode-{ep_id}-replay.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        seat = l["seat"]
        opp_seat = 1 - seat
        steps = data["steps"]
        
        us_se_step = None
        opp_se_step = None
        for t, s in enumerate(steps):
            f_us = s[seat]["observation"]["farms"][seat]
            f_opp = s[opp_seat]["observation"]["farms"][opp_seat]
            if "SE" in f_us.get("unlocked_quadrants", []) and us_se_step is None:
                us_se_step = t
            if "SE" in f_opp.get("unlocked_quadrants", []) and opp_se_step is None:
                opp_se_step = t
                
        print(f"Ep {ep_id} (Margin ${l['margin']:,.0f}): SE Unlock -> Us: {us_se_step} | Opp: {opp_se_step}")
        
    print("\n=== 4. NEAR-TIES LATE-GAME DIVERGENCE (Step 600 - 720) ===")
    for ep_id in [113176099, 113184429, 113186749]:
        path = os.path.join(REPLAY_DIR, f"episode-{ep_id}-replay.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        steps = data["steps"]
        # Look at steps 650, 680, 700, 719
        print(f"--- Episode {ep_id} ---")
        for t in [600, 650, 680, 700, 715, 719]:
            f0 = steps[t][0]["observation"]["farms"][0]
            f1 = steps[t][1]["observation"]["farms"][1]
            diff = f0["money"] - f1["money"]
            print(f"Step {t}: Us ${f0['money']:,.0f} vs Opp ${f1['money']:,.0f} | Diff: ${diff:,.0f}")

if __name__ == "__main__":
    inspect_losses()
