"""
V39 Opponent Fingerprinting Script
Extracts observable strategy fingerprints for all unique opponents in the 29 V35 live games.
Writes scratch/v39/live/opponent_fingerprints.jsonl
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live")
REPLAY_DIR = os.path.join(LIVE_DIR, "replays")
OUT_JSONL = os.path.join(LIVE_DIR, "opponent_fingerprints.jsonl")

def extract_fingerprints():
    with open(os.path.join(LIVE_DIR, "episodes.jsonl"), "r", encoding="utf-8") as f:
        episodes = [json.loads(line) for line in f if line.strip()]
        
    opponents = {}
    for ep in episodes:
        opp_name = ep["opponent_name"]
        if opp_name == "Self-Play Validation":
            continue
        if opp_name not in opponents:
            opponents[opp_name] = []
        opponents[opp_name].append(ep)
        
    fingerprints = []
    
    for opp_name, eps in opponents.items():
        # Analyze first episode for this opponent
        ep = eps[0]
        eid = ep["episode_id"]
        opp_seat = ep["opp_seat"]
        
        path = os.path.join(REPLAY_DIR, f"episode-{eid}-replay.json")
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            
        steps = data["steps"]
        
        # 1. Opening wash behavior at Step 1
        step1_mkt = steps[1][opp_seat].get("action", {}).get("market", [])
        wash_type = "NONE"
        wash_volume = 0
        for order in step1_mkt:
            if order[0] in ("BUY_PRODUCT", "SELL") and len(order) > 2 and order[1] == "WHEAT":
                wash_volume = max(wash_volume, order[2])
                wash_type = "WHEAT_WASH"
                
        # 2. Worker count trajectory
        f_init = steps[0][opp_seat]["observation"]["farms"][opp_seat]
        f_mid = steps[360][opp_seat]["observation"]["farms"][opp_seat]
        f_final = steps[-1][opp_seat]["observation"]["farms"][opp_seat]
        
        hands_mid = len(f_mid.get("hands", []))
        hands_final = len(f_final.get("hands", []))
        
        # 3. Land expansion
        quads_final = len(f_final.get("unlocked_quadrants", []))
        
        # 4. Animal timing
        first_animal_step = None
        cows_final = 0
        sheep_final = 0
        for t, s in enumerate(steps):
            tiles = s[opp_seat]["observation"]["farms"][opp_seat].get("tiles", [])
            for row in tiles:
                for tile in row:
                    if isinstance(tile, dict) and tile.get("animal"):
                        if first_animal_step is None:
                            first_animal_step = t
                        if t == len(steps) - 1:
                            if tile.get("animal") == "COW":
                                cows_final += 1
                            elif tile.get("animal") == "SHEEP":
                                sheep_final += 1
                                
        # 5. Terminal liquidation style (Step 694 vs 718)
        mkt_694 = steps[694][opp_seat].get("action", {}).get("market", [])
        liq_style = "EARLY_STEP694" if mkt_694 else "LATE_STEP718"
        
        fp_record = {
            "opponent_name": opp_name,
            "sample_episode_id": eid,
            "matches_played": len(eps),
            "v35_record_vs_opp": f"{sum(1 for e in eps if e['result'] == 'WIN')}W-{sum(1 for e in eps if e['result'] == 'LOSS')}L",
            "opening_wash_type": wash_type,
            "opening_wash_volume": wash_volume,
            "step1_raw_market": step1_mkt,
            "midgame_hands": hands_mid,
            "terminal_hands": hands_final,
            "terminal_quadrants": quads_final,
            "first_animal_step": first_animal_step,
            "terminal_cows": cows_final,
            "terminal_sheep": sheep_final,
            "terminal_liquidation_style": liq_style
        }
        fingerprints.append(fp_record)
        print(f"Fingerprinted '{opp_name}': Wash: {wash_type} ({wash_volume}) | Hands: {hands_final} | Land: {quads_final}Q | Liq: {liq_style}")
        
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for fp in fingerprints:
            f.write(json.dumps(fp) + "\n")
            
    print(f"\nSaved {len(fingerprints)} opponent fingerprints to {OUT_JSONL}")

if __name__ == "__main__":
    extract_fingerprints()
