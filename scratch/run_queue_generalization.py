import sys, os
sys.path.insert(0, '.')
import copy
import json

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod

from scratch.run_full_counterfactual_matrix import build_transformation_suite
from research.v55.benchmarks.run_v55_fresh_ladder import make_adversary

suite = build_transformation_suite()

# Established Opponents set (Section 10 requirement):
# 1. V44
# 2. V48
# 3. V49 self
# 4. dmitrii_lb2800
# 5. tetsutani_pasture
# 6. kaitofukami_v48_3009
# 7. indarkarhana_top10
# 8. saiteja_mega_3000
# 9. DAIRY_FLOOD
# 10. WOOL_FLOOD

OPPONENT_LOADERS = {
    "V44": load_elite_agent("V44"),
    "V48": v48_mod.agent,
    "V49_self": v49_mod.agent,
    "dmitrii_lb2800": load_elite_agent("dmitrii_lb2800"),
    "tetsutani_pasture": load_elite_agent("tetsutani_pasture"),
    "kaitofukami_v48_3009": load_elite_agent("kaitofukami_v48_3009"),
    "indarkarhana_top10": load_elite_agent("indarkarhana_top10"),
    "saiteja_mega_3000": load_elite_agent("saiteja_mega_3000"),
    "DAIRY_FLOOD": make_adversary("DAIRY_FLOOD"),
    "WOOL_FLOOD": make_adversary("WOOL_FLOOD"),
}

SAMPLE_SEEDS = [250600, 250616, 250617, 250621]

CANDIDATES_TO_AUDIT = [
    "Q0_baseline",
    "Q6_step697_wool_first",
    "Q6_step697_carrot_wool_egg_milk",
    "Q1_step697_lead_pad1",
    "Q6_step694_wool_first",
    "Q6_step693_egg_milk_first",
]

def run_generalization_matrix():
    print(f"Running generalization matrix across {len(OPPONENT_LOADERS)} opponents...")
    matrix_results = {}
    
    for opp_name, opp_agent in OPPONENT_LOADERS.items():
        matrix_results[opp_name] = {}
        for cand_name in CANDIDATES_TO_AUDIT:
            fn = suite[cand_name]["fn"]
            deltas = []
            cand_wins = 0
            base_wins = 0
            total_matches = 0
            
            for seed in SAMPLE_SEEDS:
                for seat in [0, 1]:
                    opp_seat = 1 - seat
                    sim = FastKagricultureSim(seed=seed)
                    obs = sim.reset(seed=seed)
                    
                    # 1. Run baseline
                    for step in range(719):
                        a49 = v49_mod.agent(obs[seat])
                        aopp = opp_agent(obs[opp_seat])
                        obs, _, done, _ = sim.step([a49, aopp] if seat == 0 else [aopp, a49])
                        if done: break
                    base_c49 = float(obs[seat]["farms"][seat]["money"])
                    base_copp = float(obs[opp_seat]["farms"][opp_seat]["money"])
                    base_marg = base_c49 - base_copp
                    if base_marg > 0: base_wins += 1
                    
                    # 2. Run candidate
                    sim = FastKagricultureSim(seed=seed)
                    obs = sim.reset(seed=seed)
                    for step in range(719):
                        a49 = v49_mod.agent(obs[seat])
                        aopp = opp_agent(obs[opp_seat])
                        if isinstance(a49, dict) and "market" in a49:
                            new_m = fn(step, a49["market"])
                            if new_m is not None:
                                a49 = copy.deepcopy(a49)
                                a49["market"] = new_m
                        obs, _, done, _ = sim.step([a49, aopp] if seat == 0 else [aopp, a49])
                        if done: break
                    cand_c49 = float(obs[seat]["farms"][seat]["money"])
                    cand_copp = float(obs[opp_seat]["farms"][opp_seat]["money"])
                    cand_marg = cand_c49 - cand_copp
                    if cand_marg > 0: cand_wins += 1
                    
                    delta = cand_marg - base_marg
                    deltas.append(delta)
                    total_matches += 1
                    
            mean_delta = sum(deltas) / len(deltas)
            matrix_results[opp_name][cand_name] = {
                "matches": total_matches,
                "base_wins": base_wins,
                "cand_wins": cand_wins,
                "mean_delta": mean_delta
            }
            if cand_name != "Q0_baseline" and mean_delta != 0.0:
                print(f"  Opp={opp_name:22s} | Cand={cand_name:30s} | MeanDelta={mean_delta:>+7.1f} | Wins: {base_wins}->{cand_wins}/{total_matches}")
                
    os.makedirs("research/v57/analysis", exist_ok=True)
    with open("research/v57/analysis/QUEUE_GENERALIZATION.json", "w") as f:
        json.dump(matrix_results, f, indent=2)
    print("Saved research/v57/analysis/QUEUE_GENERALIZATION.json")

if __name__ == "__main__":
    run_generalization_matrix()
