import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1, CROPS_DEF
import candidates.slot2_aethel_refined_v2 as v2_mod

def audit_v2_terminal_wheat_deep(seeds=list(range(1000, 1010))):
    print("Forensic reconstruction of V2's terminal wheat wave across Seeds 1000-1009...")
    
    v2_term_wheat = []
    
    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([v2_mod.agent, "starter"])
        steps = env.steps
        
        # Track Day 26-29 wheat plantings
        active_tw = {}
        for step_idx in range(1, len(steps)):
            day = step_idx // 24
            hour = step_idx % 24
            prev_f = steps[step_idx - 1][0]["observation"]["farms"][0]
            act = steps[step_idx][0].get("action") or {}
            all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
            workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
            tiles = prev_f["tiles"]
            
            for w_idx, a in enumerate(all_acts):
                if not a: continue
                op = a[0]
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                x, y = pos
                
                if op == "PLANT" and len(a) > 1 and a[1] == "WHEAT" and day >= 25:
                    prev_tile = tiles[y][x]
                    prev_k = prev_tile.get("kind") if isinstance(prev_tile, dict) else "EMPTY"
                    rec = {
                        "seed": s,
                        "step": step_idx,
                        "day": day,
                        "hour": hour,
                        "coord": (x, y),
                        "prev_kind": prev_k,
                        "waters": 0,
                        "harvested_yield": 0,
                        "harvest_step": None,
                        "final_yield_on_tile": 0
                    }
                    active_tw[(x, y)] = rec
                    v2_term_wheat.append(rec)
                    
                elif op == "WATER":
                    if pos in active_tw:
                        active_tw[pos]["waters"] += 1
                        
                elif op == "HARVEST":
                    t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
                    if isinstance(t, dict) and t.get("crop") == "WHEAT" and pos in active_tw:
                        yu = int(t.get("yield_units", 0) or 0)
                        active_tw[pos]["harvested_yield"] += yu
                        active_tw[pos]["harvest_step"] = step_idx

        final_tiles = steps[-1][0]["observation"]["farms"][0]["tiles"]
        for coord, rec in active_tw.items():
            x, y = coord
            ft = final_tiles[y][x]
            rec["final_yield_on_tile"] = int(ft.get("yield_units", 0) or 0) if isinstance(ft, dict) else 0

    return v2_term_wheat

# Clean Isolated Terminal Wheat Intervention on CL-Economic-V1
class CLTerminalWheatAgent(ClosedLoopEconomicV1):
    def __init__(self, terminal_wheat_wave=True):
        super().__init__()
        self.terminal_wheat_wave = terminal_wheat_wave

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        # Day 26 Terminal Wheat Burst: Procure up to 15 wheat seeds on Day 26 if money >= 200
        if self.terminal_wheat_wave and day == 26 and hour in (0, 1) and len(orders) < 10:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 15 and money >= 200:
                can_buy_w = min(15 - wheat_s, min(10, int((money - 100) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
        return orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, all_invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, all_invs, day)
        
        # Day 26 Terminal Wheat Wave: On Day 26, allow planting wheat on ANY vacant tile!
        if self.terminal_wheat_wave and day == 26:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s > 0:
                vacant = []
                for y in range(10):
                    for x in range(10):
                        if tiles[y][x] is None and (x, y) not in res["unbuilt_p"]:
                            vacant.append((x, y))
                res["plant_w"].extend(vacant)
        return res

def run_counterfactual_terminal_wheat(args):
    arm, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    if arm == "BASELINE":
        agent_inst = ClosedLoopEconomicV1()
    elif arm == "TERMINAL_WHEAT":
        agent_inst = CLTerminalWheatAgent(terminal_wheat_wave=True)
    else:
        raise ValueError(f"Unknown {arm}")
        
    env.run([agent_inst, "starter"])
    steps = env.steps
    total_steps = len(steps)
    
    harvest_counts = Counter()
    total_harvs = 0
    total_plants = 0
    total_moves = 0
    total_waters = 0
    wheat_plants_d26 = 0
    
    for s_idx in range(1, total_steps):
        day = s_idx // 24
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        
        for w_idx, a in enumerate(all_acts):
            if not a: continue
            op = a[0]
            if op == "HARVEST":
                total_harvs += 1
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    yu = int(t.get("yield_units", 0) or 0)
                    if t.get("kind") == "PLANT": harvest_counts[t.get("crop")] += yu
                    elif t.get("kind") == "PASTURE": harvest_counts[t.get("animal")] += yu
            elif op == "PLANT":
                total_plants += 1
                if len(a) > 1 and a[1] == "WHEAT" and day >= 25:
                    wheat_plants_d26 += 1
            elif op == "WATER":
                total_waters += 1
            elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    terminal_cash = float(steps[-1][0]["observation"]["farms"][0].get("money") or 0.0)
    
    return {
        "arm": arm,
        "seed": seed,
        "reward": reward,
        "terminal_cash": terminal_cash,
        "harvests": total_harvs,
        "plants": total_plants,
        "wheat_plants_d26": wheat_plants_d26,
        "waters": total_waters,
        "moves": total_moves,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "melon": harvest_counts.get("MELON", 0),
        "milk": harvest_counts.get("COW", 0)
    }

if __name__ == "__main__":
    # 1. Forensic V2 Terminal Wheat
    v2_tw = audit_v2_terminal_wheat_deep()
    
    print("\n" + "="*80)
    print("SECTION 10, 11, 12: V2 TERMINAL WHEAT FORENSIC AUDIT")
    print("="*80)
    print(f"Total V2 Day 25+ Wheat Plantings across 10 seeds: {len(v2_tw)} (Mean: {len(v2_tw)/10:.1f} per run)")
    
    plant_days = [x["day"] for x in v2_tw]
    print(f"Plant Days distribution: {dict(sorted(Counter(plant_days).items()))}")
    
    harvested = [x for x in v2_tw if x["harvested_yield"] > 0]
    unharvested = [x for x in v2_tw if x["harvested_yield"] == 0]
    total_yield = sum(x["harvested_yield"] for x in v2_tw)
    leftover_yield = sum(x["final_yield_on_tile"] for x in v2_tw)
    
    print(f"Total plots harvested before Step 720: {len(harvested)} ({len(harvested)/len(v2_tw)*100:.1f}%)")
    print(f"Total unharvested plots: {len(unharvested)} ({len(unharvested)/len(v2_tw)*100:.1f}%)")
    print(f"Total wheat yield units harvested: {total_yield} units (Mean: {total_yield/10:.1f}u)")
    print(f"Total unharvested yield stranded on tiles at Step 719: {leftover_yield} units")
    
    # Check harvest steps:
    h_steps = [x["harvest_step"] for x in harvested if x["harvest_step"] is not None]
    if h_steps:
        print(f"Harvest step range: min {min(h_steps)} (Day {min(h_steps)//24}), max {max(h_steps)} (Day {max(h_steps)//24})")
    
    # 2. Counterfactual Intervention Study
    seeds = list(range(1000, 1010))
    tasks = [(arm, s) for arm in ("BASELINE", "TERMINAL_WHEAT") for s in seeds]
    
    print(f"\nRunning Isolated Terminal Wheat Intervention ({len(tasks)} matches)...")
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_counterfactual_terminal_wheat, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["arm"]].append(res)
            
    with open("scratch/audit_terminal_wheat_results.json", "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2)
        
    print("\n" + "="*105)
    print(f"{'ARM':<18} | {'Reward ($)':<16} | {'Delta ($)':<12} | {'Wheat (u)':<10} | {'D26 Wheat Plants':<18} | {'Straw (u)':<10} | {'Moves':<8}")
    print("-" * 105)
    
    base_rew = np.mean([x["reward"] for x in results["BASELINE"]])
    for arm in ("BASELINE", "TERMINAL_WHEAT"):
        lst = results[arm]
        lst.sort(key=lambda x: x["seed"])
        rews = [x["reward"] for x in lst]
        m_rew = float(np.mean(rews))
        std_rew = float(np.std(rews))
        ci95 = 1.96 * std_rew / np.sqrt(len(rews))
        m_wheat = float(np.mean([x["wheat"] for x in lst]))
        m_d26 = float(np.mean([x["wheat_plants_d26"] for x in lst]))
        m_straw = float(np.mean([x["straw"] for x in lst]))
        m_moves = float(np.mean([x["moves"] for x in lst]))
        delta = m_rew - base_rew
        print(f"{arm:<18} | ${m_rew:10.2f} ± ${ci95:5.0f} | {delta:+10.2f} | {m_wheat:10.1f} | {m_d26:18.1f} | {m_straw:10.1f} | {m_moves:8.1f}")
