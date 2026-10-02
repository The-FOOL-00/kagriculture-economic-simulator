# SPDX-License-Identifier: MIT
"""V46 Phase 1: Replay & Strategy Intelligence Fingerprint Extractor.

Parses public Kaggle replays, online tournament episodes, and local agents to extract:
1. Macro fingerprints (land timing, hires, animal mix, crop mix, fertilizer, watering, feeding, care, harvest).
2. Market fingerprints (SELL/BUY density, timing, terminal liquidation shape).
3. 720-step trajectory features (cash by day, shed inventory, order density).
"""

from __future__ import annotations
import glob
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v46.phase0.governance import assert_seed_safe

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
ANIMALS = ["GOOSE", "COW", "SHEEP"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


def extract_fingerprint_from_replay_steps(steps: List[List[Dict[str, Any]]], player_idx: int) -> Dict[str, Any]:
    """Extracts a comprehensive economic and behavioral fingerprint for player_idx."""
    n_steps = len(steps)
    cash_trajectory = []
    shed_volume = []
    hires_by_day = [0] * 30
    land_purchases = []
    first_land_step = None
    animal_counts_by_day = {a: [0] * 30 for a in ANIMALS}
    crop_counts_by_day = {c: [0] * 30 for c in CROPS}
    watering_count = 0
    fertilize_count = 0
    care_count = 0
    feed_count = 0
    harvest_count = 0
    sell_count = 0
    buy_count = 0
    commodity_sales = {p: 0 for p in PRODUCTS}
    terminal_sales_steps = []

    last_quadrants = 1
    total_hires = 0

    for step_i in range(n_steps):
        s = steps[step_i]
        if player_idx >= len(s):
            continue
        state = s[player_idx]
        obs = state.get("observation", {}) or {}
        act = state.get("action", {}) or {}

        day = step_i // 24
        day = min(day, 29)

        # Observation parsing
        farms = obs.get("farms", [])
        if player_idx < len(farms):
            farm = farms[player_idx]
            money = float(farm.get("money", 0.0) or 0.0)
            cash_trajectory.append(money)
            quads = len(farm.get("unlocked_quadrants", []) or [])
            if quads > last_quadrants:
                if first_land_step is None:
                    first_land_step = step_i
                land_purchases.append(step_i)
                last_quadrants = quads

            # Tile inspections
            tiles = farm.get("tiles", [])
            for row in tiles:
                for t in row:
                    if isinstance(t, dict):
                        kind = t.get("kind")
                        if kind in ("COOP", "PASTURE") and t.get("animal"):
                            a = t.get("animal")
                            if a in animal_counts_by_day:
                                animal_counts_by_day[a][day] = max(animal_counts_by_day[a][day], 1)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop in crop_counts_by_day:
                                crop_counts_by_day[crop][day] = max(crop_counts_by_day[crop][day], 1)

        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        shed_volume.append(sum(shed.values()))

        # Action parsing
        farmer_acts = act.get("farmer", []) or []
        hands_acts = act.get("hands", []) or []
        market_acts = act.get("market", []) or []

        all_unit_acts = [farmer_acts] + list(hands_acts)
        for uact in all_unit_acts:
            if not uact:
                continue
            op = uact[0]
            if op == "WATER":
                watering_count += 1
            elif op == "FERTILIZE":
                fertilize_count += 1
            elif op == "CARE":
                care_count += 1
            elif op == "FEED":
                feed_count += 1
            elif op == "HARVEST":
                harvest_count += 1

        for mact in market_acts:
            if not mact or len(mact) == 0:
                continue
            mop = mact[0]
            if mop == "HIRE":
                total_hires += 1
                hires_by_day[day] += 1
            elif mop == "SELL":
                sell_count += 1
                if len(mact) > 1 and mact[1] in commodity_sales:
                    qty = int(mact[2]) if len(mact) > 2 else 1
                    commodity_sales[mact[1]] += qty
                if step_i >= 690:
                    terminal_sales_steps.append(step_i)
            elif mop.startswith("BUY"):
                buy_count += 1

    terminal_cash = cash_trajectory[-1] if cash_trajectory else 0.0

    return {
        "terminal_cash": terminal_cash,
        "first_land_step": first_land_step if first_land_step is not None else -1,
        "land_purchase_count": len(land_purchases),
        "total_hires": total_hires,
        "hires_by_day": hires_by_day,
        "watering_count": watering_count,
        "fertilize_count": fertilize_count,
        "care_count": care_count,
        "feed_count": feed_count,
        "harvest_count": harvest_count,
        "sell_count": sell_count,
        "buy_count": buy_count,
        "commodity_sales": commodity_sales,
        "terminal_liquidation_steps": len(terminal_sales_steps),
        "mean_shed_volume": float(np.mean(shed_volume)) if shed_volume else 0.0,
        "peak_shed_volume": float(np.max(shed_volume)) if shed_volume else 0.0,
        "cow_presence": int(any(c > 0 for c in animal_counts_by_day["COW"])),
        "sheep_presence": int(any(s > 0 for s in animal_counts_by_day["SHEEP"])),
        "goose_presence": int(any(g > 0 for g in animal_counts_by_day["GOOSE"])),
        "cash_trajectory_deciles": [float(np.mean(cash_trajectory[i*72:(i+1)*72])) if len(cash_trajectory) >= (i+1)*72 else 0.0 for i in range(10)],
    }


def process_all_available_replays() -> List[Dict[str, Any]]:
    """Discovers and parses all available public replay JSON files."""
    patterns = [
        os.path.join(REPO_ROOT, "replays", "*.json"),
        os.path.join(REPO_ROOT, "replays", "raw", "*.json"),
        os.path.join(REPO_ROOT, "replays", "live_tournament", "*.json"),
        os.path.join(REPO_ROOT, "external_repos", "lixingtao123-Kaggriculture", "online_replays", "*.json"),
        os.path.join(REPO_ROOT, "external_repos", "lixingtao123-Kaggriculture", "online_replays", "*", "*.json"),
    ]

    replay_files = []
    for pat in patterns:
        replay_files.extend(glob.glob(pat))

    # Deduplicate paths
    replay_files = sorted(list(set(replay_files)))
    print(f"Discovered {len(replay_files)} public replay files across repository.")

    fingerprints = []
    processed_count = 0

    for rf in replay_files:
        try:
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)

            steps = data.get("steps", [])
            if len(steps) < 100:
                continue

            info = data.get("info", {}) or {}
            cfg = data.get("configuration", {}) or {}
            seed = cfg.get("seed")

            # Check holdout quarantine
            if seed is not None:
                try:
                    assert_seed_safe(int(seed))
                except Exception:
                    continue  # Skip forbidden seed replays

            # Extract for both player 0 and player 1
            for p_idx in [0, 1]:
                fp = extract_fingerprint_from_replay_steps(steps, p_idx)
                fp["source_file"] = os.path.basename(rf)
                fp["player_idx"] = p_idx
                fp["seed"] = seed
                fingerprints.append(fp)

            processed_count += 1
            if processed_count % 20 == 0:
                print(f"Processed {processed_count}/{len(replay_files)} replays...")

        except Exception as e:
            continue

    print(f"Successfully extracted {len(fingerprints)} player strategy fingerprints from {processed_count} replays.")
    return fingerprints


if __name__ == "__main__":
    fps = process_all_available_replays()
    out_dir = os.path.dirname(__file__)
    out_file = os.path.join(out_dir, "replay_fingerprints.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(fps, f, indent=2)
    print(f"Saved replay fingerprints to {out_file}")
