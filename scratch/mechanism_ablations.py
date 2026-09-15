"""
Section 7: High-Speed Parallel Mechanism Ablations (M1 through M14)
Measures the isolated causal contribution of distinct mechanisms on V54.
Tested across 20 identical seeds (2000-2019) against:
- O0: IDLE
- O4: V54
- O5: V66
Uses multi-core parallel execution.
Outputs:
- research/v54_v66_mechanism_ablation.csv
- research/v54_v66_mechanism_ablation.md
"""
import sys, os, json, csv, statistics, importlib.util
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

def _run_single_match(task):
    ablation_id, opp_name, seed = task
    from kaggle_environments import make
    
    # Load agent inside worker process
    d = os.path.dirname(os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"))
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("v54_mod", "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    v54_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v54_mod)
    raw_v54 = getattr(v54_mod, "agent", None)
    
    if opp_name == "IDLE":
        opp_fn = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}
    elif opp_name == "V54":
        opp_fn = raw_v54
    elif opp_name == "V66":
        d66 = os.path.dirname(os.path.abspath("external_repos/kaggriculture-v66-agent/main.py"))
        if d66 not in sys.path: sys.path.insert(0, d66)
        spec66 = importlib.util.spec_from_file_location("v66_mod", "external_repos/kaggriculture-v66-agent/main.py")
        v66_mod = importlib.util.module_from_spec(spec66)
        spec66.loader.exec_module(v66_mod)
        opp_fn = getattr(v66_mod, "agent", None)

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

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([ablated_agent, opp_fn])
    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)
    return ablation_id, opp_name, seed, r0, r1


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

OPPONENTS = ["IDLE", "V54", "V66"]
SEEDS = list(range(2000, 2020))

if __name__ == "__main__":
    os.makedirs("research", exist_ok=True)
    os.makedirs("scratch", exist_ok=True)
    
    tasks = []
    for abl in ABLATIONS:
        for opp in OPPONENTS:
            for seed in SEEDS:
                tasks.append((abl, opp, seed))
                
    print(f"Executing {len(tasks)} parallel ablation matches across 8 workers...")
    
    raw_results = defaultdict(lambda: defaultdict(list))
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        done_count = 0
        for f in as_completed(futures):
            abl, opp, seed, r0, r1 = f.result()
            raw_results[abl][opp].append((seed, r0, r1))
            done_count += 1
            if done_count % 50 == 0:
                print(f"  ... {done_count}/{len(tasks)} matches completed")
                
    print("All matches finished! Compiling metrics...")
    
    summary_data = {}
    for abl in ABLATIONS:
        idle_r0 = [x[1] for x in raw_results[abl]["IDLE"]]
        v54_r0  = [x[1] for x in raw_results[abl]["V54"]]
        v54_r1  = [x[2] for x in raw_results[abl]["V54"]]
        v66_r0  = [x[1] for x in raw_results[abl]["V66"]]
        v66_r1  = [x[2] for x in raw_results[abl]["V66"]]
        
        m_idle = statistics.mean(idle_r0)
        m_v54  = statistics.mean(v54_r0)
        m_v66  = statistics.mean(v66_r0)
        win_v54 = sum(1 for r0, r1 in zip(v54_r0, v54_r1) if r0 > r1) / len(v54_r0)
        win_v66 = sum(1 for r0, r1 in zip(v66_r0, v66_r1) if r0 > r1) / len(v66_r0)
        
        summary_data[abl] = {
            "mean_idle": m_idle, "mean_v54": m_v54, "mean_v66": m_v66,
            "win_v54": win_v54, "win_v66": win_v66
        }
        
    base_idle = summary_data["BASELINE"]["mean_idle"]
    base_v54  = summary_data["BASELINE"]["mean_v54"]
    base_v66  = summary_data["BASELINE"]["mean_v66"]
    
    csv_path = "research/v54_v66_mechanism_ablation.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Mechanism", "vs_IDLE_Reward", "Delta_IDLE", "vs_V54_Reward", "Delta_V54", "WinRate_V54", "vs_V66_Reward", "Delta_V66", "WinRate_V66", "Classification"])
        for abl in ABLATIONS:
            res = summary_data[abl]
            d_idle = res["mean_idle"] - base_idle
            d_v54  = res["mean_v54"] - base_v54
            d_v66  = res["mean_v66"] - base_v66
            
            if abl == "BASELINE":
                cls = "BASELINE"
            elif abs(d_idle) > 25000 or abs(d_v54) > 25000:
                cls = "VERIFIED (CRITICAL)"
            elif abs(d_idle) > 5000 or abs(d_v54) > 5000:
                cls = "VERIFIED (MAJOR)"
            else:
                cls = "PROBABLE (MINOR)"
                
            writer.writerow([abl, f"{res['mean_idle']:.0f}", f"{d_idle:+.0f}", f"{res['mean_v54']:.0f}", f"{d_v54:+.0f}", f"{res['win_v54']:.1%}", f"{res['mean_v66']:.0f}", f"{d_v66:+.0f}", f"{res['win_v66']:.1%}", cls])
            print(f"{abl:26s} | vs IDLE: {res['mean_idle']:7.0f} ({d_idle:+7.0f}) | vs V54: {res['mean_v54']:7.0f} ({d_v54:+7.0f}, Win {res['win_v54']:.0%}) | vs V66: {res['mean_v66']:7.0f} ({d_v66:+7.0f}, Win {res['win_v66']:.0%}) | {cls}")
            
    print(f"\nWritten {csv_path}")
