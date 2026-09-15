"""
PHASE 17: COMPREHENSIVE STATISTICAL VALIDATION SUITE.
Runs rigorous multi-seed head-to-head tournaments across:
- Qualification Set: 50 seeds x 2 seat rotations = 100 games
- Fresh Holdout Set: 50 seeds x 2 seat rotations = 100 games
Measures:
- Mean Cash, Median, Win Rate, Paired Margin, 95% CI, Worst Loss, Best Win, Catastrophic Rate.
Compares:
1. ClosedLoopV2 vs Dmitrii Base
2. ShopConditionedSpecialist vs Dmitrii Base
3. ShopConditionedSpecialist vs ClosedLoopV2
"""
import os, sys, json, math, copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from test_tomato_with_sales import TomatoSpecialistV1

# Define Shop-Conditioned Policy:
# Evaluates town shops at Step 144:
# If PIZZA_SHOP present and NO STRAWBERRY shop (SMOOTHIE/ICE_CREAM/BRUNCH) present:
#   activates TomatoSpecialist!
# Otherwise:
#   activates ClosedLoopV2!
class ShopConditionedSpecialistAgent:
    def __init__(self):
        self.v2 = ClosedLoopAgentV2()
        self.tom = TomatoSpecialistV1(sale_batch=6)
        self.active_agent = {} # player -> agent

    def act(self, obs):
        step = int(obs["step"])
        player = int(obs["player"])
        
        if step == 144:
            shops = obs.get("town", {}).get("unlocked_shops", [])
            has_pizza = "PIZZA_SHOP" in shops
            has_straw_shops = any(s in shops for s in ["SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT"])
            has_yarn = "YARN_STORE" in shops
            
            # Pure Pizza demand condition
            if has_pizza and not has_straw_shops and not has_yarn:
                self.active_agent[player] = self.tom
            else:
                self.active_agent[player] = self.v2
                
        agent = self.active_agent.get(player, self.v2)
        return agent.act(obs)

def ci95(data):
    n = len(data)
    if n < 2: return 0.0
    mean = sum(data) / n
    var = sum((x - mean) ** 2 for x in data) / (n - 1)
    se = math.sqrt(var / n)
    return 1.96 * se

def evaluate_pairing(agent_cls_a, agent_cls_b, seeds, name_a, name_b):
    scores_a = []
    scores_b = []
    margins = []
    wins_a = 0
    catastrophes_a = 0
    
    # 2 seat rotations per seed
    for s in seeds:
        # Rotation 1: A as Seat 0, B as Seat 1
        g1 = kagsim.Game(s)
        pa1 = agent_cls_a()
        pb1 = agent_cls_b()
        while not g1.done:
            g1.step(pa1.act(g1.observe(0)), pb1.act(g1.observe(1)))
        ra1 = g1.reward(0)
        rb1 = g1.reward(1)
        scores_a.append(ra1)
        scores_b.append(rb1)
        margins.append(ra1 - rb1)
        if ra1 > rb1: wins_a += 1
        if ra1 < 60000: catastrophes_a += 1
        
        # Rotation 2: B as Seat 0, A as Seat 1
        g2 = kagsim.Game(s)
        pb2 = agent_cls_b()
        pa2 = agent_cls_a()
        while not g2.done:
            g2.step(pb2.act(g2.observe(0)), pa2.act(g2.observe(1)))
        rb2 = g2.reward(0)
        ra2 = g2.reward(1)
        scores_a.append(ra2)
        scores_b.append(rb2)
        margins.append(ra2 - rb2)
        if ra2 > rb2: wins_a += 1
        if ra2 < 60000: catastrophes_a += 1
        
    n = len(scores_a)
    mean_a = sum(scores_a) / n
    mean_b = sum(scores_b) / n
    mean_m = sum(margins) / n
    se_m = ci95(margins)
    sorted_m = sorted(margins)
    med_m = sorted_m[n // 2]
    win_rate = wins_a / n
    worst_loss = min(margins)
    best_win = max(margins)
    cat_rate = catastrophes_a / n
    
    return {
        "comparison": f"{name_a} vs {name_b}",
        "n_games": n,
        "mean_a": mean_a,
        "mean_b": mean_b,
        "paired_margin": mean_m,
        "ci95": se_m,
        "median_margin": med_m,
        "win_rate": win_rate,
        "worst_loss": worst_loss,
        "best_win": best_win,
        "catastrophic_rate": cat_rate
    }

def run_phase17():
    print("=" * 80)
    print("PHASE 17: STATISTICAL QUALIFICATION TOURNAMENT")
    print("=" * 80)
    
    # Stratified Seed Cohorts:
    # 50 Qualification seeds: 50000 to 50049
    # 50 Fresh Holdout seeds: 50050 to 50099
    qual_seeds = list(range(50000, 50050))
    holdout_seeds = list(range(50050, 50100))
    
    dmitrii_cls = lambda: mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    v2_cls = lambda: ClosedLoopAgentV2()
    spec_cls = lambda: ShopConditionedSpecialistAgent()
    
    print("\n--- 1. QUALIFICATION SET (N=100 games, Seeds 50000-50049) ---")
    q_v2_vs_dmi = evaluate_pairing(v2_cls, dmitrii_cls, qual_seeds, "ClosedLoopV2", "Dmitrii")
    q_spec_vs_dmi = evaluate_pairing(spec_cls, dmitrii_cls, qual_seeds, "Specialist", "Dmitrii")
    q_spec_vs_v2 = evaluate_pairing(spec_cls, v2_cls, qual_seeds, "Specialist", "ClosedLoopV2")
    
    for r in [q_v2_vs_dmi, q_spec_vs_dmi, q_spec_vs_v2]:
        print(f"\n{r['comparison']}:")
        print(f"  Win Rate:       {r['win_rate']:.1%}")
        print(f"  Mean Score:     ${r['mean_a']:,.0f} vs ${r['mean_b']:,.0f}")
        print(f"  Paired Margin:  ${r['paired_margin']:+,.0f} +/- ${r['ci95']:,.0f}")
        print(f"  Median Margin:  ${r['median_margin']:+,.0f}")
        print(f"  Worst Loss:     ${r['worst_loss']:+,.0f} | Best Win: ${r['best_win']:+,.0f}")
        print(f"  Catastrophic:   {r['catastrophic_rate']:.1%}")

    print("\n--- 2. FRESH HOLDOUT SET (N=100 games, Seeds 50050-50099) ---")
    h_v2_vs_dmi = evaluate_pairing(v2_cls, dmitrii_cls, holdout_seeds, "ClosedLoopV2", "Dmitrii")
    h_spec_vs_dmi = evaluate_pairing(spec_cls, dmitrii_cls, holdout_seeds, "Specialist", "Dmitrii")
    h_spec_vs_v2 = evaluate_pairing(spec_cls, v2_cls, holdout_seeds, "Specialist", "ClosedLoopV2")
    
    for r in [h_v2_vs_dmi, h_spec_vs_dmi, h_spec_vs_v2]:
        print(f"\n{r['comparison']}:")
        print(f"  Win Rate:       {r['win_rate']:.1%}")
        print(f"  Mean Score:     ${r['mean_a']:,.0f} vs ${r['mean_b']:,.0f}")
        print(f"  Paired Margin:  ${r['paired_margin']:+,.0f} +/- ${r['ci95']:,.0f}")
        print(f"  Median Margin:  ${r['median_margin']:+,.0f}")
        print(f"  Worst Loss:     ${r['worst_loss']:+,.0f} | Best Win: ${r['best_win']:+,.0f}")
        print(f"  Catastrophic:   {r['catastrophic_rate']:.1%}")

    # Save summary
    results_all = {
        "qualification": [q_v2_vs_dmi, q_spec_vs_dmi, q_spec_vs_v2],
        "holdout": [h_v2_vs_dmi, h_spec_vs_dmi, h_spec_vs_v2]
    }
    with open("scratch/statistical_validation_results.json", "w") as f:
        json.dump(results_all, f, indent=2)
    print("\nSaved statistical validation results to scratch/statistical_validation_results.json")

if __name__ == "__main__":
    run_phase17()
