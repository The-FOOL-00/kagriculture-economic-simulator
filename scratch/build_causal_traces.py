import sys, os
sys.path.insert(0, '.')
import json
import copy

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

from scratch.run_full_counterfactual_matrix import build_transformation_suite

suite = build_transformation_suite()
selected_interventions = [
    "Q0_baseline",
    "Q6_step697_wool_first",
    "Q6_step697_carrot_wool_egg_milk",
    "Q1_step697_lead_pad1",
    "Q4_step697_split_carrot",
    "Q6_step694_wool_first",
    "Q1_step694_lead_pad1",
    "Q6_step693_egg_milk_first",
    "Q6_step718_wool_egg_wheat",
]

causal_traces = {}

for name in selected_interventions:
    fn = suite[name]["fn"]
    causal_traces[name] = {"description": suite[name]["description"], "seeds": {}}
    
    for seed in [250621, 250617]:
        sim = FastKagricultureSim(seed=seed)
        obs = sim.reset(seed=seed)
        step_diffs = []
        
        for step in range(719):
            c49_pre = float(obs[0]["farms"][0]["money"])
            c44_pre = float(obs[1]["farms"][1]["money"])
            
            a49 = v49_mod.agent(obs[0])
            a44 = v44_mod.agent(obs[1])
            
            if isinstance(a49, dict) and "market" in a49:
                new_m = fn(step, a49["market"])
                if new_m is not None:
                    a49 = copy.deepcopy(a49)
                    a49["market"] = new_m
                    
            obs, _, done, _ = sim.step([a49, a44])
            c49_post = float(obs[0]["farms"][0]["money"])
            c44_post = float(obs[1]["farms"][1]["money"])
            
            if step in range(690, 700) or step in (717, 718):
                step_diffs.append({
                    "step": step,
                    "c49_post": c49_post,
                    "c44_post": c44_post,
                    "margin": c49_post - c44_post,
                    "shed_49": dict(sim.state[0].observation.private["shed"]),
                    "shed_44": dict(sim.state[1].observation.private["shed"]),
                    "market_inv": {k: obs[0]["market"]["inventory"].get(k) for k in ("CARROT", "WOOL", "EGG", "MILK")}
                })
            if done: break
            
        causal_traces[name]["seeds"][str(seed)] = {
            "final_cash_49": c49_post,
            "final_cash_44": c44_post,
            "final_margin": c49_post - c44_post,
            "step_diffs": step_diffs
        }

with open("research/v57/counterfactuals/CAUSAL_QUEUE_TRACES.json", "w") as f:
    json.dump(causal_traces, f, indent=2)

print("Saved research/v57/counterfactuals/CAUSAL_QUEUE_TRACES.json")
