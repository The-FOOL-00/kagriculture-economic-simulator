# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
from scripts.v32_common import load_agent

def walk_dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def shed_access_tiles():
    # 10x10 board, home quadrant is top-left or centered around [4,4], [4,5], [5,4], [5,5]
    # In kaggriculture:
    # Quadrant 0: [0..4, 0..4] with shed at [0,0]? Let's check shed location!
    # Let's check where shed tiles are!
    return [(4, 4), (4, 5), (5, 4), (5, 5), (4, 3), (3, 4), (5, 6), (6, 5)]

def analyze_seeds():
    seeds = range(249675, 249685)
    print("=" * 80)
    print("REACHABILITY & STRANDED PHYSICAL VALUE CENSUS (Development Panel 249675-249684)")
    print("=" * 80)
    
    for seed in seeds:
        a7 = load_agent("E9_AST")
        dmit = load_agent("E8_DMITRII")
        env = make("kaggriculture", configuration={"seed": seed})
        env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmit.act(o, c)])
        
        # Check Step 719 stranded values
        s719 = env.steps[-1][0]["observation"]
        f719 = s719["farms"][0]
        p719 = s719["private"]
        prices719 = s719["market"]["prices"]
        
        # Carried at 719
        carried719 = {}
        for inv in p719["inventories"]:
            for k, v in inv.items():
                if v > 0:
                    carried719[k] = carried719.get(k, 0) + v
        carried_val719 = sum(carried719.get(k, 0) * prices719.get(k, 0) for k in carried719)
        
        # Shed at 719
        shed719 = {k: v for k, v in p719["shed"].items() if v > 0}
        shed_val719 = sum(shed719.get(k, 0) * prices719.get(k, 0) for k in shed719)
        
        # Field yield at 719
        field719 = {}
        for r in f719["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    y = t.get("yield_units", 0)
                    kind = t.get("kind")
                    c = t.get("crop")
                    a = t.get("animal")
                    fert = t.get("fertilizer_available")
                    if y > 0:
                        item = c if kind == "PLANT" else ("MILK" if a == "COW" else ("WOOL" if a == "SHEEP" else ("EGG" if a == "GOOSE" else None)))
                        if item:
                            field719[item] = field719.get(item, 0) + y
                    if fert:
                        field719["FERTILIZER"] = field719.get("FERTILIZER", 0) + 1
        field_val719 = sum(field719.get(k, 0) * prices719.get(k, 0) for k in field719)
        
        a7_rew = env.steps[-1][0]["reward"]
        dm_rew = env.steps[-1][1]["reward"]
        
        print(f"Seed {seed}: A7=${a7_rew:,.0f} | Dm=${dm_rew:,.0f} | Margin={a7_rew - dm_rew:+,.0f}")
        print(f"  Stranded at 719: Carried=${carried_val719} ({carried719}), Shed=${shed_val719} ({shed719}), Field=${field_val719} ({field719})")

if __name__ == "__main__":
    analyze_seeds()
