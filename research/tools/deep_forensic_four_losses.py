import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict
import numpy as np

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

os.makedirs("research/v56/analysis", exist_ok=True)
os.makedirs("research/v56/counterfactuals", exist_ok=True)
os.makedirs("research/v56/candidates", exist_ok=True)
os.makedirs("research/v56/benchmarks", exist_ok=True)
os.makedirs("research/v56/reports", exist_ok=True)

loss_configs = [
    {"loss_id": "L1", "seed": 250617, "seat": 0, "opp_seat": 1},
    {"loss_id": "L2", "seed": 250617, "seat": 1, "opp_seat": 0},
    {"loss_id": "L3", "seed": 250621, "seat": 0, "opp_seat": 1},
    {"loss_id": "L4", "seed": 250621, "seat": 1, "opp_seat": 0},
]

win_comparisons = [
    {"win_id": "W1", "seed": 250616, "seat": 0, "opp_seat": 1},
    {"win_id": "W2", "seed": 250618, "seat": 0, "opp_seat": 1},
    {"win_id": "W3", "seed": 250620, "seat": 0, "opp_seat": 1},
    {"win_id": "W4", "seed": 250622, "seat": 0, "opp_seat": 1},
]

def trace_game(seed, seat, opp_seat):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    telemetry = {
        "step": [],
        "cash_v49": [],
        "cash_v44": [],
        "margin": [],
        "v49_shed": [],
        "v44_shed": [],
        "v49_sales": defaultdict(list), # commodity -> [(step, qty, price)]
        "v44_sales": defaultdict(list),
        "v49_purchases": defaultdict(list),
        "v44_purchases": defaultdict(list),
        "v49_animals": [],
        "v44_animals": [],
        "unlocked_shops": [],
        "market_prices": defaultdict(list),
        "market_inventory": defaultdict(list),
        "v49_actions_summary": defaultdict(int),
        "v44_actions_summary": defaultdict(int),
    }
    
    for step in range(719):
        # Record pre-step state
        farm49 = obs[seat]["farms"][seat]
        farm44 = obs[opp_seat]["farms"][opp_seat]
        mkt = obs[0]["market"]
        town = obs[0]["town"]
        
        telemetry["step"].append(step)
        telemetry["cash_v49"].append(float(farm49["money"]))
        telemetry["cash_v44"].append(float(farm44["money"]))
        telemetry["margin"].append(float(farm49["money"]) - float(farm44["money"]))
        
        if step % 72 == 0:
            telemetry["unlocked_shops"].append({
                "step": step,
                "shops": list(town.get("unlocked_shops", []))
            })
            
        for comm in ("MILK", "WOOL", "EGG", "WHEAT", "CARROT", "STRAWBERRY", "MELON", "TOMATO"):
            telemetry["market_prices"][comm].append(mkt["prices"].get(comm, 0))
            telemetry["market_inventory"][comm].append(mkt["inventory"].get(comm, 0))
            
        a49 = v49_mod.agent(obs[seat])
        a44 = v44_mod.agent(obs[opp_seat])
        
        # Track market actions
        if isinstance(a49, dict):
            for m_op in a49.get("market", []):
                if m_op and len(m_op) >= 3 and m_op[0] == "SELL":
                    telemetry["v49_sales"][m_op[1]].append((step, int(m_op[2]), mkt["prices"].get(m_op[1], 0)))
                elif m_op and len(m_op) >= 3 and m_op[0] == "BUY_ANIMAL":
                    telemetry["v49_purchases"][m_op[1]].append((step, int(m_op[2])))
            if a49.get("farmer"):
                telemetry["v49_actions_summary"][a49["farmer"][0]] += 1
            for h in a49.get("hands", []):
                if h:
                    telemetry["v49_actions_summary"][h[0]] += 1

        if isinstance(a44, dict):
            for m_op in a44.get("market", []):
                if m_op and len(m_op) >= 3 and m_op[0] == "SELL":
                    telemetry["v44_sales"][m_op[1]].append((step, int(m_op[2]), mkt["prices"].get(m_op[1], 0)))
                elif m_op and len(m_op) >= 3 and m_op[0] == "BUY_ANIMAL":
                    telemetry["v44_purchases"][m_op[1]].append((step, int(m_op[2])))
            if a44.get("farmer"):
                telemetry["v44_actions_summary"][a44["farmer"][0]] += 1
            for h in a44.get("hands", []):
                if h:
                    telemetry["v44_actions_summary"][h[0]] += 1

        obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
        if done:
            break
            
    final_farm49 = obs[seat]["farms"][seat]
    final_farm44 = obs[opp_seat]["farms"][opp_seat]
    final_cash49 = float(final_farm49["money"])
    final_cash44 = float(final_farm44["money"])
    
    # Animals count on terminal tiles
    def count_animals(farm):
        counts = defaultdict(int)
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and "animal" in tile:
                    counts[tile["animal"]] += 1
        return dict(counts)

    return {
        "final_cash_v49": final_cash49,
        "final_cash_v44": final_cash44,
        "margin": final_cash49 - final_cash44,
        "v49_animals": count_animals(final_farm49),
        "v44_animals": count_animals(final_farm44),
        "v49_terminal_shed": dict(final_farm49.get("shed", {}) or {}),
        "v44_terminal_shed": dict(final_farm44.get("shed", {}) or {}),
        "unlocked_shops": [s["shops"] for s in telemetry["unlocked_shops"]][-1] if telemetry["unlocked_shops"] else [],
        "telemetry": telemetry
    }

print("Tracing the 4 Loss Worlds...")
four_losses_data = {}
for cfg in loss_configs:
    lid = cfg["loss_id"]
    print(f"Tracing {lid}: Seed {cfg['seed']}, Seat {cfg['seat']}...")
    res = trace_game(cfg["seed"], cfg["seat"], cfg["opp_seat"])
    
    # Find decisive divergence step (where margin permanently turns negative or drops sharply)
    margins = res["telemetry"]["margin"]
    neg_steps = [i for i, m in enumerate(margins) if m < 0]
    first_neg = neg_steps[0] if neg_steps else None
    
    # Calculate commodity revenue summary
    rev_by_comm = {}
    for comm, sales in res["telemetry"]["v49_sales"].items():
        tot_qty = sum(s[1] for s in sales)
        tot_val = sum(s[1] * s[2] for s in sales)
        rev_by_comm[comm] = {"qty": tot_qty, "revenue": tot_val, "avg_price": tot_val / tot_qty if tot_qty else 0}
        
    v44_rev_by_comm = {}
    for comm, sales in res["telemetry"]["v44_sales"].items():
        tot_qty = sum(s[1] for s in sales)
        tot_val = sum(s[1] * s[2] for s in sales)
        v44_rev_by_comm[comm] = {"qty": tot_qty, "revenue": tot_val, "avg_price": tot_val / tot_qty if tot_qty else 0}

    four_losses_data[lid] = {
        "loss_id": lid,
        "seed": cfg["seed"],
        "seat": cfg["seat"],
        "opponent": "V44",
        "opp_seat": cfg["opp_seat"],
        "v49_final_cash": res["final_cash_v49"],
        "v44_final_cash": res["final_cash_v44"],
        "margin": res["margin"],
        "first_negative_margin_step": first_neg,
        "terminal_shops": res["unlocked_shops"],
        "v49_terminal_animals": res["v49_animals"],
        "v44_terminal_animals": res["v44_animals"],
        "v49_terminal_shed": res["v49_terminal_shed"],
        "v44_terminal_shed": res["v44_terminal_shed"],
        "v49_commodity_revenue": rev_by_comm,
        "v44_commodity_revenue": v44_rev_by_comm,
        "v49_action_counts": dict(res["telemetry"]["v49_actions_summary"]),
        "v44_action_counts": dict(res["telemetry"]["v44_actions_summary"]),
        # Last 72 steps cash progression
        "v49_last_72_steps_cash": res["telemetry"]["cash_v49"][-72:],
        "v44_last_72_steps_cash": res["telemetry"]["cash_v44"][-72:],
        "margin_last_72_steps": res["telemetry"]["margin"][-72:],
    }
    print(f"  {lid} Complete: Margin = ${res['margin']:+.2f}, First Neg Step = {first_neg}")

# Also trace nearby comparison wins
comparison_wins_data = {}
for cfg in win_comparisons:
    wid = cfg["win_id"]
    print(f"Tracing {wid}: Seed {cfg['seed']}, Seat {cfg['seat']}...")
    res = trace_game(cfg["seed"], cfg["seat"], cfg["opp_seat"])
    comparison_wins_data[wid] = {
        "win_id": wid,
        "seed": cfg["seed"],
        "seat": cfg["seat"],
        "margin": res["margin"],
        "v49_final_cash": res["final_cash_v49"],
        "v44_final_cash": res["final_cash_v44"],
        "terminal_shops": res["unlocked_shops"],
        "v49_terminal_animals": res["v49_animals"],
        "v44_terminal_animals": res["v44_animals"],
    }
    print(f"  {wid} Complete: Margin = ${res['margin']:+.2f}")

output_payload = {
    "four_losses": four_losses_data,
    "comparison_wins": comparison_wins_data
}

with open("research/v56/analysis/V49_FOUR_LOSSES.json", "w") as f:
    json.dump(output_payload, f, indent=2)

print("\nSaved research/v56/analysis/V49_FOUR_LOSSES.json!")
