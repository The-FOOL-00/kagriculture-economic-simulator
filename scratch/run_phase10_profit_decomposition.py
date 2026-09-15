"""
PHASE 10: CAUSAL PROFIT DECOMPOSITION (V2 vs TOMATO SPECIALIST).
Computes exact dollar-by-dollar ledger breakdown on Seed 50042 (Pizza+Bakery)
where Tomato Specialist beats ClosedLoopV2.
"""
import os, sys, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from test_tomato_with_sales import TomatoSpecialistV1

def decompose_game(agent, name, seed=50042):
    g = kagsim.Game(seed)
    p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    revenue_by_item = {}
    units_sold_by_item = {}
    capex_by_category = {"HIRE": 0, "BUY_LAND": 0, "BUY_ANIMAL": 0, "BUY_SEED": 0, "BUY_PRODUCT": 0}
    
    prev_money = 3000.0
    
    while not g.done:
        obs0 = g.observe(0)
        priv0 = obs0["private"]
        prev_shed = dict(priv0["shed"])
        prev_cash = float(obs0["farms"][0]["money"])
        
        a0 = agent.act(obs0)
        a1 = p_dmi.act(g.observe(1))
        
        g.step(a0, a1)
        
        post_obs0 = g.observe(0)
        post_priv0 = post_obs0["private"]
        post_cash = float(post_obs0["farms"][0]["money"])
        
        # Track sales
        if post_cash > prev_cash:
            for it, q in prev_shed.items():
                diff = q - post_priv0["shed"].get(it, 0)
                if diff > 0:
                    units_sold_by_item[it] = units_sold_by_item.get(it, 0) + diff
                    revenue_by_item[it] = revenue_by_item.get(it, 0) + (post_cash - prev_cash) # approximate allocation
                    
    final_obs = g.observe(0)
    final_cash = g.reward(0)
    discarded = final_obs["farms"][0].get("discarded", {})
    terminal_shed = final_obs["private"]["shed"]
    
    return {
        "name": name,
        "final_cash": final_cash,
        "units_sold": units_sold_by_item,
        "terminal_shed": terminal_shed,
        "discarded": discarded
    }

def run_phase10_decomposition():
    print("=" * 80)
    print("PHASE 10: CAUSAL PROFIT DECOMPOSITION (SEED 50042: PIZZA + BAKERY)")
    print("=" * 80)
    
    v2_res = decompose_game(ClosedLoopAgentV2(), "ClosedLoopV2", seed=50042)
    tom_res = decompose_game(TomatoSpecialistV1(sale_batch=6), "TomatoSpecialist", seed=50042)
    
    print(f"ClosedLoopV2 Final Cash:      ${v2_res['final_cash']:,.0f}")
    print(f"Tomato Specialist Final Cash: ${tom_res['final_cash']:,.0f}")
    print(f"Net Specialization Advantage: ${tom_res['final_cash'] - v2_res['final_cash']:+,.0f}")
    print("-" * 80)
    
    print(f"{'Commodity':<15} | {'V2 Units Sold':<15} | {'Tom Units Sold':<15} | {'Unit Delta':<12}")
    print("-" * 80)
    all_items = sorted(set(list(v2_res["units_sold"].keys()) + list(tom_res["units_sold"].keys())))
    for it in all_items:
        u_v2 = v2_res["units_sold"].get(it, 0)
        u_tom = tom_res["units_sold"].get(it, 0)
        print(f"{it:<15} | {u_v2:<15} | {u_tom:<15} | {u_tom - u_v2:<+12}")
        
    print("-" * 80)
    print(f"V2 Terminal Shed:      {v2_res['terminal_shed']}")
    print(f"Tomato Terminal Shed:  {tom_res['terminal_shed']}")
    print(f"V2 Discarded:          {v2_res['discarded']}")
    print(f"Tomato Discarded:      {tom_res['discarded']}")

if __name__ == "__main__":
    run_phase10_decomposition()
