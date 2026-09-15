import json
from collections import defaultdict
import glob
import os

def analyze_shop_worlds():
    manifest = json.load(open("scratch/live_episodes_manifest.json"))
    replay_files = {
        os.path.basename(f).replace("episode_", "").replace(".json", ""): f
        for f in glob.glob("replays/live_tournament/*.json")
    }
    
    # We can inspect shop worlds from the downloaded replays or from scratch/shop_world_seeds.json
    shop_world_losses = defaultdict(list)
    shop_world_matches = defaultdict(int)
    
    for rf_id, rf_path in replay_files.items():
        try:
            d = json.load(open(rf_path))
        except:
            continue
        steps = d.get("steps", [])
        if len(steps) < 200: continue
        
        info = d.get("info", {})
        teams = info.get("TeamNames", ["Player0", "Player1"])
        our_seat = 0 if "Eldritch" in teams[0] else 1
        opp_seat = 1 - our_seat
        
        final_step = steps[-1]
        r_us = final_step[our_seat].get("reward", 0)
        r_opp = final_step[opp_seat].get("reward", 0)
        margin = r_us - r_opp
        
        # Get first 2 shops
        shops = steps[144][0]["observation"]["town"]["unlocked_shops"]
        pair = tuple(shops[:2]) if len(shops) >= 2 else ("UNKNOWN", "UNKNOWN")
        pair_str = f"{pair[0]} + {pair[1]}"
        
        shop_world_matches[pair_str] += 1
        shop_world_losses[pair_str].append({
            "ep_id": rf_id,
            "margin": margin,
            "us_cash": r_us,
            "opp_cash": r_opp,
            "loss": margin < 0
        })
        
    print("=" * 90)
    print("LIVE SHOP WORLD LOSS & FREQUENCY DISTRIBUTION (Downloaded Replays):")
    print("=" * 90)
    
    table = []
    for pair_str, records in shop_world_losses.items():
        n = len(records)
        n_loss = sum(1 for r in records if r["loss"])
        margins = [r["margin"] for r in records]
        mean_m = sum(margins) / n
        worst_m = min(margins)
        table.append((worst_m, mean_m, n_loss, n, pair_str))
        
    table.sort()
    print(f"{'Shop Pair':<35} | {'Matches':<8} | {'Losses':<8} | {'Win Rate':<9} | {'Mean Margin':<12} | {'Worst Margin':<12}")
    print("-" * 95)
    for worst_m, mean_m, n_loss, n, pair_str in table:
        wr = (n - n_loss) / n * 100
        print(f"{pair_str:<35} | {n:<8} | {n_loss:<8} | {wr:6.1f}%   | ${mean_m:+10,.0f} | ${worst_m:+10,.0f}")

if __name__ == "__main__":
    analyze_shop_worlds()
