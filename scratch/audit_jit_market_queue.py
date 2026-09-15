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

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1, _fib

class JITMarketExperimentAgent(ClosedLoopEconomicV1):
    def __init__(self, queue_mode="HOUR0_ONLY"):
        super().__init__()
        self.queue_mode = queue_mode
        self.purchase_attempts = [] # logged purchase evaluation attempts

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        if step == 0:
            return super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)

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

        # DECIDE WHETHER THIS TICK IS ELIGIBLE FOR PURCHASING
        should_evaluate_purchases = False
        if self.queue_mode == "HOUR0_ONLY":
            should_evaluate_purchases = (hour == 0)
        elif self.queue_mode == "HOUR0_AND_HOUR1":
            should_evaluate_purchases = (hour in (0, 1))
        elif self.queue_mode == "INTRADAY_EVERY_4H":
            should_evaluate_purchases = (hour % 4 == 0)
        elif self.queue_mode == "STATE_DERIVED_RETRY":
            # Retry whenever money >= 250 or hour == 0
            should_evaluate_purchases = (hour == 0 or money >= 250)

        if should_evaluate_purchases:
            shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
            if shed_anim_count == 0 and n_animals < 14:
                if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22:
                    target_cows = 8
                    target_sheep = 6
                    cows_needed = max(0, target_cows - cows_tot)
                    sheep_needed = max(0, target_sheep - sheep_tot)

                    # Check Cow purchase
                    if cows_needed > 0:
                        if money >= 650:
                            if len(orders) < 8:
                                can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                                if can_buy_c > 0:
                                    orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                                    money -= can_buy_c * 400
                                    cows_tot += can_buy_c
                            else:
                                self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "COW", "reason": "QUEUE_FULL"})
                        else:
                            self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "COW", "reason": "INSUFFICIENT_CASH"})

                    # Check Sheep purchase
                    if sheep_needed > 0:
                        if money >= 750:
                            if len(orders) < 8:
                                can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                                if can_buy_s > 0:
                                    orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                                    money -= can_buy_s * 500
                                    sheep_tot += can_buy_s
                            else:
                                self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "SHEEP", "reason": "QUEUE_FULL"})
                        else:
                            self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "SHEEP", "reason": "INSUFFICIENT_CASH"})

            # Melons
            if 4 <= day <= 22:
                melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
                melons_s = int(seeds.get("MELON", 0) or 0)
                target_melons = 7 if day < 7 else (11 if day < 12 else 16)
                needed_m = max(0, target_melons - (melons_f + melons_s))
                if needed_m > 0:
                    if money >= 250:
                        if len(orders) < 8:
                            can_buy_m = min(needed_m, min(6, int((money - 150) // 80)))
                            if can_buy_m > 0:
                                orders.append(["BUY_SEED", "MELON", can_buy_m])
                                money -= can_buy_m * 80
                        else:
                            self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "MELON_SEED", "reason": "QUEUE_FULL"})
                    else:
                        self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "MELON_SEED", "reason": "INSUFFICIENT_CASH"})

            # Strawberries
            if 4 <= day <= 20:
                straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
                straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
                target_straw = 8 if day < 7 else (24 if day < 10 else 40)
                needed = max(0, target_straw - straw_f - straw_s)
                if needed > 0:
                    if money >= 250:
                        if len(orders) < 8:
                            can_buy = min(needed, min(8, int((money - 150) // 100)))
                            if can_buy > 0:
                                orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                                money -= can_buy * 100
                        else:
                            self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "STRAW_SEED", "reason": "QUEUE_FULL"})
                    else:
                        self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "STRAW_SEED", "reason": "INSUFFICIENT_CASH"})

            # Wheat
            if 2 <= day <= 24:
                wheat_s = int(seeds.get("WHEAT", 0) or 0)
                if wheat_s < 10:
                    if money >= 200:
                        if len(orders) < 8:
                            can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                            if can_buy_w > 0:
                                orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                                money -= can_buy_w * 10
                        else:
                            self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "WHEAT_SEED", "reason": "QUEUE_FULL"})
                    else:
                        self.purchase_attempts.append({"step": step, "day": day, "hour": hour, "item": "WHEAT_SEED", "reason": "INSUFFICIENT_CASH"})

        # Hiring (Only at hour 0 as in baseline)
        if hour == 0:
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

def run_queue_experiment_match(args):
    queue_mode, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    agent_inst = JITMarketExperimentAgent(queue_mode=queue_mode)
    env.run([agent_inst, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    harvest_counts = Counter()
    total_harvs = 0
    total_moves = 0
    
    for s_idx in range(1, total_steps):
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
            elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    
    # Analyze failure classifications
    reasons = Counter(p["reason"] for p in agent_inst.purchase_attempts)
    
    return {
        "queue_mode": queue_mode,
        "seed": seed,
        "reward": reward,
        "harvests": total_harvs,
        "moves": total_moves,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "melon": harvest_counts.get("MELON", 0),
        "milk": harvest_counts.get("COW", 0),
        "queue_full_events": reasons.get("QUEUE_FULL", 0),
        "insufficient_cash_events": reasons.get("INSUFFICIENT_CASH", 0),
        "total_attempts": len(agent_inst.purchase_attempts)
    }

if __name__ == "__main__":
    modes = [
        "HOUR0_ONLY",
        "HOUR0_AND_HOUR1",
        "INTRADAY_EVERY_4H",
        "STATE_DERIVED_RETRY"
    ]
    seeds = list(range(1000, 1010))
    tasks = [(m, s) for m in modes for s in seeds]
    
    print(f"Running JIT Market Queue Experiment ({len(tasks)} matches across 10 seeds)...")
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_queue_experiment_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["queue_mode"]].append(res)
            
    with open("scratch/audit_jit_market_queue_results.json", "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2)
        
    print("\n" + "="*115)
    print(f"{'MODE':<22} | {'Reward ($)':<16} | {'Delta ($)':<12} | {'Straw':<7} | {'Wool':<7} | {'Milk':<7} | {'Queue Full':<10} | {'No Cash':<8}")
    print("-" * 115)
    
    base_rew = np.mean([x["reward"] for x in results["HOUR0_ONLY"]])
    for m in modes:
        lst = results[m]
        lst.sort(key=lambda x: x["seed"])
        rews = [x["reward"] for x in lst]
        m_rew = float(np.mean(rews))
        std_rew = float(np.std(rews))
        ci95 = 1.96 * std_rew / np.sqrt(len(rews))
        m_straw = float(np.mean([x["straw"] for x in lst]))
        m_wool = float(np.mean([x["wool"] for x in lst]))
        m_milk = float(np.mean([x["milk"] for x in lst]))
        q_full = float(np.mean([x["queue_full_events"] for x in lst]))
        no_cash = float(np.mean([x["insufficient_cash_events"] for x in lst]))
        delta = m_rew - base_rew
        print(f"{m:<22} | ${m_rew:10.2f} ± ${ci95:5.0f} | {delta:+10.2f} | {m_straw:7.1f} | {m_wool:7.1f} | {m_milk:7.1f} | {q_full:10.1f} | {no_cash:8.1f}")
