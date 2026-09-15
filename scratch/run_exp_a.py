"""
EXP-A Full Evaluation
=====================
Seeds: VALIDATION panel (2000-2039) = 40 seeds
Opponents: IDLE, V2, V54, V66, Synthetic Aggressive, Synthetic Passive
Total: 40 x 6 = 240 games
Output: scratch/exp_a_results.json
"""
import sys, os, json, time, importlib.util, traceback
sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")

from kaggle_environments import make

# ---- Load backbone ----
from candidates.declarative_backbone.params import V54_PRIOR
from candidates.declarative_backbone.compiler import DeclarativeBackboneCompiler

def make_backbone_agent():
    """Fresh instance for each game."""
    comp = DeclarativeBackboneCompiler(V54_PRIOR)
    def _agent(obs, cfg=None):
        return comp(obs, cfg)
    return _agent

# ---- Load opponents ----
def load_file_agent(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path:
        sys.path.insert(0, d)
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "agent", None) or getattr(mod, "_kaggle_submission_entrypoint", None)
    return fn

def idle_agent(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

def synthetic_aggressive(obs, cfg=None):
    """Mimics an agent that dumps lots of goods to saturate market."""
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else {}
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {})
    orders = []
    for prod in ["MILK", "WOOL", "MELON", "STRAWBERRY", "WHEAT"]:
        qty = shed.get(prod, 0)
        if qty > 0:
            orders.append(["SELL", prod, min(qty, 30)])
    orders = orders[:10]
    return {"market": orders, "farmer": ["PASS"], "hands": []}

def synthetic_passive(obs, cfg=None):
    """Passive producer: buys seeds, plants, never sells until day 28."""
    player = obs.get("player", 0)
    day = obs.get("day", 0)
    farms = obs.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else {}
    money = float(farm.get("money", 0))
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {})
    orders = []
    if day >= 28:
        for prod in ["MILK", "WOOL", "MELON", "WHEAT"]:
            qty = shed.get(prod, 0)
            if qty > 0:
                orders.append(["SELL", prod, min(qty, 10)])
    if money >= 100 and day < 15:
        orders.append(["BUY_SEED", "WHEAT", 3])
    return {"market": orders[:5], "farmer": ["PASS"], "hands": []}

OPPONENTS = {
    "IDLE":       idle_agent,
    "V2":         load_file_agent("agents/slot4_control_frozen_v2.py"),
    "V54":        load_file_agent("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"),
    "V66":        load_file_agent("external_repos/kaggriculture-v66-agent/main.py"),
    "SYN_AGG":    synthetic_aggressive,
    "SYN_PASS":   synthetic_passive,
}

VALIDATION_SEEDS = list(range(2000, 2040))  # 40 seeds
MAX_STEPS = 720
PAUSE_BETWEEN = 0.05  # small pause to avoid heat

print("=" * 70)
print("EXP-A: DECLARATIVE BACKBONE VALIDATION PANEL")
print(f"Seeds: {VALIDATION_SEEDS[0]}-{VALIDATION_SEEDS[-1]}  Opponents: {list(OPPONENTS)}")
print(f"Total games: {len(VALIDATION_SEEDS) * len(OPPONENTS)}")
print("=" * 70)

all_results = {}
total_games = 0
total_crashes = 0

for opp_name, opp_fn in OPPONENTS.items():
    print(f"\n--- Opponent: {opp_name} ---")
    opp_results = []
    for seed in VALIDATION_SEEDS:
        backbone = make_backbone_agent()
        try:
            cfg = {"episodeSteps": MAX_STEPS, "seed": seed}
            env = make("kaggriculture", configuration=cfg, debug=False)
            env.run([backbone, opp_fn])
            final = env.steps[-1]
            r0 = float(final[0].reward or 0.0)
            r1 = float(final[1].reward or 0.0)
            margin = r0 - r1
            winner = "backbone" if r0 > r1 else ("opp" if r1 > r0 else "tie")
            opp_results.append({
                "seed": seed, "backbone": r0, "opp": r1,
                "margin": margin, "winner": winner, "error": None
            })
            total_games += 1
            if total_games % 20 == 0:
                print(f"  ... {total_games} games done")
            time.sleep(PAUSE_BETWEEN)
        except Exception as e:
            tb = traceback.format_exc()[-400:]
            opp_results.append({
                "seed": seed, "backbone": 0, "opp": 0,
                "margin": 0, "winner": "crash", "error": str(e) + "\n" + tb
            })
            total_crashes += 1
            print(f"  CRASH seed={seed} vs {opp_name}: {e}")

    rewards = [r["backbone"] for r in opp_results if r["error"] is None]
    margins = [r["margin"] for r in opp_results if r["error"] is None]
    wins = sum(1 for r in opp_results if r["winner"] == "backbone")
    n = len([r for r in opp_results if r["error"] is None])
    import statistics
    mean_r = statistics.mean(rewards) if rewards else 0
    mean_m = statistics.mean(margins) if margins else 0
    sd_m = statistics.stdev(margins) if len(margins) > 1 else 0
    print(f"  n={n}  mean_reward={mean_r:.0f}  mean_margin={mean_m:+.0f}  sd={sd_m:.0f}  wins={wins}/{n}")
    all_results[opp_name] = opp_results

print(f"\nTotal games played: {total_games}  Total crashes: {total_crashes}")

output_path = "scratch/exp_a_results.json"
json.dump(all_results, open(output_path, "w"), indent=2)
print(f"Results written to {output_path}")
print("Run scratch/exp_a_summary.py to check gate criteria")
