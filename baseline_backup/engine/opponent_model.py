"""
=============================================================================
ENGINE: OPPONENT RADAR & HARVEST PREDICTOR
=============================================================================
Scans opponent farm state, predicts harvest timings, classifies strategic archetypes,
and generates anti-glut frontrunning signals.
=============================================================================
"""

from config import CROPS, ANIMALS, PRODUCTS


class OpponentModel:
    def __init__(self):
        pass

    def analyze_opponent_farm(self, opp_tiles, current_day):
        """
        Analyzes visible opponent farm tiles and predicts imminent harvests.
        """
        crop_counts = {p: 0 for p in PRODUCTS}
        imminent_harvests = {p: 0 for p in PRODUCTS}
        animal_counts = {"COW": 0, "SHEEP": 0, "GOOSE": 0}

        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "PLANT":
                        crop = t.get("crop")
                        if crop in crop_counts:
                            crop_counts[crop] += 1
                            planted = t.get("planted_day", 0)
                            age = current_day - planted
                            cdata = CROPS.get(crop, {})
                            
                            if not cdata.get("ongoing", False):
                                max_d = cdata.get("max_yield_day", 4)
                                # Flag imminent harvest if within 1 day of max yield
                                if age >= max_d - 1:
                                    imminent_harvests[crop] += 1
                            else:
                                first_d = cdata.get("first_yield_day", 10)
                                if age >= first_d:
                                    imminent_harvests[crop] += 1

                    elif "animal" in t and t.get("animal"):
                        animal = t.get("animal")
                        if animal in animal_counts:
                            animal_counts[animal] += 1
                            if animal == "COW": crop_counts["MILK"] += 1
                            elif animal == "SHEEP": crop_counts["WOOL"] += 1
                            elif animal == "GOOSE": crop_counts["EGG"] += 1

        # Classify archetype
        total_crops = sum(crop_counts[c] for c in ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"])
        total_animals = sum(animal_counts.values())

        if total_animals >= 2:
            archetype = "LIVESTOCK_HYBRID"
        elif crop_counts["STRAWBERRY"] >= 15:
            archetype = "STRAWBERRY_HEAVY"
        elif crop_counts["MELON"] >= 15:
            archetype = "MELON_BURST"
        else:
            archetype = "BALANCED_CROP"

        return {
            "archetype": archetype,
            "crop_counts": crop_counts,
            "animal_counts": animal_counts,
            "imminent_harvests": imminent_harvests
        }

    def should_frontrun_opponent(self, product, imminent_count):
        """
        Determines if we must dump our inventory of `product` immediately
        before the opponent floods the market.
        """
        # If opponent has 6+ units maturing within 1 day, frontrun now!
        return imminent_count >= 6
