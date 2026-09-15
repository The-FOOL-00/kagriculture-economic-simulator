"""
Controlled Sheep Timing Variants
=================================
Isolates the causal impact of sheep acquisition timing by varying ONLY
the priority and schedule of sheep purchases on Days 5-18, preserving
all other mechanics of CL-Economic-V1:
- Variant 1A: Baseline (Cow priority to 8 cows; sheep reached ~Day 16)
- Variant 1B: Early Sheep (Target 6 sheep by Day 9)
- Variant 1C: Intermediate Sheep (Target 6 sheep by Day 11)
- Variant 1D: Intermediate Sheep (Target 6 sheep by Day 13)
- Variant 1E: Late Sheep Control (Sheep held at 1 until Day 18)
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1

class BaseSheepTimingCandidate(ClosedLoopEconomicV1):
    def __init__(self, sheep_schedule_name="baseline", sheep_unlock_day=16):
        super().__init__()
        self.sheep_schedule_name = sheep_schedule_name
        self.sheep_unlock_day = sheep_unlock_day

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
                p_val = float(prices.get(item, 100) or 100)
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

        # LIVESTOCK ALLOCATION LOGIC CONTROLLED BY VARIANT
        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22 and len(orders) < 8:
                target_cows = 8
                target_sheep = 6
                
                # Determine priority order based on schedule
                prioritize_sheep_now = False
                if self.sheep_schedule_name == "day9" and day >= 7:
                    # Target 6 sheep by day 9
                    needed_sheep_today = min(6, 1 + (day - 6) * 2)
                    if sheep_tot < needed_sheep_today:
                        prioritize_sheep_now = True
                elif self.sheep_schedule_name == "day11" and day >= 9:
                    needed_sheep_today = min(6, 1 + (day - 8) * 2)
                    if sheep_tot < needed_sheep_today:
                        prioritize_sheep_now = True
                elif self.sheep_schedule_name == "day13" and day >= 11:
                    needed_sheep_today = min(6, 1 + (day - 10) * 2)
                    if sheep_tot < needed_sheep_today:
                        prioritize_sheep_now = True
                elif self.sheep_schedule_name == "late18":
                    if day < 18:
                        target_sheep = 1

                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)

                if prioritize_sheep_now:
                    # BUY SHEEP FIRST
                    if sheep_needed > 0 and money >= 750 and len(orders) < 8:
                        can_buy_s = min(sheep_needed, min(2, int((money - 250) // 500)))
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
                else:
                    # BASELINE: BUY COW FIRST
                    if cows_needed > 0 and money >= 650 and len(orders) < 8:
                        can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                        if can_buy_c > 0:
                            orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                            money -= can_buy_c * 400
                            cows_tot += can_buy_c
                    if sheep_needed > 0 and money >= 750 and len(orders) < 8:
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

        from candidates.candidate_cl_economic_v1 import _fib
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

# Concrete variant classes
class Variant1A_BaselineSheep(BaseSheepTimingCandidate):
    def __init__(self): super().__init__("baseline", 16)

class Variant1B_Day9Sheep(BaseSheepTimingCandidate):
    def __init__(self): super().__init__("day9", 9)

class Variant1C_Day11Sheep(BaseSheepTimingCandidate):
    def __init__(self): super().__init__("day11", 11)

class Variant1D_Day13Sheep(BaseSheepTimingCandidate):
    def __init__(self): super().__init__("day13", 13)

class Variant1E_Late18Sheep(BaseSheepTimingCandidate):
    def __init__(self): super().__init__("late18", 18)
