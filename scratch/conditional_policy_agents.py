import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.abspath('.'))

from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Policy C1: Only apply cow cap when a 5th cow would consume slot (2, 4) (i.e. single quad and total cows >= 4)
class PolicyC1Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Only gate if single quadrant and total cows >= 4
        if len(quads) == 1:
            cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
            cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
            cows_shed = int(shed.get("COW", 0) or 0)
            total_c = cows_f + cows_inv + cows_shed
            
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed_cows = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed_cows)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Policy C2: Only apply when free sheep-compatible capacity < expected sheep demand by Day 9 (4 sheep)
class PolicyC2Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Sheep compatible slots unlocked: in single quad, there are only 2 sheep slots (4,2) and (2,4)
        # If NE unlocked, 4 more slots (5,4), (6,4), (5,3), (6,3) are unlocked = 6 total slots
        sheep_slots_unlocked = 2 if len(quads) == 1 else 6
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed

        # Free sheep capacity = max(0, sheep_slots_unlocked - max(0, total_c - 4))
        # If single quad, sheep_slots_unlocked = 2 < 4, so trigger fires!
        if sheep_slots_unlocked < 4 and total_c >= 4:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed_cows = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed_cows)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Policy C3: Only apply when expected sheep demand (4) + current sheep > projected available pasture capacity
class PolicyC3Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed
        
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        sheep_shed = int(shed.get("SHEEP", 0) or 0)
        total_s = sheep_f + sheep_inv + sheep_shed

        total_pasture_cap = 6 if len(quads) == 1 else 14
        # If buying another cow pushes (total_c + 1 + 4 sheep demand) > total pasture capacity:
        if (total_c + 1 + 4 + total_s) > total_pasture_cap and total_c >= 4:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed_cows = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed_cows)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Policy C4: Marginal expected wool value of preserving slot exceeds marginal milk value of cow
class PolicyC4Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed

        # Expected wool value = 8.5 cycles * 2 units * $200 = $3,400 gross wool
        # Expected milk value = (30 - day - 2) * 1 unit * $120 gross milk
        # If single quad and total_c >= 4, cow displaces sheep:
        if len(quads) == 1 and total_c >= 4:
            milk_val = max(0, 28 - day) * 120.0
            wool_val = 3400.0
            if wool_val > milk_val:
                new_orders = []
                for o in orders:
                    if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                        allowed_cows = max(0, 4 - total_c)
                        can_buy = min(int(o[2]), allowed_cows)
                        if can_buy > 0:
                            new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                    else:
                        new_orders.append(o)
                return new_orders
        return orders

# Policy C5: BOTH collision risk is high (single quadrant) AND sheep demand is imminent (Day >= 6)
class PolicyC5Agent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed

        # High collision risk: single quad, day >= 6, total_c >= 4
        if len(quads) == 1 and day >= 6 and total_c >= 4:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed_cows = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed_cows)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Policy SheepFirst: Prioritize sheep acquisition/placement over discretionary cow acquisition
class SheepFirstAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        cows_shed = int(shed.get("COW", 0) or 0)
        total_c = cows_f + cows_inv + cows_shed

        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        sheep_shed = int(shed.get("SHEEP", 0) or 0)
        total_s = sheep_f + sheep_inv + sheep_shed

        # If day < 9 and total_c >= 4, do not buy cow 5 until sheep have been acquired
        if day < 9 and total_c >= 4 and total_s == 0:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed_cows = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed_cows)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders
