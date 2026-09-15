import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

def decompose_seed(seed):
    print(f"=== DECOMPOSING MATCH 0 ON SEED {seed} ===")
    g = kagsim.Game(seed)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    # We want to track cash changes step-by-step
    cand_cash_prev = 3000.0
    v2_cash_prev = 3000.0
    
    cand_revenue_by_crop = {}
    v2_revenue_by_crop = {}
    cand_expenses = {}
    v2_expenses = {}
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        c0_before = o0["cash"]
        c1_before = o1["cash"]
        
        a0 = cand.act(o0)
        a1 = v2.act(o1)
        
        g.step(a0, a1)
        step += 1
        
        o0_after = g.observe(0)
        o1_after = g.observe(1)
        
        c0_after = o0_after["cash"]
        c1_after = o1_after["cash"]
        
        delta0 = c0_after - c0_before
        delta1 = c1_after - c1_before
        
    print(f"Cand final cash: {g.reward(0)}")
    print(f"V2   final cash: {g.reward(1)}")
    print(f"Diff: {g.reward(0) - g.reward(1)}")

decompose_seed(50018)
