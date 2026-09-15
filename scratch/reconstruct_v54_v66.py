"""
Reconstruct V54 and V66 Policies Exactly
Captures complete telemetry across 10 fixed validation seeds (2000-2009):
- Labor: hires, active workforce, actions
- Crops: melon, wheat, strawberry, carrot (purchases, plantings, water, harvest)
- Livestock: buy, pickup, place, feed, care, yields
- Market: order-by-order prices, inventory, timing, front-running
- Capital: cash milestones across days
"""
import sys, os, json, importlib.util, statistics
from collections import defaultdict
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

v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
v66_path = "external_repos/kaggriculture-v66-agent/main.py"

def idle_agent(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

SEEDS = list(range(2000, 2010))

def instrument_agent_solo(agent_path, agent_name, seeds):
    agent_fn = load_agent(agent_path)
    telemetry = []
    
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([agent_fn, idle_agent])
        
        # Telemetry containers
        t_data = {
            "agent": agent_name,
            "seed": seed,
            "reward": float(env.steps[-1][0].reward or 0.0),
            "hires_by_day": defaultdict(int),
            "hire_costs_by_day": defaultdict(int),
            "crops_bought": defaultdict(int),
            "crops_planted": defaultdict(int),
            "crops_harvested": defaultdict(int),
            "animals_bought": defaultdict(int),
            "animals_placed": defaultdict(int),
            "feeds": 0,
            "cares": 0,
            "fert_collected": 0,
            "market_orders": [],
            "sales_by_prod": defaultdict(int),
            "sales_rev_by_prod": defaultdict(float),
            "cash_milestones": {},
            "land_unlocked": [],
            "action_type_counts": defaultdict(int),
        }
        
        prev_land = 1
        for step_idx in range(1, len(env.steps)):
            s = env.steps[step_idx]
            obs = s[0].observation
            act = s[0].action or {}
            market = obs.market
            farm = obs.farms[0]
            priv = obs.private
            day = obs.day
            hour = obs.hour
            money = farm["money"]
            
            # Daily cash snapshots
            if hour == 23 or step_idx == 720:
                t_data["cash_milestones"][day] = money
                t_data["hires_by_day"][day] = farm["hires_today"]
                
            # Land unlocks
            curr_land = len(farm["unlocked_quadrants"])
            if curr_land > prev_land:
                t_data["land_unlocked"].append((step_idx, day, curr_land))
                prev_land = curr_land
                
            # Unit actions
            all_units = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            for u in all_units:
                if not u: continue
                op = u[0]
                t_data["action_type_counts"][op] += 1
                if op == "PLANT" and len(u) > 1:
                    t_data["crops_planted"][u[1]] += 1
                elif op == "HARVEST":
                    t_data["crops_harvested"]["TOTAL"] += 1
                elif op == "FEED":
                    t_data["feeds"] += 1
                elif op == "CARE":
                    t_data["cares"] += 1
                elif op == "COLLECT_FERTILIZER":
                    t_data["fert_collected"] += 1
                elif op == "PLACE" and len(u) > 1:
                    t_data["animals_placed"][u[1]] += 1
                    
            # Market orders
            for o in act.get("market", []):
                if not o: continue
                op = o[0]
                if op == "BUY_SEED" and len(o) > 2:
                    t_data["crops_bought"][o[1]] += o[2]
                elif op == "BUY_ANIMAL" and len(o) > 1:
                    t_data["animals_bought"][o[1]] += 1
                elif op == "SELL" and len(o) > 2:
                    prod = o[1]
                    qty = o[2]
                    price = market["prices"].get(prod, 0)
                    t_data["sales_by_prod"][prod] += qty
                    t_data["sales_rev_by_prod"][prod] += qty * price
                    t_data["market_orders"].append({
                        "step": step_idx, "day": day, "hour": hour,
                        "op": op, "prod": prod, "qty": qty,
                        "price": price, "inv_before": market["inventory"].get(prod, 0)
                    })
                    
        telemetry.append(t_data)
        print(f"[{agent_name}] Seed {seed}: Reward={t_data['reward']:,.0f}")
        
    return telemetry

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    os.makedirs("research", exist_ok=True)
    print("Starting exact reconstruction of V54...")
    v54_data = instrument_agent_solo(v54_path, "V54", SEEDS)
    print("\nStarting exact reconstruction of V66...")
    v66_data = instrument_agent_solo(v66_path, "V66", SEEDS)
    
    # Save combined telemetry JSON
    combined = {"V54": v54_data, "V66": v66_data}
    # Convert defaultdicts for clean json dumping
    def clean(obj):
        if isinstance(obj, defaultdict): return dict(obj)
        if isinstance(obj, dict): return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [clean(v) for v in obj]
        return obj
    with open("scratch/v54_v66_telemetry.json", "w") as f:
        json.dump(clean(combined), f, indent=2)
    print("Telemetry written to scratch/v54_v66_telemetry.json")
