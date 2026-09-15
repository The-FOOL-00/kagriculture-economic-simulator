"""
scratch/census_phase3_500seeds.py
Phase 3: Verify the shop-state distribution on 500 fresh seeds (seeds 50000..50499).
Parallelized execution via ProcessPoolExecutor.
Records:
- first shop, second shop, first-two-shop pair, third shop
- shop pair frequency
- Dmitrii route selected vs generic fallback Plan 0
- Final cash of Dmitrii under Plan 0 vs Specialized Route
- Quantifies expected cash gap across shop states
"""
import collections
from concurrent.futures import ProcessPoolExecutor, as_completed
import importlib.util
import json
import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

from router_parent import SHOP_PLANS

SHOPS = [
    "BAKERY", "BRUNCH_SPOT", "FARMERS_MARKET", "ICE_CREAM_SHOP",
    "PET_CAFE", "PIZZA_SHOP", "SMOOTHIE_SHOP", "YARN_STORE"
]

def simulate_seed(seed):
    import sys, os, importlib.util
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, BASE_DIR)
    sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
    sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
    sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    import kagsim
    import compiled_v54_plus_residual
    from router_parent import SHOP_PLANS
    
    spec = importlib.util.spec_from_file_location(f"dmitrii_{seed}", os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = mod.agent(o0)
        a1 = compiled_v54_plus_residual.agent(o1)
        game.step(a0, a1)
        
    r0 = float(game.reward(0))
    r1 = float(game.reward(1))
    
    obs = game.observe(0)
    unlocked = obs["town"]["unlocked_shops"]
    s0 = unlocked[0] if len(unlocked) > 0 else "NONE"
    s1 = unlocked[1] if len(unlocked) > 1 else "NONE"
    s2 = unlocked[2] if len(unlocked) > 2 else "NONE"
    pair = (s0, s1)
    plan = SHOP_PLANS.get(pair, 0)
    
    return {
        "seed": seed,
        "s0": s0,
        "s1": s1,
        "s2": s2,
        "pair": pair,
        "plan": plan,
        "r0": r0,
        "r1": r1
    }

def main():
    num_seeds = 500
    start_seed = 50000
    seeds = list(range(start_seed, start_seed + num_seeds))
    print(f"Starting Phase 3 Census on {num_seeds} seeds ({start_seed}..{start_seed+num_seeds-1}) using 8 parallel processes...")
    t0 = time.time()
    
    pair_counts = collections.Counter()
    first_shop_counts = collections.Counter()
    second_shop_counts = collections.Counter()
    third_shop_counts = collections.Counter()
    route_counts = collections.Counter()
    
    pair_dmitrii_cash = collections.defaultdict(list)
    pair_opp_cash = collections.defaultdict(list)
    plan_dmitrii_cash = collections.defaultdict(list)
    
    yarn_seeds = 0
    non_yarn_seeds = 0
    
    results = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(simulate_seed, s): s for s in seeds}
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            completed += 1
            if completed % 100 == 0:
                print(f"  [{completed}/{num_seeds}] matches completed ({time.time()-t0:.1f}s)...")
                
    for res in results:
        s0, s1, s2 = res["s0"], res["s1"], res["s2"]
        pair = res["pair"]
        plan = res["plan"]
        r0 = res["r0"]
        r1 = res["r1"]
        
        first_shop_counts[s0] += 1
        second_shop_counts[s1] += 1
        third_shop_counts[s2] += 1
        pair_counts[pair] += 1
        route_counts[plan] += 1
        
        is_yarn = (s0 == "YARN_STORE" or s1 == "YARN_STORE")
        if is_yarn: yarn_seeds += 1
        else: non_yarn_seeds += 1
        
        pair_dmitrii_cash[pair].append(r0)
        pair_opp_cash[pair].append(r1)
        plan_dmitrii_cash[plan].append(r0)
        
    elapsed = time.time() - t0
    
    # Statistical summary
    print("\n" + "="*80)
    print(f"PHASE 3 SHOP-STATE CENSUS RESULTS (N={num_seeds} seeds)")
    print("="*80)
    print(f"Total Seeds Evaluated: {num_seeds} in {elapsed:.1f}s ({num_seeds/elapsed:.1f} games/s)")
    print(f"Yarn Seeds (>=1 Yarn in first 2 shops): {yarn_seeds} ({yarn_seeds/num_seeds*100:.2f}%)")
    print(f"Non-Yarn Seeds (Generic Fallback):     {non_yarn_seeds} ({non_yarn_seeds/num_seeds*100:.2f}%)")
    print(f"Theoretical P(Yarn):                   {15/64*100:.2f}% (15/64 = 23.44%)")
    print(f"Theoretical P(Non-Yarn):               {49/64*100:.2f}% (49/64 = 76.56%)")
    
    print("\n--- DMITRII ROUTE SELECTION FREQUENCY & MEAN CASH ---")
    print(f"{'Plan':6} | {'Count':6} | {'Freq (%)':9} | {'Mean Cash':11} | {'Min Cash':10} | {'Max Cash':10} | Description")
    print("-" * 75)
    for plan in sorted(route_counts.keys()):
        cnt = route_counts[plan]
        cashes = plan_dmitrii_cash[plan]
        mean_c = sum(cashes)/len(cashes) if cashes else 0
        min_c = min(cashes) if cashes else 0
        max_c = max(cashes) if cashes else 0
        desc = "Generic Fallback Plan 0" if plan == 0 else f"Specialized Route Plan {plan}"
        print(f"{plan:6d} | {cnt:6d} | {cnt/num_seeds*100:8.2f}% | ${mean_c:10,.2f} | ${min_c:9,.2f} | ${max_c:9,.2f} | {desc}")
        
    p0_cashes = plan_dmitrii_cash[0]
    yarn_cashes = [c for p, cs in plan_dmitrii_cash.items() if p != 0 for c in cs]
    mean_p0 = sum(p0_cashes)/len(p0_cashes) if p0_cashes else 0
    mean_yarn = sum(yarn_cashes)/len(yarn_cashes) if yarn_cashes else 0
    
    print("-" * 75)
    print(f"Plan 0 (Non-Yarn Fallback) Mean Cash : ${mean_p0:,.2f} (N={len(p0_cashes)})")
    print(f"Specialized Yarn Routes Mean Cash   : ${mean_yarn:,.2f} (N={len(yarn_cashes)})")
    print(f"Observed Realized Cash Gap          : {mean_yarn - mean_p0:+,.2f}")
    
    print("\n--- TOP 20 SHOP PAIRS BY FREQUENCY ---")
    print(f"{'Shop 0':18} | {'Shop 1':18} | {'Count':6} | {'Freq (%)':9} | {'Plan':5} | {'Dmitrii Mean':12} | {'Opp Mean':10}")
    print("-" * 85)
    for pair, cnt in pair_counts.most_common(20):
        cashes_d = pair_dmitrii_cash[pair]
        cashes_o = pair_opp_cash[pair]
        m_d = sum(cashes_d)/len(cashes_d)
        m_o = sum(cashes_o)/len(cashes_o)
        plan = SHOP_PLANS.get(pair, 0)
        print(f"{pair[0]:18} | {pair[1]:18} | {cnt:6d} | {cnt/num_seeds*100:8.2f}% | {plan:5d} | ${m_d:10,.2f} | ${m_o:9,.2f}")
        
    census_data = {
        "num_seeds": num_seeds,
        "yarn_seeds": yarn_seeds,
        "non_yarn_seeds": non_yarn_seeds,
        "yarn_pct": yarn_seeds / num_seeds,
        "non_yarn_pct": non_yarn_seeds / num_seeds,
        "mean_p0_cash": mean_p0,
        "mean_yarn_cash": mean_yarn,
        "observed_cash_gap": mean_yarn - mean_p0,
        "route_counts": dict(route_counts),
        "pair_counts": {f"{k[0]}|{k[1]}": v for k, v in pair_counts.items()},
        "pair_dmitrii_mean": {f"{k[0]}|{k[1]}": sum(v)/len(v) for k, v in pair_dmitrii_cash.items()}
    }
    
    out_path = os.path.join(BASE_DIR, "results", "phase3_shop_census_500seeds.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(census_data, f, indent=2)
    print(f"\nCensus written to {out_path}")

if __name__ == "__main__":
    main()
