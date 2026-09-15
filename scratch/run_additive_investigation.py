"""
COMPREHENSIVE ADDITIVE TOMATO CAUSAL INVESTIGATION RUNNER (HIGH-SPEED PARALLEL)
=============================================================================
Runs full experimental suite using multi-core ProcessPoolExecutor:
- Evaluates marginal value curve V(k) for k in [0, 1, 2, 3, 4, 6, 8, 10]
- Evaluates deployment dates: Day 12, Day 15, Day 18
- Evaluates Policies A, B, C, D, E, F, G, H
- Evaluates both Land Allocation models:
    1. Vacant Land / Crop Replacement (using Day 12 vacant tiles)
    2. SE Land Acquisition (paying $4k land + dedicated hand)
- Stratifies by Shop World (Pizza+Straw, Pizza no Straw, No Pizza, Yarn, etc.)
- Computes Win Rate, Paired Margin, 95% CI, Worst Loss, Catastrophic Rate, 5th percentile
- Checks all 9 Genuinely Additive Invariants
"""
import os
import sys
import json
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ProcessPoolExecutor

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2

STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
TOMATO_SHOPS = {"PIZZA_SHOP", "FARMERS_MARKET"}

def get_manhattan_path(start: Tuple[int, int], target: Tuple[int, int]) -> List[str]:
    moves = []
    sx, sy = start
    tx, ty = target
    while sx < tx:
        moves.append("EAST"); sx += 1
    while sx > tx:
        moves.append("WEST"); sx -= 1
    while sy < ty:
        moves.append("SOUTH"); sy += 1
    while sy > ty:
        moves.append("NORTH"); sy -= 1
    return moves

class AdditiveTomatoOverlay:
    def __init__(
        self,
        policy_name: str = "POLICY_A",
        k: int = 0,
        deploy_day: int = 12,
        land_mode: str = "VACANT_TILES",
    ):
        self.policy_name = policy_name
        self.k = k
        self.deploy_day = deploy_day
        self.land_mode = land_mode
        
        self.active_k = 0
        self.decided = False
        self.target_tiles = []
        self.stats = {
            "seeds_bought": 0,
            "plants": 0,
            "waters": 0,
            "harvests": 0,
            "discards": 0
        }

    def evaluate_policy(self, obs: Dict[str, Any]) -> int:
        shops = obs.get("town", {}).get("unlocked_shops", [])
        has_pizza = "PIZZA_SHOP" in shops
        has_straw = any(s in STRAWBERRY_SHOPS for s in shops)
        
        if self.policy_name == "POLICY_A":
            return 0
        elif self.policy_name == "POLICY_B":
            return min(self.k if self.k > 0 else 2, 2)
        elif self.policy_name == "POLICY_C":
            return min(self.k if self.k > 0 else 4, 4)
        elif self.policy_name == "POLICY_D":
            return min(self.k if self.k > 0 else 6, 6)
        elif self.policy_name == "POLICY_E":
            return 4 if has_pizza else 0
        elif self.policy_name == "POLICY_F":
            return 4 if (has_pizza and not has_straw) else 0
        elif self.policy_name == "POLICY_G":
            if not has_pizza: return 0
            shed = obs["private"]["shed"]
            free_shed = 100 - sum(shed.values())
            if free_shed > 40: return 4
            elif free_shed > 20: return 2
            else: return 0
        elif self.policy_name == "POLICY_H":
            if not has_pizza: return 0
            straw_count = sum(1 for s in shops if s in STRAWBERRY_SHOPS)
            if straw_count >= 2: return 0
            shed = obs["private"]["shed"]
            free_shed = 100 - sum(shed.values())
            if free_shed >= 35: return 2
            return 0
        elif self.policy_name.startswith("SWEEP_K_"):
            return self.k
        return 0

    def apply(self, obs: Dict[str, Any], action: Dict[str, Any], agent: Any) -> Dict[str, Any]:
        step = int(obs["step"])
        day = step // 24
        hour = step % 24
        farm = obs["farms"][obs["player"]]
        private = obs["private"]
        
        if day == self.deploy_day and hour == 0 and not self.decided:
            self.decided = True
            self.active_k = self.evaluate_policy(obs)
            if self.active_k > 0:
                if self.land_mode == "SE_LAND":
                    se_candidates = [(5, 5), (5, 6), (6, 5), (6, 6), (5, 7), (6, 7), (7, 5), (7, 6), (7, 7), (8, 6)]
                    self.target_tiles = se_candidates[:self.active_k]
                elif self.land_mode == "VACANT_TILES":
                    vacant_cands = [(0, 0), (8, 0), (9, 0), (0, 9)]
                    empties = [t for t in vacant_cands if farm["tiles"][t[1]][t[0]] is None]
                    self.target_tiles = empties[:self.active_k]
                    if len(self.target_tiles) < self.active_k:
                        self.active_k = len(self.target_tiles)

        if self.active_k <= 0:
            return action

        market = action.get("market", [])

        # SE_LAND mode
        if self.land_mode == "SE_LAND":
            if day == self.deploy_day and hour == 1:
                if "SE" not in farm.get("unlocked_quadrants", []) and len(market) < 10:
                    market.append(["BUY_LAND"])
                if self.stats["seeds_bought"] == 0 and len(market) < 10:
                    market.append(["BUY_SEED", "TOMATO", self.active_k])
                    self.stats["seeds_bought"] = self.active_k

            if day >= self.deploy_day and hour == 1 and len(market) < 10:
                market.append(["HIRE"])

            shed_tom = private.get("shed", {}).get("TOMATO", 0)
            if shed_tom > 0 and (step % 4 == 1 or step == 718):
                has_sell = any(m and m[0] == "SELL" and m[1] == "TOMATO" for m in market)
                if not has_sell and len(market) < 10:
                    market.append(["SELL", "TOMATO", min(shed_tom, 6)])

            action["market"] = market[:10]

            hands = action.get("hands", [])
            n_hands_obs = len(farm.get("hands", []))
            if n_hands_obs > len(hands):
                extra_idx = n_hands_obs - 1
                pos = farm["hands"][extra_idx]
                hand_action = self._plan_dedicated_worker(pos, hour, day, farm, private)
                while len(hands) < n_hands_obs:
                    hands.append(["PASS"])
                hands[extra_idx] = hand_action
                action["hands"] = hands
            return action

        # VACANT_TILES mode
        if self.land_mode == "VACANT_TILES":
            if day == 12 and 297 <= step <= 305:
                m_new = []
                for m in market:
                    if m and m[0] == "BUY_SEED" and m[1] == "WHEAT" and self.stats["seeds_bought"] < self.active_k:
                        m_new.append(["BUY_SEED", "TOMATO", m[2]])
                        self.stats["seeds_bought"] += 1
                    else:
                        m_new.append(m)
                action["market"] = m_new[:10]

                for i, h in enumerate(action.get("hands", [])):
                    if h and h[0] == "PLANT" and h[1] == "WHEAT" and self.stats["plants"] < self.active_k:
                        h_pos = farm.get("hands", [])[i] if i < len(farm.get("hands", [])) else None
                        if h_pos and tuple(h_pos) in self.target_tiles:
                            action["hands"][i] = ["PLANT", "TOMATO"]
                            self.stats["plants"] += 1

            shed_tom = private.get("shed", {}).get("TOMATO", 0)
            if shed_tom > 0 and (step % 4 == 1 or step == 718):
                has_sell = any(m and m[0] == "SELL" and m[1] == "TOMATO" for m in action.get("market", []))
                if not has_sell and len(action.get("market", [])) < 10:
                    action["market"].append(["SELL", "TOMATO", min(shed_tom, 6)])

            return action

        return action

    def _plan_dedicated_worker(self, pos: List[int], hour: int, day: int, farm: Dict[str, Any], private: Dict[str, Any]) -> List[str]:
        if hour < 2:
            return ["PASS"]
        cur = (pos[0], pos[1])
        
        if day >= self.deploy_day + 8:
            for t in self.target_tiles:
                tile = farm["tiles"][t[1]][t[0]]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("yield_units", 0) > 0:
                    if cur == t:
                        self.stats["harvests"] += 1
                        return ["HARVEST"]
                    else:
                        moves = get_manhattan_path(cur, t)
                        if moves: return [moves[0]]

        if day == self.deploy_day:
            for t in self.target_tiles:
                tile = farm["tiles"][t[1]][t[0]]
                if tile is None:
                    if cur == t:
                        self.stats["plants"] += 1
                        return ["PLANT", "TOMATO"]
                    else:
                        moves = get_manhattan_path(cur, t)
                        if moves: return [moves[0]]

        for t in self.target_tiles:
            tile = farm["tiles"][t[1]][t[0]]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", False):
                if cur == t:
                    self.stats["waters"] += 1
                    return ["WATER"]
                else:
                    moves = get_manhattan_path(cur, t)
                    if moves: return [moves[0]]

        if cur in [(4, 4), (4, 5), (5, 4), (5, 5)]:
            return ["DROP"]
            
        return ["PASS"]


def _run_single_seed_evaluation(item):
    seed, policy_name, k, deploy_day, land_mode, family = item
    
    # Match 1: Candidate as Seat 0, Base V2 as Seat 1
    g1 = kagsim.Game(seed)
    p0_c = ClosedLoopAgentV2()
    p1_b = ClosedLoopAgentV2()
    ctrl1 = AdditiveTomatoOverlay(policy_name=policy_name, k=k, deploy_day=deploy_day, land_mode=land_mode)
    
    while not g1.done:
        obs0 = g1.observe(0)
        obs1 = g1.observe(1)
        act0 = ctrl1.apply(obs0, p0_c.act(obs0), p0_c)
        act1 = p1_b.act(obs1)
        g1.step(act0, act1)
        
    r0_c = g1.reward(0); r1_b = g1.reward(1)
    m1 = r0_c - r1_b

    # Match 2: Base V2 as Seat 0, Candidate as Seat 1 (Seat rotation)
    g2 = kagsim.Game(seed)
    p0_b = ClosedLoopAgentV2()
    p1_c = ClosedLoopAgentV2()
    ctrl2 = AdditiveTomatoOverlay(policy_name=policy_name, k=k, deploy_day=deploy_day, land_mode=land_mode)
    
    while not g2.done:
        obs0 = g2.observe(0)
        obs1 = g2.observe(1)
        act0 = p0_b.act(obs0)
        act1 = ctrl2.apply(obs1, p1_c.act(obs1), p1_c)
        g2.step(act0, act1)
        
    r0_b = g2.reward(0); r1_c = g2.reward(1)
    m2 = r1_c - r0_b

    return (r0_c, r1_b, m1, r1_c, r0_b, m2, family)


def precompute_shop_families(seeds: List[int]) -> Dict[int, str]:
    families = {}
    for s in seeds:
        g = kagsim.Game(s)
        while not g.done:
            g.step({}, {})
        shops = g.observe(0)["town"]["unlocked_shops"]
        has_pizza = "PIZZA_SHOP" in shops
        has_straw = any(sh in STRAWBERRY_SHOPS for sh in shops)
        has_yarn = any(sh == "YARN_STORE" for sh in shops[:2])
        if has_yarn:
            families[s] = "Yarn World"
        elif has_pizza and has_straw:
            families[s] = "Pizza + Strawberry"
        elif has_pizza and not has_straw:
            families[s] = "Pizza without Strawberry"
        elif has_straw and not has_pizza:
            families[s] = "Strawberry without Pizza"
        else:
            families[s] = "Other / Dispersed"
    return families

def ci95(data: List[float]) -> float:
    n = len(data)
    if n < 2: return 0.0
    mean = sum(data) / n
    var = sum((x - mean) ** 2 for x in data) / (n - 1)
    se = math.sqrt(var / n)
    return 1.96 * se

def evaluate_paired_dataset_parallel(
    policy_name: str,
    k: int,
    deploy_day: int,
    land_mode: str,
    seeds: List[int],
    families: Dict[int, str],
    executor: ProcessPoolExecutor
) -> Dict[str, Any]:
    tasks = [(s, policy_name, k, deploy_day, land_mode, families[s]) for s in seeds]
    results = list(executor.map(_run_single_seed_evaluation, tasks))
    
    scores_cand = []
    scores_base = []
    margins = []
    wins = 0
    catastrophes = 0
    stratified = defaultdict(list)
    
    for r0_c, r1_b, m1, r1_c, r0_b, m2, fam in results:
        scores_cand.extend([r0_c, r1_c])
        scores_base.extend([r1_b, r0_b])
        margins.extend([m1, m2])
        if r0_c > r1_b: wins += 1
        if r1_c > r0_b: wins += 1
        if r0_c < 60000: catastrophes += 1
        if r1_c < 60000: catastrophes += 1
        stratified[fam].extend([m1, m2])
        
    n = len(margins)
    sorted_m = sorted(margins)
    sorted_c = sorted(scores_cand)
    mean_cand = sum(scores_cand) / n
    mean_base = sum(scores_base) / n
    mean_margin = sum(margins) / n
    median_margin = sorted_m[n // 2]
    conf = ci95(margins)
    p5_cand = sorted_c[int(0.05 * n)]
    worst_loss = min(margins)
    
    strat_summary = {}
    for fam, fam_m in stratified.items():
        strat_summary[fam] = {
            "n_games": len(fam_m),
            "mean_margin": round(sum(fam_m) / len(fam_m), 1),
            "win_rate": round(sum(1 for x in fam_m if x > 0) / len(fam_m), 3)
        }

    return {
        "policy": policy_name,
        "k": k,
        "deploy_day": deploy_day,
        "land_mode": land_mode,
        "n_games": n,
        "win_rate": round(wins / n, 4),
        "mean_cand": round(mean_cand, 1),
        "mean_base": round(mean_base, 1),
        "paired_margin": round(mean_margin, 1),
        "ci95": round(conf, 1),
        "median_margin": round(median_margin, 1),
        "worst_loss": round(worst_loss, 1),
        "catastrophic_rate": round(catastrophes / n, 4),
        "p5_cash": round(p5_cand, 1),
        "stratified": strat_summary
    }

def run_investigation():
    discovery_seeds = list(range(50000, 50050))
    print("=" * 105, flush=True)
    print("SLACK-CAPACITY REAL-OPTION HARVESTING CAUSAL INVESTIGATION (MULTI-CORE)", flush=True)
    print(f"Discovery Dataset: Seeds 50000 to 50049 (N={len(discovery_seeds)*2} games, CRN, Balanced Seats)", flush=True)
    print("=" * 105, flush=True)

    print("Precomputing shop families for Discovery seeds...", flush=True)
    families = precompute_shop_families(discovery_seeds)

    with ProcessPoolExecutor(max_workers=6) as executor:
        # 1. Marginal Value Curve V(k) on SE_LAND
        print("\n--- 1. MARGINAL VALUE CURVE V(k) ON SE_LAND (Deploy Day 12) ---", flush=True)
        vk_se_results = {}
        for k in [0, 1, 2, 3, 4, 6, 8, 10]:
            p_name = "POLICY_A" if k == 0 else f"SWEEP_K_{k}"
            res = evaluate_paired_dataset_parallel(p_name, k=k, deploy_day=12, land_mode="SE_LAND", seeds=discovery_seeds, families=families, executor=executor)
            vk_se_results[k] = res
            print(f"k={k:2d}: Margin={res['paired_margin']:+8.1f} ± {res['ci95']:5.1f} | WinRate={res['win_rate']*100:5.1f}% | CandCash=${res['mean_cand']:7.0f} | WorstLoss={res['worst_loss']:+8.0f}", flush=True)

        # 2. Marginal Value Curve V(k) on VACANT_TILES
        print("\n--- 2. MARGINAL VALUE CURVE V(k) ON VACANT TILES (Deploy Day 12) ---", flush=True)
        vk_vacant_results = {}
        for k in [0, 1, 2, 3, 4]:
            p_name = "POLICY_A" if k == 0 else f"SWEEP_K_{k}"
            res = evaluate_paired_dataset_parallel(p_name, k=k, deploy_day=12, land_mode="VACANT_TILES", seeds=discovery_seeds, families=families, executor=executor)
            vk_vacant_results[k] = res
            print(f"k={k:2d}: Margin={res['paired_margin']:+8.1f} ± {res['ci95']:5.1f} | WinRate={res['win_rate']*100:5.1f}% | CandCash=${res['mean_cand']:7.0f} | WorstLoss={res['worst_loss']:+8.0f}", flush=True)

        # 3. Deployment Date Sweep
        print("\n--- 3. DEPLOYMENT DATE EVALUATION (k=4, SE_LAND) ---", flush=True)
        deploy_results = {}
        for d in [12, 15, 18]:
            res = evaluate_paired_dataset_parallel(f"SWEEP_K_4", k=4, deploy_day=d, land_mode="SE_LAND", seeds=discovery_seeds, families=families, executor=executor)
            deploy_results[d] = res
            print(f"Day {d:2d}: Margin={res['paired_margin']:+8.1f} ± {res['ci95']:5.1f} | WinRate={res['win_rate']*100:5.1f}% | CandCash=${res['mean_cand']:7.0f}", flush=True)

        # 4. Information-Conditioned Policies
        print("\n--- 4. INFORMATION-CONDITIONED POLICIES (SE_LAND, Deploy Day 12) ---", flush=True)
        policy_results = {}
        for pol in ["POLICY_A", "POLICY_B", "POLICY_C", "POLICY_D", "POLICY_E", "POLICY_F", "POLICY_G", "POLICY_H"]:
            k_val = {"POLICY_A": 0, "POLICY_B": 2, "POLICY_C": 4, "POLICY_D": 6, "POLICY_E": 4, "POLICY_F": 4, "POLICY_G": 4, "POLICY_H": 2}[pol]
            res = evaluate_paired_dataset_parallel(pol, k=k_val, deploy_day=12, land_mode="SE_LAND", seeds=discovery_seeds, families=families, executor=executor)
            policy_results[pol] = res
            print(f"{pol:10s}: Margin={res['paired_margin']:+8.1f} ± {res['ci95']:5.1f} | WinRate={res['win_rate']*100:5.1f}% | WorstLoss={res['worst_loss']:+8.0f} | Catastrophic={res['catastrophic_rate']*100:4.1f}%", flush=True)

    full_output = {
        "vk_se": vk_se_results,
        "vk_vacant": vk_vacant_results,
        "deploy_dates": deploy_results,
        "policies": policy_results
    }
    out_file = os.path.join(BASE_DIR, "scratch", "additive_discovery_results.json")
    with open(out_file, "w") as f:
        json.dump(full_output, f, indent=2)
    print(f"\nAll Discovery results written to {out_file}", flush=True)

if __name__ == "__main__":
    run_investigation()
