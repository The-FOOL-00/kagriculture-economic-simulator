"""
Empirical Shop Transition Model & Value of Information Engine for Kaggriculture.
Analyzes offline seed corpus under physical simulation to compute:
1. Conditional probability tables for future shop unlocks given visible shops at Days 3, 6, 9, 12, 15, 18, 21, 24.
2. Demand profile projections (Strawberry, Tomato, Carrot, Wool, Dairy).
3. Value of Information (VoI) for waiting from Day 11 to Day 12.
"""
import os
import sys
import json
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

# Shop product demands mapping
SHOP_DEMANDS = {
    "BAKERY": ["WHEAT", "EGG"],
    "BRUNCH_SPOT": ["EGG", "MILK", "STRAWBERRY"],
    "FARMERS_MARKET": ["CARROT", "TOMATO", "STRAWBERRY", "MELON"],
    "ICE_CREAM_SHOP": ["MILK", "STRAWBERRY"],
    "PET_CAFE": ["CARROT", "MILK"],
    "PIZZA_SHOP": ["WHEAT", "TOMATO"],
    "SMOOTHIE_SHOP": ["CARROT", "STRAWBERRY", "MELON"],
    "YARN_STORE": ["WOOL"]
}

STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
TOMATO_SHOPS = {"PIZZA_SHOP", "FARMERS_MARKET"}
CARROT_SHOPS = {"PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET"}
DAIRY_SHOPS = {"BRUNCH_SPOT", "ICE_CREAM_SHOP", "PET_CAFE"}
WOOL_SHOPS = {"YARN_STORE"}

def extract_shop_trajectories(seeds: List[int]) -> Dict[int, List[str]]:
    """
    Extracts the true 8-shop unlock sequence for each seed under Dmitrii baseline.
    """
    trajectories = {}
    p_dmitrii = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    for s in seeds:
        g = kagsim.Game(s)
        p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        p2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        # Step through 576 steps (Day 24, when all 8 shops unlocked)
        for _ in range(576):
            g.step(p1.act(g.observe(0)), p2.act(g.observe(1)))
        shops = list(g.observe(0)["town"]["unlocked_shops"])
        trajectories[s] = shops
    return trajectories

def analyze_conditional_distributions(trajectories: Dict[int, List[str]]):
    """
    Computes conditional future-shop probabilities for each Day-6 visible pair.
    """
    # Key: tuple of first 2 shops -> statistics on remaining 6 shops
    pair_stats = defaultdict(lambda: {
        "count": 0,
        "future_strawberry_count": 0,
        "future_tomato_count": 0,
        "future_carrot_count": 0,
        "future_wool_count": 0,
        "future_dairy_count": 0,
        "next_shop_distribution": Counter(),
        "total_future_strawberry_shops": [],
        "total_future_tomato_shops": []
    })
    
    total_seeds = len(trajectories)
    for s, shops in trajectories.items():
        if len(shops) < 8:
            continue
        visible_d6 = tuple(shops[:2])
        future_shops = shops[2:]
        
        stat = pair_stats[visible_d6]
        stat["count"] += 1
        
        has_straw = any(shop in STRAWBERRY_SHOPS for shop in future_shops)
        has_tom = any(shop in TOMATO_SHOPS for shop in future_shops)
        has_car = any(shop in CARROT_SHOPS for shop in future_shops)
        has_wool = any(shop in WOOL_SHOPS for shop in future_shops)
        has_dairy = any(shop in DAIRY_SHOPS for shop in future_shops)
        
        if has_straw: stat["future_strawberry_count"] += 1
        if has_tom: stat["future_tomato_count"] += 1
        if has_car: stat["future_carrot_count"] += 1
        if has_wool: stat["future_wool_count"] += 1
        if has_dairy: stat["future_dairy_count"] += 1
        
        # Next shop (Day 9 unlock, index 2)
        stat["next_shop_distribution"][shops[2]] += 1
        
        # Count number of strawberry shops in future
        straw_cnt = sum(1 for shop in future_shops if shop in STRAWBERRY_SHOPS)
        tom_cnt = sum(1 for shop in future_shops if shop in TOMATO_SHOPS)
        stat["total_future_strawberry_shops"].append(straw_cnt)
        stat["total_future_tomato_shops"].append(tom_cnt)
        
    summary = {}
    for pair, stat in pair_stats.items():
        n = stat["count"]
        summary[str(pair)] = {
            "n_samples": n,
            "p_future_strawberry": round(stat["future_strawberry_count"] / n, 4),
            "p_future_tomato": round(stat["future_tomato_count"] / n, 4),
            "p_future_carrot": round(stat["future_carrot_count"] / n, 4),
            "p_future_wool": round(stat["future_wool_count"] / n, 4),
            "p_future_dairy": round(stat["future_dairy_count"] / n, 4),
            "mean_future_strawberry_shops": round(sum(stat["total_future_strawberry_shops"]) / n, 2),
            "mean_future_tomato_shops": round(sum(stat["total_future_tomato_shops"]) / n, 2),
            "next_shop_top3": stat["next_shop_distribution"].most_common(3)
        }
    return summary

def run_empirical_model(corpus_size: int = 500):
    print(f"Extracting shop trajectories for {corpus_size} offline seeds...")
    seeds = list(range(50000, 50000 + corpus_size))
    trajectories = extract_shop_trajectories(seeds)
    print(f"Extracted {len(trajectories)} trajectories successfully.")
    
    summary = analyze_conditional_distributions(trajectories)
    
    out_path = os.path.join(BASE_DIR, "scratch", "empirical_shop_model.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved empirical model to {out_path}")
    
    print("=" * 80)
    print("EMPIRICAL FUTURE-SHOP PROBABILITY TABLE (TOP VISIBLE PAIRS)")
    print("=" * 80)
    print(f"{'Visible Pair (Day 6)':<38} | {'N':<4} | {'P(Future Straw)':<15} | {'P(Future Tom)':<14} | {'Mean Straw'}")
    print("-" * 80)
    
    sorted_pairs = sorted(summary.items(), key=lambda x: x[1]["n_samples"], reverse=True)
    for pair_str, data in sorted_pairs[:15]:
        print(f"{pair_str:<38} | {data['n_samples']:<4} | {data['p_future_strawberry']:<15.2%} | {data['p_future_tomato']:<14.2%} | {data['mean_future_strawberry_shops']}")
    
    return summary

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    run_empirical_model(n)
