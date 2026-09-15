import os
import sys
import json
import time
import math
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import compiled_v54_plus_residual
import main as dmitrii_main

# Load decoded tapes from yhay81_three_day_router_tapes.json
tapes_path = os.path.join(BASE_DIR, "scratch", "yhay81_three_day_router_tapes.json")
with open(tapes_path, encoding="utf-8") as f:
    yhay81_tapes = json.load(f)

def make_hayashi_agent():
    # Implement the exact policy logic from policy.cpp
    class HayashiPolicy:
        def __init__(self):
            self.route = 0
            
        def act(self, obs):
            step = int(obs.get("step", 0))
            seat = int(obs.get("player", 0))
            if step == 0:
                self.route = 0
            if step == 360:
                # select_route
                town = obs.get("town", {})
                unlocked = town.get("unlocked_shops", [])
                s0 = unlocked[0] if unlocked else "NONE"
                market = obs.get("market", {})
                inv = market.get("inventory", {})
                fert_inv = float(inv.get("FERTILIZER", 10000))
                
                # count opponent planted tiles
                opp_farm = obs.get("farms", [])[1 - seat]
                opp_tiles = opp_farm.get("tiles", [])
                opp_planted = 0
                for row in opp_tiles:
                    for tile in row:
                        if isinstance(tile, dict) and (tile.get("kind") == "PLANT" or tile.get("crop")):
                            opp_planted += 1
                            
                if s0 == "BAKERY" and fert_inv <= 10232.5:
                    self.route = 1
                elif s0 == "PET_CAFE" and opp_planted <= 64.5:
                    self.route = 1
                else:
                    self.route = 0
                    
            tape = yhay81_tapes[self.route]
            if step < len(tape):
                return tape[step]
            return {"farmer": ["PASS"], "hands": [], "market": []}
            
    policies = {}
    def agent(obs, cfg=None):
        seat = int(obs.get("player", 0))
        if seat not in policies or obs.get("step", 0) == 0:
            policies[seat] = HayashiPolicy()
        return policies[seat].act(obs)
    return agent

def run_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return float(game.reward(0)), float(game.reward(1))

def run_solo(fn, seed):
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        a0 = fn(o0)
        game.step(a0, idle)
    return float(game.reward(0))

def main():
    print("============================================================")
    print("PHASE 2: BENCHMARK YUSUKE HAYASHI THREE-DAY SHOP ROUTER")
    print("============================================================")
    
    hayashi_agent = make_hayashi_agent()
    dmitrii_agent = dmitrii_main.agent
    v54_agent = compiled_v54_plus_residual.agent
    
    seeds = list(range(40000, 40050)) # 50 seeds discovery
    
    # 1. Solo Cash comparison (50 seeds)
    print("\n1. Measuring Solo Cash (50 seeds vs IDLE)...")
    solo_hayashi = [run_solo(hayashi_agent, s) for s in seeds]
    solo_dmitrii = [run_solo(dmitrii_agent, s) for s in seeds]
    print(f"  Mean Solo Cash (Hayashi Router): ${np.mean(solo_hayashi):,.2f} (std: ${np.std(solo_hayashi):,.2f})")
    print(f"  Mean Solo Cash (Dmitrii-LB2800):  ${np.mean(solo_dmitrii):,.2f} (std: ${np.std(solo_dmitrii):,.2f})")
    print(f"  Solo Delta (Hayashi - Dmitrii):   ${np.mean(solo_hayashi) - np.mean(solo_dmitrii):,.2f}")
    
    # 2. Competitive vs V54++ residual (50 seeds, both seats = 100 matches)
    print("\n2. Measuring Competitive Matches vs V54++ Residual (100 matches)...")
    h_v54_results = []
    for s in seeds:
        # Hayashi P0
        r0, r1 = run_match(hayashi_agent, v54_agent, s)
        h_v54_results.append({"us": r0, "opp": r1, "win": r0 > r1, "margin": r0 - r1, "seat": 0})
        # Hayashi P1
        r0, r1 = run_match(v54_agent, hayashi_agent, s)
        h_v54_results.append({"us": r1, "opp": r0, "win": r1 > r0, "margin": r1 - r0, "seat": 1})
        
    mean_us = np.mean([r["us"] for r in h_v54_results])
    mean_opp = np.mean([r["opp"] for r in h_v54_results])
    mean_margin = np.mean([r["margin"] for r in h_v54_results])
    wr = np.mean([r["win"] for r in h_v54_results]) * 100
    print(f"  Hayashi vs V54++: Mean Us = ${mean_us:,.2f} | Opp = ${mean_opp:,.2f} | Margin = +${mean_margin:,.2f} | Win Rate = {wr:.1f}%")
    
    # 3. Head-to-Head: Hayashi vs Dmitrii (50 seeds, both seats = 100 matches)
    print("\n3. Measuring Head-to-Head: Hayashi Router vs Dmitrii-LB2800 (100 matches)...")
    h_d_results = []
    for s in seeds:
        # Hayashi P0, Dmitrii P1
        r0, r1 = run_match(hayashi_agent, dmitrii_agent, s)
        h_d_results.append({"hayashi": r0, "dmitrii": r1, "win": r0 > r1, "margin": r0 - r1, "seat": 0})
        # Dmitrii P0, Hayashi P1
        r0, r1 = run_match(dmitrii_agent, hayashi_agent, s)
        h_d_results.append({"hayashi": r1, "dmitrii": r0, "win": r1 > r0, "margin": r1 - r0, "seat": 1})
        
    mean_h = np.mean([r["hayashi"] for r in h_d_results])
    mean_d = np.mean([r["dmitrii"] for r in h_d_results])
    mean_diff = np.mean([r["margin"] for r in h_d_results])
    wr_h = np.mean([r["win"] for r in h_d_results]) * 100
    print(f"  Head-to-Head: Hayashi Mean = ${mean_h:,.2f} | Dmitrii Mean = ${mean_d:,.2f}")
    print(f"  Net Margin (Hayashi - Dmitrii): ${mean_diff:,.2f}")
    print(f"  Hayashi Win Rate vs Dmitrii: {wr_h:.1f}%")
    print("============================================================\n")

if __name__ == "__main__":
    main()
