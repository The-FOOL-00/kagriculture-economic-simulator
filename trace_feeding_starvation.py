"""
Trace worker feeding and inventory on Days 15-18
"""
import os
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
cand_path = os.path.join(project_root, "agents", "hybrid_8c4s_15m_feed_insulated.py")
titan_path = os.path.join(project_root, "opponents", "o1_titan.py")

cfg = {"episodeSteps": 720, "seed": 40001}
env = make("kaggriculture", configuration=cfg, debug=True)
env.run([cand_path, titan_path])

for step_idx in range(15 * 24, 18 * 24):
    s = env.steps[step_idx]
    day = step_idx // 24
    hour = step_idx % 24
    obs = s[0].get("observation", {})
    priv = obs.get("private", {})
    shed = priv.get("shed", {})
    invs = priv.get("inventories", [])
    farms = obs.get("farms", [])
    tiles = farms[0].get("tiles", [])
    
    unfed = 0
    animals = 0
    for r in tiles:
        for c in r:
            if isinstance(c, dict) and c.get("kind") == "PASTURE" and c.get("animal"):
                animals += 1
                if not c.get("fed_today", False):
                    unfed += 1
    
    farmer_act = s[0].get("action", {}).get("farmer", ["PASS"])
    hands_acts = s[0].get("action", {}).get("hands", [])
    mkt_orders = s[0].get("action", {}).get("market", [])
    
    if hour == 0 or hour == 12 or hour == 23 or unfed > 0:
        print(f"Day {day:2d} Hr {hour:2d} | Animals {animals}, Unfed {unfed} | Shed Wheat {shed.get('WHEAT', 0)}, Invs Wheat {[inv.get('WHEAT', 0) for inv in invs]} | Mkt: {mkt_orders[:2]} | Acts: {[farmer_act] + hands_acts}")
