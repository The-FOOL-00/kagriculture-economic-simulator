"""
PHASE 16: MULTI-SHOP GENERALIZATION MATRIX.
Tests the Tomato Specialist Branch vs ClosedLoopV2 and Dmitrii
across all distinct Pizza shop pair worlds:
1. PIZZA + PIZZA
2. PIZZA + PET_CAFE
3. PIZZA + YARN_STORE
4. PIZZA + ICE_CREAM_SHOP
5. PIZZA + FARMERS_MARKET
6. PIZZA + BAKERY
7. PIZZA + BRUNCH_SPOT
8. PIZZA + SMOOTHIE_SHOP
"""
import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from test_tomato_with_sales import TomatoSpecialistV1

# Find 2 seeds for each shop pair in 50000..50500
def find_shop_seeds():
    pairs_needed = {
        ("PIZZA_SHOP", "PIZZA_SHOP"): [],
        ("PIZZA_SHOP", "PET_CAFE"): [],
        ("PIZZA_SHOP", "YARN_STORE"): [],
        ("PIZZA_SHOP", "ICE_CREAM_SHOP"): [],
        ("PIZZA_SHOP", "FARMERS_MARKET"): [],
        ("PIZZA_SHOP", "BAKERY"): [],
        ("PIZZA_SHOP", "BRUNCH_SPOT"): [],
        ("PIZZA_SHOP", "SMOOTHIE_SHOP"): [],
    }
    
    for s in range(50000, 50600):
        g = kagsim.Game(s)
        for _ in range(144):
            g.step({'farmer': ['PASS'], 'hands': [], 'market': []}, {'farmer': ['PASS'], 'hands': [], 'market': []})
        shops = g.observe(0)['town']['unlocked_shops']
        if len(shops) >= 2:
            pair = tuple(sorted(shops[:2]))
            for k in list(pairs_needed.keys()):
                if tuple(sorted(k)) == pair and len(pairs_needed[k]) < 3:
                    pairs_needed[k].append(s)
                    
        # Check if all pairs have at least 2 seeds
        if all(len(v) >= 2 for v in pairs_needed.values()):
            break
            
    return pairs_needed

def run_generalization_matrix():
    print("=" * 85)
    print("PHASE 16: PIZZA SPECIALIST MULTI-SHOP GENERALIZATION MATRIX")
    print("=" * 85)
    
    seeds_by_pair = find_shop_seeds()
    results = {}
    
    print(f"{'Shop Pair':<32} | {'Seeds':<14} | {'V2 Cash':<12} | {'Tom Cash':<12} | {'Delta vs V2':<15}")
    print("-" * 85)
    
    for pair, seeds in seeds_by_pair.items():
        if not seeds:
            continue
        v2_list = []
        tom_list = []
        dmi_list = []
        
        for s in seeds:
            # V2 vs Dmitrii
            g_v2 = kagsim.Game(s)
            p_v2 = ClosedLoopAgentV2()
            p_d1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            while not g_v2.done:
                g_v2.step(p_v2.act(g_v2.observe(0)), p_d1.act(g_v2.observe(1)))
            v2_list.append(g_v2.reward(0))
            dmi_list.append(g_v2.reward(1))
            
            # Tom vs Dmitrii
            g_tom = kagsim.Game(s)
            p_tom = TomatoSpecialistV1(sale_batch=6)
            p_d2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            while not g_tom.done:
                g_tom.step(p_tom.act(g_tom.observe(0)), p_d2.act(g_tom.observe(1)))
            tom_list.append(g_tom.reward(0))
            
        m_v2 = sum(v2_list) / len(v2_list)
        m_tom = sum(tom_list) / len(tom_list)
        delta = m_tom - m_v2
        pair_str = f"{pair[0]} + {pair[1]}"
        print(f"{pair_str:<32} | {str(seeds):<14} | ${m_v2:<11,.0f} | ${m_tom:<11,.0f} | ${delta:<+14,.0f}")
        results[pair_str] = {"v2": m_v2, "tom": m_tom, "delta": delta, "seeds": seeds}
        
    with open("scratch/generalization_matrix_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_generalization_matrix()
