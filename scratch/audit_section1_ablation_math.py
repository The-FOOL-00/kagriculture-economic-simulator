"""
Audit Section 1 & Section 2: Exact Per-Seed Ablation Re-run and Statistical Audit
Re-runs the 9 ablations on seeds 2000-2019 against IDLE, V54, and V66.
Computes comprehensive paired statistical distributions, tests, and flags invalid metrics.
"""
import sys, os, json, csv, statistics, importlib.util
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

def _run_single_match(task):
    ablation_id, opp_name, seed = task
    from kaggle_environments import make
    
    # Load V54
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
    agent_fn = raw_v54 if ablation_id == "BASELINE" else ablated_agent
    env.run([agent_fn, opp_fn])
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

def bootstrap_ci(diffs, n_boot=10000, ci=0.95):
    if len(diffs) == 0: return (0.0, 0.0)
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(means, alpha * 100)), float(np.percentile(means, (1.0 - alpha) * 100))

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    raw_cache_file = "scratch/ablation_raw_per_seed.json"
    
    if os.path.exists(raw_cache_file):
        print(f"Loading cached raw results from {raw_cache_file}...")
        with open(raw_cache_file, "r") as f:
            raw_results = json.load(f)
    else:
        tasks = []
        for abl in ABLATIONS:
            for opp in OPPONENTS:
                for seed in SEEDS:
                    tasks.append((abl, opp, seed))
        print(f"Executing {len(tasks)} matches across 8 workers...")
        raw_results = defaultdict(lambda: defaultdict(dict))
        with ProcessPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_run_single_match, t) for t in tasks]
            done = 0
            for f in as_completed(futures):
                abl, opp, seed, r0, r1 = f.result()
                raw_results[abl][opp][str(seed)] = {"r0": r0, "r1": r1}
                done += 1
                if done % 50 == 0:
                    print(f"  ... {done}/{len(tasks)} completed")
        with open(raw_cache_file, "w") as f:
            json.dump(raw_results, f, indent=2)
        print(f"Saved raw results to {raw_cache_file}")
        
    print("\n" + "="*80)
    print("SECTION 1 & 2: COMPREHENSIVE STATISTICAL AUDIT TABLE")
    print("="*80)
    
    # Analyze per opponent
    audit_tables = {}
    for opp in OPPONENTS:
        print(f"\n--- OPPONENT: {opp} ---")
        base_seeds = raw_results["BASELINE"][opp]
        
        opp_table = []
        for abl in ABLATIONS:
            abl_seeds = raw_results[abl][opp]
            
            seeds = sorted([int(s) for s in base_seeds.keys()])
            base_r0 = np.array([base_seeds[str(s)]["r0"] for s in seeds])
            abl_r0  = np.array([abl_seeds[str(s)]["r0"] for s in seeds])
            abl_r1  = np.array([abl_seeds[str(s)]["r1"] for s in seeds])
            
            diffs = abl_r0 - base_r0  # Paired per-seed delta
            
            mean_base = float(np.mean(base_r0))
            mean_abl  = float(np.mean(abl_r0))
            mean_diff = float(np.mean(diffs))
            median_diff = float(np.median(diffs))
            std_diff = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
            
            ci_low, ci_high = bootstrap_ci(diffs)
            
            # Paired t-test
            if np.all(diffs == 0):
                t_stat, p_val_t = 0.0, 1.0
                w_stat, p_val_w = 0.0, 1.0
            else:
                t_stat, p_val_t = stats.ttest_rel(abl_r0, base_r0)
                try:
                    w_res = stats.wilcoxon(diffs)
                    w_stat, p_val_w = w_res.statistic, w_res.pvalue
                except Exception:
                    w_stat, p_val_w = 0.0, 1.0
                    
            wins = int(np.sum(abl_r0 > abl_r1))
            ties = int(np.sum(abl_r0 == abl_r1))
            losses = int(np.sum(abl_r0 < abl_r1))
            win_rate = wins / len(seeds)
            
            p5 = float(np.percentile(diffs, 5))
            p95 = float(np.percentile(diffs, 95))
            worst_loss = float(np.min(diffs))
            
            p_lt_1000 = float(np.mean(diffs < -1000))
            p_gt_1000 = float(np.mean(diffs > 1000))
            
            # Metric validity assessment
            # Formula in previous report was: mean(abl) - mean(base), which equals mean(paired delta).
            # But the claim attributed IDLE delta to competitive value!
            if abl in ["M3_NO_ACCELERATED_LABOR", "M7_NO_EARLY_SELLING", "M9_NO_MARKET_AWARE_SELLING", "M6_NO_BATCH_SELLING"]:
                formula_str = "mean(abl) - mean(base) [PAIRED]"
                if opp == "IDLE":
                    validity = "VALID MATH / MISLEADING ATTRIBUTION (Episode collapse)"
                else:
                    validity = "VALID COMPUTATION (True competitive impact)"
            elif abl == "BASELINE":
                formula_str = "N/A"
                validity = "BASELINE"
            else:
                formula_str = "mean(abl) - mean(base) [PAIRED]"
                validity = "VALID"
                
            row = {
                "mechanism": abl,
                "opponent": opp,
                "baseline_mean": mean_base,
                "ablation_mean": mean_abl,
                "paired_delta_mean": mean_diff,
                "median_delta": median_diff,
                "std_delta": std_diff,
                "ci_95": (ci_low, ci_high),
                "p_val_t": float(p_val_t),
                "p_val_w": float(p_val_w),
                "win_rate": win_rate,
                "record": f"{wins}W-{ties}T-{losses}L",
                "n": len(seeds),
                "p5": p5,
                "p95": p95,
                "worst_loss": worst_loss,
                "p_lt_1000": p_lt_1000,
                "p_gt_1000": p_gt_1000,
                "formula": formula_str,
                "validity": validity
            }
            opp_table.append(row)
            
            print(f"{abl:26s} | Base: {mean_base:7.0f} | Abl: {mean_abl:7.0f} | Delta Mean: {mean_diff:+8.0f} | Median: {median_diff:+8.0f} | 95% CI: [{ci_low:+8.0f}, {ci_high:+8.0f}] | p(t)={p_val_t:.3e} | p(W)={p_val_w:.3e} | Win: {win_rate:.0%} | Worst: {worst_loss:+8.0f}")
            
        audit_tables[opp] = opp_table
        
    # Save full audit results
    with open("scratch/ablation_audit_statistical_tables.json", "w") as f:
        json.dump(audit_tables, f, indent=2)
    print("\nSaved comprehensive statistics to scratch/ablation_audit_statistical_tables.json")
