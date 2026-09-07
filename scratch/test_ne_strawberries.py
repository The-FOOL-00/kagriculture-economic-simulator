import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import numpy as np

from scratch.test_hybrid_features import HybridCandidate

class NEStrawberryHybrid(HybridCandidate):
    """
    Candidate with NE Strawberry Exploitation (Day 7+) & NW Strawberry Replanting.
    """
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        # Day 7-9 NE Strawberry procurement!
        # When NE is unlocked, buy 12 strawberry seeds aggressively!
        if hour == 0 and 7 <= day <= 9 and "NE" in quads and len(orders) < 9:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 16
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100
        return orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # Allow planting strawberries in NE on empty tiles starting Day 7!
        if "NE" in quads and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day >= 7:
            for y in range(5):
                for x in range(5, 10):
                    pos = (x, y)
                    if tiles[y][x] is None and pos not in res["plant_s"] and pos not in res.get("target_pasture_slots", set()):
                        res["plant_s"].append(pos)
                        
        # Allow planting strawberries in NW on empty tiles after wheat is harvested (Day 5+)!
        if int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day >= 5:
            for y in range(5):
                for x in range(5):
                    pos = (x, y)
                    if tiles[y][x] is None and pos not in res["plant_s"] and pos not in res.get("target_pasture_slots", set()):
                        res["plant_s"].append(pos)
                        
        return res

if __name__ == '__main__':
    print("Testing NEStrawberryHybrid across seeds 42, 100, 2024...")
    agent_inst = NEStrawberryHybrid()
    def agent(obs, cfg=None): return agent_inst(obs, cfg)
    
    scores = []
    for s in [42, 100, 2024]:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
        env.run([agent, starter])
        sc = env.steps[-1][0]['reward']
        scores.append(sc)
        print(f"  Seed {s}: Final Bank = ${sc:,.1f}")
    print(f"Mean Score: ${np.mean(scores):,.1f} +/- {np.std(scores):,.1f}")
