"""
V39 Ground-Truth Episode Processor
Identifies V35 by its deterministic 25/25 wheat wash opening.
Reconstructs true wins, losses, margins, and opponent identities.
Updates scratch/v39/live/episodes.jsonl
"""

import json
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live")
REPLAY_DIR = os.path.join(LIVE_DIR, "replays")
OUT_JSONL = os.path.join(LIVE_DIR, "episodes.jsonl")

def process():
    records = []
    replays = [f for f in sorted(os.listdir(REPLAY_DIR)) if f.endswith("-replay.json")]
    
    for f in replays:
        path = os.path.join(REPLAY_DIR, f)
        with open(path, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            
        eid = d["info"].get("EpisodeId")
        seed = d["info"].get("seed")
        tn = d["info"].get("TeamNames", ["Unknown", "Unknown"])
        rewards = d.get("rewards", [0, 0])
        statuses = d.get("statuses", ["DONE", "DONE"])
        steps = d.get("steps", [])
        
        # Ground truth V35 identification:
        # Step 1 market action must be [['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]]
        act0 = steps[1][0].get("action", {}).get("market", []) if len(steps) > 1 else []
        act1 = steps[1][1].get("action", {}).get("market", []) if len(steps) > 1 else []
        
        v35_wash = [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
        
        if eid == 113153701:
            # Self-play validation: both seats are V35
            our_seat = 0
            opp_seat = 1
            opp_name = "Self-Play Validation"
        elif act0 == v35_wash and act1 != v35_wash:
            our_seat = 0
            opp_seat = 1
            opp_name = tn[1]
        elif act1 == v35_wash and act0 != v35_wash:
            our_seat = 1
            opp_seat = 0
            opp_name = tn[0]
        else:
            # Fallback
            our_seat = 0
            opp_seat = 1
            opp_name = tn[1]
            
        our_r = rewards[our_seat]
        opp_r = rewards[opp_seat]
        margin = our_r - opp_r
        res = "WIN" if margin > 0 else ("LOSS" if margin < 0 else "TIE")
        
        rec = {
            "episode_id": eid,
            "seed": seed,
            "seat": our_seat,
            "opp_seat": opp_seat,
            "opponent_name": opp_name,
            "team_names": tn,
            "our_reward": our_r,
            "opp_reward": opp_r,
            "margin": margin,
            "result": res,
            "status": statuses[our_seat],
            "step1_our_market": steps[1][our_seat].get("action", {}).get("market", []) if len(steps) > 1 else [],
            "step1_opp_market": steps[1][opp_seat].get("action", {}).get("market", []) if len(steps) > 1 else []
        }
        records.append(rec)
        
    print(f"Total processed: {len(records)}")
    wins = [r for r in records if r["result"] == "WIN"]
    losses = [r for r in records if r["result"] == "LOSS"]
    ties = [r for r in records if r["result"] == "TIE"]
    
    print(f"\n==========================================")
    print(f"TRUE V35 PERFORMANCE SUMMARY (N = {len(records)})")
    print(f"==========================================")
    print(f"WINS:   {len(wins)} ({len(wins)/len(records)*100:.1f}%)")
    print(f"LOSSES: {len(losses)} ({len(losses)/len(records)*100:.1f}%)")
    print(f"TIES:   {len(ties)} ({len(ties)/len(records)*100:.1f}%)")
    print(f"Mean V35 Score: ${np.mean([r['our_reward'] for r in records]):,.1f}")
    print(f"Mean Opp Score: ${np.mean([r['opp_reward'] for r in records]):,.1f}")
    print(f"Mean Margin:    ${np.mean([r['margin'] for r in records]):+,.1f}")
    
    print("\n--- COMPLETE LOSS LEDGER ---")
    for idx, l in enumerate(losses, 1):
        print(f"Loss #{idx:02d}: Ep {l['episode_id']} | Seed {l['seed']} | Seat {l['seat']} | "
              f"V35 ${l['our_reward']:,.0f} vs Opp ({l['opponent_name']}) ${l['opp_reward']:,.0f} | Margin ${l['margin']:,.0f}")
              
    print("\n--- COMPLETE WIN LEDGER ---")
    for idx, w in enumerate(wins, 1):
        print(f"Win  #{idx:02d}: Ep {w['episode_id']} | Seed {w['seed']} | Seat {w['seat']} | "
              f"V35 ${w['our_reward']:,.0f} vs Opp ({w['opponent_name']}) ${w['opp_reward']:,.0f} | Margin +${w['margin']:,.0f}")
              
    # Write back clean jsonl
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
    print(f"\nUpdated {OUT_JSONL} with ground-truth records.")

if __name__ == "__main__":
    process()
