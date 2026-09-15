"""
scratch/test_hybrid_challenger.py
=================================
Evaluates the new Hybrid Challenger (Public-3000 High-Throughput Route wrapped
with the proven Deficit-Preemption Residual Controller) against:
1. IDLE
2. V54++ Control Baseline
3. Raw Public-3000
across paired holdout seeds in both seats.
"""

import copy
import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))

import kagsim

V54_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
V62_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py")
V66_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py")
P3000_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "opponents", "public_3000", "main.py")
V54_SHOP_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")

for p in [V54_PATH, V62_PATH, V66_PATH, os.path.dirname(P3000_PATH), os.path.dirname(V54_SHOP_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load V54
spec_v54 = importlib.util.spec_from_file_location("v54_h", V54_PATH)
mod_v54 = importlib.util.module_from_spec(spec_v54)
spec_v54.loader.exec_module(mod_v54)

# Load V62
spec_v62 = importlib.util.spec_from_file_location("v62_h", V62_PATH)
mod_v62 = importlib.util.module_from_spec(spec_v62)
spec_v62.loader.exec_module(mod_v62)

# Load V66 overlays
spec_v66 = importlib.util.spec_from_file_location("v66_h", V66_PATH)
mod_v66 = importlib.util.module_from_spec(spec_v66)
spec_v66.loader.exec_module(mod_v66)

# Load P3000
spec_p3000 = importlib.util.spec_from_file_location("p3000_h", P3000_PATH)
mod_p3000 = importlib.util.module_from_spec(spec_p3000)
spec_p3000.loader.exec_module(mod_p3000)

# Load V54++ Control
spec_shop = importlib.util.spec_from_file_location("shop_h", V54_SHOP_PATH)
mod_shop = importlib.util.module_from_spec(spec_shop)
spec_shop.loader.exec_module(mod_shop)

# Build Hybrid Challenger with proven residual controller
cfg_dict = copy.deepcopy(dict(mod_v62._V54_CONFIG.__dict__))
cfg_dict["preempt_money_deficit"] = 2000.0
cfg_dict["preempt_minimum_delta"] = 4.0
cfg_dict["preempt_maximum_batch"] = 12
config = mod_v54._V51ResidualConfig(**cfg_dict)

policy_hybrid = mod_v54._v51_build_policy(mod_p3000._ACTIONS[:719], config)


def make_hybrid_agent():
    state = {"last_step": -1}
    def agent(obs, configuration=None):
        step = int(obs["day"] * 24 + obs["hour"])
        visible = mod_v62._v56_visible_configuration(configuration)
        act = policy_hybrid(obs, visible)
        
        # 1. Overlay: Hour-23 shed capacity guard
        capacity = int((configuration or {}).get("shedCapacity", 100)) if configuration else 100
        act = mod_v62._v60_shed_guard(obs, act, capacity)
        
        # 2. Overlay: Terminal loaded unit recall (steps 713-716)
        if 713 <= step <= 716:
            act = mod_v66._route_loaded_units(obs, act, step)
            
        # 3. Overlay: Final unit home convergence (steps 717-718)
        if step in (717, 718):
            act = mod_v66._TERMINAL_UNITS(obs, act, step)
            
        # 4. Overlay: Final market liquidation (step 718)
        if step == 718:
            act = mod_v66._TERMINAL_MARKET(obs, act, rule="collision", replace=True)
            
        return act
    return agent


def play_game(agent0, agent1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = agent0(o0)
        a1 = agent1(o1)
        game.step(a0, a1)
    return game.reward(0), game.reward(1)


def evaluate_matchup(name0, fn0, name1, fn1, seeds):
    margins = []
    wins = 0
    losses = 0
    ties = 0
    r0_list = []
    r1_list = []
    
    for s in seeds:
        # Both seats
        # Seat 0
        r0, r1 = play_game(fn0(), fn1(), s)
        m0 = r0 - r1
        margins.append(m0)
        r0_list.append(r0)
        r1_list.append(r1)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1
        else: ties += 1
        
        # Seat 1
        r1, r0 = play_game(fn1(), fn0(), s)
        m1 = r0 - r1
        margins.append(m1)
        r0_list.append(r0)
        r1_list.append(r1)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1
        else: ties += 1
        
    mean_m = sum(margins) / len(margins)
    mean_r0 = sum(r0_list) / len(r0_list)
    mean_r1 = sum(r1_list) / len(r1_list)
    winrate = wins / len(margins) * 100
    
    print(f"\n--- MATCHUP: {name0} vs {name1} ({len(margins)} games, {len(seeds)} seeds x 2 seats) ---")
    print(f"  {name0} Mean Reward: ${mean_r0:,.2f}")
    print(f"  {name1} Mean Reward: ${mean_r1:,.2f}")
    print(f"  Mean Net Margin   : {mean_m:+,.2f}")
    print(f"  Win / Loss / Tie  : {wins} / {losses} / {ties} ({winrate:.1f}% Win Rate)")
    return mean_r0, mean_r1, mean_m


if __name__ == "__main__":
    test_seeds = [11, 23, 47, 100, 200, 300, 400, 500, 600, 700]
    
    print("=" * 70)
    print("      INITIAL DISCOVERY EVALUATION: HYBRID RESIDUAL CHALLENGER")
    print("=" * 70)
    
    # 1. Hybrid vs IDLE
    idle_agent = lambda: (lambda obs: {"farmer": ["PASS"], "hands": [], "market": []})
    evaluate_matchup("Hybrid Challenger", make_hybrid_agent, "IDLE", idle_agent, test_seeds)
    
    # 2. Hybrid vs Raw Public-3000
    evaluate_matchup("Hybrid Challenger", make_hybrid_agent, "Raw Public-3000", lambda: mod_p3000.agent, test_seeds)
    
    # 3. Hybrid vs V54++ Control Baseline
    evaluate_matchup("Hybrid Challenger", make_hybrid_agent, "V54++ Control", lambda: mod_shop.agent, test_seeds)
