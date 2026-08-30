"""
=============================================================================
ENGINE: OPPONENT SUPPLY FORECASTER
=============================================================================
Mechanistic, observable-state forecaster predicting competitor crop harvests,
livestock production cycles, and imminent market liquidation injections.

Outputs:
1. Imminent harvest horizons (t+1, t+2, t+4 steps).
2. Expected commodity volume and uncertainty bounds [min_vol, max_vol].
3. Competitor strategy archetype classification.
=============================================================================
"""

from config import CROPS, ANIMALS, PRODUCTS

class OpponentSupplyForecaster:
    def __init__(self):
        self.past_sales_history = {p: [] for p in PRODUCTS}
        self.archetype = "UNKNOWN"
        self.total_opponent_melons = 0
        self.total_opponent_cows = 0
        self.total_opponent_sheep = 0

    def analyze_opponent(self, opp_tiles, current_day, current_hour, current_step):
        """
        Inspects opponent farm grid to forecast upcoming commodity harvests and sales.
        """
        board_size = len(opp_tiles) if opp_tiles else 10
        crop_counts = {c: 0 for c in CROPS}
        mature_crops = {c: 0 for c in CROPS}
        imminent_crops_1d = {c: 0 for c in CROPS}
        imminent_crops_2d = {c: 0 for c in CROPS}
        
        cow_count = 0
        sheep_count = 0
        goose_count = 0
        pasture_count = 0
        coop_count = 0

        for y in range(board_size):
            for x in range(board_size):
                t = opp_tiles[y][x] if y < len(opp_tiles) and x < len(opp_tiles[y]) else None
                if not isinstance(t, dict):
                    continue

                kind = t.get("kind")
                if kind == "PLANT":
                    crop = t.get("crop")
                    if crop in crop_counts:
                        crop_counts[crop] += 1
                        planted = t.get("planted_day", 0)
                        age = current_day - planted
                        cd = CROPS.get(crop, {})
                        
                        if cd.get("ongoing", False):
                            if age >= cd.get("first_yield_day", 8):
                                mature_crops[crop] += 1
                            elif age + 1 >= cd.get("first_yield_day", 8):
                                imminent_crops_1d[crop] += 1
                            elif age + 2 >= cd.get("first_yield_day", 8):
                                imminent_crops_2d[crop] += 1
                        else:
                            max_age = cd.get("max_yield_day", 4)
                            if age >= max_age or t.get("yield_units", 0) >= cd.get("max_yield", 4):
                                mature_crops[crop] += 1
                            elif age + 1 >= max_age:
                                imminent_crops_1d[crop] += 1
                            elif age + 2 >= max_age:
                                imminent_crops_2d[crop] += 1

                elif kind == "PASTURE":
                    pasture_count += 1
                    a = t.get("animal")
                    if a == "COW":
                        cow_count += 1
                    elif a == "SHEEP":
                        sheep_count += 1

                elif kind == "COOP":
                    coop_count += 1
                    if t.get("animal") == "GOOSE":
                        goose_count += 1

        self.total_opponent_melons = crop_counts.get("MELON", 0)
        self.total_opponent_cows = cow_count
        self.total_opponent_sheep = sheep_count

        # Archetype Classification
        if self.total_opponent_melons >= 8:
            self.archetype = "MELON_RUSH"
        elif self.total_opponent_cows >= 4 or (self.total_opponent_cows + self.total_opponent_sheep >= 6):
            self.archetype = "LIVESTOCK"
        elif crop_counts.get("CARROT", 0) >= 8 or crop_counts.get("WHEAT", 0) >= 8:
            self.archetype = "FAST_CROP"
        else:
            self.archetype = "BALANCED_HYBRID"

        # Predict commodity injections for horizons t+1 day, t+2 days
        forecast = {}
        for p in PRODUCTS:
            forecast[p] = {
                "mature_now": 0,
                "expected_t1": 0,
                "expected_t2": 0,
                "min_dump_risk": 0,
                "max_dump_risk": 0,
                "imminent_dump_prob": 0.0
            }

        # Melons
        if mature_crops["MELON"] > 0:
            vol = mature_crops["MELON"] * 6
            forecast["MELON"]["mature_now"] = vol
            forecast["MELON"]["min_dump_risk"] = int(vol * 0.7)
            forecast["MELON"]["max_dump_risk"] = vol
            forecast["MELON"]["imminent_dump_prob"] = 0.95
        elif imminent_crops_1d["MELON"] > 0:
            vol = imminent_crops_1d["MELON"] * 6
            forecast["MELON"]["expected_t1"] = vol
            forecast["MELON"]["min_dump_risk"] = int(vol * 0.5)
            forecast["MELON"]["max_dump_risk"] = vol
            forecast["MELON"]["imminent_dump_prob"] = 0.75

        # Carrots
        if mature_crops["CARROT"] > 0:
            vol = mature_crops["CARROT"] * 3
            forecast["CARROT"]["mature_now"] = vol
            forecast["CARROT"]["min_dump_risk"] = vol
            forecast["CARROT"]["max_dump_risk"] = vol
            forecast["CARROT"]["imminent_dump_prob"] = 0.90

        # Milk (Cows yield every 2 days)
        if cow_count > 0:
            daily_milk = cow_count * 0.5
            forecast["MILK"]["expected_t1"] = int(daily_milk)
            forecast["MILK"]["max_dump_risk"] = cow_count
            forecast["MILK"]["imminent_dump_prob"] = 0.60

        # Wool (Sheep yield every 3 days)
        if sheep_count > 0:
            daily_wool = sheep_count * 0.33
            forecast["WOOL"]["expected_t1"] = int(daily_wool)
            forecast["WOOL"]["max_dump_risk"] = sheep_count
            forecast["WOOL"]["imminent_dump_prob"] = 0.50

        return {
            "archetype": self.archetype,
            "crop_counts": crop_counts,
            "mature_crops": mature_crops,
            "cow_count": cow_count,
            "sheep_count": sheep_count,
            "forecast": forecast
        }
