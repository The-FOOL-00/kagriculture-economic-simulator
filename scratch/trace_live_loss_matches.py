import json
import os
import pandas as pd

loss_files = [
    ("scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json", "KawattaTaido"),
    ("scratch/replays/V2_Loss_vs_KawattaTaido_104802423.json", "KawattaTaido"),
    ("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json", "Yuyajk"),
    ("scratch/replays/V2_Loss_vs_GAYATHRI SALINI_104796498.json", "GAYATHRI SALINI"),
    ("scratch/replays/V2_Loss_vs_qihuaz_104813423.json", "qihuaz")
]

def analyze_loss_match(fpath, opp_name):
    if not os.path.exists(fpath):
        print(f"File {fpath} not found!")
        return
        
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps")
    agents = data.get("agents") or data.get("info", {}).get("Agents") or []
    
    # Identify which player is V2 and which is opponent
    # V2 usually plays with name Eldritch or similar in these internal traces
    # Let's check rewards in final step
    last_step = steps[-1]
    r0 = last_step[0].get("reward")
    r1 = last_step[1].get("reward")
    
    # Let's inspect turn-by-turn prices and sales
    # Key commodities: WHEAT, FERTILIZER, MILK, WOOL, MELON, STRAWBERRY
    timeline = []
    for s_idx, step in enumerate(steps):
        day = s_idx // 24
        hour = s_idx % 24
        
        # Check market prices
        market_obs = step[0].get("observation", {}).get("market", {})
        # market_obs typically has prices or bids/asks
        
        # Actions of P0 and P1
        act0 = step[0].get("action", {})
        act1 = step[1].get("action", {})
        
        # Cash of P0 and P1
        farms = step[0].get("observation", {}).get("farms", [])
        m0 = farms[0].get("money", 0) if len(farms) > 0 else 0
        m1 = farms[1].get("money", 0) if len(farms) > 1 else 0
        
        if s_idx in [24, 72, 122, 168, 200, 255, 264, 360, 500, 650, 719]:
            timeline.append({
                "step": s_idx,
                "day": day,
                "hour": hour,
                "P0_cash": m0,
                "P1_cash": m1,
                "market_sample": {k: v.get("price") if isinstance(v, dict) else v for k, v in list(market_obs.items())[:6]} if isinstance(market_obs, dict) else str(market_obs)[:60]
            })
            
    print(f"\n=======================================================")
    print(f"LOSS MATCH FORENSICS: {os.path.basename(fpath)}")
    print(f"Final Rewards -> P0: {r0} | P1: {r1}")
    print(f"=======================================================")
    for t in timeline:
        print(f"Step {t['step']:3d} (D{t['day']:02d}:H{t['hour']:02d}) | P0: ${t['P0_cash']:8.1f} | P1: ${t['P1_cash']:8.1f} | Market: {t['market_sample']}")

for fpath, opp in loss_files:
    analyze_loss_match(fpath, opp)
