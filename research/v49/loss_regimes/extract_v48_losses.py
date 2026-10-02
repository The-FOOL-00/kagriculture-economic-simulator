#!/usr/bin/env python3
"""Parallel extraction of all V48 losses against V44 and Tetsutani."""

import os
import sys
import json
import concurrent.futures

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v48_challenger.main as v48_mod
import candidates.v44_economic_portfolio.main as v44_mod
import research.v47.elite_corpus.agents.tetsutani_pasture.main as tet_mod

SEEDS = [249800 + i for i in range(128)]

def sim_match(args):
    opp_name, seed, seat = args
    opp_agent = v44_mod.agent if opp_name == "V44" else tet_mod.agent
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    for _ in range(719):
        a_v48 = v48_mod.agent(obs[seat])
        a_opp = opp_agent(obs[opp_seat])
        actions = [a_v48, a_opp] if seat == 0 else [a_opp, a_v48]
        obs, _, _, _ = sim.step(actions)
    cash_v48 = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    if cash_v48 < cash_opp:
        shops = obs[seat].get("town", {}).get("unlocked_shops", [])
        return {
            "opp": opp_name,
            "seed": seed,
            "seat": seat,
            "cash_v48": cash_v48,
            "cash_opp": cash_opp,
            "margin": cash_v48 - cash_opp,
            "shops": shops,
        }
    return None

def main():
    tasks = []
    for opp_name in ("V44", "Tetsutani"):
        for seed in SEEDS:
            for seat in (0, 1):
                tasks.append((opp_name, seed, seat))

    print(f"Running {len(tasks)} matches in parallel on 8 cores...")
    losses = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(sim_match, tasks):
            if res is not None:
                losses.append(res)
                print(f"  LOSS: opp={res['opp']}, seed={res['seed']}, seat={res['seat']}, margin={res['margin']:.1f}, shops={res['shops']}")

    out_file = os.path.join(REPO_ROOT, "research", "v49", "loss_regimes", "v48_loss_corpus.json")
    with open(out_file, "w") as f:
        json.dump(losses, f, indent=2)
    print(f"\nTotal losses found: {len(losses)}. Saved to {out_file}")

if __name__ == "__main__":
    main()
