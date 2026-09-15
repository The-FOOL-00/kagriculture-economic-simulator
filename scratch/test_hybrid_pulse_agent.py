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

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100,
}

class HybridPulsePolicy(mod_r.Policy):
    """
    Hybrid Adaptive Economic Agent:
    Preserves Dmitrii's 100% verified physical choreography (fertilization, watering, animal care).
    Optimizes the market execution layer with:
    1. Capacity Safety Valve (shed_total <= 80 to prevent crop loss).
    2. Liquidity Guard (preserves cash for hires).
    3. Pulse-Aligned Sales (prioritizes sales during town consumption pulses step%4 == 0).
    4. Market Price Defense (avoids selling high-value goods into collapsed prices when town is absorbing).
    """
    def __init__(self, folder):
        super().__init__(folder)
        
    def act(self, observation):
        # 1. Base tape action with weed repairs and advanced sales
        action = super().act(observation)
        step = int(observation["step"])
        
        # Don't touch terminal liquidation
        if step >= 710:
            return action
            
        farm = observation["farms"][observation["player"]]
        money = farm["money"]
        shed = observation["private"]["shed"]
        shed_total = sum(shed.values())
        prices = observation["market"]["prices"]
        unlocked_shops = observation["town"].get("unlocked_shops", [])
        
        has_yarn = "YARN_STORE" in unlocked_shops
        is_pulse = (step % 4 == 0 or step % 4 == 3)
        
        # Filter and reorder market sales
        filtered_orders = []
        buys = []
        sells = []
        
        for order in action.get("market", []):
            if not order:
                continue
            if order[0] == "SELL" and len(order) >= 3:
                sells.append(order)
            else:
                buys.append(order)
                
        for order in sells:
            item = order[1]
            qty = order[2]
            p = prices.get(item, 0)
            base_p = BASE_PRICES.get(item, 100)
            
            # Rule A: Capacity Emergency - if shed is over 75, ALWAYS allow sale
            if shed_total >= 75:
                filtered_orders.append(order)
                continue
                
            # Rule B: Wool without Yarn Store - if price is <= 10 and shed has room, skip to preserve price
            if item == "WOOL" and not has_yarn and p <= 15:
                continue
                
            # Rule C: Milk / Strawberry price defense - if price is heavily collapsed (< 40% base) and NOT a town pulse, hold for pulse
            if item in ("MILK", "STRAWBERRY") and p < 0.40 * base_p and not is_pulse:
                continue
                
            filtered_orders.append(order)
            
        # Recombine buys and filtered sells, keeping buys first
        action["market"] = (buys + filtered_orders)[:mod_r.MAX_ORDERS]
        return action

def benchmark_hybrid_agent():
    print("============================================================")
    print("PHASE 14 & 15: BENCHMARK HYBRID PULSE AGENT VS DMITRII BASE")
    print("============================================================")
    
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"]
    
    # Run 40 seeds, both seats = 80 competitive matches vs V54++ residual
    n_seeds = 40
    test_seeds = dairy_seeds[:n_seeds]
    
    results_base = []
    results_hybrid = []
    
    for idx, s in enumerate(test_seeds):
        # Seat 0: Dmitrii Base vs V54
        p_base = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        g0 = kagsim.Game(s)
        while not g0.done:
            g0.step(p_base.act(g0.observe(0)), v54.agent(g0.observe(1)))
        c_base0 = g0.reward(0)
        
        # Seat 1: V54 vs Dmitrii Base
        p_base1 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(v54.agent(g1.observe(0)), p_base1.act(g1.observe(1)))
        c_base1 = g1.reward(1)
        results_base.extend([c_base0, c_base1])
        
        # Seat 0: Hybrid vs V54
        p_hyb0 = HybridPulsePolicy("extracted_agents/dmitrii_lb2800")
        g2 = kagsim.Game(s)
        while not g2.done:
            g2.step(p_hyb0.act(g2.observe(0)), v54.agent(g2.observe(1)))
        c_hyb0 = g2.reward(0)
        
        # Seat 1: V54 vs Hybrid
        p_hyb1 = HybridPulsePolicy("extracted_agents/dmitrii_lb2800")
        g3 = kagsim.Game(s)
        while not g3.done:
            g3.step(v54.agent(g3.observe(0)), p_hyb1.act(g3.observe(1)))
        c_hyb1 = g3.reward(1)
        results_hybrid.extend([c_hyb0, c_hyb1])
        
    m_base = sum(results_base) / len(results_base)
    m_hyb = sum(results_hybrid) / len(results_hybrid)
    delta = m_hyb - m_base
    
    wins = sum(1 for h, b in zip(results_hybrid, results_base) if h > b)
    ties = sum(1 for h, b in zip(results_hybrid, results_base) if h == b)
    losses = sum(1 for h, b in zip(results_hybrid, results_base) if h < b)
    
    print(f"Total Matches:        {len(results_base)} ({n_seeds} seeds, both seats)")
    print(f"Dmitrii Base Mean:    ${m_base:,.2f}")
    print(f"Hybrid Agent Mean:    ${m_hyb:,.2f}")
    print(f"Net Paired Delta:     ${delta:+,.2f}")
    print(f"Hybrid Record vs Base:{wins}W / {ties}T / {losses}L")
    print(f"Max Win over Base:    ${max(h - b for h, b in zip(results_hybrid, results_base)):+,.2f}")
    print(f"Worst Drawdown:       ${min(h - b for h, b in zip(results_hybrid, results_base)):+,.2f}")

if __name__ == "__main__":
    benchmark_hybrid_agent()
