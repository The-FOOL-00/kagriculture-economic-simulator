#!/usr/bin/env python3
"""Run exact action-level and macro differential analysis between V44, 2945, and 3009.

Evaluates candidates on identical seeds using common random numbers (CRN).
Calculates:
- First divergence step
- Divergence density by phase and action family
- Full macro signatures (purchases, land, workers, animals, crops, sales, terminal cash)
"""

import copy
import json
import os
import sys
from collections import defaultdict

# Add workspace to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController

# Protect holdouts
PROTECTED_RANGES = [(214200, 214249), (340090, 340199), (249695, 249734)]


def check_seed_safety(seed: int):
    for start, end in PROTECTED_RANGES:
        assert not (start <= seed <= end), f"CRITICAL: Protected holdout seed {seed} accessed!"


def load_agent(agent_path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent_mod", agent_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def normalize_action(act):
    if not isinstance(act, dict):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    f = act.get("farmer") or ["PASS"]
    h = [x or ["PASS"] for x in (act.get("hands") or [])]
    m = [list(x) for x in (act.get("market") or [])]
    return {"farmer": list(f), "hands": h, "market": m}


def extract_macro_stats(obs, seat):
    farm = obs["farms"][seat]
    cash = farm["money"]
    land_count = len(farm.get("unlocked_quadrants", ["NW"]))
    hands_count = len(farm.get("hands", []))
    
    # Animals on tiles
    animals = defaultdict(int)
    crops = defaultdict(int)
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                if tile.get("kind") in ("PASTURE", "COOP"):
                    an = tile.get("animal")
                    if an:
                        animals[an] += 1
                elif tile.get("kind") == "PLANT":
                    cr = tile.get("crop")
                    if cr:
                        crops[cr] += 1
                        
    priv = obs.get("private", {})
    shed = priv.get("shed", {})
    return {
        "terminal_cash": cash,
        "land_quadrants": land_count,
        "hands": hands_count,
        "animals": dict(animals),
        "crops": dict(crops),
        "terminal_shed": dict(shed),
    }


def _act(agent_obj, obs):
    if hasattr(agent_obj, "act") and callable(getattr(agent_obj, "act")):
        return agent_obj.act(obs)
    return agent_obj(obs)


def run_single_game_capture(seed, agent0_obj, agent1_obj):
    check_seed_safety(seed)
    sim = FastKagricultureSim(seed=seed)
    obs_list = sim.reset(seed=seed)
    
    traces0 = []
    traces1 = []
    
    last_obs_a = None
    last_obs_b = None
    
    for step in range(719):
        obs_a = obs_list[0]
        obs_b = obs_list[1]
        
        act0 = _act(agent0_obj, obs_a)
        act1 = _act(agent1_obj, obs_b)
        
        norm0 = normalize_action(act0)
        norm1 = normalize_action(act1)
        
        traces0.append(norm0)
        traces1.append(norm1)
        
        obs_list, rewards, done, info = sim.step([act0, act1])
        last_obs_a = obs_list[0]
        last_obs_b = obs_list[1]
        
    stats0 = extract_macro_stats(last_obs_a, 0)
    stats1 = extract_macro_stats(last_obs_b, 1)
    return traces0, traces1, stats0, stats1


def compare_traces(trace_base, trace_cand):
    first_div = None
    divergence_by_phase = defaultdict(int)
    divergence_by_family = defaultdict(int)
    total_steps = len(trace_base)
    
    for step in range(total_steps):
        b = trace_base[step]
        c = trace_cand[step]
        
        day = step // 24
        if day < 4:
            phase = "Opening (Day 0-3)"
        elif day < 11:
            phase = "Early (Day 4-10)"
        elif day < 21:
            phase = "Mid (Day 11-20)"
        elif day < 28:
            phase = "Late (Day 21-27)"
        else:
            phase = "Terminal (Day 28-29)"
            
        diffs = []
        if b["farmer"] != c["farmer"]:
            diffs.append("farmer")
        if b["hands"] != c["hands"]:
            diffs.append("hands")
        if b["market"] != c["market"]:
            diffs.append("market")
            
        if diffs:
            if first_div is None:
                first_div = step
            divergence_by_phase[phase] += 1
            for d in diffs:
                divergence_by_family[d] += 1
                
    return {
        "first_divergence_step": first_div,
        "divergence_by_phase": dict(divergence_by_phase),
        "divergence_by_family": dict(divergence_by_family),
        "total_divergence_steps": sum(1 for step in range(total_steps) if trace_base[step] != trace_cand[step]),
    }


def main():
    seeds = list(range(249800, 249816))  # 16 clean dev seeds
    for s in seeds:
        check_seed_safety(s)
        
    t2945_path = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "thomastschinkel_2945", "main.py")
    k3009_path = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "kaitofukami_v48_3009", "main.py")
    
    agent_2945_fn = load_agent(t2945_path)
    agent_3009_fn = load_agent(k3009_path)
    
    print(f"Starting differential analysis over {len(seeds)} seeds...")
    
    h2h_results = []
    print("Running V44 vs 2945 matches...")
    for s in seeds:
        v44 = V44CandidateController()
        t_v44, t_2945, s_v44, s_2945 = run_single_game_capture(s, v44, agent_2945_fn)
        comp = compare_traces(t_v44, t_2945)
        h2h_results.append({
            "seed": s,
            "v44_cash": s_v44["terminal_cash"],
            "2945_cash": s_2945["terminal_cash"],
            "margin_v44": s_v44["terminal_cash"] - s_2945["terminal_cash"],
            "v44_macro": s_v44,
            "2945_macro": s_2945,
            "differential": comp,
        })
        print(f"  Seed {s}: V44=${s_v44['terminal_cash']:.0f} vs 2945=${s_2945['terminal_cash']:.0f} (diff={s_v44['terminal_cash']-s_2945['terminal_cash']:.0f}), 1st div step={comp['first_divergence_step']}")
        
    print("\nRunning V44 vs 3009 matches...")
    h2h_3009 = []
    for s in seeds[:8]:
        v44 = V44CandidateController()
        t_v44, t_3009, s_v44, s_3009 = run_single_game_capture(s, v44, agent_3009_fn)
        comp = compare_traces(t_v44, t_3009)
        h2h_3009.append({
            "seed": s,
            "v44_cash": s_v44["terminal_cash"],
            "3009_cash": s_3009["terminal_cash"],
            "margin_v44": s_v44["terminal_cash"] - s_3009["terminal_cash"],
            "v44_macro": s_v44,
            "3009_macro": s_3009,
            "differential": comp,
        })
        print(f"  Seed {s}: V44=${s_v44['terminal_cash']:.0f} vs 3009=${s_3009['terminal_cash']:.0f} (diff={s_v44['terminal_cash']-s_3009['terminal_cash']:.0f}), 1st div step={comp['first_divergence_step']}")
        
    out_dir = os.path.join(REPO_ROOT, "research", "v47", "differential")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "differential_analysis_results.json")
    
    summary = {
        "seeds": seeds,
        "v44_vs_2945": h2h_results,
        "v44_vs_3009": h2h_3009,
    }
    
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"\nDifferential analysis saved to {out_file}!")


if __name__ == "__main__":
    main()
