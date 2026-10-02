#!/usr/bin/env python3
"""Build the complete V49 Loss Corpus and First-Divergence Forensics.

For every outright loss of V49 in the 1,536-leg elite benchmark:
1. Replay full step-by-step match of:
   - V49 vs Opponent
   - V48 vs Opponent
   - Raw 2945 vs Opponent
2. Capture complete observable game state at the critical transition and divergence points.
3. Compare action tapes of V49, V48, 2945, and Opponent.
4. Classify each loss into causal regimes based on physical state and action consequences.
5. Generate:
   - research/v50/loss_regimes/v49_loss_corpus.json
   - research/v50/loss_regimes/v49_loss_regimes.md
   - research/v50/loss_regimes/V49_LOSS_CAUSAL_TABLE.md
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v48_challenger.main as v48_mod
import candidates.v49_meta_fusion.main as v49_mod
import research.v47.elite_corpus.agents.thomastschinkel_2945.main as m2945


def run_full_forensic_replay(seed: int, seat: int, opp_name: str) -> Dict[str, Any]:
    opp_seat = 1 - seat

    # 1. Run V49 game with full step telemetry
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    opp49 = load_elite_agent(opp_name)
    agent_v49 = v49_mod.agent
    agent_v48 = v48_mod.agent
    agent_2945 = m2945.make_agent(m2945._ROUTES, router=m2945._router, **m2945._SETTINGS)

    v49_timeline = []
    first_behind_step = None

    for step in range(719):
        # Record state snapshot before step
        my_farm = obs49[seat]["farms"][seat]
        opp_farm = obs49[opp_seat]["farms"][opp_seat]
        my_cash = float(my_farm["money"])
        opp_cash = float(opp_farm["money"])

        if my_cash < opp_cash and first_behind_step is None:
            first_behind_step = step

        a_v49 = agent_v49(obs49[seat])
        a_opp49 = opp49.act(obs49[opp_seat]) if hasattr(opp49, "act") else opp49(obs49[opp_seat])

        # Sample snapshots every 24 steps (daily) or post step 500 every step
        if step % 24 == 0 or step >= 500 or (first_behind_step is not None and step <= first_behind_step + 5):
            v49_timeline.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "cash": my_cash,
                "opp_cash": opp_cash,
                "cash_diff": my_cash - opp_cash,
                "action": a_v49,
                "opp_action": a_opp49,
                "hands_count": len(my_farm.get("hands", [])),
                "unlocked_shops": list(obs49[seat].get("town", {}).get("unlocked_shops", [])),
                "inventory": dict(my_farm.get("inventory", {})),
                "seeds": dict(obs49[seat].get("private", {}).get("seeds", {})),
                "market_prices": {p: obs49[seat].get("market", {}).get("prices", {}).get(p) for p in ["WHEAT", "CARROT", "MILK", "WOOL", "EGG", "FERTILIZER"] if p in obs49[seat].get("market", {}).get("prices", {})},
            })

        actions = [a_v49, a_opp49] if seat == 0 else [a_opp49, a_v49]
        obs49, _, _, _ = sim49.step(actions)

    final_cash_v49 = float(obs49[seat]["farms"][seat]["money"])
    final_cash_opp49 = float(obs49[opp_seat]["farms"][opp_seat]["money"])
    final_margin_v49 = final_cash_v49 - final_cash_opp49

    # 2. Run V48 game
    sim48 = FastKagricultureSim(seed=seed)
    obs48 = sim48.reset(seed=seed)
    opp48 = load_elite_agent(opp_name)
    v48_actions = []

    for step in range(719):
        a_v48 = agent_v48(obs48[seat])
        a_opp48 = opp48.act(obs48[opp_seat]) if hasattr(opp48, "act") else opp48(obs48[opp_seat])
        if step >= 500:
            v48_actions.append(a_v48)
        actions = [a_v48, a_opp48] if seat == 0 else [a_opp48, a_v48]
        obs48, _, _, _ = sim48.step(actions)

    final_cash_v48 = float(obs48[seat]["farms"][seat]["money"])
    final_cash_opp48 = float(obs48[opp_seat]["farms"][opp_seat]["money"])

    # 3. Run Raw 2945 game
    sim2945 = FastKagricultureSim(seed=seed)
    obs2945 = sim2945.reset(seed=seed)
    opp2945 = load_elite_agent(opp_name)
    raw_actions = []

    for step in range(719):
        a_2945 = agent_2945(obs2945[seat])
        a_opp2945 = opp2945.act(obs2945[opp_seat]) if hasattr(opp2945, "act") else opp2945(obs2945[opp_seat])
        if step >= 500:
            raw_actions.append(a_2945)
        actions = [a_2945, a_opp2945] if seat == 0 else [a_opp2945, a_2945]
        obs2945, _, _, _ = sim2945.step(actions)

    final_cash_2945 = float(obs2945[seat]["farms"][seat]["money"])
    final_cash_opp2945 = float(obs2945[opp_seat]["farms"][opp_seat]["money"])

    # Extract final town shops
    final_shops = list(obs49[seat].get("town", {}).get("unlocked_shops", []))
    final_inventory = dict(obs49[seat]["farms"][seat].get("inventory", {}))
    final_seeds = dict(obs49[seat].get("private", {}).get("seeds", {}))

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "final_cash_v49": final_cash_v49,
        "final_cash_opp": final_cash_opp49,
        "final_margin": final_margin_v49,
        "final_cash_v48": final_cash_v48,
        "final_cash_2945": final_cash_2945,
        "first_behind_step": first_behind_step,
        "shops": final_shops,
        "final_inventory": final_inventory,
        "final_seeds": final_seeds,
        "v49_timeline_samples": v49_timeline,
    }


def main():
    raw_path = os.path.join(REPO_ROOT, "research", "v50", "audit", "v49_audit_raw_legs.json")
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} does not exist yet. Run audit first.")
        return

    with open(raw_path, "r") as f:
        all_legs = json.load(f)

    losses = [l for l in all_legs if l["loss_v49"]]
    print(f"Loaded {len(all_legs)} legs. Found {len(losses)} outright V49 losses.")

    forensics_list = []
    for idx, loss_leg in enumerate(losses):
        seed = loss_leg["seed"]
        seat = loss_leg["seat"]
        opp = loss_leg["opp"]
        print(f"Analyzing loss {idx+1}/{len(losses)}: seed={seed}, seat={seat}, opp={opp}...")
        f_res = run_full_forensic_replay(seed, seat, opp)
        forensics_list.append(f_res)
        print(f"  Result: V49=${f_res['final_cash_v49']:.0f}, Opp=${f_res['final_cash_opp']:.0f} (Margin: {f_res['final_margin']:+.0f}), V48=${f_res['final_cash_v48']:.0f}, 2945=${f_res['final_cash_2945']:.0f}")
        print(f"  First behind step: {f_res['first_behind_step']}, Shops: {f_res['shops']}")

    # Save detailed loss corpus json
    out_json = os.path.join(REPO_ROOT, "research", "v50", "loss_regimes", "v49_loss_corpus.json")
    with open(out_json, "w") as f:
        json.dump(forensics_list, f, indent=2)
    print(f"\nSaved detailed loss forensics to {out_json}")


if __name__ == "__main__":
    main()
