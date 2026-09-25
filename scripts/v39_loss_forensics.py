"""
V39 Deep Loss Forensics Analyzer
Parses all 11 V35 loss episodes from scratch/v39/live/replays/
Reconstructs complete economic trajectories, first divergence, and causal signatures.
"""

import json
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPLAY_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live", "replays")
OUT_FORENSICS_JSON = os.path.join(BASE_DIR, "scratch", "v39", "loss_forensics_data.json")

LOSS_EPISODES = [
    113153701,
    113165586,
    113167894,
    113169085,
    113176099,
    113177277,
    113179717,
    113180924,
    113182085,
    113184429,
    113186749
]

def analyze_episode(ep_id):
    replay_path = os.path.join(REPLAY_DIR, f"episode-{ep_id}-replay.json")
    with open(replay_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    info = data.get("info", {})
    team_names = info.get("TeamNames", [])
    rewards = data.get("rewards", [0, 0])
    seed = info.get("seed")
    
    # Determine seat
    if len(team_names) >= 2 and team_names[1] == "Sanjay" and team_names[0] != "Sanjay":
        our_seat = 1
        opp_seat = 0
        opp_name = team_names[0]
    else:
        our_seat = 0
        opp_seat = 1
        opp_name = team_names[1] if len(team_names) > 1 else "Unknown"
        if team_names and team_names[0] == "Sanjay" and len(team_names) > 1 and team_names[1] == "Sanjay":
            opp_name = "Self/Validation"
            
    steps = data.get("steps", [])
    
    our_cash = []
    opp_cash = []
    our_hands = []
    opp_hands = []
    our_land = []
    opp_land = []
    
    our_first_hire = None
    opp_first_hire = None
    our_first_land = None
    opp_first_land = None
    
    first_meaningful_divergence = None
    cash_deficit_streak = 0
    
    for t, step in enumerate(steps):
        obs = step[0].get("observation", {})
        farms = obs.get("farms", [])
        if len(farms) < 2:
            continue
            
        f_our = farms[our_seat]
        f_opp = farms[opp_seat]
        
        m_our = f_our.get("money", 0)
        m_opp = f_opp.get("money", 0)
        our_cash.append(m_our)
        opp_cash.append(m_opp)
        
        h_our = len(f_our.get("hands", []))
        h_opp = len(f_opp.get("hands", []))
        our_hands.append(h_our)
        opp_hands.append(h_opp)
        
        if our_first_hire is None and h_our > 0:
            our_first_hire = t
        if opp_first_hire is None and h_opp > 0:
            opp_first_hire = t
            
        q_our = len(f_our.get("unlocked_quadrants", []))
        q_opp = len(f_opp.get("unlocked_quadrants", []))
        our_land.append(q_our)
        opp_land.append(q_opp)
        
        if our_first_land is None and q_our > 1:
            our_first_land = t
        if opp_first_land is None and q_opp > 1:
            opp_first_land = t
            
        # Track first sustained cash deficit (> $1,500 deficit for 15 turns)
        if m_opp - m_our > 1500:
            cash_deficit_streak += 1
            if cash_deficit_streak >= 15 and first_meaningful_divergence is None:
                first_meaningful_divergence = t - 15
        else:
            cash_deficit_streak = 0
            
    if first_meaningful_divergence is None and our_cash:
        # If no sustained midgame divergence, check when deficit permanently opened
        for t in range(len(our_cash) - 1, -1, -1):
            if our_cash[t] >= opp_cash[t]:
                first_meaningful_divergence = t + 1
                break
        if first_meaningful_divergence is None:
            first_meaningful_divergence = 0
            
    # Check step 0 actions
    step0_our_action = steps[0][our_seat].get("action")
    step0_opp_action = steps[0][opp_seat].get("action")
    
    # Check terminal liquidation change (steps 700 to 719)
    liq_start = 700 if len(our_cash) > 700 else -1
    liq_our = our_cash[-1] - our_cash[liq_start]
    liq_opp = opp_cash[-1] - opp_cash[liq_start]
    
    # Analyze trajectory at first divergence
    div_step = first_meaningful_divergence
    div_cash_our = our_cash[div_step] if div_step < len(our_cash) else our_cash[-1]
    div_cash_opp = opp_cash[div_step] if div_step < len(opp_cash) else opp_cash[-1]
    
    summary = {
        "episode_id": ep_id,
        "seed": seed,
        "opp_name": opp_name,
        "seat": our_seat,
        "our_reward": rewards[our_seat],
        "opp_reward": rewards[opp_seat],
        "margin": rewards[our_seat] - rewards[opp_seat],
        "first_divergence_step": div_step,
        "div_cash_our": div_cash_our,
        "div_cash_opp": div_cash_opp,
        "our_first_hire": our_first_hire,
        "opp_first_hire": opp_first_hire,
        "our_first_land": our_first_land,
        "opp_first_land": opp_first_land,
        "our_terminal_hands": our_hands[-1] if our_hands else 0,
        "opp_terminal_hands": opp_hands[-1] if opp_hands else 0,
        "our_terminal_quadrants": our_land[-1] if our_land else 0,
        "opp_terminal_quadrants": opp_land[-1] if opp_land else 0,
        "terminal_liquidation_delta": liq_our - liq_opp,
        "step0_our_action": step0_our_action,
        "step0_opp_action": step0_opp_action,
        "trajectory_divergence_summary": (
            f"Step {div_step}: Us ${div_cash_our:,.0f} vs Opp ${div_cash_opp:,.0f}. "
            f"Final Hands Us {our_hands[-1]} vs Opp {opp_hands[-1]}, "
            f"Land Us {our_land[-1]} vs Opp {opp_land[-1]}."
        )
    }
    
    return summary

def main():
    print(f"Analyzing all {len(LOSS_EPISODES)} loss episodes...")
    all_summaries = []
    for ep_id in LOSS_EPISODES:
        s = analyze_episode(ep_id)
        all_summaries.append(s)
        print(f"Ep {s['episode_id']} | Seed {s['seed']} | Margin ${s['margin']:,.0f} | "
              f"Div Step {s['first_divergence_step']} | "
              f"Hands Us {s['our_terminal_hands']} vs Opp {s['opp_terminal_hands']} | "
              f"Land Us {s['our_terminal_quadrants']} vs Opp {s['opp_terminal_quadrants']} | "
              f"Liq $\\Delta$ ${s['terminal_liquidation_delta']:,.0f} | Opp: {s['opp_name']}")
              
    with open(OUT_FORENSICS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2)
        
    print(f"\nSaved forensics data to {OUT_FORENSICS_JSON}")

if __name__ == "__main__":
    main()
