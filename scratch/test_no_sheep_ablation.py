import copy
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54

def run_no_sheep_test():
    # Load tapes
    with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
        tapes = json.load(f)
        
    tape0_clean = copy.deepcopy(tapes[0])
    
    # In tape 0, suppress SHEEP purchases and see what happens to workers
    tape0_no_sheep = copy.deepcopy(tapes[0])
    for s in range(144, 719):
        act = tape0_no_sheep[s]
        # Remove BUY_ANIMAL SHEEP
        new_market = []
        for o in act.get("market", []):
            if len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "SHEEP":
                continue
            new_market.append(o)
        act["market"] = new_market

    # But wait: if worker does PICKUP SHEEP or PLACE SHEEP, what happens if no sheep is in shed?
    # In kagsim, if no sheep in shed, PICKUP SHEEP simply fails (noop)!
    # Let's test both tapes on our 18 non-yarn dairy seeds vs V54++ residual!
    
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"]
    
    results_base = []
    results_no_sheep = []
    
    for s in dairy_seeds[:20]:
        # Run base
        p_base = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        p_base.tapes = [tape0_clean] + p_base.tapes[1:]
        
        g = kagsim.Game(s)
        while not g.done:
            g.step(p_base.act(g.observe(0)), v54.agent(g.observe(1)))
        cash_base = g.reward(0)
        results_base.append(cash_base)
        
        # Run no sheep
        p_no = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        p_no.tapes = [tape0_no_sheep] + p_no.tapes[1:]
        
        g2 = kagsim.Game(s)
        while not g2.done:
            g2.step(p_no.act(g2.observe(0)), v54.agent(g2.observe(1)))
        cash_no = g2.reward(0)
        results_no_sheep.append(cash_no)
        
    mean_base = sum(results_base) / len(results_base)
    mean_no = sum(results_no_sheep) / len(results_no_sheep)
    print("============================================================")
    print("CAUSAL TEST: SUPPRESS MIDGAME SHEEP ON NON-YARN SEEDS (N=20)")
    print("============================================================")
    print(f"Base Plan 0 Mean Cash:     ${mean_base:,.2f}")
    print(f"No-Sheep Plan 0 Mean Cash:   ${mean_no:,.2f}")
    print(f"Delta:                     ${mean_no - mean_base:+,.2f}")
    for i, s in enumerate(dairy_seeds[:20]):
        diff = results_no_sheep[i] - results_base[i]
        print(f"  Seed {s}: Base=${results_base[i]:,.2f} | NoSheep=${results_no_sheep[i]:,.2f} | Delta=${diff:+,.2f}")

if __name__ == "__main__":
    run_no_sheep_test()
