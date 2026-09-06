import os
import glob
import json
import pandas as pd
import numpy as np

def extract_episode_telemetry(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps")
    agents = data.get("agents") or data.get("info", {}).get("Agents") or []
    
    # Process both players
    players_data = []
    for p_idx in [0, 1]:
        name = "Unknown"
        if len(agents) > p_idx:
            ag = agents[p_idx]
            name = ag.get("name") if isinstance(ag, dict) else str(ag)
            
        # Let's inspect step 0, step 1, step 24 (Day 1), step 122 (Day 5), step 168 (Day 7), step 200 (Day 8), step 264 (Day 11), step 500 (Day 20), step 719 (Day 30)
        # We also compute all cumulative sales, purchases, max cows, max sheep, max pastures, Q2 unlock step, Q3 unlock step, Q4 usage
        
        cows_timeline = []
        sheep_timeline = []
        pastures_timeline = []
        workers_timeline = []
        cash_timeline = []
        quadrants_timeline = []
        
        wheat_bought = 0
        wheat_bought_cost = 0.0
        wheat_sold = 0
        wheat_sold_rev = 0.0
        
        milk_sold = 0
        milk_sold_rev = 0.0
        wool_sold = 0
        wool_sold_rev = 0.0
        fertilizer_sold = 0
        fertilizer_sold_rev = 0.0
        
        crops_sold = {}
        crops_rev = {}
        seeds_bought = {}
        
        q2_step = None
        q3_step = None
        q4_step = None
        
        day0_workers = 1
        day0_cows = 0
        day0_sheep = 0
        day0_crops = {}
        day0_pastures = 0
        
        # Turn-by-turn analysis
        for step_idx, step in enumerate(steps):
            if not isinstance(step, list) or len(step) <= p_idx:
                continue
            p_state = step[p_idx]
            obs = p_state.get("observation", {})
            act = p_state.get("action", {})
            
            # Extract state if available
            # If obs is present:
            # Let's check keys of obs
            # Sometimes obs contains player state, cash, inventory, farm, etc.
            # Let's parse both action and observation
            
            # Check actions for buys/sells/unlocks/hires
            if act:
                # act can be list of dicts or dict
                actions_list = act if isinstance(act, list) else [act]
                for a in actions_list:
                    if not isinstance(a, dict):
                        continue
                    atype = a.get("action_type") or a.get("type") or ""
                    # Land unlock
                    if "QUAD_UNLOCK" in str(atype) or "BUY_LAND" in str(atype) or "UNLOCK" in str(atype):
                        q = str(a.get("quadrant") or a.get("quadrants") or "")
                        if "NE" in q or "Q2" in q:
                            if q2_step is None: q2_step = step_idx
                        elif "SW" in q or "Q3" in q:
                            if q3_step is None: q3_step = step_idx
                        elif "SE" in q or "Q4" in q:
                            if q4_step is None: q4_step = step_idx
                    # Market actions
                    if "BUY_PRODUCT" in str(atype) or "BUY" in str(atype):
                        item = str(a.get("item") or a.get("product") or "")
                        amt = a.get("amount") or a.get("quantity") or 0
                        if "WHEAT" in item.upper() and not "SEED" in item.upper():
                            wheat_bought += amt
                        elif "SEED" in item.upper():
                            seeds_bought[item] = seeds_bought.get(item, 0) + amt
                    if "SELL_PRODUCT" in str(atype) or "SELL" in str(atype):
                        item = str(a.get("item") or a.get("product") or "")
                        amt = a.get("amount") or a.get("quantity") or 0
                        if "MILK" in item.upper():
                            milk_sold += amt
                        elif "WOOL" in item.upper():
                            wool_sold += amt
                        elif "FERTILIZER" in item.upper():
                            fertilizer_sold += amt
                        elif "WHEAT" in item.upper():
                            wheat_sold += amt
                        else:
                            crops_sold[item] = crops_sold.get(item, 0) + amt
                            
        final_reward = p_state.get("reward") if 'p_state' in locals() else None
        
        players_data.append({
            "file": os.path.basename(fpath),
            "p_idx": p_idx,
            "player": name,
            "reward": final_reward,
            "q2_step": q2_step,
            "q3_step": q3_step,
            "q4_step": q4_step,
            "wheat_bought": wheat_bought,
            "wheat_sold": wheat_sold,
            "milk_sold": milk_sold,
            "wool_sold": wool_sold,
            "fertilizer_sold": fertilizer_sold,
            "crops_sold": crops_sold,
            "seeds_bought": seeds_bought
        })
    return players_data

def main():
    files = glob.glob("scratch/replays/*.json")
    print(f"Analyzing {len(files)} replays in scratch/replays...")
    all_results = []
    for f in files:
        if os.path.getsize(f) < 1000:
            continue
        try:
            res = extract_episode_telemetry(f)
            all_results.extend(res)
        except Exception as e:
            # print(f"Error {f}: {e}")
            pass
            
    print(f"Extracted {len(all_results)} player trajectories.")
    with open("scratch/detailed_replays_telemetry.json", "w", encoding="utf-8") as fp:
        json.dump(all_results, fp, indent=2)

if __name__ == "__main__":
    main()
