import os
import sys
import json
import time
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def analyze_match_timeline(agent0_path, agent1_path, seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent0_path, agent1_path])
    
    steps = env.steps
    timeline = []
    
    # Sample every day (every 24 steps)
    for d in range(30):
        step_idx = min(len(steps) - 1, d * 24 + 23)
        s = steps[step_idx]
        obs0 = s[0].observation
        
        farm0 = obs0.farms[0]
        farm1 = obs0.farms[1]
        
        priv0 = steps[step_idx][0].observation.private or {}
        priv1 = steps[step_idx][1].observation.private or {}
        
        shed0 = priv0.get("shed", {})
        shed1 = priv1.get("shed", {})
        
        # Count animals & plants
        def count_assets(tiles):
            cows, sheep, geese, melons, carrots, wheat = 0, 0, 0, 0, 0, 0
            for row in tiles:
                for t in row:
                    if isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "PASTURE" and t.get("animal") == "COW": cows += 1
                        elif kind == "PASTURE" and t.get("animal") == "SHEEP": sheep += 1
                        elif kind == "COOP" and t.get("animal") == "GOOSE": geese += 1
                        elif kind == "PLANT":
                            c = t.get("crop")
                            if c == "MELON": melons += 1
                            elif c == "CARROT": carrots += 1
                            elif c == "WHEAT": wheat += 1
            return {"cows": cows, "sheep": sheep, "geese": geese, "melons": melons, "carrots": carrots, "wheat": wheat}
        
        a0 = count_assets(farm0["tiles"])
        a1 = count_assets(farm1["tiles"])
        
        timeline.append({
            "day": d,
            "cash0": farm0["money"],
            "cash1": farm1["money"],
            "diff": farm0["money"] - farm1["money"],
            "hands0": len(farm0.get("hands", [])),
            "hands1": len(farm1.get("hands", [])),
            "unlocked0": len(farm0.get("unlocked_quadrants", [])),
            "unlocked1": len(farm1.get("unlocked_quadrants", [])),
            "assets0": a0,
            "assets1": a1,
            "shed0": {k: v for k, v in shed0.items() if v > 0},
            "shed1": {k: v for k, v in shed1.items() if v > 0},
            "market_prices": dict(obs0.market.get("prices", {}))
        })
        
    final_r0 = steps[-1][0].reward
    final_r1 = steps[-1][1].reward
    return {
        "seed": seed,
        "final_r0": final_r0,
        "final_r1": final_r1,
        "winner": 0 if final_r0 > final_r1 else (1 if final_r1 > final_r0 else -1),
        "timeline": timeline
    }

if __name__ == "__main__":
    ctrl = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")
    titan = os.path.join(project_root, "opponents", "o1_titan.py")
    
    print("Forensic match timeline analysis...")
    # Find a match where control loses to Titan
    for s in [50001, 50002, 50003, 50004, 50005]:
        # P0 Control vs P1 Titan
        res = analyze_match_timeline(ctrl, titan, s)
        print(f"Seed {s} (Control P0 vs Titan P1): Control=${res['final_r0']:,.2f} | Titan=${res['final_r1']:,.2f} | Winner: {'Control' if res['winner']==0 else 'Titan'}")
        
        # P0 Titan vs P1 Control
        res_sw = analyze_match_timeline(titan, ctrl, s)
        print(f"Seed {s} (Titan P0 vs Control P1): Titan=${res_sw['final_r0']:,.2f} | Control=${res_sw['final_r1']:,.2f} | Winner: {'Titan' if res_sw['winner']==0 else 'Control'}")
