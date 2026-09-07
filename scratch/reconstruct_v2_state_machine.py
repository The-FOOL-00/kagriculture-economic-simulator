import sys, os
sys.path.insert(0, os.path.abspath('.'))
import json
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_aethel_prime import agent as prime_agent

def extract_timeline(agent_fn, agent_name, seed=42):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    starter_fn = kaggle_environments.environments['kaggriculture']['agents']['starter']
    env.run([agent_fn, starter_fn])
    
    milestones = [0, 23, 95, 119, 167, 239, 263, 359, 479, 599, 711, 719]
    timeline = []
    
    for step in milestones:
        obs = env.steps[step][0]['observation']
        farm = obs['farms'][0]
        priv = obs['private']
        tiles = farm['tiles']
        
        day = step // 24
        hour = step % 24
        money = farm['money']
        quads = farm['unlocked_quadrants']
        hands = len(farm.get('hands', []))
        total_workers = hands + 1
        
        # Count crops
        crop_counts = {}
        pasture_count = 0
        cow_count = 0
        sheep_count = 0
        weed_count = 0
        
        for row in tiles:
            for t in row:
                if isinstance(t, dict):
                    k = t.get('kind')
                    if k == 'PLANT':
                        c = t.get('crop')
                        crop_counts[c] = crop_counts.get(c, 0) + 1
                    elif k == 'PASTURE':
                        pasture_count += 1
                        an = t.get('animal')
                        if an == 'COW': cow_count += 1
                        elif an == 'SHEEP': sheep_count += 1
                    elif k == 'WEED':
                        weed_count += 1
                        
        shed = priv.get('shed', {})
        seeds = priv.get('seeds', {})
        
        # Count productive vs move actions up to this step
        move_cnt = 0
        prod_cnt = 0
        for s in range(1, step + 1):
            act = env.steps[s][0]['action']
            units = [act.get('farmer', ['PASS'])] + (act.get('hands', []) if isinstance(act, dict) else [])
            for u in units:
                if not u: continue
                op = u[0] if isinstance(u, (list, tuple)) else str(u)
                if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    move_cnt += 1
                elif op != "PASS":
                    prod_cnt += 1
                    
        entry = {
            "step": step,
            "day": day,
            "hour": hour,
            "money": round(money, 1),
            "quads": list(quads),
            "workers": total_workers,
            "pastures": pasture_count,
            "cows": cow_count,
            "sheep": sheep_count,
            "crops": crop_counts,
            "weeds": weed_count,
            "shed_wheat": shed.get('WHEAT', 0),
            "shed_milk": shed.get('MILK', 0),
            "shed_wool": shed.get('WOOL', 0),
            "shed_melon": shed.get('MELON', 0),
            "shed_straw": shed.get('STRAWBERRY', 0),
            "seeds": seeds,
            "prod_actions": prod_cnt,
            "move_actions": move_cnt,
            "prod_ratio": round(prod_cnt / max(1, prod_cnt + move_cnt), 3)
        }
        timeline.append(entry)
        
    return timeline

if __name__ == '__main__':
    v2_time = extract_timeline(v2_agent, "V2 Baseline", 42)
    prime_time = extract_timeline(prime_agent, "CL-Aethel Prime", 42)
    
    print("="*100)
    print("PHASE 2: V2 vs PRIME STATE TRANSITION TIMELINE (SEED 42)")
    print("="*100)
    for v2_e, p_e in zip(v2_time, prime_time):
        s = v2_e['step']
        d = v2_e['day']
        h = v2_e['hour']
        print(f"\n--- STEP {s:3d} (DAY {d:02d} HOUR {h:02d}) ---")
        print(f"  V2:    Cash=${v2_e['money']:>8,.1f} | Workers={v2_e['workers']:>2} | Quads={v2_e['quads']} | Cows={v2_e['cows']} | Sheep={v2_e['sheep']} | Pastures={v2_e['pastures']} | Crops={v2_e['crops']} | Weeds={v2_e['weeds']} | ProdRatio={v2_e['prod_ratio']:.1%}")
        print(f"  Prime: Cash=${p_e['money']:>8,.1f} | Workers={p_e['workers']:>2} | Quads={p_e['quads']} | Cows={p_e['cows']} | Sheep={p_e['sheep']} | Pastures={p_e['pastures']} | Crops={p_e['crops']} | Weeds={p_e['weeds']} | ProdRatio={p_e['prod_ratio']:.1%}")
        print(f"  Shed Wheat: V2={v2_e['shed_wheat']} vs Prime={p_e['shed_wheat']} | Shed Melon: V2={v2_e['shed_melon']} vs Prime={p_e['shed_melon']}")
        
    with open("scratch/v2_state_machine_timeline.json", "w") as f:
        json.dump({"v2": v2_time, "prime": prime_time}, f, indent=2)
    print("\nSaved timeline to scratch/v2_state_machine_timeline.json")
