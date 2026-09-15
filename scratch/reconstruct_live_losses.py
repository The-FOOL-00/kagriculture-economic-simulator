import json
import os
import glob
from collections import defaultdict

CHECKPOINT_DAYS = [3, 6, 9, 10, 11, 12, 13, 14, 15, 18, 21, 24, 27, 30]

def analyze_episode(ep_path, our_sub_id):
    with open(ep_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    info = data.get("info", {})
    agents = info.get("Agents", [])
    
    # Determine our seat (0 or 1)
    # agents is list of dicts with 'SubmissionId'
    our_seat = None
    opp_seat = None
    opp_sub_id = None
    for idx, a in enumerate(agents):
        s_id = a.get("SubmissionId") or a.get("submissionId")
        if s_id == int(our_sub_id):
            our_seat = idx
        else:
            opp_seat = idx
            opp_sub_id = s_id
            
    if our_seat is None:
        # Fallback if info is structured differently
        # Let's inspect agents structure
        pass

    steps = data.get("steps", [])
    if not steps:
        return None
        
    cfg = data.get("configuration", {})
    seed = cfg.get("seed")

    # If seat not determined, let's look at initial observation or final reward
    if our_seat is None:
        # inspect step 0
        our_seat = 0
        opp_seat = 1

    # Extract shops revealed
    shops = []
    for s_idx in [72, 144, 216, 288, 360, 432, 504, 576]:
        if s_idx < len(steps):
            obs = steps[s_idx][0].get("observation", {})
            town_shops = obs.get("town", {}).get("unlocked_shops", [])
            if town_shops:
                shops = town_shops

    checkpoints = {}
    for day in CHECKPOINT_DAYS:
        step_idx = min(day * 24 if day < 30 else 719, len(steps) - 1)
        step_entry = steps[step_idx]
        obs = step_entry[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        
        # Analyze farm state for both
        def parse_farm(f):
            if not f: return {}
            money = f.get("money", 0)
            hands = len(f.get("units", []))
            unlocked_quads = sum(1 for q in f.get("unlocked_quadrants", []) if q)
            
            # Count tiles
            crops = defaultdict(int)
            animals = defaultdict(int)
            fertilized_tiles = 0
            tiles = f.get("tiles", [])
            for row in tiles:
                for t in row:
                    if isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "PLANT":
                            crops[t.get("crop")] += 1
                            if t.get("fertilized"):
                                fertilized_tiles += 1
                        elif kind == "PASTURE":
                            animals[t.get("animal")] += 1
                            
            # Inventory / shed
            inventory = f.get("inventory", {})
            manure = f.get("manure", 0)
            fertilizer = inventory.get("FERTILIZER", 0)
            
            return {
                "money": money,
                "hands": hands,
                "quadrants": unlocked_quads,
                "crops": dict(crops),
                "animals": dict(animals),
                "fertilized_tiles": fertilized_tiles,
                "inventory": dict(inventory),
                "manure": manure,
                "fertilizer": fertilizer
            }
            
        cp_our = parse_farm(farms[our_seat] if our_seat < len(farms) else {})
        cp_opp = parse_farm(farms[opp_seat] if opp_seat < len(farms) else {})
        
        checkpoints[day] = {
            "step": step_idx,
            "our": cp_our,
            "opp": cp_opp
        }
        
    final_step = steps[-1]
    final_rewards = [final_step[0].get("reward", 0), final_step[1].get("reward", 0)]
    
    # Cumulative market actions across full match
    our_market_counts = defaultdict(int)
    opp_market_counts = defaultdict(int)
    for s_idx, st in enumerate(steps):
        # Action for player 0 is in st[0].get('action'), player 1 in st[1].get('action')
        a0 = st[0].get("action", {}) or {}
        a1 = st[1].get("action", {}) or {}
        m0 = a0.get("market", [])
        m1 = a1.get("market", [])
        
        our_m = m0 if our_seat == 0 else m1
        opp_m = m1 if our_seat == 0 else m0
        
        for ord in our_m:
            if ord:
                key = f"{ord[0]}_{ord[1]}" if len(ord) > 1 else ord[0]
                our_market_counts[key] += (ord[2] if len(ord) > 2 else 1)
        for ord in opp_m:
            if ord:
                key = f"{ord[0]}_{ord[1]}" if len(ord) > 1 else ord[0]
                opp_market_counts[key] += (ord[2] if len(ord) > 2 else 1)
                
    # Track first step where cash diverged irreversibly
    # Check turn-by-turn cash
    cash_trace_our = []
    cash_trace_opp = []
    for s_idx, st in enumerate(steps):
        obs = st[0].get("observation", {})
        farms = obs.get("farms", [{}, {}])
        c_our = farms[our_seat].get("money", 0) if our_seat < len(farms) else 0
        c_opp = farms[opp_seat].get("money", 0) if opp_seat < len(farms) else 0
        cash_trace_our.append(c_our)
        cash_trace_opp.append(c_opp)
        
    return {
        "episode_id": os.path.basename(ep_path).replace("episode_", "").replace(".json", ""),
        "our_seat": our_seat,
        "opp_sub_id": opp_sub_id,
        "seed": seed,
        "shops": shops,
        "final_rewards": final_rewards,
        "checkpoints": checkpoints,
        "our_market_counts": dict(our_market_counts),
        "opp_market_counts": dict(opp_market_counts),
        "cash_trace_our": cash_trace_our,
        "cash_trace_opp": cash_trace_opp
    }

def main():
    target_episodes = [
        ("replays/live_tournament/episode_107543042.json", "56146971"),
        ("replays/live_tournament/episode_107564294.json", "56146971"),
        ("replays/live_tournament/episode_107582150.json", "56146947"),
        ("replays/live_tournament/episode_107560807.json", "56146947"),
        ("replays/live_tournament/episode_107581148.json", "56146971"),
        ("replays/live_tournament/episode_107522150.json", "56146971"),
        ("replays/live_tournament/episode_107563778.json", "56146947"),
        ("replays/live_tournament/episode_107540087.json", "56146971"),
        ("replays/live_tournament/episode_107700784.json", "56146971"),
    ]
    
    results = []
    for ep_file, sub_id in target_episodes:
        if not os.path.exists(ep_file):
            print(f"File missing: {ep_file}")
            continue
        print(f"Analyzing {ep_file}...")
        res = analyze_episode(ep_file, sub_id)
        if res:
            results.append(res)
            
    # Save parsed forensics
    out_file = "scratch/reconstructed_live_losses_forensics.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved detailed forensics for {len(results)} live losses to {out_file}")

if __name__ == "__main__":
    main()
