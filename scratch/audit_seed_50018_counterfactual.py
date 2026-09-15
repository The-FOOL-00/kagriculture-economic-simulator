import os
import sys
import json
import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

# Let's inspect sim.hpp constants or kaggriculture constants
print("Checking Crop parameters in kaggriculture...")

# Counterfactual Agent:
class Dev001CounterfactualNoTomatoSub(Dev001DynamicPortfolioAgent):
    """
    Identical to Dev001DynamicPortfolioAgent in every way,
    EXCEPT it does not perform the Day 11 Tomato substitution!
    """
    def act(self, obs):
        step = int(obs.get("step", 0))
        player = int(obs.get("player", 0))
        
        # Keep track of mode exactly as candidate does
        if step == 72:
            self.mode_selected[player] = self._determine_crop_mode(obs.get("town", {}).get("unlocked_shops", [])[:1])
        elif step == 144:
            self.mode_selected[player] = self._determine_crop_mode(obs.get("town", {}).get("unlocked_shops", [])[:2])
            
        mode = self.mode_selected.get(player, "STRAWBERRY")
        
        # Base V2 action
        action = super(Dev001DynamicPortfolioAgent, self).act(obs)
        
        # If in TOMATO mode, do NOT substitute on Day 11, but DO keep the active tomato sales logic on day >= 19!
        if mode == "TOMATO":
            # Active tomato market sales on step % 4 == 1 if any tomatoes exist
            day = step // 24
            if day >= 19 and step % 4 == 1 and len(action.get("market", [])) < 10:
                from router_parent import FarmView
                view = FarmView(obs)
                shed_tom = view.shed.get("TOMATO", 0)
                if shed_tom > 0:
                    has_tom_sell = any(m and m[0] == "SELL" and m[1] == "TOMATO" for m in action.get("market", []))
                    if not has_tom_sell:
                        batch = min(shed_tom, self.tomato_sale_batch)
                        action["market"].append(["SELL", "TOMATO", batch])
        return action

# Let's run paired match on Seed 50018 with this Counterfactual agent vs ClosedLoopAgentV2
def run_cf(seed):
    print(f"=== RUNNING CONTROLLED COUNTERFACTUAL ON SEED {seed} ===")
    # Match 0: CF Seat 0 vs V2 Seat 1
    g0 = kagsim.Game(seed)
    cf0 = Dev001CounterfactualNoTomatoSub()
    v2_1 = ClosedLoopAgentV2()
    
    s = 0
    diff_actions_0 = 0
    while not g0.done:
        o0 = g0.observe(0)
        o1 = g0.observe(1)
        a0 = cf0.act(o0)
        a1 = v2_1.act(o1)
        if a0 != a1:
            diff_actions_0 += 1
        g0.step(a0, a1)
        s += 1
        
    rew_cf0 = g0.reward(0)
    rew_v2_1 = g0.reward(1)
    
    # Match 1: V2 Seat 0 vs CF Seat 1
    g1 = kagsim.Game(seed)
    v2_0 = ClosedLoopAgentV2()
    cf1 = Dev001CounterfactualNoTomatoSub()
    
    diff_actions_1 = 0
    while not g1.done:
        o0 = g1.observe(0)
        o1 = g1.observe(1)
        a0 = v2_0.act(o0)
        a1 = cf1.act(o1)
        if a0 != a1:
            diff_actions_1 += 1
        g1.step(a0, a1)
        
    rew_v2_0 = g1.reward(0)
    rew_cf1 = g1.reward(1)
    
    m0 = rew_cf0 - rew_v2_1
    m1 = rew_cf1 - rew_v2_0
    paired_margin = m0 + m1
    
    print(f"CF Mode selected: {cf0.mode_selected}")
    print(f"Match 0: CF = {rew_cf0}, V2 = {rew_v2_1}, Margin = {m0}, Diff Actions = {diff_actions_0}")
    print(f"Match 1: V2 = {rew_v2_0}, CF = {rew_cf1}, Margin = {m1}, Diff Actions = {diff_actions_1}")
    print(f"Paired Margin: {paired_margin}")
    print(f"Did -$2,388 loss disappear completely? {paired_margin == 0.0}")

run_cf(50018)
print()
run_cf(50004)
