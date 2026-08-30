"""
Debug forensic match: Trace turn-by-turn why hybrid_8c4s_15m_feed_insulated.py scored $9.6k
"""
import os
import sys
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
cand_path = os.path.join(project_root, "agents", "hybrid_8c4s_15m_feed_insulated.py")
titan_path = os.path.join(project_root, "opponents", "o1_titan.py")

cfg = {"episodeSteps": 720, "seed": 40001}
env = make("kaggriculture", configuration=cfg, debug=True)
env.run([cand_path, titan_path])

steps = env.steps
print(f"Final Step 0 (Cand) Reward: {steps[-1][0].reward}")
print(f"Final Step 1 (Titan) Reward: {steps[-1][1].reward}")
print(f"Step 0 Status: {steps[-1][0].status}, Step 1 Status: {steps[-1][1].status}")

# Print sample days
for d in [0, 1, 2, 3, 5, 8, 10, 12, 15, 20, 25, 29]:
    s_idx = min(719, d * 24)
    obs = steps[s_idx][0].get("observation", {})
    farms = obs.get("farms", [{}, {}])
    m0 = farms[0].get("money", 0)
    m1 = farms[1].get("money", 0)
    t0 = farms[0].get("tiles", [])
    t1 = farms[1].get("tiles", [])
    
    def count_animals_crops(tiles):
        cows, sheep, melons, wheat = 0, 0, 0, 0
        for r in tiles:
            for c in r:
                if isinstance(c, dict):
                    k = c.get("kind")
                    if k == "PASTURE":
                        if c.get("animal") == "COW": cows += 1
                        elif c.get("animal") == "SHEEP": sheep += 1
                    elif k == "PLANT":
                        if c.get("crop") == "MELON": melons += 1
                        elif c.get("crop") == "WHEAT": wheat += 1
        return cows, sheep, melons, wheat
    
    c0, s0, m_c0, w0 = count_animals_crops(t0)
    c1, s1, m_c1, w1 = count_animals_crops(t1)
    
    mkt = obs.get("market", {}) or {}
    wp = mkt.get("prices", {}).get("WHEAT", 25)
    
    print(f"Day {d:2d} | Cand: Cash ${m0:6,.0f}, Herd {c0}C/{s0}S, Crops {m_c0}M/{w0}W | Titan: Cash ${m1:6,.0f}, Herd {c1}C/{s1}S, Crops {m_c1}M/{w1}W | Wheat Price: ${wp}")
