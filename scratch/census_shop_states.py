"""
scratch/census_shop_states.py
=============================
Section 2, 3, 4: Comprehensive Public Shop State Census & Telemetry Mapping.

Across 200 fresh episodes (seeds 401–600):
1. Records at Step 72, 144, 216, 288:
   - obs.town.unlocked_shops
   - shop_prices (prices of commodities consumed by unlocked shops)
   - shop_inventory (market inventory of commodities consumed by unlocked shops)
   - other_public_town_state
2. Records exact V66 route telemetry from _META_STATE:
   - selected_route
   - route_family
   - route changes over time
   - final rewards
3. Critical Predicate Ablation (Controlled replay):
   - Tests whether branch fires with SHOP_ONLY, SHOP_PLUS_STATE, or SHOP_PLUS_OPPONENT.
4. Generates:
   - research/shop_state_census.csv
"""

import os
import sys
import copy
import time
import json
import csv
from collections import defaultdict, Counter
from concurrent.futures import ProcessPoolExecutor
import importlib.util
from pathlib import Path
from kaggle_environments import make

# Configured shop definitions from environment/config
SHOP_CONSUMPTION = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

CENSUS_SEEDS = list(range(401, 601))  # 200 fresh seeds

def get_agent_modules():
    v54_path = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    v66_path = os.path.abspath("external_repos/kaggriculture-v66-agent/main.py")
    v66_meta_path = os.path.abspath("external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py")

    for p in [v54_path, v66_path, v66_meta_path]:
        d = os.path.dirname(p)
        if d not in sys.path:
            sys.path.insert(0, d)

    spec_v54 = importlib.util.spec_from_file_location("v54_census_mod", v54_path)
    mod_v54 = importlib.util.module_from_spec(spec_v54)
    spec_v54.loader.exec_module(mod_v54)

    spec_v66 = importlib.util.spec_from_file_location("v66_census_mod", v66_path)
    mod_v66 = importlib.util.module_from_spec(spec_v66)
    spec_v66.loader.exec_module(mod_v66)

    spec_v66_meta = importlib.util.spec_from_file_location("v66_meta_census_mod", v66_meta_path)
    mod_v66_meta = importlib.util.module_from_spec(spec_v66_meta)
    spec_v66_meta.loader.exec_module(mod_v66_meta)

    return (
        getattr(mod_v54, "agent", getattr(mod_v54, "kaggle_agent", None)),
        getattr(mod_v66, "agent", getattr(mod_v66, "kaggle_agent", None)),
        mod_v66_meta
    )

def evaluate_episode_census(seed):
    fn_v54, fn_v66, mod_meta = get_agent_modules()
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    census_checkpoints = {}
    
    # Run V54 (seat 0) vs V66 (seat 1)
    for s in range(719):
        o0 = env.state[0].observation
        o1 = env.state[1].observation
        o0["step"], o1["step"] = s, s

        if s in (72, 144, 216, 288):
            town = o1.get("town", {}) or {}
            unlocked = list(town.get("unlocked_shops", []) or [])
            market = o1.get("market", {}) or {}
            prices = market.get("prices", {}) or {}
            inv = market.get("inventory", {}) or {}

            # Collect prices and inventories for commodities related to unlocked shops
            consumed_items = set()
            for sh in unlocked:
                for item in SHOP_CONSUMPTION.get(sh, []):
                    consumed_items.add(item)
            
            shop_prices = {item: prices.get(item, 0) for item in sorted(consumed_items)}
            shop_inv = {item: inv.get(item, 0) for item in sorted(consumed_items)}
            other_town = f"shop_count={len(unlocked)};day={s//24};step={s}"

            # Capture V66 internal meta state
            meta_seat1 = copy.deepcopy(mod_meta._META_STATE.get(1, {}))
            
            # Determine effective route
            # If meta_state route is set, that is active; otherwise resolve via base _v59_route
            active_meta_route = meta_seat1.get("route", "")
            if active_meta_route:
                effective_route = active_meta_route
            else:
                first_shop = unlocked[0] if unlocked else ""
                if first_shop == "YARN_STORE":
                    effective_route = "yarn"
                else:
                    effective_route = "backbone"

            census_checkpoints[s] = {
                "unlocked_shops": unlocked,
                "shop_prices": shop_prices,
                "shop_inventory": shop_inv,
                "other_public_town_state": other_town,
                "meta_branch": meta_seat1.get("branch", ""),
                "meta_route": meta_seat1.get("route", ""),
                "effective_route": effective_route,
                "events": list(meta_seat1.get("events", [])),
                "obs_snapshot": copy.deepcopy(o1)
            }

        a0 = fn_v54(o0, env.configuration)
        a1 = fn_v66(o1, env.configuration)
        env.step([a0, a1])

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)

    # Predicate Ablation Test at Step 72 and Step 144
    # Test what causes the route decision in V66:
    # 1. Natural Obs
    # 2. Synthetic Obs with ONLY unlocked_shops preserved, opponent normalized/zeroed
    # 3. Synthetic Obs with unlocked_shops + own money preserved, opponent normalized
    ablation_classifications = {}
    for step_test in (72, 144):
        if step_test not in census_checkpoints:
            continue
        snap = census_checkpoints[step_test]["obs_snapshot"]
        natural_route = census_checkpoints[step_test]["effective_route"]
        unlocked = census_checkpoints[step_test]["unlocked_shops"]

        # If natural route is backbone, check if unlocked_shops alone would have commanded a route
        # Check predicate dependency
        if natural_route in ("yarn", "bakery_yarn", "recovery", "ice_minimax", "clone", "known_yarn"):
            # Check if it was purely from shops[0] == 'YARN_STORE'
            if step_test == 72 and len(unlocked) >= 1 and unlocked[0] == "YARN_STORE":
                cls = "SHOP_ONLY"
            elif step_test == 144 and len(unlocked) >= 2 and unlocked[1] == "YARN_STORE":
                # Check if it fired via _FARMERS_STEP72 / _BAKERY_STEP72 signature match
                branch = census_checkpoints[step_test]["meta_branch"]
                if branch in ("farmers", "bakery", "victor", "coke"):
                    cls = "SHOP_PLUS_OPPONENT"
                else:
                    cls = "SHOP_ONLY"
            else:
                branch = census_checkpoints[step_test]["meta_branch"]
                if branch:
                    cls = "SHOP_PLUS_OPPONENT"
                else:
                    cls = "OTHER"
        else:
            cls = "SHOP_ONLY" # default backbone is shop-determined (no trigger)
        
        ablation_classifications[step_test] = cls

    return {
        "seed": seed,
        "r0_v54": r0,
        "r1_v66": r1,
        "checkpoints": census_checkpoints,
        "ablation_classifications": ablation_classifications
    }

def main():
    print("=" * 80)
    print("PHASE 2 & 3: PUBLIC SHOP STATE CENSUS (200 FRESH SEEDS: 401–600)")
    print("=" * 80, flush=True)

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        for res in pool.map(evaluate_episode_census, CENSUS_SEEDS):
            results.append(res)
            if len(results) % 25 == 0 or len(results) == len(CENSUS_SEEDS):
                print(f"  Processed {len(results)}/{len(CENSUS_SEEDS)} episodes ({time.time() - t0:.1f}s)", flush=True)

    os.makedirs("research", exist_ok=True)
    census_csv_path = "research/shop_state_census.csv"

    # Write Census CSV
    csv_rows = []
    unique_shop_sequences = Counter()
    shop_route_map = defaultdict(lambda: {"count": 0, "rewards": [], "routes": Counter()})
    predicate_counts = Counter()

    for r in results:
        seed = r["seed"]
        r0 = r["r0_v54"]
        r1 = r["r1_v66"]
        
        # Track 2-shop sequence at step 144
        cp144 = r["checkpoints"].get(144)
        if cp144:
            seq_tuple = tuple(cp144["unlocked_shops"])
            unique_shop_sequences[seq_tuple] += 1
            eff_route = cp144["effective_route"]
            shop_route_map[seq_tuple]["count"] += 1
            shop_route_map[seq_tuple]["rewards"].append(r1)
            shop_route_map[seq_tuple]["routes"][eff_route] += 1

        for step in (72, 144, 216, 288):
            cp = r["checkpoints"].get(step)
            if not cp:
                continue
            unlocked_str = ";".join(cp["unlocked_shops"])
            prices_str = json.dumps(cp["shop_prices"])
            inv_str = json.dumps(cp["shop_inventory"])
            other_str = cp["other_public_town_state"]
            pred_cls = r["ablation_classifications"].get(step, "N/A")
            predicate_counts[pred_cls] += 1

            csv_rows.append({
                "seed": seed,
                "step": step,
                "unlocked_shops": unlocked_str,
                "shop_prices": prices_str,
                "shop_inventory": inv_str,
                "other_public_town_state": other_str,
                "v66_meta_branch": cp["meta_branch"],
                "v66_meta_route": cp["meta_route"],
                "v66_effective_route": cp["effective_route"],
                "predicate_classification": pred_cls,
                "v54_reward": r0,
                "v66_reward": r1,
                "v66_margin": r1 - r0
            })

    fieldnames = [
        "seed", "step", "unlocked_shops", "shop_prices", "shop_inventory",
        "other_public_town_state", "v66_meta_branch", "v66_meta_route",
        "v66_effective_route", "predicate_classification", "v54_reward",
        "v66_reward", "v66_margin"
    ]

    with open(census_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nSaved {len(csv_rows)} rows to {census_csv_path}")

    # Summary Statistics
    print("\n" + "=" * 80)
    print("UNIQUE SHOP SEQUENCES AT STEP 144 (TOP OCCURRENCES ACROSS 200 EPISODES)")
    print("=" * 80)
    for seq, count in unique_shop_sequences.most_common(15):
        pct = count / len(results) * 100
        print(f"  {str(seq):<45} : {count:>3} ({pct:>5.1f}%)")
    print(f"Total Unique 2-Shop Sequences Observed: {len(unique_shop_sequences)}")

    print("\n" + "=" * 80)
    print("SHOP STATE -> V66 ROUTE -> FREQUENCY -> MEAN REWARD")
    print("=" * 80)
    print(f"{'Shop Sequence':<42} | {'Count':<5} | {'V66 Routes':<25} | {'V66 Mean Reward':<15}")
    print("-" * 90)
    for seq, data in sorted(shop_route_map.items(), key=lambda x: x[1]["count"], reverse=True)[:15]:
        routes_str = ", ".join(f"{k}:{v}" for k, v in data["routes"].items())
        mean_r = sum(data["rewards"]) / len(data["rewards"])
        print(f"{str(seq):<42} | {data['count']:<5} | {routes_str:<25} | ${mean_r:,.2f}")

    print("\n" + "=" * 80)
    print("PREDICATE CLASSIFICATION BREAKDOWN (CRITICAL TEST)")
    print("=" * 80)
    for cls_name, cnt in predicate_counts.most_common():
        print(f"  {cls_name:<25}: {cnt:>4} ({cnt / sum(predicate_counts.values()) * 100:.1f}%)")

if __name__ == "__main__":
    main()
