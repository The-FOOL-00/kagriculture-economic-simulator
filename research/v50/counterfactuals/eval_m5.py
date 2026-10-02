import concurrent.futures
import sys
import os
import json
import numpy as np

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
from research.v50.counterfactuals.test_exact_crop import make_exact_crop_agent
from research.v50.counterfactuals.run_exact_counterfactuals import compute_bootstrap_ci

def run_one_leg(args):
    s, seat = args
    opp_seat = 1 - seat
    opp = load_elite_agent("V44")
    exact_agent = make_exact_crop_agent(seed_thresh=624)

    # 1. V49
    sim49 = FastKagricultureSim(seed=s)
    obs49 = sim49.reset(seed=s)
    for _ in range(719):
        a49 = v49_mod.agent(obs49[seat])
        aopp = opp.act(obs49[opp_seat]) if hasattr(opp, "act") else opp(obs49[opp_seat])
        obs49, _, _, _ = sim49.step([a49, aopp] if seat == 0 else [aopp, a49])
    c49 = obs49[seat]["farms"][seat]["money"]
    copp49 = obs49[opp_seat]["farms"][opp_seat]["money"]
    w49 = c49 > copp49
    
    # 2. Exact Agent
    sim_ex = FastKagricultureSim(seed=s)
    obs_ex = sim_ex.reset(seed=s)
    for _ in range(719):
        a_ex = exact_agent(obs_ex[seat])
        aopp = opp.act(obs_ex[opp_seat]) if hasattr(opp, "act") else opp(obs_ex[opp_seat])
        obs_ex, _, _, _ = sim_ex.step([a_ex, aopp] if seat == 0 else [aopp, a_ex])
    c_ex = obs_ex[seat]["farms"][seat]["money"]
    copp_ex = obs_ex[opp_seat]["farms"][opp_seat]["money"]
    w_ex = c_ex > copp_ex
    
    delta = c_ex - c49
    rescue = not w49 and w_ex
    casualty = w49 and not w_ex
    return delta, w49, w_ex, rescue, casualty, s, seat, c49, c_ex

if __name__ == "__main__":
    seeds = [250400 + i for i in range(32)]
    tasks = [(s, seat) for s in seeds for seat in (0, 1)]

    print(f"Running M5 Per-Crop Exact Cap across {len(tasks)} legs in parallel...")
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_one_leg, tasks))

    deltas = np.array([r[0] for r in results], dtype=float)
    wins_49 = sum(r[1] for r in results)
    wins_ex = sum(r[2] for r in results)
    rescues = sum(r[3] for r in results)
    casualties = sum(r[4] for r in results)
    active = [d for d in deltas if d != 0.0]
    ci = compute_bootstrap_ci(deltas)

    for r in results:
        delta, w49, w_ex, rescue, casualty, s, seat, c49, c_ex = r
        if delta != 0.0:
            print(f"Seed {s} Seat {seat}: V49={c49:.0f}, Ex={c_ex:.0f}, Delta={delta:+.1f} (w49={w49}, wex={w_ex})")

    print("\n" + "=" * 50)
    print(f"M5_Per_Crop_Exact_Cap Evaluation (64 legs vs V44):")
    print(f"Mean Delta vs V49: {np.mean(deltas):+.2f} (95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}])")
    print(f"Active Legs: {len(active)} / {len(deltas)} ({len(active)/len(deltas)*100:.1f}%)")
    print(f"Active Mean: {np.mean(active) if active else 0.0:+.2f}")
    print(f"Rescues: {rescues}, Casualties: {casualties}")
    print(f"V49 Win Rate: {wins_49/len(deltas)*100:.2f}%, Exact Win Rate: {wins_ex/len(deltas)*100:.2f}%")
    print(f"Min Delta: {np.min(deltas):+.2f}, Max Delta: {np.max(deltas):+.2f}")
