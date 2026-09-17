import sys
from pathlib import Path

# Ensure workspace root is in sys.path for test imports
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import pytest
from typing import Any, Dict


@pytest.fixture
def normal_opening_obs() -> Dict[str, Any]:
    return {
        "step": 0, "day": 0, "hour": 0, "player": 0,
        "farms": [
            {
                "money": 3000.0, "farmer": [4, 4], "hands": [],
                "tiles": [[None]*10 for _ in range(10)],
                "unlocked_quadrants": ["NW"], "hires_today": 0
            },
            {
                "money": 3000.0, "farmer": [4, 4], "hands": [],
                "tiles": [[None]*10 for _ in range(10)],
                "unlocked_quadrants": ["NW"], "hires_today": 0
            }
        ],
        "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        "market": {
            "prices": {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100},
            "inventory": {"WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000, "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000}
        },
        "town": {"unlocked_shops": []}
    }


@pytest.fixture
def weed_obstruction_obs() -> Dict[str, Any]:
    tiles = [[None]*10 for _ in range(10)]
    tiles[4][4] = {"kind": "WEED"}  # Farmer stands here
    return {
        "step": 48, "day": 2, "hour": 0, "player": 0,
        "farms": [
            {"money": 2500.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": tiles, "unlocked_quadrants": ["NW"], "hires_today": 1},
            {"money": 2500.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 1}
        ],
        "private": {"shed": {"WHEAT": 10}, "seeds": {"WHEAT": 4}, "inventories": [{}, {}]},
        "market": {
            "prices": {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100},
            "inventory": {"WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000, "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000}
        },
        "town": {"unlocked_shops": []}
    }


@pytest.fixture
def cash_deficit_obs() -> Dict[str, Any]:
    return {
        "step": 72, "day": 3, "hour": 0, "player": 0,
        "farms": [
            {"money": 110.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 0},
            {"money": 2800.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 0}
        ],
        "private": {"shed": {"WHEAT": 5, "STRAWBERRY": 10}, "seeds": {}, "inventories": [{}, {}]},
        "market": {
            "prices": {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100},
            "inventory": {"WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000, "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000}
        },
        "town": {"unlocked_shops": ["YARN_STORE"]}
    }


@pytest.fixture
def shed_capacity_obs() -> Dict[str, Any]:
    return {
        "step": 93, "day": 3, "hour": 21, "player": 0,
        "farms": [
            {"money": 3500.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 0},
            {"money": 3000.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW"], "hires_today": 0}
        ],
        "private": {"shed": {"STRAWBERRY": 90, "WHEAT": 6}, "seeds": {}, "inventories": [{"STRAWBERRY": 2}, {"STRAWBERRY": 1}]},
        "market": {
            "prices": {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100},
            "inventory": {"WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000, "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000}
        },
        "town": {"unlocked_shops": ["BRUNCH_SPOT"]}
    }


@pytest.fixture
def terminal_proximity_obs() -> Dict[str, Any]:
    return {
        "step": 718, "day": 29, "hour": 22, "player": 0,
        "farms": [
            {"money": 15000.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW", "NE"], "hires_today": 0},
            {"money": 14000.0, "farmer": [4, 4], "hands": [[3, 4]], "tiles": [[None]*10 for _ in range(10)], "unlocked_quadrants": ["NW", "NE"], "hires_today": 0}
        ],
        "private": {"shed": {"STRAWBERRY": 25, "WOOL": 10, "MELON": 5}, "seeds": {}, "inventories": [{}, {}]},
        "market": {
            "prices": {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100},
            "inventory": {"WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000, "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000}
        },
        "town": {"unlocked_shops": ["YARN_STORE", "BAKERY", "SMOOTHIE_SHOP"]}
    }
