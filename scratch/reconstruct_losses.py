import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

HISTORICAL_LOSSES = [
    {"loss_id": "L01", "seed": 250416, "seat": 0, "nominal_loss": -716.0, "category": "Barn/Macro"},
    {"loss_id": "L02", "seed": 250416, "seat": 1, "nominal_loss": -716.0, "category": "Barn/Macro"},
    {"loss_id": "L03", "seed": 250428, "seat": 0, "nominal_loss": -31.0, "category": "Late Crop/Timing"},
    {"loss_id": "L04", "seed": 250428, "seat": 1, "nominal_loss": -160.0, "category": "Late Crop/Timing"},
    {"loss_id": "L05", "seed": 250433, "seat": 0, "nominal_loss": -470.0, "category": "Route Branch"},
    {"loss_id": "L06", "seed": 250433, "seat": 1, "nominal_loss": -470.0, "category": "Route Branch"},
    {"loss_id": "L07", "seed": 250436, "seat": 0, "nominal_loss": -1405.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L08", "seed": 250436, "seat": 1, "nominal_loss": -1405.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L09", "seed": 250439, "seat": 0, "nominal_loss": -1407.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L10", "seed": 250439, "seat": 1, "nominal_loss": -1407.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L11", "seed": 250497, "seat": 1, "nominal_loss": -901.0, "category": "Route Branch"},
]

def extract_farm_stats(farm: Dict[str, Any]) -> Dict[str, Any]:
    tiles = farm.get("tiles") or []
    counts = {
        "money": float(farm.get("money", 0.0)),
        "hands": len(farm.get("hands") or []),
        "quadrants": list(farm.get("unlocked_quadrants") or []),
        "unlocked_tiles": 0,
        "pastures": 0,
        "coops": 0,
        "cows": 0,
        "sheep": 0,
        "geese": 0,
        "plants": 0,
        "unharvested_milk": 0,
        "unharvested_wool": 0,
        "unharvested_eggs": 0,
        "cows_fed_today": 0,
        "cows_cared_today": 0,
    }
    for row in tiles:
        for t in row:
            if t != "LOCKED":
                counts["unlocked_tiles"] += 1
            if isinstance(t, dict):
                kind = t.get("kind")
                animal = t.get("animal")
                if kind == "PASTURE":
                    counts["pastures"] += 1
                elif kind == "COOP":
                    counts["coops"] += 1
                elif kind == "PLANT":
                    counts["plants"] += 1
                
                if animal == "COW":
                    counts["cows"] += 1
                    counts["unharvested_milk"] += t.get("yield_units", 0)
                    if t.get("fed_today"):
                        counts["cows_fed_today"] += 1
                    if t.get("cared_today"):
                        counts["cows_cared_today"] += 1
                elif animal == "SHEEP":
                    counts["sheep"] += 1
                    counts["unharvested_wool"] += t.get("yield_units", 0)
                elif animal == "GOOSE":
                    counts["geese"] += 1
                    counts["unharvested_eggs"] += t.get("yield_units", 0)
    return counts

def analyze_loss(loss_spec: Dict[str, Any]) -> Dict[str, Any]:
    seed = loss_spec["seed"]
    seat = loss_spec["seat"]
    opp_seat = 1 - seat
    
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    
    snapshots = {}
    v49_decision_record = {}
    
    # Run full match
    target_steps = [0, 143, 144, 150, 151, 168, 300, 719]
    
    for step in range(720):
        # Current observation for V49
        v49_obs = obs[seat]
        opp_obs = obs[opp_seat]
        
        if step in target_steps:
            opp_stats = extract_farm_stats(v49_obs["farms"][opp_seat])
            v49_stats = extract_farm_stats(v49_obs["farms"][seat])
            mkt_prices = dict(v49_obs["market"]["prices"])
            mkt_inv = dict(v49_obs["market"]["inventory"])
            shops = list(v49_obs["town"]["unlocked_shops"])
            
            snapshots[f"step_{step}"] = {
                "step": step,
                "shops": shops,
                "milk_price": mkt_prices.get("MILK"),
                "egg_price": mkt_prices.get("EGG"),
                "wool_price": mkt_prices.get("WOOL"),
                "market_prices": mkt_prices,
                "market_inventory": mkt_inv,
                "opponent_public_state": opp_stats,
                "v49_state": v49_stats
            }
        
        # Call agents
        if seat == 0:
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = v44_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
        else:
            a0 = v44_mod.agent(obs[0], sim.configuration)
            a1 = v49_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
            
        if step == 150:
            v49_decision_record["step_150_v49_action"] = a0 if seat == 0 else a1
            v49_decision_record["cs_report"] = dict(v49_mod._CS_REPORT)
            v49_decision_record["cs_state"] = dict(v49_mod._CS_STATE.get(seat, {}))
            
        obs, rewards, done, info = sim.step(actions)
        if done:
            break
            
    v49_terminal_cash = float(obs[seat]["farms"][seat]["money"])
    opp_terminal_cash = float(obs[seat]["farms"][opp_seat]["money"])
    margin = v49_terminal_cash - opp_terminal_cash
    
    return {
        "loss_id": loss_spec["loss_id"],
        "seed": seed,
        "seat": seat,
        "nominal_loss": loss_spec["nominal_loss"],
        "category": loss_spec["category"],
        "terminal_v49_cash": v49_terminal_cash,
        "terminal_opp_cash": opp_terminal_cash,
        "terminal_margin": margin,
        "v49_decision": v49_decision_record,
        "snapshots": snapshots
    }

print("Running loss reconstruction across all 11 matches...")
results = []
for loss in HISTORICAL_LOSSES:
    res = analyze_loss(loss)
    print(f"Done {res['loss_id']} (seed {res['seed']} seat {res['seat']}): margin = ${res['terminal_margin']:,.2f}, cs_decision = {res['v49_decision'].get('cs_report', {}).get('cs_decision')}")
    results.append(res)

def sanitize(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, tuple):
        return [sanitize(v) for v in obj]
    return obj

with open("research/v54/losses/LOSS_STATE_COMPARISON.json", "w") as f:
    json.dump(sanitize(results), f, indent=2)

print("Saved LOSS_STATE_COMPARISON.json")
