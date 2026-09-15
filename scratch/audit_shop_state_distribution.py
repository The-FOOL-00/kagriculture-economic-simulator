"""
scratch/audit_shop_state_distribution.py
Measures the empirical distribution of shop pairs and Dmitrii route selections across 200 seeds (20000-20199).
"""
import os
import sys
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent

def analyze_shop_states():
    seeds = list(range(20000, 20200))
    shop_pairs = Counter()
    plan_selections = Counter()
    has_yarn = 0
    
    for s in seeds:
        g = kagsim.Game(s)
        # Advance to step 144
        while not g.done and g.step_count < 144:
            g.step({"farmer": ["PASS"], "hands": [], "market": []}, {"farmer": ["PASS"], "hands": [], "market": []})
        obs = g.observe(0)
        shops = obs["town"]["unlocked_shops"]
        pair = tuple(shops[:2])
        shop_pairs[pair] += 1
        
        plan = router_parent.SHOP_PLANS.get(pair, 0)
        plan_selections[plan] += 1
        if "YARN_STORE" in pair:
            has_yarn += 1
            
    print("=" * 70)
    print(f"SHOP PAIR & ROUTE SELECTION DISTRIBUTION ACROSS {len(seeds)} SEEDS")
    print("=" * 70)
    print(f"Seeds with YARN_STORE in first 2 shops: {has_yarn}/{len(seeds)} ({has_yarn/len(seeds)*100:.1f}%)")
    print(f"Seeds falling back to Plan 0          : {plan_selections[0]}/{len(seeds)} ({plan_selections[0]/len(seeds)*100:.1f}%)")
    print("\nPlan Selections Breakdown:")
    for plan, count in sorted(plan_selections.items()):
        print(f"  Plan {plan:2d} : {count:3d} seeds ({count/len(seeds)*100:4.1f}%)")
        
    print("\nTop 10 Most Common Shop Pairs:")
    for pair, count in shop_pairs.most_common(10):
        mapped = router_parent.SHOP_PLANS.get(pair, "0 (Fallback)")
        print(f"  {pair[0]:<16} + {pair[1]:<16} : {count:2d} seeds -> Plan {mapped}")
    print("=" * 70)

if __name__ == "__main__":
    analyze_shop_states()
