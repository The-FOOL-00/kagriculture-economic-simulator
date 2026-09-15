"""
scratch/test_fertilize_intervention.py
======================================
Controlled counterfactual experiment:
Does opportunistic fertilization of Strawberry tiles by workers carrying fertilizer
increase final cash over the frozen V54++ baseline?
"""

import copy
import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_shop
import v54_plus_residual


def make_fertilizing_agent(base_agent_fn):
    def agent(obs, configuration=None):
        act = base_agent_fn(obs)
        day = obs.get("day", 0)
        p = obs.get("player", 0)
        farm = obs["farms"][p]
        tiles = farm["tiles"]
        hands = farm.get("hands", [])
        
        priv = obs.get("private", {})
        inventories = priv.get("inventories", [{}])
        
        # Check farmer (index 0 in inventories)
        farmer_pos = farm.get("farmer", [-1, -1])
        fx, fy = farmer_pos[0], farmer_pos[1]
        f_inv = inventories[0] if len(inventories) > 0 else {}
        if f_inv.get("FERTILIZER", 0) > 0:
            if 0 <= fx < len(tiles) and 0 <= fy < len(tiles):
                tile = tiles[fy][fx]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "STRAWBERRY":
                    if tile.get("fertilized_until_day", -1) < day:
                        act["farmer"] = ["FERTILIZE"]
                        
        # Check hands (index 1..N in inventories)
        hand_acts = act.get("hands", [])
        for i, h_pos in enumerate(hands):
            if i >= len(hand_acts):
                continue
            hx, hy = h_pos[0], h_pos[1]
            h_inv = inventories[i + 1] if (i + 1) < len(inventories) else {}
            if h_inv.get("FERTILIZER", 0) > 0:
                if 0 <= hx < len(tiles) and 0 <= hy < len(tiles):
                    tile = tiles[hy][hx]
                    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "STRAWBERRY":
                        if tile.get("fertilized_until_day", -1) < day:
                            hand_acts[i] = ["FERTILIZE"]
                            
        act["hands"] = hand_acts
        return act
    return agent


def play_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return game.reward(0), game.reward(1)


def run_experiment():
    seeds = [11, 23, 47, 100, 200, 300, 400, 500, 600, 700,
             1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
    
    print("=" * 70)
    print(f"COUNTERFACTUAL EXPERIMENT: Opportunistic Strawberry Fertilization")
    print(f"Evaluation over {len(seeds)} paired seeds (2 seats each = {len(seeds)*2} matches)")
    print("=" * 70)
    
    fert_agent = make_fertilizing_agent(v54_plus_residual.agent)
    control_agent = v54_plus_residual.agent
    
    # 1. Solo vs IDLE
    idle_agent = lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}
    deltas_idle = []
    for s in seeds:
        r_ctrl, _ = play_match(control_agent, idle_agent, s)
        r_fert, _ = play_match(fert_agent, idle_agent, s)
        deltas_idle.append(r_fert - r_ctrl)
    mean_idle_delta = sum(deltas_idle) / len(deltas_idle)
    print(f"\n1. VS IDLE: Mean Delta = {mean_idle_delta:+,.2f}")
    
    # 2. Head-to-Head: Fertilized Agent vs Control Baseline
    h2h_deltas = []
    wins = 0
    losses = 0
    ties = 0
    for s in seeds:
        # Seat 0
        r0, r1 = play_match(fert_agent, control_agent, s)
        d0 = r0 - r1
        h2h_deltas.append(d0)
        if d0 > 0: wins += 1
        elif d0 < 0: losses += 1
        else: ties += 1
        
        # Seat 1
        r1, r0 = play_match(control_agent, fert_agent, s)
        d1 = r0 - r1
        h2h_deltas.append(d1)
        if d1 > 0: wins += 1
        elif d1 < 0: losses += 1
        else: ties += 1
        
    mean_h2h = sum(h2h_deltas) / len(h2h_deltas)
    winrate = wins / len(h2h_deltas) * 100
    print(f"2. HEAD-TO-HEAD VS V54++ RESIDUAL:")
    print(f"   Matches: {len(h2h_deltas)}")
    print(f"   Mean Net Margin: {mean_h2h:+,.2f}")
    print(f"   Wins / Losses / Ties: {wins} / {losses} / {ties} ({winrate:.1f}% Win Rate)")
    print("=" * 70)


if __name__ == "__main__":
    run_experiment()
