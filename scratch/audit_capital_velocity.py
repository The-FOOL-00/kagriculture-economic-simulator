"""
Section 14: Capital Velocity Evaluation
Tests three controlled financial variants of the Declarative Backbone:
V0: Baseline (initial_cash_reserve = 30)
V1: Conservative (initial_cash_reserve = 100)
V2: Aggressive (initial_cash_reserve = 0)
Tested against IDLE and V54 across seeds 2000-2009.
"""
import sys, os, json, statistics, copy
sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")

from kaggle_environments import make
from candidates.declarative_backbone.params import BackboneParams, V54_PRIOR
from candidates.declarative_backbone.compiler import DeclarativeBackboneCompiler
from scratch.extract_comparative_telemetry import load_agent

backbone_path = "candidates/declarative_backbone/agent.py"
v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"

def idle_agent(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

p_v0 = copy.deepcopy(V54_PRIOR)
p_v0.initial_cash_reserve = 30

p_v1 = copy.deepcopy(V54_PRIOR)
p_v1.initial_cash_reserve = 100

p_v2 = copy.deepcopy(V54_PRIOR)
p_v2.initial_cash_reserve = 0

VARIANTS = {
    "V0_BASELINE": p_v0,
    "V1_CONSERVATIVE": p_v1,
    "V2_AGGRESSIVE": p_v2,
}

SEEDS = list(range(2000, 2010))
results = {}

print("Running Capital Velocity Evaluation...")

for v_name, v_params in VARIANTS.items():
    print(f"\n--- Variant {v_name} (reserve = {v_params.initial_cash_reserve}) ---")
    idle_rewards = []
    v54_rewards = []
    for seed in SEEDS:
        # vs IDLE
        comp_idle = DeclarativeBackboneCompiler(v_params)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([lambda o, c=None, cp=comp_idle: cp(o, c), idle_agent])
        r_idle = float(env.steps[-1][0].reward or 0.0)
        idle_rewards.append(r_idle)
        
        # vs V54
        comp_v54 = DeclarativeBackboneCompiler(v_params)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([lambda o, c=None, cp=comp_v54: cp(o, c), load_agent(v54_path)])
        r_v54 = float(env.steps[-1][0].reward or 0.0)
        v54_rewards.append(r_v54)
        
    m_idle = statistics.mean(idle_rewards)
    m_v54  = statistics.mean(v54_rewards)
    results[v_name] = {
        "mean_idle": m_idle,
        "mean_v54": m_v54,
        "sd_idle": statistics.stdev(idle_rewards),
        "sd_v54": statistics.stdev(v54_rewards),
    }
    print(f"  {v_name}: vs IDLE = {m_idle:,.0f} | vs V54 = {m_v54:,.0f}")

json.dump(results, open("scratch/capital_velocity_results.json", "w"), indent=2)
print("Saved to scratch/capital_velocity_results.json")
