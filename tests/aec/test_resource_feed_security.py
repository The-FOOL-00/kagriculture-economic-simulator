# SPDX-License-Identifier: MIT
"""Unit tests for AEC-RESOURCE Feed Security Engine (§5, §6)."""

from __future__ import annotations

import copy
import pytest

from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch
from aec.resource.feed_security import (
    FeedIntervalProfile,
    FeedSecurityEngine,
    FeedSecurityState,
    LivestockEntity,
)


def test_livestock_entity_escape_semantics() -> None:
    """Validate exact game rules: animal escapes when consecutive_unfed >= 2 (§6)."""
    animal = LivestockEntity(
        animal_id="COW_3_4",
        subtype="COW",
        position=(3, 4),
        structure="PASTURE",
        placed_day=0,
        consecutive_unfed=0,
        fed_today=True,
        cared_today=False
    )
    assert animal.days_until_escape == 2
    assert not animal.is_starving

    # Day 1 un-fed
    animal.consecutive_unfed = 1
    assert animal.days_until_escape == 1
    assert animal.is_starving

    # Day 2 un-fed -> escapes
    animal.consecutive_unfed = 2
    assert animal.days_until_escape == 0


def test_feed_engine_extract_all_livestock_subtypes(normal_opening_obs) -> None:
    """Verify FeedSecurityEngine extracts COW, SHEEP, and GOOSE from tiles (§5)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "consecutive_unfed": 0, "fed_today": False}
    obs["farms"][0]["tiles"][2][2] = {"kind": "PASTURE", "animal": "SHEEP", "consecutive_unfed": 1, "fed_today": False}
    obs["farms"][0]["tiles"][3][3] = {"kind": "COOP", "animal": "GOOSE", "consecutive_unfed": 0, "fed_today": True}

    econ_state = build_economic_state(obs)
    engine = FeedSecurityEngine()
    animals = engine.extract_livestock(econ_state)

    assert len(animals) == 3
    subtypes = {a.subtype for a in animals}
    assert subtypes == {"COW", "SHEEP", "GOOSE"}


def test_feed_trajectory_adequate_supply(normal_opening_obs) -> None:
    """Verify feed trajectory evaluates to is_secure=True when feed is abundant (§5)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "consecutive_unfed": 0, "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 10

    econ_state = build_economic_state(obs)
    engine = FeedSecurityEngine()

    # Trajectory where worker feeds cow at step 0
    trajectory = [{"farmer": ["FEED"], "hands": [], "market": []}]
    sec_state = engine.evaluate_feed_trajectory(econ_state, trajectory, horizon=12)

    assert sec_state.is_secure
    assert sec_state.deficit_count == 0
    assert sec_state.escaped_animals_count == 0


def test_feed_trajectory_detects_starvation_escape(normal_opening_obs) -> None:
    """Verify feed trajectory catches animal escaping when un-fed across 2 day boundaries (48 steps) (§6)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 0
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "consecutive_unfed": 0, "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 0 # No wheat!

    econ_state = build_economic_state(obs)
    engine = FeedSecurityEngine()

    # 48 steps of idle pass across 2 day boundaries (turns 23 and 47)
    trajectory = [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(48)]
    sec_state = engine.evaluate_feed_trajectory(econ_state, trajectory, horizon=48)

    assert not sec_state.is_secure
    assert sec_state.escaped_animals_count >= 1
    assert "escaped" in (sec_state.reason or "").lower()


def test_candidate_patch_selling_needed_feed_is_rejected(normal_opening_obs) -> None:
    """Verify candidate patch proposing to sell wheat needed by livestock is caught (§5, §18)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 0
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "consecutive_unfed": 0, "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 1 # Exactly 1 unit needed

    econ_state = build_economic_state(obs)
    engine = FeedSecurityEngine()

    baseline_action = {"farmer": ["FEED"], "hands": [], "market": []}
    # Candidate patch sells the 1 unit of wheat for quick cash!
    cand_patch = CoupledPatch(
        patch_id="PATCH_SELL_FEED",
        source_opportunity_id="OPP_CASH",
        market_mutations=[["SELL", "WHEAT", 1]],
        expected_horizon=6
    )

    future_traj = [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(12)]
    sec_state = engine.verify_candidate_patch(cand_patch, baseline_action, econ_state, future_traj, horizon=6)

    # With wheat sold, cow cannot be fed and surplus is negative
    assert not sec_state.is_secure
    assert sec_state.deficit_count > 0
