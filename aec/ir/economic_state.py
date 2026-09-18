# SPDX-License-Identifier: MIT
"""Master Economic State Intermediate Representation (IR)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import (
    CROP_GROWTH_DAYS,
    CROPS,
    FINAL_STEP,
    PRODUCTS,
    TURNS_PER_DAY,
)
from aec.ir.farm_state import FarmState, PipelineItem
from aec.ir.market_state import (
    BASE_PRICES,
    MarketState,
    compute_expected_absorption,
)
from aec.ir.opponent_state import OpponentState, extract_opponent_state
from aec.ir.worker_state import (
    WorkerEntity,
    WorkerState,
    min_distance_to_shed,
)


def get_game_phase(step: int) -> str:
    if step < 24:
        return "OPENING"
    elif step < 144:
        return "EXPANSION"
    elif step < 574:
        return "PRODUCTION"
    elif step < 670:
        return "WIND_DOWN"
    else:
        return "TERMINAL"


@dataclass
class EconomicState:
    """Master Economic IR representing the complete game at decision time."""
    step: int = 0
    day: int = 0
    hour: int = 0
    player: int = 0
    phase: str = ""
    remaining_horizon: Optional[int] = None
    terminal_distance: Optional[int] = None

    workers: WorkerState = field(default_factory=WorkerState)
    farm: FarmState = field(default_factory=FarmState)
    market: MarketState = field(default_factory=MarketState)
    opponent: OpponentState = field(default_factory=OpponentState)
    
    # Feasibility windows: crop -> can reach harvest before step 718 if planted today
    crop_feasibility: Dict[str, bool] = field(default_factory=dict)
    raw_obs_snapshot: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.day == 0 and self.step > 0:
            self.day = self.step // TURNS_PER_DAY
        if self.hour == 0 and self.step > 0:
            self.hour = self.step % TURNS_PER_DAY
        if not self.phase:
            self.phase = get_game_phase(self.step)
        if self.remaining_horizon is None:
            self.remaining_horizon = max(0, FINAL_STEP - self.step)
        if self.terminal_distance is None:
            self.terminal_distance = self.remaining_horizon

    @property
    def is_terminal_phase(self) -> bool:
        return self.phase == "TERMINAL"

    @property
    def is_wind_down_phase(self) -> bool:
        return self.phase in ("WIND_DOWN", "TERMINAL")

    @property
    def cash(self) -> float:
        return self.farm.cash


def build_economic_state(
    observation: Dict[str, Any],
    previous_state: Optional[EconomicState] = None
) -> EconomicState:
    """Deterministically construct Economic IR from raw game observation."""
    step = int(observation.get("step", 0) or 0)
    day = int(observation.get("day", step // TURNS_PER_DAY) or 0)
    hour = int(observation.get("hour", step % TURNS_PER_DAY) or 0)
    player = int(observation.get("player", 0) or 0)
    
    phase = get_game_phase(step)
    remaining_horizon = max(0, FINAL_STEP - step)
    terminal_distance = remaining_horizon

    # 1. Own Farm extraction
    farms = observation.get("farms", []) or []
    own_farm = farms[player] if player < len(farms) and isinstance(farms[player], dict) else {}
    opp_farm = farms[1 - player] if 1 - player < len(farms) and isinstance(farms[1 - player], dict) else {}
    
    cash = float(own_farm.get("money", 0.0) or 0.0)
    tiles = copy.deepcopy(own_farm.get("tiles", []) or [])
    quadrants = list(own_farm.get("unlocked_quadrants", ["NW"]) or ["NW"])
    
    # Private inventory
    private = observation.get("private", {}) or {}
    raw_shed = private.get("shed", {}) or {}
    shed_inv = {p: int(raw_shed.get(p, 0) or 0) for p in PRODUCTS}
    seeds = {c: int((private.get("seeds", {}) or {}).get(c, 0) or 0) for c in CROPS}
    
    # Workers extraction
    farmer_pos = tuple(own_farm.get("farmer", [4, 4]))
    hands = own_farm.get("hands", []) or []
    raw_invs = private.get("inventories", []) or []
    
    workers_list: List[WorkerEntity] = []
    carried_totals: Dict[str, int] = {p: 0 for p in PRODUCTS}
    
    all_positions = [farmer_pos] + [tuple(h) for h in hands]
    for w_idx, pos in enumerate(all_positions):
        w_inv_raw = raw_invs[w_idx] if w_idx < len(raw_invs) and isinstance(raw_invs[w_idx], dict) else {}
        w_cargo = {p: int(w_inv_raw.get(p, 0) or 0) for p in PRODUCTS if int(w_inv_raw.get(p, 0) or 0) > 0}
        for p, q in w_cargo.items():
            carried_totals[p] += q
            
        dist_shed = min_distance_to_shed(pos)
        w_entity = WorkerEntity(
            worker_id=w_idx,
            position=pos,
            task="PASS",
            cargo=w_cargo,
            deposit_path_len=dist_shed,
            available_slack_steps=0,
            marginal_opportunity_value=0.0
        )
        workers_list.append(w_entity)
        
    worker_state = WorkerState(workers=workers_list)
    
    # Farm pipeline extraction
    pipeline: List[PipelineItem] = []
    expected_harvests: Dict[str, int] = {p: 0 for p in PRODUCTS}
    
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                crop = tile.get("crop")
                yield_units = int(tile.get("yield_units", 0) or 0)
                growth_days = CROP_GROWTH_DAYS.get(crop, 2)
                planted_day = int(tile.get("planted_day", day) or day)
                days_elapsed = day - planted_day
                days_left = max(0, growth_days - days_elapsed)
                
                pipeline.append(PipelineItem(
                    item_type="PLANT",
                    subtype=crop,
                    position=(x, y),
                    days_to_next_yield=days_left,
                    yield_quantity=max(1, yield_units),
                    is_ongoing=crop in ("STRAWBERRY", "TOMATO"),
                    requires_input=not bool(tile.get("watered_today"))
                ))
                if days_left == 0 and yield_units > 0 and crop in expected_harvests:
                    expected_harvests[crop] += yield_units
                    
            elif kind in ("COOP", "PASTURE"):
                animal = tile.get("animal")
                if animal:
                    pipeline.append(PipelineItem(
                        item_type="ANIMAL",
                        subtype=animal,
                        position=(x, y),
                        days_to_next_yield=1,
                        yield_quantity=1,
                        is_ongoing=True,
                        requires_input=not bool(tile.get("fed_today"))
                    ))

    farm_state = FarmState(
        cash=cash,
        carried_inventory=carried_totals,
        shed_inventory=shed_inv,
        capacity=100,
        seeds=seeds,
        production_pipeline=pipeline,
        expected_harvests=expected_harvests,
        unlocked_quadrants=quadrants,
        tiles=tiles,
        hires_today=int(own_farm.get("hires_today", 0) or 0)
    )

    
    # 2. Market extraction
    market_raw = observation.get("market", {}) or {}
    raw_prices = market_raw.get("prices", {}) or {}
    raw_market_inv = market_raw.get("inventory", {}) or {}
    
    current_prices = {p: int(raw_prices.get(p, BASE_PRICES.get(p, 1)) or 1) for p in PRODUCTS}
    market_inv = {p: int(raw_market_inv.get(p, 10000) or 10000) for p in PRODUCTS}
    
    town = observation.get("town", {}) or {}
    unlocked_shops = list(town.get("unlocked_shops", []) or [])
    steps_to_town_tick = 4 - (step % 4)
    expected_absorption = compute_expected_absorption(unlocked_shops)
    
    liquidity_ratios = {
        p: current_prices[p] / max(1.0, float(BASE_PRICES.get(p, 1))) for p in PRODUCTS
    }
    
    market_state = MarketState(
        current_prices=current_prices,
        market_inventory=market_inv,
        unlocked_shops=unlocked_shops,
        steps_to_town_tick=steps_to_town_tick,
        expected_absorption=expected_absorption,
        liquidity_ratios=liquidity_ratios
    )
    
    # 3. Opponent state extraction
    prev_opp = previous_state.opponent if previous_state else None
    opponent_state = extract_opponent_state(opp_farm, step, current_prices, prev_opp)
    
    # 4. Crop feasibility windows
    feasibility: Dict[str, bool] = {}
    for crop in CROPS:
        req_steps = CROP_GROWTH_DAYS.get(crop, 2) * TURNS_PER_DAY
        feasibility[crop] = (remaining_horizon >= req_steps)
        
    return EconomicState(
        step=step,
        day=day,
        hour=hour,
        player=player,
        phase=phase,
        remaining_horizon=remaining_horizon,
        terminal_distance=terminal_distance,
        workers=worker_state,
        farm=farm_state,
        market=market_state,
        opponent=opponent_state,
        crop_feasibility=feasibility,
        raw_obs_snapshot=copy.deepcopy(observation)
    )
