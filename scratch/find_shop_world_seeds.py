import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
import kagsim

def scan_shop_pairs(start_seed=50000, n_seeds=3000):
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    pair_to_seeds = {}
    
    for s in range(start_seed, start_seed + n_seeds):
        game = kagsim.Game(s)
        # Advance to step 145 to unlock first 2 shops
        for _ in range(145):
            game.step(idle, idle)
        obs = game.observe(0)
        shops = obs["town"]["unlocked_shops"]
        s0 = shops[0] if len(shops) > 0 else "NONE"
        s1 = shops[1] if len(shops) > 1 else "NONE"
        pair = (s0, s1)
        if pair not in pair_to_seeds:
            pair_to_seeds[pair] = []
        pair_to_seeds[pair].append(s)
        
    print(f"Scanned {n_seeds} seeds ({start_seed}..{start_seed + n_seeds - 1})")
    
    # Target pairs
    targets = [
        ("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"),
        ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP"),
        ("PIZZA_SHOP", "ICE_CREAM_SHOP"),
        ("ICE_CREAM_SHOP", "PIZZA_SHOP"),
        ("PIZZA_SHOP", "BAKERY"),
        ("BRUNCH_SPOT", "FARMERS_MARKET"),
        ("FARMERS_MARKET", "BAKERY"),
    ]
    
    results = {}
    for t in targets:
        s_list = pair_to_seeds.get(t, [])
        print(f"  {t[0]} + {t[1]}: {len(s_list)} seeds found")
        results[f"{t[0]}+{t[1]}"] = s_list
        
    out_file = os.path.join(BASE_DIR, "scratch", "shop_world_seeds.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    scan_shop_pairs()
