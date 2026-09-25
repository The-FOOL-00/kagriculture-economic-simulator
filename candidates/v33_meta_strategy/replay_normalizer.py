# SPDX-License-Identifier: MIT
"""V33 Replay Normalizer.

Transforms raw Kaggle replay dictionaries into canonical NormalizedTrajectory objects,
extracting time-indexed state records, action traces, and strategic event markers.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json

from candidates.v33_meta_strategy.trajectory_schema import StepRecord, NormalizedTrajectory


def _count_crops_and_livestock(tiles: List[Dict[str, Any]]) -> tuple[Dict[str, int], Dict[str, int]]:
    crops: Dict[str, int] = {}
    livestock: Dict[str, int] = {}
    if not isinstance(tiles, list):
        return crops, livestock
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        kind = tile.get("kind")
        if kind == "CROP":
            crop_type = tile.get("crop", "UNKNOWN")
            crops[crop_type] = crops.get(crop_type, 0) + 1
        elif kind in ("PASTURE", "COOP"):
            animal = tile.get("animal", kind)
            livestock[animal] = livestock.get(animal, 0) + 1
    return crops, livestock


class ReplayNormalizer:
    def __init__(self):
        pass

    def normalize_replay(self, replay_data: Dict[str, Any], filepath: str = "") -> List[NormalizedTrajectory]:
        """Normalizes a 2-player Kaggle replay into two NormalizedTrajectory instances (Seat 0 and Seat 1)."""
        steps_data = replay_data.get("steps", [])
        if len(steps_data) < 700:
            return []

        cfg = replay_data.get("configuration", {})
        seed = int(cfg.get("seed", 0) or 0)
        episode_id = str(replay_data.get("id", os.path.basename(filepath)))
        agents_meta = replay_data.get("agents", [])
        rewards = replay_data.get("rewards", [0.0, 0.0]) or [0.0, 0.0]

        agent_names = [
            (agents_meta[i].get("name") if i < len(agents_meta) and isinstance(agents_meta[i], dict) else f"Player_{i}")
            for i in range(2)
        ]

        trajectories = []
        for seat in (0, 1):
            opp_seat = 1 - seat
            agent_id = agent_names[seat] or f"Seat_{seat}"
            opponent_id = agent_names[opp_seat] or f"Seat_{opp_seat}"
            term_cash = float(rewards[seat] if len(rewards) > seat and rewards[seat] is not None else 0.0)
            opp_cash = float(rewards[opp_seat] if len(rewards) > opp_seat and rewards[opp_seat] is not None else 0.0)

            if term_cash > opp_cash:
                outcome = "W"
            elif term_cash < opp_cash:
                outcome = "L"
            else:
                outcome = "T"

            step_records = []
            prev_workers = 1
            prev_land = 1

            for t, step_pair in enumerate(steps_data):
                if seat >= len(step_pair):
                    continue
                p_step = step_pair[seat]
                opp_p_step = step_pair[opp_seat] if opp_seat < len(step_pair) else {}

                obs = p_step.get("observation", {}) or {}
                act = p_step.get("action", {}) or {}
                farms = obs.get("farms", []) or []
                farm = farms[seat] if seat < len(farms) and isinstance(farms[seat], dict) else {}
                opp_farm = farms[opp_seat] if opp_seat < len(farms) and isinstance(farms[opp_seat], dict) else {}

                private = obs.get("private", {}) or {}
                shed = private.get("shed", {}) or {}
                market = obs.get("market", {}) or {}
                prices = market.get("prices", {}) or {}

                cash = float(farm.get("money", 0.0) or 0.0)
                tiles = farm.get("tiles", []) or []
                land_count = len(farm.get("unlocked_quadrants", [1]) or [1])
                hands = farm.get("hands", []) or []
                worker_count = 1 + len(hands)

                crops, livestock = _count_crops_and_livestock(tiles)
                mkt_orders = act.get("market", []) or []

                # Detect key strategic events
                events = []
                if worker_count > prev_workers:
                    events.append(f"HIRE_WORKER_{worker_count}")
                if land_count > prev_land:
                    events.append(f"EXPAND_LAND_{land_count}")

                for order in mkt_orders:
                    if isinstance(order, (list, tuple)) and len(order) > 0:
                        cmd = order[0]
                        if cmd == "BUY_ANIMAL":
                            events.append(f"BUY_ANIMAL_{order[1] if len(order)>1 else ''}")
                        elif cmd == "SELL":
                            events.append(f"SELL_{order[1] if len(order)>1 else ''}")

                opp_visible = {
                    "money": float(opp_farm.get("money", 0.0) or 0.0),
                    "workers": 1 + len(opp_farm.get("hands", []) or []),
                    "land": len(opp_farm.get("unlocked_quadrants", [1]) or [1]),
                }

                rec = StepRecord(
                    step=t,
                    cash=cash,
                    land_count=land_count,
                    worker_count=worker_count,
                    worker_states=[{"farmer": farm.get("farmer")}] + [{"hand": h} for h in hands],
                    crops=crops,
                    livestock=livestock,
                    inventory=shed,
                    market_prices=prices,
                    action=act,
                    market_orders=mkt_orders,
                    opponent_observable=opp_visible,
                    events=events
                )
                step_records.append(rec)
                prev_workers = worker_count
                prev_land = land_count

            traj = NormalizedTrajectory(
                episode_id=episode_id,
                seed=seed,
                seat=seat,
                agent_id=agent_id,
                opponent_id=opponent_id,
                terminal_cash=term_cash,
                opponent_cash=opp_cash,
                outcome=outcome,
                steps=step_records,
                metadata={"source_file": filepath}
            )
            trajectories.append(traj)

        return trajectories
