"""
COMPREHENSIVE EXPERIMENTAL SUITE FOR CLOSED-LOOP ECONOMIC ARCHITECTURE
Runs:
1. Phase 9: Counterfactual Decision Evaluations
2. Phase 10: Live Opponent Replay Testing against all 6 major opponents
3. Phase 11: Experiment Matrix across seed cohorts (Yarn, Non-Yarn, High-Demand, Low-Demand, Holdout)
4. Phase 12: Pareto frontier metrics (Mean, Median, CI, Win Rate, Worst Loss, Catastrophic Rate)
"""
import copy
import json
import math
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54_res
import compiled_v54_plus_shop as v54_shop
from closed_loop_agent import ClosedLoopAgent

# ==============================================================================
# PHASE 9: COUNTERFACTUAL DECISION TESTING
# ==============================================================================
def run_phase9_counterfactuals():
    print("\n" + "=" * 90)
    print("PHASE 9: TARGETED COUNTERFACTUAL DECISION EVALUATION")
    print("=" * 90)
    
    seeds = [50007, 50009, 50027, 50082, 50266]
    deltas_switching = []
    deltas_shed_guard = []
    
    for s in seeds:
        # Decision 1: At Step 144 in Dual Dairy World:
        # Option A: Stay Module A (Base 61-fert strawberry)
        # Option B: Switch to Module B (Dairy continuation)
        g_optA = kagsim.Game(s)
        ag_optA = ClosedLoopAgent(switching_mode="NO_SWITCHING")
        while not g_optA.done:
            g_optA.step(ag_optA.act(g_optA.observe(0)), v54_res.agent(g_optA.observe(1)))
        score_optA = g_optA.reward(0)
        
        g_optB = kagsim.Game(s)
        ag_optB = ClosedLoopAgent(switching_mode="MILESTONE_CONSERVATIVE")
        while not g_optB.done:
            g_optB.step(ag_optB.act(g_optB.observe(0)), v54_res.agent(g_optB.observe(1)))
        score_optB = g_optB.reward(0)
        
        # Decision 2: Shed Guard (75 ceiling vs No Shed Purge)
        g_no_shed = kagsim.Game(s)
        ag_no_shed = ClosedLoopAgent(switching_mode="NO_SWITCHING", shed_policy="NO_PURGE")
        # Overwrite ceiling to 100
        ag_no_shed.shed_controller.get_effective_ceiling = lambda state: 100
        while not g_no_shed.done:
            g_no_shed.step(ag_no_shed.act(g_no_shed.observe(0)), v54_res.agent(g_no_shed.observe(1)))
        score_no_shed = g_no_shed.reward(0)
        
        delta_switch = score_optB - score_optA
        delta_shed = score_optA - score_no_shed
        deltas_switching.append(delta_switch)
        deltas_shed_guard.append(delta_shed)
        
        print(f"Seed {s}:")
        print(f"  Option A (Module A Base):      ${score_optA:,.2f}")
        print(f"  Option B (Module B Dairy):     ${score_optB:,.2f}  (Delta: ${delta_switch:+,.2f})")
        print(f"  Option C (No Shed Headroom):   ${score_no_shed:,.2f}  (Shed Guard Value: ${delta_shed:+,.2f})")
        
    print(f"\nCounterfactual Summary over {len(seeds)} Dairy Seeds:")
    print(f"  Mean Module B vs Module A Delta:   ${sum(deltas_switching)/len(seeds):+,.2f}")
    print(f"  Mean Shed Headroom Guard Value:    ${sum(deltas_shed_guard)/len(seeds):+,.2f}")

# ==============================================================================
# PHASE 10: LIVE OPPONENT REPLAY TESTING
# ==============================================================================
def run_phase10_live_opponents():
    print("\n" + "=" * 90)
    print("PHASE 10: LIVE OPPONENT REPLAY TESTS (6 MAJOR OPPONENTS)")
    print("=" * 90)
    
    episodes = [
        {"ep": "107543042", "opp_name": "ORiginators (56120608)", "seed": 50266, "world": "PIZZA + PIZZA"},
        {"ep": "107560807", "opp_name": "AGI (56145326)", "seed": 50130, "world": "PET CAFE + BAKERY"},
        {"ep": "107563778", "opp_name": "Meteor (56145078)", "seed": 50058, "world": "ICE CREAM + PET CAFE"},
        {"ep": "107581148", "opp_name": "Re:dorf (56149337)", "seed": 50036, "world": "BAKERY + ICE CREAM"},
        {"ep": "107564294", "opp_name": "Les 2 oies (56149479)", "seed": 50186, "world": "BAKERY + BRUNCH"},
        {"ep": "107582150", "opp_name": "xxxxyt (56148830)", "seed": 50025, "world": "YARN + PIZZA + ICE CREAM"}
    ]
    
    results = []
    
    for item in episodes:
        ep_id = item["ep"]
        path = f"replays/live_tournament/episode_{ep_id}.json"
        if not os.path.exists(path):
            print(f"Skipping {ep_id}: file not found")
            continue
            
        d = json.load(open(path))
        info = d.get("info", {})
        seed = int(info.get("seed") or d.get("configuration", {}).get("seed"))
        teams = info.get("TeamNames", ["Player0", "Player1"])
        our_seat = 0 if "Eldritch" in teams[0] else 1
        opp_seat = 1 - our_seat
        replay_steps = d["steps"]
        
        official_us = replay_steps[-1][our_seat].get("reward", 0)
        official_opp = replay_steps[-1][opp_seat].get("reward", 0)
        
        # Test 1: Closed-Loop Agent vs Replayed Opponent Actions
        g_cl = kagsim.Game(seed)
        ag_cl = ClosedLoopAgent(switching_mode="MILESTONE_CONSERVATIVE")
        for s in range(len(replay_steps) - 1):
            opp_act = replay_steps[s][opp_seat].get("action") or {}
            obs_us = g_cl.observe(our_seat)
            our_act = ag_cl.act(obs_us)
            if our_seat == 0: g_cl.step(our_act, opp_act)
            else: g_cl.step(opp_act, our_act)
        cl_us = g_cl.reward(our_seat)
        cl_opp = g_cl.reward(opp_seat)
        
        # Test 2: Dmitrii Base vs Replayed Opponent Actions
        g_dm = kagsim.Game(seed)
        p_dm = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        for s in range(len(replay_steps) - 1):
            opp_act = replay_steps[s][opp_seat].get("action") or {}
            obs_us = g_dm.observe(our_seat)
            our_act = p_dm.act(obs_us)
            if our_seat == 0: g_dm.step(our_act, opp_act)
            else: g_dm.step(opp_act, our_act)
        dm_us = g_dm.reward(our_seat)
        dm_opp = g_dm.reward(opp_seat)
        
        item_res = {
            "ep": ep_id,
            "opp": item["opp_name"],
            "world": item["world"],
            "official_margin": official_us - official_opp,
            "cl_cash": cl_us,
            "cl_margin": cl_us - cl_opp,
            "dm_cash": dm_us,
            "dm_margin": dm_us - dm_opp,
            "delta_vs_dm": cl_us - dm_us,
            "hires_protected": ag_cl.diagnostics["hires_protected"],
            "shed_purges": ag_cl.diagnostics["shed_purges"],
            "switches": ag_cl.diagnostics["switches_performed"]
        }
        results.append(item_res)
        
        print(f"\nEpisode {ep_id} vs {item['opp_name']} ({item['world']}):")
        print(f"  Official Live Result: Us=${official_us:,.0f} vs Opp=${official_opp:,.0f} (Margin: ${official_us - official_opp:+,.0f})")
        print(f"  Closed-Loop Agent:   Us=${cl_us:,.0f} vs Opp=${cl_opp:,.0f} (Margin: ${cl_us - cl_opp:+,.0f})")
        print(f"  Dmitrii Base:        Us=${dm_us:,.0f} vs Opp=${dm_opp:,.0f} (Margin: ${dm_us - dm_opp:+,.0f})")
        print(f"  CL vs Dmitrii Delta: ${cl_us - dm_us:+,.0f} | Hires Protected: {ag_cl.diagnostics['hires_protected']}")
        
    return results

# ==============================================================================
# PHASE 11 & 12: EXPERIMENT MATRIX & PARETO EVALUATION
# ==============================================================================
def run_phase11_matrix():
    print("\n" + "=" * 90)
    print("PHASE 11: FULL EXPERIMENT MATRIX ACROSS SEED COHORTS (COMMON RANDOM NUMBERS)")
    print("=" * 90)
    
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    
    # Cohorts:
    # 1. Yarn Worlds
    yarn_seeds = seeds_data.get("YARN_STORE+YARN_STORE", []) + seeds_data.get("YARN_STORE+BAKERY", [])
    # 2. Non-Yarn High Demand (Smoothie + Ice Cream, Pizza)
    dairy_seeds = seeds_data.get("SMOOTHIE_SHOP+ICE_CREAM_SHOP", []) + seeds_data.get("ICE_CREAM_SHOP+SMOOTHIE_SHOP", [])
    pizza_seeds = seeds_data.get("PIZZA_SHOP+PIZZA_SHOP", []) + seeds_data.get("PIZZA_SHOP+SMOOTHIE_SHOP", [])
    # 3. Non-Yarn Dispersed (Pet Cafe, Bakery)
    dispersed_seeds = seeds_data.get("PET_CAFE+BAKERY", []) + seeds_data.get("BAKERY+BRUNCH_SPOT", [])
    # 4. Previously catastrophic seeds
    catastrophic_seeds = [50007, 50266, 50130, 50058, 50036]
    
    cohorts = {
        "Yarn Worlds": yarn_seeds[:10],
        "Dual Dairy Worlds": dairy_seeds[:10],
        "Pizza Worlds": pizza_seeds[:10],
        "Dispersed Worlds": dispersed_seeds[:10],
        "Known Catastrophic Seeds": catastrophic_seeds
    }
    
    all_res_cl = []
    all_res_dm = []
    all_res_v54 = []
    
    cohort_stats = {}
    
    for c_name, c_seeds in cohorts.items():
        if not c_seeds: continue
        cl_scores = []
        dm_scores = []
        v54_scores = []
        
        for s in c_seeds:
            # Seat 0: CL vs V54++
            g0 = kagsim.Game(s)
            ag = ClosedLoopAgent(switching_mode="MILESTONE_CONSERVATIVE")
            while not g0.done: g0.step(ag.act(g0.observe(0)), v54_res.agent(g0.observe(1)))
            cl_scores.append(g0.reward(0))
            v54_scores.append(g0.reward(1))
            
            # Seat 0: Dmitrii vs V54++
            g1 = kagsim.Game(s)
            p = mod_r.Policy("extracted_agents/dmitrii_lb2800")
            while not g1.done: g1.step(p.act(g1.observe(0)), v54_res.agent(g1.observe(1)))
            dm_scores.append(g1.reward(0))
            
        all_res_cl.extend(cl_scores)
        all_res_dm.extend(dm_scores)
        all_res_v54.extend(v54_scores)
        
        mean_cl = sum(cl_scores) / len(cl_scores)
        mean_dm = sum(dm_scores) / len(dm_scores)
        mean_v54 = sum(v54_scores) / len(v54_scores)
        cohort_stats[c_name] = {
            "n": len(cl_scores),
            "cl_mean": mean_cl,
            "dm_mean": mean_dm,
            "v54_mean": mean_v54,
            "delta_vs_dm": mean_cl - mean_dm,
            "delta_vs_v54": mean_cl - mean_v54
        }
        
        print(f"\nCohort: {c_name} (N={len(cl_scores)}):")
        print(f"  Closed-Loop Mean:  ${mean_cl:,.2f}")
        print(f"  Dmitrii Base Mean: ${mean_dm:,.2f}  (Delta: ${mean_cl - mean_dm:+,.2f})")
        print(f"  V54++ Mean:        ${mean_v54:,.2f}  (Delta: ${mean_cl - mean_v54:+,.2f})")

    # Aggregate Statistics
    total_matches = len(all_res_cl)
    mean_cl = sum(all_res_cl) / total_matches
    mean_dm = sum(all_res_dm) / total_matches
    mean_v54 = sum(all_res_v54) / total_matches
    
    diffs_vs_dm = [c - d for c, d in zip(all_res_cl, all_res_dm)]
    diffs_vs_dm.sort()
    median_diff = diffs_vs_dm[total_matches // 2]
    
    var_diff = sum((d - (mean_cl - mean_dm)) ** 2 for d in diffs_vs_dm) / (total_matches - 1)
    se_diff = math.sqrt(var_diff) / math.sqrt(total_matches)
    ci95 = [ (mean_cl - mean_dm) - 1.96 * se_diff, (mean_cl - mean_dm) + 1.96 * se_diff ]
    
    wins_vs_v54 = sum(1 for c, v in zip(all_res_cl, all_res_v54) if c > v)
    losses_vs_v54 = sum(1 for c, v in zip(all_res_cl, all_res_v54) if c < v)
    ties_vs_v54 = total_matches - wins_vs_v54 - losses_vs_v54
    
    wins_vs_dm = sum(1 for d in diffs_vs_dm if d > 0)
    losses_vs_dm = sum(1 for d in diffs_vs_dm if d < 0)
    ties_vs_dm = total_matches - wins_vs_dm - losses_vs_dm
    
    catastrophic_cl = sum(1 for c in all_res_cl if c < 60000)
    catastrophic_v54 = sum(1 for v in all_res_v54 if v < 60000)
    
    print("\n" + "=" * 90)
    print("GLOBAL AGGREGATE EVALUATION SUMMARY")
    print("=" * 90)
    print(f"Total Matches Evaluated:        {total_matches}")
    print(f"Closed-Loop Overall Mean:       ${mean_cl:,.2f}")
    print(f"Dmitrii Base Overall Mean:      ${mean_dm:,.2f}")
    print(f"V54++ Residual Overall Mean:    ${mean_v54:,.2f}")
    print(f"Net Delta vs Dmitrii:           ${mean_cl - mean_dm:+,.2f}")
    print(f"Median Delta vs Dmitrii:        ${median_diff:+,.2f}")
    print(f"95% CI vs Dmitrii:              [${ci95[0]:+,.2f}, ${ci95[1]:+,.2f}]")
    print(f"Record vs V54++:                {wins_vs_v54}W / {ties_vs_v54}T / {losses_vs_v54}L (Win Rate: {wins_vs_v54/total_matches*100:.1f}%)")
    print(f"Record vs Dmitrii:              {wins_vs_dm}W / {ties_vs_dm}T / {losses_vs_dm}L (Win Rate: {wins_vs_dm/total_matches*100:.1f}%)")
    print(f"Catastrophic Rate (< $60k):     CL: {catastrophic_cl}/{total_matches} ({catastrophic_cl/total_matches*100:.1f}%) vs V54++: {catastrophic_v54}/{total_matches} ({catastrophic_v54/total_matches*100:.1f}%)")
    print(f"Worst Delta vs Dmitrii:         ${min(diffs_vs_dm):+,.2f}")
    print(f"Best Win vs Dmitrii:            ${max(diffs_vs_dm):+,.2f}")

if __name__ == "__main__":
    run_phase9_counterfactuals()
    run_phase10_live_opponents()
    run_phase11_matrix()
