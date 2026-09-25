# SPDX-License-Identifier: MIT
"""V33 Route Extractor.

Extracts time-indexed strategic plans, event sequences, and multidimensional
route fingerprints from normalized trajectories and expert agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import numpy as np

from candidates.v33_meta_strategy.trajectory_schema import NormalizedTrajectory, StepRecord


@dataclass
class RouteFingerprint:
    route_id: str
    source_file: str
    seed: int
    seat: int
    terminal_cash: float
    # Strategic phases
    worker_trajectory: List[int]       # sampled at steps [12, 24, 48, 72, 120, 240, 360, 480, 600, 719]
    land_trajectory: List[int]         # sampled at steps [72, 144, 288, 432, 576, 719]
    crop_mix: Dict[str, float]         # normalized fraction of crops planted
    livestock_mix: Dict[str, float]    # peak animal stocking
    event_sequence: List[str]          # ordered macro-events
    major_sale_steps: List[int]        # steps with significant SELL orders
    cash_trajectory: List[float]       # cash at days 1..30
    terminal_cash_bucket: str          # LOW (<50k), MID (50-100k), HIGH (>100k)

    def to_feature_vector(self) -> np.ndarray:
        """Flattens fingerprint into a standard numeric feature vector for clustering."""
        features = []
        # Workers (10 dims)
        features.extend(self.worker_trajectory)
        # Land (6 dims)
        features.extend(self.land_trajectory)
        # Standard crops: WHEAT, CARROT, TOMATO, STRAWBERRY, MELON (5 dims)
        for c in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
            features.append(self.crop_mix.get(c, 0.0))
        # Standard animals: COW, SHEEP, GOOSE (3 dims)
        for a in ["COW", "SHEEP", "GOOSE"]:
            features.append(self.livestock_mix.get(a, 0.0))
        # Normalized cash trajectory (30 dims, normalized by 100,000)
        norm_cash = [c / 100000.0 for c in self.cash_trajectory]
        features.extend(norm_cash)
        return np.array(features, dtype=np.float32)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class RouteExtractor:
    WORKER_SAMPLE_STEPS = [12, 24, 48, 72, 120, 240, 360, 480, 600, 719]
    LAND_SAMPLE_STEPS = [72, 144, 288, 432, 576, 719]

    def extract_fingerprint(self, traj: NormalizedTrajectory, route_id: Optional[str] = None) -> RouteFingerprint:
        steps = traj.steps
        n_steps = len(steps)
        r_id = route_id or f"{traj.agent_id}_s{traj.seed}_p{traj.seat}"

        # 1. Worker trajectory
        worker_traj = []
        for s in self.WORKER_SAMPLE_STEPS:
            idx = min(s, n_steps - 1)
            worker_traj.append(steps[idx].worker_count if idx < n_steps else 1)

        # 2. Land trajectory
        land_traj = []
        for s in self.LAND_SAMPLE_STEPS:
            idx = min(s, n_steps - 1)
            land_traj.append(steps[idx].land_count if idx < n_steps else 1)

        # 3. Crop mix
        total_crops: Dict[str, int] = {}
        for rec in steps:
            for c, cnt in rec.crops.items():
                total_crops[c] = max(total_crops.get(c, 0), cnt)
        sum_c = sum(total_crops.values()) or 1
        crop_mix = {c: cnt / sum_c for c, cnt in total_crops.items()}

        # 4. Livestock mix
        total_animals: Dict[str, int] = {}
        for rec in steps:
            for a, cnt in rec.livestock.items():
                total_animals[a] = max(total_animals.get(a, 0), cnt)
        sum_a = sum(total_animals.values()) or 1
        livestock_mix = {a: cnt / sum_a for a, cnt in total_animals.items()}

        # 5. Event sequence
        events = []
        for rec in steps:
            for ev in rec.events:
                if not events or events[-1] != ev:  # deduplicate consecutive identical events
                    events.append(ev)

        # 6. Major sales
        major_sales = []
        for rec in steps:
            for order in rec.market_orders:
                if isinstance(order, (list, tuple)) and len(order) >= 3 and order[0] == "SELL":
                    try:
                        qty = int(order[2])
                        if qty >= 20:
                            major_sales.append(rec.step)
                            break
                    except (ValueError, TypeError):
                        pass

        # 7. Cash trajectory at day boundaries (step 24, 48, ... 720)
        cash_trajectory = []
        for d in range(1, 31):
            s_idx = min(d * 24 - 1, n_steps - 1)
            cash_trajectory.append(steps[s_idx].cash if s_idx < n_steps else 0.0)

        # 8. Cash bucket
        if traj.terminal_cash < 50000:
            bucket = "LOW"
        elif traj.terminal_cash < 100000:
            bucket = "MID"
        else:
            bucket = "HIGH"

        return RouteFingerprint(
            route_id=r_id,
            source_file=traj.metadata.get("source_file", ""),
            seed=traj.seed,
            seat=traj.seat,
            terminal_cash=traj.terminal_cash,
            worker_trajectory=worker_traj,
            land_trajectory=land_traj,
            crop_mix=crop_mix,
            livestock_mix=livestock_mix,
            event_sequence=events[:50],  # keep top 50 macro-events
            major_sale_steps=major_sales,
            cash_trajectory=cash_trajectory,
            terminal_cash_bucket=bucket
        )
