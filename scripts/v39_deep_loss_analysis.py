"""
V39 Deep Loss Analysis on the 6 Real V35 Losses
Reconstructs exact timelines, first divergences, and causal mechanisms.
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPLAY_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live", "replays")

THE_6_LOSSES = [
    {"eid": 113153701, "seat": 0, "opp": "Self-Play Validation", "seed": 0, "margin": -640},
    {"eid": 113164394, "seat": 1, "opp": "junxing peng", "seed": 1722133329, "margin": -1988},
    {"eid": 113166778, "seat": 1, "opp": "NonCaffeine", "seed": 2020456157, "margin": -2247},
    {"eid": 113171441, "seat": 1, "opp": "Lisan al-Gaib", "seed": 194590906, "margin": -996},
    {"eid": 113177277, "seat": 0, "opp": "Adhiraj Jagtap", "seed": 203942858, "margin": -11630},
    {"eid": 113183263, "seat": 1, "opp": "Yassine Chritt", "seed": 124304182, "margin": -791},
]

def analyze_loss(loss_info):
    eid = loss_info["eid"]
    seat = loss_info["seat"]
    opp_seat = 1 - seat
    path = os.path.join(REPLAY_DIR, f"episode-{eid}-replay.json")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data["steps"]
    
    # Milestone detection
    v35_hires = []
    opp_hires = []
    v35_lands = {}
    opp_lands = {}
    v35_animals = []
    opp_animals = []
    
    cash_history_v35 = []
    cash_history_opp = []
    
    opp_step1_market = steps[1][opp_seat].get("action", {}).get("market", [])
    v35_step1_market = steps[1][seat].get("action", {}).get("market", [])
    
    prev_v35_h = 0
    prev_opp_h = 0
    prev_v35_q = set()
    prev_opp_q = set()
    
    first_div_step = None
    first_div_reason = None
    
    for t, step in enumerate(steps):
        f_v35 = step[0]["observation"]["farms"][seat]
        f_opp = step[0]["observation"]["farms"][opp_seat]
        
        m_v35 = f_v35.get("money", 0)
        m_opp = f_opp.get("money", 0)
        cash_history_v35.append(m_v35)
        cash_history_opp.append(m_opp)
        
        h_v35 = len(f_v35.get("hands", []))
        h_opp = len(f_opp.get("hands", []))
        if h_v35 > prev_v35_h:
            v35_hires.append((t, h_v35))
            prev_v35_h = h_v35
        if h_opp > prev_opp_h:
            opp_hires.append((t, h_opp))
            prev_opp_h = h_opp
            
        q_v35 = set(f_v35.get("unlocked_quadrants", []))
        q_opp = set(f_opp.get("unlocked_quadrants", []))
        for q in q_v35 - prev_v35_q:
            v35_lands[q] = t
        for q in q_opp - prev_opp_q:
            opp_lands[q] = t
        prev_v35_q = q_v35
        prev_opp_q = q_opp
        
        # Divergence check: when did opponent start pulling ahead?
        if first_div_step is None and t > 50:
            if m_opp - m_v35 > 1000:
                first_div_step = t
                first_div_reason = f"Opp cash ${m_opp:,.0f} vs V35 ${m_v35:,.0f} (diff +${m_opp - m_v35:,.0f})"
                
    if first_div_step is None:
        first_div_step = 700
        first_div_reason = "Late terminal liquidation delta"
        
    print(f"\n=======================================================")
    print(f"LOSS ANALYSIS: Episode {eid} | Opponent: {loss_info['opp']} | Seed: {loss_info['seed']}")
    print(f"Final Scores: V35 ${cash_history_v35[-1]:,.0f} vs Opp ${cash_history_opp[-1]:,.0f} | Margin: ${loss_info['margin']:,.0f}")
    print(f"Seat: V35 in Seat {seat} | Opp in Seat {opp_seat}")
    print(f"Step 1 Opp Opening Market: {opp_step1_market}")
    print(f"First Divergence: Step {first_div_step} ({first_div_reason})")
    print(f"Workers: V35 final {prev_v35_h} ({v35_hires[:4]}...) vs Opp final {prev_opp_h} ({opp_hires[:4]}...)")
    print(f"Land Unlocks: V35 {v35_lands} vs Opp {opp_lands}")
    
    # Trajectory checkpoints
    print("Checkpoint Cash:")
    for cp in [24, 72, 144, 288, 432, 576, 700, 719]:
        if cp < len(cash_history_v35):
            print(f"  Step {cp:03d} (Day {cp//24:02d}): V35 ${cash_history_v35[cp]:,.0f} vs Opp ${cash_history_opp[cp]:,.0f} (Diff: ${cash_history_v35[cp] - cash_history_opp[cp]:+,.0f})")

def main():
    for l in THE_6_LOSSES:
        analyze_loss(l)

if __name__ == "__main__":
    main()
