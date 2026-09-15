import os
import sys
import json
import importlib.util

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
spec = importlib.util.spec_from_file_location("baseline_mod", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)


def summarize_farm_tiles(tiles_2d):
    counts = {}
    for row in tiles_2d:
        for t in row:
            if not t:
                continue
            if isinstance(t, str):
                counts[f"terrain_{t}"] = counts.get(f"terrain_{t}", 0) + 1
                continue
            crop = t.get("crop")
            animal = t.get("animal")
            building = t.get("building")
            if crop:
                c_name = crop if isinstance(crop, str) else crop.get("type", "UNKNOWN_CROP")
                counts[f"crop_{c_name}"] = counts.get(f"crop_{c_name}", 0) + 1
            if animal:
                a_name = animal if isinstance(animal, str) else animal.get("type", "UNKNOWN_ANIMAL")
                counts[f"animal_{a_name}"] = counts.get(f"animal_{a_name}", 0) + 1
            if building:
                b_name = building if isinstance(building, str) else building.get("type", "UNKNOWN_BUILDING")
                counts[f"building_{b_name}"] = counts.get(f"building_{b_name}", 0) + 1
    return counts


def trace_seed_detailed(seed: int):
    print(f"\n=======================================================")
    print(f"DETAILED FORENSIC TRACE FOR SEED {seed}")
    print(f"=======================================================")

    g = kagsim.Game(seed)
    cand = Dev005ConfirmedShopScheduler(seat=0, seed=seed)
    base = base_mod

    step = 0
    divergence_step = None
    divergence_details = None

    cand_market_acts = []
    base_market_acts = []

    # Inventory / asset tracking over time
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)

        f0_cand = o0["farms"][0]
        f1_base = o0["farms"][1]

        m_diff = f0_cand["money"] - f1_base["money"]
        if divergence_step is None and abs(m_diff) > 1e-4:
            divergence_step = step
            divergence_details = f"Step {step}: Money diff cand={f0_cand['money']} vs base={f1_base['money']} (delta={m_diff})"

        a0 = cand.act(o0)
        a1 = base.agent(o1)

        if divergence_step is None and a0 != a1:
            divergence_step = step
            divergence_details = f"Step {step}: First action divergence: cand={a0} vs base={a1}"

        if a0.get("market"):
            cand_market_acts.append((step, a0["market"]))
        if a1.get("market"):
            base_market_acts.append((step, a1["market"]))

        g.step(a0, a1)
        step += 1

    cand_rew = g.reward(0)
    base_rew = g.reward(1)
    delta = cand_rew - base_rew

    print(f"Final Outcome: Cand Cash = {cand_rew}, Base Cash = {base_rew}, Delta = {delta}")
    print(f"First Divergence: {divergence_details}")

    print("\nCandidate Decision Events:")
    for ev in cand.decision_events:
        print(f"  Step {ev['step']}: decision={ev['decision']}, shops={ev['current_shops']}, best_plan={ev['best_candidate_plan']}, exp_val={ev['expected_incremental_value']}, liq={ev['liquidity']}")

    # Let's inspect differences in market actions post Step 288
    cand_post288_m = [x for x in cand_market_acts if x[0] >= 288]
    base_post288_m = [x for x in base_market_acts if x[0] >= 288]

    print(f"\nTotal Market Action Steps post 288: Cand={len(cand_post288_m)}, Base={len(base_post288_m)}")
    
    # Categorize all purchases and sales post 288
    def categorize_market_acts(m_acts):
        buys = {}
        sells = {}
        for s, acts in m_acts:
            for act in acts:
                if not act:
                    continue
                cmd = act[0]
                if cmd in ("BUY_SEED", "BUY_ANIMAL"):
                    item = act[1]
                    qty = act[2] if len(act) > 2 else 1
                    buys[item] = buys.get(item, 0) + qty
                elif cmd in ("SELL", "SELL_ANIMAL", "SELL_PRODUCE"):
                    item = act[1]
                    qty = act[2] if len(act) > 2 else 1
                    sells[item] = sells.get(item, 0) + qty
                elif cmd == "HIRE":
                    buys["HIRE"] = buys.get("HIRE", 0) + 1
        return buys, sells

    cand_buys, cand_sells = categorize_market_acts(cand_post288_m)
    base_buys, base_sells = categorize_market_acts(base_post288_m)

    print(f"\nPost-288 Purchases:")
    print(f"  Candidate: {cand_buys}")
    print(f"  Baseline:  {base_buys}")

    print(f"\nPost-288 Sales:")
    print(f"  Candidate: {cand_sells}")
    print(f"  Baseline:  {base_sells}")

    o_end = g.observe(0)
    farm0 = o_end["farms"][0]
    farm1 = o_end["farms"][1]

    print("\nTerminal State Comparison:")
    print(f"Cand Farm: Money = {farm0['money']}, Hands = {len(farm0['hands'])}, Unlocked Quadrants = {farm0['unlocked_quadrants']}")
    print(f"Base Farm: Money = {farm1['money']}, Hands = {len(farm1['hands'])}, Unlocked Quadrants = {farm1['unlocked_quadrants']}")

    cand_tiles_summary = summarize_farm_tiles(farm0['tiles'])
    base_tiles_summary = summarize_farm_tiles(farm1['tiles'])

    print(f"\nCand Tiles Summary: {cand_tiles_summary}")
    print(f"Base Tiles Summary: {base_tiles_summary}")


if __name__ == "__main__":
    for s in (247025, 247034):
        trace_seed_detailed(s)
