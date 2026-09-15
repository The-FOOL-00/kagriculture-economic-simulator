import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_residual

OKAMI_PATH = os.path.join(BASE_DIR, "external_repos", "okami001-Kaggriculture", "main.py")
spec_okami = importlib.util.spec_from_file_location("okami", OKAMI_PATH)
mod_okami = importlib.util.module_from_spec(spec_okami)
spec_okami.loader.exec_module(mod_okami)

def play_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return game.reward(0), game.reward(1)

def run():
    seeds = [11, 23, 47, 100, 200, 300, 400, 500, 600, 700]
    idle = lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}
    
    print("=" * 65)
    print("OKAMI001 EVALUATION")
    print("=" * 65)
    
    # Solo vs IDLE
    idle_scores = []
    for s in seeds:
        r, _ = play_match(mod_okami.agent, idle, s)
        idle_scores.append(r)
    print(f"Okami vs IDLE (10 seeds): Mean Cash = ${sum(idle_scores)/len(idle_scores):,.2f}")
    
    # Head to head vs V54++ Residual
    okami_scores, v54_scores, margins = [], [], []
    wins, losses, ties = 0, 0, 0
    for s in seeds:
        # Seat 0
        r0, r1 = play_match(mod_okami.agent, v54_plus_residual.agent, s)
        margins.append(r0 - r1)
        okami_scores.append(r0)
        v54_scores.append(r1)
        if r0 > r1: wins += 1
        elif r0 < r1: losses += 1
        else: ties += 1
        
        # Seat 1
        r1, r0 = play_match(v54_plus_residual.agent, mod_okami.agent, s)
        margins.append(r0 - r1)
        okami_scores.append(r0)
        v54_scores.append(r1)
        if r0 > r1: wins += 1
        elif r0 < r1: losses += 1
        else: ties += 1
        
    print(f"Okami Head-to-Head Mean : ${sum(okami_scores)/len(okami_scores):,.2f}")
    print(f"V54++ Residual Control  : ${sum(v54_scores)/len(v54_scores):,.2f}")
    print(f"Net Margin              : {sum(margins)/len(margins):+,.2f}")
    print(f"Win / Loss / Tie        : {wins} / {losses} / {ties} ({wins/len(margins)*100:.1f}%)")
    print("=" * 65)

if __name__ == "__main__":
    run()
