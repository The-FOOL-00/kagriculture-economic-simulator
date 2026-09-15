"""
scratch/test_geese_ablation.py
Test removing Geese from Dmitrii-LB2800 Plan 0 and Plan 2.
Evaluates on 50 fresh seeds (100 matches) vs V54++ Residual.
"""
import copy
import json
import math
import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import compiled_v54_plus_residual

DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, DMITRII_DIR)

import router_parent

with open(os.path.join(DMITRII_DIR, "actions.json"), "r", encoding="utf-8") as f:
    RAW_TAPES = json.load(f)

def make_no_geese_agent():
    tapes = copy.deepcopy(RAW_TAPES)
    for p_idx in (0, 2):
        tape = tapes[p_idx]
        for act in tape:
            # Drop BUY_ANIMAL GOOSE
            mkt = act.get("market", [])
            act["market"] = [o for o in mkt if not (o and o[0] == "BUY_ANIMAL" and len(o) > 1 and o[1] == "GOOSE")]
            # In workers: BUILD_COOP -> PASS, CARE / FEED goose -> PASS
            farmer = act.get("farmer")
            if farmer and farmer[0] == "BUILD_COOP":
                act["farmer"] = ["PASS"]
            hands = act.get("hands", [])
            for i, h in enumerate(hands):
                if h and h[0] == "BUILD_COOP":
                    hands[i] = ["PASS"]

    class NoGeesePolicy(router_parent.Policy):
        def __init__(self):
            self.tapes = tapes
            self.players = {}

    policy_inst = NoGeesePolicy()
    def agent_fn(obs, config=None):
        return policy_inst.act(obs)
        
    return agent_fn

def play_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return float(game.reward(0)), float(game.reward(1))

def run():
    seeds = list(range(20000, 20050))
    opp = compiled_v54_plus_residual.agent
    agent_nogeese = make_no_geese_agent()
    
    # Run No-Geese
    scores_d, scores_o, margins = [], [], []
    for s in seeds:
        r0, r1 = play_match(agent_nogeese, opp, s)
        scores_d.append(r0); scores_o.append(r1); margins.append(r0 - r1)
        r1, r0 = play_match(opp, agent_nogeese, s)
        scores_d.append(r0); scores_o.append(r1); margins.append(r0 - r1)
        
    n = len(margins)
    mean_d = sum(scores_d) / n
    mean_m = sum(margins) / n
    wr = sum(1 for m in margins if m > 0) / n
    print("=" * 65)
    print(f"NO-GEESE ABLATION RESULTS (100 matches vs V54++ residual)")
    print(f"Dmitrii No-Geese Mean Cash : ${mean_d:,.2f}")
    print(f"Mean Paired Margin         : {mean_m:+,.2f}")
    print(f"Win Rate                   : {wr*100:.1f}%")
    print(f"Delta from Standard Base   : {mean_m - 7674:+,.2f}")
    print("=" * 65)

if __name__ == "__main__":
    run()
