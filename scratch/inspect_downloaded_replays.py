import json
import os
import glob

def inspect_downloaded_replays():
    replay_files = glob.glob("replays/live_tournament/*.json")
    print(f"Total downloaded replays available: {len(replay_files)}")
    
    losses = []
    wins = []
    
    for rf in replay_files:
        try:
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            continue
            
        steps = data.get("steps", [])
        if not steps: continue
        
        info = data.get("info", {})
        # Find player index for our submissions (56146971 or 56146947)
        # Check step 0
        agents = info.get("Agents", [])
        
        # Check final step reward
        final_step = steps[-1]
        rewards = [final_step[0].get("reward", 0), final_step[1].get("reward", 0)]
        
        # Extract shops revealed
        shops = []
        for s_idx in [72, 144, 216, 288, 360, 432, 504, 576]:
            if s_idx < len(steps):
                obs = steps[s_idx][0].get("observation", {})
                town_shops = obs.get("town", {}).get("unlocked_shops", [])
                if town_shops:
                    shops = town_shops
                    
        # Check cash milestones for both players
        milestones = [72, 144, 216, 288, 360, 432, 504, 576, 648, 718]
        p0_cash_curve = []
        p1_cash_curve = []
        for m in milestones:
            if m < len(steps):
                obs0 = steps[m][0].get("observation", {})
                farms = obs0.get("farms", [])
                if len(farms) >= 2:
                    p0_cash_curve.append(farms[0].get("money", 0))
                    p1_cash_curve.append(farms[1].get("money", 0))
                    
        # Identify our seat
        # In info['TeamNames'] or check which matches our live control logic
        diff = rewards[0] - rewards[1]
        ep_id = os.path.basename(rf).replace("episode_", "").replace(".json", "")
        
        # Count opponent animals & crops at step 360 (Day 15)
        step360 = steps[min(360, len(steps)-1)][0].get("observation", {})
        farms360 = step360.get("farms", [])
        p0_animals, p1_animals = {}, {}
        p0_crops, p1_crops = {}, {}
        if len(farms360) >= 2:
            for y in range(10):
                for x in range(10):
                    t0 = farms360[0]["tiles"][y][x]
                    t1 = farms360[1]["tiles"][y][x]
                    if isinstance(t0, dict):
                        if t0.get("kind") == "PASTURE": p0_animals[t0.get("animal")] = p0_animals.get(t0.get("animal"), 0) + 1
                        elif t0.get("kind") == "PLANT": p0_crops[t0.get("crop")] = p0_crops.get(t0.get("crop"), 0) + 1
                    if isinstance(t1, dict):
                        if t1.get("kind") == "PASTURE": p1_animals[t1.get("animal")] = p1_animals.get(t1.get("animal"), 0) + 1
                        elif t1.get("kind") == "PLANT": p1_crops[t1.get("crop")] = p1_crops.get(t1.get("crop"), 0) + 1

        entry = {
            "episode_id": ep_id,
            "rewards": rewards,
            "diff": diff,
            "shops": shops,
            "p0_cash_curve": p0_cash_curve,
            "p1_cash_curve": p1_cash_curve,
            "p0_animals_day15": p0_animals,
            "p1_animals_day15": p1_animals,
            "p0_crops_day15": p0_crops,
            "p1_crops_day15": p1_crops,
        }
        
        if abs(diff) > 20000:
            losses.append(entry)
            
    print(f"Large Margin Episodes analyzed: {len(losses)}")
    for e in losses[:10]:
        print(f"\nEpisode {e['episode_id']}: P0=${e['rewards'][0]:,.0f} vs P1=${e['rewards'][1]:,.0f} (Diff: ${e['diff']:+,.0f})")
        print(f"  Shops: {e['shops']}")
        print(f"  P0 Animals (D15): {e['p0_animals_day15']} | Crops: {e['p0_crops_day15']}")
        print(f"  P1 Animals (D15): {e['p1_animals_day15']} | Crops: {e['p1_crops_day15']}")
        print(f"  P0 Cash Milestones (D3,6,9,12,15,18,21,24,27,30): {e['p0_cash_curve']}")
        print(f"  P1 Cash Milestones (D3,6,9,12,15,18,21,24,27,30): {e['p1_cash_curve']}")

if __name__ == "__main__":
    inspect_downloaded_replays()
