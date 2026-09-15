"""
EXP-A: Declarative Backbone Parameter Dataclass
================================================
22 free scalar/ordinal parameters representing the macroeconomic strategy
of the V54/V66 backbone WITHOUT copying its exact 719-step action sequence.

All values here are the INFORMATIONAL PRIOR estimates derived from V54 route
analysis. The compiler will use these to generate actions on-the-fly.

IMPORTANT: This is not a replay. The compiler generates actions from the
current observation and these parameters each step.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class BackboneParams:
    # ------------------------------------------------------------------ #
    # CAPITAL                                                              #
    # ------------------------------------------------------------------ #
    initial_cash_reserve: int = 30

    # ------------------------------------------------------------------ #
    # LAND EXPANSION                                                       #
    # ------------------------------------------------------------------ #
    land_expansion_1_step: int = 150
    land_expansion_2_step: int = 265
    land_expansion_2_enabled: bool = True

    # ------------------------------------------------------------------ #
    # LABOR (HIRE)                                                         #
    # ------------------------------------------------------------------ #
    hire_start_step: int = 0   # step is 0-indexed; V54 hires at game start
    hire_interval_steps: int = 24
    hire_batch_per_interval: int = 4
    hire_initial_burst: int = 5
    max_workers: int = 11

    # ------------------------------------------------------------------ #
    # LIVESTOCK (from opening shed)                                        #
    # ------------------------------------------------------------------ #
    cow_target: int = 8
    sheep_target: int = 4

    # ------------------------------------------------------------------ #
    # CROPS -- MELON                                                       #
    # ------------------------------------------------------------------ #
    melon_seed_count: int = 8
    melon_liquidation_step: int = 249
    melon_sell_batch: int = 24

    # ------------------------------------------------------------------ #
    # CROPS -- STRAWBERRY                                                  #
    # ------------------------------------------------------------------ #
    strawberry_seed_count: int = 38
    strawberry_start_step: int = 128
    strawberry_sell_batch: int = 12

    # ------------------------------------------------------------------ #
    # CROPS -- WHEAT                                                       #
    # ------------------------------------------------------------------ #
    wheat_seed_count: int = 187
    wheat_sell_batch: int = 24
    buy_wheat_for_feed: bool = True

    # ------------------------------------------------------------------ #
    # FEED                                                                 #
    # ------------------------------------------------------------------ #
    feed_reserve_days: int = 3

    # ------------------------------------------------------------------ #
    # LIQUIDATION                                                          #
    # ------------------------------------------------------------------ #
    sell_start_step: int = 72
    sell_batch_size: int = 18
    terminal_liquidation_step: int = 670
    terminal_sell_livestock: bool = False
    terminal_wheat_dump: bool = True


# Default instance (V54-calibrated priors)
V54_PRIOR = BackboneParams()

# Search bounds for EXP-D
PARAM_BOUNDS = {
    "initial_cash_reserve":       (0, 100),
    "land_expansion_1_step":      (72, 216),
    "land_expansion_2_step":      (192, 360),
    "hire_start_step":            (0, 24),
    "hire_interval_steps":        (12, 48),
    "hire_batch_per_interval":    (2, 8),
    "hire_initial_burst":         (3, 8),
    "max_workers":                (8, 15),
    "cow_target":                 (5, 12),
    "sheep_target":               (3, 8),
    "melon_seed_count":           (6, 20),
    "melon_liquidation_step":     (200, 300),
    "melon_sell_batch":           (12, 24),
    "strawberry_seed_count":      (20, 60),
    "strawberry_start_step":      (96, 200),
    "strawberry_sell_batch":      (8, 24),
    "wheat_seed_count":           (100, 250),
    "wheat_sell_batch":           (12, 61),
    "feed_reserve_days":          (2, 5),
    "sell_start_step":            (100, 200),
    "sell_batch_size":            (12, 24),
    "terminal_liquidation_step":  (600, 700),
}
