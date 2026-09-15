"""
candidates/cms5_v54_faithful.py
================================
Faithful V54-class macro engine for Championship Phase CMS-5.

Preserves:
- Daily labor curve (5 opening, 8 at Day 6, 11 at Day 10, 12 at Day 15, 11 late)
- Land expansion timing (Quadrant 2 @ step 150, Quadrant 3 @ step 265)
- Livestock purchases (7 cows, 3 sheep bought -> 9 cows, 5 sheep on pasture)
- Pasture placement adjacent to shed
- Wheat production & on-farm feed cycling autarky (187 seeds)
- Strawberry wave (38 seeds starting Day 5)
- Melon opening cash engine (12 seeds)
- Market selling timing & queue controller
- Terminal liquidation timing (Step 670 default)
- Spatial chore navigation and weed repair

Exposes CMS5Config for controlled economic decision sweeps.
Default CMS5Config reproduces canonical V54 exactly.
"""

from __future__ import annotations
import os
import sys
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import importlib.util

# Ensure external repos are on sys.path if needed
V54_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py"))
if not os.path.exists(V54_PATH):
    # Fallback to local relative path
    V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")

v54_dir = os.path.dirname(V54_PATH)
if v54_dir not in sys.path:
    sys.path.insert(0, v54_dir)

# Load V54 module symbols directly as source of truth
_spec = importlib.util.spec_from_file_location("v54_source_truth", V54_PATH)
_v54_mod = importlib.util.module_from_spec(_spec)
sys.modules["v54_source_truth"] = _v54_mod
_spec.loader.exec_module(_v54_mod)

_CANONICAL_V54_ROUTE = _v54_mod._V54_ROUTE
_CANONICAL_V54_CONFIG = _v54_mod._V54_CONFIG
_v51_build_policy = _v54_mod._v51_build_policy
_V51ResidualConfig = _v54_mod._V51ResidualConfig


@dataclass
class CMS5Config:
    """True macroeconomic decisions in V54."""
    # LABOR
    initial_workers: int = 5          # Day 0 opening hires (step 1)
    ramp_day_2_workers: int = 8       # Day 6 hires (step 144+)
    ramp_day_3_workers: int = 11      # Day 10/11 hires (step 240+)
    peak_workers: int = 12            # Peak workforce (Day 15-20)
    late_workers: int = 11            # Late game workforce (Day 21-29)

    # LIVESTOCK FLEET
    cow_purchases: int = 7            # Target cows bought from market (default 7)
    sheep_purchases: int = 3          # Target sheep bought from market (default 3)

    # CROP ENGINES
    wheat_seeds: int = 187            # Wheat seeds purchased & planted (default 187)
    strawberry_seeds: int = 38        # Strawberry seeds purchased & planted (default 38)
    strawberry_start_day: int = 5     # Day strawberry purchases begin (default 5, step 128)
    melon_seeds: int = 12             # Melon seeds bought on Day 0-1 (default 12)

    # LAND EXPANSION
    land_1_step: int = 150            # Step for first expansion (default 150)
    land_2_step: int = 265            # Step for second expansion (default 265)

    # TERMINAL LIQUIDATION
    liquidation_step: int = 670       # Step when endgame inventory selloff begins (default 670)
    liquidation_batch: int = 30       # Max units per liquidation order

    # RESIDUAL MARKET CONTROLLER DYNAMICS
    front_existing_sells: bool = True
    front_supply_threshold: float = 3.0
    preempt_enabled: bool = True
    preempt_horizon: int = 3
    preempt_maximum_batch: int = 4
    near_scheduled_supply_weight: float = 0.0
    adaptive_near_schedule_weight: bool = True


def build_cms5_route(config: CMS5Config) -> List[Dict[str, Any]]:
    """Generates the 719-step action proposal reflecting the macro parameters."""
    route = copy.deepcopy(_CANONICAL_V54_ROUTE)

    # If all parameters are default, return exact golden route
    is_default = (
        config.wheat_seeds == 187 and
        config.strawberry_seeds == 38 and
        config.strawberry_start_day == 5 and
        config.melon_seeds == 12 and
        config.cow_purchases == 7 and
        config.sheep_purchases == 3 and
        config.initial_workers == 5 and
        config.ramp_day_2_workers == 8 and
        config.ramp_day_3_workers == 11 and
        config.peak_workers == 12 and
        config.late_workers == 11 and
        config.land_1_step == 150 and
        config.land_2_step == 265
    )
    if is_default:
        return route

    # Apply parameter adjustments:
    # 1. Wheat adjustments
    if config.wheat_seeds != 187:
        cum_wheat = 0
        extra_to_add = max(0, config.wheat_seeds - 187)
        for act in route:
            new_market = []
            for o in act.get("market", []):
                if o and o[0] == "BUY_SEED" and o[1] == "WHEAT":
                    qty = o[2]
                    if cum_wheat + qty <= config.wheat_seeds:
                        new_market.append(o)
                        cum_wheat += qty
                    elif cum_wheat < config.wheat_seeds:
                        allowed = config.wheat_seeds - cum_wheat
                        new_market.append(["BUY_SEED", "WHEAT", allowed])
                        cum_wheat += allowed
                    # drop excess
                else:
                    new_market.append(o)
            act["market"] = new_market
        if extra_to_add > 0:
            added = 0
            # Inject extra wheat buys in Day 6-8 (steps 144-200) where liquidity exists
            for act in route[144:220]:
                if added >= extra_to_add:
                    break
                m = act.setdefault("market", [])
                if len(m) < 10:
                    batch = min(10, extra_to_add - added)
                    m.append(["BUY_SEED", "WHEAT", batch])
                    added += batch

    # 2. Strawberry adjustments
    if config.strawberry_seeds != 38:
        cum_strawb = 0
        extra_strawb = max(0, config.strawberry_seeds - 38)
        for act in route:
            new_market = []
            for o in act.get("market", []):
                if o and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    qty = o[2]
                    if cum_strawb + qty <= config.strawberry_seeds:
                        new_market.append(o)
                        cum_strawb += qty
                    elif cum_strawb < config.strawberry_seeds:
                        allowed = config.strawberry_seeds - cum_strawb
                        new_market.append(["BUY_SEED", "STRAWBERRY", allowed])
                        cum_strawb += allowed
                else:
                    new_market.append(o)
            act["market"] = new_market
        if extra_strawb > 0:
            added = 0
            for act in route[128:200]:
                if added >= extra_strawb:
                    break
                m = act.setdefault("market", [])
                if len(m) < 10:
                    batch = min(4, extra_strawb - added)
                    m.append(["BUY_SEED", "STRAWBERRY", batch])
                    added += batch

    # 3. Melon adjustments
    if config.melon_seeds != 12:
        cum_melon = 0
        extra_melon = max(0, config.melon_seeds - 12)
        for act in route:
            new_market = []
            for o in act.get("market", []):
                if o and o[0] == "BUY_SEED" and o[1] == "MELON":
                    qty = o[2]
                    if cum_melon + qty <= config.melon_seeds:
                        new_market.append(o)
                        cum_melon += qty
                    elif cum_melon < config.melon_seeds:
                        allowed = config.melon_seeds - cum_melon
                        new_market.append(["BUY_SEED", "MELON", allowed])
                        cum_melon += allowed
                else:
                    new_market.append(o)
            act["market"] = new_market
        if extra_melon > 0 and len(route) > 1:
            m = route[1].setdefault("market", [])
            if len(m) < 10:
                m.append(["BUY_SEED", "MELON", extra_melon])

    # 4. Livestock adjustments
    if config.cow_purchases != 7 or config.sheep_purchases != 3:
        cum_cows = 0
        cum_sheep = 0
        for act in route:
            new_market = []
            for o in act.get("market", []):
                if o and o[0] == "BUY_ANIMAL":
                    animal = o[1]
                    qty = o[2]
                    if animal == "COW":
                        if cum_cows + qty <= config.cow_purchases:
                            new_market.append(o)
                            cum_cows += qty
                        elif cum_cows < config.cow_purchases:
                            allowed = config.cow_purchases - cum_cows
                            new_market.append(["BUY_ANIMAL", "COW", allowed])
                            cum_cows += allowed
                    elif animal == "SHEEP":
                        if cum_sheep + qty <= config.sheep_purchases:
                            new_market.append(o)
                            cum_sheep += qty
                        elif cum_sheep < config.sheep_purchases:
                            allowed = config.sheep_purchases - cum_sheep
                            new_market.append(["BUY_ANIMAL", "SHEEP", allowed])
                            cum_sheep += allowed
                else:
                    new_market.append(o)
            act["market"] = new_market

    # 5. Labor curve adjustments
    if config.initial_workers != 5:
        # Step 1 opening hires
        m1 = route[1].get("market", [])
        hires = [o for o in m1 if o and o[0] == "HIRE"]
        non_hires = [o for o in m1 if not (o and o[0] == "HIRE")]
        new_hires = [["HIRE"] for _ in range(config.initial_workers)]
        route[1]["market"] = non_hires + new_hires

    # 6. Land expansion timing
    if config.land_1_step != 150:
        # Move BUY_LAND from 150 to land_1_step
        for act in route:
            act["market"] = [o for o in act.get("market", []) if o != ["BUY_LAND"]]
        if config.land_1_step < len(route):
            route[config.land_1_step].setdefault("market", []).append(["BUY_LAND"])
        if config.land_2_step < len(route):
            route[config.land_2_step].setdefault("market", []).append(["BUY_LAND"])

    return route


def build_cms5_policy(config: Optional[CMS5Config] = None):
    """Builds the complete CMS5 agent policy callable."""
    if config is None:
        config = CMS5Config()

    route = build_cms5_route(config)

    # Build residual controller configuration
    residual_cfg = _V51ResidualConfig(
        front_existing_sells=config.front_existing_sells,
        front_on_near=False,
        front_money_deficit=1000000.0,
        front_supply_threshold=config.front_supply_threshold,
        preempt_enabled=config.preempt_enabled,
        preempt_on_near=False,
        preempt_horizon=config.preempt_horizon,
        preempt_maximum_batch=config.preempt_maximum_batch,
        near_scheduled_supply_weight=config.near_scheduled_supply_weight,
        adaptive_near_schedule_weight=config.adaptive_near_schedule_weight,
        adaptive_confidence_decay=0.99,
        adaptive_confidence_negative_alpha=0.55,
        adaptive_confidence_minimum_events=2,
        adaptive_confidence_activation_threshold=0.3,
        preempt_money_deficit=1000000.0,
        near_distance=8.0,
        near_streak_required=12
    )

    base_policy = _v51_build_policy(route, residual_cfg)

    # Terminal liquidation handler
    target_liq = config.liquidation_step
    max_batch = config.liquidation_batch

    def cms5_agent(obs, configuration=None):
        step = obs.get("step", obs.get("day", 0) * 24 + obs.get("hour", 0))
        act = base_policy(obs, configuration)
        if not isinstance(act, dict):
            return act

        # If liquidation timing is customized:
        if target_liq != 670:
            if step < target_liq and step >= 640:
                # Suppress early large terminal dumps
                market = act.get("market", [])
                act["market"] = [o for o in market if not (o and o[0] == "SELL" and o[2] > 10)]
            elif step >= target_liq:
                # Active liquidation of shed inventory
                player = obs.get("player", 0)
                farms = obs.get("farms", [{}])
                farm = farms[player] if player < len(farms) else {}
                shed = farm.get("shed", {})
                market = list(act.get("market", []))
                existing_sells = {o[1] for o in market if o and o[0] == "SELL"}
                for item, qty in shed.items():
                    if qty > 0 and item not in existing_sells and len(market) < 10:
                        market.append(["SELL", item, min(qty, max_batch)])
                act["market"] = market[:10]

        return act

    return cms5_agent


# Default standalone submission-ready entry point
_DEFAULT_CMS5_AGENT = build_cms5_policy(CMS5Config())

def agent(obs, configuration=None):
    """Kaggle environment entrypoint."""
    visible = configuration
    if isinstance(configuration, dict):
        visible = {
            k: v for k, v in configuration.items()
            if str(k).lower() not in {"seed", "randomseed"}
        }
    return _DEFAULT_CMS5_AGENT(obs, visible)


def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)
