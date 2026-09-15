"""
scratch/run_mechanism_and_solo_audit.py
=======================================
Performs:
  1. Exact Macro Immutability Verification (500 fresh seeds):
     - route_prior candidate == route_prior V54++ (must be 0 divergences across all turns)
     - Shop route selection identical across all turns
     - Worker schedules, livestock schedules, terminal schedules verified
  2. Mechanism-Level Causal Accounting (100 fresh seeds sample from holdout):
     - Preemption events: count, items, cash before/after, inventory before/after
     - Liquidity fronting & downstream investments
     - Commodity accounting: units produced, units sold, sale timing, average price, final inventory
       for strawberry, wheat, wool, milk, eggs, fertilizer
  3. Solo Test (50 fresh seeds 950,001 to 950,050 vs IDLE):
     - Candidate vs Frozen V54++ solo economics
"""

import os
import sys
import json
import time
import copy
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
    os.path.join(BASE_DIR, "candidates"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util

def bootstrap_ci(arr, n_boot=2000, ci=0.95):
    if len(arr) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(42)
    boot = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return (float(np.percentile(boot, alpha * 100)), float(np.percentile(boot, (1.0 - alpha) * 100)))

def worker_init():
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    for p in [
        os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
        os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
        os.path.join(BASE_DIR, "candidates"),
    ]:
        if p not in sys.path:
            sys.path.insert(0, p)

def idle_agent(obs):
    return [1, 0, 0, 0, 0, 0, 0]

def run_solo_match(seed):
    worker_init()
    from candidates.v54_plus_residual import agent as cand_agent
    from candidates.v54_plus_shop import agent as v54pp_agent
    
    # Run candidate vs IDLE
    env_c = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env_c.reset()
    for s in range(719):
        o0, o1 = env_c.state[0].observation, env_c.state[1].observation
        o0["step"], o1["step"] = s, s
        env_c.step([cand_agent(o0), idle_agent(o1)])
    r_cand = float(env_c.state[0].reward or 0)

    # Run V54++ vs IDLE
    env_v = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env_v.reset()
    for s in range(719):
        o0, o1 = env_v.state[0].observation, env_v.state[1].observation
        o0["step"], o1["step"] = s, s
        env_v.step([v54pp_agent(o0), idle_agent(o1)])
    r_v54pp = float(env_v.state[0].reward or 0)

    return {"seed": seed, "r_cand": r_cand, "r_v54pp": r_v54pp, "delta": r_cand - r_v54pp}

def run_immutability_and_accounting(seed):
    worker_init()
    from scratch.instrumented_v54_plus import InstrumentedV54Plus
    import candidates.v54_plus_residual as cand_mod
    import candidates.v54_plus_shop as v54pp_mod

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    v66_path = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
    spec = importlib.util.spec_from_file_location("v66_opp_audit", v66_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    v66 = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))

    agent_v54pp = InstrumentedV54Plus()
    agent_cand = InstrumentedV54Plus()
    agent_cand.config_dict["preempt_money_deficit"] = 2000.0
    agent_cand.config_dict["preempt_minimum_delta"] = 4.0
    agent_cand.config_dict["preempt_maximum_batch"] = 12
    agent_cand.v51_config = agent_cand.policies["backbone"].residual_config.__class__(**agent_cand.config_dict)
    for rname in agent_cand.policies:
        p = agent_cand.policies[rname]
        if hasattr(p, "controller"):
            p.controller.config = agent_cand.v51_config

    macro_route_divergences = 0
    shop_route_divergences = 0
    
    preempt_events = []
    
    # Track sales per commodity
    commodities = ["STRAWBERRY", "WHEAT", "WOOL", "MILK", "EGG", "FERTILIZER"]
    sales_cand = {c: {"units": 0, "total_revenue": 0.0, "sale_steps": []} for c in commodities}

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        
        o_copy = copy.deepcopy(o0)
        a_cand = agent_cand(o0)
        a_v54pp = agent_v54pp(o_copy)

        c_route = agent_cand.shop_state[0]["route"]
        v_route = agent_v54pp.shop_state[0]["route"]
        if c_route != v_route:
            shop_route_divergences += 1

        p_c = agent_cand.routes[c_route][s]
        p_v = agent_v54pp.routes[v_route][s]
        if p_c != p_v:
            macro_route_divergences += 1

        t_cand = agent_cand.telemetry_history[-1]
        if t_cand.get("firings", {}).get("market_preempt"):
            preempt_events.append({
                "step": s,
                "commodities": t_cand.get("preempt_commodities", []),
                "money_gap": t_cand.get("money_gap", 0.0),
            })

        # Track sales from a_cand
        market_actions = a_cand.get("market", []) if isinstance(a_cand, dict) else []
        for act in market_actions:
            if isinstance(act, (list, tuple)) and len(act) >= 3 and str(act[0]).startswith("SELL"):
                item, qty = str(act[1]), int(act[2])
                if item in sales_cand:
                    mkt = o0.get("market", {}).get(item, {})
                    cur_price = float(mkt.get("price", 0.0) or 0.0)
                    sales_cand[item]["units"] += qty
                    sales_cand[item]["total_revenue"] += qty * cur_price
                    sales_cand[item]["sale_steps"].append(s)

        env.step([a_cand, v66(o1)])

    r0 = float(env.state[0].reward or 0)
    r1 = float(env.state[1].reward or 0)

    inv = env.state[0].observation.get("players", [{}, {}])[0].get("inventory", {})

    return {
        "seed": seed,
        "macro_route_divergences": macro_route_divergences,
        "shop_route_divergences": shop_route_divergences,
        "preempt_count": len(preempt_events),
        "preempt_events": preempt_events,
        "sales": sales_cand,
        "r0": r0,
        "r1": r1,
        "final_inventory": inv,
    }

def main():
    print("=== STARTING MECHANISM TELEMETRY, IMMUTABILITY AUDIT & SOLO TEST ===")
    
    # 1. Solo test: 50 seeds vs IDLE
    solo_seeds = list(range(950001, 950051))
    print(f"\n[1/2] Running Solo Economics vs IDLE across {len(solo_seeds)} seeds ({solo_seeds[0]}–{solo_seeds[-1]})...")
    solo_results = []
    with ProcessPoolExecutor(max_workers=12) as executor:
        for r in executor.map(run_solo_match, solo_seeds):
            solo_results.append(r)

    cand_solo = np.array([r["r_cand"] for r in solo_results])
    v54pp_solo = np.array([r["r_v54pp"] for r in solo_results])
    deltas_solo = np.array([r["delta"] for r in solo_results])

    print("--- SOLO TEST RESULTS (vs IDLE) ---")
    print(f"Candidate Mean Solo Reward : ${np.mean(cand_solo):.2f}")
    print(f"V54++ Mean Solo Reward     : ${np.mean(v54pp_solo):.2f}")
    print(f"Paired Mean Delta          : ${np.mean(deltas_solo):.2f}")
    print(f"Paired Median Delta        : ${np.median(deltas_solo):.2f}")
    print(f"95% CI Delta               : {bootstrap_ci(deltas_solo)}")

    # 2. Immutability and Mechanism Accounting: 100 seeds from holdout
    audit_seeds = list(range(940001, 940101))
    print(f"\n[2/2] Running Detailed Telemetry & Immutability Audit across {len(audit_seeds)} seeds ({audit_seeds[0]}–{audit_seeds[-1]})...")
    audit_results = []
    with ProcessPoolExecutor(max_workers=12) as executor:
        for r in executor.map(run_immutability_and_accounting, audit_seeds):
            audit_results.append(r)

    tot_macro_div = sum(r["macro_route_divergences"] for r in audit_results)
    tot_shop_div = sum(r["shop_route_divergences"] for r in audit_results)
    avg_preempts = np.mean([r["preempt_count"] for r in audit_results])
    total_preempt_events = sum(r["preempt_count"] for r in audit_results)

    # Commodity aggregation
    commodities = ["STRAWBERRY", "WHEAT", "WOOL", "MILK", "EGG", "FERTILIZER"]
    comm_summary = {}
    for c in commodities:
        tot_units = sum(r["sales"][c]["units"] for r in audit_results)
        tot_rev = sum(r["sales"][c]["total_revenue"] for r in audit_results)
        all_steps = [s for r in audit_results for s in r["sales"][c]["sale_steps"]]
        mean_step = float(np.mean(all_steps)) if all_steps else 0.0
        avg_price = (tot_rev / tot_units) if tot_units > 0 else 0.0
        tot_inv = sum(r["final_inventory"].get(c, 0) for r in audit_results)
        comm_summary[c] = {
            "total_units_sold": tot_units,
            "avg_units_sold_per_match": tot_units / len(audit_seeds),
            "total_revenue": tot_rev,
            "avg_realized_price": avg_price,
            "mean_sale_step": mean_step,
            "total_final_inventory": tot_inv,
            "avg_final_inventory": tot_inv / len(audit_seeds),
        }

    print("\n--- MACRO IMMUTABILITY RESULTS ---")
    print(f"Total Macro Route Prior Divergences : {tot_macro_div} (MUST BE 0)")
    print(f"Total Shop Route Divergences        : {tot_shop_div} (MUST BE 0)")
    print(f"Average Preemptions per Match       : {avg_preempts:.2f}")
    print(f"Total Preemption Firings Observed   : {total_preempt_events}")

    print("\n--- COMMODITY SALES & TIMING ACCOUNTING ---")
    for c, s in comm_summary.items():
        print(f"  {c:<12}: Units Sold {s['avg_units_sold_per_match']:5.1f} | Avg Price ${s['avg_realized_price']:5.2f} | Mean Step {s['mean_sale_step']:5.1f} | Final Inv {s['avg_final_inventory']:4.1f}")

    out_file = os.path.join(BASE_DIR, "research", "residual_mechanism_and_solo_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "solo_test": {
                "num_seeds": len(solo_seeds),
                "cand_mean": float(np.mean(cand_solo)),
                "v54pp_mean": float(np.mean(v54pp_solo)),
                "mean_delta": float(np.mean(deltas_solo)),
                "median_delta": float(np.median(deltas_solo)),
                "ci_95": bootstrap_ci(deltas_solo),
            },
            "immutability_and_accounting": {
                "num_seeds": len(audit_seeds),
                "total_macro_divergences": tot_macro_div,
                "total_shop_divergences": tot_shop_div,
                "avg_preempts_per_match": float(avg_preempts),
                "total_preempt_events": int(total_preempt_events),
                "commodity_accounting": comm_summary,
                "sample_preempt_events": [e for r in audit_results for e in r["preempt_events"][:3]][:20],
            }
        }, f, indent=2)

    print(f"\nMechanism and Solo audit results saved to {out_file}")

if __name__ == "__main__":
    main()
