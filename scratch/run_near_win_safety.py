import sys, os
sys.path.insert(0, '.')
import copy
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

from scratch.run_full_counterfactual_matrix import build_transformation_suite

suite = build_transformation_suite()

# Candidate interventions to test for safety
CANDIDATES = [
    "Q6_step697_wool_first",
    "Q6_step697_carrot_wool_egg_milk",
    "Q1_step697_lead_pad1",
    "Q4_step697_split_carrot",
    "Q6_step693_egg_milk_first",
    "Q6_step694_wool_first",
    "Q1_step694_lead_pad1",
    "Q6_step718_wool_egg_wheat",
]

# Evaluation seeds
LOSS_SEEDS = [250617, 250621]
NEAR_WIN_SEEDS = [250631, 250616, 250604, 250627]
COMFORTABLE_SEEDS = [250618, 250620, 250622, 250600]

ALL_SAFETY_SEEDS = LOSS_SEEDS + NEAR_WIN_SEEDS + COMFORTABLE_SEEDS

def run_safety_audit():
    # 1. Establish baseline margins for all seeds
    baselines = {}
    for seed in ALL_SAFETY_SEEDS:
        for seat in [0, 1]:
            opp_seat = 1 - seat
            leg_key = f"seed_{seed}_seat_{seat}"
            sim = FastKagricultureSim(seed=seed)
            obs = sim.reset(seed=seed)
            for step in range(719):
                a49 = v49_mod.agent(obs[seat])
                a44 = v44_mod.agent(obs[opp_seat])
                obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
                if done: break
            c49 = float(obs[seat]["farms"][seat]["money"])
            c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
            baselines[leg_key] = {"c49": c49, "c44": c44, "margin": c49 - c44, "win": c49 > c44}
            
    print("Baseline computed across 20 legs.")
    
    safety_results = {}
    
    for cand_name in CANDIDATES:
        fn = suite[cand_name]["fn"]
        cand_res = {}
        rescues = 0
        casualties = 0
        near_win_deltas = []
        
        for seed in ALL_SAFETY_SEEDS:
            seed_type = "LOSS" if seed in LOSS_SEEDS else ("NEAR_WIN" if seed in NEAR_WIN_SEEDS else "COMFORTABLE_WIN")
            for seat in [0, 1]:
                opp_seat = 1 - seat
                leg_key = f"seed_{seed}_seat_{seat}"
                sim = FastKagricultureSim(seed=seed)
                obs = sim.reset(seed=seed)
                
                for step in range(719):
                    a49 = v49_mod.agent(obs[seat])
                    a44 = v44_mod.agent(obs[opp_seat])
                    
                    if isinstance(a49, dict) and "market" in a49:
                        new_m = fn(step, a49["market"])
                        if new_m is not None:
                            a49 = copy.deepcopy(a49)
                            a49["market"] = new_m
                            
                    obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
                    if done: break
                    
                c49 = float(obs[seat]["farms"][seat]["money"])
                c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
                marg = c49 - c44
                base_win = baselines[leg_key]["win"]
                cand_win = c49 > c44
                delta = marg - baselines[leg_key]["margin"]
                
                if seed in NEAR_WIN_SEEDS:
                    near_win_deltas.append(delta)
                    
                if not base_win and cand_win:
                    rescues += 1
                elif base_win and not cand_win:
                    casualties += 1
                    
                cand_res[leg_key] = {
                    "seed": seed,
                    "seat": seat,
                    "seed_type": seed_type,
                    "baseline_margin": baselines[leg_key]["margin"],
                    "candidate_margin": marg,
                    "delta": delta,
                    "baseline_win": base_win,
                    "candidate_win": cand_win
                }
                
        safety_results[cand_name] = {
            "description": suite[cand_name]["description"],
            "rescues": rescues,
            "casualties": casualties,
            "mean_near_win_delta": sum(near_win_deltas) / len(near_win_deltas) if near_win_deltas else 0.0,
            "legs": cand_res
        }
        print(f"[{cand_name:32s}] Rescues={rescues} | Casualties={casualties} | NearWinDelta={safety_results[cand_name]['mean_near_win_delta']:>+7.1f}")
        
    os.makedirs("research/v57/analysis", exist_ok=True)
    with open("research/v57/analysis/NEAR_WIN_SAFETY.json", "w") as f:
        json.dump(safety_results, f, indent=2)
    print("Saved research/v57/analysis/NEAR_WIN_SAFETY.json")

if __name__ == "__main__":
    run_safety_audit()
