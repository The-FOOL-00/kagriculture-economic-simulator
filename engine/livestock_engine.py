"""
=============================================================================
ENGINE: LIVESTOCK MANAGEMENT SUBSYSTEM (CORRECTED)
=============================================================================
Manages end-to-end livestock operations:
1. Structure requirements and layout planning (Pastures for Cow/Sheep, Coops for Goose).
2. Capital-aware animal procurement with strict liquidity and feed protection.
3. Daily maintenance chores: Feeding, Caring (for yield bonus), Fertilizer collection.
4. Wheat feed reserve tracking and auto-replenishment.
5. Worker animal pickup from shed and placement onto constructed structures.
=============================================================================
"""

from config import ANIMALS, PRODUCTS, CROPS


class LivestockEngine:
    def __init__(self, target_cows=6, target_sheep=3, target_geese=0, care_animals=True):
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = target_geese
        self.care_animals = care_animals

    def update_targets(self, target_cows=None, target_sheep=None, target_geese=None):
        if target_cows is not None: self.target_cows = target_cows
        if target_sheep is not None: self.target_sheep = target_sheep
        if target_geese is not None: self.target_geese = target_geese

    def analyze_livestock_state(self, tiles, shed, inventories):
        """
        Inspects the farm grid and inventories to extract exact livestock metrics.
        """
        cow_count = 0
        sheep_count = 0
        goose_count = 0
        pasture_count = 0
        occupied_pastures = 0
        empty_pastures = []
        coop_count = 0
        occupied_coops = 0
        empty_coops = []
        livestock_chores = []
        unfed_animal_tiles = []

        for y in range(len(tiles)):
            for x in range(len(tiles[0])):
                t = tiles[y][x]
                pos = (x, y)
                if not isinstance(t, dict):
                    continue

                kind = t.get("kind")
                if kind == "COOP":
                    coop_count += 1
                    if "animal" in t and t.get("animal"):
                        occupied_coops += 1
                        goose_count += 1
                        if not t.get("fed_today", False):
                            livestock_chores.append({"type": "FEED", "pos": pos, "weight": 90})
                            unfed_animal_tiles.append(pos)
                        if self.care_animals and not t.get("cared_today", False):
                            livestock_chores.append({"type": "CARE", "pos": pos, "weight": 75})
                        if t.get("fertilizer_available", False):
                            livestock_chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 85})
                        if t.get("yield_units", 0) > 0:
                            livestock_chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                    else:
                        empty_coops.append(pos)

                elif kind == "PASTURE":
                    pasture_count += 1
                    if "animal" in t and t.get("animal"):
                        occupied_pastures += 1
                        a_type = t.get("animal")
                        if a_type == "COW": cow_count += 1
                        elif a_type == "SHEEP": sheep_count += 1

                        if not t.get("fed_today", False):
                            livestock_chores.append({"type": "FEED", "pos": pos, "weight": 92})
                            unfed_animal_tiles.append(pos)
                        if self.care_animals and not t.get("cared_today", False):
                            livestock_chores.append({"type": "CARE", "pos": pos, "weight": 76})
                        if t.get("fertilizer_available", False):
                            livestock_chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                        if t.get("yield_units", 0) > 0:
                            livestock_chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                    else:
                        empty_pastures.append(pos)

        cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
        sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
        geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
        total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

        return {
            "cow_count": cow_count,
            "sheep_count": sheep_count,
            "goose_count": goose_count,
            "total_active_animals": total_active_animals,
            "pasture_count": pasture_count,
            "occupied_pastures": occupied_pastures,
            "coop_count": coop_count,
            "occupied_coops": occupied_coops,
            "empty_pastures": empty_pastures,
            "empty_coops": empty_coops,
            "cows_in_transit": cows_in_transit,
            "sheep_in_transit": sheep_in_transit,
            "geese_in_transit": geese_in_transit,
            "chores": livestock_chores,
            "unfed_animal_tiles": unfed_animal_tiles
        }

    def generate_market_orders(self, state_summary, money, spendable, day, current_orders):
        """
        Generates buy orders for animals and feed with capital liquidity protection.
        """
        orders = []
        rem_spendable = spendable
        rem_money = money

        needed_cows = max(0, self.target_cows - state_summary["cow_count"] - state_summary["cows_in_transit"])
        needed_sheep = max(0, self.target_sheep - state_summary["sheep_count"] - state_summary["sheep_in_transit"])
        needed_geese = max(0, self.target_geese - state_summary["goose_count"] - state_summary["geese_in_transit"])

        cows_ordered = 0
        sheep_ordered = 0
        geese_ordered = 0

        # 1. Animal Purchasing (Early to Mid Season, Days 0 - 12)
        if day <= 12:
            if needed_cows > 0 and rem_spendable >= 695 and len(current_orders) + len(orders) < 10:
                orders.append(["BUY_ANIMAL", "COW", 1])
                rem_spendable -= 600
                rem_money -= 600
                needed_cows -= 1
                cows_ordered += 1
            elif needed_sheep > 0 and rem_spendable >= 595 and len(current_orders) + len(orders) < 10:
                orders.append(["BUY_ANIMAL", "SHEEP", 1])
                rem_spendable -= 500
                rem_money -= 500
                needed_sheep -= 1
                sheep_ordered += 1
            elif needed_geese > 0 and rem_spendable >= 395 and len(current_orders) + len(orders) < 10:
                orders.append(["BUY_ANIMAL", "GOOSE", 1])
                rem_spendable -= 300
                rem_money -= 300
                needed_geese -= 1
                geese_ordered += 1

        state_summary["cows_ordered"] = cows_ordered
        state_summary["sheep_ordered"] = sheep_ordered
        state_summary["geese_ordered"] = geese_ordered

        return orders, rem_spendable, rem_money

    def check_wheat_feed_reserve(self, state_summary, shed, inventories, spendable, day, current_orders):
        """
        Ensures we maintain sufficient Wheat in the shed to feed all active animals daily.
        """
        orders = []
        rem_spendable = spendable
        total_animals = state_summary["total_active_animals"] + state_summary.get("cows_ordered", 0) + state_summary.get("sheep_ordered", 0) + state_summary.get("geese_ordered", 0)

        if total_animals > 0 and day <= 28:
            total_wheat_held = shed.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in inventories)
            safety_buffer = total_animals * (3 if day <= 5 else 2)
            
            if total_wheat_held < safety_buffer:
                deficit = safety_buffer - total_wheat_held
                wheat_buy_qty = min(deficit + total_animals, int(rem_spendable // 25))
                if wheat_buy_qty > 0 and len(current_orders) + len(orders) < 10:
                    orders.append(["BUY_PRODUCT", "WHEAT", wheat_buy_qty])
                    rem_spendable -= wheat_buy_qty * 25

        return orders, rem_spendable
