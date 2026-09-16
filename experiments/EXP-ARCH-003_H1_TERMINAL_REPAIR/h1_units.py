# SPDX-License-Identifier: MIT
"""ARCH-003 H1 engine-exact unit/decay shim (prereg §11/Q1, §7/S2).

Re-exports the pinned engine extract
``extracted_agents/dmitrii_lb2800/unit_model.py`` (file SHA-256
c03e8c5c…, engine 1.32.7) after verifying its hash.  H1 performs
NO reimplementation of unit or decay semantics: every tile, inventory,
and deposit transition in the shadow simulator calls these exact
functions.  Any hash mismatch fails closed (import raises).
"""

from __future__ import annotations

import hashlib
import importlib.util
import os

from h1_const import (
    UNIT_MODEL_ENGINE_VERSION,
    UNIT_MODEL_PATH,
    UNIT_MODEL_SHA256,
    UNIT_MODEL_SOURCE_SHA256,
)

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_unit_model():
    path = os.path.join(_REPO_ROOT, UNIT_MODEL_PATH)
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    if digest != UNIT_MODEL_SHA256:
        raise RuntimeError(
            "H1 FAIL-CLOSED: unit_model hash mismatch: %s != %s"
            % (digest, UNIT_MODEL_SHA256)
        )
    spec = importlib.util.spec_from_file_location("h1_pinned_unit_model", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "ENGINE_VERSION", None) != UNIT_MODEL_ENGINE_VERSION:
        raise RuntimeError("H1 FAIL-CLOSED: unit_model ENGINE_VERSION drift")
    if getattr(module, "SOURCE_SHA256", None) != UNIT_MODEL_SOURCE_SHA256:
        raise RuntimeError("H1 FAIL-CLOSED: unit_model SOURCE_SHA256 drift")
    return module


_unit = _load_unit_model()

# Exact engine-extract surface used by the H1 shadow simulator.
CROPS = _unit.CROPS
ANIMALS = _unit.ANIMALS
PRODUCTS = _unit.PRODUCTS
FARMER_MOVES = _unit.FARMER_MOVES
ENGINE_VERSION = _unit.ENGINE_VERSION
SOURCE_SHA256 = _unit.SOURCE_SHA256
_apply_unit_action = _unit._apply_unit_action
_decay_plants = _unit._decay_plants
_shed_access_tiles = _unit._shed_access_tiles
_is_shed_adjacent = _unit._is_shed_adjacent


def maturity_day(item):
    """First-yield day for a crop product (prereg §7/S2)."""
    return int(CROPS[item]["first_yield_day"])
