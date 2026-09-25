# SPDX-License-Identifier: MIT
"""EXP-V32-P10-01: A7 Loss Forensics & Opportunity Discovery.

Executes instrumented matches of the frozen A7 incumbent against the benchmark panel:
1. E8_DMITRII (Frontier 2800+ terminal search)
2. E1_V22R1 (Live Slot A champion)
3. E0_V3 (Base tape player)
4. V54 (Declarative backbone reference)
5. SYN_AGG (Adversarial hostile market dumper)

Collects full per-step telemetry to identify where A7 loses or leaves money on the table:
- First economic divergence step
- Market state and spot prices
- Opponent actions (sales, hiring, structures)
- Player inventory and cash
- Terminal cash delta
"""

from __future__ import annotations
import argparse
import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P10_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
if P10_ROOT not in sys.path:
    sys.path.append(P10_ROOT)

from kaggle_environments import make
from v32_common import assert_frozen, check_seed_allowed, load_agent
from candidates.v32_p10.config import DEV_SEEDS_HISTORICAL, PRODUCTS
from candidates.v32_p10.incumbent import load_fresh_a7


def _synthetic_aggressive(obs, cfg=None):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else {}
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {})
    orders = []
    for prod in ["MILK", "WOOL", "MELON", "STRAWBERRY", "WHEAT"]:
        qty = shed.get(prod, 0)
        if qty > 0:
            orders.append(["SELL", prod, min(qty, 30)])
    orders = orders[:10]
    return {"market": orders, "farmer": ["PASS"], "hands": []}


def _load_opponent(opp_id: str):
    if opp_id == "SYN_AGG":
        return _synthetic_aggressive
    elif opp_id == "V54":
        path = os.path.join(REPO_ROOT, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
        import uuid
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        ns = {"__name__": f"v54_iso_{uuid.uuid4().hex[:8]}"}
        exec(compile(code, path, "exec"), ns)
        return ns.get("agent")
    elif opp_id in ("E2_A7", "A7"):
        return load_agent("E9_AST")
    elif opp_id == "o9_market_aggressor":
        path = os.path.join(REPO_ROOT, "opponents", "o9_market_aggressor.py")
        import uuid
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        ns = {"__name__": f"o9_iso_{uuid.uuid4().hex[:8]}"}
        exec(compile(code, path, "exec"), ns)
        return ns.get("agent")
    else:
        return load_agent(opp_id)


def _to_callable(agent):
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return lambda o, c=None: agent.act(o, c)
    elif callable(agent):
        return agent
    raise ValueError(f"Agent {agent} is not callable")


def _run_forensic_match(args: Tuple[str, int, int]) -> Dict[str, Any]:
    opp_id, seed, seat = args
    check_seed_allowed(seed)
    
    a7_fn = load_fresh_a7()
    opp_fn = _load_opponent(opp_id)
    
    p_callable = _to_callable(a7_fn)
    opp_callable = _to_callable(opp_fn)
    
    agents = [p_callable, opp_callable] if seat == 0 else [opp_callable, p_callable]
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    
    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0
    
    n_steps = len(env.steps)
    final_step = env.steps[-1]
    p_reward = float(final_step[seat]["reward"] or 0.0)
    opp_reward = float(final_step[1 - seat]["reward"] or 0.0)
    margin = p_reward - opp_reward
    win = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
    
    # Analyze divergence timeline
    divergences = []
    p_money_curve = []
    opp_money_curve = []
    loss_events = []
    
    for t in range(n_steps):
        step_rec = env.steps[t]
        obs_p = step_rec[seat]["observation"]
        obs_opp = step_rec[1 - seat]["observation"]
        
        p_farm = obs_p["farms"][seat]
        opp_farm = obs_opp["farms"][1 - seat]
        
        p_cash = float(p_farm.get("money", 0.0) or 0.0)
        opp_cash = float(opp_farm.get("money", 0.0) or 0.0)
        
        p_money_curve.append(p_cash)
        opp_money_curve.append(opp_cash)
        
        # Track action taken at step t (recorded at step t+1)
        if t + 1 < n_steps:
            act_p = env.steps[t + 1][seat].get("action") or {}
            act_opp = env.steps[t + 1][1 - seat].get("action") or {}
            
            # Check market pressure
            mkt_p = act_p.get("market") or []
            mkt_opp = act_opp.get("market") or []
            
            # Look for large market dumps by opponent
            for o in mkt_opp:
                if o and o[0] == "SELL" and len(o) >= 3:
                    item, qty = o[1], int(o[2])
                    if qty >= 10:
                        loss_events.append({
                            "step": t,
                            "type": "OPPONENT_LARGE_SELL",
                            "item": item,
                            "qty": qty,
                            "p_cash": p_cash,
                            "opp_cash": opp_cash
                        })
                        
        # Check cash deficit divergence
        if p_cash < opp_cash - 500 and not divergences:
            divergences.append({
                "step": t,
                "p_cash": p_cash,
                "opp_cash": opp_cash,
                "deficit": opp_cash - p_cash
            })

    first_div_step = divergences[0]["step"] if divergences else -1
    first_div_deficit = divergences[0]["deficit"] if divergences else 0.0
    
    return {
        "opp": opp_id,
        "seed": seed,
        "seat": seat,
        "p_cash": p_reward,
        "opp_cash": opp_reward,
        "margin": margin,
        "win": win,
        "duration": dur,
        "first_div_step": first_div_step,
        "first_div_deficit": first_div_deficit,
        "n_loss_events": len(loss_events),
        "loss_events": loss_events[:10],
        "p_final_cash": p_reward,
        "opp_final_cash": opp_reward
    }


def run_a7_loss_forensics(
    opponents: List[str] = None,
    seeds: List[int] = None,
    max_workers: int = 4
) -> Dict[str, Any]:
    assert_frozen()
    opponents = opponents or ["E8_DMITRII", "E1_V22R1", "E0_V3", "V54", "SYN_AGG"]
    seeds = seeds or DEV_SEEDS_HISTORICAL
    
    tasks = []
    for opp in opponents:
        for s in seeds:
            for seat in (0, 1):
                tasks.append((opp, s, seat))
                
    print(f"\n=================================================================")
    print(f"EXP-V32-P10-01: A7 LOSS FORENSICS ACROSS {len(opponents)} OPPONENTS x {len(seeds)} SEEDS x 2 SEATS ({len(tasks)} MATCHES)")
    print(f"=================================================================")
    
    results: List[Dict[str, Any]] = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_forensic_match, t): t for t in tasks}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            status = "WIN" if res["win"] == 1.0 else ("LOSS" if res["win"] == 0.0 else "TIE")
            print(f"  [{res['opp']}] Seed {res['seed']} Seat {res['seat']}: {status} | Cash=${res['p_cash']:,.2f} Opp=${res['opp_cash']:,.2f} Margin=${res['margin']:+,.2f} (DivStep={res['first_div_step']})")
            
    # Group by opponent
    by_opp: Dict[str, List[Dict[str, Any]]] = {o: [] for o in opponents}
    for r in results:
        by_opp[r["opp"]].append(r)
        
    summary = {}
    print("\n" + "=" * 90)
    print(f"{'Opponent':<15} {'Legs':<5} {'Wins':<5} {'Losses':<7} {'Ties':<5} {'Win%':<7} {'Mean Margin':<14} {'Min Margin':<14}")
    print("-" * 90)
    
    losing_matches = []
    low_margin_matches = []
    
    for opp, records in by_opp.items():
        margins = [r["margin"] for r in records]
        wins = sum(1 for r in records if r["win"] == 1.0)
        losses = sum(1 for r in records if r["win"] == 0.0)
        ties = sum(1 for r in records if r["win"] == 0.5)
        mean_margin = float(sum(margins) / len(margins))
        min_margin = float(min(margins))
        win_pct = wins / len(records) * 100.0
        
        summary[opp] = {
            "legs": len(records),
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_pct": win_pct,
            "mean_margin": mean_margin,
            "min_margin": min_margin,
            "p25_margin": float(sorted(margins)[len(margins)//4]),
            "median_margin": float(sorted(margins)[len(margins)//2])
        }
        print(f"{opp:<15} {len(records):<5} {wins:<5} {losses:<7} {ties:<5} {win_pct:>5.1f}% ${mean_margin:>+12,.2f} ${min_margin:>+12,.2f}")
        
        for r in records:
            if r["win"] == 0.0:
                losing_matches.append(r)
            elif 0.0 < r["margin"] < 2000.0:
                low_margin_matches.append(r)

    print("=" * 90)
    print(f"Total Losing Matches Found: {len(losing_matches)}")
    print(f"Total Low-Margin Matches (<$2k) Found: {len(low_margin_matches)}")
    
    return {
        "summary": summary,
        "losing_matches": losing_matches,
        "low_margin_matches": low_margin_matches,
        "all_records": results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--opponents", nargs="+", default=None)
    parser.add_argument("--seeds", type=int, nargs="+", default=None)
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--out", default="candidates/v32_p10/reports/loss_forensics.json")
    args = parser.parse_args()
    
    res = run_a7_loss_forensics(args.opponents, args.seeds, args.workers)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"\nForensics results written to {args.out}")
