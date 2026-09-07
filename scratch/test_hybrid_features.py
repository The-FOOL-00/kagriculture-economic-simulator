import sys, os
sys.path.insert(0, os.path.abspath('.'))
import copy
import json
import kaggle_environments
import numpy as np

from candidates.candidate_cl_aethel_prime import CLAethelPrime, CROPS_DEF, _fib, _dist, _nearest_shed, SHED_ACCESS, PRODUCE_TO_DROP, PASTURE_SPECIES, BOARD, TPD

SEEDS = [42, 100, 2024]

class HybridCandidate(CLAethelPrime):
    """
    Candidate CL-Aethel Grandmaster (Architecture H):
    100% Closed-Loop, Zero Replay, Pure Observation-Driven.
    Combines Prime's Closed-Loop Spatial Scheduler with:
    1. Scaled Workload-Driven Hiring (D0: 5, D1-3: 4, D4-6: 6, D7-9: 8, D10+: 12-14)
    2. Guarded Maturation Harvesting (Never harvest melons/ongoing crops prematurely!)
    3. Dedicated Mid-Game Melon Pipeline (10-12 melons in unlocked quads on D10-14)
    4. Water-First Dispatch (Water all crops every day to maximize yield & prevent weeds)
    5. Value-Maximizing Market Queue (Gross-impact sorting to capture peak shop prices)
    """
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        # Day 0 Synchronized Opening: 3 Cows, 1 Sheep, 7 Melons, 10 Wheat, 17 Feed, 2 Hires (then 3 more hires over day 0)
        if step == 0:
            if money >= 2780:
                return [
                    ["BUY_ANIMAL", "COW", 3],
                    ["BUY_ANIMAL", "SHEEP", 1],
                    ["BUY_SEED", "MELON", 7],
                    ["BUY_SEED", "WHEAT", 10],
                    ["BUY_PRODUCT", "WHEAT", 17],
                    ["HIRE"], ["HIRE"]
                ]
            else:
                cur_m = money
                ret = []
                if cur_m >= 400: ret.append(["BUY_ANIMAL", "COW", 1]); cur_m -= 400
                if cur_m >= 100: ret.append(["BUY_SEED", "WHEAT", min(10, int(cur_m // 10))])
                if cur_m >= 1: ret.append(["HIRE"])
                return ret

        # Count animals
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_tot = cows_f + int(shed.get("COW", 0) or 0)
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0)
        n_animals = cows_tot + sheep_tot

        # Market Sells: High-Value Liquidation with Peak Impact Sorting
        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                # Keep feed buffer! Only sell surplus wheat above feed reserve
                feed_res = max(15, n_animals * 2)
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, 100) or 100)
                # Gross value sorting
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells:
            if len(orders) < 8:
                orders.append(["SELL", item, qty])

        # Dynamic Feed Replenishment
        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(15, n_animals * 2)
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 9:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        # Dynamic Land Expansions: Day 7 NE, Day 10 SW
        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 9:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 9:
            orders.append(["BUY_LAND"])
            money -= 2000

        # Animal Scaling: 8 Cows and 6 Sheep
        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)
        if shed_anim_count == 0 and hour == 0:
            if ("NE" in quads or (len(quads) == 1 and day >= 7)) and 7 <= day <= 22 and len(orders) < 9:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                if sheep_needed > 0 and money >= 750:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                if cows_needed > 0 and money >= 650 and len(orders) < 9:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400

        # Mid-game Melon Succession (Days 10-14): Replant 12-14 melons in SW/NE!
        if hour == 0 and 10 <= day <= 15 and len(orders) < 9:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 14
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 300:
                can_buy_m = min(needed_m, min(8, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        # Strawberry Procurement (Days 4-16)
        if hour == 0 and 4 <= day <= 16 and len(orders) < 9:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 4 if day < 7 else (18 if day < 10 else 38)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        # Scaled Hiring Cadence (Proportional to farm active workload)
        # Day 0: 5 hands, Day 1-3: 4 hands, Day 4-6: 6-7 hands, Day 7-9: 8-10 hands, Day 10+: 12-14 hands
        if day == 0: target_hands = 5
        elif day < 4: target_hands = 4
        elif day < 7: target_hands = 6
        elif day < 10: target_hands = 9
        elif day < 20: target_hands = 12
        else: target_hands = 13

        cur_h = hired
        budget = money
        while cur_h < target_hands and len(orders) < 10:
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break

        return orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        # Enhanced Field Scan with Strict Maturation Guards
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # Override ripe_crops: ONLY harvest melons if yield_units >= 5 or day >= 27!
        guarded_ripe = []
        for pos in res["ripe_crops"]:
            t = tiles[pos[1]][pos[0]]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop = t.get("crop")
                yu = int(t.get("yield_units", 0) or 0)
                if crop == "MELON":
                    if yu >= 5 or day >= 27:
                        guarded_ripe.append(pos)
                elif crop == "WHEAT":
                    if yu >= 4 or day >= 27:
                        guarded_ripe.append(pos)
                else:
                    guarded_ripe.append(pos)
            else:
                guarded_ripe.append(pos)
        res["ripe_crops"] = guarded_ripe
        return res

def eval_candidate():
    print("Evaluating New Closed-Loop Hybrid Candidate...")
    scores = []
    hybrid = HybridCandidate()
    def agent(obs, cfg=None): return hybrid(obs, cfg)
    
    for s in SEEDS:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
        env.run([agent, starter])
        sc = env.steps[-1][0]['reward']
        scores.append(sc)
        print(f"  Seed {s}: Score = ${sc:,.1f}")
    print(f"Hybrid Candidate Mean: ${np.mean(scores):,.1f} +/- {np.std(scores):,.1f}")

if __name__ == '__main__':
    eval_candidate()
