import os
import sys
import json
import time
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def analyze_losses(cand_path, opp_path, seeds):
    losses = []
    wins = []
    
    print(f"\nAnalyzing Matchups: {os.path.basename(cand_path)} vs {os.path.basename(opp_path)} across {len(seeds)*2} matches...")
    
    for s in seeds:
        # Match A: Cand as P0, Opp as P1
        cfg = {"episodeSteps": 720, "seed": s}
        env = make("kaggriculture", configuration=cfg, debug=False)
        env.run([cand_path, opp_path])
        s0 = env.steps[-1]
        r_cand_p0 = float(s0[0].reward or 0.0)
        r_opp_p1 = float(s0[1].reward or 0.0)
        margin_p0 = r_cand_p0 - r_opp_p1
        
        if margin_p0 < 0:
            losses.append({"seed": s, "cand_side": "P0", "r_cand": r_cand_p0, "r_opp": r_opp_p1, "margin": margin_p0, "steps": env.steps})
        else:
            wins.append({"seed": s, "cand_side": "P0", "r_cand": r_cand_p0, "r_opp": r_opp_p1, "margin": margin_p0})
            
        # Match B: Opp as P0, Cand as P1
        env2 = make("kaggriculture", configuration=cfg, debug=False)
        env2.run([opp_path, cand_path])
        s1 = env2.steps[-1]
        r_opp_p0 = float(s1[0].reward or 0.0)
        r_cand_p1 = float(s1[1].reward or 0.0)
        margin_p1 = r_cand_p1 - r_opp_p0
        
        if margin_p1 < 0:
            losses.append({"seed": s, "cand_side": "P1", "r_cand": r_cand_p1, "r_opp": r_opp_p0, "margin": margin_p1, "steps": env2.steps})
        else:
            wins.append({"seed": s, "cand_side": "P1", "r_cand": r_cand_p1, "r_opp": r_opp_p0, "margin": margin_p1})

    print(f"Total Games: {len(wins)+len(losses)} | Wins: {len(wins)} ({len(wins)/(len(wins)+len(losses))*100:.1f}%) | Losses: {len(losses)} ({len(losses)/(len(wins)+len(losses))*100:.1f}%)")
    
    p0_losses = [l for l in losses if l["cand_side"] == "P0"]
    p1_losses = [l for l in losses if l["cand_side"] == "P1"]
    print(f"Loss breakdown: P0 losses = {len(p0_losses)} / {len(seeds)} ({len(p0_losses)/len(seeds)*100:.1f}%) | P1 losses = {len(p1_losses)} / {len(seeds)} ({len(p1_losses)/len(seeds)*100:.1f}%)")
    
    # Analyze the most severe losses
    losses.sort(key=lambda x: x["margin"])
    print("\nTop 5 Worst Losses Forensics:")
    for i, l in enumerate(losses[:5]):
        print(f"\n--- Worst Loss #{i+1}: Seed {l['seed']} ({l['cand_side']}) | Margin: ${l['margin']:+,.2f} (Cand: ${l['r_cand']:,.2f} vs Opp: ${l['r_opp']:,.2f}) ---")
        steps = l["steps"]
        cand_idx = 0 if l["cand_side"] == "P0" else 1
        opp_idx = 1 - cand_idx
        
        # Check Day 5, Day 10, Day 15, Day 20, Day 25, Day 29
        for d in [2, 5, 10, 15, 20, 25, 29]:
            step_num = min(len(steps)-1, d * 24 + 23)
            st = steps[step_num]
            f_cand = st[0].observation.farms[cand_idx]
            f_opp = st[0].observation.farms[opp_idx]
            
            p_cand = st[cand_idx].observation.private or {}
            p_opp = st[opp_idx].observation.private or {}
            
            shed_cand = p_cand.get("shed", {})
            shed_opp = p_opp.get("shed", {})
            
            m_prices = st[0].observation.market.get("prices", {})
            
            # Count livestock & crops
            def get_counts(tiles):
                c, s, g, m, cr, w = 0, 0, 0, 0, 0, 0
                unfed = 0
                for row in tiles:
                    for tile in row:
                        if isinstance(tile, dict):
                            k = tile.get("kind")
                            if k == "PASTURE" and tile.get("animal") == "COW": 
                                c += 1
                                if not tile.get("fed_today"): unfed += 1
                            elif k == "PASTURE" and tile.get("animal") == "SHEEP": 
                                s += 1
                                if not tile.get("fed_today"): unfed += 1
                            elif k == "COOP" and tile.get("animal") == "GOOSE": g += 1
                            elif k == "PLANT":
                                crp = tile.get("crop")
                                if crp == "MELON": m += 1
                                elif crp == "CARROT": cr += 1
                                elif crp == "WHEAT": w += 1
                return c, s, g, m, cr, w, unfed
            
            c0, s0, g0, m0, cr0, w0, unfed0 = get_counts(f_cand["tiles"])
            c1, s1, g1, m1, cr1, w1, unfed1 = get_counts(f_opp["tiles"])
            
            print(f"  Day {d:2d} (Step {step_num:3d}):")
            print(f"    Cand: Cash=${f_cand['money']:7,.0f} | Cows={c0} Sheep={s0} Melons={m0} Carrots={cr0} WheatInShed={shed_cand.get('WHEAT',0)} Hands={len(f_cand.get('hands',[]))}")
            print(f"    Opp:  Cash=${f_opp['money']:7,.0f} | Cows={c1} Sheep={s1} Melons={m1} Carrots={cr1} WheatInShed={shed_opp.get('WHEAT',0)} Hands={len(f_opp.get('hands',[]))}")
            print(f"    Diff: ${f_cand['money'] - f_opp['money']:+7,.0f} | Prices: Melon=${m_prices.get('MELON',0)} Milk=${m_prices.get('MILK',0)} Wool=${m_prices.get('WOOL',0)} Carrot=${m_prices.get('CARROT',0)}")

if __name__ == "__main__":
    ctrl = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
    titan = os.path.join(project_root, "opponents", "o1_titan.py")
    
    seeds = [50000 + i for i in range(25)]
    analyze_losses(ctrl, titan, seeds)
