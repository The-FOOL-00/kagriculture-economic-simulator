"""
scratch/run_dmitrii_causal_ablations.py
=======================================
Controlled Causal Decomposition of Dmitrii-LB2800 across 50 paired seeds (100 matches per ablation)
against V54++ Residual Baseline.

Ablations:
0. Baseline: Full Dmitrii-LB2800
1. Ablation A: No Terminal Search (settings['enabled'] = False)
2. Ablation B: No Shop Routing (force plan = 0 at Step 144)
3. Ablation C: No Weed Repair (skip repair_weeds)
4. Ablation D: No Advance Sales (skip advance_sales and subtract_advanced_sales)
5. Ablation E: No Fertilizer (replace FERTILIZE worker actions with PASS)
6. Ablation F: No Fertilizer + Water Instead (replace FERTILIZE with WATER)
7. Ablation G: Inject V54++ Residual Preemption Overlay into Dmitrii-LB2800
"""

import copy
import importlib.util
import json
import math
import os
import sys
import time
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import compiled_v54_plus_residual

DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, DMITRII_DIR)

import router_parent
import policy

# Build base tapes
with open(os.path.join(DMITRII_DIR, "actions.json"), "r", encoding="utf-8") as f:
    RAW_TAPES = json.load(f)

def make_dmitrii_variant(
    terminal_search=True,
    shop_routing=True,
    weed_repair=True,
    advance_sales=True,
    fertilizer_mode="keep", # "keep", "pass", "water"
    preemption_overlay=False
):
    """Factory that returns an agent function with specific ablations."""
    tapes = copy.deepcopy(RAW_TAPES)
    
    if fertilizer_mode in ("pass", "water"):
        replacement = ["WATER"] if fertilizer_mode == "water" else ["PASS"]
        for tape in tapes:
            for step, act in enumerate(tape):
                # Worker
                farmer = act.get("farmer")
                if farmer and farmer[0] == "FERTILIZE":
                    act["farmer"] = list(replacement)
                hands = act.get("hands", [])
                for i, h in enumerate(hands):
                    if h and h[0] == "FERTILIZE":
                        hands[i] = list(replacement)
                # Drop BUY_PRODUCT FERTILIZER from market orders
                mkt = act.get("market", [])
                act["market"] = [o for o in mkt if not (o and o[0] == "BUY_PRODUCT" and len(o) > 1 and o[1] == "FERTILIZER")]

    class CustomRouterPolicy(router_parent.Policy):
        def __init__(self):
            self.tapes = tapes
            self.players = {}

        def act(self, observation):
            step, player = int(observation["step"]), int(observation["player"])
            state = self.players.get(player)
            if state is None or step <= state.last_step:
                state = self.players[player] = router_parent.DayState()
            state.last_step = step

            if step == router_parent.ROUTE_STEP:
                if shop_routing:
                    shops = observation["town"]["unlocked_shops"]
                    state.plan = router_parent.SHOP_PLANS.get(tuple(shops[:2]), 0)
                else:
                    state.plan = 0
            if step == router_parent.FINAL_PLAN_STEP:
                state.plan = 2

            view = router_parent.FarmView(observation)
            tape = self.tapes[state.plan]
            action = copy.deepcopy(tape[step])
            
            if weed_repair:
                router_parent.repair_weeds(action, view, state, step)
                
            if advance_sales:
                router_parent.subtract_advanced_sales(action, state, step)
                router_parent.advance_sales(action, view, state, tape, step)
                
            action["market"] = action["market"][:router_parent.MAX_ORDERS]
            
            if preemption_overlay:
                # Apply V54++ residual preemption logic
                # Check shed commodities and current market prices
                shed = view.shed
                prices = view.prices
                money = observation["farms"][player]["money"]
                if money < 2000.0: # preempt_money_deficit
                    for item in ("MILK", "WOOL", "STRAWBERRY", "MELON"):
                        qty = shed.get(item, 0)
                        if qty >= 3: # front_supply_threshold
                            batch = min(qty, 12) # preempt_maximum_batch
                            if prices.get(item, 0) >= 4:
                                action["market"] = [["SELL", item, batch]] + [o for o in action["market"] if not (o and o[0] == "SELL" and o[1] == item)]
                                action["market"] = action["market"][:router_parent.MAX_ORDERS]
                                break

            return router_parent.liquidate(view) if step == router_parent.LAST_STEP else action

    if terminal_search:
        # Wrap in ShopClosure
        closure = policy.ShopClosure({"enabled": True, "max_simulations": 128, "passes": 1, "proposals_per_actor": 8})
        closure.parent = CustomRouterPolicy()
        def agent_fn(obs, config=None):
            return closure.act(obs, config)
    else:
        router = CustomRouterPolicy()
        def agent_fn(obs, config=None):
            return router.act(obs)
            
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

def evaluate_ablation(name, agent_fn, seeds, opp_fn):
    dmitrii_scores = []
    opp_scores = []
    margins = []
    p0_margins = []
    p1_margins = []
    
    for s in seeds:
        # Seat 0
        r0, r1 = play_match(agent_fn, opp_fn, s)
        m0 = r0 - r1
        dmitrii_scores.append(r0)
        opp_scores.append(r1)
        margins.append(m0)
        p0_margins.append(m0)
        
        # Seat 1
        r1, r0 = play_match(opp_fn, agent_fn, s)
        m1 = r0 - r1
        dmitrii_scores.append(r0)
        opp_scores.append(r1)
        margins.append(m1)
        p1_margins.append(m1)
        
    n = len(margins)
    mean_d = sum(dmitrii_scores) / n
    mean_o = sum(opp_scores) / n
    mean_m = sum(margins) / n
    median_d = sorted(dmitrii_scores)[n // 2]
    median_o = sorted(opp_scores)[n // 2]
    median_m = sorted(margins)[n // 2]
    
    var_m = sum((x - mean_m) ** 2 for x in margins) / (n - 1) if n > 1 else 0.0
    std_m = math.sqrt(var_m)
    se_m = std_m / math.sqrt(n) if n > 0 else 0.0
    ci95 = (mean_m - 1.96 * se_m, mean_m + 1.96 * se_m)
    
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)
    ties = sum(1 for m in margins if m == 0)
    win_rate = wins / n
    
    p0_wr = sum(1 for m in p0_margins if m > 0) / len(p0_margins)
    p1_wr = sum(1 for m in p1_margins if m > 0) / len(p1_margins)
    worst_loss = min(margins)
    best_win = max(margins)
    
    return {
        "name": name,
        "N": n,
        "mean_cash": mean_d,
        "median_cash": median_d,
        "opp_mean": mean_o,
        "mean_margin": mean_m,
        "median_margin": median_m,
        "std_margin": std_m,
        "se_margin": se_m,
        "ci95": ci95,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "worst_loss": worst_loss,
        "best_win": best_win
    }

def main():
    seeds = list(range(20000, 20050)) # 50 fresh seeds x 2 seats = 100 matches per ablation
    opp_agent = compiled_v54_plus_residual.agent
    
    ablations = [
        ("0. Full Dmitrii LB2800 Baseline", make_dmitrii_variant()),
        ("1. Ablation: No Terminal Search", make_dmitrii_variant(terminal_search=False)),
        ("2. Ablation: No Shop Routing (Plan 0 Only)", make_dmitrii_variant(shop_routing=False)),
        ("3. Ablation: No Weed Repair", make_dmitrii_variant(weed_repair=False)),
        ("4. Ablation: No Advance Sales", make_dmitrii_variant(advance_sales=False)),
        ("5. Ablation: No Fertilizer (Pass)", make_dmitrii_variant(fertilizer_mode="pass")),
        ("6. Ablation: No Fertilizer (Water Instead)", make_dmitrii_variant(fertilizer_mode="water")),
        ("7. Candidate: Inject Preemption Overlay", make_dmitrii_variant(preemption_overlay=True)),
    ]
    
    print("=" * 105)
    print(f"DMITRII LB2800 CAUSAL ABLATION SUITE ({len(seeds)} seeds x 2 seats = 100 matches per ablation)")
    print(f"Opponent: V54++ Residual Baseline")
    print("=" * 105)
    
    results = []
    base_margin = None
    
    for name, agent_fn in ablations:
        t0 = time.time()
        res = evaluate_ablation(name, agent_fn, seeds, opp_agent)
        elapsed = time.time() - t0
        if base_margin is None:
            base_margin = res["mean_margin"]
            delta_base = 0.0
        else:
            delta_base = res["mean_margin"] - base_margin
            
        res["delta_from_baseline"] = delta_base
        res["elapsed_s"] = elapsed
        results.append(res)
        
        print(f"Finished {name:<42} | Cash: ${res['mean_cash']:,.0f} | Margin: {res['mean_margin']:+,.0f} (Delta: {delta_base:+,.0f}) | WR: {res['win_rate']*100:4.1f}% | Worst: {res['worst_loss']:+,.0f} | Elapsed: {elapsed:.1f}s")
        sys.stdout.flush()
        
    print("\n" + "=" * 125)
    print(f"{'Ablation':<42} | {'Mean Cash':<10} | {'Mean Margin':<12} | {'Delta to Base':<14} | {'95% CI':<24} | {'Win Rate':<9} | {'Worst Loss':<11}")
    print("-" * 125)
    for r in results:
        ci_str = f"[{r['ci95'][0]:+,.0f}, {r['ci95'][1]:+,.0f}]"
        print(f"{r['name']:<42} | ${r['mean_cash']:<9,.0f} | {r['mean_margin']:<+12,.0f} | {r['delta_from_baseline']:<+14,.0f} | {ci_str:<24} | {r['win_rate']*100:5.1f}%   | {r['worst_loss']:<+11,.0f}")
    print("=" * 125)
    
    out_path = os.path.join(BASE_DIR, "results", "dmitrii_causal_ablations_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved ablation results to {out_path}")

if __name__ == "__main__":
    main()
