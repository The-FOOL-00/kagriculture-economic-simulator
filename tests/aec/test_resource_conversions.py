# SPDX-License-Identifier: MIT
"""Unit tests for AEC-RESOURCE Conversion Catalog and Discovery Engine (§8, §9, §10, §11, §12)."""

from __future__ import annotations

import copy
import pytest

from aec.ir.economic_state import build_economic_state
from aec.resource.conversions import (
    ConversionCatalog,
    ConversionDiscoveryEngine,
    ConversionPath,
    ConversionRecipe,
)


def test_conversion_catalog_recipes() -> None:
    """Validate standard game conversion recipes match exact parameters (§8)."""
    catalog = ConversionCatalog()
    recipes = catalog.get_standard_recipes()

    assert "BUY_WHEAT_FEED" in recipes
    assert "FEED_LIVESTOCK_COW" in recipes
    assert "FEED_LIVESTOCK_GOOSE" in recipes
    assert "FEED_LIVESTOCK_SHEEP" in recipes
    assert "GROW_CARROT_CROP" in recipes
    assert "TERMINAL_LIQUIDATE_COMMODITY" in recipes

    cow_feed = recipes["FEED_LIVESTOCK_COW"]
    assert cow_feed.input_resources == {"WHEAT": 1}
    assert cow_feed.output_resources == {"MILK": 1, "FERTILIZER": 1}
    assert cow_feed.requires_worker
    assert cow_feed.requires_structure == "PASTURE"


def test_conversion_discovery_finds_livestock_paths(normal_opening_obs) -> None:
    """Verify discovery engine finds cow and goose paths when active (§8)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 100
    obs["farms"][0]["tiles"][2][2] = {"kind": "PASTURE", "animal": "COW", "consecutive_unfed": 0, "fed_today": True}
    obs["farms"][0]["tiles"][3][3] = {"kind": "COOP", "animal": "GOOSE", "consecutive_unfed": 0, "fed_today": True}

    econ_state = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ_state)

    path_ids = {p.path_id for p in paths}
    assert "CONV_CHAIN_WHEAT_TO_MILK" in path_ids
    assert "CONV_CHAIN_WHEAT_TO_EGG" in path_ids


def test_conversion_feasibility_catches_cash_liquidity_hole(normal_opening_obs) -> None:
    """Verify conversion path fails when cash is insufficient (§10)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["money"] = 5.0 # Only $5, but wheat costs $25

    econ_state = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    recipes = ConversionCatalog.get_standard_recipes()

    path = ConversionPath(
        path_id="TEST_EXPENSIVE_CHAIN",
        target_commodity="MILK",
        recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_COW"]],
        total_steps=49,
        total_cost_est=25.0,
        expected_revenue_est=160.0,
        net_value_est=135.0
    )

    is_feas, reason = engine.check_path_feasibility(path, econ_state)
    assert not is_feas
    assert "Cash liquidity hole" in (reason or "")


def test_conversion_feasibility_catches_shed_capacity_overflow(normal_opening_obs) -> None:
    """Verify conversion path fails when it would overflow shed capacity (100) (§11)."""
    obs = copy.deepcopy(normal_opening_obs)
    # Fill shed to capacity 100
    obs["private"]["shed"]["WHEAT"] = 100

    econ_state = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    recipes = ConversionCatalog.get_standard_recipes()

    # Buying 1 unit of wheat feed has shed_capacity_delta = +1 -> 101 units
    path = ConversionPath(
        path_id="TEST_OVERFLOW_CHAIN",
        target_commodity="WHEAT",
        recipes=[recipes["BUY_WHEAT_FEED"]],
        total_steps=1,
        total_cost_est=25.0,
        expected_revenue_est=25.0,
        net_value_est=0.0
    )

    is_feas, reason = engine.check_path_feasibility(path, econ_state)
    assert not is_feas
    assert "Shed capacity overflow" in (reason or "")


def test_conversion_feasibility_catches_terminal_distance(normal_opening_obs) -> None:
    """Verify conversion path requiring more turns than remain is rejected (§12)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 710 # Only 8 steps remain before step 718

    econ_state = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    recipes = ConversionCatalog.get_standard_recipes()

    # Growing carrot requires 48 steps
    path = ConversionPath(
        path_id="TEST_TERMINAL_TOO_LATE",
        target_commodity="CARROT",
        recipes=[recipes["GROW_CARROT_CROP"]],
        total_steps=48,
        total_cost_est=20.0,
        expected_revenue_est=140.0,
        net_value_est=120.0
    )

    is_feas, reason = engine.check_path_feasibility(path, econ_state)
    assert not is_feas
    assert "Terminal infeasibility" in (reason or "")
