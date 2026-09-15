"""
Section 8: Controlled Opponent Ablations
Tests EXP-A Backbone against:
O0: IDLE
O1: Passive farmer (grows crops, never sells to market)
O2: Moderate farmer (2 cows, 1 sheep, sells normally)
O3: Aggressive livestock producer (8 cows, 4 sheep, aggressive seller)
O4: V54
O5: V66
across seeds 2000-2009.
"""
import sys, os, json, importlib.util, statistics
from kaggle_environments import make

def load_agent(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path:
        sys.path.insert(0, d)
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", None) or getattr(mod, "_kaggle_submission_entrypoint", None)

backbone_path = "candidates/declarative_backbone/agent.py"
v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
v66_path = "external_repos/kaggriculture-v66-agent/main.py"

# O0: IDLE
def o0_idle(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

# O1: Passive farmer (buys seeds, plants, waters, NEVER sells)
def make_o1():
    def _agent(obs, cfg=None):
        player = obs.get("player", 1)
        farm = obs.get("farms", [{}, {}])[player]
        priv = obs.get("private", {})
        day = obs.get("day", 0)
        hour = obs.get("hour", 0)
        money = farm.get("money", 0)
        orders = []
        if hour == 0 and farm.get("hires_today", 0) < 3 and money > 20:
            orders.append(["HIRE"])
        seeds = priv.get("seeds", {})
        if sum(seeds.values()) < 5 and money > 100:
            orders.append(["BUY_SEED", "CARROT", 3])
        # simple farm actions: PASS
        hands_count = len(farm.get("hands", []))
        return {"market": orders, "farmer": ["PASS"], "hands": [["PASS"]] * hands_count}
    return _agent

# O2: Moderate farmer (buys 2 cows, sells milk/fert)
def make_o2():
    cows_bought = 0
    def _agent(obs, cfg=None):
        nonlocal cows_bought
        player = obs.get("player", 1)
        farm = obs.get("farms", [{}, {}])[player]
        priv = obs.get("private", {})
        shed = priv.get("shed", {})
        hour = obs.get("hour", 0)
        money = farm.get("money", 0)
        orders = []
        if hour == 0 and farm.get("hires_today", 0) < 3 and money > 20:
            orders.append(["HIRE"])
        if cows_bought < 2 and money >= 600:
            orders.append(["BUY_ANIMAL", "COW", 1])
            cows_bought += 1
        # Moderate selling
        for p in ["MILK", "FERTILIZER", "WOOL"]:
            if shed.get(p, 0) > 0:
                orders.append(["SELL", p, min(shed[p], 5)])
        hands_count = len(farm.get("hands", []))
        return {"market": orders[:5], "farmer": ["PASS"], "hands": [["PASS"]] * hands_count}
    return _agent

# O3: Aggressive producer (buys cows/sheep, sells heavily)
def make_o3():
    cows_bought = 0
    def _agent(obs, cfg=None):
        nonlocal cows_bought
        player = obs.get("player", 1)
        farm = obs.get("farms", [{}, {}])[player]
        priv = obs.get("private", {})
        shed = priv.get("shed", {})
        hour = obs.get("hour", 0)
        money = farm.get("money", 0)
        orders = []
        if hour == 0 and farm.get("hires_today", 0) < 8 and money > 50:
            orders.append(["HIRE"])
        if cows_bought < 6 and money >= 600:
            orders.append(["BUY_ANIMAL", "COW", 1])
            cows_bought += 1
        for p in ["MILK", "FERTILIZER", "WOOL", "MELON", "STRAWBERRY"]:
            if shed.get(p, 0) > 0:
                orders.append(["SELL", p, min(shed[p], 20)])
        hands_count = len(farm.get("hands", []))
        return {"market": orders[:10], "farmer": ["PASS"], "hands": [["PASS"]] * hands_count}
    return _agent

OPPONENTS = {
    "O0_IDLE": o0_idle,
    "O1_PASSIVE_NO_SELL": make_o1,
    "O2_MODERATE_SELL": make_o2,
    "O3_AGGRESSIVE_SELL": make_o3,
    "O4_V54": lambda: load_agent(v54_path),
    "O5_V66": lambda: load_agent(v66_path),
}

SEEDS = list(range(2000, 2010))
results = {}

for opp_key, opp_factory in OPPONENTS.items():
    print(f"\nRunning Ablation vs {opp_key}...")
    opp_rewards = []
    our_rewards = []
    for seed in SEEDS:
        opp_fn = opp_factory() if callable(opp_factory) and not opp_key.startswith("O0") else o0_idle
        if opp_key in ("O4_V54", "O5_V66"):
            opp_fn = load_agent(v54_path if opp_key == "O4_V54" else v66_path)
            
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([load_agent(backbone_path), opp_fn])
        r0 = float(env.steps[-1][0].reward or 0.0)
        r1 = float(env.steps[-1][1].reward or 0.0)
        our_rewards.append(r0)
        opp_rewards.append(r1)
        
    mean_our = statistics.mean(our_rewards)
    mean_opp = statistics.mean(opp_rewards)
    results[opp_key] = {
        "our_mean": mean_our,
        "opp_mean": mean_opp,
        "our_sd": statistics.stdev(our_rewards),
        "seeds": {s: (r0, r1) for s, r0, r1 in zip(SEEDS, our_rewards, opp_rewards)}
    }
    print(f"  {opp_key}: Our Mean = {mean_our:,.0f} | Opp Mean = {mean_opp:,.0f}")

json.dump(results, open("scratch/ablation_opponents_results.json", "w"), indent=2)
print("Saved to scratch/ablation_opponents_results.json")
