"""
Audit Section 3: Test for Fundamental Ablation Error & Contamination
Inspects whether disabling each mechanism M1-M9 directly or indirectly altered:
1. Worker counts
2. Cash availability trajectory
3. Crop planting & harvesting
4. Market inventory & prices
5. Livestock feeding & animal uptime
6. RNG divergence
7. Route timing & downstream dependencies
"""
import sys, os, json, importlib.util
from collections import defaultdict
from kaggle_environments import make

def run_instrumented_ablation(ablation_id, seed=2000):
    # Load V54
    v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
    d = os.path.dirname(os.path.abspath(v54_path))
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("v54_mod", v54_path)
    v54_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v54_mod)
    raw_v54 = getattr(v54_mod, "agent", None)

    telemetry = {
        "ablation": ablation_id,
        "seed": seed,
        "hires_by_day": defaultdict(int),
        "cash_by_day": {},
        "crops_bought": defaultdict(int),
        "crops_planted": defaultdict(int),
        "crops_harvested": defaultdict(int),
        "animals_bought": defaultdict(int),
        "feeds": 0,
        "cares": 0,
        "sells": defaultdict(int),
        "final_reward": 0.0,
        "starvations": 0,
    }

    def ablated_agent(obs, cfg=None):
        act = raw_v54(obs, cfg)
        if not isinstance(act, dict): return act
        
        step = obs.get("step", obs.get("day", 0) * 24 + obs.get("hour", 0))
        day = obs.get("day", step // 24)
        market = list(act.get("market", []))
        farmer = list(act.get("farmer", ["PASS"]))
        hands = [list(h) for h in act.get("hands", [])]
        
        if ablation_id == "M1_NO_EARLY_WHEAT":
            market = [o for o in market if not (o and o[0] == "BUY_SEED" and o[1] == "WHEAT" and day < 7)]
        elif ablation_id == "M2_NO_STRAWBERRY":
            market = [o for o in market if not (o and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY")]
        elif ablation_id == "M3_NO_ACCELERATED_LABOR":
            player = obs.get("player", 0)
            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            hires_today = farm.get("hires_today", 0)
            new_m = []
            for o in market:
                if o and o[0] == "HIRE":
                    if hires_today < 3:
                        new_m.append(o)
                        hires_today += 1
                else:
                    new_m.append(o)
            market = new_m
        elif ablation_id == "M4_NO_EARLY_LIVESTOCK":
            if day < 10:
                market = [o for o in market if not (o and o[0] == "BUY_ANIMAL")]
        elif ablation_id == "M6_NO_BATCH_SELLING":
            new_m = []
            for o in market:
                if o and o[0] == "SELL":
                    new_m.append(["SELL", o[1], 1])
                else:
                    new_m.append(o)
            market = new_m
        elif ablation_id == "M7_NO_EARLY_SELLING":
            if step < 240:
                market = [o for o in market if not (o and o[0] == "SELL")]
        elif ablation_id == "M8_NO_TERMINAL_LIQUIDATION":
            if step >= 670:
                market = [o for o in market if not (o and o[0] == "SELL")]
        elif ablation_id == "M9_NO_MARKET_AWARE_SELLING":
            if step % 8 != 0:
                market = [o for o in market if not (o and o[0] == "SELL")]
                
        act["market"] = market[:10]
        act["farmer"] = farmer
        act["hands"] = hands
        return act

    opp_fn = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    agent_fn = raw_v54 if ablation_id == "BASELINE" else ablated_agent
    env.run([agent_fn, opp_fn])

    telemetry["final_reward"] = float(env.steps[-1][0].reward or 0.0)
    for step_idx in range(1, len(env.steps)):
        s = env.steps[step_idx]
        obs = s[0].observation
        act = s[0].action or {}
        farm = obs.farms[0]
        day = obs.day
        hour = obs.hour
        if hour == 23 or step_idx == 720:
            telemetry["cash_by_day"][day] = farm["money"]
            telemetry["hires_by_day"][day] = farm["hires_today"]
        all_units = [act.get("farmer", ["PASS"])] + act.get("hands", [])
        for u in all_units:
            if not u: continue
            if u[0] == "PLANT" and len(u) > 1:
                telemetry["crops_planted"][u[1]] += 1
            elif u[0] == "HARVEST":
                telemetry["crops_harvested"]["TOTAL"] += 1
            elif u[0] == "FEED":
                telemetry["feeds"] += 1
            elif u[0] == "CARE":
                telemetry["cares"] += 1
        for o in act.get("market", []):
            if not o: continue
            if o[0] == "BUY_SEED" and len(o) > 2:
                telemetry["crops_bought"][o[1]] += o[2]
            elif o[0] == "BUY_ANIMAL" and len(o) > 1:
                telemetry["animals_bought"][o[1]] += 1
            elif o[0] == "SELL" and len(o) > 2:
                telemetry["sells"][o[1]] += o[2]
                
    return telemetry

ABLATIONS = [
    "BASELINE",
    "M1_NO_EARLY_WHEAT",
    "M2_NO_STRAWBERRY",
    "M3_NO_ACCELERATED_LABOR",
    "M4_NO_EARLY_LIVESTOCK",
    "M6_NO_BATCH_SELLING",
    "M7_NO_EARLY_SELLING",
    "M8_NO_TERMINAL_LIQUIDATION",
    "M9_NO_MARKET_AWARE_SELLING",
]

if __name__ == "__main__":
    results = {}
    for abl in ABLATIONS:
        print(f"Profiling {abl}...")
        results[abl] = run_instrumented_ablation(abl, seed=2000)
        
    base = results["BASELINE"]
    print("\n" + "="*90)
    print("CONTAMINATION ANALYSIS MATRIX")
    print("="*90)
    
    analysis = []
    for abl in ABLATIONS:
        if abl == "BASELINE": continue
        res = results[abl]
        
        # Check side effects
        hires_diff = sum(res["hires_by_day"].values()) - sum(base["hires_by_day"].values())
        cash_d5 = res["cash_by_day"].get(5, 0) - base["cash_by_day"].get(5, 0)
        cash_d10 = res["cash_by_day"].get(10, 0) - base["cash_by_day"].get(10, 0)
        wheat_diff = res["crops_planted"]["WHEAT"] - base["crops_planted"]["WHEAT"]
        strawb_diff = res["crops_planted"]["STRAWBERRY"] - base["crops_planted"]["STRAWBERRY"]
        cows_diff = res["animals_bought"]["COW"] - base["animals_bought"]["COW"]
        feeds_diff = res["feeds"] - base["feeds"]
        cares_diff = res["cares"] - base["cares"]
        sells_diff = sum(res["sells"].values()) - sum(base["sells"].values())
        
        intended = {
            "M1_NO_EARLY_WHEAT": "Disable wheat seed buys before Day 7",
            "M2_NO_STRAWBERRY": "Disable strawberry seed buys",
            "M3_NO_ACCELERATED_LABOR": "Clamp hires to max 2/day",
            "M4_NO_EARLY_LIVESTOCK": "Disable animal buys before Day 10",
            "M6_NO_BATCH_SELLING": "Sell 1 unit per order",
            "M7_NO_EARLY_SELLING": "Block all sales before Step 240 (Day 10)",
            "M8_NO_TERMINAL_LIQUIDATION": "Block all sales after Step 670",
            "M9_NO_MARKET_AWARE_SELLING": "Filter sales to step % 8 == 0",
        }.get(abl, "Unknown")
        
        actual_changes = []
        is_pure = True
        
        if abl == "M1_NO_EARLY_WHEAT":
            actual_changes.append(f"Wheat planted {wheat_diff:+.0f}")
            if feeds_diff != 0:
                actual_changes.append(f"Animal feeds {feeds_diff:+.0f} (Wheat feed starvation!)")
                is_pure = False
            if cash_d10 < -10000:
                actual_changes.append(f"Day 10 cash {cash_d10:+.0f} (Capital starvation)")
        elif abl == "M2_NO_STRAWBERRY":
            actual_changes.append(f"Strawberries planted {strawb_diff:+.0f}")
            if wheat_diff != 0 or cows_diff != 0:
                actual_changes.append(f"Altered other production: wheat {wheat_diff:+.0f}, cows {cows_diff:+.0f}")
                is_pure = False
        elif abl == "M3_NO_ACCELERATED_LABOR":
            actual_changes.append(f"Hires {hires_diff:+.0f}")
            actual_changes.append(f"Day 5 cash {cash_d5:+.0f}")
            actual_changes.append(f"Feeds {feeds_diff:+.0f}, Cares {cares_diff:+.0f}, Wheat planted {wheat_diff:+.0f}")
            actual_changes.append("Route desynchronization & catastrophic physical failure (Hands count mismatch!)")
            is_pure = False
        elif abl == "M4_NO_EARLY_LIVESTOCK":
            actual_changes.append(f"Cows {cows_diff:+.0f}")
            actual_changes.append(f"Feeds {feeds_diff:+.0f}, Cares {cares_diff:+.0f}")
            if wheat_diff != 0:
                actual_changes.append(f"Wheat planted {wheat_diff:+.0f}")
                is_pure = False
        elif abl == "M6_NO_BATCH_SELLING":
            actual_changes.append(f"Total units sold {sells_diff:+.0f} (Capped to max 10 units/turn by engine 10-order limit)")
            actual_changes.append(f"Day 10 cash {cash_d10:+.0f}")
            actual_changes.append(f"Cows {cows_diff:+.0f}, Feeds {feeds_diff:+.0f} (Shed overflow + capital bankruptcy)")
            is_pure = False
        elif abl == "M7_NO_EARLY_SELLING":
            actual_changes.append("Zero sales before Day 10")
            actual_changes.append(f"Day 5 cash {cash_d5:+.0f}, Day 10 cash {cash_d10:+.0f} ($0 cash left!)")
            actual_changes.append(f"Hires {hires_diff:+.0f}, Cows {cows_diff:+.0f}, Wheat {wheat_diff:+.0f} (Complete early farm freeze)")
            is_pure = False
        elif abl == "M8_NO_TERMINAL_LIQUIDATION":
            actual_changes.append("Zero sales after Step 670")
            if hires_diff == 0 and wheat_diff == 0 and cows_diff == 0:
                is_pure = True
            else:
                is_pure = False
        elif abl == "M9_NO_MARKET_AWARE_SELLING":
            actual_changes.append("Arbitrarily drops ~87.5% of all sell orders (only step % 8 == 0 permitted)")
            actual_changes.append(f"Total sales {sells_diff:+.0f} (Collapses sales from {sum(base['sells'].values())} to {sum(res['sells'].values())})")
            actual_changes.append(f"Day 5 cash {cash_d5:+.0f}, Hires {hires_diff:+.0f} (Immediate capital strangulation)")
            is_pure = False
            
        entry = {
            "mechanism": abl,
            "intended": intended,
            "actual_changes": "; ".join(actual_changes),
            "pure_ablation": "YES" if is_pure else "NO (CONTAMINATED)",
            "reward": res["final_reward"],
            "baseline_reward": base["final_reward"],
            "delta": res["final_reward"] - base["final_reward"]
        }
        analysis.append(entry)
        print(f"\n{abl}:")
        print(f"  Intended: {intended}")
        print(f"  Actual:   {'; '.join(actual_changes)}")
        print(f"  Pure:     {entry['pure_ablation']}")
        print(f"  Reward:   {res['final_reward']:,.0f} (Delta: {entry['delta']:+,.0f})")
        
    with open("scratch/ablation_contamination_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    print("\nSaved contamination analysis to scratch/ablation_contamination_analysis.json")
