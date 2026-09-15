"""
SWEEP PIZZA-DEMAND SPECIALIST (BRANCH A)
Tests dedicated tomato production and harvest scheduling against Dmitrii Base.
Parametric sweeps:
- Tomato plant counts: [10, 15, 19, 25, 30]
- Worker counts: [10, 11, 12, 13]
- Sale batching: micro-batch (step % 4 == 1) vs standard
"""
import os
import sys
import copy
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class PizzaSpecialistAgent(ClosedLoopAgentV2):
    def __init__(
        self,
        tomato_target: int = 19,
        extra_workers: int = 0,
        start_day: int = 12,
        enable_daily_harvest: bool = True
    ):
        super().__init__(jit_headroom_threshold=96)
        self.tomato_target = tomato_target
        self.extra_workers = extra_workers
        self.start_day = start_day
        self.enable_daily_harvest = enable_daily_harvest
        self.tomatoes_planted = 0
        self.tomatoes_sold = 0

    def act(self, obs):
        step = int(obs["step"])
        player = int(obs["player"])
        day = step // 24
        hour = step % 24
        
        # In steps 0..143, execute base V2 logic strictly untouched
        if step < 144:
            return super().act(obs)
            
        action = super().act(obs)
        if step >= mod_r.LAST_STEP:
            return action

        shops = obs.get("town", {}).get("unlocked_shops", [])
        has_pizza = ("PIZZA_SHOP" in shops)
        if not has_pizza:
            return action

        # 1. Tomato Seed Substitution on Days start_day..start_day+3
        if self.start_day <= day <= self.start_day + 3 and self.tomatoes_planted < self.tomato_target:
            # Substitute BUY_SEED STRAWBERRY -> BUY_SEED TOMATO
            new_market = []
            for m in action.get("market", []):
                if m and m[0] == "BUY_SEED" and len(m) > 1 and m[1] == "STRAWBERRY":
                    qty = min(m[2], self.tomato_target - self.tomatoes_planted)
                    if qty > 0:
                        new_market.append(["BUY_SEED", "TOMATO", qty])
                        rem = m[2] - qty
                        if rem > 0:
                            new_market.append(["BUY_SEED", "STRAWBERRY", rem])
                    else:
                        new_market.append(m)
                else:
                    new_market.append(m)
            action["market"] = new_market
            
            # Substitute PLANT STRAWBERRY -> PLANT TOMATO
            if action.get("farmer") and action["farmer"][0] == "PLANT" and len(action["farmer"]) > 1 and action["farmer"][1] == "STRAWBERRY":
                if self.tomatoes_planted < self.tomato_target:
                    action["farmer"] = ["PLANT", "TOMATO"]
                    self.tomatoes_planted += 1
            for i, h in enumerate(action.get("hands", [])):
                if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY":
                    if self.tomatoes_planted < self.tomato_target:
                        action["hands"][i] = ["PLANT", "TOMATO"]
                        self.tomatoes_planted += 1

        # 2. Daily Tomato Harvesting on Days 20..28
        # If worker is standing on a ripe Tomato tile with yield > 0, override PASS or unneeded movement with HARVEST
        if self.enable_daily_harvest and 20 <= day <= 28:
            farm = obs["farms"][player]
            all_pos = [farm["farmer"]] + farm["hands"]
            tiles = farm["tiles"]
            
            workers = [action.get("farmer")] + action.get("hands", [])
            for u_idx, pos in enumerate(all_pos):
                if u_idx < len(workers) and workers[u_idx]:
                    x, y = pos[0], pos[1]
                    tile = tiles[y][x]
                    if isinstance(tile, dict) and tile.get("crop") == "TOMATO" and tile.get("yield_units", 0) > 0:
                        cur_op = workers[u_idx][0]
                        # If current action is not essential (PASS or move that can be deferred)
                        if cur_op in ["PASS", "NORTH", "SOUTH", "EAST", "WEST"]:
                            workers[u_idx] = ["HARVEST"]
                            
            action["farmer"] = workers[0]
            action["hands"] = workers[1:]

        # 3. Market Sales Optimization: Sell Tomatoes at step % 4 == 1
        view = mod_r.FarmView(obs)
        tomato_in_shed = view.shed.get("TOMATO", 0)
        if step % 4 == 1 and tomato_in_shed > 0:
            sell_qty = min(tomato_in_shed, 10)
            if len(action["market"]) < mod_r.MAX_ORDERS:
                action["market"].append(["SELL", "TOMATO", sell_qty])
                self.tomatoes_sold += sell_qty

        action["market"] = action["market"][:mod_r.MAX_ORDERS]
        return action

def run_sweeps():
    pizza_seeds = [50007, 50010, 50012, 50018, 50030]
    print("="*85)
    print("SWEEPING TOMATO TARGETS FOR PIZZA SPECIALIST (BRANCH A)")
    print("="*85)
    
    targets = [0, 10, 15, 19, 25]
    
    for t_tgt in targets:
        wins = 0
        losses = 0
        margins = []
        
        for s in pizza_seeds:
            # Seat 0
            p_spec = PizzaSpecialistAgent(tomato_target=t_tgt) if t_tgt > 0 else ClosedLoopAgentV2()
            p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            g0 = kagsim.Game(s)
            while not g0.done:
                g0.step(p_spec.act(g0.observe(0)), p_dmi.act(g0.observe(1)))
            c0 = g0.reward(0)
            d1 = g0.reward(1)
            m0 = c0 - d1
            margins.append(m0)
            if m0 > 0: wins += 1
            elif m0 < 0: losses += 1

            # Seat 1
            p_dmi0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            p_spec1 = PizzaSpecialistAgent(tomato_target=t_tgt) if t_tgt > 0 else ClosedLoopAgentV2()
            g1 = kagsim.Game(s)
            while not g1.done:
                g1.step(p_dmi0.act(g1.observe(0)), p_spec1.act(g1.observe(1)))
            d0 = g1.reward(0)
            c1 = g1.reward(1)
            m1 = c1 - d0
            margins.append(m1)
            if m1 > 0: wins += 1
            elif m1 < 0: losses += 1

        mean_m = sum(margins) / len(margins)
        print(f"Tomato Target {t_tgt:2d}: Wins {wins:2d}/{len(margins)} ({wins/len(margins)*100:5.1f}%) | Mean Margin vs Dmitrii: ${mean_m:+8.2f}")

if __name__ == "__main__":
    run_sweeps()
