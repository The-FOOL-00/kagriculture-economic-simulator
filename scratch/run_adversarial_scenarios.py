import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
from scratch.run_exact_loss_counterfactuals import evaluate_cowswap_gate

def make_synthetic_opponent(behavior: str):
    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0))
        seat = int(obs.get("player", 0))
        farm = obs["farms"][seat]
        shed = (obs.get("private") or {}).get("shed", {}) or {}
        money = float(farm.get("money", 0.0))
        mkt = []
        farmer_act = ["PASS"]
        
        if behavior == "A1_DAIRY_COMMITTER":
            # Aggressively buys cows / expands dairy
            milk = shed.get("MILK", 0)
            if milk > 0:
                mkt.append(["SELL", "MILK", milk])
            if money >= 400 and step < 400:
                mkt.append(["BUY_ANIMAL", "COW", 1])
                
        elif behavior == "A2_EGG_COMMITTER":
            # Avoids dairy, emphasizes geese / eggs
            eggs = shed.get("EGG", 0)
            if eggs > 0:
                mkt.append(["SELL", "EGG", eggs])
            if money >= 200 and step < 400:
                mkt.append(["BUY_ANIMAL", "GOOSE", 1])
                
        elif behavior == "A3_BALANCED":
            # Mixed strategy
            for prod in ["MILK", "WOOL", "EGG"]:
                q = shed.get(prod, 0)
                if q > 0:
                    mkt.append(["SELL", prod, q])
            if step % 50 == 0:
                if money >= 400:
                    mkt.append(["BUY_ANIMAL", "COW", 1])
                elif money >= 200:
                    mkt.append(["BUY_ANIMAL", "GOOSE", 1])
                    
        elif behavior == "A4_PRICE_DUMPER":
            # Aggressively sells milk immediately
            milk = shed.get("MILK", 0)
            if milk > 0:
                mkt.append(["SELL", "MILK", milk])
            if money >= 400 and step < 300:
                mkt.append(["BUY_ANIMAL", "COW", 1])
                
        elif behavior == "A5_PASSIVE":
            # Minimal market interaction
            pass
            
        return {"farmer": farmer_act, "hands": [], "market": mkt}
    return _agent

ADVERSARIES = [
    "A1_DAIRY_COMMITTER",
    "A2_EGG_COMMITTER",
    "A3_BALANCED",
    "A4_PRICE_DUMPER",
    "A5_PASSIVE"
]

TEST_SEEDS = [250600, 250601, 250602, 250603]

scenario_results = []

print("Running synthetic adversarial behavior scenarios...")
for adv_name in ADVERSARIES:
    adv_agent = make_synthetic_opponent(adv_name)
    for seed in TEST_SEEDS:
        for pol in ["C0", "C6"]:
            sim = FastKagricultureSim(seed=seed)
            obs = sim.reset()
            
            step_150_suppressed = False
            step_150_dairy_score = 0.0
            step_150_cows = 0
            
            for step in range(720):
                if step == 150:
                    suppress, score, details = evaluate_cowswap_gate(pol, obs[0], 0)
                    step_150_suppressed = suppress
                    step_150_dairy_score = score
                    step_150_cows = details.get("opp_cows", 0)
                    
                    if suppress:
                        v49_mod._CS_OPTIONS = ()
                    else:
                        v49_mod._CS_OPTIONS = ('GOOSE',)
                        
                a0 = v49_mod.agent(obs[0], sim.configuration)
                a1 = adv_agent(obs[1], sim.configuration)
                
                if step == 150:
                    v49_mod._CS_OPTIONS = ('GOOSE',)
                    
                obs, rewards, done, info = sim.step([a0, a1])
                if done:
                    break
                    
            v49_cash = float(obs[0]["farms"][0]["money"])
            opp_cash = float(obs[0]["farms"][1]["money"])
            margin = v49_cash - opp_cash
            
            rec = {
                "adversary": adv_name,
                "seed": seed,
                "policy": pol,
                "opp_cows_step150": step_150_cows,
                "dairy_score_step150": step_150_dairy_score,
                "step_150_suppressed": step_150_suppressed,
                "terminal_v49_cash": v49_cash,
                "terminal_opp_cash": opp_cash,
                "terminal_margin": margin,
                "won": margin > 0
            }
            scenario_results.append(rec)
            print(f"[{adv_name:<19}] Seed {seed} Pol {pol}: OppCows={step_150_cows} Suppress={step_150_suppressed} Margin=${margin:,.2f}")

os.makedirs("research/v54/adversarial", exist_ok=True)
with open("research/v54/adversarial/opponent_behavior_scenarios.json", "w") as f:
    json.dump(scenario_results, f, indent=2)

print("\nSaved opponent_behavior_scenarios.json")
