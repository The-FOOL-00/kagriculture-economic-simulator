# SPDX-License-Identifier: MIT
"""ARCH-002 H1 frozen constants (preregistration §0/D1–D8, §5–§10).

Every value below is frozen by ``02_PREREGISTRATION.md``.  This module
contains NO logic, NO imports from the baseline, and NO tunable values.
Changing any constant invalidates the implementation freeze.
"""

from __future__ import annotations

# --- D2: terminal entry (prereg §6) --------------------------------------
ENTRY_STEP = 712
FINAL_STEP = 718
WINDOW_STEPS = tuple(range(ENTRY_STEP, FINAL_STEP + 1))
WINDOW_LEN = 7

# --- D1: worker-command whitelist + emission schema (prereg §5.1) ---------
# NOTE: DROP-only; no PLACE in proposals.  Markets are always the live
# baseline markets verbatim (B1/D3); H1 never constructs a market order.
WHITELIST_UNIT_OPS = frozenset({
    "NORTH", "SOUTH", "EAST", "WEST",
    "HARVEST", "COLLECT_FERTILIZER", "DROP", "PASS",
})
MOVE_OPS = ("NORTH", "SOUTH", "EAST", "WEST")

# --- D4: search budget (prereg §7/S5; Dmitrii live settings 128/1/8) ------
MAX_SIMULATIONS = 128
PASSES = 1
PROPOSALS_PER_ACTOR = 8
START_OFFSETS = tuple(range(7))  # offsets 0–6
TOP_SINGLES = 6
TOP_PAIR_HALF = 3
DIRECT_RETURN_RESERVE = 2

# --- D5: BUY coverage gate (prereg §8.2/H2) -------------------------------
# $125 = WHEAT curve maximum from MARKET_PARAMS WHEAT (25,10000,400,
# "sqrt",0.80,…): 25 + (0.8*25/sqrt(400))*sqrt(10000) = 25 + 100.
BUY_COVERAGE_PER_UNIT = 125

# --- D6: tie-breaking (prereg §9) -----------------------------------------
# Strict `>` everywhere; integer inclusion; frozen sort keys.  Declared
# here for auditability; enforced in h1_search / h1_dominance.

# --- G0: config pins (prereg §10.1) ---------------------------------------
PIN_BOARD_SIZE = 10
PIN_TURNS_PER_DAY = 24
PIN_EPISODE_STEPS = 720
PIN_SHED_CAPACITY = 100
PIN_MAX_ORDERS = 10

# --- Engine products (pinned unit_model.PRODUCTS order) --------------------
PRODUCTS_9 = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)
ANIMALS_3 = ("GOOSE", "COW", "SHEEP")

# --- Frozen baseline identity (prereg §3/D8) --------------------------------
BASELINE_PATH = "candidates/compiled_v54_plus_residual.py"
BASELINE_SHA256 = (
    "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
)

# --- Pinned engine-extract identity (unit_model, engine 1.32.7) ------------
# NOTE: this pins the EXTRACTED FILE's bytes as committed (worktree-clean,
# commit a8c3649).  The upstream kaggle-environments 1.32.7 source hash
# bc8a5487… (claimed inside the file) is asserted separately at load.
UNIT_MODEL_PATH = "extracted_agents/dmitrii_lb2800/unit_model.py"
UNIT_MODEL_SHA256 = (
    "c03e8c5cd10466c229ee0a44dece9a3943c10bff135d96a7822ffe75d6922724"
)
UNIT_MODEL_ENGINE_VERSION = "1.32.7"
UNIT_MODEL_SOURCE_SHA256 = (
    "bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e"
)
