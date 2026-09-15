"""
Candidate Fixed Day-8 Sheep Schedule Control (Arm C)
====================================================
Isolates the causal impact of livestock acquisition timing:
Inverts animal prioritization on Day 7+:
Channeling Day-8 cow milk windfall into Sheep (up to 4 sheep),
capturing 6 full shearing cycles (Days 14, 17, 20, 23, 26, 29).
All other logic (including baseline strawberry throttle) remains identical.

100% Observation-Driven, Replay-Free, Closed-Loop.
"""
from candidates.candidate_cl_economic_v1 import (
    ClosedLoopEconomicV1, BOARD, TPD, SHED_ACCESS, WELL_ACCESS,
    CROPS_DEF, PASTURE_SLOTS, PASTURE_SPECIES, MELON_TILES_D0,
    MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE, PRODUCE_TO_DROP,
    BASE_PRICES, MOVES, _fib, _dist, _quad, _walkable, _bfs_step,
    _nearest_shed, min_cost_bipartite_matching
)

class FixedSheepControl(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

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

        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0) + sheep_inv
        n_animals = cows_tot + sheep_tot

        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                feed_res = max(12, int(n_animals * 1.5))
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells[:5]:
            orders.append(["SELL", item, qty])

        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(12, int(n_animals * 1.5))
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 8:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 2000

        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        
        # ARM C MECHANISM: DAY 7+ SHEEP INVERSION
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22 and len(orders) < 8:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                
                # DAY 7+ SHEEP FIRST!
                if day >= 7 and sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(4, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s
                        
                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c
                        
                if day < 7 and sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s

        if hour == 0 and 4 <= day <= 22 and len(orders) < 8:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 7 if day < 7 else (11 if day < 12 else 16)
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 250:
                can_buy_m = min(needed_m, min(6, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        # BASELINE STRAWBERRY THROTTLE (Max 8/day)
        if hour == 0 and 4 <= day <= 20 and len(orders) < 8:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else (24 if day < 10 else 40)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        if day == 0: target_hands = 5
        elif day < 4: target_hands = 4
        elif day < 7: target_hands = 6
        elif day < 10: target_hands = 9
        else: target_hands = 11

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

agent = FixedSheepControl()
def agent_fn(obs, config=None):
    return agent(obs, config)
