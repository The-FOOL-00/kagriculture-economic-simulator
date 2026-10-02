# SPDX-License-Identifier: MIT
"""V46 Phase 8 & 9: Legal Early Opponent Signature Extractor.

Extracts strictly legal, publicly observable features from the early game (Steps 0..T,
where T in [12, 24, 36, 48, 60, 72, 96]) without ANY access to private sheds,
hidden plans, seed or future game state:
- Opponent public cash trajectory and rate of change
- Opponent visible land expansion (quadrants count & timing)
- Opponent visible structures (pastures, coops)
- Opponent visible animals (cows, sheep, geese)
- Opponent visible crops (wheat, carrot, tomato, strawberry, melon)
- Opponent unit count (farmer + hands) and hiring velocity
- Opponent spatial movement signature (farmer radius from shed, hand spread)
- Public market price impacts (early wheat/seed buying or selling pressure)
- Town shop sequence (unlocked shops)
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def extract_early_signature(history: List[Dict[str, Any]], my_player_idx: int, window_t: int) -> Dict[str, float]:
    """Extracts a legal public feature vector from observations up to step window_t."""
    opp_idx = 1 - my_player_idx

    # If history is shorter than window_t, use what is available
    obs_slice = [h for h in history if int(h.get("step", 0) or 0) <= window_t]
    if not obs_slice:
        return {}

    # Extract trajectory sequences
    opp_cash_traj = []
    opp_land_traj = []
    opp_hands_traj = []
    farmer_distances = []

    opp_pasture_count = 0
    opp_coop_count = 0
    opp_cow_count = 0
    opp_sheep_count = 0
    opp_goose_count = 0

    opp_crops = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}

    for obs in obs_slice:
        farms = obs.get("farms", [])
        if len(farms) > opp_idx:
            opp_farm = farms[opp_idx]
            money = float(opp_farm.get("money", 0.0) or 0.0)
            opp_cash_traj.append(money)

            quads = len(opp_farm.get("unlocked_quadrants", ["NW"]) or ["NW"])
            opp_land_traj.append(quads)

            hands = opp_farm.get("hands", []) or []
            opp_hands_traj.append(len(hands))

            farmer_pos = opp_farm.get("farmer", [5, 5])
            farmer_distances.append(abs(farmer_pos[0] - 5) + abs(farmer_pos[1] - 5))

            # Inspect visible tiles from latest observation in slice
            tiles = opp_farm.get("tiles", [])
            for row in tiles:
                for t in row:
                    if isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "PASTURE":
                            opp_pasture_count = max(opp_pasture_count, 1)
                            animal = t.get("animal")
                            if animal == "COW":
                                opp_cow_count += 1
                            elif animal == "SHEEP":
                                opp_sheep_count += 1
                        elif kind == "COOP":
                            opp_coop_count = max(opp_coop_count, 1)
                            if t.get("animal") == "GOOSE":
                                opp_goose_count += 1
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop in opp_crops:
                                opp_crops[crop] += 1

    latest_obs = obs_slice[-1]
    mkt = latest_obs.get("market", {}) or {}
    prices = dict(mkt.get("prices", {}) or {})

    # Compute behavioral features
    initial_cash = opp_cash_traj[0] if opp_cash_traj else 1000.0
    final_cash = opp_cash_traj[-1] if opp_cash_traj else 1000.0
    cash_delta = final_cash - initial_cash
    cash_burn_rate = (initial_cash - min(opp_cash_traj)) if opp_cash_traj else 0.0

    final_land = opp_land_traj[-1] if opp_land_traj else 1
    final_hands = opp_hands_traj[-1] if opp_hands_traj else 0

    town = latest_obs.get("town", {}) or {}
    unlocked = list(town.get("unlocked_shops", []) or [])
    known_shops = ["YARN_STORE", "BAKERY", "BRUNCH_SPOT", "FARMERS_MARKET", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "PET_CAFE", "SALAD_BAR"]

    features = {
        "opp_final_cash": float(final_cash),
        "opp_cash_delta": float(cash_delta),
        "opp_cash_burn_rate": float(cash_burn_rate),
        "opp_land_quadrants": float(final_land),
        "opp_land_expansion": float(1.0 if final_land > 1 else 0.0),
        "opp_hands_count": float(final_hands),
        "opp_pasture_present": float(1.0 if opp_pasture_count > 0 else 0.0),
        "opp_coop_present": float(1.0 if opp_coop_count > 0 else 0.0),
        "opp_cows_visible": float(opp_cow_count),
        "opp_sheep_visible": float(opp_sheep_count),
        "opp_geese_visible": float(opp_goose_count),
        "opp_wheat_plots": float(opp_crops["WHEAT"]),
        "opp_carrot_plots": float(opp_crops["CARROT"]),
        "opp_tomato_plots": float(opp_crops["TOMATO"]),
        "opp_strawberry_plots": float(opp_crops["STRAWBERRY"]),
        "opp_melon_plots": float(opp_crops["MELON"]),
        "opp_mean_farmer_dist": float(np.mean(farmer_distances)) if farmer_distances else 0.0,
        "mkt_wheat_price": float(prices.get("WHEAT", 10)),
        "mkt_carrot_price": float(prices.get("CARROT", 20)),
        "mkt_strawberry_price": float(prices.get("STRAWBERRY", 100)),
        "mkt_melon_price": float(prices.get("MELON", 80)),
        "mkt_milk_price": float(prices.get("MILK", 100)),
        "mkt_wool_price": float(prices.get("WOOL", 100)),
    }
    for s_name in known_shops:
        features[f"town_shop_{s_name.lower()}"] = float(1.0 if s_name in unlocked else 0.0)

    return features
