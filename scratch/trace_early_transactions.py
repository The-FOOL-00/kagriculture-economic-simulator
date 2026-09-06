import json

def trace_early_transactions(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps")
    print(f"\n=======================================================")
    print(f"EARLY CASHFLOW TRACE (Steps 0-264): {fpath}")
    print(f"=======================================================")
    
    for s_idx in range(265):
        step = steps[s_idx]
        day = s_idx // 24
        hour = s_idx % 24
        
        for p_idx in [0, 1]:
            act = step[p_idx].get("action", {})
            market_acts = act.get("market", []) if isinstance(act, dict) else []
            farm = step[p_idx].get("observation", {}).get("farms", [{}])[p_idx]
            money = farm.get("money", 0) if isinstance(farm, dict) else 0
            
            # Print any turn with market actions
            if market_acts:
                # Filter sells/buys
                print(f"Step {s_idx:3d} (D{day:02d}:H{hour:02d}) | P{p_idx} (Cash: ${money:7.1f}) -> Market: {market_acts}")

trace_early_transactions("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json")
trace_early_transactions("scratch/replays/V2_Loss_vs_GAYATHRI SALINI_104796498.json")
