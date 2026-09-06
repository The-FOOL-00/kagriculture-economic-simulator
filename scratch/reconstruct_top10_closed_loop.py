import os
import sys
import json
import glob
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# List of replay sets by team
teams = {
    "MtN": [
        "scratch/replays/MtN_104821772.json",
        "scratch/replays/MtN_104823472.json",
        "scratch/replays/MtN_104824200.json"
    ],
    "Crop_Dusta": [
        "scratch/replays/Crop_Dusta_104821339.json",
        "scratch/replays/Crop_Dusta_104823501.json",
        "scratch/replays/Crop_Dusta_104824599.json"
    ],
    "Yuan800": [
        "scratch/replays/Yuan800_104822515.json",
        "scratch/replays/Yuan800_104823350.json",
        "scratch/replays/Yuan800_104824200.json"
    ],
    "Whyme_Labs": [
        "scratch/replays/Whyme_Labs_104821658.json",
        "scratch/replays/Whyme_Labs_104821944.json",
        "scratch/replays/Whyme_Labs_104824599.json"
    ],
    "KawattaTaido": [
        "scratch/replays/V2_Loss_vs_KawattaTaido_104802423.json",
        "scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json"
    ]
}

def parse_replay_agent(fpath, target_team_name):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps", [])
    info = data.get("info", {})
    description = data.get("description", "")
    
    # Identify player index for target_team_name
    # Check first step observation
    obs0 = steps[0][0].get("observation", {})
    # In some replays, teamName is in step info or metadata
    # If not explicitly named in obs, check rewards or match against opponent
    # Let's inspect step 0 and last step
    p_idx = None
    
    # Try to find player index by matching team name in filename or agents info
    # For V2_Loss_vs_KawattaTaido, Player 0 is KawattaTaido (P0 reward ~114k/128k)
    if "KawattaTaido" in target_team_name:
        p_idx = 0
    elif "MtN" in target_team_name:
        # In 104824200, MtN is Player 1 (reward 64658 vs Yuan 81346) or check other matches
        # Let's check which player has the MtN strategy
        p_idx = 0 if "MtN_104824200.json" in fpath and steps[-1][0].get("reward", 0) > steps[-1][1].get("reward", 0) else 1
    else:
        # Default check player with higher reward or check action footprint
        p_idx = 0
        
    # Extract turn-by-turn detailed trace
    trace = []
    for step_idx, step in enumerate(steps):
        day = step_idx // 24
        hour = step_idx % 24
        
        # Check both players' observations
        # Public state is in step[0].observation
        pub_obs = step[0].get("observation", {})
        farms = pub_obs.get("farms", [{}, {}])
        
        # In competition replays, farm 0 corresponds to player 0, farm 1 to player 1
        # Let's extract for both player 0 and player 1 to be fully rigorous
        f0 = farms[0] if len(farms) > 0 else {}
        f1 = farms[1] if len(farms) > 1 else {}
        
        town = pub_obs.get("town", {})
        shops = town.get("unlocked_shops", [])
        
        market = pub_obs.get("market", {})
        prices = market.get("prices", {})
        inventory = market.get("inventory", {})
        
        act0 = step[0].get("action", {}) or {}
        act1 = step[1].get("action", {}) or {}
        
        trace.append({
            'step': step_idx,
            'day': day,
            'hour': hour,
            'shops': list(shops),
            'prices': dict(prices),
            'inventory': dict(inventory),
            'f0_money': f0.get("money", 0),
            'f1_money': f1.get("money", 0),
            'f0_hands': len(f0.get("hands", [])),
            'f1_hands': len(f1.get("hands", [])),
            'f0_quads': list(f0.get("unlocked_quadrants", [])),
            'f1_quads': list(f1.get("unlocked_quadrants", [])),
            'act0': act0,
            'act1': act1,
            'reward0': step[0].get("reward", 0),
            'reward1': step[1].get("reward", 0)
        })
        
    return trace

# 1. Multi-game action identity audit (Open-Loop vs Closed-Loop)
print("=" * 90)
print("1. MULTI-GAME ACTION IDENTITY AUDIT (OPEN-LOOP vs CLOSED-LOOP)")
print("=" * 90)

for team_name, file_list in teams.items():
    print(f"\n--- Analyzing {team_name} across {len(file_list)} available games ---")
    valid_traces = []
    for f in file_list:
        if os.path.exists(f) and os.path.getsize(f) > 100000:
            tr = parse_replay_agent(f, team_name)
            valid_traces.append((os.path.basename(f), tr))
            
    print(f"Loaded {len(valid_traces)} valid complete replay traces for {team_name}")
    
    if len(valid_traces) >= 2:
        name1, tr1 = valid_traces[0]
        name2, tr2 = valid_traces[1]
        
        # Compare act0 actions between game 1 and game 2
        identical_farmer_actions = 0
        identical_market_actions = 0
        total_steps = min(len(tr1), len(tr2))
        
        diff_events = []
        for s in range(total_steps):
            a1 = tr1[s]['act0']
            a2 = tr2[s]['act0']
            
            f_match = (a1.get('farmer') == a2.get('farmer'))
            m_match = (a1.get('market') == a2.get('market'))
            h_match = (a1.get('hands') == a2.get('hands'))
            
            if f_match: identical_farmer_actions += 1
            if m_match: identical_market_actions += 1
            
            if not f_match or not m_match or not h_match:
                if len(diff_events) < 10:
                    diff_events.append((s, tr1[s]['day'], tr1[s]['hour'], a1, a2))
                    
        f_pct = (identical_farmer_actions / total_steps) * 100
        m_pct = (identical_market_actions / total_steps) * 100
        
        print(f"Comparison between {name1} and {name2}:")
        print(f"  Farmer Action Identity: {f_pct:.1f}% ({identical_farmer_actions}/{total_steps} turns)")
        print(f"  Market Action Identity: {m_pct:.1f}% ({identical_market_actions}/{total_steps} turns)")
        
        if f_pct > 95.0 and m_pct > 95.0:
            print(f"  >> CLASSIFICATION: OPEN-LOOP TAPE (Shared static tape across games)")
        elif f_pct > 50.0:
            print(f"  >> CLASSIFICATION: PARTIALLY ADAPTIVE / SHARED TRACE WITH EARLY BRANCHING")
        else:
            print(f"  >> CLASSIFICATION: DYNAMIC CLOSED-LOOP AGENT (Fully state-responsive)")
            
        if diff_events:
            print(f"  Earliest action divergence point: Step {diff_events[0][0]} (Day {diff_events[0][1]}, Hour {diff_events[0][2]})")

