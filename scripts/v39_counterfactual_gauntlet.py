"""
V39 Counterfactual Gauntlet & Rescue Simulation
Tests candidate interventions across:
- All 6 live losses
- All narrow wins (< $3k margin)
- Representative baseline wins
Measures:
- Loss rescue count & margin delta
- Casualty count (wins converted to losses)
- Paired cash delta
"""

import json
import os
import sys
import numpy as np
from kaggle_environments import make

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
LIVE_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live")
REPLAY_DIR = os.path.join(LIVE_DIR, "replays")
OUT_RESULTS = os.path.join(LIVE_DIR, "counterfactual_gauntlet_results.json")

# Load V35 reference
from candidates.v35_a7_opening.main import agent as v35_agent

def create_counterfactual_agent(arm="flush_693"):
    def cf_agent(obs, cfg=None):
        act = v35_agent(obs, cfg)
        step = int(obs.get("step", 0) or 0)
        
        # INTERVENTION: Early high-value perishable liquidation at step 693-694
        if arm in ("flush_693", "flush_combined") and step in (693, 694):
            shed = obs.get("private", {}).get("shed", {})
            mkt = act.setdefault("market", [])
            already = {o[1] for o in mkt if o[0] == "SELL"}
            for item in ("STRAWBERRY", "MILK", "WOOL"):
                qty = shed.get(item, 0)
                if qty > 0 and item not in already and len(mkt) < 10:
                    mkt.append(["SELL", item, qty])
                    
        return act
    return cf_agent

def run_matchup(eid, agent_to_test):
    path = os.path.join(REPLAY_DIR, f"episode-{eid}-replay.json")
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
        
    seed = data["info"]["seed"]
    steps = data["steps"]
    
    # Identify V35 seat from step 1
    act0 = steps[1][0].get("action", {}).get("market", [])
    v35_wash = [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
    
    if eid == 113153701:
        our_seat = 0
        opp_seat = 1
        opp_name = "Self-Play Validation"
    elif act0 == v35_wash:
        our_seat = 0
        opp_seat = 1
        opp_name = data["info"].get("TeamNames", ["", ""])[1]
    else:
        our_seat = 1
        opp_seat = 0
        opp_name = data["info"].get("TeamNames", ["", ""])[0]
        
    def opp_replay_agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        if step + 1 < len(steps):
            act = steps[step + 1][opp_seat].get("action")
            if act:
                return act
        return {"farmer": ["PASS"], "hands": [], "market": []}
        
    agents = [None, None]
    agents[our_seat] = agent_to_test
    agents[opp_seat] = opp_replay_agent
    
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.run(agents)
    
    r_our = env.state[our_seat].reward
    r_opp = env.state[opp_seat].reward
    margin = r_our - r_opp
    res = "WIN" if margin > 0 else ("LOSS" if margin < 0 else "TIE")
    
    return {
        "episode_id": eid,
        "seed": seed,
        "opp_name": opp_name,
        "our_seat": our_seat,
        "our_reward": r_our,
        "opp_reward": r_opp,
        "margin": margin,
        "result": res
    }

def run_gauntlet():
    with open(os.path.join(LIVE_DIR, "episodes.jsonl"), "r", encoding="utf-8") as f:
        all_episodes = [json.loads(line) for line in f if line.strip()]
        
    loss_eids = [e["episode_id"] for e in all_episodes if e["result"] == "LOSS"]
    narrow_win_eids = [e["episode_id"] for e in all_episodes if e["result"] == "WIN" and e["margin"] < 10000]
    
    print(f"Target Cohort: {len(loss_eids)} Losses, {len(narrow_win_eids)} Narrow Wins.")
    
    cf_agent = create_counterfactual_agent(arm="flush_693")
    
    results = []
    rescued_count = 0
    casualty_count = 0
    preserved_win_count = 0
    
    print("\n--- 1. LOSS RESCUE EVALUATION ---")
    for eid in loss_eids:
        # Get baseline live result
        base = next(e for e in all_episodes if e["episode_id"] == eid)
        base_margin = base["margin"]
        
        sim = run_matchup(eid, cf_agent)
        cf_margin = sim["margin"]
        delta = cf_margin - base_margin
        
        rescued = (base_margin < 0 and cf_margin > 0)
        improved = (cf_margin > base_margin)
        if rescued:
            rescued_count += 1
            status_str = ">>> RESCUED TO WIN! <<<"
        elif improved:
            status_str = f"Improved (+${delta:,.0f})"
        else:
            status_str = f"No change (${delta:,.0f})"
            
        print(f"Ep {eid} ({sim['opp_name']}): Base ${base_margin:,.0f} -> CF ${cf_margin:,.0f} (Delta {delta:+,.0f}) | {status_str}")
        sim["baseline_margin"] = base_margin
        sim["delta"] = delta
        sim["cohort"] = "LOSS"
        results.append(sim)
        
    print("\n--- 2. NARROW WIN CASUALTY EVALUATION ---")
    for eid in narrow_win_eids:
        base = next(e for e in all_episodes if e["episode_id"] == eid)
        base_margin = base["margin"]
        
        sim = run_matchup(eid, cf_agent)
        cf_margin = sim["margin"]
        delta = cf_margin - base_margin
        
        is_casualty = (base_margin > 0 and cf_margin < 0)
        if is_casualty:
            casualty_count += 1
            status_str = "!!! CASUALTY (WIN -> LOSS) !!!"
        else:
            preserved_win_count += 1
            status_str = f"PRESERVED ({sim['result']}, Delta {delta:+,.0f})"
            
        print(f"Ep {eid} ({sim['opp_name']}): Base +${base_margin:,.0f} -> CF +${cf_margin:,.0f} (Delta {delta:+,.0f}) | {status_str}")
        sim["baseline_margin"] = base_margin
        sim["delta"] = delta
        sim["cohort"] = "NARROW_WIN"
        results.append(sim)
        
    print("\n==========================================")
    print("GAUNTLET SUMMARY")
    print("==========================================")
    print(f"Target Losses Tested:      {len(loss_eids)}")
    print(f"Target Losses Rescued:     {rescued_count}")
    print(f"Wins Preserved:            {preserved_win_count} / {len(narrow_win_eids)}")
    print(f"Casualties (Wins->Losses): {casualty_count}")
    print(f"Mean Paired Cash Delta:    ${np.mean([r['delta'] for r in results]):+,.1f}")
    
    with open(OUT_RESULTS, "w", encoding="utf-8") as f:
        json.dump({
            "rescued_count": rescued_count,
            "casualty_count": casualty_count,
            "preserved_win_count": preserved_win_count,
            "results": results
        }, f, indent=2)

if __name__ == "__main__":
    run_gauntlet()
