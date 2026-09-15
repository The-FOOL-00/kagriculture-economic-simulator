"""
Section 15: Isolated Counterfactual Attribution of Labor, Strawberry, and Fertilizer
Tests:
C0: Baseline Backbone
C1: V54-like labor curve (hires 5 day 0, 8 day 6, 11 day 11)
C2: V54-like strawberry wave (actually plant the 38 strawberry seeds bought!)
C3: V54-like fertilizer liquidation (sell fertilizer every turn)
C4: All three combined
Evaluated across seeds 2000-2009 vs IDLE and vs V54.
"""
import sys, os, json, copy, statistics
sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")

from kaggle_environments import make
from candidates.declarative_backbone.params import V54_PRIOR
from candidates.declarative_backbone.compiler import DeclarativeBackboneCompiler
from scratch.extract_comparative_telemetry import load_agent

v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"

def idle_agent(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

def make_agent(variant):
    comp = DeclarativeBackboneCompiler(V54_PRIOR)
    
    def _agent(obs, cfg=None):
        # We invoke compiler then apply isolated intervention
        player = obs.get("player", 0)
        farms = obs.get("farms", [])
        farm = farms[player] if farms and player < len(farms) else {}
        day = obs.get("day", 0)
        hour = obs.get("hour", 0)
        priv = obs.get("private", {})
        shed = priv.get("shed", {})
        seeds = priv.get("seeds", {})
        
        # C1 intervention: labor curve
        if variant in ("C1", "C4") and hour == 0:
            # Target labor curve: 5 day 0, 8 day 6+, 11 day 11+
            if day < 6: target = 5
            elif day < 11: target = 8
            else: target = 11
            # Adjust compiler p.hire_initial_burst or target_hands
            comp.p.hire_initial_burst = target
            comp.p.max_workers = target
            
        act = comp(obs, cfg)
        
        # C2 intervention: Strawberry planting priority
        # If variant has C2, modify actions so if Strawberry seeds exist, plant Strawberry instead of Carrot
        if variant in ("C2", "C4"):
            straw_seeds = seeds.get("STRAWBERRY", 0)
            if straw_seeds > 0:
                farmer_act = act.get("farmer", [])
                if farmer_act and farmer_act[0] == "PLANT" and farmer_act[1] == "CARROT":
                    act["farmer"] = ["PLANT", "STRAWBERRY"]
                    straw_seeds -= 1
                hands = act.get("hands", [])
                for i, h in enumerate(hands):
                    if straw_seeds > 0 and h and h[0] == "PLANT" and h[1] == "CARROT":
                        hands[i] = ["PLANT", "STRAWBERRY"]
                        straw_seeds -= 1
                act["hands"] = hands
                
        # C3 intervention: Immediate fertilizer liquidation
        if variant in ("C3", "C4"):
            fert_qty = shed.get("FERTILIZER", 0)
            if fert_qty > 0:
                # Add SELL FERTILIZER order if room
                m_orders = act.get("market", [])
                if len(m_orders) < 10:
                    # check if already selling fert
                    if not any(o[0] == "SELL" and o[1] == "FERTILIZER" for o in m_orders):
                        m_orders.append(["SELL", "FERTILIZER", min(fert_qty, 30)])
                        act["market"] = m_orders[:10]
                        
        return act
    return _agent

SEEDS = list(range(2000, 2010))
results = {}

for var in ["C0", "C1", "C2", "C3", "C4"]:
    print(f"\n--- Running Counterfactual {var} ---")
    idle_res = []
    v54_res = []
    for seed in SEEDS:
        # vs IDLE
        agent_fn = make_agent(var)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([agent_fn, idle_agent])
        r_idle = float(env.steps[-1][0].reward or 0.0)
        idle_res.append(r_idle)
        
        # vs V54
        agent_fn = make_agent(var)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([agent_fn, load_agent(v54_path)])
        r_v54 = float(env.steps[-1][0].reward or 0.0)
        v54_res.append(r_v54)
        
    m_idle = statistics.mean(idle_res)
    m_v54 = statistics.mean(v54_res)
    results[var] = {
        "idle_mean": m_idle,
        "v54_mean": m_v54,
        "idle_seeds": idle_res,
        "v54_seeds": v54_res,
    }
    print(f"  {var}: vs IDLE = {m_idle:,.0f} | vs V54 = {m_v54:,.0f}")

# Compute deltas
c0_idle = results["C0"]["idle_mean"]
c0_v54  = results["C0"]["v54_mean"]

d1_idle = results["C1"]["idle_mean"] - c0_idle
d2_idle = results["C2"]["idle_mean"] - c0_idle
d3_idle = results["C3"]["idle_mean"] - c0_idle
d4_idle = results["C4"]["idle_mean"] - c0_idle

d1_v54 = results["C1"]["v54_mean"] - c0_v54
d2_v54 = results["C2"]["v54_mean"] - c0_v54
d3_v54 = results["C3"]["v54_mean"] - c0_v54
d4_v54 = results["C4"]["v54_mean"] - c0_v54

print("\n=== ISOLATED ATTRIBUTION RESULTS ===")
print(f"Vs IDLE:")
print(f"  C0 (Baseline) : {c0_idle:,.0f}")
print(f"  C1 (Labor)    : {results['C1']['idle_mean']:,.0f} (Delta 1 = {d1_idle:+,.0f})")
print(f"  C2 (Strawb)   : {results['C2']['idle_mean']:,.0f} (Delta 2 = {d2_idle:+,.0f})")
print(f"  C3 (Fert)     : {results['C3']['idle_mean']:,.0f} (Delta 3 = {d3_idle:+,.0f})")
print(f"  C4 (All 3)    : {results['C4']['idle_mean']:,.0f} (Delta 4 = {d4_idle:+,.0f})")
print(f"  Linear Sum    : {d1_idle + d2_idle + d3_idle:+,.0f}")
print(f"  Interaction   : {d4_idle - (d1_idle + d2_idle + d3_idle):+,.0f}")

print(f"\nVs V54:")
print(f"  C0 (Baseline) : {c0_v54:,.0f}")
print(f"  C1 (Labor)    : {results['C1']['v54_mean']:,.0f} (Delta 1 = {d1_v54:+,.0f})")
print(f"  C2 (Strawb)   : {results['C2']['v54_mean']:,.0f} (Delta 2 = {d2_v54:+,.0f})")
print(f"  C3 (Fert)     : {results['C3']['v54_mean']:,.0f} (Delta 3 = {d3_v54:+,.0f})")
print(f"  C4 (All 3)    : {results['C4']['v54_mean']:,.0f} (Delta 4 = {d4_v54:+,.0f})")
print(f"  Linear Sum    : {d1_v54 + d2_v54 + d3_v54:+,.0f}")
print(f"  Interaction   : {d4_v54 - (d1_v54 + d2_v54 + d3_v54):+,.0f}")

json.dump(results, open("scratch/isolated_counterfactuals_results.json", "w"), indent=2)
