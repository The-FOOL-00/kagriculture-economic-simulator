"""
PHASE 1: CROP PORTFOLIO SWEEP (STRAWBERRY / TOMATO ALLOCATION FRONTIER)
Sweeps allocations:
[19/0, 17/2, 15/4, 13/6, 11/8, 10/9, 9/10, 8/11, 6/13, 4/15, 2/17, 0/19]
Measures:
- Mean Cash, Median, Win Rate vs Dmitrii, Worst Loss, Best Win, Paired Margin, Catastrophic Rate.
- Performance grouped by actual final town shop configuration.
- Risk-adjusted objective: ExpectedCash - lambda * DownsideRisk (for lambda in [0, 0.1, 0.25, 0.5, 1, 2]).
"""
import os, sys, json, math, copy
from collections import defaultdict
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class HybridCropPortfolioAgent(ClosedLoopAgentV2):
    def __init__(self, s_target: int, t_target: int, sale_batch: int = 6):
        super().__init__(jit_headroom_threshold=96)
        self.s_target = s_target
        self.t_target = t_target
        self.sale_batch = sale_batch
        self.tomatoes_bought = 0
        self.tomatoes_planted = 0

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs["step"])
        day = step // 24
        
        # Reset counters at start of game
        if step == 0:
            self.tomatoes_bought = 0
            self.tomatoes_planted = 0
            
        action = super().act(obs)
        
        # On Day 11 (steps 264 to 287), substitute Strawberry -> Tomato up to t_target
        if 264 <= step <= 287:
            # Modify seed buys proportionally without increasing total quantity
            new_market = []
            for order in action.get("market", []):
                if order and order[0] == "BUY_SEED" and len(order) >= 3 and order[1] == "STRAWBERRY":
                    q = int(order[2])
                    q_tom = min(q, max(0, self.t_target - self.tomatoes_bought))
                    q_straw = q - q_tom
                    self.tomatoes_bought += q_tom
                    if q_tom > 0:
                        new_market.append(["BUY_SEED", "TOMATO", q_tom])
                    if q_straw > 0:
                        new_market.append(["BUY_SEED", "STRAWBERRY", q_straw])
                else:
                    new_market.append(order)
            action["market"] = new_market[:10]
            
            # Modify plant actions
            if action.get("farmer") and action["farmer"][0] == "PLANT" and action["farmer"][1] == "STRAWBERRY":
                if self.tomatoes_planted < self.t_target:
                    action["farmer"] = ["PLANT", "TOMATO"]
                    self.tomatoes_planted += 1
            for i, h in enumerate(action.get("hands", [])):
                if h and h[0] == "PLANT" and h[1] == "STRAWBERRY":
                    if self.tomatoes_planted < self.t_target:
                        action["hands"][i] = ["PLANT", "TOMATO"]
                        self.tomatoes_planted += 1
                        
        # On Days 19 to 29: active tomato market sales on step % 4 == 1
        if day >= 19 and step % 4 == 1 and self.t_target > 0:
            shed_tom = obs["private"]["shed"].get("TOMATO", 0)
            if shed_tom > 0 and len(action.get("market", [])) < 10:
                batch = min(shed_tom, self.sale_batch)
                action["market"].append(["SELL", "TOMATO", batch])
                
        # If tomatoes in shed, substitute planned Strawberry sells with Tomato sells
        if self.t_target > 0:
            new_market = []
            for m in action.get("market", []):
                if m and m[0] == "SELL" and m[1] == "STRAWBERRY":
                    shed_tom = obs["private"]["shed"].get("TOMATO", 0)
                    if shed_tom > 0:
                        batch = min(shed_tom, m[2])
                        new_market.append(["SELL", "TOMATO", batch])
                    else:
                        new_market.append(m)
                else:
                    new_market.append(m)
            action["market"] = new_market[:10]
            
        return action

def evaluate_allocation(s_target: int, t_target: int, seeds: List[int]) -> Dict[str, Any]:
    scores_agent = []
    scores_dmitrii = []
    margins = []
    wins = 0
    catastrophes = 0
    cat_margins = defaultdict(list)
    
    for s in seeds:
        for seat in [0, 1]:
            g = kagsim.Game(s)
            p_agent = HybridCropPortfolioAgent(s_target, t_target)
            p_dmitrii = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            
            if seat == 0:
                while not g.done:
                    g.step(p_agent.act(g.observe(0)), p_dmitrii.act(g.observe(1)))
                r_agent = g.reward(0)
                r_dmi = g.reward(1)
            else:
                while not g.done:
                    g.step(p_dmitrii.act(g.observe(0)), p_agent.act(g.observe(1)))
                r_agent = g.reward(1)
                r_dmi = g.reward(0)
                
            margin = r_agent - r_dmi
            scores_agent.append(r_agent)
            scores_dmitrii.append(r_dmi)
            margins.append(margin)
            if r_agent > r_dmi: wins += 1
            if r_agent < 60000: catastrophes += 1
            
            # Final shop classification
            final_shops = g.observe(0)["town"]["unlocked_shops"]
            has_pizza = "PIZZA_SHOP" in final_shops
            has_straw = any(shop in final_shops for shop in ["SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT"])
            if has_pizza and not has_straw:
                cat_margins["pizza_pure"].append(margin)
            elif has_straw:
                cat_margins["strawberry_present"].append(margin)
            else:
                cat_margins["other"].append(margin)
                
    n = len(margins)
    mean_margin = sum(margins) / n
    mean_cash = sum(scores_agent) / n
    sorted_margins = sorted(margins)
    median_margin = sorted_margins[n // 2]
    worst_loss = min(margins)
    best_win = max(margins)
    win_rate = wins / n
    cat_rate = catastrophes / n
    
    neg_margins = [min(0, m) for m in margins]
    downside_risk = math.sqrt(sum(x ** 2 for x in neg_margins) / n)
    
    return {
        "allocation": f"{s_target}S / {t_target}T",
        "s_target": s_target,
        "t_target": t_target,
        "mean_cash": round(mean_cash, 2),
        "mean_margin": round(mean_margin, 2),
        "median_margin": round(median_margin, 2),
        "win_rate": round(win_rate, 4),
        "worst_loss": round(worst_loss, 2),
        "best_win": round(best_win, 2),
        "catastrophic_rate": round(cat_rate, 4),
        "downside_risk": round(downside_risk, 2),
        "cat_pizza_pure_margin": round(sum(cat_margins["pizza_pure"]) / len(cat_margins["pizza_pure"]), 2) if cat_margins["pizza_pure"] else 0.0,
        "cat_straw_present_margin": round(sum(cat_margins["strawberry_present"]) / len(cat_margins["strawberry_present"]), 2) if cat_margins["strawberry_present"] else 0.0,
        "cat_other_margin": round(sum(cat_margins["other"]) / len(cat_margins["other"]), 2) if cat_margins["other"] else 0.0,
        "n_pizza_pure": len(cat_margins["pizza_pure"]),
        "n_straw_present": len(cat_margins["strawberry_present"])
    }

def run_portfolio_sweep():
    allocs = [
        (19, 0),
        (17, 2),
        (15, 4),
        (13, 6),
        (11, 8),
        (10, 9),
        (9, 10),
        (8, 11),
        (6, 13),
        (4, 15),
        (2, 17),
        (0, 19)
    ]
    
    # Discovery dataset: Seeds 50000 to 50049 (50 seeds x 2 seats = 100 games)
    discovery_seeds = list(range(50000, 50050))
    print(f"Starting Crop Portfolio Sweep on Discovery Set ({len(discovery_seeds)} seeds, 100 games per allocation)...", flush=True)
    
    results = []
    for s_cnt, t_cnt in allocs:
        print(f"Evaluating allocation: {s_cnt}S / {t_cnt}T ...", flush=True)
        res = evaluate_allocation(s_cnt, t_cnt, discovery_seeds)
        results.append(res)
        print(f"  -> Mean Margin: {res['mean_margin']:+,.2f} | Win Rate: {res['win_rate']:.1%} | Worst Loss: {res['worst_loss']:,.0f} | Downside: {res['downside_risk']:,.0f} | Pizza: {res['cat_pizza_pure_margin']:+,.0f} | Straw: {res['cat_straw_present_margin']:+,.0f}", flush=True)
        
    out_path = os.path.join(BASE_DIR, "scratch", "crop_portfolio_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved complete results to {out_path}", flush=True)
    
    # Pareto frontier analysis
    print("\n" + "=" * 90, flush=True)
    print("PARETO EFFICIENT FRONTIER: OBJECTIVE = ExpectedCash - lambda * DownsideRisk", flush=True)
    print("=" * 90, flush=True)
    print(f"{'Allocation':<12} | {'Mean Cash':<11} | {'Margin':<9} | {'Win Rate':<9} | {'Worst Loss':<11} | {'Downside':<9} | {'Score(L=0.25)':<14} | {'Score(L=1.0)'}", flush=True)
    print("-" * 90, flush=True)
    for r in results:
        score_025 = r["mean_cash"] - 0.25 * r["downside_risk"]
        score_10 = r["mean_cash"] - 1.0 * r["downside_risk"]
        print(f"{r['allocation']:<12} | ${r['mean_cash']:<10,.0f} | {r['mean_margin']:+<9,.0f} | {r['win_rate']:<9.1%} | ${r['worst_loss']:<10,.0f} | ${r['downside_risk']:<8,.0f} | ${score_025:<13,.0f} | ${score_10:,.0f}", flush=True)

if __name__ == "__main__":
    run_portfolio_sweep()
