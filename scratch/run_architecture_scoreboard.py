"""
ARCHITECTURE SCOREBOARD EVALUATION HARNESS
Runs a rigorous, reproducible 100-match tournament (50 stratified seeds x 2 balanced seats)
for each candidate against:
1. Benchmark Opponent: compiled_v54_plus_residual (Frozen Live Control 56146971)
2. Head-to-Head: dmitrii_lb2800 Base Policy

Calculates:
- Mean Cash, Median Cash, Std Dev
- Win Rate, Loss Rate, Tie Rate
- Mean Paired Margin & 95% CI
- Best Win, Worst Loss
- Catastrophic Loss Rate (< $60,000)
- Breakdown by Shop Category (Yarn, Dairy, Pizza, Pet Cafe, Dispersed)
- Breakdown by Seat (Seat 0 vs Seat 1)
"""
import argparse
import copy
import json
import math
import os
import sys
import time
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54_res
import compiled_v54_plus_shop as v54_shop
from closed_loop_agent import ClosedLoopAgent
from closed_loop_v2 import ClosedLoopAgentV2

class SafeDairyPolicy:
    """Runs Safe Dairy tape on Smoothie+Ice Cream worlds; Dmitrii otherwise."""
    def __init__(self):
        self.dmitrii = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        tape_path = os.path.join(BASE_DIR, "scratch", "safe_liquidity_dairy_tape.json")
        with open(tape_path, "r") as f:
            self.dairy_tape = json.load(f)
        self.players = {}

    def act(self, obs):
        step = int(obs["step"])
        player = int(obs["player"])
        state = self.players.get(player)
        if state is None or step <= state.last_step:
            state = self.players[player] = mod_r.DayState()
        state.last_step = step

        if step == 144:
            shops = set(obs["town"]["unlocked_shops"])
            if "SMOOTHIE_SHOP" in shops and "ICE_CREAM_SHOP" in shops:
                state.is_dairy = True
            else:
                state.is_dairy = False
                state.plan = mod_r.SHOP_PLANS.get(tuple(obs["town"]["unlocked_shops"][:2]), 0)

        if getattr(state, "is_dairy", False):
            view = mod_r.FarmView(obs)
            action = copy.deepcopy(self.dairy_tape[step])
            mod_r.repair_weeds(action, view, state, step)
            mod_r.subtract_advanced_sales(action, state, step)
            mod_r.advance_sales(action, view, state, self.dairy_tape, step)
            action["market"] = action["market"][:mod_r.MAX_ORDERS]
            return mod_r.liquidate(view) if step == mod_r.LAST_STEP else action
        else:
            return self.dmitrii.act(obs)

def create_candidate_agent(cand_id: str):
    if cand_id == "V54_RESIDUAL":
        return lambda obs: v54_res.agent(obs)
    elif cand_id == "V54_SHOP":
        return lambda obs: v54_shop.agent(obs)
    elif cand_id == "DMITRII_BASE":
        p = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        return lambda obs: p.act(obs)
    elif cand_id == "SAFE_DAIRY":
        p = SafeDairyPolicy()
        return lambda obs: p.act(obs)
    elif cand_id == "CLOSED_LOOP_V1":
        ag = ClosedLoopAgent(switching_mode="MILESTONE_CONSERVATIVE", shed_policy="88_CEILING")
        return lambda obs: ag.act(obs)
    elif cand_id == "CLOSED_LOOP_V2":
        ag = ClosedLoopAgentV2(jit_headroom_threshold=96)
        return lambda obs: ag.act(obs)
    else:
        raise ValueError(f"Unknown candidate: {cand_id}")

def evaluate_matchup(cand_id: str, opp_id: str, seed_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    matches = []
    
    for item in seed_items:
        s = item["seed"]
        cat = item["category"]
        
        # Match 1: Candidate as Player 0, Opponent as Player 1
        c_fn_0 = create_candidate_agent(cand_id)
        o_fn_1 = create_candidate_agent(opp_id)
        g0 = kagsim.Game(s)
        while not g0.done:
            g0.step(c_fn_0(g0.observe(0)), o_fn_1(g0.observe(1)))
        rew_c0 = g0.reward(0)
        rew_o1 = g0.reward(1)
        matches.append({
            "seed": s, "category": cat, "seat": 0,
            "cand_cash": rew_c0, "opp_cash": rew_o1, "margin": rew_c0 - rew_o1
        })

        # Match 2: Candidate as Player 1, Opponent as Player 0
        o_fn_0 = create_candidate_agent(opp_id)
        c_fn_1 = create_candidate_agent(cand_id)
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(o_fn_0(g1.observe(0)), c_fn_1(g1.observe(1)))
        rew_c1 = g1.reward(1)
        rew_o0 = g1.reward(0)
        matches.append({
            "seed": s, "category": cat, "seat": 1,
            "cand_cash": rew_c1, "opp_cash": rew_o0, "margin": rew_c1 - rew_o0
        })

    # Statistical Aggregation
    N = len(matches)
    cand_cashes = [m["cand_cash"] for m in matches]
    opp_cashes = [m["opp_cash"] for m in matches]
    margins = [m["margin"] for m in matches]
    
    mean_cash = sum(cand_cashes) / N
    cand_cashes_sorted = sorted(cand_cashes)
    median_cash = cand_cashes_sorted[N // 2]
    var_cash = sum((c - mean_cash) ** 2 for c in cand_cashes) / (N - 1)
    std_cash = math.sqrt(var_cash)
    
    mean_margin = sum(margins) / N
    margins_sorted = sorted(margins)
    median_margin = margins_sorted[N // 2]
    var_margin = sum((m - mean_margin) ** 2 for m in margins) / (N - 1)
    se_margin = math.sqrt(var_margin) / math.sqrt(N)
    ci95 = [mean_margin - 1.96 * se_margin, mean_margin + 1.96 * se_margin]
    
    wins = sum(1 for m in margins if m > 0)
    ties = sum(1 for m in margins if m == 0)
    losses = sum(1 for m in margins if m < 0)
    win_rate = (wins / N) * 100.0
    loss_rate = (losses / N) * 100.0
    tie_rate = (ties / N) * 100.0
    
    worst_loss = min(margins)
    best_win = max(margins)
    catastrophic = sum(1 for c in cand_cashes if c < 60000.0)
    catastrophic_rate = (catastrophic / N) * 100.0

    # Breakdown by Category
    cat_breakdown = {}
    cats = sorted(list({m["category"] for m in matches}))
    for cat in cats:
        cat_matches = [m for m in matches if m["category"] == cat]
        n_c = len(cat_matches)
        c_mean = sum(m["cand_cash"] for m in cat_matches) / n_c
        c_margin = sum(m["margin"] for m in cat_matches) / n_c
        c_wins = sum(1 for m in cat_matches if m["margin"] > 0)
        cat_breakdown[cat] = {
            "n": n_c,
            "mean_cash": c_mean,
            "mean_margin": c_margin,
            "win_rate": (c_wins / n_c) * 100.0
        }

    # Breakdown by Seat
    seat_breakdown = {}
    for seat in [0, 1]:
        s_matches = [m for m in matches if m["seat"] == seat]
        n_s = len(s_matches)
        s_mean = sum(m["cand_cash"] for m in s_matches) / n_s
        s_margin = sum(m["margin"] for m in s_matches) / n_s
        s_wins = sum(1 for m in s_matches if m["margin"] > 0)
        seat_breakdown[f"Seat_{seat}"] = {
            "n": n_s,
            "mean_cash": s_mean,
            "mean_margin": s_margin,
            "win_rate": (s_wins / n_s) * 100.0
        }

    return {
        "candidate": cand_id,
        "opponent": opp_id,
        "matches": N,
        "mean_cash": mean_cash,
        "median_cash": median_cash,
        "std_cash": std_cash,
        "mean_margin": mean_margin,
        "median_margin": median_margin,
        "ci95": ci95,
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "tie_rate": tie_rate,
        "worst_loss": worst_loss,
        "best_win": best_win,
        "catastrophic_rate": catastrophic_rate,
        "cat_breakdown": cat_breakdown,
        "seat_breakdown": seat_breakdown,
        "raw_matches": matches
    }

def print_summary_table(results_list: List[Dict[str, Any]], opp_name: str):
    print("\n" + "=" * 120)
    print(f"SCOREBOARD SUMMARY vs {opp_name} (N={results_list[0]['matches']} matches, Balanced Seats)")
    print("=" * 120)
    header = f"{'Candidate':<18} | {'Mean Cash':<11} | {'Median':<11} | {'Win Rate':<9} | {'Mean Margin':<12} | {'95% CI':<24} | {'Catastrophic':<12} | {'Worst Loss':<11}"
    print(header)
    print("-" * 120)
    for r in results_list:
        ci_str = f"[${r['ci95'][0]:+,.0f}, ${r['ci95'][1]:+,.0f}]"
        print(f"{r['candidate']:<18} | ${r['mean_cash']:>9,.0f} | ${r['median_cash']:>9,.0f} | {r['win_rate']:>7.1f}% | ${r['mean_margin']:>+10,.0f} | {ci_str:<24} | {r['catastrophic_rate']:>10.1f}% | ${r['worst_loss']:>+9,.0f}")
    print("=" * 120)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["qualification", "holdout"], default="qualification")
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    seed_file = f"scratch/{args.tier}_seeds.json" if args.tier == "qualification" else "scratch/fresh_holdout_seeds.json"
    if not os.path.exists(seed_file):
        print(f"Error: {seed_file} not found.")
        sys.exit(1)

    with open(seed_file, "r") as f:
        data = json.load(f)
    seed_items = data["seeds"]
    print(f"\nLoaded {len(seed_items)} {args.tier.upper()} seeds. Running 2 seats per seed -> {len(seed_items) * 2} total matches per candidate.")

    candidates = [
        "V54_RESIDUAL",
        "V54_SHOP",
        "DMITRII_BASE",
        "SAFE_DAIRY",
        "CLOSED_LOOP_V1",
        "CLOSED_LOOP_V2"
    ]

    t0 = time.time()
    
    # 1. EVALUATE ALL CANDIDATES VS BENCHMARK CONTROL (V54_RESIDUAL)
    print(f"\nEvaluating candidates against benchmark control (V54_RESIDUAL)...")
    results_vs_v54 = []
    for cid in candidates:
        print(f"  Running {cid} vs V54_RESIDUAL...")
        res = evaluate_matchup(cid, "V54_RESIDUAL", seed_items)
        results_vs_v54.append(res)
    print_summary_table(results_vs_v54, "V54_RESIDUAL (Control Submission 56146971)")

    # 2. EVALUATE ALL CANDIDATES VS DMITRII BASE (HEAD-TO-HEAD)
    print(f"\nEvaluating candidates in direct Head-to-Head against DMITRII_BASE...")
    results_vs_dm = []
    for cid in candidates:
        if cid == "DMITRII_BASE":
            continue
        print(f"  Running {cid} vs DMITRII_BASE...")
        res = evaluate_matchup(cid, "DMITRII_BASE", seed_items)
        results_vs_dm.append(res)
    print_summary_table(results_vs_dm, "DMITRII_BASE (Gold Standard Champion)")

    t1 = time.time()
    print(f"\nTotal tournament evaluation time: {t1 - t0:.1f}s")

    out_path = args.out or f"scratch/scoreboard_{args.tier}_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "tier": args.tier,
            "seeds_count": len(seed_items),
            "matches_per_cand": len(seed_items) * 2,
            "results_vs_v54": results_vs_v54,
            "results_vs_dm": results_vs_dm
        }, f, indent=2)
    print(f"Full scoreboard results saved to {out_path}")

if __name__ == "__main__":
    main()
