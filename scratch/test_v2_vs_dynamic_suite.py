import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent

# Import key opponents
import opponents.live_flooder_v1 as flooder
import opponents.adversarial_champion_killer as ack
import opponents.o9_market_aggressor as mkt_agg
import opponents.o10_anti_melon as anti_melon
import opponents.o12_top_meta as top_meta
import opponents.o3_melon_specialist as melon_spec
import opponents.o4_fast_crop as fast_crop
import opponents.replay_whyme_labs as whyme
import opponents.replay_crop_dusta as crop_dusta

OPPONENTS = [
    ("Live Flooder", flooder.agent),
    ("Adversarial Champion Killer", ack.agent),
    ("Market Aggressor", mkt_agg.agent),
    ("Anti-Melon", anti_melon.agent),
    ("Top Meta Adaptive", top_meta.agent),
    ("Melon Specialist", melon_spec.agent),
    ("Fast Crop", fast_crop.agent),
    ("Replay Whyme Labs", whyme.agent),
    ("Replay Crop Dusta", crop_dusta.agent),
]

SEEDS = [42, 100, 2024, 104816794, 104817623]

def run_suite_eval():
    print("="*90)
    print("PHASE 10 & 11: DYNAMIC & ADVERSARIAL OPPONENT SUITE BENCHMARK")
    print("="*90)
    
    candidates = [
        ("Frozen V2", v2_mod.agent),
        ("CL-Aethel Prime", prime_agent),
        ("CL-Aethel Grandmaster", gm_agent),
    ]
    
    results = {}
    
    for c_name, c_agent in candidates:
        print(f"\nEvaluating Candidate: {c_name}...")
        c_results = {}
        all_margins = []
        all_wins = 0
        all_losses = 0
        all_ties = 0
        all_cand_scores = []
        all_opp_scores = []
        
        for opp_name, opp_agent in OPPONENTS:
            opp_margins = []
            opp_scores_cand = []
            opp_scores_opp = []
            wins = 0
            losses = 0
            ties = 0
            
            for s in SEEDS:
                # Play Seat 0
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
                env.run([c_agent, opp_agent])
                r0 = env.steps[-1][0]["reward"]
                r1 = env.steps[-1][1]["reward"]
                m = r0 - r1
                opp_margins.append(m)
                opp_scores_cand.append(r0)
                opp_scores_opp.append(r1)
                if m > 0: wins += 1; all_wins += 1
                elif m < 0: losses += 1; all_losses += 1
                else: ties += 1; all_ties += 1
                
                # Play Seat 1 (Seat Invariance Test)
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
                env.run([opp_agent, c_agent])
                r0 = env.steps[-1][0]["reward"]
                r1 = env.steps[-1][1]["reward"]
                m = r1 - r0
                opp_margins.append(m)
                opp_scores_cand.append(r1)
                opp_scores_opp.append(r0)
                if m > 0: wins += 1; all_wins += 1
                elif m < 0: losses += 1; all_losses += 1
                else: ties += 1; all_ties += 1
                
            all_margins.extend(opp_margins)
            all_cand_scores.extend(opp_scores_cand)
            all_opp_scores.extend(opp_scores_opp)
            
            win_rate = wins / len(opp_margins)
            mean_m = float(np.mean(opp_margins))
            mean_c = float(np.mean(opp_scores_cand))
            mean_o = float(np.mean(opp_scores_opp))
            c_results[opp_name] = {
                "W-L-T": f"{wins}-{losses}-{ties}",
                "win_rate": win_rate,
                "mean_cand_score": mean_c,
                "mean_opp_score": mean_o,
                "mean_margin": mean_m
            }
            print(f"  vs {opp_name:<30}: W-L-T={wins:>2}-{losses:>2}-{ties} ({win_rate:>5.1%}) | Cand=${mean_c:>9,.0f} | Opp=${mean_o:>9,.0f} | Margin=${mean_m:>+10,.0f}")
            
        overall_wr = all_wins / len(all_margins)
        overall_cand = float(np.mean(all_cand_scores))
        overall_margin = float(np.mean(all_margins))
        results[c_name] = {
            "overall_W-L-T": f"{all_wins}-{all_losses}-{all_ties}",
            "overall_win_rate": overall_wr,
            "overall_cand_score": overall_cand,
            "overall_margin": overall_margin,
            "per_opponent": c_results
        }
        print(f"==> {c_name} Overall: {all_wins}-{all_losses}-{all_ties} ({overall_wr:.1%}) | Mean Score=${overall_cand:,.0f} | Margin=${overall_margin:>+10,.0f}")

    import json
    with open("scratch/dynamic_opponent_suite_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved full dynamic suite results to scratch/dynamic_opponent_suite_results.json")

if __name__ == '__main__':
    run_suite_eval()
