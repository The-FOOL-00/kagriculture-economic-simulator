import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

SEEDS = list(range(1000, 1010))

def audit_actions_and_decay():
    print("================================================================================")
    print("AUDITING ACTION CONVERSION, V2 FERTILIZER USAGE, AND CL DECAY EVENTS")
    print("================================================================================")
    
    # 1. Action conversion audit (Baseline vs Gated)
    # Action categories: FERTILIZE, HARVEST_STRAWBERRY, HARVEST_OTHER, WATER, CARE, FEED, DROP, PASS, MOVE
    actions_base = {cat: 0 for cat in ["FERTILIZE", "HARVEST_STRAW", "HARVEST_OTHER", "WATER", "CARE", "FEED", "COLLECT_FERT", "DROP", "MOVE", "PASS"]}
    actions_gated = {cat: 0 for cat in actions_base}
    
    # Decay tracking for CL
    decay_events_cl = []
    
    # V2 fertilizer tracking: list of (seed, step, day, pos, crop, age, was_useful)
    v2_fert_actions = []
    
    for seed in SEEDS:
        print(f"--- Running Seed {seed} ---")
        # Run Baseline
        env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_b = env_b.run([cl_baseline, "starter"])
        
        for s_idx in range(1, len(steps_b)):
            prev_obs = steps_b[s_idx-1][0]["observation"]
            curr_obs = steps_b[s_idx][0]["observation"]
            act = steps_b[s_idx-1][0].get("action") or {}
            all_wacts = [act.get("farmer", [])] + act.get("hands", [])
            all_wpos = [prev_obs["farms"][0]["farmer"]] + prev_obs["farms"][0]["hands"]
            
            for wpos, wact in zip(all_wpos, all_wacts):
                if not wact: continue
                c = wact[0]
                if c == "FERTILIZE": actions_base["FERTILIZE"] += 1
                elif c == "WATER": actions_base["WATER"] += 1
                elif c == "CARE": actions_base["CARE"] += 1
                elif c == "FEED": actions_base["FEED"] += 1
                elif c == "COLLECT_FERTILIZER": actions_base["COLLECT_FERT"] += 1
                elif c == "DROP": actions_base["DROP"] += 1
                elif c == "PASS": actions_base["PASS"] += 1
                elif c in ("NORTH", "SOUTH", "EAST", "WEST"): actions_base["MOVE"] += 1
                elif c == "HARVEST":
                    x, y = wpos
                    tile = prev_obs["farms"][0]["tiles"][y][x]
                    if isinstance(tile, dict) and tile.get("crop") == "STRAWBERRY":
                        actions_base["HARVEST_STRAW"] += 1
                    else:
                        actions_base["HARVEST_OTHER"] += 1
                        
            # Track decay in CL: check strawberry bushes
            prev_tiles = prev_obs["farms"][0]["tiles"]
            curr_tiles = curr_obs["farms"][0]["tiles"]
            for r in range(len(prev_tiles)):
                for col in range(len(prev_tiles[r])):
                    pt = prev_tiles[r][col]
                    ct = curr_tiles[r][col]
                    if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                        # Check decay: in engine, strawberry ongoing bushes don't decay by _decay_plants
                        # WAIT! Does strawberry decay in engine?
                        # Let's check: max_lifespan_step = -1 for ongoing!
                        # But wait, did mature strawberry decay into weed or did yield drop?
                        # Let's check if yield decreased without harvest!
                        py = int(pt.get("yield_units", 0) or 0)
                        cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) else 0
                        
                        # Was there a harvest on this tile?
                        harvested = False
                        for wpos, wact in zip(all_wpos, all_wacts):
                            if tuple(wpos) == (col, r) and wact and wact[0] == "HARVEST":
                                harvested = True
                                break
                        if not harvested and cy < py:
                            decay_events_cl.append({
                                "seed": seed, "step": s_idx, "pos": (col, r), "py": py, "cy": cy,
                                "kind": ct.get("kind") if isinstance(ct, dict) else ct
                            })

        # Run Gated
        env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_g = env_g.run([cl_gated, "starter"])
        for s_idx in range(1, len(steps_g)):
            prev_obs = steps_g[s_idx-1][0]["observation"]
            act = steps_g[s_idx-1][0].get("action") or {}
            all_wacts = [act.get("farmer", [])] + act.get("hands", [])
            all_wpos = [prev_obs["farms"][0]["farmer"]] + prev_obs["farms"][0]["hands"]
            for wpos, wact in zip(all_wpos, all_wacts):
                if not wact: continue
                c = wact[0]
                if c == "FERTILIZE": actions_gated["FERTILIZE"] += 1
                elif c == "WATER": actions_gated["WATER"] += 1
                elif c == "CARE": actions_gated["CARE"] += 1
                elif c == "FEED": actions_gated["FEED"] += 1
                elif c == "COLLECT_FERTILIZER": actions_gated["COLLECT_FERT"] += 1
                elif c == "DROP": actions_gated["DROP"] += 1
                elif c == "PASS": actions_gated["PASS"] += 1
                elif c in ("NORTH", "SOUTH", "EAST", "WEST"): actions_gated["MOVE"] += 1
                elif c == "HARVEST":
                    x, y = wpos
                    tile = prev_obs["farms"][0]["tiles"][y][x]
                    if isinstance(tile, dict) and tile.get("crop") == "STRAWBERRY":
                        actions_gated["HARVEST_STRAW"] += 1
                    else:
                        actions_gated["HARVEST_OTHER"] += 1

        # Run V2
        env_v2 = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_v2 = env_v2.run([v2_agent, "starter"])
        for s_idx in range(1, len(steps_v2)):
            prev_obs = steps_v2[s_idx-1][0]["observation"]
            act = steps_v2[s_idx-1][0].get("action") or {}
            day = prev_obs["day"]
            all_wacts = [act.get("farmer", [])] + act.get("hands", [])
            all_wpos = [prev_obs["farms"][0]["farmer"]] + prev_obs["farms"][0]["hands"]
            for wpos, wact in zip(all_wpos, all_wacts):
                if wact and wact[0] == "FERTILIZE":
                    x, y = wpos
                    tile = prev_obs["farms"][0]["tiles"][y][x]
                    if isinstance(tile, dict):
                        crop = tile.get("crop")
                        p_day = tile.get("planted_day", 0)
                        age = day - p_day
                        # Is it in valid window?
                        valid = (p_day + 7 <= day <= min(29, p_day + 15)) if crop == "STRAWBERRY" else True
                        v2_fert_actions.append({
                            "seed": seed, "day": day, "crop": crop, "age": age,
                            "planted_day": p_day, "valid": valid
                        })

    print("\n" + "="*80)
    print("ACTION BUDGET RECONCILIATION (10-SEED TOTALS & PER-SEED MEANS)")
    print("="*80)
    print(f"{'Action Category':<18} | {'Baseline (per seed)':>20} | {'Gated (per seed)':>20} | {'Delta':>15}")
    print("-" * 80)
    for cat in actions_base:
        b_val = actions_base[cat] / 10.0
        g_val = actions_gated[cat] / 10.0
        d_val = g_val - b_val
        print(f"{cat:<18} | {b_val:>20.1f} | {g_val:>20.1f} | {d_val:>+15.1f}")
        
    print("\n" + "="*80)
    print("V2 FERTILIZER AUDIT (Did Frozen V2 waste immature fertilizer?)")
    print("="*80)
    v2_straw_ferts = [fa for fa in v2_fert_actions if fa["crop"] == "STRAWBERRY"]
    v2_immature_ferts = [fa for fa in v2_straw_ferts if not fa["valid"]]
    print(f"Total V2 Strawberry Fertilizer Actions: {len(v2_straw_ferts)} ({len(v2_straw_ferts)/10.0:.1f} per seed)")
    print(f"Total V2 Immature / Invalid Fert Actions: {len(v2_immature_ferts)} ({len(v2_immature_ferts)/10.0:.1f} per seed)")
    if v2_immature_ferts:
        print("Sample of invalid actions in V2:")
        for fa in v2_immature_ferts[:10]:
            print(f"  Seed {fa['seed']}, Day {fa['day']}, Planted {fa['planted_day']}, Age {fa['age']}")
    else:
        print("Frozen V2 wasted EXACTLY 0 immature fertilizer actions!")

    print("\n" + "="*80)
    print("CL MATURE STRAWBERRY DECAY AUDIT")
    print("="*80)
    print(f"Total Unexplained Yield Drops / Decay on Strawberry: {len(decay_events_cl)}")
    for ev in decay_events_cl[:10]:
        print(ev)

if __name__ == "__main__":
    audit_actions_and_decay()
